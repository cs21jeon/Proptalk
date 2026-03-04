"""
핵심 과금 비즈니스 로직
- 잔액 확인, 사용량 차감, 시간 추가
- billingKey AES-256 암호화/복호화
"""
import os
import base64
import logging
from models_billing import BillingPlan, UserBilling, UsageLog

logger = logging.getLogger(__name__)


# ============================================================
# 잔액 확인 / 차감
# ============================================================

def ensure_user_billing(user_id):
    """사용자 billing 행 보장 (없으면 무료 10분으로 생성)"""
    return UserBilling.ensure(user_id)


def check_can_transcribe(user_id):
    """
    STT 가능 여부 확인.
    Returns: (bool, reason_str)
    """
    billing = UserBilling.find_by_user_id(user_id)
    if not billing:
        # 첫 사용자 - billing 행 생성
        billing = ensure_user_billing(user_id)
        if not billing:
            return False, '과금 정보 생성 실패'

    remaining = billing['remaining_seconds']

    if remaining <= 0:
        return False, '이용 시간이 소진되었습니다. 충전 후 이용해주세요.'

    return True, 'ok'


def deduct_usage(user_id, audio_file_id, duration_seconds):
    """
    STT 완료 후 사용량 차감.
    duration_seconds: Whisper 결과에서 추출한 음성 길이(초)
    음수 잔액 허용 (다음 업로드 시 차단됨)
    """
    billing = UserBilling.find_by_user_id(user_id)
    if not billing:
        logger.error(f"[Billing] user_billing not found for user {user_id}")
        return None

    seconds_before = billing['remaining_seconds']
    plan_code = None
    if billing.get('current_plan_id'):
        plan = BillingPlan.find_by_id(billing['current_plan_id'])
        plan_code = plan['code'] if plan else None

    # 원자적 차감
    result = UserBilling.deduct_seconds(user_id, duration_seconds)
    seconds_after = result['remaining_seconds'] if result else seconds_before - duration_seconds

    # 사용 로그 기록
    UsageLog.create(
        user_id=user_id,
        audio_file_id=audio_file_id,
        seconds_used=duration_seconds,
        seconds_before=seconds_before,
        seconds_after=seconds_after,
        plan_code=plan_code,
    )

    logger.info(
        f"[Billing] 차감: user={user_id}, audio={audio_file_id}, "
        f"used={duration_seconds:.1f}s, before={seconds_before:.1f}s, after={seconds_after:.1f}s"
    )

    return {
        'seconds_used': duration_seconds,
        'seconds_before': seconds_before,
        'seconds_after': seconds_after,
    }


def add_time(user_id, plan_id, minutes=None):
    """
    시간팩 구매 시 잔여 시간 추가.
    minutes가 None이면 plan의 minutes_included 사용.
    """
    plan = BillingPlan.find_by_id(plan_id)
    if not plan:
        raise ValueError(f"Plan not found: {plan_id}")

    if minutes is None:
        minutes = plan['minutes_included']

    seconds = minutes * 60

    # billing 행 보장
    ensure_user_billing(user_id)

    result = UserBilling.add_seconds(user_id, seconds)

    logger.info(
        f"[Billing] 시간 추가: user={user_id}, plan={plan['code']}, "
        f"+{minutes}분, 잔여={result['remaining_seconds']:.0f}초"
    )

    return result


def get_billing_status(user_id):
    """사용자 과금 상태 조회"""
    billing = UserBilling.find_by_user_id(user_id)
    if not billing:
        billing = ensure_user_billing(user_id)

    plan = None
    if billing and billing.get('current_plan_id'):
        plan = BillingPlan.find_by_id(billing['current_plan_id'])

    return {
        'remaining_seconds': billing['remaining_seconds'] if billing else 600,
        'subscription_status': billing['subscription_status'] if billing else 'free',
        'plan': {
            'code': plan['code'] if plan else 'free',
            'name': plan['name'] if plan else '무료 체험',
            'plan_type': plan['plan_type'] if plan else 'free',
        } if plan else {'code': 'free', 'name': '무료 체험', 'plan_type': 'free'},
        'subscription_expires_at': billing.get('subscription_expires_at') if billing else None,
        'auto_renew': billing.get('auto_renew', False) if billing else False,
    }


# ============================================================
# billingKey AES-256-CBC 암호화
# ============================================================

def _get_encryption_key():
    """환경변수에서 32바이트 AES 키 로드"""
    from config import Config
    key_hex = Config.BILLING_ENCRYPTION_KEY
    if not key_hex or len(key_hex) < 64:
        raise ValueError("BILLING_ENCRYPTION_KEY must be a 64-char hex string (32 bytes)")
    return bytes.fromhex(key_hex)


def encrypt_billing_key(plaintext):
    """
    billingKey를 AES-256-CBC로 암호화.
    Returns: (encrypted_b64, iv_b64)
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding

    key = _get_encryption_key()
    iv = os.urandom(16)

    # PKCS7 패딩
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode('utf-8')) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    return base64.b64encode(ciphertext).decode(), base64.b64encode(iv).decode()


def decrypt_billing_key(encrypted_b64, iv_b64):
    """
    AES-256-CBC 복호화 → 원본 billingKey 반환.
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding

    key = _get_encryption_key()
    iv = base64.b64decode(iv_b64)
    ciphertext = base64.b64decode(encrypted_b64)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded) + unpadder.finalize()

    return plaintext.decode('utf-8')


def extract_audio_duration(segments):
    """Whisper segments에서 음성 전체 길이(초) 추출"""
    if not segments:
        return 0
    last = segments[-1]
    # segments는 dict 또는 object일 수 있음
    if isinstance(last, dict):
        return last.get('end', 0)
    return getattr(last, 'end', 0)

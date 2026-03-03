"""
Google OAuth 인증 + JWT 토큰 관리
"""
import jwt
import logging
import requests as http_requests
from datetime import datetime, timezone
from functools import wraps
from flask import request, jsonify, g
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from config import Config
from models import User, Room, UserConsent, AccessLog, CURRENT_CONSENT_VERSION

logger = logging.getLogger(__name__)

# Google OAuth token endpoint
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'


# ============================================================
# JWT 토큰 생성/검증
# ============================================================
def create_token(user_id):
    """JWT 토큰 생성"""
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + Config.JWT_EXPIRY,
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')


def decode_token(token):
    """JWT 토큰 디코딩"""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ============================================================
# Google OAuth 토큰 교환
# ============================================================
def exchange_auth_code(server_auth_code):
    """
    serverAuthCode를 access_token + refresh_token으로 교환
    Flutter에서 받은 authorization code를 Google에 전송하여 토큰을 받음
    """
    resp = http_requests.post(GOOGLE_TOKEN_URL, data={
        'code': server_auth_code,
        'client_id': Config.GOOGLE_CLIENT_ID,
        'client_secret': Config.GOOGLE_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'redirect_uri': '',  # 모바일 앱은 빈 문자열
    })

    if resp.status_code != 200:
        logger.error(f"Token exchange failed: {resp.status_code} {resp.text}")
        return None

    data = resp.json()
    return {
        'access_token': data['access_token'],
        'refresh_token': data.get('refresh_token'),
        'expires_at': datetime.now(timezone.utc).timestamp() + data.get('expires_in', 3600),
        'token_type': data.get('token_type', 'Bearer'),
    }


def refresh_access_token(tokens):
    """
    refresh_token으로 새 access_token 발급
    Returns: 갱신된 토큰 dict 또는 None
    """
    refresh_token = tokens.get('refresh_token')
    if not refresh_token:
        return None

    resp = http_requests.post(GOOGLE_TOKEN_URL, data={
        'refresh_token': refresh_token,
        'client_id': Config.GOOGLE_CLIENT_ID,
        'client_secret': Config.GOOGLE_CLIENT_SECRET,
        'grant_type': 'refresh_token',
    })

    if resp.status_code != 200:
        logger.error(f"Token refresh failed: {resp.status_code} {resp.text}")
        return None

    data = resp.json()
    tokens['access_token'] = data['access_token']
    tokens['expires_at'] = datetime.now(timezone.utc).timestamp() + data.get('expires_in', 3600)
    return tokens


# ============================================================
# 인증 데코레이터
# ============================================================
def login_required(f):
    """로그인 필수 데코레이터"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Authorization 헤더에서 토큰 추출
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': '인증 토큰이 필요합니다'}), 401

        payload = decode_token(token)
        if not payload:
            return jsonify({'error': '토큰이 만료되었거나 유효하지 않습니다'}), 401

        user = User.find_by_id(payload['user_id'])
        if not user:
            return jsonify({'error': '사용자를 찾을 수 없습니다'}), 401

        g.user = user
        g.user_id = user['id']
        return f(*args, **kwargs)

    return decorated


def room_role_required(role='admin'):
    """방 역할 확인 데코레이터 (login_required 이후 사용)
    URL에 room_id가 있어야 함"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            room_id = kwargs.get('room_id')
            if room_id is None:
                return jsonify({'error': 'room_id가 필요합니다'}), 400

            from models import query_one
            member = query_one(
                "SELECT role, status FROM room_members WHERE room_id = %s AND user_id = %s",
                (room_id, g.user_id)
            )

            if not member or member['status'] != 'active':
                return jsonify({'error': '접근 권한이 없습니다'}), 403

            if role == 'admin' and member['role'] != 'admin':
                return jsonify({'error': '관리자 권한이 필요합니다'}), 403

            g.room_role = member['role']
            return f(*args, **kwargs)

        return decorated
    return decorator


# ============================================================
# Google OAuth 로그인 API
# ============================================================
def register_auth_routes(app):

    @app.route('/api/auth/google', methods=['POST'])
    def google_login():
        """
        Google Sign-In 토큰 검증 후 JWT 발급
        server_auth_code가 있으면 Drive 토큰도 교환하여 저장

        Request:
            {
                "id_token": "구글에서 받은 id_token",
                "server_auth_code": "(선택) Drive 권한용 auth code"
            }
        """
        data = request.get_json()
        google_token = data.get('id_token')
        server_auth_code = data.get('server_auth_code')

        if not google_token:
            return jsonify({'error': 'id_token이 필요합니다'}), 400

        try:
            # Google id_token 검증
            idinfo = id_token.verify_oauth2_token(
                google_token,
                google_requests.Request(),
                Config.GOOGLE_CLIENT_ID
            )

            google_id = idinfo['sub']
            email = idinfo.get('email', '')
            name = idinfo.get('name', email.split('@')[0])
            avatar_url = idinfo.get('picture', '')

            # 사용자 생성/업데이트
            user = User.create(google_id, email, name, avatar_url)

            # server_auth_code가 있으면 Drive 토큰 교환
            drive_connected = False
            if server_auth_code and Config.GOOGLE_CLIENT_SECRET:
                try:
                    tokens = exchange_auth_code(server_auth_code)
                    if tokens and tokens.get('refresh_token'):
                        User.update_google_tokens(user['id'], tokens)
                        drive_connected = True
                        logger.info(f"Drive 토큰 저장 완료: {email}")
                    else:
                        # refresh_token이 없으면 기존 토큰이 있는지 확인
                        existing = User.get_google_tokens(user['id'])
                        if existing and existing.get('refresh_token') and tokens:
                            # access_token만 갱신
                            existing['access_token'] = tokens['access_token']
                            existing['expires_at'] = tokens['expires_at']
                            User.update_google_tokens(user['id'], existing)
                            drive_connected = True
                except Exception as e:
                    logger.error(f"Drive 토큰 교환 실패: {e}")
            else:
                # 기존 토큰이 있는지 확인
                existing = User.get_google_tokens(user['id'])
                if existing and existing.get('refresh_token'):
                    drive_connected = True

            # JWT 토큰 발급
            token = create_token(user['id'])

            # 필수 동의 항목 확인
            missing_consents = UserConsent.check_required(user['id'])
            consent_required = len(missing_consents) > 0

            # 접속 로그
            AccessLog.log(user['id'], 'login', 'user', user['id'],
                          ip_address=request.remote_addr,
                          user_agent=request.headers.get('User-Agent'))

            logger.info(f"로그인 성공: {email} (Drive: {drive_connected}, consent_required: {consent_required})")

            return jsonify({
                'token': token,
                'user': {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'avatar_url': user['avatar_url'],
                    'drive_connected': drive_connected,
                },
                'consent_required': consent_required,
                'missing_consents': missing_consents,
            })

        except ValueError as e:
            logger.error(f"Google 토큰 검증 실패: {e}")
            return jsonify({'error': '유효하지 않은 Google 토큰입니다'}), 401


    @app.route('/api/auth/me', methods=['GET'])
    @login_required
    def get_me():
        """현재 로그인 사용자 정보"""
        user = g.user
        tokens = User.get_google_tokens(user['id'])
        drive_connected = bool(tokens and tokens.get('refresh_token'))

        return jsonify({
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'avatar_url': user['avatar_url'],
                'drive_connected': drive_connected,
            }
        })


    @app.route('/api/auth/drive/status', methods=['GET'])
    @login_required
    def drive_status():
        """Drive 연동 상태 확인"""
        tokens = User.get_google_tokens(g.user_id)
        connected = bool(tokens and tokens.get('refresh_token'))

        return jsonify({
            'connected': connected,
            'has_refresh_token': bool(tokens and tokens.get('refresh_token')),
        })


    @app.route('/api/auth/drive/disconnect', methods=['POST'])
    @login_required
    def drive_disconnect():
        """Drive 연동 해제"""
        User.clear_google_tokens(g.user_id)
        logger.info(f"Drive 연동 해제: user_id={g.user_id}")
        return jsonify({'success': True, 'message': 'Drive 연동이 해제되었습니다.'})


    # ============================================================
    # 동의 관련 API
    # ============================================================
    @app.route('/api/auth/consent', methods=['POST'])
    @login_required
    def record_consent():
        """
        동의 기록 저장
        Request: { "consents": [{"type": "terms", "version": "2026-03-01"}, ...] }
        """
        data = request.get_json()
        consents = data.get('consents', [])

        if not consents:
            return jsonify({'error': '동의 항목이 필요합니다'}), 400

        ip = request.remote_addr
        ua = request.headers.get('User-Agent')
        results = []

        for item in consents:
            consent_type = item.get('type')
            version = item.get('version', CURRENT_CONSENT_VERSION)

            if not consent_type:
                continue

            result = UserConsent.create(g.user_id, consent_type, version, ip, ua)
            if result:
                results.append({
                    'type': consent_type,
                    'version': version,
                    'agreed_at': result['agreed_at'].isoformat() if hasattr(result['agreed_at'], 'isoformat') else str(result['agreed_at']),
                })

        # 감사 로그
        AccessLog.log(g.user_id, 'consent', 'consent', None, ip, ua,
                       details={'consents': [c['type'] for c in consents]})

        logger.info(f"동의 기록: user_id={g.user_id}, types={[c.get('type') for c in consents]}")
        return jsonify({'success': True, 'consents': results})


    @app.route('/api/auth/consent/status', methods=['GET'])
    @login_required
    def consent_status():
        """현재 동의 상태 조회"""
        all_consents = UserConsent.get_all_for_user(g.user_id)
        missing = UserConsent.check_required(g.user_id)

        consent_list = []
        for c in all_consents:
            consent_list.append({
                'type': c['consent_type'],
                'version': c['version'],
                'agreed': c['agreed'],
                'agreed_at': c['agreed_at'].isoformat() if c.get('agreed_at') and hasattr(c['agreed_at'], 'isoformat') else None,
                'withdrawn_at': c['withdrawn_at'].isoformat() if c.get('withdrawn_at') and hasattr(c['withdrawn_at'], 'isoformat') else None,
            })

        return jsonify({
            'consents': consent_list,
            'missing': missing,
            'consent_required': len(missing) > 0,
        })


    @app.route('/api/auth/consent/withdraw', methods=['POST'])
    @login_required
    def withdraw_consent():
        """동의 철회"""
        data = request.get_json()
        consent_type = data.get('type')

        if not consent_type:
            return jsonify({'error': '동의 유형이 필요합니다'}), 400

        result = UserConsent.withdraw(g.user_id, consent_type)

        AccessLog.log(g.user_id, 'consent_withdraw', 'consent', None,
                       request.remote_addr, request.headers.get('User-Agent'),
                       details={'consent_type': consent_type})

        logger.info(f"동의 철회: user_id={g.user_id}, type={consent_type}")
        return jsonify({'success': True, 'type': consent_type})


    @app.route('/api/auth/account', methods=['DELETE'])
    @login_required
    def delete_account():
        """회원 탈퇴 - 모든 개인정보 삭제"""
        # 감사 로그 (삭제 전에 기록)
        AccessLog.log(g.user_id, 'account_delete', 'user', g.user_id,
                       request.remote_addr, request.headers.get('User-Agent'))

        User.delete_account(g.user_id)
        logger.info(f"회원 탈퇴: user_id={g.user_id}")
        return jsonify({'success': True, 'message': '계정이 삭제되었습니다.'})

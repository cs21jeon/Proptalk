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
from models import User

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

            logger.info(f"로그인 성공: {email} (Drive: {drive_connected})")

            return jsonify({
                'token': token,
                'user': {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'avatar_url': user['avatar_url'],
                    'drive_connected': drive_connected,
                }
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

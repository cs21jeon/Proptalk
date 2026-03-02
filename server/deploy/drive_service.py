"""
Google Drive Service - 방장의 Google Drive에 파일 저장
사용자 OAuth 토큰 기반, 자동 토큰 갱신 포함
"""
import os
import io
import re
import logging
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

logger = logging.getLogger(__name__)


def _get_valid_credentials(user_tokens):
    """
    사용자 토큰으로 Credentials 생성, 만료 시 자동 갱신
    Returns: (credentials, updated_tokens or None)
    """
    credentials = Credentials(
        token=user_tokens.get('access_token'),
        refresh_token=user_tokens.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=['https://www.googleapis.com/auth/drive.file']
    )

    updated_tokens = None

    # 토큰 만료 확인 및 갱신
    expires_at = user_tokens.get('expires_at', 0)
    now = datetime.now(timezone.utc).timestamp()

    if now >= expires_at - 300:  # 5분 전부터 갱신
        if credentials.refresh_token:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
            updated_tokens = {
                **user_tokens,
                'access_token': credentials.token,
                'expires_at': now + 3600,
            }
            logger.info("[Drive] 토큰 자동 갱신 완료")

    return credentials, updated_tokens


def _sanitize_folder_name(name):
    """폴더명에서 특수문자 제거"""
    sanitized = re.sub(r'[\\/:*?"<>|]', '_', name)
    return sanitized.strip() or 'Unnamed'


def get_drive_service(user_tokens):
    """사용자 토큰으로 Drive 서비스 생성"""
    credentials, updated_tokens = _get_valid_credentials(user_tokens)
    service = build('drive', 'v3', credentials=credentials)
    return service, updated_tokens


def get_or_create_folder(service, folder_name, parent_id=None):
    """폴더가 없으면 생성, 있으면 ID 반환"""
    safe_name = _sanitize_folder_name(folder_name)
    query = f"name='{safe_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])

    if files:
        return files[0]['id']

    # 폴더 생성
    file_metadata = {
        'name': safe_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]

    folder = service.files().create(body=file_metadata, fields='id').execute()
    logger.info(f"[Drive] 폴더 생성: {safe_name} ({folder.get('id')})")
    return folder.get('id')


def ensure_room_folder(user_tokens, room_name):
    """
    Proptalk/{room_name} 폴더 확보 (없으면 생성)
    Returns: (folder_id, updated_tokens)
    """
    service, updated_tokens = get_drive_service(user_tokens)

    proptalk_folder_id = get_or_create_folder(service, 'Proptalk')
    room_folder_id = get_or_create_folder(service, room_name, proptalk_folder_id)

    return room_folder_id, updated_tokens


def upload_to_drive(user_tokens, file_path, room_name, room_folder_id=None):
    """
    방장의 Google Drive에 파일 업로드
    폴더 구조: Proptalk/{room_name}/{file}

    Returns:
        {'file_id': str, 'web_link': str, 'updated_tokens': dict or None, 'folder_id': str}
    """
    try:
        service, updated_tokens = get_drive_service(user_tokens)

        # 폴더 ID가 캐시되어 있으면 사용, 없으면 생성
        if not room_folder_id:
            proptalk_folder_id = get_or_create_folder(service, 'Proptalk')
            room_folder_id = get_or_create_folder(service, room_name, proptalk_folder_id)

        # 파일 업로드
        file_name = os.path.basename(file_path)
        file_metadata = {
            'name': file_name,
            'parents': [room_folder_id]
        }

        # MIME 타입 결정
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac',
            '.webm': 'audio/webm',
            '.aac': 'audio/aac',
            '.amr': 'audio/amr',
            '.3gp': 'audio/3gpp',
        }
        mime_type = mime_types.get(ext, 'audio/mpeg')

        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink, webContentLink'
        ).execute()

        logger.info(f"[Drive] 업로드 완료: {file_name} → {file.get('id')}")

        return {
            'file_id': file.get('id'),
            'web_link': file.get('webViewLink'),
            'download_link': file.get('webContentLink'),
            'updated_tokens': updated_tokens,
            'folder_id': room_folder_id,
        }
    except Exception as e:
        logger.error(f"[Drive] 업로드 실패: {e}")
        raise


def download_from_drive(user_tokens, file_id):
    """
    Google Drive에서 파일 다운로드 (서버 프록시용)
    Returns: (파일 바이트, updated_tokens)
    """
    try:
        service, updated_tokens = get_drive_service(user_tokens)

        request = service.files().get_media(fileId=file_id)
        file_data = io.BytesIO()
        downloader = MediaIoBaseDownload(file_data, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        return file_data.getvalue(), updated_tokens
    except Exception as e:
        logger.error(f"[Drive] 다운로드 실패: {e}")
        raise


def delete_from_drive(user_tokens, file_id):
    """Google Drive에서 파일 삭제"""
    try:
        service, _ = get_drive_service(user_tokens)
        service.files().delete(fileId=file_id).execute()
        return True
    except Exception as e:
        logger.error(f"[Drive] 삭제 실패: {e}")
        return False

"""
DB 모델 및 헬퍼 함수 (psycopg2 기반)
"""
import json
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from config import Config

# ============================================================
# DB 연결 풀
# ============================================================
from psycopg2 import pool

db_pool = pool.ThreadedConnectionPool(
    minconn=2,
    maxconn=10,
    dsn=Config.DATABASE_URL
)


@contextmanager
def get_db():
    """DB 커넥션 컨텍스트 매니저"""
    conn = db_pool.getconn()
    try:
        conn.autocommit = False
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        db_pool.putconn(conn)


def query_one(sql, params=None):
    """단일 행 조회"""
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def query_all(sql, params=None):
    """다중 행 조회"""
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def execute(sql, params=None):
    """INSERT/UPDATE/DELETE 실행, 반환값 있으면 반환"""
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            try:
                return cur.fetchone()
            except psycopg2.ProgrammingError:
                return None


# ============================================================
# User 모델
# ============================================================
class User:
    @staticmethod
    def find_by_google_id(google_id):
        return query_one("SELECT * FROM users WHERE google_id = %s", (google_id,))

    @staticmethod
    def find_by_id(user_id):
        return query_one("SELECT * FROM users WHERE id = %s", (user_id,))

    @staticmethod
    def create(google_id, email, name, avatar_url=None):
        return execute(
            """INSERT INTO users (google_id, email, name, avatar_url)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (google_id) DO UPDATE
               SET name = EXCLUDED.name, avatar_url = EXCLUDED.avatar_url
               RETURNING *""",
            (google_id, email, name, avatar_url)
        )

    @staticmethod
    def update_google_tokens(user_id, tokens):
        """Google OAuth 토큰 저장/갱신"""
        return execute(
            "UPDATE users SET google_tokens = %s WHERE id = %s RETURNING *",
            (json.dumps(tokens), user_id)
        )

    @staticmethod
    def get_google_tokens(user_id):
        """Google OAuth 토큰 조회"""
        result = query_one("SELECT google_tokens FROM users WHERE id = %s", (user_id,))
        return result['google_tokens'] if result else None

    @staticmethod
    def clear_google_tokens(user_id):
        """Google OAuth 토큰 삭제"""
        return execute(
            "UPDATE users SET google_tokens = NULL WHERE id = %s RETURNING *",
            (user_id,)
        )

    @staticmethod
    def delete_account(user_id):
        """회원 탈퇴 - CASCADE로 연관 데이터 모두 삭제"""
        return execute(
            "DELETE FROM users WHERE id = %s RETURNING id",
            (user_id,)
        )


# ============================================================
# Room 모델
# ============================================================
class Room:
    @staticmethod
    def create(name, description, created_by, invite_code):
        return execute(
            """INSERT INTO rooms (name, description, created_by, invite_code)
               VALUES (%s, %s, %s, %s) RETURNING *""",
            (name, description, created_by, invite_code)
        )

    @staticmethod
    def find_by_id(room_id):
        return query_one("SELECT * FROM rooms WHERE id = %s", (room_id,))

    @staticmethod
    def find_by_invite_code(code):
        return query_one("SELECT * FROM rooms WHERE invite_code = %s", (code,))

    @staticmethod
    def list_for_user(user_id):
        return query_all(
            """SELECT r.*, rm.role, rm.status as my_status,
                      COALESCE(rm.is_favorite, false) as is_favorite,
                      (SELECT COUNT(*) FROM room_members WHERE room_id = r.id AND status = 'active') as member_count,
                      (SELECT COUNT(*) FROM room_members WHERE room_id = r.id AND status = 'pending') as pending_count,
                      (SELECT content FROM messages WHERE room_id = r.id ORDER BY created_at DESC LIMIT 1) as last_message
               FROM rooms r
               JOIN room_members rm ON r.id = rm.room_id
               WHERE rm.user_id = %s
               ORDER BY COALESCE(rm.is_favorite, false) DESC, r.updated_at DESC""",
            (user_id,)
        )

    @staticmethod
    def add_member(room_id, user_id, role='member', status='active'):
        return execute(
            """INSERT INTO room_members (room_id, user_id, role, status)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (room_id, user_id) DO NOTHING
               RETURNING *""",
            (room_id, user_id, role, status)
        )

    @staticmethod
    def get_members(room_id):
        return query_all(
            """SELECT u.id, u.name, u.email, u.avatar_url, rm.role, rm.status, rm.joined_at
               FROM room_members rm
               JOIN users u ON rm.user_id = u.id
               WHERE rm.room_id = %s AND rm.status = 'active'
               ORDER BY rm.joined_at""",
            (room_id,)
        )

    @staticmethod
    def is_member(room_id, user_id):
        result = query_one(
            "SELECT 1 FROM room_members WHERE room_id = %s AND user_id = %s AND status = 'active'",
            (room_id, user_id)
        )
        return result is not None

    @staticmethod
    def get_member_status(room_id, user_id):
        """멤버의 role + status 조회 (pending 포함)"""
        return query_one(
            "SELECT role, status FROM room_members WHERE room_id = %s AND user_id = %s",
            (room_id, user_id)
        )

    @staticmethod
    def get_pending_members(room_id):
        """승인 대기 중 멤버 목록"""
        return query_all(
            """SELECT u.id, u.name, u.email, u.avatar_url, rm.joined_at
               FROM room_members rm
               JOIN users u ON rm.user_id = u.id
               WHERE rm.room_id = %s AND rm.status = 'pending'
               ORDER BY rm.joined_at""",
            (room_id,)
        )

    @staticmethod
    def approve_member(room_id, user_id):
        """멤버 승인: pending → active, joined_at 갱신"""
        return execute(
            """UPDATE room_members SET status = 'active', joined_at = NOW()
               WHERE room_id = %s AND user_id = %s AND status = 'pending'
               RETURNING *""",
            (room_id, user_id)
        )

    @staticmethod
    def reject_member(room_id, user_id):
        """멤버 거절: row 삭제 (재신청 가능)"""
        return execute(
            """DELETE FROM room_members
               WHERE room_id = %s AND user_id = %s AND status = 'pending'
               RETURNING *""",
            (room_id, user_id)
        )

    @staticmethod
    def update_drive_folder(room_id, drive_folder_id):
        """방의 Drive 폴더 ID 저장"""
        return execute(
            "UPDATE rooms SET drive_folder_id = %s WHERE id = %s RETURNING *",
            (drive_folder_id, room_id)
        )

    @staticmethod
    def delete(room_id):
        """방 삭제 (CASCADE로 messages, room_members 모두 삭제)"""
        return execute(
            "DELETE FROM rooms WHERE id = %s RETURNING id",
            (room_id,)
        )

    @staticmethod
    def rename(room_id, new_name):
        """방 이름 변경"""
        return execute(
            "UPDATE rooms SET name = %s, updated_at = NOW() WHERE id = %s RETURNING *",
            (new_name, room_id)
        )

    @staticmethod
    def remove_member(room_id, user_id):
        """멤버 스스로 나가기"""
        return execute(
            "DELETE FROM room_members WHERE room_id = %s AND user_id = %s RETURNING *",
            (room_id, user_id)
        )

    @staticmethod
    def get_admin_count(room_id):
        """방의 admin 수 조회"""
        result = query_one(
            "SELECT COUNT(*) as cnt FROM room_members WHERE room_id = %s AND role = 'admin' AND status = 'active'",
            (room_id,)
        )
        return result['cnt'] if result else 0

    @staticmethod
    def transfer_admin(room_id, new_admin_user_id):
        """관리자 권한 이전"""
        return execute(
            "UPDATE room_members SET role = 'admin' WHERE room_id = %s AND user_id = %s AND status = 'active' RETURNING *",
            (room_id, new_admin_user_id)
        )

    @staticmethod
    def toggle_favorite(room_id, user_id):
        """즐겨찾기 토글"""
        return execute(
            """UPDATE room_members SET is_favorite = NOT COALESCE(is_favorite, false)
               WHERE room_id = %s AND user_id = %s RETURNING is_favorite""",
            (room_id, user_id)
        )


# ============================================================
# Message 모델
# ============================================================
class Message:
    @staticmethod
    def create(room_id, user_id, msg_type, content, parent_id=None):
        return execute(
            """INSERT INTO messages (room_id, user_id, type, content, parent_id)
               VALUES (%s, %s, %s, %s, %s) RETURNING *""",
            (room_id, user_id, msg_type, content, parent_id)
        )

    @staticmethod
    def list_for_room(room_id, limit=50, before_id=None):
        if before_id:
            return query_all(
                """SELECT m.*, u.name as user_name, u.avatar_url as user_avatar,
                          af.id as audio_id, af.status as audio_status,
                          (SELECT json_agg(json_build_object(
                              'id', r.id, 'type', r.type, 'content', r.content,
                              'user_name', ru.name, 'created_at', r.created_at,
                              'audio_id', (SELECT af2.id FROM audio_files af2 WHERE af2.message_id = m.id LIMIT 1)
                          ) ORDER BY r.created_at)
                          FROM messages r JOIN users ru ON r.user_id = ru.id
                          WHERE r.parent_id = m.id) as replies
                   FROM messages m
                   JOIN users u ON m.user_id = u.id
                   LEFT JOIN audio_files af ON af.message_id = m.id
                   WHERE m.room_id = %s AND m.id < %s AND m.parent_id IS NULL
                   ORDER BY m.created_at DESC
                   LIMIT %s""",
                (room_id, before_id, limit)
            )
        return query_all(
            """SELECT m.*, u.name as user_name, u.avatar_url as user_avatar,
                      af.id as audio_id, af.status as audio_status,
                      (SELECT json_agg(json_build_object(
                          'id', r.id, 'type', r.type, 'content', r.content,
                          'user_name', ru.name, 'created_at', r.created_at,
                          'audio_id', (SELECT af2.id FROM audio_files af2 WHERE af2.message_id = m.id LIMIT 1)
                      ) ORDER BY r.created_at)
                      FROM messages r JOIN users ru ON r.user_id = ru.id
                      WHERE r.parent_id = m.id) as replies
               FROM messages m
               JOIN users u ON m.user_id = u.id
               LEFT JOIN audio_files af ON af.message_id = m.id
               WHERE m.room_id = %s AND m.parent_id IS NULL
               ORDER BY m.created_at DESC
               LIMIT %s""",
            (room_id, limit)
        )


    @staticmethod
    def delete(message_id):
        """메시지 삭제"""
        return execute(
            "DELETE FROM messages WHERE id = %s RETURNING *",
            (message_id,)
        )

    @staticmethod
    def get_replies(message_id):
        return query_all(
            """SELECT m.*, u.name as user_name, u.avatar_url as user_avatar
               FROM messages m
               JOIN users u ON m.user_id = u.id
               WHERE m.parent_id = %s
               ORDER BY m.created_at""",
            (message_id,)
        )


# ============================================================
# AudioFile 모델
# ============================================================
class AudioFile:
    @staticmethod
    def create(message_id, room_id, user_id, original_filename, file_size=0):
        return execute(
            """INSERT INTO audio_files
               (message_id, room_id, user_id, original_filename, file_size, status)
               VALUES (%s, %s, %s, %s, %s, 'uploading') RETURNING *""",
            (message_id, room_id, user_id, original_filename, file_size)
        )

    @staticmethod
    def update_parsed(audio_id, phone_number=None, record_date=None,
                      parsed_name=None, parsed_memo=None):
        return execute(
            """UPDATE audio_files
               SET phone_number = %s, record_date = %s,
                   parsed_name = %s, parsed_memo = %s
               WHERE id = %s RETURNING *""",
            (phone_number, record_date, parsed_name, parsed_memo, audio_id)
        )

    @staticmethod
    def update_transcript(audio_id, transcript_text, transcript_summary=None,
                          transcript_segments=None):
        return execute(
            """UPDATE audio_files
               SET transcript_text = %s, transcript_summary = %s,
                   transcript_segments = %s, status = 'completed', completed_at = NOW()
               WHERE id = %s RETURNING *""",
            (transcript_text, transcript_summary,
             json.dumps(transcript_segments) if transcript_segments else None,
             audio_id)
        )

    @staticmethod
    def update_drive(audio_id, drive_file_id, drive_url):
        return execute(
            """UPDATE audio_files
               SET drive_file_id = %s, drive_url = %s, drive_status = 'uploaded'
               WHERE id = %s RETURNING *""",
            (drive_file_id, drive_url, audio_id)
        )

    @staticmethod
    def update_status(audio_id, status, error_message=None):
        return execute(
            """UPDATE audio_files SET status = %s, error_message = %s
               WHERE id = %s RETURNING *""",
            (status, error_message, audio_id)
        )

    @staticmethod
    def update_drive_status(audio_id, drive_status):
        """Drive 업로드 상태 업데이트"""
        return execute(
            "UPDATE audio_files SET drive_status = %s WHERE id = %s RETURNING *",
            (drive_status, audio_id)
        )

    @staticmethod
    def find_by_id(audio_id):
        return query_one("SELECT * FROM audio_files WHERE id = %s", (audio_id,))

    @staticmethod
    def list_for_room(room_id, limit=50):
        return query_all(
            """SELECT af.*, u.name as user_name
               FROM audio_files af
               JOIN users u ON af.user_id = u.id
               WHERE af.room_id = %s
               ORDER BY af.created_at DESC
               LIMIT %s""",
            (room_id, limit)
        )

    @staticmethod
    def search(room_id=None, phone_number=None, date_from=None, date_to=None):
        """음성 파일 검색 (전화번호, 날짜 범위)"""
        conditions = []
        params = []

        if room_id:
            conditions.append("af.room_id = %s")
            params.append(room_id)
        if phone_number:
            conditions.append("af.phone_number LIKE %s")
            params.append(f"%{phone_number}%")
        if date_from:
            conditions.append("af.record_date >= %s")
            params.append(date_from)
        if date_to:
            conditions.append("af.record_date <= %s")
            params.append(date_to)

        where = " AND ".join(conditions) if conditions else "1=1"

        return query_all(
            f"""SELECT af.*, u.name as user_name
                FROM audio_files af
                JOIN users u ON af.user_id = u.id
                WHERE {where}
                ORDER BY af.created_at DESC
                LIMIT 100""",
            tuple(params)
        )


# ============================================================
# UserConsent 모델
# ============================================================
CURRENT_CONSENT_VERSION = '2026-03-01'

class UserConsent:
    @staticmethod
    def create(user_id, consent_type, version, ip_address=None, user_agent=None):
        return execute(
            """INSERT INTO user_consents (user_id, consent_type, version, agreed, agreed_at, ip_address, user_agent)
               VALUES (%s, %s, %s, true, NOW(), %s, %s) RETURNING *""",
            (user_id, consent_type, version, ip_address, user_agent)
        )

    @staticmethod
    def get_latest(user_id, consent_type):
        return query_one(
            """SELECT * FROM user_consents
               WHERE user_id = %s AND consent_type = %s AND agreed = true AND withdrawn_at IS NULL
               ORDER BY agreed_at DESC LIMIT 1""",
            (user_id, consent_type)
        )

    @staticmethod
    def has_valid_consent(user_id, consent_type, version=None):
        if version is None:
            version = CURRENT_CONSENT_VERSION
        result = query_one(
            """SELECT 1 FROM user_consents
               WHERE user_id = %s AND consent_type = %s AND version = %s
                     AND agreed = true AND withdrawn_at IS NULL
               LIMIT 1""",
            (user_id, consent_type, version)
        )
        return result is not None

    @staticmethod
    def get_all_for_user(user_id):
        return query_all(
            """SELECT DISTINCT ON (consent_type)
                      consent_type, version, agreed, agreed_at, withdrawn_at
               FROM user_consents
               WHERE user_id = %s
               ORDER BY consent_type, agreed_at DESC""",
            (user_id,)
        )

    @staticmethod
    def withdraw(user_id, consent_type):
        return execute(
            """UPDATE user_consents SET withdrawn_at = NOW()
               WHERE user_id = %s AND consent_type = %s AND withdrawn_at IS NULL
               RETURNING *""",
            (user_id, consent_type)
        )

    @staticmethod
    def check_required(user_id):
        """필수 동의 항목 중 미동의 항목 반환"""
        required_types = ['terms', 'privacy', 'overseas_transfer']
        missing = []
        for ct in required_types:
            if not UserConsent.has_valid_consent(user_id, ct):
                missing.append(ct)
        return missing


# ============================================================
# AccessLog 모델
# ============================================================
class AccessLog:
    @staticmethod
    def log(user_id, action, resource_type=None, resource_id=None,
            ip_address=None, user_agent=None, details=None):
        return execute(
            """INSERT INTO access_logs (user_id, action, resource_type, resource_id,
                                        ip_address, user_agent, details)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (user_id, action, resource_type, resource_id,
             ip_address, user_agent, json.dumps(details) if details else None)
        )

    @staticmethod
    def cleanup_old(days=90):
        """지정 일수 이상 된 로그 삭제"""
        return execute(
            "DELETE FROM access_logs WHERE created_at < NOW() - INTERVAL '%s days'",
            (days,)
        )

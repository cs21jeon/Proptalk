"""
채팅방 API 라우트
"""
import string
import random
import logging
from flask import request, jsonify, g
from auth import login_required, room_role_required
from models import Room, Message, User, AccessLog
from config import Config

logger = logging.getLogger(__name__)


def generate_invite_code(length=8):
    """초대 코드 생성"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))


def register_room_routes(app):

    @app.route('/api/rooms', methods=['GET'])
    @login_required
    def list_rooms():
        """내가 참여한 채팅방 목록"""
        rooms = Room.list_for_user(g.user_id)
        return jsonify({'rooms': rooms})


    @app.route('/api/rooms', methods=['POST'])
    @login_required
    def create_room():
        """
        채팅방 생성
        방장이 Drive 연동 되어있으면 Proptalk/{방이름} 폴더 자동 생성
        """
        data = request.get_json()
        name = data.get('name', '').strip()

        if not name:
            return jsonify({'error': '채팅방 이름이 필요합니다'}), 400

        description = data.get('description', '')
        invite_code = generate_invite_code()

        # 채팅방 생성
        room = Room.create(name, description, g.user_id, invite_code)

        # 생성자를 admin으로 추가
        Room.add_member(room['id'], g.user_id, role='admin')

        # 시스템 메시지
        Message.create(room['id'], g.user_id, 'system',
                       f'{g.user["name"]}님이 채팅방을 만들었습니다.')

        # Drive 폴더 생성 (방장이 Drive 연동된 경우)
        drive_folder_id = None
        if Config.ENABLE_GOOGLE_DRIVE_BACKUP:
            owner_tokens = User.get_google_tokens(g.user_id)
            if owner_tokens and owner_tokens.get('refresh_token'):
                try:
                    from drive_service import ensure_room_folder
                    folder_id, updated_tokens = ensure_room_folder(owner_tokens, name)
                    if folder_id:
                        Room.update_drive_folder(room['id'], folder_id)
                        drive_folder_id = folder_id
                        logger.info(f"[Drive] 방 폴더 생성: {name} → {folder_id}")

                    # 토큰이 갱신되었으면 DB 업데이트
                    if updated_tokens:
                        User.update_google_tokens(g.user_id, updated_tokens)
                except Exception as e:
                    logger.error(f"[Drive] 방 폴더 생성 실패: {e}")

        AccessLog.log(g.user_id, 'create_room', 'room', room['id'],
                      request.remote_addr, request.headers.get('User-Agent'),
                      details={'name': name})
        logger.info(f"채팅방 생성: {name} (by {g.user['email']}, drive_folder={drive_folder_id})")

        return jsonify({
            'room': room,
            'invite_code': invite_code,
        }), 201


    @app.route('/api/rooms/<int:room_id>', methods=['GET'])
    @login_required
    def get_room(room_id):
        """채팅방 상세 정보"""
        member_info = Room.get_member_status(room_id, g.user_id)
        if not member_info:
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        room = Room.find_by_id(room_id)
        if not room:
            return jsonify({'error': '채팅방을 찾을 수 없습니다'}), 404

        # pending 유저에게는 제한 정보만 반환
        if member_info['status'] == 'pending':
            return jsonify({
                'room': {'id': room['id'], 'name': room['name']},
                'my_status': 'pending',
            })

        members = Room.get_members(room_id)
        result = {
            'room': room,
            'members': members,
            'my_status': 'active',
        }

        # admin이면 pending 멤버도 반환
        if member_info['role'] == 'admin':
            result['pending_members'] = Room.get_pending_members(room_id)

        return jsonify(result)


    @app.route('/api/rooms/join', methods=['POST'])
    @login_required
    def join_room():
        """
        초대 코드로 채팅방 참여

        Request:
            { "invite_code": "ABC12345" }
        """
        data = request.get_json()
        code = data.get('invite_code', '').strip().upper()

        if not code:
            return jsonify({'error': '초대 코드가 필요합니다'}), 400

        room = Room.find_by_invite_code(code)
        if not room:
            return jsonify({'error': '유효하지 않은 초대 코드입니다'}), 404

        # 이미 멤버인지 확인 (active)
        if Room.is_member(room['id'], g.user_id):
            return jsonify({'room': room, 'message': '이미 참여한 채팅방입니다', 'status': 'active'})

        # 이미 pending인지 확인
        existing = Room.get_member_status(room['id'], g.user_id)
        if existing and existing['status'] == 'pending':
            return jsonify({'room': room, 'message': '승인 대기 중입니다', 'status': 'pending'})

        # pending 상태로 참여 신청
        Room.add_member(room['id'], g.user_id, role='member', status='pending')

        AccessLog.log(g.user_id, 'join_room', 'room', room['id'],
                      request.remote_addr, request.headers.get('User-Agent'))
        logger.info(f"채팅방 참여 신청: room={room['id']} user={g.user['email']} (pending)")

        return jsonify({
            'room': room,
            'status': 'pending',
            'message': '참여 신청이 완료되었습니다. 방장의 승인을 기다려 주세요.',
        })


    @app.route('/api/rooms/<int:room_id>/members', methods=['GET'])
    @login_required
    def get_room_members(room_id):
        """채팅방 멤버 목록"""
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        members = Room.get_members(room_id)
        return jsonify({'members': members})


    @app.route('/api/rooms/<int:room_id>/members/<int:user_id>', methods=['DELETE'])
    @login_required
    @room_role_required('admin')
    def remove_member(room_id, user_id):
        """멤버 추방 (admin 전용)"""
        # 자기 자신은 추방 불가
        if user_id == g.user_id:
            return jsonify({'error': '자기 자신은 추방할 수 없습니다'}), 400

        from models import execute
        result = execute(
            "DELETE FROM room_members WHERE room_id = %s AND user_id = %s RETURNING *",
            (room_id, user_id)
        )

        if not result:
            return jsonify({'error': '멤버를 찾을 수 없습니다'}), 404

        # 시스템 메시지
        removed_user = User.find_by_id(user_id)
        removed_name = removed_user['name'] if removed_user else '알 수 없는 사용자'
        Message.create(room_id, g.user_id, 'system',
                       f'{removed_name}님이 퇴장되었습니다.')

        AccessLog.log(g.user_id, 'remove_member', 'room', room_id,
                      request.remote_addr, request.headers.get('User-Agent'),
                      details={'removed_user_id': user_id})

        logger.info(f"멤버 추방: room={room_id}, user={user_id}, by={g.user_id}")
        return jsonify({'success': True})


    @app.route('/api/rooms/<int:room_id>/members/pending', methods=['GET'])
    @login_required
    @room_role_required('admin')
    def get_pending_members(room_id):
        """승인 대기 멤버 목록 (admin 전용)"""
        pending = Room.get_pending_members(room_id)
        return jsonify({'pending_members': pending})


    @app.route('/api/rooms/<int:room_id>/members/<int:user_id>/approve', methods=['POST'])
    @login_required
    @room_role_required('admin')
    def approve_member(room_id, user_id):
        """멤버 승인 (admin 전용)"""
        result = Room.approve_member(room_id, user_id)
        if not result:
            return jsonify({'error': '승인 대기 멤버를 찾을 수 없습니다'}), 404

        # 시스템 메시지
        approved_user = User.find_by_id(user_id)
        approved_name = approved_user['name'] if approved_user else '알 수 없는 사용자'
        Message.create(room_id, g.user_id, 'system',
                       f'{approved_name}님의 참여가 승인되었습니다.')

        AccessLog.log(g.user_id, 'approve_member', 'room', room_id,
                      request.remote_addr, request.headers.get('User-Agent'),
                      details={'approved_user_id': user_id})

        logger.info(f"멤버 승인: room={room_id}, user={user_id}, by={g.user_id}")
        return jsonify({'success': True, 'message': f'{approved_name}님이 승인되었습니다.'})


    @app.route('/api/rooms/<int:room_id>/members/<int:user_id>/reject', methods=['POST'])
    @login_required
    @room_role_required('admin')
    def reject_member(room_id, user_id):
        """멤버 거절 (admin 전용) — row 삭제하여 재신청 가능"""
        result = Room.reject_member(room_id, user_id)
        if not result:
            return jsonify({'error': '승인 대기 멤버를 찾을 수 없습니다'}), 404

        AccessLog.log(g.user_id, 'reject_member', 'room', room_id,
                      request.remote_addr, request.headers.get('User-Agent'),
                      details={'rejected_user_id': user_id})

        logger.info(f"멤버 거절: room={room_id}, user={user_id}, by={g.user_id}")
        return jsonify({'success': True})


    @app.route('/api/rooms/<int:room_id>', methods=['DELETE'])
    @login_required
    @room_role_required('admin')
    def delete_room(room_id):
        """채팅방 삭제 (admin 전용, CASCADE)"""
        room = Room.find_by_id(room_id)
        if not room:
            return jsonify({'error': '채팅방을 찾을 수 없습니다'}), 404

        Room.delete(room_id)

        AccessLog.log(g.user_id, 'delete_room', 'room', room_id,
                      request.remote_addr, request.headers.get('User-Agent'),
                      details={'name': room['name']})
        logger.info(f"채팅방 삭제: room={room_id}, name={room['name']}, by={g.user_id}")
        return jsonify({'success': True})


    @app.route('/api/rooms/<int:room_id>', methods=['PATCH'])
    @login_required
    @room_role_required('admin')
    def rename_room(room_id):
        """채팅방 이름 변경 (admin 전용)"""
        data = request.get_json()
        new_name = data.get('name', '').strip()
        if not new_name:
            return jsonify({'error': '새 이름이 필요합니다'}), 400

        room = Room.rename(room_id, new_name)
        if not room:
            return jsonify({'error': '채팅방을 찾을 수 없습니다'}), 404

        Message.create(room_id, g.user_id, 'system',
                       f'채팅방 이름이 "{new_name}"(으)로 변경되었습니다.')

        logger.info(f"채팅방 이름 변경: room={room_id}, new_name={new_name}, by={g.user_id}")
        return jsonify({'room': room})


    @app.route('/api/rooms/<int:room_id>/leave', methods=['POST'])
    @login_required
    def leave_room(room_id):
        """채팅방 나가기"""
        member = Room.get_member_status(room_id, g.user_id)
        if not member:
            return jsonify({'error': '멤버가 아닙니다'}), 404

        # admin이 나가려면 다른 admin이 있어야 함
        if member['role'] == 'admin':
            admin_count = Room.get_admin_count(room_id)
            if admin_count <= 1:
                members = Room.get_members(room_id)
                other_members = [m for m in members if m['id'] != g.user_id]
                if other_members:
                    return jsonify({
                        'error': '유일한 관리자입니다. 다른 멤버에게 관리자를 넘기거나 방을 삭제해주세요.',
                        'need_transfer': True,
                    }), 400
                else:
                    # 마지막 멤버이면 방 자체를 삭제
                    Room.delete(room_id)
                    logger.info(f"마지막 관리자 퇴장으로 방 삭제: room={room_id}")
                    return jsonify({'success': True, 'room_deleted': True})

        Room.remove_member(room_id, g.user_id)

        Message.create(room_id, g.user_id, 'system',
                       f'{g.user["name"]}님이 나갔습니다.')

        logger.info(f"채팅방 퇴장: room={room_id}, user={g.user_id}")
        return jsonify({'success': True})


    @app.route('/api/rooms/<int:room_id>/transfer-admin', methods=['POST'])
    @login_required
    @room_role_required('admin')
    def transfer_admin(room_id):
        """관리자 권한 이전"""
        data = request.get_json()
        new_admin_id = data.get('user_id')
        if not new_admin_id:
            return jsonify({'error': 'user_id가 필요합니다'}), 400

        result = Room.transfer_admin(room_id, new_admin_id)
        if not result:
            return jsonify({'error': '해당 멤버를 찾을 수 없습니다'}), 404

        from models import execute as db_execute
        db_execute(
            "UPDATE room_members SET role = 'member' WHERE room_id = %s AND user_id = %s",
            (room_id, g.user_id)
        )

        new_admin = User.find_by_id(new_admin_id)
        new_admin_name = new_admin['name'] if new_admin else '알 수 없는 사용자'
        Message.create(room_id, g.user_id, 'system',
                       f'관리자가 {new_admin_name}님에게 이전되었습니다.')

        logger.info(f"관리자 이전: room={room_id}, new_admin={new_admin_id}, by={g.user_id}")
        return jsonify({'success': True})


    @app.route('/api/rooms/<int:room_id>/favorite', methods=['POST'])
    @login_required
    def toggle_favorite(room_id):
        """즐겨찾기 토글"""
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '멤버가 아닙니다'}), 403

        result = Room.toggle_favorite(room_id, g.user_id)
        is_favorite = result['is_favorite'] if result else False

        return jsonify({'success': True, 'is_favorite': is_favorite})

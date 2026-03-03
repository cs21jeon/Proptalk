"""
메시지 / 음성파일 API 라우트
핵심: 음성 업로드 → Whisper STT 변환 → Claude 요약 → 자동 댓글 → Drive 저장
"""
import os
import uuid
import time
import shutil
import logging
import threading
from flask import request, jsonify, g, send_file, Response
from werkzeug.utils import secure_filename
from auth import login_required
from models import Room, Message, AudioFile, User, AccessLog
from config import Config

logger = logging.getLogger(__name__)

def _serialize_msg(msg):
    """메시지 dict의 datetime을 ISO 문자열로 변환"""
    result = {}
    for k, v in msg.items():
        if hasattr(v, 'isoformat'):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result



def transcribe_with_whisper(filepath: str, language: str = 'ko') -> dict:
    """OpenAI Whisper API로 음성 변환"""
    from whisper_service import transcribe_audio
    return transcribe_audio(filepath, language)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def register_message_routes(app, socketio):

    @app.route('/api/rooms/<int:room_id>/messages', methods=['GET'])
    @login_required
    def get_messages(room_id):
        """채팅방 메시지 목록"""
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        before_id = request.args.get('before_id', type=int)
        limit = request.args.get('limit', 50, type=int)

        messages = Message.list_for_room(room_id, limit=limit, before_id=before_id)
        return jsonify({'messages': messages})


    @app.route('/api/rooms/<int:room_id>/messages', methods=['POST'])
    @login_required
    def send_message(room_id):
        """텍스트 메시지 전송"""
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        data = request.get_json()
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')

        if not content:
            return jsonify({'error': '메시지 내용이 필요합니다'}), 400

        msg = Message.create(room_id, g.user_id, 'text', content, parent_id)

        socketio.emit('new_message', {
            'message': {
                **_serialize_msg(msg),
                'user_name': g.user['name'],
                'user_avatar': g.user.get('avatar_url'),
            }
        }, room=f'room_{room_id}')

        return jsonify({'message': msg}), 201


    @app.route('/api/rooms/<int:room_id>/audio', methods=['POST'])
    @login_required
    def upload_audio(room_id):
        """음성 파일 업로드 → Whisper STT → 자동 댓글"""
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        if 'file' not in request.files:
            return jsonify({'error': '파일이 없습니다'}), 400

        file = request.files['file']
        if not file.filename or not allowed_file(file.filename):
            return jsonify({'error': '허용되지 않는 파일 형식입니다'}), 400

        language = request.form.get('language', 'ko')
        original_filename = file.filename

        file_id = str(uuid.uuid4())
        ext = original_filename.rsplit('.', 1)[1].lower()
        saved_filename = f"{file_id}.{ext}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, saved_filename)

        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        file.save(filepath)
        file_size = os.path.getsize(filepath)

        msg = Message.create(room_id, g.user_id, 'audio', f'🎙️ {original_filename}')
        audio = AudioFile.create(msg['id'], room_id, g.user_id, original_filename, file_size)

        socketio.emit('new_message', {
            'message': {
                **_serialize_msg(msg),
                'user_name': g.user['name'],
                'user_avatar': g.user.get('avatar_url'),
                'audio_id': audio['id'],
                'audio_status': 'uploading',
            }
        }, room=f'room_{room_id}')

        # 방장 토큰 조회
        room = Room.find_by_id(room_id)
        owner_tokens = None
        room_drive_folder_id = None
        if room and Config.ENABLE_GOOGLE_DRIVE_BACKUP:
            owner = User.find_by_id(room['created_by'])
            if owner and owner.get('google_tokens'):
                owner_tokens = owner['google_tokens']
            room_drive_folder_id = room.get('drive_folder_id')

        # 감사 로그
        AccessLog.log(g.user_id, 'upload', 'audio', audio['id'],
                      request.remote_addr, request.headers.get('User-Agent'),
                      details={'filename': original_filename, 'room_id': room_id, 'file_size': file_size})

        thread = threading.Thread(
            target=process_audio_background,
            args=(app, socketio, filepath, audio['id'], msg['id'], room_id,
                  g.user_id, g.user['name'], original_filename, language,
                  owner_tokens, room['name'] if room else 'Unknown',
                  room.get('created_by') if room else None,
                  room_drive_folder_id)
        )
        thread.daemon = True
        thread.start()

        return jsonify({'message': msg, 'audio': audio, 'status': '변환을 시작합니다...'}), 201


    @app.route('/api/rooms/<int:room_id>/audio/search', methods=['GET'])
    @login_required
    def search_audio(room_id):
        """음성 파일 검색"""
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        phone = request.args.get('phone')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        results = AudioFile.search(room_id=room_id, phone_number=phone, date_from=date_from, date_to=date_to)
        return jsonify({'audio_files': results})


    @app.route('/api/audio/<int:audio_id>', methods=['GET'])
    @login_required
    def get_audio_detail(audio_id):
        """음성 파일 상세"""
        audio = AudioFile.find_by_id(audio_id)
        if not audio:
            return jsonify({'error': '파일을 찾을 수 없습니다'}), 404

        if not Room.is_member(audio['room_id'], g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        return jsonify({'audio': audio})

    @app.route('/api/audio/<int:audio_id>/download', methods=['GET'])
    @login_required
    def download_audio(audio_id):
        """음성 파일 다운로드 (로컬 → Drive 프록시 fallback)"""
        audio = AudioFile.find_by_id(audio_id)
        if not audio:
            return jsonify({'error': '파일을 찾을 수 없습니다'}), 404

        if not Room.is_member(audio['room_id'], g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        # 감사 로그
        AccessLog.log(g.user_id, 'download', 'audio', audio_id,
                      request.remote_addr, request.headers.get('User-Agent'),
                      details={'room_id': audio['room_id']})

        original_filename = audio['original_filename']
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'mp3'

        # 1) 로컬 파일 확인
        filepath = os.path.join(Config.AUDIO_FOLDER, f"{audio['id']}.{ext}")
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True, download_name=original_filename)

        # 2) Drive에서 프록시 다운로드
        drive_file_id = audio.get('drive_file_id')
        if drive_file_id:
            try:
                room = Room.find_by_id(audio['room_id'])
                if room:
                    owner = User.find_by_id(room['created_by'])
                    if owner:
                        owner_tokens = User.get_google_tokens(owner['id'])
                        if owner_tokens:
                            from drive_service import download_from_drive
                            file_data, updated_tokens = download_from_drive(owner_tokens, drive_file_id)

                            # 토큰이 갱신되었으면 저장
                            if updated_tokens:
                                User.update_google_tokens(owner['id'], updated_tokens)

                            mime_types = {
                                'mp3': 'audio/mpeg', 'wav': 'audio/wav',
                                'm4a': 'audio/mp4', 'ogg': 'audio/ogg',
                                'flac': 'audio/flac', '3gp': 'audio/3gpp',
                            }
                            mime_type = mime_types.get(ext, 'audio/mpeg')

                            return Response(file_data, mimetype=mime_type,
                                headers={'Content-Disposition': f'attachment; filename="{original_filename}"'})
            except Exception as e:
                logger.error(f"[Drive] 프록시 다운로드 실패: {e}")

        return jsonify({'error': '파일이 만료되었거나 존재하지 않습니다'}), 404


def process_audio_background(app, socketio, filepath, audio_id, message_id,
                              room_id, user_id, user_name, original_filename, language,
                              owner_tokens=None, room_name='Unknown',
                              owner_id=None, room_drive_folder_id=None):
    """백그라운드에서 음성 파일 처리"""
    with app.app_context():
        try:
            logger.info(f"[STT] 처리 시작: audio_id={audio_id}, file={original_filename}")

            # 1) 파일명 파싱
            from filename_parser import parse_filename
            parsed = parse_filename(original_filename)

            AudioFile.update_parsed(
                audio_id,
                phone_number=parsed.get('phone_number'),
                record_date=parsed.get('record_date'),
                parsed_name=parsed.get('name'),
                parsed_memo=parsed.get('memo')
            )

            parsed_info = []
            if parsed.get('phone_number'):
                phone = parsed['phone_number']
                if len(phone) == 11:
                    phone = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
                parsed_info.append(f"📞 {phone}")
            if parsed.get('record_date'):
                parsed_info.append(f"📅 {parsed['record_date']}")
            if parsed.get('name'):
                parsed_info.append(f"👤 {parsed['name']}")

            if parsed_info:
                info_text = "\n".join(parsed_info)
                file_info_content = "📋 파일 정보\n" + info_text
                info_msg = Message.create(room_id, user_id, 'system', file_info_content, parent_id=message_id)
                socketio.emit('new_message', {
                    'message': {**_serialize_msg(info_msg), 'user_name': '시스템'}
                }, room=f'room_{room_id}')

            # 2) Whisper STT
            AudioFile.update_status(audio_id, 'transcribing')

            progress_msg = Message.create(room_id, user_id, 'system', "⏳ 내용 정리 중입니다...", parent_id=message_id)
            socketio.emit('new_message', {
                'message': {**_serialize_msg(progress_msg), 'user_name': '시스템'}
            }, room=f'room_{room_id}')

            socketio.emit('audio_status', {
                'audio_id': audio_id,
                'message_id': message_id,
                'status': 'transcribing',
            }, room=f'room_{room_id}')

            start_time = time.time()
            result = transcribe_with_whisper(filepath, language)

            elapsed = time.time() - start_time
            transcript_text = result['text']
            segments = result.get('segments', [])

            logger.info(f"[STT] Whisper 변환 완료: {elapsed:.1f}초, {len(transcript_text)}자")

            # 3) Claude 요약
            summary_text = None
            try:
                from claude_service import summarize_transcript
                socketio.emit('audio_status', {
                    'audio_id': audio_id,
                    'message_id': message_id,
                    'status': 'summarizing',
                }, room=f'room_{room_id}')

                summary_text = summarize_transcript(transcript_text, language)
                if summary_text:
                    logger.info(f"[Claude] 요약 완료: {len(summary_text)}자")
            except Exception as e:
                logger.error(f"[Claude] 요약 실패: {e}")

            AudioFile.update_transcript(audio_id, transcript_text,
                                        transcript_summary=summary_text,
                                        transcript_segments=segments)

            # 4) 자동 댓글
            # 진행 메시지 삭제
            try:
                Message.delete(progress_msg['id'])
                socketio.emit('delete_message', {
                    'message_id': progress_msg['id'],
                    'room_id': room_id,
                }, room=f'room_{room_id}')
            except Exception as e:
                logger.warning(f"[cleanup] 진행 메시지 삭제 실패: {e}")

            # 5) Drive 업로드
            drive_uploaded = False
            if owner_tokens and Config.ENABLE_GOOGLE_DRIVE_BACKUP:
                try:
                    from drive_service import upload_to_drive
                    AudioFile.update_drive_status(audio_id, 'uploading')

                    drive_result = upload_to_drive(
                        owner_tokens, filepath, room_name,
                        room_folder_id=room_drive_folder_id
                    )

                    if drive_result:
                        AudioFile.update_drive(
                            audio_id,
                            drive_result['file_id'],
                            drive_result.get('web_link', '')
                        )
                        drive_uploaded = True
                        logger.info(f"[Drive] 업로드 성공: {drive_result['file_id']}")

                        # 토큰 갱신 시 DB 업데이트
                        if drive_result.get('updated_tokens') and owner_id:
                            User.update_google_tokens(owner_id, drive_result['updated_tokens'])

                        # 방의 drive_folder_id 캐시 (아직 없으면)
                        if not room_drive_folder_id and drive_result.get('folder_id'):
                            Room.update_drive_folder(room_id, drive_result['folder_id'])

                except Exception as e:
                    logger.error(f"[Drive] 업로드 실패 (fallback 로컬 보관): {e}")
                    AudioFile.update_drive_status(audio_id, 'failed')

            # 6) 댓글 내용 결정
            if drive_uploaded:
                # Drive에 저장됨 → 영구 보관
                if summary_text:
                    reply_content = f"{summary_text}\n\n---\n\n☁️ **Google Drive에 저장되었습니다.**"
                else:
                    reply_content = "📝 음성 변환 완료\n\n요약을 생성하지 못했습니다.\n\n---\n\n☁️ **Google Drive에 저장되었습니다.**"
            else:
                # Drive 없음 → 서버 보관 (24시간)
                if summary_text:
                    reply_content = f"{summary_text}\n\n---\n\n⚠️ **{Config.AUDIO_RETENTION_HOURS}시간 후 파일이 삭제됩니다.** 저장이 필요하면 다운로드하세요."
                else:
                    reply_content = f"📝 음성 변환 완료\n\n요약을 생성하지 못했습니다.\n\n---\n\n⚠️ **{Config.AUDIO_RETENTION_HOURS}시간 후 파일이 삭제됩니다.** 저장이 필요하면 다운로드하세요."

            reply_msg = Message.create(room_id, user_id, 'transcript', reply_content, parent_id=message_id)

            socketio.emit('new_message', {
                'message': {
                    **_serialize_msg(reply_msg),
                    'user_name': '🤖 자동 변환',
                    'audio_id': audio_id,
                    'can_download': True,
                }
            }, room=f'room_{room_id}')

            socketio.emit('audio_status', {
                'audio_id': audio_id,
                'message_id': message_id,
                'status': 'completed',
                'transcript_preview': transcript_text[:100],
                'has_summary': summary_text is not None,
                'drive_uploaded': drive_uploaded,
            }, room=f'room_{room_id}')

            # 7) 파일 보관 처리
            ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'mp3'
            audio_folder = Config.AUDIO_FOLDER
            os.makedirs(audio_folder, exist_ok=True)
            permanent_path = os.path.join(audio_folder, f"{audio_id}.{ext}")

            if drive_uploaded:
                # Drive에 저장 완료 → 서버 파일 삭제
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    logger.info(f"[파일] 서버 삭제 (Drive 저장됨): {filepath}")
                except Exception as e:
                    logger.warning(f"[파일] 서버 삭제 실패: {e}")
                    # 삭제 실패 시 로컬 보관 fallback
                    if os.path.exists(filepath):
                        shutil.move(filepath, permanent_path)
            else:
                # Drive 없음 → 로컬 보관 (cleanup_service가 24시간 후 삭제)
                shutil.move(filepath, permanent_path)
                logger.info(f"[파일] 로컬 보관: {permanent_path}")

        except Exception as e:
            logger.error(f"[STT] 처리 실패: {e}", exc_info=True)
            AudioFile.update_status(audio_id, 'failed', str(e))

            socketio.emit('audio_status', {
                'audio_id': audio_id,
                'message_id': message_id,
                'status': 'failed',
                'error': str(e),
            }, room=f'room_{room_id}')

            Message.create(room_id, user_id, 'system', f'⚠️ 음성 변환 실패: {str(e)[:100]}', parent_id=message_id)

            if os.path.exists(filepath):
                os.remove(filepath)

"""
메시지 / 음성파일 API 라우트
핵심: 음성 업로드 → STT 변환 → Claude 요약 → 자동 댓글
"""
import os
import uuid
import time
import shutil
import logging
import threading
from flask import request, jsonify, g, send_file
from werkzeug.utils import secure_filename
from auth import login_required
from models import Room, Message, AudioFile
from config import Config

logger = logging.getLogger(__name__)

# Whisper 모델 (지연 로딩)
_whisper_model = None


def get_whisper_model():
    """Whisper 모델 싱글턴"""
    global _whisper_model
    if _whisper_model is None:
        import whisper
        logger.info(f"Whisper 모델 로딩: {Config.WHISPER_MODEL}")
        _whisper_model = whisper.load_model(Config.WHISPER_MODEL, device='cpu')
        logger.info("Whisper 모델 로딩 완료")
    return _whisper_model


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def register_message_routes(app, socketio):
    
    # ============================================================
    # 텍스트 메시지
    # ============================================================
    @app.route('/api/rooms/<int:room_id>/messages', methods=['GET'])
    @login_required
    def get_messages(room_id):
        """채팅방 메시지 목록 (페이지네이션)"""
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403
        
        before_id = request.args.get('before_id', type=int)
        limit = request.args.get('limit', 50, type=int)
        
        messages = Message.list_for_room(room_id, limit=limit, before_id=before_id)
        return jsonify({'messages': messages})
    
    
    @app.route('/api/rooms/<int:room_id>/messages', methods=['POST'])
    @login_required
    def send_message(room_id):
        """
        텍스트 메시지 전송
        
        Request:
            { "content": "메시지 내용", "parent_id": null }
        """
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403
        
        data = request.get_json()
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')
        
        if not content:
            return jsonify({'error': '메시지 내용이 필요합니다'}), 400
        
        msg = Message.create(room_id, g.user_id, 'text', content, parent_id)
        
        # WebSocket으로 실시간 전송
        socketio.emit('new_message', {
            'message': {
                **msg,
                'user_name': g.user['name'],
                'user_avatar': g.user.get('avatar_url'),
            }
        }, room=f'room_{room_id}')
        
        return jsonify({'message': msg}), 201
    
    
    # ============================================================
    # 음성 파일 업로드 + 자동 STT
    # ============================================================
    @app.route('/api/rooms/<int:room_id>/audio', methods=['POST'])
    @login_required
    def upload_audio(room_id):
        """
        음성 파일 업로드 → 자동 STT 변환 → 자동 댓글
        
        Request: multipart/form-data
            - file: 음성 파일
            - language: 언어코드 (기본: ko)
        """
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        # 과금: 방장(room owner)에게 부과
        room = Room.find_by_id(room_id)
        owner_id = room['created_by']
        from billing_service import check_can_transcribe, ensure_user_billing, get_audio_duration_fast
        ensure_user_billing(owner_id)
        can_use, reason = check_can_transcribe(owner_id)
        if not can_use:
            return jsonify({'error': reason, 'code': 'INSUFFICIENT_BALANCE'}), 402

        if 'file' not in request.files:
            return jsonify({'error': '파일이 없습니다'}), 400

        file = request.files['file']
        if not file.filename or not allowed_file(file.filename):
            return jsonify({'error': '허용되지 않는 파일 형식입니다'}), 400

        language = request.form.get('language', 'ko')
        original_filename = file.filename

        # 1) 파일 저장
        file_id = str(uuid.uuid4())
        ext = original_filename.rsplit('.', 1)[1].lower()
        saved_filename = f"{file_id}.{ext}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, saved_filename)

        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        file.save(filepath)
        file_size = os.path.getsize(filepath)

        # 과금: 파일 길이 vs 방장 잔여 시간 비교 (2차 — 부족 시 차단)
        audio_duration = get_audio_duration_fast(filepath)
        if audio_duration:
            can_use, reason = check_can_transcribe(owner_id, audio_duration_seconds=audio_duration)
            if not can_use:
                os.remove(filepath)
                return jsonify({'error': reason, 'code': 'INSUFFICIENT_BALANCE'}), 402

        # 2) 음성 메시지 생성 (채팅에 표시)
        msg = Message.create(
            room_id, g.user_id, 'audio',
            f'🎙️ {original_filename}'
        )
        
        # 3) audio_files 레코드 생성
        audio = AudioFile.create(
            msg['id'], room_id, g.user_id, original_filename, file_size
        )
        
        # 4) WebSocket으로 음성 메시지 전송
        socketio.emit('new_message', {
            'message': {
                **msg,
                'user_name': g.user['name'],
                'user_avatar': g.user.get('avatar_url'),
                'audio_id': audio['id'],
                'audio_status': 'uploading',
            }
        }, room=f'room_{room_id}')
        
        # 5) 백그라운드에서 STT + Drive 업로드 처리
        thread = threading.Thread(
            target=process_audio_background,
            args=(app._get_current_object(), socketio,
                  filepath, audio['id'], msg['id'], room_id,
                  g.user_id, g.user['name'], original_filename, language,
                  owner_id)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': msg,
            'audio': audio,
            'status': '변환을 시작합니다...'
        }), 201
    
    
    # ============================================================
    # 음성 파일 검색
    # ============================================================
    @app.route('/api/rooms/<int:room_id>/audio/search', methods=['GET'])
    @login_required
    def search_audio(room_id):
        """
        음성 파일 검색 (전화번호, 날짜)
        
        Query params:
            - phone: 전화번호 (부분 일치)
            - date_from: 시작일 (YYYY-MM-DD)
            - date_to: 종료일 (YYYY-MM-DD)
        """
        if not Room.is_member(room_id, g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403
        
        phone = request.args.get('phone')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        results = AudioFile.search(
            room_id=room_id,
            phone_number=phone,
            date_from=date_from,
            date_to=date_to
        )
        
        return jsonify({'audio_files': results})
    
    
    # ============================================================
    # 음성 파일 상세
    # ============================================================
    @app.route('/api/audio/<int:audio_id>', methods=['GET'])
    @login_required
    def get_audio_detail(audio_id):
        """음성 파일 상세 정보 (변환 결과 포함)"""
        audio = AudioFile.find_by_id(audio_id)
        if not audio:
            return jsonify({'error': '파일을 찾을 수 없습니다'}), 404

        if not Room.is_member(audio['room_id'], g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        return jsonify({'audio': audio})

    # ============================================================
    # 음성 파일 다운로드
    # ============================================================
    @app.route('/api/audio/<int:audio_id>/download', methods=['GET'])
    @login_required
    def download_audio(audio_id):
        """
        음성 파일 다운로드
        24시간 내에만 다운로드 가능
        """
        audio = AudioFile.find_by_id(audio_id)
        if not audio:
            return jsonify({'error': '파일을 찾을 수 없습니다'}), 404

        if not Room.is_member(audio['room_id'], g.user_id):
            return jsonify({'error': '접근 권한이 없습니다'}), 403

        # 파일 경로 확인
        original_filename = audio['original_filename']
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'mp3'
        filepath = os.path.join(Config.AUDIO_FOLDER, f"{audio_id}.{ext}")

        if not os.path.exists(filepath):
            return jsonify({'error': '파일이 만료되었거나 존재하지 않습니다'}), 404

        return send_file(
            filepath,
            as_attachment=True,
            download_name=original_filename
        )


# ============================================================
# 백그라운드 STT 처리
# ============================================================
def process_audio_background(app, socketio, filepath, audio_id, message_id,
                              room_id, user_id, user_name, original_filename, language,
                              owner_id=None):
    """
    백그라운드에서 음성 파일 처리:
    1. 파일명에서 전화번호/날짜 파싱
    2. Whisper로 STT 변환
    3. Claude API로 핵심 요약
    4. 요약 + 다운로드 안내를 자동 댓글로 달기
    5. 파일을 24시간 보관 폴더로 이동
    6. (선택) Google Drive에 백업 저장
    """
    with app.app_context():
        try:
            logger.info(f"[STT] 처리 시작: audio_id={audio_id}, file={original_filename}")

            # --- 1단계: 파일명 AI 파싱 ---
            from filename_parser import parse_filename
            parsed = parse_filename(original_filename)

            AudioFile.update_parsed(
                audio_id,
                phone_number=parsed.get('phone_number'),
                record_date=parsed.get('record_date'),
                parsed_name=parsed.get('name'),
                parsed_memo=parsed.get('memo')
            )

            # 파싱 결과 알림
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
                info_text = ' | '.join(parsed_info)
                info_msg = Message.create(
                    room_id, user_id, 'system',
                    f"파일 정보: {info_text}",
                    parent_id=message_id
                )
                socketio.emit('new_message', {
                    'message': {**info_msg, 'user_name': '시스템'}
                }, room=f'room_{room_id}')

            # --- 2단계: STT 변환 ---
            AudioFile.update_status(audio_id, 'transcribing')
            socketio.emit('audio_status', {
                'audio_id': audio_id,
                'message_id': message_id,
                'status': 'transcribing',
            }, room=f'room_{room_id}')

            model = get_whisper_model()
            start_time = time.time()

            result = model.transcribe(
                filepath,
                language=language if language != 'auto' else None,
                task='transcribe',
                verbose=False,
                fp16=False,
                condition_on_previous_text=True,
                initial_prompt="이것은 한국어 음성입니다." if language == 'ko' else None,
            )

            elapsed = time.time() - start_time
            transcript_text = result['text'].strip()

            # 세그먼트 정리
            segments = []
            for seg in result.get('segments', []):
                segments.append({
                    'start': round(seg['start'], 2),
                    'end': round(seg['end'], 2),
                    'text': seg['text'].strip(),
                })

            # 음성 길이(초) 추출 + duration_seconds DB 기록
            from billing_service import extract_audio_duration, deduct_usage
            duration_seconds = extract_audio_duration(result.get('segments', []))
            if duration_seconds > 0:
                from models import execute as db_execute
                db_execute(
                    "UPDATE audio_files SET duration_seconds = %s WHERE id = %s",
                    (duration_seconds, audio_id)
                )

            logger.info(f"[STT] 변환 완료: {elapsed:.1f}초, {len(transcript_text)}자, 음성길이={duration_seconds:.1f}초")

            # 과금: 방장(owner)에게 사용량 차감
            billing_user_id = owner_id or user_id
            if duration_seconds > 0:
                deduct_result = deduct_usage(billing_user_id, audio_id, duration_seconds)
                if deduct_result:
                    logger.info(f"[Billing] 차감 완료: 잔여 {deduct_result['seconds_after']:.0f}초")

            # --- 3단계: Claude API 요약 ---
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
                logger.error(f"[Claude] 요약 실패 (STT는 완료됨): {e}")

            # DB 업데이트
            AudioFile.update_transcript(audio_id, transcript_text,
                                        transcript_summary=summary_text,
                                        transcript_segments=segments)

            # --- 4단계: 자동 댓글 (요약 + 다운로드 안내) ---
            if summary_text:
                reply_content = (
                    f"📝 **통화 요약**\n\n"
                    f"{summary_text}\n\n"
                    f"───────────────────\n\n"
                    f"⚠️ **{Config.AUDIO_RETENTION_HOURS}시간 후 파일 삭제됩니다.**\n"
                    f"저장이 필요하면 지금 다운로드 받으세요."
                )
            else:
                # 요약 실패 시 원본 텍스트 표시
                preview = transcript_text[:300] + '...' if len(transcript_text) > 300 else transcript_text
                reply_content = (
                    f"📝 **음성 변환 결과**\n\n"
                    f"{preview}\n\n"
                    f"───────────────────\n\n"
                    f"⚠️ **{Config.AUDIO_RETENTION_HOURS}시간 후 파일 삭제됩니다.**\n"
                    f"저장이 필요하면 지금 다운로드 받으세요."
                )

            reply_msg = Message.create(
                room_id, user_id, 'transcript',
                reply_content,
                parent_id=message_id
            )

            socketio.emit('new_message', {
                'message': {
                    **reply_msg,
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
            }, room=f'room_{room_id}')

            # --- 5단계: 파일을 보관 폴더로 이동 (24시간 보관) ---
            ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'mp3'
            audio_folder = Config.AUDIO_FOLDER
            os.makedirs(audio_folder, exist_ok=True)
            permanent_path = os.path.join(audio_folder, f"{audio_id}.{ext}")

            shutil.move(filepath, permanent_path)
            logger.info(f"[파일] 보관 폴더로 이동: {permanent_path}")

            # --- 6단계: (선택) Google Drive 업로드 ---
            if Config.ENABLE_GOOGLE_DRIVE_BACKUP:
                try:
                    from drive_service import upload_to_drive
                    from datetime import datetime

                    subfolder = datetime.now().strftime('%Y-%m')
                    drive_result = upload_to_drive(
                        permanent_path, original_filename,
                        subfolder=subfolder
                    )

                    if drive_result:
                        AudioFile.update_drive(
                            audio_id,
                            drive_result['file_id'],
                            drive_result['url']
                        )
                        logger.info(f"[Drive] 업로드 성공: {drive_result['file_id']}")

                except Exception as e:
                    logger.error(f"[Drive] 업로드 실패: {e}")

            logger.info(f"[STT] 전체 처리 완료: audio_id={audio_id}")

        except Exception as e:
            logger.error(f"[STT] 처리 실패: {e}", exc_info=True)
            AudioFile.update_status(audio_id, 'failed', str(e))

            socketio.emit('audio_status', {
                'audio_id': audio_id,
                'message_id': message_id,
                'status': 'failed',
                'error': str(e),
            }, room=f'room_{room_id}')

            Message.create(
                room_id, user_id, 'system',
                f'⚠️ 음성 변환 실패: {str(e)[:100]}',
                parent_id=message_id
            )

            # 실패 시에도 임시 파일 정리
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"임시 파일 삭제: {filepath}")

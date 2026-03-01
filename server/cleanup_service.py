"""
음성 파일 자동 정리 서비스
설정된 시간(기본 24시간) 후 파일 자동 삭제
"""
import os
import time
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config

logger = logging.getLogger(__name__)


def cleanup_expired_audio_files():
    """
    만료된 음성 파일 삭제
    AUDIO_RETENTION_HOURS 시간이 지난 파일을 삭제
    """
    audio_folder = Config.AUDIO_FOLDER
    retention_hours = Config.AUDIO_RETENTION_HOURS

    if not os.path.exists(audio_folder):
        logger.debug(f"음성 폴더가 존재하지 않음: {audio_folder}")
        return

    now = datetime.now()
    expiry_time = now - timedelta(hours=retention_hours)
    deleted_count = 0
    error_count = 0

    logger.info(f"[Cleanup] 파일 정리 시작 - {retention_hours}시간 이전 파일 삭제")

    for filename in os.listdir(audio_folder):
        filepath = os.path.join(audio_folder, filename)

        # 디렉토리는 스킵
        if os.path.isdir(filepath):
            continue

        try:
            # 파일 수정 시간 확인
            file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))

            if file_mtime < expiry_time:
                os.remove(filepath)
                deleted_count += 1
                logger.info(f"[Cleanup] 파일 삭제: {filename} (생성: {file_mtime})")

        except Exception as e:
            error_count += 1
            logger.error(f"[Cleanup] 파일 삭제 실패: {filename} - {e}")

    if deleted_count > 0 or error_count > 0:
        logger.info(f"[Cleanup] 정리 완료 - 삭제: {deleted_count}개, 오류: {error_count}개")


def cleanup_temp_uploads():
    """
    임시 업로드 폴더 정리
    1시간 이상 된 임시 파일 삭제
    """
    upload_folder = Config.UPLOAD_FOLDER

    if not os.path.exists(upload_folder):
        return

    now = datetime.now()
    expiry_time = now - timedelta(hours=1)

    for filename in os.listdir(upload_folder):
        filepath = os.path.join(upload_folder, filename)

        if os.path.isdir(filepath):
            continue

        try:
            file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))

            if file_mtime < expiry_time:
                os.remove(filepath)
                logger.info(f"[Cleanup] 임시 파일 삭제: {filename}")

        except Exception as e:
            logger.error(f"[Cleanup] 임시 파일 삭제 실패: {filename} - {e}")


# 스케줄러 인스턴스
_scheduler = None


def init_cleanup_scheduler():
    """
    정리 스케줄러 초기화
    매 시간마다 만료된 파일 정리
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("스케줄러가 이미 실행 중입니다")
        return _scheduler

    _scheduler = BackgroundScheduler()

    # 매 시간마다 만료 파일 정리
    _scheduler.add_job(
        cleanup_expired_audio_files,
        'interval',
        hours=1,
        id='cleanup_audio',
        name='음성 파일 정리'
    )

    # 매 30분마다 임시 파일 정리
    _scheduler.add_job(
        cleanup_temp_uploads,
        'interval',
        minutes=30,
        id='cleanup_temp',
        name='임시 파일 정리'
    )

    _scheduler.start()
    logger.info("[Cleanup] 스케줄러 시작됨")

    # 시작 시 즉시 한 번 실행
    cleanup_expired_audio_files()
    cleanup_temp_uploads()

    return _scheduler


def shutdown_cleanup_scheduler():
    """스케줄러 종료"""
    global _scheduler

    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("[Cleanup] 스케줄러 종료됨")


# 테스트용
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print(f"음성 폴더: {Config.AUDIO_FOLDER}")
    print(f"보관 시간: {Config.AUDIO_RETENTION_HOURS}시간")

    cleanup_expired_audio_files()
    cleanup_temp_uploads()

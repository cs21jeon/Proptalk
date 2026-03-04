module.exports = {
  apps: [{
    name: 'voiceroom',
    script: '/home/webapp/goldenrabbit/chat_stt/server/venv/bin/python',
    args: 'app.py',
    cwd: '/home/webapp/goldenrabbit/chat_stt/server',
    interpreter: 'none',
    env: {
      // DB
      DB_HOST: 'localhost',
      DB_PORT: '5432',
      DB_NAME: 'voiceroom',
      DB_USER: 'goldenrabbit',
      DB_PASS: 'your-db-password',  // 실제 비밀번호로 변경

      // 보안
      SECRET_KEY: 'change-to-random-secret-key',  // 랜덤 문자열로 변경
      JWT_SECRET: 'change-to-random-jwt-secret',  // 랜덤 문자열로 변경

      // Claude API (요약 기능)
      CLAUDE_API_KEY: 'your-claude-api-key',  // Claude API 키로 변경

      // Google
      GOOGLE_CLIENT_ID: 'your-google-client-id.apps.googleusercontent.com',
      GOOGLE_SERVICE_ACCOUNT_FILE: '/home/webapp/goldenrabbit/chat_stt/credentials/service-account.json',
      GOOGLE_DRIVE_FOLDER_ID: 'your-drive-folder-id',
      ENABLE_DRIVE_BACKUP: 'false',  // Drive 백업 비활성화 (선택)

      // Whisper
      WHISPER_MODEL: 'small',

      // 파일 관리
      UPLOAD_FOLDER: '/home/webapp/goldenrabbit/chat_stt/uploads',
      AUDIO_FOLDER: '/home/webapp/goldenrabbit/chat_stt/audio',
      AUDIO_RETENTION_HOURS: '24',  // 파일 보관 시간

      // 토스페이먼츠 결제
      TOSS_CLIENT_KEY: '',                     // 토스 클라이언트 키
      TOSS_SECRET_KEY: '',                     // 토스 시크릿 키
      TOSS_WEBHOOK_SECRET: '',                 // 토스 웹훅 시크릿
      BILLING_ENCRYPTION_KEY: '',              // AES-256 키 (64자 hex)

      // 서버
      PORT: '5060',
      FLASK_DEBUG: 'false',
    },
    max_memory_restart: '3G',
    kill_timeout: 15000,
    // 로그
    error_file: '/home/webapp/goldenrabbit/chat_stt/logs/error.log',
    out_file: '/home/webapp/goldenrabbit/chat_stt/logs/out.log',
    merge_logs: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss',
  }]
};

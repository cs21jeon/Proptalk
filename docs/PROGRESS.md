# Proptalk 프로젝트 진행 현황

> 최종 업데이트: 2026-03-01

## 프로젝트 개요

음성-텍스트 변환 채팅 앱 (VoiceRoom/Proptalk)
- 통화 녹음 파일 업로드 → **Google STT** → Claude 요약 → 자동 댓글

### 핵심 기능
1. Google 계정 로그인 (OAuth 2.0) ✅
2. 전용 채팅방 (생성/참여/멤버 관리) ✅
3. 음성 파일 업로드 ✅
4. 자동 STT 변환 (**Google Speech-to-Text**) ✅ 설정 완료
5. Claude API 요약 ✅ (코드 완성, 테스트 필요)
6. 자동 댓글 ✅
7. 파일명 파싱 (전화번호/날짜/이름) ✅
8. 24시간 후 자동 삭제 ✅

---

## 현재 상태

### 완료된 작업 ✅

| 항목 | 상태 | 비고 |
|------|------|------|
| 서버 배포 | ✅ | goldenrabbit.biz:5060 |
| Nginx 프록시 | ✅ | /voiceroom/ 경로 |
| PostgreSQL DB | ✅ | voiceroom DB |
| Google OAuth | ✅ | 웹/앱 클라이언트 설정 완료 |
| Flutter 앱 빌드 | ✅ | Release APK 생성됨 |
| 채팅방 기능 | ✅ | 생성/참여/메시지 |
| 파일 업로드 | ✅ | 녹음 파일 선택 가능 |
| 커스텀 파일 브라우저 | ✅ | 최신순 정렬 |
| **Google STT** | ✅ | 클라우드 API로 전환 완료 |

### 진행 중 / 테스트 필요 🔄

| 항목 | 상태 | 비고 |
|------|------|--------|
| STT 변환 | 🔄 | Google STT 설정 완료, 테스트 필요 |
| Claude 요약 | 🔄 | STT 이후 단계라 테스트 필요 |
| 음성 다운로드 | 🔄 | 구현 완료, 테스트 필요 |

---

## 서버 정보

### 원격 서버
- **IP**: 175.119.224.71
- **도메인**: goldenrabbit.biz
- **SSH**: `ssh root@175.119.224.71`
- **배포 경로**: `/home/webapp/goldenrabbit/chat_stt/server/`

### 서버 사양 (현재 문제)
```
RAM: 956MB (부족!)
Disk: 26GB (사용 가능: ~5GB)
CPU: 가상 CPU
```

### PM2 관리
```bash
# 로그 확인
pm2 logs voiceroom --lines 50

# 재시작
pm2 restart voiceroom

# 환경변수 적용 재시작
cd /home/webapp/goldenrabbit/chat_stt/server
pm2 delete voiceroom && pm2 start ecosystem.config.js
```

### 주요 설정 파일
- `ecosystem.config.js` - PM2 환경변수 설정
- `config.py` - Flask 설정
- `routes_messages.py` - STT/업로드 로직

---

## STT 설정: Google Speech-to-Text ✅

### 해결됨: 메모리 부족 문제
- 기존 문제: Whisper 로컬 실행 시 서버 메모리 부족 (956MB)
- 해결: **Google Speech-to-Text API**로 전환 (클라우드 처리)

### Google STT 설정
| 항목 | 값 |
|------|-----|
| 프로젝트 ID | `speech-to-text-goldenrabbit` |
| 서비스 계정 | `proptalk@speech-to-text-goldenrabbit.iam.gserviceaccount.com` |
| 인증 파일 | `/home/webapp/goldenrabbit/chat_stt/credentials/google-stt.json` |
| 서비스 파일 | `google_stt_service.py` |

### 가격
| 사용량 | 비용 |
|--------|------|
| 0~60분/월 | **무료** |
| 60분 초과 | $0.024/분 (약 32원) |

### 이전 시도 기록
1. ❌ PyTorch MKL 환경변수 → primitive 오류
2. ❌ faster-whisper 전환 → 여전히 메모리 부족
3. ❌ tiny 모델 → 메모리 부족 지속
4. ✅ **Google STT API** → 성공

---

## Google OAuth 설정

### 클라이언트 ID
- **웹**: `325885879870-rj00lod4843dj8qrt9gjnrpcfmsltc9v.apps.googleusercontent.com`
- **앱**: `325885879870-48jleq7i81j80iskr2cqhf1cjup3odmk.apps.googleusercontent.com`

### SHA-1 (릴리즈)
```
A0:D0:C4:7F:7A:E3:51:50:06:6C:A8:DD:2C:E7:7A:31:A9:A1:0E:4A
```

---

## Flutter 앱

### 빌드 명령어
```bash
cd C:\Users\ant19\projects\Proptalk\flutter

# 디버그
flutter run

# 릴리즈 APK
flutter build apk --release
```

### APK 위치
```
flutter\build\app\outputs\flutter-apk\app-release.apk
```

### 주요 수정 파일
- `lib/services/auth_service.dart` - serverClientId 추가
- `lib/screens/chat_screen.dart` - 파일 선택 UI
- `lib/screens/audio_picker_screen.dart` - 커스텀 파일 브라우저 (신규)

---

## 다음 단계

### 우선순위 1: 전체 플로우 테스트
- [ ] Google STT 변환 테스트 (음성 업로드)
- [ ] Claude 요약 자동 생성 확인
- [ ] 자동 댓글 달리는지 확인

### 우선순위 2: 기능 테스트
- [ ] 음성 파일 다운로드 테스트
- [ ] 24시간 자동 삭제 확인
- [ ] 검색 기능 테스트

### 우선순위 3: 개선
- [ ] 에러 핸들링 강화
- [ ] 사용자 피드백 (진행률 표시)
- [ ] UI/UX 개선

---

## 파일 구조

```
Proptalk/
├── server/                     # 백엔드 (로컬 복사본)
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── routes_messages.py      # STT 로직 (Google STT 사용)
│   ├── google_stt_service.py   # Google Speech-to-Text 서비스 ⭐ 신규
│   ├── claude_service.py       # Claude 요약
│   ├── filename_parser.py
│   ├── cleanup_service.py      # 24시간 삭제
│   └── ecosystem.config.js
│
├── credentials/                # 인증 파일 (서버에만 존재)
│   └── google-stt.json         # Google STT 서비스 계정 키
│
├── flutter/                    # Flutter 앱
│   ├── lib/
│   │   ├── main.dart
│   │   ├── screens/
│   │   │   ├── login_screen.dart
│   │   │   ├── rooms_screen.dart
│   │   │   ├── chat_screen.dart
│   │   │   └── audio_picker_screen.dart  # 신규
│   │   └── services/
│   └── pubspec.yaml
│
└── docs/
    ├── ARCHITECTURE.md
    ├── SETUP_GUIDE.md
    └── PROGRESS.md             # 이 파일
```

---

## 트러블슈팅 기록

### 1. Google 로그인 안됨
- **원인**: GOOGLE_CLIENT_ID 환경변수 미설정
- **해결**: ecosystem.config.js에 설정 후 PM2 재시작

### 2. DB 권한 오류
- **원인**: PostgreSQL 테이블 권한 없음
- **해결**: `GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO goldenrabbit_user;`

### 3. ffmpeg 없음
- **해결**: `apt-get install -y ffmpeg`

### 4. PyTorch primitive 오류
- **원인**: MKL 백엔드 CPU 호환성 문제
- **해결**: faster-whisper로 교체 (CTranslate2 기반)

### 5. 서버 크래시 (메모리)
- **원인**: 1GB RAM으로 Whisper 실행 불가
- **해결**: Google Speech-to-Text API로 전환

### 6. Google STT 설정 (2026-03-01)
- **작업**: 로컬 Whisper → Google Cloud STT 전환
- **설정**: 서비스 계정 생성, 인증 파일 업로드, google_stt_service.py 생성
- **상태**: 설정 완료, 테스트 필요

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | /api/health | 헬스체크 |
| POST | /api/auth/google | Google 로그인 |
| GET | /api/rooms | 채팅방 목록 |
| POST | /api/rooms | 채팅방 생성 |
| POST | /api/rooms/:id/audio | 음성 업로드 |
| GET | /api/audio/:id/download | 음성 다운로드 |

---

## 연락처 / 참고

- 서버 관리: SSH root@175.119.224.71
- 프로젝트 경로: C:\Users\ant19\projects\Proptalk
- Claude API: Anthropic 콘솔에서 키 관리

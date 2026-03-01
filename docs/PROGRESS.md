# Proptalk 프로젝트 진행 현황

> 최종 업데이트: 2026-03-02

## 프로젝트 개요

음성-텍스트 변환 채팅 앱 (Proptalk)
- 통화 녹음 파일 업로드 → **OpenAI Whisper API** → Claude 요약 → 자동 댓글

### 핵심 기능
1. Google 계정 로그인 (OAuth 2.0) ✅
2. 전용 채팅방 (생성/참여/멤버 관리) ✅
3. 음성 파일 업로드 ✅
4. 자동 STT 변환 (**OpenAI Whisper API**) ✅
5. Claude API 요약 ✅
6. 자동 댓글 ✅
7. 파일명 파싱 (전화번호/날짜/이름) ✅
8. 24시간 후 자동 삭제 ✅
9. 3초 폴링 실시간 업데이트 ✅ **신규**

---

## 현재 상태

### 완료된 작업 ✅

| 항목 | 상태 | 비고 |
|------|------|------|
| 서버 배포 | ✅ | goldenrabbit.biz:5060 |
| Nginx 프록시 | ✅ | /voiceroom/ 경로 |
| PostgreSQL DB | ✅ | voiceroom DB |
| Google OAuth | ✅ | 웹/앱 클라이언트 설정 완료 |
| Flutter 앱 빌드 | ✅ | Release APK (49.3MB) |
| 채팅방 기능 | ✅ | 생성/참여/메시지 |
| 파일 업로드 | ✅ | 녹음 파일 선택 가능 |
| 커스텀 파일 브라우저 | ✅ | 최신순 정렬, 통신사별 폴더 지원 |
| **OpenAI Whisper STT** | ✅ | 무제한 길이 지원 (자동 분할) |
| **Claude 요약** | ✅ | 자동 요약 생성 |
| **3초 폴링** | ✅ | 실시간 메시지 업데이트 |
| **GitHub 커밋** | ✅ | cs21jeon/Proptalk |

### 테스트 필요 🔄

| 항목 | 상태 | 비고 |
|------|------|--------|
| 전체 플로우 | 🔄 | 앱에서 업로드 → STT → 요약 → 댓글 |
| 음성 다운로드 | 🔄 | Download/Proptalk 폴더 저장 |

---

## 서버 정보

### 원격 서버
- **IP**: 175.119.224.71
- **도메인**: goldenrabbit.biz
- **SSH**: `ssh root@175.119.224.71`
- **배포 경로**: `/home/webapp/goldenrabbit/chat_stt/server/`

### PM2 관리
```bash
# 로그 확인
pm2 logs voiceroom --lines 50

# 재시작
pm2 restart voiceroom

# 환경변수 적용 재시작
cd /home/webapp/goldenrabbit/chat_stt/server
pm2 restart voiceroom --update-env
```

### 주요 설정 파일
- `ecosystem.config.js` - PM2 환경변수 설정
- `config.py` - Flask 설정
- `routes_messages.py` - STT/업로드 로직
- `whisper_service.py` - OpenAI Whisper API 서비스

---

## STT 설정: OpenAI Whisper API ✅

### 변경 이력
1. ❌ 로컬 Whisper → 서버 메모리 부족 (956MB)
2. ❌ Google STT → 1분 제한 (inline audio)
3. ✅ **OpenAI Whisper API** → 무제한 (25MB 분할)

### OpenAI Whisper 설정
| 항목 | 값 |
|------|-----|
| API | OpenAI Whisper API |
| 모델 | whisper-1 |
| 가격 | $0.006/분 (약 8원) |
| 파일 제한 | 25MB (자동 10분 분할) |
| 서비스 파일 | `whisper_service.py` |

### 환경변수
```
OPENAI_API_KEY=sk-proj-...
CLAUDE_API_KEY=sk-ant-api03-...
```

---

## Flutter 앱

### 빌드 명령어
```bash
cd C:\Users\ant19\projects\Proptalk\flutter

# 릴리즈 APK
flutter build apk --release
```

### APK 위치
```
flutter\build\app\outputs\flutter-apk\app-release.apk
```

### 주요 기능
- Google 로그인
- 채팅방 생성/참여
- 음성 파일 업로드 (녹음 폴더 브라우저)
- 3초 폴링으로 실시간 메시지 업데이트
- Optimistic Update (업로드 즉시 UI 표시)
- 다운로드 (Download/Proptalk 폴더)

---

## GitHub

### 저장소
- **URL**: https://github.com/cs21jeon/Proptalk
- **브랜치**: main

### 커밋 이력
- `2026-03-02` - 초기 구현 (Whisper API, 폴링, Flutter 앱)

---

## 다음 단계

### 우선순위 1: 전체 플로우 테스트
- [ ] APK 설치 및 로그인 테스트
- [ ] 음성 파일 업로드 → STT 변환 확인
- [ ] Claude 요약 자동 생성 확인
- [ ] 자동 댓글 달리는지 확인

### 우선순위 2: Google Drive 연동 (선택)
- [ ] OAuth 2.0 토큰 저장 구현
- [ ] 방장 Drive에 자동 백업
- [ ] 다운로드 시 Drive에서 프록시

### 우선순위 3: 개선
- [ ] 에러 핸들링 강화
- [ ] UI/UX 개선
- [ ] 푸시 알림 (FCM)

---

## 파일 구조

```
Proptalk/
├── server/                     # 백엔드
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── routes_messages.py      # STT 로직
│   ├── whisper_service.py      # OpenAI Whisper API ⭐
│   ├── claude_service.py       # Claude 요약
│   ├── drive_service.py        # Google Drive (준비됨)
│   ├── filename_parser.py
│   ├── cleanup_service.py      # 24시간 삭제
│   └── ecosystem.config.js
│
├── flutter/                    # Flutter 앱
│   ├── lib/
│   │   ├── main.dart
│   │   ├── screens/
│   │   │   ├── login_screen.dart
│   │   │   ├── rooms_screen.dart
│   │   │   ├── chat_screen.dart    # 3초 폴링 추가
│   │   │   └── audio_picker_screen.dart
│   │   └── services/
│   └── pubspec.yaml
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SETUP_GUIDE.md
│   └── PROGRESS.md             # 이 파일
│
└── images/                     # 로고/아이콘
```

---

## 트러블슈팅 기록

### 1. Google STT 1분 제한 (2026-03-02)
- **원인**: Inline audio는 1분까지만 지원
- **해결**: OpenAI Whisper API로 전환 (무제한)

### 2. WebSocket 실시간 업데이트 안됨
- **원인**: 연결 불안정
- **해결**: 3초 폴링 추가 (WebSocket + 폴링 병행)

### 3. 서버 메모리 부족
- **원인**: Whisper 로컬 실행 불가 (956MB RAM)
- **해결**: 클라우드 API 사용 (OpenAI/Google)

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
| GET | /api/rooms/:id/messages | 메시지 목록 (폴링용) |

---

## 연락처 / 참고

- GitHub: https://github.com/cs21jeon/Proptalk
- 서버 관리: SSH root@175.119.224.71
- 프로젝트 경로: C:\Users\ant19\projects\Proptalk

# Proptalk - 음성 채팅방 STT 플랫폼

> 최종 업데이트: 2026-03-02

## 전체 아키텍처

```
┌──────────────────────────────────────────────────────────────────┐
│                    Flutter App (Android)                          │
│  ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐    │
│  │ Google    │ │ 채팅방   │ │ 음성파일 │ │ 실시간 메시지   │    │
│  │ 로그인   │ │ 목록/생성│ │ 업로드   │ │ (폴링+Socket)  │    │
│  │ +Drive   │ │ +Drive   │ │ +3GP변환 │ │ +MD 렌더링     │    │
│  └────┬──────┘ └────┬─────┘ └────┬─────┘ └───────┬────────┘    │
└───────┼──────────────┼───────────┼────────────────┼─────────────┘
        │              │           │                │
        ▼              ▼           ▼                ▼
┌──────────────────────────────────────────────────────────────────┐
│               Cafe24 서버 (goldenrabbit.biz:5060)                │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                  Flask + SocketIO Server                    │  │
│  │  /api/auth/*      - Google OAuth + Drive 토큰 교환         │  │
│  │  /api/rooms/*     - 채팅방 CRUD + Drive 폴더 생성          │  │
│  │  /api/rooms/*/audio - 음성 업로드 → STT → 요약 → Drive     │  │
│  │  /api/audio/*/download - 다운로드 (로컬 → Drive 프록시)    │  │
│  └───────┬────────────┬──────────────┬────────────────────────┘  │
│          │            │              │                            │
│  ┌───────▼────┐ ┌────▼─────┐ ┌─────▼──────┐                    │
│  │ PostgreSQL │ │ OpenAI   │ │ Anthropic  │                    │
│  │ - users    │ │ Whisper  │ │ Claude     │                    │
│  │ - rooms    │ │ API      │ │ API        │                    │
│  │ - messages │ │ (STT)    │ │ (요약)     │                    │
│  │ - audio    │ └──────────┘ └────────────┘                    │
│  └────────────┘                                                  │
└──────────────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────┐
│  Google Drive      │
│  (방장 OAuth)      │
│  Proptalk/방이름/  │
└────────────────────┘
```

## DB 스키마

```sql
-- 사용자
users: id, google_id, email, name, avatar_url, google_tokens(JSONB), created_at

-- 채팅방
rooms: id, name, description, created_by, invite_code, drive_folder_id, created_at, updated_at

-- 채팅방 멤버
room_members: room_id, user_id, role(admin/member), joined_at

-- 메시지 (텍스트 + 음성 + 자동댓글)
messages: id, room_id, user_id, type(text/audio/transcript/system),
          content, parent_id(댓글용), created_at

-- 음성 파일 기록
audio_files: id, message_id, room_id, user_id,
             original_filename, file_size, drive_file_id, drive_url,
             phone_number, record_date, parsed_name, parsed_memo,
             transcript_text, transcript_summary, transcript_segments,
             status, drive_status, error_message, created_at, completed_at
```

## 핵심 플로우

### 1. 로그인 + Drive 연동
1) Flutter에서 Google Sign-In (email + profile + drive.file 스코프)
2) `serverAuthCode` + `idToken` 서버로 전송
3) 서버에서 idToken 검증 → JWT 발급
4) serverAuthCode → Google token endpoint에서 access_token + refresh_token 교환
5) tokens를 users.google_tokens에 저장

### 2. 방 생성 + Drive 폴더
1) 방장이 채팅방 생성
2) 방장의 Drive 토큰이 있으면 → Proptalk/{방이름} 폴더 자동 생성
3) drive_folder_id를 rooms 테이블에 캐시

### 3. 음성 업로드 → STT → 요약 → Drive 저장
1) 사용자가 음성파일 업로드
2) 서버에서 음성 메시지 생성 → WebSocket 알림
3) 백그라운드 스레드:
   a. 파일명 파싱 (전화번호/날짜/이름)
   b. 3GP/AMR 감지 → MP3 변환 (ffprobe + ffmpeg)
   c. OpenAI Whisper API로 STT 변환
   d. Claude API로 마크다운 구조화 요약
   e. 자동 댓글 (summary + Drive 저장 여부 메시지)
   f. 방장 Drive에 파일 업로드
   g. Drive 성공 → 서버 파일 삭제 / 실패 → 24시간 로컬 보관

### 4. 다운로드 (프록시)
1) 서버 로컬 파일 있으면 → 직접 전송
2) 없으면 → 방장 Drive에서 프록시 다운로드 (토큰 자동 갱신)

## 기술 스택

| 구분 | 기술 |
|------|------|
| 앱 | Flutter 3.x (Android) |
| 서버 | Flask + Flask-SocketIO + PM2 |
| DB | PostgreSQL (psycopg2) |
| 인증 | Google Sign-In + JWT + OAuth2 (drive.file) |
| STT | OpenAI Whisper API ($0.006/분) |
| 요약 | Anthropic Claude API (마크다운) |
| 실시간 | 3초 폴링 + WebSocket (병행) |
| 파일저장 | Google Drive API (방장 OAuth 토큰) |
| 포맷변환 | ffprobe + ffmpeg (3GP/AMR → MP3) |

## 파일 구조

```
Proptalk/
├── server/                      # 백엔드 (원격 서버 배포)
│   ├── app.py                   # 메인 Flask 앱
│   ├── config.py                # 설정 (환경변수 기반)
│   ├── models.py                # DB 모델 (psycopg2, 토큰/Drive CRUD)
│   ├── auth.py                  # OAuth + JWT + serverAuthCode 교환
│   ├── routes_rooms.py          # 채팅방 API + Drive 폴더 생성
│   ├── routes_messages.py       # 음성 업로드 + STT + Drive 저장
│   ├── whisper_service.py       # OpenAI Whisper API + 포맷 변환
│   ├── claude_service.py        # Claude 마크다운 요약
│   ├── drive_service.py         # Drive 업로드/다운로드 (토큰 자동 갱신)
│   ├── filename_parser.py       # 파일명 파싱
│   ├── cleanup_service.py       # 24시간 파일 삭제
│   ├── ecosystem.config.js      # PM2 환경변수
│   └── deploy/                  # 배포용 파일
│
├── flutter/                     # Flutter 앱
│   ├── lib/
│   │   ├── main.dart
│   │   ├── screens/
│   │   │   ├── login_screen.dart
│   │   │   ├── rooms_screen.dart
│   │   │   ├── chat_screen.dart          # 폴링 + 마크다운 렌더링
│   │   │   └── audio_picker_screen.dart  # 파일 권한 처리
│   │   └── services/
│   │       ├── auth_service.dart          # drive.file 스코프 + serverAuthCode
│   │       ├── api_service.dart           # API + Drive 메서드
│   │       └── socket_service.dart
│   └── pubspec.yaml
│
├── docs/
│   ├── ARCHITECTURE.md          # 이 파일
│   ├── SETUP_GUIDE.md
│   ├── LAUNCH_PLAN.md
│   └── PROGRESS.md
│
└── images/                      # 로고/아이콘
```

# Proptalk 프로젝트 진행 현황

> 최종 업데이트: 2026-03-03 (UI 개선 + 재로그인 Drive 동의 수정 + 정렬 기능)

## 프로젝트 개요

음성-텍스트 변환 채팅 앱 (Proptalk)
- 통화 녹음 파일 업로드 → **OpenAI Whisper API** → **Claude 요약 (마크다운)** → 자동 댓글 → **Google Drive 저장**

### 핵심 기능
1. Google 계정 로그인 (OAuth 2.0 + Drive 연동) ✅
2. 전용 채팅방 (생성/참여/멤버 관리) ✅
3. 음성 파일 업로드 (3GP/AMR 자동 변환) ✅
4. 자동 STT 변환 (**OpenAI Whisper API**) ✅
5. Claude API 요약 (**마크다운 구조화**) ✅
6. 자동 댓글 (MarkdownBody 렌더링) ✅
7. 파일명 파싱 (전화번호/날짜/이름) ✅
8. Google Drive 자동 저장 (방장 드라이브) ✅
9. Drive 프록시 다운로드 ✅
10. 3초 폴링 실시간 업데이트 ✅
11. **서비스 이용 동의 화면** (약관/개인정보/국외이전) ✅ **신규**
12. **음성 데이터 처리 동의 팝업** ✅ **신규**
13. **접속기록 감사 로그** (3개월 보관) ✅ **신규**
14. **RBAC 권한 강화** (admin/member 역할 적용) ✅ **신규**
15. **회원 탈퇴 + 동의 철회** ✅ **신규**
16. **설정 화면** (법적 문서, 동의 관리, 계정 삭제) ✅ **신규**
17. **톡방 참여 승인 프로세스** (방장 승인/거절) ✅ **신규**
18. **FAB 라벨** ("참여", "새 톡방") ✅ **신규**
19. **톡방 관리 기능** (삭제/이름변경/나가기/즐겨찾기) ✅ **신규**
20. **헤더 리디자인** (Proptalk 아이콘 + 태그라인) ✅ **신규**
21. **동의화면 버그 수정** (재로그인 시 동의화면 재표시 방지) ✅ **신규**
22. **관리자 권한 이전** (방장 변경 기능) ✅ **신규**
23. **재로그인 Drive 동의 반복 수정** ✅ **신규**
24. **채팅방 정렬 기능** (생성순/이름순/참여인원순, 오름차순/내림차순) ✅ **신규**
25. **채팅방 설정 UI 개선** (톱니바퀴 아이콘, 전체 높이 시트, 인라인 이름변경) ✅ **신규**
26. **앱 아이콘 변경** ✅ **신규**

---

## 현재 상태

### 완료된 작업 ✅

| 항목 | 상태 | 비고 |
|------|------|------|
| 서버 배포 | ✅ | goldenrabbit.biz:5060 |
| Nginx 프록시 | ✅ | /voiceroom/ 경로 |
| PostgreSQL DB | ✅ | voiceroom DB (google_tokens, drive_folder_id 추가) |
| Google OAuth + Drive | ✅ | `speech-to-text-goldenrabbit` 프로젝트, drive.file 스코프 |
| Flutter 앱 빌드 | ✅ | Release APK (50.7MB) |
| 채팅방 기능 | ✅ | 생성/참여/메시지, 방 생성 시 Drive 폴더 자동 생성 |
| 파일 업로드 | ✅ | 3GP/AMR 자동 감지 → MP3 변환 |
| 커스텀 파일 브라우저 | ✅ | 최신순 정렬, MANAGE_EXTERNAL_STORAGE 권한 |
| **OpenAI Whisper STT** | ✅ | 무제한 길이 지원 (자동 분할) |
| **Claude 요약** | ✅ | 마크다운 구조화 (볼드 키워드 + 불릿) |
| **Google Drive 연동** | ✅ | 방장 Drive에 자동 저장, 서버 파일 즉시 삭제 |
| **Drive 프록시 다운로드** | ✅ | 서버 로컬 없으면 Drive에서 다운로드 |
| **3초 폴링** | ✅ | 실시간 메시지 + 댓글 내용 변경 감지 |
| **GitHub 커밋** | ✅ | cs21jeon/Proptalk |
| **서비스 동의 화면** | ✅ | 약관/개인정보/국외이전 3항목 필수 동의 |
| **음성 처리 동의 팝업** | ✅ | 첫 업로드 시 표시, SharedPreferences + DB 저장 |
| **접속기록 감사 로그** | ✅ | access_logs 테이블, 3개월 보관 후 자동 삭제 |
| **RBAC 권한 강화** | ✅ | room_role_required 데코레이터, admin/member 역할 적용 |
| **회원 탈퇴** | ✅ | CASCADE 삭제, Drive 파일 보존 |
| **동의 철회 UI** | ✅ | 설정 화면에서 각 동의 항목별 철회 가능 |
| **설정 화면** | ✅ | 법적 문서 링크, 동의 관리, 계정 삭제, 로그아웃 |
| **톡방 참여 승인** | ✅ | 초대코드 참여 → pending → 방장 승인/거절 |
| **FAB 라벨** | ✅ | "참여", "새 톡방" 텍스트 표시 |
| **톡방 삭제** | ✅ | admin 전용, CASCADE 삭제 |
| **톡방 이름 변경** | ✅ | admin 전용, 시스템 메시지 생성 |
| **톡방 나가기** | ✅ | 유일 admin 보호 로직 (이전 필요 또는 방 자동 삭제) |
| **즐겨찾기** | ✅ | 별 아이콘 토글, 즐겨찾기 우선 정렬 |
| **관리자 권한 이전** | ✅ | 다른 멤버에게 admin 이전 |
| **헤더 리디자인** | ✅ | Proptalk 아이콘 + 텍스트 + "세상 쉬운 업무 공유" 태그라인 |
| **동의화면 버그 수정** | ✅ | signOut() 시 consent 상태 초기화 |
| **승인 대기 UI** | ✅ | 방 목록: 모래시계+뱃지, 방 정보: 승인/거절 버튼 |
| **재로그인 Drive 동의 수정** | ✅ | forceCodeForRefreshToken 제거, 재로그인 시 Drive 동의 반복 방지 |
| **채팅방 정렬** | ✅ | 생성순/이름순/참여인원순 + 오름차순/내림차순 토글 |
| **채팅방 설정 UI** | ✅ | 톱니바퀴 아이콘, 전체 높이 시트, 인라인 이름변경 |
| **앱 아이콘 변경** | ✅ | Proptalk_icon_half size.png 적용 |

### 테스트 진행 중 🔄

| 항목 | 상태 | 비고 |
|------|------|--------|
| Google Drive 전체 플로우 | 🔄 | 로그인 → Drive 동의 → 방 생성 → 업로드 → Drive 저장 |
| OAuth 동의화면 프로덕션 전환 | 🔄 | 현재 테스트 모드 (100명 제한) |
| 법적 컴플라이언스 전체 플로우 | 🔄 | 로그인 → 동의 화면 → 음성 동의 → 설정/철회 |

---

## Google Cloud 설정

### 프로젝트
- **프로젝트**: `speech-to-text-goldenrabbit` (846392940969)
- **서비스 계정**: `proptalk@speech-to-text-goldenrabbit.iam.gserviceaccount.com`

### OAuth 클라이언트
| 이름 | 타입 | Client ID |
|------|------|-----------|
| Proptalk Web | 웹 애플리케이션 | `846392940969-a7k37gkon1p451mlnhp0oj9qaok1d8o1` |
| Proptalk App | Android | `846392940969-ro1j6gm1r9mdsmfjkfv40311l0053s5a` |

### 필요 설정
- Google Drive API: 활성화 필요
- OAuth 동의화면: `drive.file` 스코프 추가
- Android SHA-1: `FA:53:98:5C:4B:D3:69:C1:A2:36:87:19:A8:79:BC:E3:68:F6:D0:98`

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

# 재시작 (환경변수 변경 시)
cd /home/webapp/goldenrabbit/chat_stt/server
pm2 delete voiceroom && pm2 start ecosystem.config.js && pm2 save

# 주의: pm2 restart --update-env 가 캐시 문제로 동작 안 할 수 있음
# 환경변수 변경 시 delete → start 방식 권장
```

### 주요 설정 파일
- `ecosystem.config.js` - PM2 환경변수 (GOOGLE_CLIENT_ID, CLIENT_SECRET, API 키 등)
- `config.py` - Flask 설정
- `models.py` - DB 모델 (User 토큰, Room 폴더ID, AudioFile Drive, **UserConsent, AccessLog**)
- `auth.py` - Google OAuth + Drive + **동의 API + RBAC 데코레이터 + 계정 삭제**
- `drive_service.py` - Google Drive 업로드/다운로드 (사용자 OAuth, 토큰 자동 갱신)
- `routes_rooms.py` - 채팅방 API + Drive 폴더 + **멤버 관리/승인/거절 + 삭제/이름변경/나가기/즐겨찾기 + 감사 로그**
- `routes_messages.py` - STT/업로드/Drive 저장 + **감사 로그**
- `whisper_service.py` - OpenAI Whisper API (3GP/AMR 자동 변환)
- `claude_service.py` - Claude 마크다운 요약
- `cleanup_service.py` - 24시간 파일 삭제 + **3개월 초과 감사 로그 삭제**

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
| 포맷 변환 | 3GP/AMR → MP3 자동 변환 (ffprobe + ffmpeg) |

---

## Google Drive 연동 ✅

### 흐름
```
Flutter 로그인 (drive.file 스코프 포함)
  → serverAuthCode를 서버로 전송
  → 서버가 Google에서 access_token + refresh_token 교환
  → DB users.google_tokens에 저장

방 생성 시
  → 방장 Drive에 Proptalk/{방이름} 폴더 자동 생성
  → rooms.drive_folder_id에 캐시

음성 업로드 후
  → STT/요약 완료 → Drive 업로드 → 서버 파일 즉시 삭제
  → 실패 시 기존처럼 24시간 서버 보관 (fallback)

다운로드 시
  → 서버 로컬 파일 있으면 직접 전송
  → 없으면 방장 Drive에서 프록시 다운로드
```

### DB 스키마 변경
```sql
ALTER TABLE users ADD COLUMN google_tokens JSONB;
ALTER TABLE rooms ADD COLUMN drive_folder_id VARCHAR(200);
ALTER TABLE audio_files ADD COLUMN drive_status VARCHAR(20) DEFAULT 'pending';

-- 톡방 참여 승인 + 즐겨찾기 (2026-03-03)
ALTER TABLE room_members ADD COLUMN status VARCHAR(20) DEFAULT 'active';  -- active/pending
ALTER TABLE room_members ADD COLUMN is_favorite BOOLEAN DEFAULT false;

-- 법적 컴플라이언스 (2026-03-03)
CREATE TABLE user_consents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    consent_type VARCHAR(50) NOT NULL,  -- terms/privacy/overseas_transfer/audio_processing
    version VARCHAR(20) NOT NULL,
    agreed BOOLEAN NOT NULL DEFAULT true,
    agreed_at TIMESTAMP DEFAULT NOW(),
    withdrawn_at TIMESTAMP,
    ip_address VARCHAR(50),
    user_agent TEXT
);

CREATE TABLE access_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(30),
    resource_id INTEGER,
    ip_address VARCHAR(50),
    user_agent TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Flutter 앱

### 빌드 명령어
```bash
cd C:\Users\ant19\projects\Proptalk\flutter
flutter build apk --release
```

### APK 위치
```
flutter\build\app\outputs\flutter-apk\app-release.apk (51.1MB)
```

### 주요 기능
- Google 로그인 + Drive 권한 동의
- **서비스 동의 화면** (약관/개인정보/국외이전 필수 동의)
- 채팅방 생성/참여 (방 생성 시 Drive 폴더 자동 생성)
- 음성 파일 업로드 (MANAGE_EXTERNAL_STORAGE 권한)
- **음성 데이터 처리 동의** (첫 업로드 시 팝업)
- 3초 폴링으로 실시간 메시지 + 댓글 변경 감지
- 마크다운 요약 렌더링 (flutter_markdown)
- 다운로드 (서버 로컬 → Drive 프록시 fallback)
- **설정 화면** (법적 문서, 동의 관리, 계정 삭제)

### 주요 패키지
- `google_sign_in` - OAuth + drive.file 스코프
- `flutter_markdown` - 요약 마크다운 렌더링
- `permission_handler` - MANAGE_EXTERNAL_STORAGE
- `record` - 녹음
- `socket_io_client` - WebSocket
- `url_launcher` - 법적 문서 외부 링크
- `shared_preferences` - 음성 동의 상태 로컬 저장

---

## GitHub

### 저장소
- **URL**: https://github.com/cs21jeon/Proptalk
- **브랜치**: main

### 커밋 이력
- `2026-03-02` - 초기 구현 (Whisper API, 폴링, Flutter 앱)
- `2026-03-02` - Whisper API 전환 완료
- `2026-03-02` - Google Drive 연동 구현
- `2026-03-03` - 법적 컴플라이언스 구현 (동의/감사로그/RBAC/탈퇴/설정)
- `2026-03-03` - 톡방 참여 승인 프로세스 + FAB 라벨 추가
- `2026-03-03` - 톡방 관리 기능 + 헤더 리디자인 + 동의화면 버그 수정
- `2026-03-03` - UI 개선 (정렬, 설정시트, 인라인 이름변경, 앱아이콘, Drive 재동의 수정)

---

## 다음 단계

### 우선순위 1: Google Drive 연동 테스트
- [x] DB 마이그레이션 (google_tokens, drive_folder_id, drive_status)
- [x] 서버 코드 배포 (auth.py, drive_service.py, routes 등)
- [x] Flutter 코드 업데이트 (drive.file 스코프, serverAuthCode)
- [x] Google Cloud Console 설정 (Drive API, 스코프, 클라이언트)
- [ ] 앱 로그인 → Drive 동의 → 전체 플로우 테스트
- [ ] OAuth 동의화면 프로덕션 전환

### 우선순위 2: 법적 컴플라이언스 ✅ 완료 (2026-03-03)
- [x] 서비스 이용 동의 화면 (약관/개인정보/국외이전)
- [x] 음성 데이터 처리 동의 팝업
- [x] 동의 이력 DB 저장 (user_consents 테이블)
- [x] 접속기록 감사 로그 (access_logs 테이블, 3개월 보관)
- [x] RBAC 권한 강화 (admin/member 역할 적용)
- [x] 회원 탈퇴 기능 (CASCADE 삭제)
- [x] 동의 철회 UI (설정 화면)
- [x] 앱 내 이용약관/개인정보처리방침 열람
- [x] 설정 화면 (법적 문서, 동의 관리, 계정 삭제)
- [x] 서버 배포 (DB 마이그레이션 + 코드 배포 완료)

### 우선순위 3: 앱 출시 준비
- [ ] 에러 핸들링 강화
- [ ] Google Play Console 등록
- [ ] 무료 이용량 관리 로직

### 우선순위 4: 개선
- [x] FAB 라벨 추가 ("참여", "새 톡방")
- [x] 톡방 참여 승인 프로세스 (pending → 방장 승인/거절)
- [x] 승인 대기 UI (방 목록 뱃지 + 방 정보 승인/거절)
- [x] 톡방 관리 기능 (삭제/이름변경/나가기/즐겨찾기/관리자이전)
- [x] 헤더 리디자인 (Proptalk 아이콘 + 태그라인)
- [x] 동의화면 재표시 버그 수정
- [x] 재로그인 Drive 동의 반복 수정
- [x] 채팅방 정렬 기능 (생성순/이름순/참여인원순 + 오름차순/내림차순)
- [x] 채팅방 설정 UI 개선 (톱니바퀴, 전체높이, 인라인 이름변경)
- [x] 앱 아이콘 변경
- [ ] 푸시 알림 (FCM)
- [ ] UI/UX 추가 개선

---

## 파일 구조

```
Proptalk/
├── server/                     # 백엔드 (원격 배포)
│   ├── app.py
│   ├── config.py
│   ├── models.py               # User 토큰, Room Drive폴더, AudioFile Drive상태
│   ├── auth.py                 # OAuth + serverAuthCode 교환 + Drive API
│   ├── routes_rooms.py         # 방 생성 시 Drive 폴더 생성
│   ├── routes_messages.py      # STT + Drive 업로드/삭제 로직
│   ├── whisper_service.py      # OpenAI Whisper API + 3GP 변환
│   ├── claude_service.py       # Claude 마크다운 요약
│   ├── drive_service.py        # Google Drive 업로드/다운로드 (사용자 OAuth)
│   ├── filename_parser.py
│   ├── cleanup_service.py      # 24시간 삭제
│   ├── ecosystem.config.js     # PM2 환경변수
│   └── deploy/                 # 배포용 파일
│
├── flutter/                    # Flutter 앱
│   ├── lib/
│   │   ├── main.dart                    # 동의 화면 라우팅
│   │   ├── constants/
│   │   │   └── terms.dart               # 법적 문서 텍스트 (약관/처리방침/동의문)
│   │   ├── screens/
│   │   │   ├── login_screen.dart        # 법적 문서 링크 추가
│   │   │   ├── consent_screen.dart      # **신규** 서비스 동의 화면
│   │   │   ├── rooms_screen.dart        # 설정 메뉴 추가
│   │   │   ├── settings_screen.dart     # **신규** 설정 (동의/탈퇴/법적문서)
│   │   │   ├── chat_screen.dart         # 폴링 + 마크다운 + 음성 동의
│   │   │   └── audio_picker_screen.dart # 파일 권한 처리
│   │   └── services/
│   │       ├── auth_service.dart         # drive.file + 동의 상태 관리
│   │       ├── api_service.dart          # Drive + 동의/탈퇴 API
│   │       └── socket_service.dart
│   └── pubspec.yaml                      # url_launcher 추가
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SETUP_GUIDE.md
│   ├── LAUNCH_PLAN.md
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

### 4. KeyError: 'owner_id' (2026-03-02)
- **원인**: rooms 테이블은 `created_by` 컬럼인데 `owner_id`로 접근
- **해결**: `room['owner_id']` → `room['created_by']` 수정

### 5. 3GP 포맷 인식 실패 (2026-03-02)
- **원인**: Android 통화 녹음이 3GP 형식이지만 .m4a 확장자로 저장됨
- **해결**: ffprobe로 실제 포맷 감지 → ffmpeg로 MP3 변환

### 6. TranscriptionSegment 객체 접근 오류 (2026-03-02)
- **원인**: OpenAI API가 dict가 아닌 객체를 반환
- **해결**: `seg.get('start')` → `getattr(seg, 'start', 0)`

### 7. "내용 정리 중입니다" 메시지 잔류 (2026-03-02)
- **원인**: 진행 메시지가 DB에서 삭제되지 않음
- **해결**: Message.delete() 추가, STT 완료 후 삭제

### 8. datetime JSON 직렬화 오류 (2026-03-02)
- **원인**: socketio.emit에서 Python datetime 객체 직렬화 실패
- **해결**: `_serialize_msg()` 헬퍼 함수 추가 (ISO 문자열 변환)

### 9. 파일 접근 권한 (2026-03-02)
- **원인**: MANAGE_EXTERNAL_STORAGE 권한 누락
- **해결**: AndroidManifest.xml에 권한 추가, 권한 요청 UI 개선

### 10. PM2 환경변수 캐시 문제 (2026-03-02)
- **원인**: `pm2 restart --update-env`가 환경변수를 갱신하지 않음
- **해결**: `pm2 delete` → `pm2 start ecosystem.config.js` 방식 사용

### 11. OAuth audience 불일치 (2026-03-02)
- **원인**: 서버 GOOGLE_CLIENT_ID가 옛날 프로젝트 값으로 남아있음
- **해결**: PM2 delete → start로 환경변수 완전 갱신

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | /api/health | 헬스체크 |
| POST | /api/auth/google | Google 로그인 + Drive 토큰 교환 (**consent_required 포함**) |
| GET | /api/auth/me | 현재 사용자 정보 (drive_connected 포함) |
| GET | /api/auth/drive/status | Drive 연동 상태 |
| POST | /api/auth/drive/disconnect | Drive 연동 해제 |
| **POST** | **/api/auth/consent** | **동의 기록 저장** |
| **GET** | **/api/auth/consent/status** | **현재 동의 상태 조회** |
| **POST** | **/api/auth/consent/withdraw** | **동의 철회** |
| **DELETE** | **/api/auth/account** | **회원 탈퇴 (CASCADE 삭제)** |
| GET | /api/rooms | 채팅방 목록 |
| POST | /api/rooms | 채팅방 생성 (Drive 폴더 자동 생성) |
| GET | /api/rooms/:id | 채팅방 상세 정보 |
| POST | /api/rooms/join | 초대코드로 참여 |
| GET | /api/rooms/:id/members | 멤버 목록 |
| **DELETE** | **/api/rooms/:id/members/:uid** | **멤버 추방 (admin 전용)** |
| **GET** | **/api/rooms/:id/members/pending** | **승인 대기 멤버 목록 (admin)** |
| **POST** | **/api/rooms/:id/members/:uid/approve** | **멤버 승인 (admin)** |
| **POST** | **/api/rooms/:id/members/:uid/reject** | **멤버 거절 (admin)** |
| **DELETE** | **/api/rooms/:id** | **톡방 삭제 (admin, CASCADE)** |
| **PATCH** | **/api/rooms/:id** | **톡방 이름 변경 (admin)** |
| **POST** | **/api/rooms/:id/leave** | **톡방 나가기** |
| **POST** | **/api/rooms/:id/transfer-admin** | **관리자 권한 이전 (admin)** |
| **POST** | **/api/rooms/:id/favorite** | **즐겨찾기 토글** |
| POST | /api/rooms/:id/audio | 음성 업로드 → STT → Drive 저장 |
| GET | /api/audio/:id/download | 음성 다운로드 (로컬 → Drive 프록시) |
| GET | /api/rooms/:id/messages | 메시지 목록 (폴링용) |

---

## 연락처 / 참고

- GitHub: https://github.com/cs21jeon/Proptalk
- 서버 관리: SSH root@175.119.224.71
- 프로젝트 경로: C:\Users\ant19\projects\Proptalk
- Google Cloud: `speech-to-text-goldenrabbit` 프로젝트

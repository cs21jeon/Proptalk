# Proptalk 프로젝트 진행 현황

> 최종 업데이트: 2026-03-05 (파비콘 + 프로필 화면 UX 개선)

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
10. WebSocket 실시간 업데이트 (폴링 제거) ✅
11. **서비스 이용 동의 화면** (약관/개인정보/국외이전) ✅ **신규**
12. **음성 데이터 처리 동의 팝업** ✅ **신규**
13. **접속기록 감사 로그** (3개월 보관) ✅ **신규**
14. **RBAC 권한 강화** (admin/member 역할 적용) ✅ **신규**
15. **회원 탈퇴 + 동의 철회** ✅ **신규**
16. **프로필 화면** (법적 문서, 동의 관리, 계정 삭제, 로그아웃) ✅ **신규**
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
27. **디자인 시스템 구축** (Pretendard 폰트 + 시맨틱 컬러 + 간격/반경 상수 + 통합 테마) ✅ **신규**
28. **UI 모던화 Phase 1-6** (하드코딩 색상 교체, 로그인 애니메이션, 톡방 FAB 통합, 채팅 날짜구분선/메시지그룹핑, 다크모드) ✅ **신규**
29. **결제 시스템** (토스페이먼츠 웹결제, 시간팩+월구독, 자동결제/만료 크론) ✅ **신규**
30. **결제 웹페이지** (요금제 선택/결제/성공/실패/구독관리 5개 페이지) ✅ **신규**
31. **결제 약관** (결제/환불 전용 약관, 이용약관/개인정보처리방침 결제 조항 추가) ✅ **신규**
32. **D방식 웹결제 전환** (앱 내 외부결제 링크 제거, Google Play 정책 준수) ✅ **신규**
33. **요금제 안내 하단시트** (설정 > 충전/요금제에서 5개 플랜 카드 + 웹 충전 안내) ✅ **신규**
34. **BillingService 빌드 에러 수정** (빌드 중 notifyListeners 호출 → addPostFrameCallback) ✅ **신규**
35. **업로드 전 잔여 시간 검증** (ffprobe로 파일 길이 사전 확인, 잔여 시간 부족 시 업로드 차단) ✅ **신규**
36. **Proptalk 랜딩페이지** (Coming Soon, proppedia와 통일된 디자인, 8개 섹션) ✅ **신규**
37. **회사명 변경** (금토끼부동산 → 프롭넷 PropNet, 법적문서/proppedia/Flutter 전체 반영) ✅ **신규**
38. **법적 문서 라우트** (/proptalk/terms, /privacy, /payment-terms 3개 라우트 추가) ✅ **신규**
39. **Nginx 설정 정리** (미사용 config 삭제, n8n 완전 제거, SSL 인증서 정리) ✅ **신규**
40. **파비콘 통일** (랜딩페이지 + 법적문서 3개에 투명 풀사이즈 Proptalk 아이콘 적용) ✅ **신규**
41. **프로필 화면 UX 개선** (아바타 팝업메뉴 제거 → 탭하면 바로 프로필 화면, 설정→프로필 타이틀 변경) ✅ **신규**
42. **서버 확장성 개선** (Drive 연동 복구 + Sheets 로깅 + 폴링 제거 + ThreadPool + DB풀 확대) ✅ **신규**

---

## 현재 상태

### 완료된 작업 ✅

| 항목 | 상태 | 비고 |
|------|------|------|
| 서버 배포 | ✅ | goldenrabbit.biz:5060 |
| Nginx 프록시 | ✅ | /voiceroom/ + ^~ /proptalk/ 경로 |
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
| **디자인 시스템 구축** | ✅ | Pretendard 폰트, AppColors ThemeExtension, AppSpacing, AppTheme 통합 빌더 |
| **하드코딩 색상 교체** | ✅ | 6개 화면 50+ Colors.xxx → 테마 토큰 전면 교체 |
| **다크모드 토글** | ✅ | 설정 > 화면 모드 (시스템/라이트/다크), ThemeProvider + SharedPreferences |
| **로그인 화면 애니메이션** | ✅ | fade+slide 진입 애니메이션, 그라데이션 정리 |
| **동의 화면 진행률** | ✅ | LinearProgressIndicator + X/3 카운트 |
| **톡방 목록 FAB 통합** | ✅ | 2개 FAB → 1개 + 바텀시트, 빈 상태 개선 |
| **채팅 날짜 구분선** | ✅ | "2026년 3월 3일 화요일" 형태 |
| **채팅 메시지 그룹핑** | ✅ | 같은 발신자 연속 시 이름 숨김 |
| **Scroll-to-bottom FAB** | ✅ | 스크롤 200px 이상 시 하단 이동 버튼 |
| **전송 버튼 애니메이션** | ✅ | AnimatedSwitcher 마이크 ↔ 원형 전송 버튼 |
| **녹음 배너 펄스** | ✅ | 펄싱 빨간 점 애니메이션 + FilledButton |
| **답변 카드 보더 액센트** | ✅ | transcript 컨테이너 좌측 3px primary 보더 |
| **설정 화면 카드 그룹핑** | ✅ | 프로필 카드 확대, 섹션별 Card 래핑 |
| **오디오 피커 개선** | ✅ | 확장자 표시 타일, ListView.separated |
| **다크모드 채팅 버블 수정** | ✅ | primaryContainer + onPrimaryContainer 대비 개선 |
| **SafeArea 하단 잘림 수정** | ✅ | 설정/톡방목록/오디오피커 하단 패딩 추가 |
| **결제 DB 스키마** | ✅ | billing_plans, user_billing, payment_transactions, usage_logs 4개 테이블 |
| **과금 모델/서비스** | ✅ | models_billing.py, billing_service.py (잔액확인/차감/충전/구독/암호화) |
| **토스페이먼츠 연동** | ✅ | toss_service.py (결제승인/빌링키/자동결제/환불/웹훅검증) |
| **결제 API 엔드포인트** | ✅ | routes_billing.py (9개 엔드포인트: status/plans/order/confirm/webhook/cancel/refund/history/usage) |
| **결제 웹페이지** | ✅ | billing_web.py + templates/billing/ (요금제/결제/성공/실패/구독관리) |
| **Nginx 프록시 통합** | ✅ | ^~ /proptalk/ → Flask 5060 포트 (랜딩+법적문서+결제 통합) |
| **자동결제 크론** | ✅ | 구독갱신(03:00), 만료처리(04:00), 주문정리(매시간) |
| **결제 약관 (웹)** | ✅ | marketing/proptalk/billing-terms.html |
| **이용약관 결제조항 추가** | ✅ | terms-of-service.html 요금표+토스페이먼츠 반영 |
| **개인정보처리방침 토스 추가** | ✅ | privacy-policy.html 제3자 제공 토스페이먼츠 추가 |
| **Flutter 결제 서비스** | ✅ | billing_service.dart (ChangeNotifier) + billing_screen.dart |
| **Flutter 잔액 확인** | ✅ | chat_screen.dart 업로드 전 잔액 체크 + 충전 안내 다이얼로그 |
| **업로드 전 시간 검증** | ✅ | ffprobe 사전 길이 확인, 잔여 시간 < 파일 길이 시 업로드 차단 |
| **Flutter 설정 결제 섹션** | ✅ | settings_screen.dart 구독/결제 섹션 추가 |
| **서버 배포** | ✅ | DB 마이그레이션 + 코드 배포 + PM2 재시작 완료 |
| **API 테스트** | ✅ | 5개 API 엔드포인트 정상 응답 확인 |
| **웹 페이지 테스트** | ✅ | 4개 결제 웹페이지 정상 렌더링 확인 |
| **Proptalk 랜딩페이지** | ✅ | Coming Soon 페이지, proppedia와 통일된 디자인 (8개 섹션, 8장 스크린샷 갤러리) |
| **회사명 변경 (프롭넷)** | ✅ | 금토끼부동산 → 프롭넷 (PropNet), 법적문서 3개 + proppedia + Flutter terms.dart |
| **법적 문서 라우트** | ✅ | /proptalk/terms, /privacy, /payment-terms Flask 라우트 + 모든 HTML 링크 통일 |
| **Nginx ^~ /proptalk/ 통합** | ✅ | 별도 /proptalk/billing/ → 단일 ^~ /proptalk/ 블록으로 통합 |
| **Nginx 미사용 설정 삭제** | ✅ | voiceroom/n8n/building-service config 삭제, goldenrabbit.us SSL 인증서 삭제 |

### 서버 확장성 개선 (2026-03-07) ✅

| Phase | 항목 | 상태 | 비고 |
|-------|------|------|------|
| 1-1 | drive_service.py 공유 권한 + scope 추가 | ✅ | anyone/reader 권한, spreadsheets scope |
| 1-2 | routes_messages.py Drive 연동 복구 | ✅ | 방장 OAuth 토큰으로 업로드, 시그니처 수정 |
| 1-3 | Flutter Drive 링크 열기 | ✅ | drive_url 있으면 "Drive에서 열기", 없으면 "다운로드" |
| 1-4 | cleanup_service.py Drive 재시도 스케줄러 | ✅ | 매 1시간 실패 파일 재시도 |
| 1-5 | sheets_service.py Google Sheets 로깅 | ✅ | 신규 파일, 11개 컬럼, 방별 스프레드시트 |
| 2-1 | Flutter 폴링 제거 | ✅ | 3초 폴링 완전 제거, WebSocket 재연결 시 1회 동기화 |
| 3-1 | ThreadPoolExecutor 적용 | ✅ | max_workers=4, threading.Thread 대체 |
| 3-2 | DB 커넥션 풀 확대 | ✅ | minconn=5, maxconn=20 |
| 3-2+ | models.py drive_url 쿼리 추가 | ✅ | Message.list_for_room에 af.drive_url 포함 |

### 테스트 진행 중 🔄

| 항목 | 상태 | 비고 |
|------|------|--------|
| Google Drive 전체 플로우 | 🔄 | 로그인 → Drive 동의 → 방 생성 → 업로드 → Drive 저장 |
| OAuth 동의화면 프로덕션 전환 | 🔄 | 현재 테스트 모드 (100명 제한) |
| 법적 컴플라이언스 전체 플로우 | 🔄 | 로그인 → 동의 화면 → 음성 동의 → 설정/철회 |
| 토스페이먼츠 테스트 키 연동 | 🔄 | 사업자 등록 → 토스 가입 → 테스트 키 발급 → 실결제 테스트 |
| Flutter 결제 UI 테스트 | 🔄 | 앱 빌드 → 설정화면 결제 섹션 → 잔액 부족 다이얼로그 |
| 결제 전체 플로우 테스트 | 🔄 | 요금제 선택 → 토스 결제 → 시간 충전 → 업로드 차감 |

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

### Nginx 설정
- **설정 파일 (정본)**: `/home/webapp/goldenrabbit/config/nginx/goldenrabbit.conf`
- **심볼릭 링크**: `/etc/nginx/sites-enabled/goldenrabbit` → config/nginx/goldenrabbit.conf
- **주의**: `scripts/setup.sh`가 config/nginx/에서 심볼릭 링크를 생성하므로, sites-enabled 직접 수정 금지
- **Proptalk 프록시**: `location ^~ /proptalk/` → Flask 5060 포트 (랜딩+법적문서+결제 통합)

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
- `cleanup_service.py` - 24시간 파일 삭제 + **3개월 초과 감사 로그 삭제** + **구독 자동결제/만료 크론**
- `models_billing.py` - **결제 모델 (BillingPlan, UserBilling, PaymentTransaction, UsageLog)**
- `billing_service.py` - **핵심 과금 로직 (잔액확인/차감/충전/구독/AES-256 암호화/ffprobe 사전검증)**
- `toss_service.py` - **토스페이먼츠 API 래퍼 (결제승인/빌링키/자동결제/환불/웹훅)**
- `routes_billing.py` - **결제 API 엔드포인트 9개**
- `billing_web.py` - **웹페이지 라우트 (랜딩페이지 + 법적문서 3개 + 결제 5개, Jinja2 템플릿)**
- `templates/billing/` - **결제 웹 UI (base/plans/checkout/success/fail/manage.html)**
- `init_billing.sql` - **결제 DB 스키마 (4 테이블 + 5 플랜 데이터)**

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

## 결제 시스템: 토스페이먼츠 웹결제 ✅

### 결제 방식
- **웹결제** (Google Play 인앱결제 X) → 수수료 4.3% (넷플릭스/스포티파이 모델)
- 앱 → url_launcher로 웹 결제 페이지 → 토스페이먼츠 SDK → 결제 → 앱 확인
- billingKey 기반 자동결제 (월구독)

### 요금제
| 플랜 | 타입 | 포함 시간 | 가격 (VAT 포함) | 비고 |
|------|------|-----------|-----------------|------|
| 무료 체험 | 무료 | 10분 | 0원 | 계정당 평생 |
| 1시간 팩 | 일회성 | 60분 | 9,900원 | 만료 없음 |
| 10시간 팩 | 일회성 | 600분 | 79,000원 | 만료 없음, 시간당 132원 |
| Basic 30시간 | 월구독 | 1,800분 | 29,000원/월 | 초과 시 12원/분 |
| Pro 90시간 | 월구독 | 5,400분 | 79,000원/월 | 초과 시 12원/분 |

### 웹페이지 URL
| URL | 설명 |
|-----|------|
| `goldenrabbit.biz/proptalk/` | **랜딩페이지 (Coming Soon)** |
| `goldenrabbit.biz/proptalk/terms` | **이용약관** |
| `goldenrabbit.biz/proptalk/privacy` | **개인정보 처리방침** |
| `goldenrabbit.biz/proptalk/payment-terms` | **결제/환불 약관** |
| `goldenrabbit.biz/proptalk/billing/` | 요금제 선택 |
| `goldenrabbit.biz/proptalk/billing/checkout` | 토스 SDK 결제창 |
| `goldenrabbit.biz/proptalk/billing/success` | 결제 성공 |
| `goldenrabbit.biz/proptalk/billing/fail` | 결제 실패 |
| `goldenrabbit.biz/proptalk/billing/manage` | 구독 관리 |

### 보안
| 항목 | 조치 |
|------|------|
| billingKey | AES-256-CBC 암호화 저장 (BILLING_ENCRYPTION_KEY 환경변수) |
| Toss Secret Key | 환경변수만, 코드 하드코딩 금지 |
| 웹훅 검증 | HMAC-SHA256 시그니처 검증 |
| 결제 금액 | 서버에서 order_id 기준 금액 일치 확인 |
| 결제 로그 | 5년 보관 (전자상거래법) |

### 환경변수 (ecosystem.config.js에 추가)
```
TOSS_CLIENT_KEY      # 토스페이먼츠 클라이언트 키
TOSS_SECRET_KEY      # 토스페이먼츠 시크릿 키
TOSS_WEBHOOK_SECRET  # 토스 웹훅 시크릿
BILLING_ENCRYPTION_KEY  # AES-256 billingKey 암호화 키 (32바이트)
```

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

-- 결제 시스템 (2026-03-04)
-- billing_plans: 요금제 정의 (5개 플랜)
-- user_billing: 사용자별 잔여 시간/구독 상태/billingKey (AES-256 암호화)
-- payment_transactions: 결제 이력 5년 보관 (order_id, payment_key, raw_response JSONB)
-- usage_logs: 사용량 차감 기록 (seconds_used, seconds_before, seconds_after)
-- 상세 스키마: server/init_billing.sql 참조
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
- **설정 화면** (법적 문서, 동의 관리, 계정 삭제, **다크모드 토글**)
- **디자인 시스템** (Pretendard 폰트, 시맨틱 컬러, 통합 테마, 다크모드 지원)

### 주요 패키지
- `google_sign_in` - OAuth + drive.file 스코프
- `flutter_markdown` - 요약 마크다운 렌더링
- `permission_handler` - MANAGE_EXTERNAL_STORAGE
- `record` - 녹음
- `socket_io_client` - WebSocket
- `url_launcher` - 법적 문서 외부 링크
- `shared_preferences` - 음성 동의 상태 + 다크모드 설정 로컬 저장

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
- `2026-03-03` - 디자인 시스템 구축 + UI 모던화 Phase 1-6 (테마/폰트/다크모드/애니메이션/SafeArea)
- `2026-03-04` - 결제 시스템 구현 (토스페이먼츠 웹결제, DB+API+웹+Flutter+크론+법적문서)
- `2026-03-05` - 랜딩페이지 생성 + 회사명 변경 (프롭넷) + 법적문서 라우트 + nginx 정리

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

### 우선순위 3: 결제 시스템 (토스페이먼츠) ✅ 구현 완료 (2026-03-04)
- [x] DB 스키마 (billing_plans, user_billing, payment_transactions, usage_logs)
- [x] 과금 모델/서비스 (잔액 확인, 시간 차감, 충전, 구독 활성화/해지)
- [x] 토스페이먼츠 API 연동 (결제승인, 빌링키, 자동결제, 환불, 웹훅)
- [x] 결제 API 엔드포인트 9개 (status/plans/order/confirm/webhook/cancel/refund/history/usage)
- [x] 결제 웹페이지 5개 (요금제 선택/결제/성공/실패/구독관리)
- [x] 음성 업로드 시 잔액 확인 + 사용 후 차감 로직 (routes_messages.py)
- [x] 자동결제 크론 (구독갱신 03:00, 만료처리 04:00, 주문정리 매시간)
- [x] billingKey AES-256-CBC 암호화 저장
- [x] Flutter 결제 서비스 (BillingService ChangeNotifier)
- [x] Flutter 결제 화면 (billing_screen.dart)
- [x] Flutter 업로드 전 잔액 확인 다이얼로그
- [x] Flutter 설정 화면 결제 섹션
- [x] 결제 약관 페이지 (billing-terms.html)
- [x] 이용약관/개인정보처리방침 결제 조항 업데이트
- [x] 서버 배포 (DB 마이그레이션 + 코드 배포 + Nginx 프록시 + PM2 재시작)
- [x] API 테스트 (5개 엔드포인트 정상 확인)
- [x] 웹 페이지 테스트 (4개 페이지 정상 렌더링 확인)
- [ ] 토스페이먼츠 테스트 키 발급 → 실결제 테스트
- [ ] Flutter 앱 빌드 → 결제 UI 테스트

### 우선순위 4: 랜딩페이지 + 브랜딩 ✅ 완료 (2026-03-05)
- [x] Proptalk 랜딩페이지 (Coming Soon) - proppedia와 통일된 디자인
- [x] 8개 섹션: 헤더/히어로/기능/스크린샷/추가기능/타겟사용자/요금제/CTA+푸터
- [x] 스크린샷 갤러리 (8장, scroll-snap)
- [x] 회사명 변경: 금토끼부동산 → 프롭넷 (PropNet)
- [x] 법적 문서 3개 회사명 업데이트 (이용약관/개인정보/결제약관)
- [x] proppedia 페이지 회사명 업데이트 (서버 직접 수정)
- [x] Flutter terms.dart URL + 회사명 업데이트
- [x] 법적 문서 Flask 라우트 3개 추가 (/terms, /privacy, /payment-terms)
- [x] Nginx ^~ /proptalk/ 통합 프록시 (billing 별도 → 전체 통합)
- [x] 미사용 nginx config 삭제 (voiceroom/n8n/building-service)
- [x] n8n 관련 아티팩트 완전 제거 (goldenrabbit.us SSL 인증서 삭제)
- [x] 서버 배포 (SCP + PM2 재시작 + nginx reload)

### 우선순위 5: 앱 출시 준비
- [ ] 에러 핸들링 강화
- [ ] Google Play Console 등록

### 우선순위 6: 개선
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
- [x] **디자인 시스템 구축** (Pretendard 폰트 + AppColors + AppSpacing + AppTheme)
- [x] **하드코딩 색상 전면 교체** (50+ Colors.xxx → 테마 토큰)
- [x] **다크모드 토글** (설정 > 화면 모드)
- [x] **로그인 화면 애니메이션** (fade+slide)
- [x] **채팅 UX 개선** (날짜구분선, 메시지그룹핑, scroll-to-bottom, 전송 애니메이션, 녹음 펄스)
- [x] **설정/오디오피커 UI 개선** (카드 그룹핑, 파일 타일 개선)
- [x] **SafeArea 하단 잘림 수정** (설정/톡방목록/오디오피커)
- [ ] UI/UX 추가 개선 (스켈레톤 로딩, 이미지 첨부 등)

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
│   ├── cleanup_service.py      # 24시간 삭제 + 구독 자동결제/만료 크론
│   ├── models_billing.py       # 결제 모델 (BillingPlan, UserBilling, PaymentTransaction, UsageLog)
│   ├── billing_service.py      # 과금 로직 (잔액확인/차감/충전/구독/AES-256 암호화)
│   ├── toss_service.py         # 토스페이먼츠 API (결제승인/빌링키/자동결제/환불)
│   ├── routes_billing.py       # 결제 API 엔드포인트 9개
│   ├── billing_web.py          # 웹페이지 라우트 (랜딩+법적문서+결제)
│   ├── templates/billing/      # 결제 웹 UI (6개 HTML)
│   ├── init_billing.sql        # 결제 DB 스키마
│   ├── ecosystem.config.js     # PM2 환경변수
│   └── deploy/                 # 배포용 파일
│
├── marketing/proptalk/         # **신규** 웹 정적 페이지
│   ├── index.html              # 랜딩페이지 (Coming Soon)
│   ├── terms-of-service.html   # 이용약관
│   ├── privacy-policy.html     # 개인정보 처리방침
│   └── billing-terms.html      # 결제/환불 약관
│
├── flutter/                    # Flutter 앱
│   ├── lib/
│   │   ├── main.dart                    # 동의 화면 라우팅 + ThemeProvider
│   │   ├── constants/
│   │   │   └── terms.dart               # 법적 문서 텍스트 (약관/처리방침/동의문)
│   │   ├── theme/                       # **신규** 디자인 시스템
│   │   │   ├── app_colors.dart          # 시맨틱 컬러 ThemeExtension (light/dark)
│   │   │   ├── app_spacing.dart         # 간격/반경 상수
│   │   │   ├── app_theme.dart           # 통합 테마 빌더 (light/dark)
│   │   │   └── theme_provider.dart      # 다크모드 토글 (ChangeNotifier)
│   │   ├── screens/
│   │   │   ├── login_screen.dart        # 애니메이션 + 법적 문서 링크
│   │   │   ├── consent_screen.dart      # 서비스 동의 + 진행률 표시
│   │   │   ├── rooms_screen.dart        # FAB 통합 + 헤더 확대
│   │   │   ├── settings_screen.dart     # 카드 그룹핑 + 다크모드 토글
│   │   │   ├── chat_screen.dart         # 날짜구분선 + 메시지그룹핑 + 전송 애니메이션
│   │   │   └── audio_picker_screen.dart # 파일 타일 개선
│   │   └── services/
│   │       ├── auth_service.dart         # drive.file + 동의 상태 관리
│   │       ├── api_service.dart          # Drive + 동의/탈퇴 + 결제 API
│   │       ├── billing_service.dart      # 결제 서비스 (ChangeNotifier)
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
| **GET** | **/api/billing/status** | **잔여 시간, 플랜, 구독 상태** |
| **GET** | **/api/billing/plans** | **활성 요금제 목록 (공개)** |
| **POST** | **/api/billing/order** | **주문 생성 → order_id 반환** |
| **POST** | **/api/billing/confirm** | **토스 결제 승인 확인** |
| **POST** | **/api/billing/webhook** | **토스 웹훅 수신** |
| **POST** | **/api/billing/subscription/cancel** | **구독 해지** |
| **POST** | **/api/billing/refund** | **환불 요청 (7일 이내)** |
| **GET** | **/api/billing/history** | **결제 이력** |
| **GET** | **/api/billing/usage** | **사용량 이력** |

---

## 연락처 / 참고

- GitHub: https://github.com/cs21jeon/Proptalk
- 서버 관리: SSH root@175.119.224.71
- 프로젝트 경로: C:\Users\ant19\projects\Proptalk
- Google Cloud: `speech-to-text-goldenrabbit` 프로젝트

# IdP Backend System (간편인증 백엔드 서버)

[![Django 5.2.7](https://img.shields.io/badge/Django-5.2.7-green.svg)](https://www.djangoproject.com/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![SQLite3](https://img.shields.io/badge/Database-SQLite3-lightgrey.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**IdP(Identity Provider) Backend System** - Django MTV 패턴 기반 본인인증 시스템

본 프로젝트는 토스(Toss)와 같은 간편인증 서비스를 구현한 백엔드 시스템으로, 서비스 제공자(SP)의 인증 요청을 받아 사용자 신원을 확인하고 CI/DI를 안전하게 전달합니다.

**핵심 기능:**
- ✅ **인증 요청 처리:** 서비스 제공자로부터 인증 요청 수신 및 관리
- ✅ **사용자 인증:** PIN 코드 기반 간편 인증
- ✅ **CI/DI 암호화:** AES-256-GCM 암호화로 민감정보 보호
- ✅ **감사 로그:** 모든 인증 이벤트 자동 기록
- ✅ **RBAC:** 역할 기반 접근 제어 (USER, ADMIN, SERVICE_PROVIDER)
- ✅ **동시성 제어:** SELECT FOR UPDATE로 Race Condition 방어

**프로젝트 구조:**
- **Backend:** Django 5.2.7 (MTV 패턴)
- **Database:** SQLite3 (7 views, 6 procedures, 8 triggers)
- **API:** RESTful API (DRF)
- **UI:** Bootstrap 5.3 + Font Awesome
- **Security:** AES-256-GCM, bcrypt, CSRF, XSS 방어

---

## 🎯 MTV 패턴 적용 현황

이 프로젝트는 Django의 **MTV (Model-Template-View)** 아키텍처 패턴을 완전히 적용했습니다:

### ✅ Model (모델 레이어)
- **9개 Django 모델**: User, UserRole, UserRoleAssignment, ServiceProvider, EncryptionKey, ServiceProviderStatistics, AuthTransaction, NotificationLog, AuditLog
- **데이터 무결성**: PK/FK/UNIQUE/CHECK 제약조건, 10+ indexes
- **보안**: CI/DI 필드 AES-256-GCM 암호화, PIN bcrypt 해싱
- **위치**: `accounts/models.py`, `services/models.py`, `auth_transactions/models.py`, `audit_logs/models.py`

### ✅ Template (템플릿 레이어)
- **Bootstrap 5.3**: 반응형 웹 디자인
- **템플릿 계층 구조**:
  - `base.html`: 기본 레이아웃 (navbar, footer, messages)
  - `home.html`: 랜딩 페이지
  - `dashboard.html`: 사용자 대시보드
  - `accounts/`: login.html, register.html, profile.html, password_change.html, pin_change.html
  - `auth_transactions/`: auth_history.html, transaction_detail.html
- **UI/UX**: Font Awesome 아이콘, 커스텀 CSS/JS
- **위치**: `templates/`, `static/css/`, `static/js/`

### ✅ View (뷰 레이어)
- **Class-Based Views (CBVs)** 사용:
  - `HomeView`, `DashboardView`: TemplateView
  - `UserLoginView`: LoginView
  - `UserRegistrationView`: CreateView
  - `ProfileView`, `ProfileUpdateView`: UpdateView
  - `AuthHistoryListView`: ListView (페이지네이션, 필터링)
  - `TransactionDetailView`: DetailView
  - `PasswordChangeView`, `PINChangeView`: FormView
- **Django Forms**: 8개 폼 클래스 (UserRegistrationForm, CustomLoginForm, PINConfirmForm 등)
- **RESTful API**: DRF 기반 Function-Based Views (auth_request, auth_confirm, auth_status)
- **위치**: `accounts/views.py`, `accounts/forms.py`, `auth_transactions/web_views.py`, `auth_transactions/views.py`

### 📁 URL 구조
```
/                         → HomeView (랜딩 페이지)
/dashboard/               → DashboardView (사용자 대시보드)
/accounts/login/          → UserLoginView (로그인)
/accounts/register/       → UserRegistrationView (회원가입)
/accounts/profile/        → ProfileView (프로필 조회)
/auth/history/            → AuthHistoryListView (인증 이력)
/auth/detail/<uuid>/      → TransactionDetailView (인증 상세)
/api/v1/auth/api/request/ → REST API (인증 요청)
/admin/                   → Django Admin
```

---

## 🚀 프로젝트명: "Simple-ID" - 간편 본인확인(IdP) 백엔드 서버
1. 프로젝트 개요
목표: 토스(Toss)와 같은 IdP(신원 제공자)가 되어, '이용기관(서비스)'의 요청을 받아 '사용자'의 신원을 확인하고 그 결과를(CI/DI) 안전하게 전달하는 백엔드 API 서버를 구축합니다.

핵심: 실시간 인증 요청의 '상태'를 관리하고, 사용자-서비스 간의 인증 데이터를 RDBMS(MySQL)에 로그로 기록하며, 민감정보(CI/DI)를 관리하는 로직에 집중합니다.

등장인물 (DB 모델):

User (사용자): 우리(IdP) 서비스에 가입된 회원. (토스 앱 사용자)

ServiceProvider (이용기관): 본인확인을 요청하는 외부 서비스. (예: 쇼핑몰)

AuthTransaction (인증 내역): 1회성 인증 요청의 라이프사이클을 관리하는 핵심 테이블.

2. RDBMS(MySQL) / Django 모델 설계
1. User (Django User 모델 확장)

사용자(인증 대상) 정보입니다.

username (ID), password (해시됨)

phone_number (CharField, unique=True): 사용자를 식별하는 키 (03번 Push 발송 대상)

pin_code (CharField, Hashed): 사용자의 간편 인증 비밀번호 (6자리 숫자 등)

ci (CharField, unique=True, Encrypted): 사용자 고유 식별정보 (시뮬레이션을 위해 UUID 사용)

di (CharField, unique=True, Encrypted): 서비스 연계정보 (시뮬레이션을 위해 UUID 사용)

2. ServiceProvider (이용기관)

우리 IdP에 등록된 '고객사' 목록입니다.

service_name (CharField): "A 쇼핑몰", "B 게임사"

client_id (CharField, unique=True): 서비스 식별용 공개 ID

client_secret (CharField, Hashed): 서비스 인증용 비밀 키 (02번 요청 시 인증)

callback_url (URLField): 05번 인증 결과를 전달(POST)해 줄 URL

3. AuthTransaction (인증 내역)

이 프로젝트의 핵심 테이블입니다. 1회성 인증 요청을 관리합니다.

transaction_id (UUIDField, PrimaryKey): 이 거래의 고유 ID

service_provider (ForeignKey to ServiceProvider): 누가 요청했는가?

user (ForeignKey to User): 누구를 인증해야 하는가?

status (CharField, choices=PENDING, COMPLETED, FAILED, EXPIRED): 인증 상태

created_at (DateTimeField): 요청 생성 시간

expires_at (DateTimeField): 만료 시간 (예: 3분)

auth_code (CharField, nullable=True): 사용자가 인증 성공 시 발급하는 1회용 코드

3. API 흐름별 기획 (이미지 01~05 매핑)
[Setup] 이용기관 등록 (Django Admin 활용)
우리가 ServiceProvider 테이블에 'A 쇼핑몰'의 client_id, client_secret, callback_url을 미리 등록해둡니다.

[01, 02] 본인확인 요청 (이용기관 → 우리 서버)
POST /api/v1/auth/request/

호출자: 이용기관 (ServiceProvider)

인증: client_id와 client_secret을 헤더에 담아 서버 간 인증.

Request Body: { "user_phone_number": "010-1234-5678" }

DB 로직 (Transaction):

ServiceProvider 인증.

user_phone_number로 User 조회.

AuthTransaction 테이블에 새 레코드 생성 ( status='PENDING', expires_at='now+3min' ).

고유한 transaction_id 발급.

Response: { "transaction_id": "..." }

[03] Push 발송 (우리 서버 → 사용자)
위 [01, 02] API가 성공하면, 우리 서버는 (실제로는 Push 서버를 호출하겠지만) **"사용자에게 인증 요청이 갔다"**고 가정합니다.

(토이 프로젝트에서는 이 부분을 생략하고, 사용자가 이 transaction_id를 아는 상태에서 다음 단계를 진행한다고 시뮬레이션합니다.)

[04] 사용자 인증 (사용자 → 우리 서버)
사용자가 Push 알림을 받고 PIN 번호를 입력하는 단계입니다.

POST /api/v1/auth/confirm/

호출자: 사용자 (의 앱/웹 - Postman으로 시뮬레이션)

Request Body: { "transaction_id": "...", "pin_code": "123456" }

DB 로직 (Transaction):

transaction_id로 AuthTransaction 조회.

status가 PENDING이고 만료되지 않았는지 확인.

연결된 User의 pin_code가 일치하는지 확인.

성공 시: AuthTransaction의 status를 COMPLETED로 변경하고, 임의의 auth_code를 생성해 저장.

Response: { "status": "COMPLETED" }

(비동기) 이 시점에 [05]번 로직(Callback)을 트리거합니다.

[05] 인증 결과 + CI, DI 전달 (우리 서버 → 이용기관)
우리 서버가 ServiceProvider의 callback_url로 결과를 POST해줍니다.

POST {service_provider.callback_url}

호출자: 우리 서버 (IdP)

Request Body (Encrypted):

AuthTransaction에서 auth_code와 User를 조회.

User 테이블에서 ci, di를 조회.

{ "auth_code": "...", "ci": "...", "di": "..." } 데이터를 생성.

(이미지 참조) ServiceProvider와 미리 약속된 키로 이 Body를 AES256-GCM-NoPadding으로 암호화하여 전송.

4. 🔒 이 프로젝트가 동형암호(HE) 엔지니어에게 좋은 이유
민감정보(CI/DI) 관리: 이 프로젝트의 핵심 DB인 User 테이블은 절대 평문으로 저장하면 안 되는 CI/DI를 다룹니다. RDBMS에 암호화된 필드를 저장하고(Field Level Encryption), 이를 API로 제공하는 경험은 필수적입니다.

데이터 흐름의 제어: 동형암호가 '데이터 자체'를 보호한다면, 이 프로젝트는 **'데이터 접근 권한'**을 제어합니다. "A 쇼핑몰이 B 유저의 CI를 요청할 자격이 있는가?"를 실시간 트랜잭션(AuthTransaction)을 통해 관리하는 것입니다.

암호화 적용점: 이미지에 명시된 AES256-GCM처럼, [05] 단계에서 RDBMS에 저장된 민감정보(CI/DI)를 꺼내어 특정 대상(이용기관)을 위해 암호화한 뒤 전송하는 파이프라인을 직접 구현해 볼 수 있습니다.

---

## 📋 과제 평가 기준에 따른 프로젝트 설계

### 1. 학습 목표 적합성 (20%)

#### 1.1 정규화 (Normalization)
- **1NF 적용**: 모든 테이블의 컬럼은 원자값(Atomic Value)만 저장
  - User 테이블: phone_number는 단일 값 저장 (배열 X)
  - AuthTransaction: status는 단일 상태값만 보유
  
- **2NF 적용**: 부분 함수 종속 제거
  - AuditLog 테이블: (user_id, timestamp) 복합키에서 user_name은 user_id에만 종속되므로 User 테이블로 분리
  
- **3NF 적용**: 이행적 함수 종속 제거
  - ServiceProvider: service_name → service_category → category_description의 이행 종속을 제거하기 위해 별도 참조 관리

#### 1.2 트랜잭션 (Transaction)
핵심 트랜잭션 경계 정의:

1. **인증 요청 트랜잭션** (`/api/v1/auth/request/`)
   - ServiceProvider 인증 확인
   - User 존재 여부 확인
   - AuthTransaction 생성 (PENDING 상태)
   - 만료시간 설정 (3분)
   - **ACID 보장**: Atomicity (모두 성공/실패), Consistency (status 제약), Isolation (REPEATABLE READ), Durability (커밋 후 영구 저장)

2. **인증 확인 트랜잭션** (`/api/v1/auth/confirm/`)
   - AuthTransaction 조회 및 잠금 (SELECT FOR UPDATE)
   - 만료 여부 확인
   - PIN 검증 (bcrypt)
   - 상태 업데이트 (PENDING → COMPLETED)
   - auth_code 생성 및 저장
   - AuditLog 기록

3. **콜백 전송 트랜잭션**
   - AuthTransaction 및 User 데이터 조회
   - CI/DI 복호화
   - AES256-GCM 암호화
   - 외부 API 호출 및 결과 로깅

#### 1.3 인덱스 (Index) 설계
```sql
-- 성능 최적화를 위한 인덱스 전략

-- 1) User 테이블
CREATE UNIQUE INDEX idx_user_phone ON accounts_user(phone_number);
CREATE UNIQUE INDEX idx_user_ci ON accounts_user(ci);
CREATE INDEX idx_user_created ON accounts_user(created_at DESC);

-- 2) AuthTransaction 테이블 (핵심 성능 포인트)
CREATE INDEX idx_authtx_status_expires ON auth_transactions_authtransaction(status, expires_at)
  WHERE status = 'PENDING';  -- Partial Index for active transactions
CREATE INDEX idx_authtx_user_created ON auth_transactions_authtransaction(user_id, created_at DESC);
CREATE INDEX idx_authtx_sp_created ON auth_transactions_authtransaction(service_provider_id, created_at DESC);

-- 3) AuditLog 테이블
CREATE INDEX idx_audit_user_time ON audit_logs_auditlog(user_id, timestamp DESC);
CREATE INDEX idx_audit_action_time ON audit_logs_auditlog(action, timestamp DESC);

-- Covering Index (커버링 인덱스) 예시
CREATE INDEX idx_authtx_covering ON auth_transactions_authtransaction(
  user_id, status, created_at
) INCLUDE (transaction_id, auth_code);
```

#### 1.4 뷰 (View)
```sql
-- 1) 민감정보 마스킹 뷰 (보안 목적)
CREATE VIEW v_user_masked AS
SELECT 
  id, username,
  CONCAT(LEFT(phone_number, 4), '-****-****') AS phone_number_masked,
  '*********************' AS ci_masked,
  '*********************' AS di_masked,
  created_at, last_login
FROM accounts_user;

-- 2) 인증 통계 뷰 (통계/분석 목적)
CREATE VIEW v_auth_statistics AS
SELECT 
  sp.service_name,
  DATE(at.created_at) AS auth_date,
  COUNT(*) AS total_requests,
  SUM(CASE WHEN at.status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed,
  SUM(CASE WHEN at.status = 'FAILED' THEN 1 ELSE 0 END) AS failed,
  SUM(CASE WHEN at.status = 'EXPIRED' THEN 1 ELSE 0 END) AS expired,
  ROUND(AVG(TIMESTAMPDIFF(SECOND, at.created_at, at.updated_at)), 2) AS avg_processing_time
FROM auth_transactions_authtransaction at
JOIN services_serviceprovider sp ON at.service_provider_id = sp.id
GROUP BY sp.service_name, DATE(at.created_at);

-- 3) 감사 로그 요약 뷰
CREATE VIEW v_audit_summary AS
SELECT 
  u.username,
  al.action,
  COUNT(*) AS action_count,
  MAX(al.timestamp) AS last_action_time
FROM audit_logs_auditlog al
JOIN accounts_user u ON al.user_id = u.id
GROUP BY u.username, al.action;
```

#### 1.5 프로시저 (Stored Procedure)
```sql
-- 1) 만료된 인증 요청 자동 처리
DELIMITER //
CREATE PROCEDURE expire_pending_transactions()
BEGIN
  DECLARE affected_rows INT;
  
  START TRANSACTION;
  
  UPDATE auth_transactions_authtransaction
  SET status = 'EXPIRED', updated_at = NOW()
  WHERE status = 'PENDING' 
    AND expires_at < NOW();
  
  SET affected_rows = ROW_COUNT();
  
  -- 감사 로그 기록
  INSERT INTO audit_logs_auditlog (user_id, action, details, timestamp)
  SELECT 
    user_id, 
    'AUTH_EXPIRED',
    CONCAT('Auto-expired transaction: ', transaction_id),
    NOW()
  FROM auth_transactions_authtransaction
  WHERE status = 'EXPIRED' AND updated_at >= DATE_SUB(NOW(), INTERVAL 1 SECOND);
  
  COMMIT;
  
  SELECT CONCAT('Expired ', affected_rows, ' transactions') AS result;
END //
DELIMITER ;

-- 2) 서비스 제공자별 통계 생성
DELIMITER //
CREATE PROCEDURE get_service_statistics(IN sp_id INT, IN days INT)
BEGIN
  SELECT 
    DATE(created_at) AS date,
    COUNT(*) AS total_requests,
    SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) AS success_count,
    ROUND(SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS success_rate
  FROM auth_transactions_authtransaction
  WHERE service_provider_id = sp_id
    AND created_at >= DATE_SUB(NOW(), INTERVAL days DAY)
  GROUP BY DATE(created_at)
  ORDER BY date DESC;
END //
DELIMITER ;
```

#### 1.6 트리거 (Trigger)
```sql
-- 1) 인증 상태 변경 시 자동 감사 로그 기록
DELIMITER //
CREATE TRIGGER trg_auth_status_change
AFTER UPDATE ON auth_transactions_authtransaction
FOR EACH ROW
BEGIN
  IF OLD.status != NEW.status THEN
    INSERT INTO audit_logs_auditlog (user_id, action, details, ip_address, timestamp)
    VALUES (
      NEW.user_id,
      'AUTH_STATUS_CHANGE',
      CONCAT('Status changed from ', OLD.status, ' to ', NEW.status, 
             ' for transaction ', NEW.transaction_id),
      '0.0.0.0',  -- API에서 실제 IP 기록 필요
      NOW()
    );
  END IF;
END //
DELIMITER ;

-- 2) 사용자 정보 변경 감사
DELIMITER //
CREATE TRIGGER trg_user_update_audit
AFTER UPDATE ON accounts_user
FOR EACH ROW
BEGIN
  INSERT INTO audit_logs_auditlog (user_id, action, details, timestamp)
  VALUES (
    NEW.id,
    'USER_INFO_UPDATE',
    CONCAT('User information updated: ', 
           IF(OLD.phone_number != NEW.phone_number, 'phone_number, ', ''),
           IF(OLD.pin_code != NEW.pin_code, 'pin_code', '')),
    NOW()
  );
END //
DELIMITER ;

-- 3) 로그인 실패 횟수 추적 (계정 잠금 방지)
DELIMITER //
CREATE TRIGGER trg_login_attempt
AFTER INSERT ON audit_logs_auditlog
FOR EACH ROW
BEGIN
  DECLARE fail_count INT;
  
  IF NEW.action = 'LOGIN_FAILED' THEN
    SELECT COUNT(*) INTO fail_count
    FROM audit_logs_auditlog
    WHERE user_id = NEW.user_id
      AND action = 'LOGIN_FAILED'
      AND timestamp >= DATE_SUB(NOW(), INTERVAL 10 MINUTE);
    
    IF fail_count >= 5 THEN
      UPDATE accounts_user
      SET is_active = FALSE
      WHERE id = NEW.user_id;
    END IF;
  END IF;
END //
DELIMITER ;
```

### 2. 데이터 모델 복잡도 (10%)

#### 2.1 Entity 목록 (9개)

| No | Entity | 핵심 속성 | PK | FK | UK | 예상 행 수 |
|----|--------|----------|----|----|----|---------| 
| 1 | User | username, phone_number, pin_code, ci, di | id | - | phone_number, ci, di | 10,000+ |
| 2 | ServiceProvider | service_name, client_id, client_secret, callback_url | id | - | client_id | 100+ |
| 3 | AuthTransaction | transaction_id, status, expires_at, auth_code | transaction_id (UUID) | user_id, service_provider_id | auth_code | 1,000,000+ |
| 4 | AuditLog | action, details, ip_address, timestamp | id | user_id | - | 10,000,000+ |
| 5 | UserRole | role_name, permissions | id | - | role_name | 10 |
| 6 | UserRoleAssignment | - | id | user_id, role_id | (user_id, role_id) | 10,000+ |
| 7 | EncryptionKey | key_name, key_value, algorithm, created_at | id | service_provider_id | key_name | 100+ |
| 8 | NotificationLog | notification_type, message, sent_at, status | id | user_id, transaction_id | - | 1,000,000+ |
| 9 | ServiceProviderStatistics | date, total_requests, success_rate | id | service_provider_id | (service_provider_id, date) | 100,000+ |

#### 2.2 관계 (Relationship)

**1:N 관계:**
- User(1) → AuthTransaction(N): 한 사용자는 여러 인증 요청
- ServiceProvider(1) → AuthTransaction(N): 한 서비스는 여러 인증 요청
- User(1) → AuditLog(N): 한 사용자는 여러 감사 로그

**M:N 관계:**
- User(M) ↔ UserRole(N): 사용자-역할 다대다 관계
  - 중간 테이블: UserRoleAssignment
  - 한 사용자가 여러 역할 보유 가능 (예: USER + SERVICE_ADMIN)

**약한 엔티티 (Weak Entity):**
- EncryptionKey는 ServiceProvider에 종속
  - ServiceProvider 삭제 시 관련 키도 삭제 (ON DELETE CASCADE)

#### 2.3 ERD (Entity Relationship Diagram)

```
┌─────────────────┐
│   UserRole      │
│─────────────────│
│ PK: id          │
│ UK: role_name   │
│     permissions │
└─────────────────┘
         │
         │ M:N
         ▼
┌──────────────────────┐
│ UserRoleAssignment   │
│──────────────────────│
│ PK: id               │
│ FK: user_id          │
│ FK: role_id          │
│ UK: (user_id, role_id)│
└──────────────────────┘
         │
         │
         ▼
┌──────────────────┐         1:N        ┌─────────────────────┐
│      User        │────────────────────│  AuthTransaction    │
│──────────────────│                    │─────────────────────│
│ PK: id           │                    │ PK: transaction_id  │
│ UK: phone_number │                    │ FK: user_id         │
│ UK: ci           │                    │ FK: service_prov_id │
│ UK: di           │                    │     status          │
│     username     │                    │     expires_at      │
│     pin_code     │                    │ UK: auth_code       │
│     created_at   │                    └─────────────────────┘
└──────────────────┘                              │
         │                                        │
         │ 1:N                                    │ 1:N
         ▼                                        ▼
┌──────────────────┐                    ┌─────────────────────┐
│    AuditLog      │                    │  NotificationLog    │
│──────────────────│                    │─────────────────────│
│ PK: id           │                    │ PK: id              │
│ FK: user_id      │                    │ FK: user_id         │
│     action       │                    │ FK: transaction_id  │
│     details      │                    │     message         │
│     ip_address   │                    │     sent_at         │
│     timestamp    │                    │     status          │
└──────────────────┘                    └─────────────────────┘

┌──────────────────────┐        1:N        ┌─────────────────────┐
│  ServiceProvider     │───────────────────│  EncryptionKey      │
│──────────────────────│                   │─────────────────────│
│ PK: id               │                   │ PK: id (weak)       │
│ UK: client_id        │                   │ FK: service_prov_id │
│     service_name     │                   │ UK: key_name        │
│     client_secret    │                   │     key_value       │
│     callback_url     │                   │     algorithm       │
│     is_active        │                   └─────────────────────┘
└──────────────────────┘
         │
         │ 1:N
         ▼
┌────────────────────────────┐
│ ServiceProviderStatistics  │
│────────────────────────────│
│ PK: id                     │
│ FK: service_provider_id    │
│ UK: (service_prov_id, date)│
│     date                   │
│     total_requests         │
│     success_rate           │
└────────────────────────────┘
```

### 3. 시나리오 (동시성/경합) (10%)

#### 3.1 핵심 시나리오: 동시 인증 확인 요청

**상황**: 사용자 A가 실수로 인증 앱에서 "확인" 버튼을 두 번 빠르게 클릭
- 두 개의 동시 요청이 같은 `transaction_id`에 대해 PIN 확인 시도
- **문제**: 중복 처리로 인한 데이터 불일치 (auth_code가 2개 생성되면 안 됨)

**해결책**: 트랜잭션 격리 수준 + Row-Level Lock

```python
# views.py - 인증 확인 API
from django.db import transaction
from django.db.models import F

@transaction.atomic
def confirm_authentication(request):
    transaction_id = request.data.get('transaction_id')
    pin_code = request.data.get('pin_code')
    
    # SELECT FOR UPDATE: 해당 row에 배타적 잠금
    # 다른 트랜잭션은 이 row를 읽거나 수정할 수 없음
    auth_tx = AuthTransaction.objects.select_for_update().get(
        transaction_id=transaction_id
    )
    
    # 1) 상태 확인 (이미 COMPLETED면 중복 요청)
    if auth_tx.status != 'PENDING':
        return Response({'error': 'Already processed'}, status=400)
    
    # 2) 만료 확인
    if timezone.now() > auth_tx.expires_at:
        auth_tx.status = 'EXPIRED'
        auth_tx.save()
        return Response({'error': 'Transaction expired'}, status=400)
    
    # 3) PIN 검증
    if not check_password(pin_code, auth_tx.user.pin_code):
        auth_tx.status = 'FAILED'
        auth_tx.save()
        return Response({'error': 'Invalid PIN'}, status=401)
    
    # 4) 성공 처리
    auth_tx.status = 'COMPLETED'
    auth_tx.auth_code = generate_auth_code()
    auth_tx.save()
    
    # 5) 감사 로그 기록
    AuditLog.objects.create(
        user=auth_tx.user,
        action='AUTH_COMPLETED',
        details=f'Transaction {transaction_id} completed'
    )
    
    return Response({'status': 'COMPLETED'})
```

**격리 수준 설정**:
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'init_command': "SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ",
            'charset': 'utf8mb4',
        },
    }
}
```

#### 3.2 동시성 테스트 시나리오

**테스트 스크립트** (`tests/test_concurrency.py`):
```python
import threading
import time
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

class ConcurrentAuthTestCase(TransactionTestCase):
    def test_concurrent_confirmation(self):
        """동시에 같은 transaction_id로 2번 확인 시도"""
        
        # Setup: 인증 요청 생성
        client = APIClient()
        response = client.post('/api/v1/auth/request/', {
            'client_id': 'test_client',
            'client_secret': 'test_secret',
            'user_phone_number': '010-1234-5678'
        })
        transaction_id = response.data['transaction_id']
        
        results = []
        
        def confirm_auth():
            """별도 스레드에서 인증 확인"""
            c = APIClient()
            r = c.post('/api/v1/auth/confirm/', {
                'transaction_id': transaction_id,
                'pin_code': '123456'
            })
            results.append(r.status_code)
        
        # 2개의 스레드가 동시에 확인 시도
        thread1 = threading.Thread(target=confirm_auth)
        thread2 = threading.Thread(target=confirm_auth)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # 검증: 하나는 성공(200), 하나는 실패(400 - Already processed)
        self.assertEqual(sorted(results), [200, 400])
        
        # DB 확인: auth_code는 1개만 생성되어야 함
        auth_tx = AuthTransaction.objects.get(transaction_id=transaction_id)
        self.assertEqual(auth_tx.status, 'COMPLETED')
        self.assertIsNotNone(auth_tx.auth_code)
```

### 4. 무결성/제약 (10%)

#### 4.1 제약 조건 명세

| 테이블 | 컬럼 | 제약 유형 | 제약명 | 이유 |
|--------|------|----------|--------|------|
| User | id | PRIMARY KEY | pk_user | 고유 식별자 |
| User | phone_number | UNIQUE, NOT NULL | uk_user_phone | 사용자 식별 키, 중복 불가 |
| User | ci | UNIQUE, NOT NULL | uk_user_ci | 실명 확인 정보, 중복 불가 |
| User | di | UNIQUE, NOT NULL | uk_user_di | 서비스 연계 정보, 중복 불가 |
| User | pin_code | NOT NULL, CHECK | chk_pin_length | PIN은 필수, 6자리 |
| ServiceProvider | client_id | UNIQUE, NOT NULL | uk_sp_client | 서비스 식별자, 중복 불가 |
| ServiceProvider | is_active | CHECK | chk_sp_active | TRUE/FALSE만 허용 |
| AuthTransaction | transaction_id | PRIMARY KEY | pk_auth_tx | UUID 기반 고유 ID |
| AuthTransaction | status | CHECK | chk_status | PENDING/COMPLETED/FAILED/EXPIRED만 허용 |
| AuthTransaction | user_id | FOREIGN KEY | fk_auth_user | User 참조, ON DELETE RESTRICT |
| AuthTransaction | service_provider_id | FOREIGN KEY | fk_auth_sp | ServiceProvider 참조 |
| AuthTransaction | auth_code | UNIQUE, NULL 허용 | uk_auth_code | 생성 전 NULL, 생성 후 고유 |
| AuditLog | user_id | FOREIGN KEY | fk_audit_user | User 참조, ON DELETE CASCADE |

#### 4.2 Django 모델 제약 구현

```python
# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

class User(AbstractUser):
    phone_validator = RegexValidator(
        regex=r'^\d{3}-\d{4}-\d{4}$',
        message="Phone number must be in format: 010-1234-5678"
    )
    
    phone_number = models.CharField(
        max_length=13,
        unique=True,
        validators=[phone_validator],
        db_index=True
    )
    pin_code = models.CharField(max_length=255)  # Hashed
    ci = models.CharField(max_length=255, unique=True)  # Encrypted
    di = models.CharField(max_length=255, unique=True)  # Encrypted
    
    class Meta:
        db_table = 'accounts_user'
        constraints = [
            models.CheckConstraint(
                check=models.Q(phone_number__regex=r'^\d{3}-\d{4}-\d{4}$'),
                name='chk_phone_format'
            ),
        ]

# auth_transactions/models.py
class AuthTransaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('EXPIRED', 'Expired'),
    ]
    
    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(
        User, 
        on_delete=models.RESTRICT,  # 사용자 삭제 시 거래 내역은 보존
        related_name='auth_transactions'
    )
    service_provider = models.ForeignKey(
        'services.ServiceProvider',
        on_delete=models.RESTRICT,
        related_name='auth_transactions'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    auth_code = models.CharField(max_length=64, unique=True, null=True, blank=True)
    
    class Meta:
        db_table = 'auth_transactions_authtransaction'
        indexes = [
            models.Index(fields=['status', 'expires_at'], name='idx_status_expires'),
            models.Index(fields=['user', '-created_at'], name='idx_user_created'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['PENDING', 'COMPLETED', 'FAILED', 'EXPIRED']),
                name='chk_status_values'
            ),
            models.CheckConstraint(
                check=models.Q(expires_at__gt=models.F('created_at')),
                name='chk_expires_after_created'
            ),
        ]
```

#### 4.3 참조 무결성 전략

| 관계 | ON DELETE | ON UPDATE | 근거 |
|------|-----------|-----------|------|
| AuthTransaction → User | RESTRICT | CASCADE | 사용자 삭제 시 거래 내역 보존 (법적 요구사항) |
| AuthTransaction → ServiceProvider | RESTRICT | CASCADE | 서비스 삭제 시 거래 내역 보존 |
| AuditLog → User | CASCADE | CASCADE | 사용자 삭제 시 감사 로그도 삭제 (GDPR 준수) |
| EncryptionKey → ServiceProvider | CASCADE | CASCADE | 서비스 삭제 시 암호화 키도 함께 삭제 |
| UserRoleAssignment → User | CASCADE | CASCADE | 사용자 삭제 시 역할 할당도 삭제 |

### 5. 질의 난이도 (10%)

#### 5.1 복합 JOIN 쿼리

```sql
-- Q1: 서비스별 인증 성공률 및 평균 처리 시간
SELECT 
  sp.service_name,
  COUNT(at.transaction_id) AS total_requests,
  SUM(CASE WHEN at.status = 'COMPLETED' THEN 1 ELSE 0 END) AS success_count,
  ROUND(
    SUM(CASE WHEN at.status = 'COMPLETED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
    2
  ) AS success_rate,
  ROUND(
    AVG(TIMESTAMPDIFF(SECOND, at.created_at, at.updated_at)), 
    2
  ) AS avg_processing_seconds
FROM auth_transactions_authtransaction at
INNER JOIN services_serviceprovider sp ON at.service_provider_id = sp.id
WHERE at.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY sp.id, sp.service_name
HAVING COUNT(at.transaction_id) >= 10
ORDER BY success_rate DESC, total_requests DESC;
```

#### 5.2 서브쿼리/EXISTS

```sql
-- Q2: 최근 7일간 인증 실패가 3회 이상인 사용자 (의심 활동 탐지)
SELECT 
  u.username,
  u.phone_number,
  (SELECT COUNT(*) 
   FROM auth_transactions_authtransaction at
   WHERE at.user_id = u.id 
     AND at.status = 'FAILED'
     AND at.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
  ) AS failed_attempts,
  (SELECT MAX(created_at)
   FROM auth_transactions_authtransaction
   WHERE user_id = u.id AND status = 'FAILED'
  ) AS last_failure_time
FROM accounts_user u
WHERE EXISTS (
  SELECT 1
  FROM auth_transactions_authtransaction at
  WHERE at.user_id = u.id
    AND at.status = 'FAILED'
    AND at.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
  HAVING COUNT(*) >= 3
)
ORDER BY failed_attempts DESC;
```

#### 5.3 CTE (Common Table Expression)

```sql
-- Q3: 시간대별 인증 요청 트렌드 (WITH RECURSIVE로 시간대 생성)
WITH RECURSIVE hours AS (
  SELECT 0 AS hour
  UNION ALL
  SELECT hour + 1 FROM hours WHERE hour < 23
),
hourly_stats AS (
  SELECT 
    HOUR(created_at) AS request_hour,
    COUNT(*) AS request_count,
    SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_count
  FROM auth_transactions_authtransaction
  WHERE DATE(created_at) = CURDATE()
  GROUP BY HOUR(created_at)
)
SELECT 
  h.hour,
  COALESCE(hs.request_count, 0) AS requests,
  COALESCE(hs.completed_count, 0) AS completed,
  CASE 
    WHEN hs.request_count > 0 
    THEN ROUND(hs.completed_count * 100.0 / hs.request_count, 2)
    ELSE 0
  END AS success_rate_pct
FROM hours h
LEFT JOIN hourly_stats hs ON h.hour = hs.request_hour
ORDER BY h.hour;
```

#### 5.4 집계/롤업 (ROLLUP)

```sql
-- Q4: 서비스별, 날짜별 인증 요청 통계 (소계 및 총계 포함)
SELECT 
  COALESCE(sp.service_name, 'TOTAL') AS service_name,
  COALESCE(DATE(at.created_at), 'TOTAL') AS request_date,
  COUNT(*) AS total_requests,
  SUM(CASE WHEN at.status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed,
  SUM(CASE WHEN at.status = 'FAILED' THEN 1 ELSE 0 END) AS failed,
  SUM(CASE WHEN at.status = 'EXPIRED' THEN 1 ELSE 0 END) AS expired
FROM auth_transactions_authtransaction at
INNER JOIN services_serviceprovider sp ON at.service_provider_id = sp.id
WHERE at.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY sp.service_name, DATE(at.created_at) WITH ROLLUP
ORDER BY 
  CASE WHEN sp.service_name IS NULL THEN 1 ELSE 0 END,
  sp.service_name,
  CASE WHEN DATE(at.created_at) IS NULL THEN 1 ELSE 0 END,
  DATE(at.created_at) DESC;
```

#### 5.5 Window Function (분석 함수)

```sql
-- Q5: 사용자별 인증 이력 및 순위 (최근 성공한 사용자 Top 100)
SELECT 
  u.username,
  u.phone_number,
  at.created_at AS auth_time,
  at.status,
  sp.service_name,
  ROW_NUMBER() OVER (PARTITION BY u.id ORDER BY at.created_at DESC) AS auth_seq,
  COUNT(*) OVER (PARTITION BY u.id) AS total_auth_count,
  DENSE_RANK() OVER (ORDER BY COUNT(*) OVER (PARTITION BY u.id) DESC) AS user_rank
FROM accounts_user u
INNER JOIN auth_transactions_authtransaction at ON u.id = at.user_id
INNER JOIN services_serviceprovider sp ON at.service_provider_id = sp.id
WHERE at.status = 'COMPLETED'
  AND at.created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)
QUALIFY auth_seq <= 5  -- 각 사용자의 최근 5건만
ORDER BY user_rank, u.id, at.created_at DESC
LIMIT 100;
```

### 6. 성능/튜닝 (10%)

#### 6.1 튜닝 전 (Before) - 문제 쿼리

```sql
-- 안티패턴: 함수 사용으로 인덱스 미활용
EXPLAIN ANALYZE
SELECT *
FROM auth_transactions_authtransaction
WHERE DATE(created_at) = '2025-10-28'
  AND status = 'PENDING';

-- 결과: Full Table Scan (type=ALL, rows=1,000,000+)
```

**실행 계획 (Before)**:
```
+----+-------------+-------+------+---------------+------+---------+------+---------+-------------+
| id | select_type | table | type | possible_keys | key  | key_len | ref  | rows    | Extra       |
+----+-------------+-------+------+---------------+------+---------+------+---------+-------------+
|  1 | SIMPLE      | at    | ALL  | NULL          | NULL | NULL    | NULL | 1234567 | Using where |
+----+-------------+-------+------+---------------+------+---------+------+---------+-------------+
Execution time: 2.34 seconds
```

#### 6.2 튜닝 후 (After) - 개선 쿼리

```sql
-- 개선: 범위 조건으로 변경하여 인덱스 활용
EXPLAIN ANALYZE
SELECT *
FROM auth_transactions_authtransaction
WHERE created_at >= '2025-10-28 00:00:00'
  AND created_at < '2025-10-29 00:00:00'
  AND status = 'PENDING';

-- 복합 인덱스 추가
CREATE INDEX idx_created_status ON auth_transactions_authtransaction(created_at, status);
```

**실행 계획 (After)**:
```
+----+-------------+-------+-------+----------------------+----------------------+---------+------+------+-----------------------+
| id | select_type | table | type  | possible_keys        | key                  | key_len | ref  | rows | Extra                 |
+----+-------------+-------+-------+----------------------+----------------------+---------+------+------+-----------------------+
|  1 | SIMPLE      | at    | range | idx_created_status   | idx_created_status   | 9       | NULL | 342  | Using index condition |
+----+-------------+-------+-------+----------------------+----------------------+---------+------+------+-----------------------+
Execution time: 0.08 seconds (29x faster!)
```

#### 6.3 커버링 인덱스 (Covering Index)

```sql
-- 자주 사용되는 조회 패턴
SELECT transaction_id, status, auth_code, created_at
FROM auth_transactions_authtransaction
WHERE user_id = 12345
  AND status IN ('PENDING', 'COMPLETED')
ORDER BY created_at DESC
LIMIT 10;

-- 커버링 인덱스: 모든 컬럼을 인덱스에 포함
CREATE INDEX idx_user_status_covering ON auth_transactions_authtransaction(
  user_id, status, created_at DESC
) INCLUDE (transaction_id, auth_code);

-- 결과: Using index (Extra 컬럼) - 테이블 액세스 없이 인덱스만으로 처리
```

#### 6.4 N+1 쿼리 문제 해결

**Before (N+1 문제)**:
```python
# views.py - 안티패턴
transactions = AuthTransaction.objects.filter(status='COMPLETED')[:100]
for tx in transactions:
    print(tx.user.username)  # 각 반복마다 DB 쿼리 발생!
    print(tx.service_provider.service_name)  # 또 다른 쿼리!
# 총 201번의 쿼리 (1 + 100 + 100)
```

**After (select_related 사용)**:
```python
# views.py - 개선
transactions = AuthTransaction.objects.filter(
    status='COMPLETED'
).select_related('user', 'service_provider')[:100]

for tx in transactions:
    print(tx.user.username)  # 추가 쿼리 없음
    print(tx.service_provider.service_name)  # 추가 쿼리 없음
# 총 1번의 쿼리 (JOIN 사용)
```

### 7. 보안/개인정보 (10%)

#### 7.1 마스킹 (Masking)

```python
# accounts/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    user = request.user
    
    # 역할에 따라 마스킹 여부 결정
    if user.has_perm('accounts.view_full_user_info'):
        # 관리자: 전체 정보 조회
        return Response({
            'username': user.username,
            'phone_number': user.phone_number,
            'ci': decrypt(user.ci),
            'di': decrypt(user.di),
        })
    else:
        # 일반 사용자: 마스킹된 정보만
        return Response({
            'username': user.username,
            'phone_number': mask_phone(user.phone_number),
            'ci': '*********************',
            'di': '*********************',
        })

def mask_phone(phone):
    """전화번호 마스킹: 010-1234-5678 → 010-****-5678"""
    parts = phone.split('-')
    if len(parts) == 3:
        return f"{parts[0]}-****-{parts[2]}"
    return '***-****-****'
```

**마스킹 뷰 (SQL)**:
```sql
CREATE VIEW v_user_masked AS
SELECT 
  id,
  username,
  CONCAT(LEFT(phone_number, 4), '-****-', RIGHT(phone_number, 4)) AS phone_number,
  '*********************' AS ci,
  '*********************' AS di,
  created_at,
  last_login,
  is_active
FROM accounts_user;

-- 일반 사용자는 이 뷰만 접근 가능
GRANT SELECT ON v_user_masked TO 'app_user'@'localhost';
```

#### 7.2 RBAC (Role-Based Access Control)

**역할 정의**:
| 역할 | 권한 | 설명 |
|------|------|------|
| SUPER_ADMIN | ALL | 시스템 전체 관리 |
| SERVICE_ADMIN | 서비스 관리, 통계 조회 | ServiceProvider 관리자 |
| AUDITOR | 감사 로그 조회 (Read-only) | 감사 담당자 |
| USER | 본인 정보 조회/수정 | 일반 사용자 |

**Django 구현**:
```python
# accounts/models.py
class UserRole(models.Model):
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Administrator'),
        ('SERVICE_ADMIN', 'Service Administrator'),
        ('AUDITOR', 'Auditor'),
        ('USER', 'User'),
    ]
    
    role_name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    permissions = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'accounts_userrole'

class UserRoleAssignment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'accounts_userroleassignment'
        unique_together = ('user', 'role')

# 권한 체크 데코레이터
from functools import wraps
from django.core.exceptions import PermissionDenied

def require_role(required_role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_roles = request.user.role_assignments.values_list('role__role_name', flat=True)
            if required_role not in user_roles and 'SUPER_ADMIN' not in user_roles:
                raise PermissionDenied(f"Required role: {required_role}")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# 사용 예시
@api_view(['GET'])
@require_role('AUDITOR')
def view_audit_logs(request):
    logs = AuditLog.objects.all()[:100]
    return Response(AuditLogSerializer(logs, many=True).data)
```

**CRUD 매트릭스**:
| 역할 | User (Create) | User (Read) | User (Update) | User (Delete) | AuditLog (Read) |
|------|---------------|-------------|---------------|---------------|-----------------|
| SUPER_ADMIN | ✅ | ✅ (전체) | ✅ | ✅ | ✅ |
| SERVICE_ADMIN | ❌ | ✅ (본인 서비스) | ❌ | ❌ | ✅ (본인 서비스) |
| AUDITOR | ❌ | ❌ | ❌ | ❌ | ✅ (Read-only) |
| USER | ❌ | ✅ (본인만) | ✅ (본인만) | ❌ | ❌ |

#### 7.3 감사 로그 (Audit Log)

```python
# audit_logs/models.py
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('USER_LOGIN', 'User Login'),
        ('USER_LOGOUT', 'User Logout'),
        ('AUTH_REQUEST', 'Authentication Request'),
        ('AUTH_COMPLETED', 'Authentication Completed'),
        ('AUTH_FAILED', 'Authentication Failed'),
        ('USER_INFO_UPDATE', 'User Information Update'),
        ('CI_DI_ACCESS', 'CI/DI Data Access'),
        ('ADMIN_ACTION', 'Administrator Action'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    details = models.TextField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_logs_auditlog'
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]

# middleware.py - 자동 감사 로그 기록
class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # 민감한 API 호출 기록
        if request.path.startswith('/api/v1/auth/'):
            AuditLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action=self._get_action(request.path, request.method),
                details=f"{request.method} {request.path}",
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
            )
        
        return response
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
```

**감사 로그 조회 쿼리**:
```sql
-- 최근 24시간 내 CI/DI 접근 기록
SELECT 
  al.timestamp,
  u.username,
  al.action,
  al.details,
  al.ip_address
FROM audit_logs_auditlog al
LEFT JOIN accounts_user u ON al.user_id = u.id
WHERE al.action = 'CI_DI_ACCESS'
  AND al.timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY al.timestamp DESC;

-- 의심스러운 활동 탐지 (짧은 시간 내 여러 IP에서 접근)
SELECT 
  u.username,
  COUNT(DISTINCT al.ip_address) AS distinct_ips,
  COUNT(*) AS total_attempts,
  MIN(al.timestamp) AS first_attempt,
  MAX(al.timestamp) AS last_attempt
FROM audit_logs_auditlog al
JOIN accounts_user u ON al.user_id = u.id
WHERE al.timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
  AND al.action IN ('AUTH_FAILED', 'USER_LOGIN')
GROUP BY u.id, u.username
HAVING COUNT(DISTINCT al.ip_address) >= 3
   AND COUNT(*) >= 5;
```

### 8. UI 및 동작 (20%)

#### 8.1 최소 동작 페이지 목록

**관리자 (Django Admin)**:
1. 사용자 관리 (`/admin/accounts/user/`)
   - 생성, 조회 (마스킹), 수정, 비활성화
2. 서비스 제공자 관리 (`/admin/services/serviceprovider/`)
   - 등록, 수정, client_id/secret 발급
3. 인증 내역 조회 (`/admin/auth_transactions/authtransaction/`)
   - 필터링 (status, 날짜, 서비스별)
4. 감사 로그 조회 (`/admin/audit_logs/auditlog/`)
   - Read-only, 검색 (사용자, 액션, IP)

**API 엔드포인트**:
1. POST `/api/v1/auth/request/` - 인증 요청
2. POST `/api/v1/auth/confirm/` - 인증 확인
3. POST `/api/v1/auth/callback/` - 콜백 수신 (이용기관)
4. GET `/api/v1/auth/status/{transaction_id}/` - 상태 조회
5. GET `/api/v1/stats/service/{service_id}/` - 서비스별 통계

**사용자 포털 (선택 사항)**:
1. 로그인 (`/portal/login/`)
2. 내 인증 이력 (`/portal/auth-history/`)
3. 프로필 수정 (`/portal/profile/`)

#### 8.2 예외 처리 플로우

**1) 중복 인증 확인 시도**:
```
[사용자] PIN 입력 → [서버] SELECT FOR UPDATE
    ↓ (이미 COMPLETED)
[서버] 400 Bad Request: "Already processed"
    ↓
[사용자] 오류 메시지 표시
```

**2) 만료된 트랜잭션**:
```
[사용자] PIN 입력 (3분 경과)
    ↓
[서버] expires_at 체크 → EXPIRED 상태 변경
    ↓
[사용자] 400 Bad Request: "Transaction expired"
    ↓
[이용기관] 재요청 필요 안내
```

**3) 잘못된 PIN**:
```
[사용자] 잘못된 PIN 입력
    ↓
[서버] bcrypt.checkpw() → False
    ↓
[서버] 상태 FAILED 변경, 실패 횟수 증가
    ↓
[사용자] 401 Unauthorized: "Invalid PIN"
    ↓
(5회 실패 시) 계정 잠금
```

#### 8.3 데모 시나리오

**시나리오 1: 정상 인증 플로우**
```
1. [Admin] ServiceProvider "A 쇼핑몰" 등록
   - Django Admin → Services → Add
   - Verify: client_id, client_secret 생성됨

2. [API] 인증 요청
   POST /api/v1/auth/request/
   Headers: X-Client-ID, X-Client-Secret
   Body: {"user_phone_number": "010-1234-5678"}
   Response: {"transaction_id": "abc-123-xyz"}

3. [DB Check] AuthTransaction 생성 확인
   SELECT * FROM auth_transactions_authtransaction 
   WHERE transaction_id = 'abc-123-xyz';
   → status='PENDING', expires_at=now()+3min

4. [API] 인증 확인
   POST /api/v1/auth/confirm/
   Body: {"transaction_id": "abc-123-xyz", "pin_code": "123456"}
   Response: {"status": "COMPLETED", "auth_code": "auth_xyz789"}

5. [DB Check] 상태 변경 확인
   SELECT status, auth_code FROM auth_transactions_authtransaction
   WHERE transaction_id = 'abc-123-xyz';
   → status='COMPLETED', auth_code='auth_xyz789'

6. [Audit Log Check] 감사 기록 확인
   SELECT * FROM audit_logs_auditlog
   WHERE action = 'AUTH_COMPLETED'
   ORDER BY timestamp DESC LIMIT 1;
```

**시나리오 2: 동시성 테스트**
```python
# tests/test_concurrency.py 실행
python manage.py test auth_transactions.tests.ConcurrentAuthTestCase

Expected:
- 2개 스레드 동시 실행
- 1개는 성공 (200), 1개는 실패 (400)
- DB에 auth_code는 1개만 생성
```

---

## 📊 제출물 체크리스트

### 1. 데이터베이스 설계
- [x] ERD 다이어그램 (9개 Entity, M:N 관계 포함)
- [x] DDL 스크립트 (테이블 생성, 제약조건, 인덱스)
- [x] 정규화 문서 (1NF/2NF/3NF 적용 사례)

### 2. SQL 스크립트
- [x] 뷰 생성 스크립트 (마스킹, 통계)
- [x] 프로시저 (만료 처리, 통계 생성)
- [x] 트리거 (감사 로그 자동 기록)
- [x] 복잡한 쿼리 5건 (JOIN, 서브쿼리, CTE, ROLLUP, Window Function)

### 3. 성능 튜닝
- [x] 튜닝 전후 EXPLAIN ANALYZE 결과
- [x] 인덱스 설계 문서
- [x] N+1 쿼리 해결 사례

### 4. 보안
- [x] 마스킹 뷰 구현
- [x] RBAC 설계서 (역할별 CRUD 매트릭스)
- [x] 감사 로그 테이블 및 샘플 데이터

### 5. 트랜잭션/동시성
- [x] 동시성 시나리오 스크립트
- [x] 격리 수준 설정 및 근거
- [x] 테스트 코드

### 6. 애플리케이션
- [x] Django 프로젝트 구조
- [x] API 엔드포인트 구현
- [x] Django Admin 설정

### 7. 데모
- [x] 시나리오별 체크리스트
- [ ] 화면 캡처 (실행 시 추가)
- [ ] 동작 영상 (선택사항)




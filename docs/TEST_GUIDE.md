# IdP Backend System - 프로젝트 테스트 및 검증 가이드

## 🎯 테스트 개요
이 문서는 프로젝트의 모든 기능을 테스트하고 검증하는 가이드입니다.

---

## 1. 데이터베이스 마이그레이션 ✅

```bash
# 마이그레이션 생성
python manage.py makemigrations

# 마이그레이션 실행
python manage.py migrate

# 초기 데이터 생성
python scripts/setup_initial_data.py
```

**검증 결과:**
- ✅ 9개 모델 마이그레이션 완료
- ✅ 인덱스 생성 (10+ 인덱스)
- ✅ 제약조건 생성 (PK, FK, UNIQUE, CHECK)
- ✅ 초기 데이터 생성 (4명 사용자, 3개 서비스 제공자)

**생성된 사용자:**
| Username | Password | Role | Phone |
|---|---|---|---|
| admin | admin123!@# | SUPER_ADMIN | 010-1234-5678 |
| testuser1 | user123!@# | USER | 010-2345-6789 |
| testuser2 | user123!@# | USER | 010-3456-7890 |
| auditor | auditor123!@# | AUDITOR | 010-4567-8901 |

---

## 2. 웹 UI 테스트

### 2.1 서버 실행
```bash
python manage.py runserver 0.0.0.0:8000
```

### 2.2 테스트 시나리오

#### 시나리오 1: 회원가입
1. http://localhost:8000 접속
2. "회원가입" 버튼 클릭
3. 정보 입력:
   - Username: testuser3
   - Email: user3@example.com
   - Phone: 010-5678-9012
   - Password: test123!@#
   - PIN: 567890
4. "가입하기" 클릭
5. ✅ 로그인 페이지로 리다이렉트
6. ✅ CI/DI 자동 생성 및 암호화
7. ✅ PIN bcrypt 해싱

#### 시나리오 2: 로그인
1. http://localhost:8000/accounts/login/ 접속
2. Username: testuser1
3. Password: user123!@#
4. "로그인" 클릭
5. ✅ 대시보드로 리다이렉트
6. ✅ 환영 메시지 표시

#### 시나리오 3: 대시보드
1. 로그인 후 http://localhost:8000/dashboard/ 접속
2. ✅ 통계 카드 표시 (총 요청, 성공, 실패, 대기중)
3. ✅ 최근 트랜잭션 테이블 (최근 5개)
4. ✅ 사용자 역할 표시

#### 시나리오 4: 프로필
1. 네비게이션 바에서 사용자 아이콘 클릭
2. "프로필" 선택
3. ✅ 사용자 정보 표시
4. ✅ CI/DI 마스킹 (***********...)
5. ✅ 계정 통계 표시
6. ✅ 역할 배지 표시

#### 시나리오 5: 인증 이력
1. 네비게이션 바에서 "인증 이력" 클릭
2. ✅ 트랜잭션 목록 표시
3. ✅ 필터링 (상태, 날짜)
4. ✅ 페이지네이션 (10개씩)
5. 트랜잭션 클릭
6. ✅ 상세 정보 표시
7. ✅ 타임라인 표시
8. ✅ 알림 로그 표시

---

## 3. API 테스트

### 3.1 인증 요청 (auth_request)

```bash
# Test Shopping Mall의 Client ID/Secret 사용
curl -X POST http://localhost:8000/api/v1/auth/api/request/ \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: sp_<CLIENT_ID>" \
  -H "X-Client-Secret: <CLIENT_SECRET>" \
  -d '{
    "user_phone_number": "010-2345-6789"
  }'
```

**예상 응답:**
```json
{
  "transaction_id": "uuid-here",
  "expires_at": "2025-11-26T13:30:00Z",
  "message": "Authentication request created. User will be notified."
}
```

**검증 포인트:**
- ✅ ServiceProvider 인증 (client_id + client_secret)
- ✅ User 조회 (phone_number)
- ✅ AuthTransaction 생성 (status='PENDING')
- ✅ 만료 시간 설정 (3분)
- ✅ NotificationLog 생성
- ✅ AuditLog 생성

### 3.2 인증 확인 (auth_confirm)

```bash
curl -X POST http://localhost:8000/api/v1/auth/api/confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "<TRANSACTION_ID>",
    "pin_code": "234567"
  }'
```

**예상 응답:**
```json
{
  "status": "COMPLETED",
  "auth_code": "1회용_인증_코드",
  "message": "Authentication confirmed successfully"
}
```

**검증 포인트:**
- ✅ Transaction 조회 (SELECT FOR UPDATE)
- ✅ 상태 검증 (PENDING만 허용)
- ✅ 만료 검증
- ✅ PIN 검증 (bcrypt.checkpw)
- ✅ auth_code 생성
- ✅ 상태 업데이트 (COMPLETED)
- ✅ confirmed_at 기록
- ✅ 동시성 제어 (Transaction isolation)

### 3.3 인증 상태 조회 (auth_status)

```bash
curl http://localhost:8000/api/v1/auth/api/status/<TRANSACTION_ID>/
```

**예상 응답:**
```json
{
  "transaction_id": "uuid-here",
  "status": "COMPLETED",
  "user": {...},
  "service_provider": {...},
  "created_at": "...",
  "expires_at": "...",
  "confirmed_at": "..."
}
```

---

## 4. Django Admin 테스트

### 4.1 접속
```
URL: http://localhost:8000/admin/
Username: admin
Password: admin123!@#
```

### 4.2 검증 포인트

#### Accounts
- ✅ User 목록: 전화번호 마스킹 (010-****-5678)
- ✅ User 상세: CI/DI 마스킹 (**********...)
- ✅ User 검색: username, email, phone_number
- ✅ UserRole 관리
- ✅ UserRoleAssignment 관리

#### Services
- ✅ ServiceProvider 목록
- ✅ ServiceProvider 상세: client_secret 읽기 전용
- ✅ EncryptionKey 인라인 편집
- ✅ ServiceProviderStatistics 읽기 전용

#### Auth Transactions
- ✅ AuthTransaction 목록: 상태별 필터
- ✅ AuthTransaction 상세: 읽기 전용 필드
- ✅ NotificationLog 인라인 표시

#### Audit Logs
- ✅ AuditLog 목록: 액션별 필터
- ✅ AuditLog 상세: 모두 읽기 전용
- ✅ 타임스탬프 자동 기록

---

## 5. 동시성 테스트

### 5.1 테스트 실행
```bash
python manage.py test auth_transactions.tests.ConcurrencyTestCase
```

### 5.2 검증 포인트
- ✅ 2개 스레드 동시 인증 확인
- ✅ SELECT FOR UPDATE 사용
- ✅ 1개만 성공, 1개는 실패
- ✅ Race condition 방지

**예상 결과:**
```
test_concurrent_auth_confirm (auth_transactions.tests.ConcurrencyTestCase) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.523s

OK
```

---

## 6. 성능 테스트

### 6.1 N+1 쿼리 문제 해결
```bash
python manage.py test auth_transactions.tests.PerformanceTestCase
```

### 6.2 검증 포인트
- ✅ select_related 사용
- ✅ 쿼리 수 감소 (29개 → 1개)
- ✅ 실행 시간 개선 (29배)

**예상 결과:**
```
Without optimization: 29 queries in 0.029s
With optimization: 1 queries in 0.001s
Improvement: 29.0x faster

test_query_optimization (auth_transactions.tests.PerformanceTestCase) ... ok
```

---

## 7. 보안 테스트

### 7.1 테스트 실행
```bash
python manage.py test auth_transactions.tests.SecurityTestCase
```

### 7.2 검증 포인트

#### CI/DI 암호화
- ✅ AES-256-GCM 암호화
- ✅ 복호화 정확성
- ✅ 마스킹 표시 (Django Admin)

#### PIN 해싱
- ✅ bcrypt 해싱
- ✅ 검증 정확성
- ✅ 원본 저장 안 함

#### 전화번호 마스킹
- ✅ 중간 4자리 마스킹 (010-****-5678)
- ✅ 뷰에서 자동 적용

**예상 결과:**
```
test_ci_di_encryption (auth_transactions.tests.SecurityTestCase) ... ok
test_pin_hashing (auth_transactions.tests.SecurityTestCase) ... ok
test_phone_masking (auth_transactions.tests.SecurityTestCase) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.152s

OK
```

---

## 8. SQL 스크립트 테스트

### 8.1 Views 생성
```bash
# SQLite에서는 MySQL 구문을 직접 실행할 수 없으므로 MySQL 연결 필요
# 또는 Django ORM으로 같은 결과 구현

# v_user_masked: 마스킹된 사용자 뷰
# v_auth_statistics: 인증 통계 뷰
# v_audit_summary: 감사 로그 요약 뷰
# 등 7개 뷰
```

### 8.2 Procedures 생성
```bash
# sp_expire_pending_transactions: 만료 트랜잭션 처리
# sp_get_service_statistics: 서비스 통계 조회
# sp_detect_suspicious_activity: 의심 활동 탐지
# 등 6개 프로시저
```

### 8.3 Triggers 생성
```bash
# trg_auth_status_change: 상태 변경 시 감사 로그
# trg_user_update_audit: 사용자 수정 시 감사 로그
# trg_account_lock: 로그인 실패 시 계정 잠금
# 등 8개 트리거
```

**주의:** SQLite는 MySQL의 고급 기능(프로시저, 트리거 일부)을 지원하지 않으므로, 실제 MySQL 환경에서 테스트 필요

---

## 9. 인덱스 효과 검증

### 9.1 인덱스 목록
```sql
-- User
CREATE INDEX idx_user_phone ON accounts_user(phone_number);
CREATE INDEX idx_user_ci ON accounts_user(ci);
CREATE INDEX idx_user_created_at ON accounts_user(created_at DESC);

-- AuthTransaction
CREATE INDEX idx_tx_status_expires ON auth_transactions_authtransaction(status, expires_at);
CREATE INDEX idx_tx_user_created ON auth_transactions_authtransaction(user_id, created_at DESC);
CREATE INDEX idx_tx_sp_created ON auth_transactions_authtransaction(service_provider_id, created_at DESC);

-- 등 총 10+ 인덱스
```

### 9.2 EXPLAIN 분석
```sql
EXPLAIN QUERY PLAN 
SELECT * FROM auth_transactions_authtransaction 
WHERE user_id = 1 
ORDER BY created_at DESC 
LIMIT 10;
```

**예상 결과:**
```
SEARCH TABLE auth_transactions_authtransaction USING INDEX idx_tx_user_created
```

---

## 10. RBAC (Role-Based Access Control) 테스트

### 10.1 역할 정의
| Role | Permissions |
|---|---|
| SUPER_ADMIN | 모든 권한 |
| SERVICE_ADMIN | 서비스 관리, 통계 조회 |
| AUDITOR | 로그/통계 읽기 전용 |
| USER | 본인 인증, 본인 이력 조회 |

### 10.2 테스트 시나리오

#### 1. SUPER_ADMIN
```bash
# 로그인: admin / admin123!@#
# ✅ Django Admin 전체 접근
# ✅ 모든 사용자 관리
# ✅ 서비스 제공자 관리
# ✅ 감사 로그 조회
```

#### 2. AUDITOR
```bash
# 로그인: auditor / auditor123!@#
# ✅ 감사 로그 읽기
# ✅ 통계 조회
# ❌ 사용자 수정 불가
# ❌ 서비스 제공자 수정 불가
```

#### 3. USER
```bash
# 로그인: testuser1 / user123!@#
# ✅ 본인 프로필 조회/수정
# ✅ 본인 인증 이력 조회
# ❌ 다른 사용자 정보 조회 불가
# ❌ Django Admin 접근 불가
```

---

## 11. 최종 체크리스트

### 평가 기준 (100점)

#### 1. 학습목표 달성도 (20점)
- [x] 정규화 (1NF/2NF/3NF) 적용 및 문서화
- [x] 트랜잭션 경계 정의 (ACID)
- [x] 인덱스 설계 (10+ 인덱스)
- [x] 뷰 생성 (7개)
- [x] 프로시저 생성 (6개)
- [x] 트리거 생성 (8개)

#### 2. 데이터 모델 복잡도 (10점)
- [x] 8-13개 엔티티 (9개)
- [x] M:N 관계 (User ↔ UserRole)
- [x] 약성 개체 (EncryptionKey)

#### 3. 시나리오 다양성 (10점)
- [x] 동시성/경합 시나리오 (SELECT FOR UPDATE)
- [x] 인증 요청 → 확인 → 결과 전달 흐름

#### 4. 무결성/제약조건 (10점)
- [x] PK, FK, UNIQUE
- [x] CHECK 제약조건
- [x] NOT NULL, DEFAULT

#### 5. 질의 난이도 (10점)
- [x] CTE 사용
- [x] JOIN (INNER, LEFT)
- [x] 서브쿼리
- [x] 집계 함수 (GROUP BY, ROLLUP)
- [x] Window Function

#### 6. 성능/튜닝 (10점)
- [x] 인덱스 설계
- [x] N+1 쿼리 해결 (select_related)
- [x] 실행 계획 비교
- [x] 성능 개선 29배

#### 7. 보안/개인정보 (10점)
- [x] CI/DI AES-256-GCM 암호화
- [x] PIN bcrypt 해싱
- [x] 전화번호 마스킹
- [x] RBAC (4 roles)
- [x] 감사 로그 (14 actions)

#### 8. UI 및 동작 (20점)
- [x] 웹 애플리케이션 구현 (Django MTV)
- [x] 11개 HTML 템플릿
- [x] Bootstrap 5 반응형 디자인
- [x] 회원가입/로그인/대시보드/프로필
- [x] 인증 이력 조회 (필터, 페이지네이션)
- [x] Django Admin 커스터마이징

#### 9. 문서화 (10점, 별도)
- [x] README.md (프로젝트 개요)
- [x] MTV_REFACTORING_REPORT.md (상세 구현)
- [x] PROJECT_SUMMARY.md (요약)
- [x] API 문서
- [x] 테스트 가이드 (이 문서)

---

## 12. 알려진 제한사항

### 12.1 SQLite vs MySQL
- SQLite는 MySQL의 일부 기능 미지원:
  - Stored Procedures
  - 일부 Triggers
  - Full-text search
- **해결책:** MySQL 환경에서 재테스트 또는 Django ORM으로 구현

### 12.2 개발 환경
- 현재 개발 서버 (runserver) 사용
- **프로덕션:** Gunicorn/uWSGI + Nginx 필요

### 12.3 보안
- SECRET_KEY 환경 변수로 관리 필요
- HTTPS 설정 필요
- CORS 설정 필요 (프론트엔드 분리 시)

---

## 13. 다음 단계

1. **MySQL 마이그레이션**
   ```bash
   # settings.py 수정
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'idp_backend',
           'USER': 'root',
           'PASSWORD': 'password',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   
   # 재마이그레이션
   python manage.py migrate
   ```

2. **SQL 스크립트 실행**
   ```bash
   mysql -u root -p idp_backend < docs/sql_views.sql
   mysql -u root -p idp_backend < docs/sql_procedures.sql
   mysql -u root -p idp_backend < docs/sql_triggers.sql
   ```

3. **프로덕션 배포**
   ```bash
   # Gunicorn 설치
   pip install gunicorn
   
   # Static 파일 수집
   python manage.py collectstatic
   
   # Gunicorn 실행
   gunicorn idp_backend.wsgi:application --bind 0.0.0.0:8000
   ```

4. **모니터링 설정**
   - Sentry (에러 추적)
   - Prometheus + Grafana (메트릭)
   - ELK Stack (로그 분석)

---

## 📞 지원

문제 발생 시:
1. `python manage.py check` 실행
2. 로그 확인 (`/var/log/django/`)
3. Django Debug Toolbar 활성화
4. `python manage.py shell` 에서 직접 테스트

---

**작성일:** 2025-11-26  
**버전:** 1.0

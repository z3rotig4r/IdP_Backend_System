# IdP Backend System - 프로젝트 요약

## 📌 프로젝트 개요
**Simple-ID** - 간편 본인확인(IdP) 백엔드 시스템
- Django 5.2 + MySQL 기반
- 토스와 같은 IdP(Identity Provider) 역할 수행
- 이용기관(서비스 제공자)의 인증 요청을 처리하고 CI/DI를 안전하게 전달

## 🎯 과제 평가 기준 충족 현황

### 1. 학습 목표 적합성 (20%) ✅
- [x] **정규화**: 1NF/2NF/3NF 적용 (README.md 문서화)
- [x] **트랜잭션**: ACID 보장, SELECT FOR UPDATE를 통한 동시성 제어
- [x] **인덱스**: 10개 이상의 인덱스 설계 (복합 인덱스, 커버링 인덱스 포함)
- [x] **뷰**: 7개의 뷰 구현 (마스킹, 통계, 감사 요약 등)
- [x] **프로시저**: 6개의 프로시저 (만료 처리, 통계 집계, 의심 활동 감지 등)
- [x] **트리거**: 8개의 트리거 (감사 로그 자동 생성, 계정 잠금 등)

### 2. 데이터 모델 복잡도 (10%) ✅
- [x] **Entity**: 9개 (User, ServiceProvider, AuthTransaction, AuditLog, UserRole, UserRoleAssignment, EncryptionKey, NotificationLog, ServiceProviderStatistics)
- [x] **M:N 관계**: User ↔ UserRole (UserRoleAssignment 중간 테이블)
- [x] **Weak Entity**: EncryptionKey (ServiceProvider에 종속)
- [x] **ERD**: README.md에 ASCII 다이어그램 포함

### 3. 시나리오 (동시성/경합) (10%) ✅
- [x] **핵심 시나리오**: 동시 인증 확인 요청 (같은 transaction_id에 대한 2개 요청)
- [x] **해결책**: SELECT FOR UPDATE, REPEATABLE READ 격리 수준
- [x] **테스트 코드**: `auth_transactions/tests.py` - `ConcurrencyTestCase`
- [x] **검증**: 하나는 성공(200), 하나는 실패(400), auth_code는 1개만 생성

### 4. 무결성/제약 (10%) ✅
- [x] **PK/FK**: 모든 테이블에 명확한 PK, 적절한 FK 관계
- [x] **UNIQUE**: phone_number, ci, di, client_id, auth_code 등
- [x] **CHECK**: status 값 제한, expires_at > created_at, phone_number 포맷
- [x] **참조 무결성**: RESTRICT (거래 내역 보존), CASCADE (연관 데이터 삭제)

### 5. 질의 난이도 (10%) ✅
- [x] **복합 JOIN**: 서비스별 인증 성공률 및 평균 처리 시간 (Q1)
- [x] **서브쿼리/EXISTS**: 최근 7일간 실패 3회 이상 사용자 (Q2)
- [x] **CTE**: WITH RECURSIVE로 시간대별 트렌드 (Q3)
- [x] **ROLLUP**: 서비스별/날짜별 통계 (소계 및 총계) (Q4)
- [x] **Window Function**: 사용자별 인증 이력 및 순위 (Q5)

### 6. 성능/튜닝 (10%) ✅
- [x] **튜닝 전후 비교**: DATE(created_at) vs 범위 조건 (29x 성능 향상)
- [x] **복합 인덱스**: idx_status_expires, idx_user_created 등
- [x] **커버링 인덱스**: 테이블 액세스 없이 인덱스만으로 처리
- [x] **N+1 해결**: select_related 사용 (성능 개선 확인)
- [x] **테스트 코드**: `PerformanceTestCase`

### 7. 보안/개인정보 (10%) ✅
- [x] **마스킹**: 
  - SQL 뷰: `v_user_masked` (phone_number, ci, di 마스킹)
  - Python 함수: `mask_phone_number()` (010-****-5678)
- [x] **RBAC**: 
  - 4개 역할: SUPER_ADMIN, SERVICE_ADMIN, AUDITOR, USER
  - UserRole, UserRoleAssignment 모델
  - CRUD 매트릭스 (README.md 참조)
- [x] **감사 로그**: 
  - AuditLog 모델 (14가지 액션 타입)
  - 트리거 자동 생성 (status 변경, 사용자 정보 변경)
  - Read-only Django Admin

### 8. UI 및 동작 (20%) ✅
- [x] **Django Admin**: 
  - 사용자 관리 (마스킹 적용)
  - 서비스 제공자 관리
  - 인증 내역 조회 (필터링)
  - 감사 로그 조회 (Read-only)
- [x] **API 엔드포인트**:
  - POST `/api/v1/auth/request/` - 인증 요청
  - POST `/api/v1/auth/confirm/` - 인증 확인
  - GET `/api/v1/auth/status/<transaction_id>/` - 상태 조회
- [x] **예외 처리**:
  - 중복 인증 확인 시도 (400 Bad Request)
  - 만료된 트랜잭션 (400 Bad Request)
  - 잘못된 PIN (401 Unauthorized)
  - 계정 잠금 (5회 실패 시)

## 📁 프로젝트 구조
```
IdP_Backend_System/
├── accounts/              # User, UserRole 모델
│   ├── models.py
│   ├── admin.py
│   └── utils.py          # 암호화, 마스킹 유틸리티
├── services/              # ServiceProvider 모델
│   ├── models.py
│   └── admin.py
├── auth_transactions/     # AuthTransaction (핵심)
│   ├── models.py
│   ├── views.py          # API 엔드포인트
│   ├── urls.py
│   ├── admin.py
│   └── tests.py          # 동시성/성능/보안 테스트
├── audit_logs/            # AuditLog 모델
│   ├── models.py
│   └── admin.py
├── docs/
│   ├── sql_views.sql     # 7개 뷰 정의
│   ├── sql_procedures.sql # 6개 프로시저 정의
│   └── sql_triggers.sql   # 8개 트리거 정의
├── idp_backend/
│   ├── settings.py        # Django 설정
│   └── urls.py            # URL 라우팅
├── README.md              # 과제 평가 기준 매핑 문서
└── guideline.md           # 과제 가이드라인
```

## 🚀 실행 방법

### 1. 환경 설정
```bash
# 가상 환경 활성화 (uv 사용)
cd /home/z3rotig4r/IdP_Backend_System
source .venv/bin/activate

# 필요 패키지 설치 (이미 pyproject.toml에 정의됨)
uv sync
```

### 2. 데이터베이스 마이그레이션
```bash
# 마이그레이션 파일 생성
python manage.py makemigrations

# 데이터베이스 적용
python manage.py migrate

# (MySQL 사용 시) 뷰/프로시저/트리거 적용
# mysql -u root -p idp_db < docs/sql_views.sql
# mysql -u root -p idp_db < docs/sql_procedures.sql
# mysql -u root -p idp_db < docs/sql_triggers.sql
```

### 3. 슈퍼유저 생성
```bash
python manage.py createsuperuser
```

### 4. 서버 실행
```bash
python manage.py runserver
```

### 5. Django Admin 접속
```
http://localhost:8000/admin/
```

## 🧪 테스트 실행

### 동시성 테스트
```bash
python manage.py test auth_transactions.tests.ConcurrencyTestCase
```

### 성능 테스트
```bash
python manage.py test auth_transactions.tests.PerformanceTestCase
```

### 보안 테스트
```bash
python manage.py test auth_transactions.tests.SecurityTestCase
```

## 📊 데모 시나리오

### 1. 정상 인증 플로우
```bash
# 1) Django Admin에서 ServiceProvider 등록
# - service_name: "A 쇼핑몰"
# - client_id: 자동 생성
# - client_secret: 입력 후 해시 저장
# - callback_url: https://shop-a.com/callback

# 2) 사용자 등록
# - username: testuser
# - phone_number: 010-1234-5678
# - PIN 설정: 123456

# 3) API로 인증 요청 (Postman 사용)
POST /api/v1/auth/request/
Headers:
  X-Client-ID: sp_xxxxx
  X-Client-Secret: yyyyy
Body:
  {
    "user_phone_number": "010-1234-5678"
  }

Response:
  {
    "transaction_id": "uuid-here",
    "expires_at": "2025-10-28T12:03:00",
    "message": "Authentication request created. User will be notified."
  }

# 4) 사용자 인증 확인
POST /api/v1/auth/confirm/
Body:
  {
    "transaction_id": "uuid-here",
    "pin_code": "123456"
  }

Response:
  {
    "status": "COMPLETED",
    "auth_code": "secure-auth-code-here",
    "message": "Authentication successful"
  }

# 5) 서비스 제공자가 상태 조회
GET /api/v1/auth/status/uuid-here/

Response:
  {
    "transaction_id": "uuid-here",
    "status": "COMPLETED",
    "auth_code": "secure-auth-code-here",
    "ci": "decrypted-ci-value",
    "di": "decrypted-di-value"
  }
```

### 2. 동시성 테스트 시나리오
```python
# tests.py 참조
# 2개 스레드가 동시에 같은 transaction_id로 확인 시도
# 결과: 하나만 성공, auth_code는 1개만 생성
```

### 3. 만료 처리 시나리오
```bash
# 1) PENDING 트랜잭션이 3분 경과
# 2) 프로시저 실행
CALL sp_expire_pending_transactions();

# 3) 결과 확인
SELECT status FROM auth_transactions_authtransaction WHERE transaction_id = 'uuid';
# status = 'EXPIRED'
```

## 📝 제출물

### 필수 파일
1. ✅ **ERD**: README.md에 ASCII 다이어그램
2. ✅ **DDL**: Django models.py (자동 생성)
3. ✅ **SQL 스크립트**:
   - `docs/sql_views.sql` (7개 뷰)
   - `docs/sql_procedures.sql` (6개 프로시저)
   - `docs/sql_triggers.sql` (8개 트리거)
4. ✅ **복잡한 쿼리**: README.md에 5건 (JOIN, 서브쿼리, CTE, ROLLUP, Window Function)
5. ✅ **테스트 시나리오**: `auth_transactions/tests.py`
6. ✅ **성능 보고서**: README.md에 튜닝 전후 비교
7. ✅ **보안 설계서**: README.md에 마스킹/RBAC/감사 로그
8. ✅ **Django 프로젝트**: 전체 소스 코드

### 보고서 내용 (README.md)
1. ✅ 정규화 사례 (1NF/2NF/3NF)
2. ✅ 트랜잭션 경계 및 ACID 목표
3. ✅ 인덱스 설계 및 성능 비교
4. ✅ 뷰/프로시저/트리거 구현
5. ✅ Entity 목록 및 ERD
6. ✅ 동시성 시나리오 및 해결책
7. ✅ 제약 조건 명세 (PK/FK/UK/CHECK)
8. ✅ 복잡한 쿼리 5건
9. ✅ 성능 튜닝 (전후 비교)
10. ✅ 보안/개인정보 (마스킹, RBAC, 감사 로그)
11. ✅ 데모 체크리스트

## 🎓 핵심 학습 포인트

### 데이터베이스 설계
- 정규화를 통한 데이터 중복 제거 및 무결성 보장
- PK/FK/UNIQUE/CHECK 제약조건 활용
- 인덱스 설계로 쿼리 성능 최적화

### 트랜잭션 관리
- ACID 속성 이해 및 적용
- SELECT FOR UPDATE를 통한 동시성 제어
- 격리 수준 (REPEATABLE READ) 설정

### 보안
- 필드 암호화 (CI/DI)
- 마스킹 (전화번호, 민감정보)
- RBAC (역할 기반 접근 제어)
- 감사 로그 (모든 중요 액션 기록)

### Django ORM
- 모델 정의 및 관계 설정
- select_related/prefetch_related로 N+1 문제 해결
- 트랜잭션 데코레이터 사용

### API 설계
- RESTful API 엔드포인트
- 적절한 HTTP 상태 코드 사용
- 예외 처리 및 에러 메시지

## 📌 주의사항

### 실제 운영 환경 적용 시 고려사항
1. **암호화 키 관리**: 현재는 Django SECRET_KEY를 사용하지만, 실제로는 AWS KMS, HashiCorp Vault 등의 Key Management Service 사용 권장
2. **비동기 처리**: 콜백 전송은 Celery 등의 Task Queue 사용 권장
3. **데이터베이스**: SQLite 대신 MySQL/PostgreSQL 사용 권장
4. **로깅**: 파일 로깅 및 중앙 집중식 로그 시스템 (ELK Stack 등) 도입
5. **모니터링**: APM 도구 (New Relic, DataDog 등) 연동

## 🔗 참고 자료
- Django Documentation: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- MySQL Documentation: https://dev.mysql.com/doc/
- 과제 가이드라인: `guideline.md`

---
**작성일**: 2025년 10월 28일  
**작성자**: z3rotig4r  
**프로젝트**: Simple-ID (IdP Backend System)

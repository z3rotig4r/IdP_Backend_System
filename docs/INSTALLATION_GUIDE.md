# 프로젝트 실행 가이드

## 📋 목차
1. [사전 요구사항](#사전-요구사항)
2. [프로젝트 설치](#프로젝트-설치)
3. [데이터베이스 설정](#데이터베이스-설정)
4. [서버 실행](#서버-실행)
5. [API 테스트](#api-테스트)
6. [웹 UI 접속](#웹-ui-접속)
7. [Django 테스트 실행](#django-테스트-실행)
8. [문제 해결](#문제-해결)

---

## 🔧 사전 요구사항

### 필수 소프트웨어
- **Python:** 3.10 이상
- **pip:** 최신 버전
- **Git:** 버전 관리

### 권장 환경
- **OS:** Linux (Ubuntu 20.04+), macOS, Windows 10+
- **메모리:** 4GB 이상
- **디스크:** 1GB 이상 여유 공간

---

## 📦 프로젝트 설치

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/IdP_Backend_System.git
cd IdP_Backend_System
```

### 2. 가상 환경 생성 (권장)
```bash
# Python 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 3. 의존성 패키지 설치
```bash
pip install -r requirements.txt
```

**주요 패키지:**
- Django 5.2.7
- djangorestframework
- cryptography
- bcrypt
- python-dotenv

---

## 🗄️ 데이터베이스 설정

### 1. 환경 변수 설정
`.env` 파일을 프로젝트 루트에 생성:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# 암호화 키 (32바이트 hex)
ENCRYPTION_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

**암호화 키 생성 방법:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 2. 데이터베이스 마이그레이션
```bash
# 마이그레이션 파일 생성
python3 manage.py makemigrations

# 마이그레이션 적용
python3 manage.py migrate
```

**예상 출력:**
```
Operations to perform:
  Apply all migrations: accounts, admin, auth, auth_transactions, audit_logs, contenttypes, services, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying accounts.0001_initial... OK
  ...
```

### 3. 초기 데이터 생성
```bash
# 슈퍼유저 생성
python3 manage.py createsuperuser

# 초기 데이터 로드 (선택사항)
python3 manage.py loaddata initial_data.json
```

### 4. SQL 스크립트 실행 (Views, Procedures, Triggers)
```bash
# SQLite3에서 스크립트 실행
sqlite3 db.sqlite3 < sql_scripts/views.sql
sqlite3 db.sqlite3 < sql_scripts/procedures.sql
sqlite3 db.sqlite3 < sql_scripts/triggers.sql
```

**스크립트 목록:**
- `views.sql`: 7개 뷰 (v_active_transactions, v_user_auth_summary 등)
- `procedures.sql`: 6개 프로시저 (expire_old_transactions, cleanup_expired 등)
- `triggers.sql`: 8개 트리거 (audit_auth_request, audit_auth_confirm 등)

---

## 🚀 서버 실행

### 개발 서버 실행
```bash
python3 manage.py runserver
```

**기본 접속 주소:**
- **웹 UI:** http://127.0.0.1:8000/
- **Django Admin:** http://127.0.0.1:8000/admin/
- **API Endpoint:** http://127.0.0.1:8000/api/v1/auth/api/

**서버 시작 확인:**
```
Django version 5.2.7, using settings 'idp_backend.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

### 다른 포트로 실행
```bash
python3 manage.py runserver 8080
```

---

## 🧪 API 테스트

### 1. 인증 요청 (auth_request)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/api/request/ \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "sp_test_001",
    "client_secret": "test_secret_123",
    "user_phone": "010-1234-5678"
  }'
```

**예상 응답:**
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "expires_at": "2025-01-26T15:30:00Z"
}
```

### 2. 인증 확인 (auth_confirm)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/api/confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
    "pin_code": "123456"
  }'
```

**예상 응답:**
```json
{
  "status": "COMPLETED",
  "ci": "encrypted_ci_data...",
  "di": "encrypted_di_data..."
}
```

### 3. 인증 상태 조회 (auth_status)
```bash
curl http://127.0.0.1:8000/api/v1/auth/api/status/550e8400-e29b-41d4-a716-446655440000/
```

**예상 응답:**
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "COMPLETED",
  "created_at": "2025-01-26T15:00:00Z",
  "updated_at": "2025-01-26T15:05:00Z"
}
```

**API 테스트 스크립트:**
```bash
# 자동화된 테스트 실행
bash scripts/test_api.sh
```

---

## 🌐 웹 UI 접속

### 주요 페이지

#### 1. 홈 페이지
```
http://127.0.0.1:8000/
```
- 서비스 소개
- 주요 기능 안내
- 회원가입/로그인 링크

#### 2. 로그인
```
http://127.0.0.1:8000/accounts/login/
```
**테스트 계정:**
- Username: `testuser`
- Password: `test1234`

#### 3. 대시보드
```
http://127.0.0.1:8000/dashboard/
```
- 인증 통계 (전체, 성공, 실패)
- 최근 인증 내역
- 빠른 작업 링크

#### 4. 인증 이력
```
http://127.0.0.1:8000/auth/history/
```
- 페이지네이션 (10개/페이지)
- 상태별 필터링
- 검색 기능

#### 5. Django Admin
```
http://127.0.0.1:8000/admin/
```
- 슈퍼유저 로그인 필요
- 모든 모델 관리
- CI/DI 마스킹 표시

---

## 🧪 Django 테스트 실행

### 전체 테스트 실행
```bash
python3 manage.py test --verbosity=2
```

**예상 결과:**
```
Ran 8 tests in 22.574s
OK
```

### 테스트 카테고리별 실행

#### 1. 동시성 테스트
```bash
python3 manage.py test auth_transactions.tests.ConcurrencyTestCase
```
- test_concurrent_authentication_confirmation
- test_race_condition_on_expiry_check

#### 2. 성능 테스트
```bash
python3 manage.py test auth_transactions.tests.PerformanceTestCase
```
- test_index_performance_on_status_query (0.0029s)
- test_select_related_performance (5.18x speedup)

#### 3. 보안 테스트
```bash
python3 manage.py test auth_transactions.tests.SecurityTestCase
```
- test_ci_di_encryption_decryption
- test_pin_code_hashing
- test_phone_number_masking
- test_audit_log_creation

### 커버리지 측정
```bash
# coverage 설치
pip install coverage

# 테스트 실행 + 커버리지 측정
coverage run --source='.' manage.py test

# 리포트 생성
coverage report

# HTML 리포트 생성
coverage html
# 브라우저에서 htmlcov/index.html 열기
```

---

## ❓ 문제 해결

### 1. 마이그레이션 오류
**문제:** `django.db.utils.OperationalError: no such table`

**해결:**
```bash
# 데이터베이스 삭제 후 재생성
rm db.sqlite3
python3 manage.py migrate
```

### 2. 암호화 키 오류
**문제:** `ValueError: Encryption key must be 32 bytes`

**해결:**
```bash
# .env 파일에 올바른 키 설정
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" >> .env
```

### 3. 포트 충돌
**문제:** `Error: That port is already in use.`

**해결:**
```bash
# 다른 포트로 실행
python3 manage.py runserver 8080

# 또는 프로세스 종료
lsof -ti:8000 | xargs kill -9
```

### 4. 정적 파일 로딩 실패
**문제:** CSS/JS 파일이 로드되지 않음

**해결:**
```bash
# 정적 파일 수집
python3 manage.py collectstatic --noinput
```

### 5. CSRF 토큰 오류
**문제:** `CSRF verification failed`

**해결:**
```python
# API 테스트 시 CSRF 제외 데코레이터 사용 (개발 환경)
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def api_view(request):
    pass
```

---

## 📚 추가 문서

- **API 문서:** [docs/API_TESTING_GUIDE.md](docs/API_TESTING_GUIDE.md)
- **테스트 가이드:** [docs/TEST_GUIDE.md](docs/TEST_GUIDE.md)
- **성능 보고서:** [docs/PERFORMANCE_REPORT.md](docs/PERFORMANCE_REPORT.md)
- **보안 보고서:** [docs/SECURITY_REPORT.md](docs/SECURITY_REPORT.md)
- **프로젝트 요약:** [docs/PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md)

---

## 🤝 기여 방법

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참조

---

## 👨‍💻 개발자

**프로젝트 담당:** z3rotig4r  
**이메일:** your-email@example.com  
**GitHub:** https://github.com/z3rotig4r/IdP_Backend_System

---

**최종 업데이트:** 2025-01-26  
**버전:** 1.0.0

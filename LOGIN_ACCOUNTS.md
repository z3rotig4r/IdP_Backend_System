# 📋 로그인 계정 정보

## 🔐 관리자 계정 (Django Admin 전용)

### Admin 계정
```
URL: http://localhost:8000/admin/
Username: admin
Password: admin123!
용도: Django Admin 관리
```

**⚠️ 주의:** admin 계정은 관리자용이므로 일반 웹 UI 대시보드에서는 인증 요청이 0개입니다.

---

## 👤 일반 사용자 계정 (웹 UI 및 인증 테스트용)

### TestUser1 계정 (권장)
```
URL: http://localhost:8000/accounts/login/
Username: testuser1
Password: testuser123!
전화번호: 010-2345-6789
PIN: 234567
```

**✅ 사용 가능:**
- 웹 UI 대시보드: http://localhost:8000/dashboard/
- 인증 이력: http://localhost:8000/auth/history/
- 대기 중인 인증: http://localhost:8000/auth/pending/
- 인증 요청 11개 (대기 중 1개)

### TestUser2 계정
```
URL: http://localhost:8000/accounts/login/
Username: testuser2
Password: testuser123!
전화번호: 010-3456-7890
PIN: 345678
```

---

## 🔧 인증 요청 테스트 방법

### 1단계: API로 인증 요청 생성
```bash
cd /home/z3rotig4r/IdP_Backend_System
./test_auth_flow.sh
```

### 2단계: 웹에서 로그인 및 승인
1. **로그인**: http://localhost:8000/accounts/login/
   - Username: `testuser1`
   - Password: `testuser123!`

2. **대기 요청 확인**: http://localhost:8000/auth/pending/
   - 네비게이션 바의 🔔 알림 클릭

3. **PIN 입력 후 승인**:
   - PIN: `234567`
   - '승인하기' 버튼 클릭

---

## 🐛 문제 해결

### 로그인이 안 될 때
```bash
# testuser1 비밀번호 재설정
python3 manage.py shell << 'EOF'
from accounts.models import User
user = User.objects.get(username='testuser1')
user.set_password('testuser123!')
user.save()
print("✅ 비밀번호 재설정 완료")
EOF
```

### admin 대시보드에 데이터가 없을 때
**정상입니다!** admin은 관리자 계정이므로:
- Django Admin 페이지: http://localhost:8000/admin/
- 일반 사용자 대시보드는 `testuser1`으로 로그인하세요.

---

## 📊 현재 데이터 상태

| 사용자 | 전체 요청 | 완료 | 대기 중 | 용도 |
|--------|----------|------|---------|------|
| **admin** | 0 | 0 | 0 | Django Admin 전용 |
| **testuser1** | 11 | 10 | 1 | 테스트 계정 (권장) |
| **testuser2** | 0 | 0 | 0 | 추가 테스트 계정 |

---

**업데이트:** 2025-11-26  
**작성자:** IdP Backend System

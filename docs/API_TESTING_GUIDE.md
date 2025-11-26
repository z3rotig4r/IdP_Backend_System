# API 테스트 가이드

## Postman 또는 curl을 사용한 API 테스트

### 사전 준비
1. Django 서버 실행: `python manage.py runserver`
2. 테스트 데이터 확인 (setup.sh 실행 후):
   - User: testuser (phone: 010-1234-5678, PIN: 123456)
   - ServiceProvider: client_id=test_client_123, client_secret=test_secret_456

---

## 1. 인증 요청 API

### Endpoint
```
POST http://localhost:8000/api/v1/auth/request/
```

### Headers
```
Content-Type: application/json
X-Client-ID: test_client_123
X-Client-Secret: test_secret_456
```

### Request Body
```json
{
    "user_phone_number": "010-1234-5678"
}
```

### Response (Success - 200 OK)
```json
{
    "transaction_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "expires_at": "2025-10-28T12:03:00+09:00",
    "message": "Authentication request created. User will be notified."
}
```

### cURL 명령어
```bash
curl -X POST http://localhost:8000/api/v1/auth/request/ \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: test_client_123" \
  -H "X-Client-Secret: test_secret_456" \
  -d '{"user_phone_number": "010-1234-5678"}'
```

### 오류 케이스

#### 1) 잘못된 client_id/secret (401 Unauthorized)
```json
{
    "error": "Invalid client credentials"
}
```

#### 2) 사용자 없음 (404 Not Found)
```json
{
    "error": "User not found"
}
```

#### 3) 필수 필드 누락 (400 Bad Request)
```json
{
    "error": "Missing required fields"
}
```

---

## 2. 인증 확인 API

### Endpoint
```
POST http://localhost:8000/api/v1/auth/confirm/
```

### Headers
```
Content-Type: application/json
```

### Request Body
```json
{
    "transaction_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "pin_code": "123456"
}
```

### Response (Success - 200 OK)
```json
{
    "status": "COMPLETED",
    "auth_code": "xYz123AbC456DeF789...",
    "message": "Authentication successful"
}
```

### cURL 명령어
```bash
# 먼저 transaction_id를 위 1번 API 응답에서 복사
curl -X POST http://localhost:8000/api/v1/auth/confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "pin_code": "123456"
  }'
```

### 오류 케이스

#### 1) 이미 처리된 트랜잭션 (400 Bad Request)
```json
{
    "error": "Transaction already completed"
}
```

#### 2) 만료된 트랜잭션 (400 Bad Request)
```json
{
    "error": "Transaction expired"
}
```

#### 3) 잘못된 PIN (401 Unauthorized)
```json
{
    "error": "Invalid PIN"
}
```

#### 4) 트랜잭션 없음 (404 Not Found)
```json
{
    "error": "Transaction not found"
}
```

---

## 3. 인증 상태 조회 API

### Endpoint
```
GET http://localhost:8000/api/v1/auth/status/{transaction_id}/
```

### Headers
```
없음 (GET 요청)
```

### Response (PENDING 상태)
```json
{
    "transaction_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "PENDING",
    "created_at": "2025-10-28T12:00:00+09:00",
    "expires_at": "2025-10-28T12:03:00+09:00"
}
```

### Response (COMPLETED 상태)
```json
{
    "transaction_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "COMPLETED",
    "created_at": "2025-10-28T12:00:00+09:00",
    "expires_at": "2025-10-28T12:03:00+09:00",
    "auth_code": "xYz123AbC456DeF789...",
    "ci": "decrypted-ci-value",
    "di": "decrypted-di-value"
}
```

### cURL 명령어
```bash
curl -X GET http://localhost:8000/api/v1/auth/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890/
```

### 오류 케이스

#### 1) 트랜잭션 없음 (404 Not Found)
```json
{
    "error": "Transaction not found"
}
```

---

## 전체 플로우 테스트 (Bash Script)

```bash
#!/bin/bash

# 1. 인증 요청
echo "1️⃣ 인증 요청..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/request/ \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: test_client_123" \
  -H "X-Client-Secret: test_secret_456" \
  -d '{"user_phone_number": "010-1234-5678"}')

echo "Response: $RESPONSE"
echo ""

# transaction_id 추출 (jq 사용)
TRANSACTION_ID=$(echo $RESPONSE | jq -r '.transaction_id')
echo "Transaction ID: $TRANSACTION_ID"
echo ""

# 2. 상태 조회 (PENDING 확인)
echo "2️⃣ 상태 조회 (PENDING 확인)..."
curl -s -X GET http://localhost:8000/api/v1/auth/status/$TRANSACTION_ID/ | jq
echo ""

# 3. 인증 확인
echo "3️⃣ 인증 확인 (PIN 입력)..."
curl -s -X POST http://localhost:8000/api/v1/auth/confirm/ \
  -H "Content-Type: application/json" \
  -d "{\"transaction_id\": \"$TRANSACTION_ID\", \"pin_code\": \"123456\"}" | jq
echo ""

# 4. 상태 조회 (COMPLETED 확인)
echo "4️⃣ 상태 조회 (COMPLETED 확인)..."
curl -s -X GET http://localhost:8000/api/v1/auth/status/$TRANSACTION_ID/ | jq
echo ""

echo "✅ 전체 플로우 테스트 완료!"
```

저장 후 실행:
```bash
chmod +x test_api_flow.sh
./test_api_flow.sh
```

---

## Postman Collection

### Collection 정보
- Name: IdP Backend System API
- Base URL: `{{base_url}}` = http://localhost:8000

### Environment Variables
```json
{
    "base_url": "http://localhost:8000",
    "client_id": "test_client_123",
    "client_secret": "test_secret_456",
    "test_phone": "010-1234-5678",
    "test_pin": "123456"
}
```

### Request 1: Auth Request
- Method: POST
- URL: `{{base_url}}/api/v1/auth/request/`
- Headers:
  - Content-Type: application/json
  - X-Client-ID: {{client_id}}
  - X-Client-Secret: {{client_secret}}
- Body (JSON):
```json
{
    "user_phone_number": "{{test_phone}}"
}
```
- Tests Script:
```javascript
// transaction_id를 환경 변수에 저장
var jsonData = pm.response.json();
pm.environment.set("transaction_id", jsonData.transaction_id);
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});
```

### Request 2: Auth Confirm
- Method: POST
- URL: `{{base_url}}/api/v1/auth/confirm/`
- Headers:
  - Content-Type: application/json
- Body (JSON):
```json
{
    "transaction_id": "{{transaction_id}}",
    "pin_code": "{{test_pin}}"
}
```

### Request 3: Auth Status
- Method: GET
- URL: `{{base_url}}/api/v1/auth/status/{{transaction_id}}/`

---

## 동시성 테스트 (Apache Bench)

### 동일 transaction_id에 대한 동시 요청
```bash
# 먼저 transaction_id 생성
TRANSACTION_ID=$(curl -s -X POST http://localhost:8000/api/v1/auth/request/ \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: test_client_123" \
  -H "X-Client-Secret: test_secret_456" \
  -d '{"user_phone_number": "010-1234-5678"}' | jq -r '.transaction_id')

# POST 데이터를 파일로 저장
echo "{\"transaction_id\": \"$TRANSACTION_ID\", \"pin_code\": \"123456\"}" > post_data.json

# Apache Bench로 동시 요청 (10개 동시, 총 20개)
ab -n 20 -c 10 -p post_data.json -T application/json \
  http://localhost:8000/api/v1/auth/confirm/

# 결과: 하나만 성공(200), 나머지는 실패(400 - Already processed)
```

---

## Python 스크립트를 사용한 테스트

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. 인증 요청
print("1️⃣ 인증 요청...")
response = requests.post(
    f"{BASE_URL}/api/v1/auth/request/",
    headers={
        "Content-Type": "application/json",
        "X-Client-ID": "test_client_123",
        "X-Client-Secret": "test_secret_456"
    },
    json={"user_phone_number": "010-1234-5678"}
)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Response: {json.dumps(data, indent=2)}")
transaction_id = data['transaction_id']
print()

# 2. 상태 조회 (PENDING)
print("2️⃣ 상태 조회 (PENDING)...")
response = requests.get(f"{BASE_URL}/api/v1/auth/status/{transaction_id}/")
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
print()

# 3. 인증 확인
print("3️⃣ 인증 확인...")
response = requests.post(
    f"{BASE_URL}/api/v1/auth/confirm/",
    json={
        "transaction_id": transaction_id,
        "pin_code": "123456"
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
print()

# 4. 상태 조회 (COMPLETED)
print("4️⃣ 상태 조회 (COMPLETED)...")
response = requests.get(f"{BASE_URL}/api/v1/auth/status/{transaction_id}/")
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
print()

print("✅ 전체 플로우 테스트 완료!")
```

---

## 예상 시나리오별 응답

### 시나리오 1: 정상 플로우 ✅
1. 인증 요청 → 200 OK, transaction_id 발급
2. 상태 조회 → 200 OK, status=PENDING
3. 인증 확인 → 200 OK, status=COMPLETED, auth_code 발급
4. 상태 조회 → 200 OK, status=COMPLETED, CI/DI 포함

### 시나리오 2: 만료된 트랜잭션 ⏰
1. 인증 요청 → 200 OK
2. 3분 대기
3. 인증 확인 → 400 Bad Request, "Transaction expired"

### 시나리오 3: 중복 확인 시도 🔄
1. 인증 요청 → 200 OK
2. 인증 확인 → 200 OK
3. 인증 확인 (재시도) → 400 Bad Request, "Transaction already completed"

### 시나리오 4: 잘못된 PIN 🔑
1. 인증 요청 → 200 OK
2. 인증 확인 (wrong PIN) → 401 Unauthorized, "Invalid PIN"
3. 5회 반복 → 계정 잠금 (is_active=False)

---

## 주의사항

1. **트랜잭션 만료 시간**: 기본 3분이므로 빠르게 테스트해야 함
2. **중복 처리 방지**: 같은 transaction_id로는 한 번만 성공 가능
3. **클라이언트 인증**: client_id와 client_secret이 정확해야 함
4. **데이터베이스 초기화**: 테스트 후 `python manage.py flush` 또는 `python manage.py migrate --run-syncdb`로 초기화 가능

#!/bin/bash

echo "==================================="
echo "IdP API 전체 흐름 테스트"
echo "==================================="
echo ""

# Step 1: Auth Request
echo "[1] 인증 요청 (auth_request)"
echo "-----------------------------------"
response1=$(curl -s -X POST http://localhost:8000/api/v1/auth/api/request/ \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: sp_OmenCwYu_Y7DB8JxIF-ddYFVXZFw-Xi9" \
  -H "X-Client-Secret: test_secret_123456789" \
  -d '{"user_phone_number": "010-2345-6789"}')

echo "$response1" | python3 -m json.tool
TX_ID=$(echo "$response1" | python3 -c "import sys, json; print(json.load(sys.stdin)['transaction_id'])")
echo ""
echo "✓ Transaction ID: $TX_ID"
echo ""

# Step 2: Auth Confirm
echo "[2] 인증 확인 (auth_confirm)"
echo "-----------------------------------"
curl -s -X POST http://localhost:8000/api/v1/auth/api/confirm/ \
  -H "Content-Type: application/json" \
  -d "{\"transaction_id\": \"$TX_ID\", \"pin_code\": \"234567\"}" | python3 -m json.tool
echo ""

# Step 3: Auth Status
echo "[3] 상태 조회 (auth_status)"
echo "-----------------------------------"
curl -s -X GET "http://localhost:8000/api/v1/auth/api/status/$TX_ID/" \
  -H "X-Client-ID: sp_OmenCwYu_Y7DB8JxIF-ddYFVXZFw-Xi9" \
  -H "X-Client-Secret: test_secret_123456789" | python3 -m json.tool
echo ""

echo "==================================="
echo "✅ 모든 API 테스트 완료!"
echo "==================================="

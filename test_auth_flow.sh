#!/bin/bash

echo "==================================="
echo "🔐 IdP 인증 요청 완전 가이드"
echo "==================================="
echo ""

# 서비스 제공자 정보
CLIENT_ID="sp_gbkG-9dHfX8LVoTrm82qGR-cLGA-h8Pf"
CLIENT_SECRET="0bf135e696b0c5b77fe75bb1235fe0c3e89b621f23882cc619e8d8888ce844ea"
USER_PHONE="010-2345-6789"

echo "📋 Step 1: 인증 요청 (API)"
echo "-----------------------------------"
echo "서비스 제공자가 IdP에 인증을 요청합니다."
echo ""

response=$(curl -s -X POST http://localhost:8000/api/v1/auth/api/request/ \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: $CLIENT_ID" \
  -H "X-Client-Secret: $CLIENT_SECRET" \
  -d "{\"user_phone_number\": \"$USER_PHONE\"}")

echo "$response" | python3 -m json.tool

# Transaction ID 추출
TX_ID=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('transaction_id', ''))" 2>/dev/null)

if [ -z "$TX_ID" ]; then
    echo ""
    echo "❌ 인증 요청 실패!"
    echo "응답: $response"
    exit 1
fi

echo ""
echo "✅ Transaction ID: $TX_ID"
echo ""

echo "👤 Step 2: 사용자 웹에서 확인 및 승인"
echo "-----------------------------------"
echo "1. 웹 브라우저로 이동: http://localhost:8000/accounts/login/"
echo "2. 로그인 정보:"
echo "   - Username: testuser1"
echo "   - Password: testuser123!"
echo ""
echo "3. 로그인 후 대기 중인 인증 요청 확인:"
echo "   - URL: http://localhost:8000/auth/pending/"
echo "   - 또는 네비게이션 바의 🔔 알림 클릭"
echo ""
echo "4. 인증 승인 페이지에서 PIN 입력:"
echo "   - URL: http://localhost:8000/auth/approval/$TX_ID/"
echo "   - PIN: 234567"
echo "   - '승인하기' 버튼 클릭"
echo ""
echo "⏳ 사용자가 웹에서 승인할 때까지 대기 중..."
echo "   (수동으로 승인하세요. 10초 후 상태를 확인합니다)"
sleep 10
echo ""

echo "🔍 Step 3: 인증 상태 확인 (API)"
echo "-----------------------------------"
curl -s -X GET "http://localhost:8000/api/v1/auth/api/status/$TX_ID/" \
  -H "X-Client-ID: $CLIENT_ID" \
  -H "X-Client-Secret: $CLIENT_SECRET" | python3 -m json.tool

echo ""
echo "==================================="
echo "📝 요약"
echo "==================================="
echo "✅ Step 1: API로 인증 요청 생성"
echo "👉 Step 2: 사용자가 웹에서 승인 필요"
echo "✅ Step 3: API로 결과 확인 (CI/DI 수신)"
echo ""
echo "🌐 사용자 승인 URL:"
echo "   http://localhost:8000/auth/pending/"
echo "==================================="

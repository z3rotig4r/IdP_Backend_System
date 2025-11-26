#!/bin/bash

echo "=========================================="
echo "       웹 UI 기능 테스트"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8000"
COOKIE_FILE="/tmp/django_cookies.txt"

# 색상 코드
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_count=0
pass_count=0
fail_count=0

# 테스트 함수
test_page() {
    local name=$1
    local url=$2
    local expected_code=$3
    
    test_count=$((test_count + 1))
    
    response=$(curl -s -o /dev/null -w "%{http_code}" -b "$COOKIE_FILE" "$BASE_URL$url")
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✅ PASS${NC} - $name (HTTP $response)"
        pass_count=$((pass_count + 1))
    else
        echo -e "${RED}❌ FAIL${NC} - $name (Expected: $expected_code, Got: $response)"
        fail_count=$((fail_count + 1))
    fi
}

test_content() {
    local name=$1
    local url=$2
    local search_text=$3
    
    test_count=$((test_count + 1))
    
    response=$(curl -s -b "$COOKIE_FILE" "$BASE_URL$url")
    
    if echo "$response" | grep -q "$search_text"; then
        echo -e "${GREEN}✅ PASS${NC} - $name (Content found)"
        pass_count=$((pass_count + 1))
    else
        echo -e "${RED}❌ FAIL${NC} - $name (Content not found: $search_text)"
        fail_count=$((fail_count + 1))
    fi
}

echo "=== 1. 공개 페이지 접근성 테스트 ==="
echo ""

test_page "홈페이지" "/" "200"
test_page "로그인 페이지" "/accounts/login/" "200"
test_page "회원가입 페이지" "/accounts/register/" "200"

echo ""
echo "=== 2. 페이지 콘텐츠 검증 ==="
echo ""

test_content "홈페이지 제목" "/" "Simple-ID"
test_content "로그인 폼" "/accounts/login/" "username"
test_content "회원가입 폼" "/accounts/register/" "password1"

echo ""
echo "=== 3. 로그인 필요 페이지 (리다이렉트 테스트) ==="
echo ""

test_page "대시보드 (미로그인)" "/dashboard/" "302"
test_page "프로필 (미로그인)" "/accounts/profile/" "302"
test_page "인증 이력 (미로그인)" "/auth/history/" "302"

echo ""
echo "=== 4. 로그인 테스트 ==="
echo ""

# CSRF 토큰 가져오기
csrf_token=$(curl -s -c "$COOKIE_FILE" "$BASE_URL/accounts/login/" | grep -oP 'csrfmiddlewaretoken.*?value="\K[^"]+')

if [ -n "$csrf_token" ]; then
    echo "✓ CSRF 토큰 획득: ${csrf_token:0:20}..."
    
    # 로그인 시도
    login_response=$(curl -s -o /dev/null -w "%{http_code}" \
        -b "$COOKIE_FILE" -c "$COOKIE_FILE" \
        -X POST "$BASE_URL/accounts/login/" \
        -d "username=testuser1" \
        -d "password=user123!@#" \
        -d "csrfmiddlewaretoken=$csrf_token" \
        -L)
    
    if [ "$login_response" = "200" ]; then
        echo -e "${GREEN}✅ 로그인 성공${NC}"
        pass_count=$((pass_count + 1))
    else
        echo -e "${RED}❌ 로그인 실패 (HTTP $login_response)${NC}"
        fail_count=$((fail_count + 1))
    fi
    test_count=$((test_count + 1))
else
    echo -e "${RED}❌ CSRF 토큰 획득 실패${NC}"
    fail_count=$((fail_count + 1))
    test_count=$((test_count + 1))
fi

echo ""
echo "=== 5. 인증 후 페이지 접근 테스트 ==="
echo ""

test_page "대시보드 (로그인 후)" "/dashboard/" "200"
test_page "프로필 (로그인 후)" "/accounts/profile/" "200"
test_page "인증 이력 (로그인 후)" "/auth/history/" "200"

echo ""
echo "=== 6. 정적 파일 로딩 테스트 ==="
echo ""

test_page "CSS 파일" "/static/css/style.css" "200"
test_page "JS 파일" "/static/js/main.js" "200"

echo ""
echo "=========================================="
echo "           테스트 결과 요약"
echo "=========================================="
echo ""
echo "총 테스트: $test_count"
echo -e "${GREEN}성공: $pass_count${NC}"
echo -e "${RED}실패: $fail_count${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✅ 모든 테스트 통과!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  일부 테스트 실패${NC}"
    exit 1
fi

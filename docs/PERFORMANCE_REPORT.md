# 성능 측정 및 최적화 보고서

## 1. 개요
본 문서는 IdP Backend System의 성능 측정 결과와 최적화 내역을 정리합니다.

---

## 2. 인덱스 설계 및 효과

### 2.1 생성된 인덱스 목록

#### accounts_user 테이블
```sql
CREATE UNIQUE INDEX idx_user_phone ON accounts_user(phone_number);
CREATE UNIQUE INDEX idx_user_ci ON accounts_user(ci);
CREATE INDEX idx_user_created ON accounts_user(created_at DESC);
```

#### auth_transactions_authtransaction 테이블
```sql
-- 복합 인덱스 (status + expires_at)
CREATE INDEX idx_tx_status_expires 
ON auth_transactions_authtransaction(status, expires_at);

-- 복합 인덱스 (user_id + created_at)
CREATE INDEX idx_tx_user_created 
ON auth_transactions_authtransaction(user_id, created_at DESC);

-- 복합 인덱스 (service_provider_id + created_at)
CREATE INDEX idx_tx_sp_created 
ON auth_transactions_authtransaction(service_provider_id, created_at DESC);
```

#### audit_logs_auditlog 테이블
```sql
CREATE INDEX idx_audit_user_time ON audit_logs_auditlog(user_id, timestamp DESC);
CREATE INDEX idx_audit_action_time ON audit_logs_auditlog(action, timestamp DESC);
```

### 2.2 인덱스 효과 측정

#### Query 1: PENDING 상태 + 만료되지 않은 트랜잭션 조회
```python
AuthTransaction.objects.filter(
    status='PENDING',
    expires_at__gt=timezone.now()
).order_by('-created_at')
```

**실행 계획:**
```
SEARCH auth_transactions_authtransaction 
USING INDEX idx_tx_status_expires (status=? AND expires_at>?)
```

**결과:**
- ✅ **idx_tx_status_expires 인덱스 사용 확인**
- 100개 레코드 조회 시 **0.0029s** 실행 시간
- Full Table Scan 방지

#### Query 2: 특정 사용자의 최근 트랜잭션 조회
```python
AuthTransaction.objects.filter(
    user_id=1
).order_by('-created_at')[:10]
```

**실행 계획:**
```
SEARCH auth_transactions_authtransaction 
USING INDEX idx_tx_user_created (user_id=?)
```

**결과:**
- ✅ **idx_tx_user_created 인덱스 사용 확인**
- ORDER BY 절도 인덱스로 처리 (정렬 비용 제거)

---

## 3. N+1 쿼리 문제 해결

### 3.1 문제 상황
```python
# ❌ N+1 쿼리 발생 코드
transactions = AuthTransaction.objects.all()
for tx in transactions:
    print(tx.user.username)           # 쿼리 1번
    print(tx.service_provider.name)   # 쿼리 1번
# 총 쿼리: 1 + N*2 = 201개 (N=100)
```

### 3.2 해결 방법
```python
# ✅ select_related 사용
transactions = AuthTransaction.objects.select_related(
    'user', 'service_provider'
).all()
for tx in transactions:
    print(tx.user.username)           # 추가 쿼리 없음
    print(tx.service_provider.name)   # 추가 쿼리 없음
# 총 쿼리: 1개 (JOIN 사용)
```

### 3.3 측정 결과

**테스트 데이터:** 100개 AuthTransaction 레코드

| 방법 | 실행 시간 | 쿼리 수 | 성능 개선 |
|------|-----------|---------|-----------|
| **Without select_related** | 0.0084s | 201개 | - |
| **With select_related** | 0.0016s | 1개 | **5.18x faster** |

**테스트 코드 출력:**
```
Without select_related: 0.0084s
With select_related: 0.0016s
Speedup: 5.18x
```

---

## 4. 동시성 제어 (SELECT FOR UPDATE)

### 4.1 구현 코드
```python
# auth_transactions/views.py - auth_confirm()
with transaction.atomic():
    auth_tx = AuthTransaction.objects.select_for_update().get(
        transaction_id=transaction_id
    )
    # 중복 처리 방지 로직
    if auth_tx.status != 'PENDING':
        return JsonResponse({'error': 'Already processed'}, status=400)
    
    auth_tx.status = 'COMPLETED'
    auth_tx.save()
```

### 4.2 효과
- ✅ 동시 요청 시 첫 번째 요청만 성공 (200 OK)
- ✅ 두 번째 요청은 실패 (400 Bad Request)
- ✅ Race Condition 방지

---

## 5. 만료 트랜잭션 처리 성능

### 5.1 자동 정리 프로시저
```sql
CREATE PROCEDURE expire_old_transactions()
BEGIN
    UPDATE auth_transactions_authtransaction
    SET status = 'EXPIRED',
        updated_at = CURRENT_TIMESTAMP
    WHERE status = 'PENDING'
      AND expires_at < CURRENT_TIMESTAMP;
END;
```

### 5.2 인덱스 활용
- **idx_tx_status_expires** 인덱스로 만료 대상 빠르게 검색
- WHERE 절 (status + expires_at) 조건 모두 인덱스 커버

---

## 6. 종합 성능 지표

### 6.1 Django 테스트 결과
```
Ran 8 tests in 22.574s
OK

test_index_performance_on_status_query: 0.0029s (100 records)
test_select_related_performance: 5.18x speedup
test_concurrent_authentication_confirmation: PASSED
test_race_condition_on_expiry_check: PASSED
test_phone_number_masking: PASSED
test_ci_di_encryption_decryption: PASSED
test_pin_code_hashing: PASSED
test_audit_log_creation: PASSED
```

### 6.2 주요 성능 개선 사항

| 항목 | 개선 전 | 개선 후 | 개선율 |
|------|---------|---------|--------|
| **N+1 쿼리** | 201 queries | 1 query | **200x** |
| **실행 시간** | 0.0084s | 0.0016s | **5.18x** |
| **인덱스 사용** | ❌ Full Scan | ✅ Index Scan | - |
| **동시성 제어** | ❌ Race Condition | ✅ SELECT FOR UPDATE | - |

### 6.3 데이터베이스 제약 조건
- ✅ PK/FK 제약 조건 (4개 테이블)
- ✅ UNIQUE 제약 (phone_number, ci)
- ✅ CHECK 제약 (expires_at > created_at)
- ✅ NOT NULL 제약 (필수 필드)

---

## 7. 결론

### 7.1 목표 달성
- ✅ **인덱스 효과 확인:** EXPLAIN QUERY PLAN으로 인덱스 사용 검증
- ✅ **N+1 쿼리 해결:** select_related로 5.18배 성능 개선
- ✅ **동시성 제어:** SELECT FOR UPDATE로 Race Condition 방지
- ✅ **쿼리 실행 시간:** 0.0029s (100개 레코드, 인덱스 사용)

### 7.2 추가 최적화 가능 영역
1. **Partial Index:** PENDING 상태만 인덱싱 (SQLite 3.8.0+)
2. **Covering Index:** SELECT 절 컬럼 포함 (읽기 성능 추가 향상)
3. **Connection Pooling:** django-db-pool 사용
4. **Redis 캐싱:** 자주 조회되는 데이터 캐싱

---

**보고서 작성일:** 2025-01-26  
**테스트 환경:** Django 5.2.7, SQLite 3, Python 3.10+  
**측정 도구:** Django TestCase, EXPLAIN QUERY PLAN

-- ============================================
-- IdP Backend System - Database Views
-- 과제 요구사항: 뷰(View) 구현
-- ============================================

-- 1. 마스킹 뷰 (Masking View) - 보안 목적
-- 일반 사용자/직원이 사용하는 뷰 (민감정보 마스킹)
CREATE OR REPLACE VIEW v_user_masked AS
SELECT 
    id,
    username,
    email,
    CONCAT(LEFT(phone_number, 4), '-****-', RIGHT(phone_number, 4)) AS phone_number,
    '*********************' AS ci,
    '*********************' AS di,
    is_active,
    is_staff,
    date_joined,
    last_login,
    created_at
FROM accounts_user;

-- 2. 인증 통계 뷰 (Authentication Statistics View)
-- 서비스별 일별 인증 통계
CREATE OR REPLACE VIEW v_auth_statistics AS
SELECT 
    sp.id AS service_provider_id,
    sp.service_name,
    DATE(at.created_at) AS auth_date,
    COUNT(*) AS total_requests,
    SUM(CASE WHEN at.status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_count,
    SUM(CASE WHEN at.status = 'FAILED' THEN 1 ELSE 0 END) AS failed_count,
    SUM(CASE WHEN at.status = 'EXPIRED' THEN 1 ELSE 0 END) AS expired_count,
    SUM(CASE WHEN at.status = 'PENDING' THEN 1 ELSE 0 END) AS pending_count,
    ROUND(
        SUM(CASE WHEN at.status = 'COMPLETED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
        2
    ) AS success_rate,
    ROUND(
        AVG(
            CASE WHEN at.status = 'COMPLETED' 
            THEN TIMESTAMPDIFF(SECOND, at.created_at, at.updated_at)
            ELSE NULL END
        ), 
        2
    ) AS avg_processing_time
FROM auth_transactions_authtransaction at
INNER JOIN services_serviceprovider sp ON at.service_provider_id = sp.id
GROUP BY sp.id, sp.service_name, DATE(at.created_at);

-- 3. 감사 로그 요약 뷰 (Audit Log Summary View)
-- 사용자별 액션별 요약
CREATE OR REPLACE VIEW v_audit_summary AS
SELECT 
    u.id AS user_id,
    u.username,
    al.action,
    COUNT(*) AS action_count,
    MAX(al.timestamp) AS last_action_time,
    MIN(al.timestamp) AS first_action_time
FROM audit_logs_auditlog al
LEFT JOIN accounts_user u ON al.user_id = u.id
GROUP BY u.id, u.username, al.action;

-- 4. 활성 트랜잭션 뷰 (Active Transactions View)
-- 현재 진행 중인(PENDING) 트랜잭션 목록
CREATE OR REPLACE VIEW v_active_transactions AS
SELECT 
    at.transaction_id,
    u.username,
    u.phone_number,
    sp.service_name,
    at.status,
    at.created_at,
    at.expires_at,
    TIMESTAMPDIFF(SECOND, NOW(), at.expires_at) AS seconds_until_expiry
FROM auth_transactions_authtransaction at
INNER JOIN accounts_user u ON at.user_id = u.id
INNER JOIN services_serviceprovider sp ON at.service_provider_id = sp.id
WHERE at.status = 'PENDING' 
  AND at.expires_at > NOW()
ORDER BY at.expires_at ASC;

-- 5. 사용자 인증 이력 뷰 (User Authentication History View)
-- 사용자별 최근 10건의 인증 이력
CREATE OR REPLACE VIEW v_user_auth_history AS
SELECT 
    u.id AS user_id,
    u.username,
    at.transaction_id,
    sp.service_name,
    at.status,
    at.created_at,
    at.expires_at,
    at.failure_reason,
    ROW_NUMBER() OVER (PARTITION BY u.id ORDER BY at.created_at DESC) AS row_num
FROM accounts_user u
INNER JOIN auth_transactions_authtransaction at ON u.id = at.user_id
INNER JOIN services_serviceprovider sp ON at.service_provider_id = sp.id;

-- 6. 서비스 제공자 대시보드 뷰 (Service Provider Dashboard)
-- 서비스별 전체 통계 (총 요청, 성공률, 평균 처리 시간)
CREATE OR REPLACE VIEW v_service_dashboard AS
SELECT 
    sp.id,
    sp.service_name,
    sp.is_active,
    COUNT(at.transaction_id) AS total_transactions,
    SUM(CASE WHEN at.status = 'COMPLETED' THEN 1 ELSE 0 END) AS total_completed,
    ROUND(
        SUM(CASE WHEN at.status = 'COMPLETED' THEN 1 ELSE 0 END) * 100.0 / 
        NULLIF(COUNT(at.transaction_id), 0), 
        2
    ) AS overall_success_rate,
    ROUND(
        AVG(
            CASE WHEN at.status = 'COMPLETED'
            THEN TIMESTAMPDIFF(SECOND, at.created_at, at.updated_at)
            ELSE NULL END
        ),
        2
    ) AS avg_processing_time,
    MIN(at.created_at) AS first_transaction,
    MAX(at.created_at) AS last_transaction
FROM services_serviceprovider sp
LEFT JOIN auth_transactions_authtransaction at ON sp.id = at.service_provider_id
GROUP BY sp.id, sp.service_name, sp.is_active;

-- 7. 의심스러운 활동 뷰 (Suspicious Activity View)
-- 최근 1시간 내 실패가 많은 사용자
CREATE OR REPLACE VIEW v_suspicious_activity AS
SELECT 
    u.id AS user_id,
    u.username,
    u.phone_number,
    COUNT(*) AS failed_attempts,
    COUNT(DISTINCT al.ip_address) AS distinct_ips,
    MIN(al.timestamp) AS first_failure,
    MAX(al.timestamp) AS last_failure
FROM accounts_user u
INNER JOIN audit_logs_auditlog al ON u.id = al.user_id
WHERE al.action IN ('AUTH_FAILED', 'LOGIN_FAILED')
  AND al.timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY u.id, u.username, u.phone_number
HAVING COUNT(*) >= 3;

-- 뷰 사용 예시 쿼리

-- 마스킹된 사용자 정보 조회
-- SELECT * FROM v_user_masked WHERE username = 'testuser';

-- 오늘의 인증 통계
-- SELECT * FROM v_auth_statistics WHERE auth_date = CURDATE();

-- 특정 사용자의 액션 요약
-- SELECT * FROM v_audit_summary WHERE username = 'admin';

-- 현재 활성 트랜잭션 (만료 임박 순)
-- SELECT * FROM v_active_transactions;

-- 사용자의 최근 10건 인증 이력
-- SELECT * FROM v_user_auth_history WHERE user_id = 1 AND row_num <= 10;

-- 서비스 제공자 대시보드
-- SELECT * FROM v_service_dashboard ORDER BY total_transactions DESC;

-- 의심스러운 활동 감지
-- SELECT * FROM v_suspicious_activity ORDER BY failed_attempts DESC;

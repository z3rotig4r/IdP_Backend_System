-- ============================================
-- IdP Backend System - Stored Procedures
-- 과제 요구사항: 프로시저(Stored Procedure) 구현
-- ============================================

DELIMITER //

-- 1. 만료된 트랜잭션 자동 처리 프로시저
-- 용도: 스케줄러(cron)를 통해 주기적으로 호출하여 만료된 PENDING 트랜잭션을 EXPIRED로 변경
CREATE PROCEDURE sp_expire_pending_transactions()
BEGIN
    DECLARE affected_rows INT DEFAULT 0;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SELECT 'Error occurred during transaction expiration' AS error_message;
    END;
    
    START TRANSACTION;
    
    -- PENDING 상태이면서 만료 시간이 지난 트랜잭션 업데이트
    UPDATE auth_transactions_authtransaction
    SET status = 'EXPIRED',
        updated_at = NOW()
    WHERE status = 'PENDING' 
      AND expires_at < NOW();
    
    SET affected_rows = ROW_COUNT();
    
    -- 감사 로그 기록
    INSERT INTO audit_logs_auditlog (user_id, action, details, ip_address, timestamp)
    SELECT 
        user_id,
        'AUTH_EXPIRED',
        CONCAT('Auto-expired transaction: ', transaction_id),
        '0.0.0.0',
        NOW()
    FROM auth_transactions_authtransaction
    WHERE status = 'EXPIRED' 
      AND updated_at >= DATE_SUB(NOW(), INTERVAL 1 SECOND);
    
    COMMIT;
    
    SELECT CONCAT('Successfully expired ', affected_rows, ' transactions') AS result;
END //

-- 2. 서비스 제공자별 통계 생성 프로시저
-- 용도: 특정 서비스의 지정 기간 통계 조회
CREATE PROCEDURE sp_get_service_statistics(
    IN p_service_id INT,
    IN p_days INT
)
BEGIN
    SELECT 
        DATE(created_at) AS date,
        COUNT(*) AS total_requests,
        SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) AS success_count,
        SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failed_count,
        SUM(CASE WHEN status = 'EXPIRED' THEN 1 ELSE 0 END) AS expired_count,
        ROUND(
            SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
            2
        ) AS success_rate,
        ROUND(
            AVG(
                CASE WHEN status = 'COMPLETED'
                THEN TIMESTAMPDIFF(SECOND, created_at, updated_at)
                ELSE NULL END
            ),
            2
        ) AS avg_processing_time
    FROM auth_transactions_authtransaction
    WHERE service_provider_id = p_service_id
      AND created_at >= DATE_SUB(NOW(), INTERVAL p_days DAY)
    GROUP BY DATE(created_at)
    ORDER BY date DESC;
END //

-- 3. 일일 통계 집계 프로시저
-- 용도: 매일 자정에 실행하여 ServiceProviderStatistics 테이블 업데이트
CREATE PROCEDURE sp_aggregate_daily_statistics(
    IN p_target_date DATE
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SELECT 'Error occurred during statistics aggregation' AS error_message;
    END;
    
    START TRANSACTION;
    
    -- 기존 통계가 있으면 삭제 (재집계)
    DELETE FROM services_serviceproviderstatistics
    WHERE date = p_target_date;
    
    -- 새 통계 삽입
    INSERT INTO services_serviceproviderstatistics (
        service_provider_id,
        date,
        total_requests,
        completed_requests,
        failed_requests,
        expired_requests,
        success_rate,
        avg_processing_time,
        created_at,
        updated_at
    )
    SELECT 
        service_provider_id,
        p_target_date,
        COUNT(*) AS total_requests,
        SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_requests,
        SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failed_requests,
        SUM(CASE WHEN status = 'EXPIRED' THEN 1 ELSE 0 END) AS expired_requests,
        ROUND(
            SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
            2
        ) AS success_rate,
        ROUND(
            AVG(
                CASE WHEN status = 'COMPLETED'
                THEN TIMESTAMPDIFF(SECOND, created_at, updated_at)
                ELSE NULL END
            ),
            2
        ) AS avg_processing_time,
        NOW(),
        NOW()
    FROM auth_transactions_authtransaction
    WHERE DATE(created_at) = p_target_date
    GROUP BY service_provider_id;
    
    COMMIT;
    
    SELECT CONCAT('Statistics aggregated for ', p_target_date) AS result;
END //

-- 4. 사용자 인증 이력 조회 프로시저
-- 용도: 특정 사용자의 최근 인증 이력 조회 (페이징)
CREATE PROCEDURE sp_get_user_auth_history(
    IN p_user_id INT,
    IN p_limit INT,
    IN p_offset INT
)
BEGIN
    SELECT 
        at.transaction_id,
        sp.service_name,
        at.status,
        at.created_at,
        at.expires_at,
        at.updated_at,
        at.failure_reason,
        TIMESTAMPDIFF(SECOND, at.created_at, at.updated_at) AS processing_time
    FROM auth_transactions_authtransaction at
    INNER JOIN services_serviceprovider sp ON at.service_provider_id = sp.id
    WHERE at.user_id = p_user_id
    ORDER BY at.created_at DESC
    LIMIT p_limit OFFSET p_offset;
    
    -- 총 개수도 함께 반환
    SELECT COUNT(*) AS total_count
    FROM auth_transactions_authtransaction
    WHERE user_id = p_user_id;
END //

-- 5. 의심스러운 활동 감지 및 계정 잠금 프로시저
-- 용도: 실패 횟수가 임계값을 초과한 사용자 계정 자동 잠금
CREATE PROCEDURE sp_detect_and_lock_suspicious_accounts(
    IN p_failure_threshold INT,
    IN p_time_window_minutes INT
)
BEGIN
    DECLARE locked_count INT DEFAULT 0;
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SELECT 'Error occurred during suspicious account detection' AS error_message;
    END;
    
    START TRANSACTION;
    
    -- 임계값 초과 사용자 계정 비활성화
    UPDATE accounts_user u
    SET is_active = 0
    WHERE id IN (
        SELECT user_id
        FROM audit_logs_auditlog
        WHERE action IN ('AUTH_FAILED', 'LOGIN_FAILED')
          AND timestamp >= DATE_SUB(NOW(), INTERVAL p_time_window_minutes MINUTE)
        GROUP BY user_id
        HAVING COUNT(*) >= p_failure_threshold
    );
    
    SET locked_count = ROW_COUNT();
    
    -- 감사 로그 기록
    INSERT INTO audit_logs_auditlog (user_id, action, details, ip_address, timestamp)
    SELECT 
        u.id,
        'ADMIN_ACTION',
        CONCAT('Account locked due to ', COUNT(al.id), ' failed attempts'),
        '0.0.0.0',
        NOW()
    FROM accounts_user u
    INNER JOIN audit_logs_auditlog al ON u.id = al.user_id
    WHERE u.is_active = 0
      AND al.action IN ('AUTH_FAILED', 'LOGIN_FAILED')
      AND al.timestamp >= DATE_SUB(NOW(), INTERVAL p_time_window_minutes MINUTE)
    GROUP BY u.id;
    
    COMMIT;
    
    SELECT CONCAT('Locked ', locked_count, ' suspicious accounts') AS result;
END //

-- 6. 서비스 제공자 성능 보고서 프로시저
-- 용도: 특정 기간의 서비스별 성능 비교 보고서
CREATE PROCEDURE sp_service_performance_report(
    IN p_start_date DATE,
    IN p_end_date DATE
)
BEGIN
    SELECT 
        sp.service_name,
        COUNT(at.transaction_id) AS total_transactions,
        SUM(CASE WHEN at.status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed,
        SUM(CASE WHEN at.status = 'FAILED' THEN 1 ELSE 0 END) AS failed,
        SUM(CASE WHEN at.status = 'EXPIRED' THEN 1 ELSE 0 END) AS expired,
        ROUND(
            SUM(CASE WHEN at.status = 'COMPLETED' THEN 1 ELSE 0 END) * 100.0 / 
            NULLIF(COUNT(at.transaction_id), 0),
            2
        ) AS success_rate,
        ROUND(
            AVG(
                CASE WHEN at.status = 'COMPLETED'
                THEN TIMESTAMPDIFF(SECOND, at.created_at, at.updated_at)
                ELSE NULL END
            ),
            2
        ) AS avg_processing_time,
        MIN(CASE WHEN at.status = 'COMPLETED' 
            THEN TIMESTAMPDIFF(SECOND, at.created_at, at.updated_at) 
            ELSE NULL END) AS min_processing_time,
        MAX(CASE WHEN at.status = 'COMPLETED'
            THEN TIMESTAMPDIFF(SECOND, at.created_at, at.updated_at)
            ELSE NULL END) AS max_processing_time
    FROM services_serviceprovider sp
    LEFT JOIN auth_transactions_authtransaction at ON sp.id = at.service_provider_id
        AND DATE(at.created_at) BETWEEN p_start_date AND p_end_date
    WHERE sp.is_active = 1
    GROUP BY sp.id, sp.service_name
    ORDER BY total_transactions DESC;
END //

DELIMITER ;

-- ============================================
-- 프로시저 사용 예시
-- ============================================

-- 1. 만료된 트랜잭션 처리 (cron으로 매분 실행 권장)
-- CALL sp_expire_pending_transactions();

-- 2. 특정 서비스의 최근 7일 통계 조회
-- CALL sp_get_service_statistics(1, 7);

-- 3. 어제 날짜의 통계 집계
-- CALL sp_aggregate_daily_statistics(CURDATE() - INTERVAL 1 DAY);

-- 4. 사용자 ID 1의 최근 10건 인증 이력 조회
-- CALL sp_get_user_auth_history(1, 10, 0);

-- 5. 10분 내 5회 이상 실패한 계정 잠금
-- CALL sp_detect_and_lock_suspicious_accounts(5, 10);

-- 6. 최근 30일 서비스 성능 보고서
-- CALL sp_service_performance_report(CURDATE() - INTERVAL 30 DAY, CURDATE());

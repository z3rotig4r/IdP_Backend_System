-- ============================================
-- IdP Backend System - Triggers
-- 과제 요구사항: 트리거(Trigger) 구현
-- ============================================

DELIMITER //

-- 1. 인증 상태 변경 시 자동 감사 로그 기록 트리거
-- 용도: AuthTransaction의 status가 변경될 때마다 자동으로 감사 로그 생성
CREATE TRIGGER trg_auth_status_change
AFTER UPDATE ON auth_transactions_authtransaction
FOR EACH ROW
BEGIN
    IF OLD.status != NEW.status THEN
        INSERT INTO audit_logs_auditlog (
            user_id,
            action,
            details,
            ip_address,
            request_path,
            request_method,
            timestamp
        )
        VALUES (
            NEW.user_id,
            'AUTH_STATUS_CHANGE',
            CONCAT('Status changed from ', OLD.status, ' to ', NEW.status,
                   ' for transaction ', NEW.transaction_id),
            '0.0.0.0',  -- 트리거에서는 실제 IP를 알 수 없으므로 기본값
            '/system/trigger',
            'TRIGGER',
            NOW()
        );
    END IF;
END //

-- 2. 사용자 정보 변경 감사 트리거
-- 용도: User 테이블의 중요 정보가 변경될 때 감사 로그 생성
CREATE TRIGGER trg_user_update_audit
AFTER UPDATE ON accounts_user
FOR EACH ROW
BEGIN
    DECLARE change_details TEXT DEFAULT '';
    
    -- 변경된 필드 추적
    IF OLD.phone_number != NEW.phone_number THEN
        SET change_details = CONCAT(change_details, 'phone_number: ',
                                    OLD.phone_number, ' -> ', NEW.phone_number, '; ');
    END IF;
    
    IF OLD.pin_code != NEW.pin_code THEN
        SET change_details = CONCAT(change_details, 'pin_code changed; ');
    END IF;
    
    IF OLD.is_active != NEW.is_active THEN
        SET change_details = CONCAT(change_details, 'is_active: ',
                                    OLD.is_active, ' -> ', NEW.is_active, '; ');
    END IF;
    
    IF OLD.ci != NEW.ci THEN
        SET change_details = CONCAT(change_details, 'CI changed; ');
    END IF;
    
    IF OLD.di != NEW.di THEN
        SET change_details = CONCAT(change_details, 'DI changed; ');
    END IF;
    
    -- 변경사항이 있으면 감사 로그 기록
    IF change_details != '' THEN
        INSERT INTO audit_logs_auditlog (
            user_id,
            action,
            details,
            ip_address,
            timestamp
        )
        VALUES (
            NEW.id,
            'USER_INFO_UPDATE',
            CONCAT('User information updated: ', change_details),
            '0.0.0.0',
            NOW()
        );
    END IF;
END //

-- 3. 로그인 실패 횟수 추적 및 계정 잠금 트리거
-- 용도: 감사 로그에 로그인 실패가 기록될 때, 최근 실패 횟수를 확인하고 임계값 초과 시 계정 잠금
CREATE TRIGGER trg_login_failure_detection
AFTER INSERT ON audit_logs_auditlog
FOR EACH ROW
BEGIN
    DECLARE fail_count INT;
    DECLARE lock_threshold INT DEFAULT 5;
    DECLARE time_window_minutes INT DEFAULT 10;
    
    -- LOGIN_FAILED 또는 AUTH_FAILED 액션에 대해서만 동작
    IF NEW.action IN ('LOGIN_FAILED', 'AUTH_FAILED') AND NEW.user_id IS NOT NULL THEN
        -- 최근 10분 내 실패 횟수 확인
        SELECT COUNT(*) INTO fail_count
        FROM audit_logs_auditlog
        WHERE user_id = NEW.user_id
          AND action IN ('LOGIN_FAILED', 'AUTH_FAILED')
          AND timestamp >= DATE_SUB(NOW(), INTERVAL time_window_minutes MINUTE);
        
        -- 임계값 초과 시 계정 비활성화
        IF fail_count >= lock_threshold THEN
            UPDATE accounts_user
            SET is_active = 0
            WHERE id = NEW.user_id;
            
            -- 계정 잠금 감사 로그 추가
            INSERT INTO audit_logs_auditlog (
                user_id,
                action,
                details,
                ip_address,
                timestamp
            )
            VALUES (
                NEW.user_id,
                'ADMIN_ACTION',
                CONCAT('Account automatically locked after ', fail_count, ' failed attempts'),
                NEW.ip_address,
                NOW()
            );
        END IF;
    END IF;
END //

-- 4. 서비스 제공자 생성 시 기본 암호화 키 생성 트리거
-- 용도: ServiceProvider가 생성될 때 자동으로 기본 암호화 키 레코드 생성
CREATE TRIGGER trg_create_default_encryption_key
AFTER INSERT ON services_serviceprovider
FOR EACH ROW
BEGIN
    -- 기본 암호화 키 생성 (실제 키 값은 애플리케이션에서 설정)
    INSERT INTO services_encryptionkey (
        service_provider_id,
        key_name,
        key_value,
        algorithm,
        is_active,
        created_at
    )
    VALUES (
        NEW.id,
        'default_key',
        'PLACEHOLDER_TO_BE_SET_BY_APPLICATION',
        'AES-256-GCM',
        1,
        NOW()
    );
END //

-- 5. 트랜잭션 생성 시 통지 로그 자동 생성 트리거
-- 용도: AuthTransaction이 생성될 때 자동으로 NotificationLog 생성
CREATE TRIGGER trg_create_notification_on_auth_request
AFTER INSERT ON auth_transactions_authtransaction
FOR EACH ROW
BEGIN
    DECLARE service_name VARCHAR(200);
    
    -- 서비스 이름 조회
    SELECT s.service_name INTO service_name
    FROM services_serviceprovider s
    WHERE s.id = NEW.service_provider_id;
    
    -- 통지 로그 생성
    INSERT INTO auth_transactions_notificationlog (
        user_id,
        transaction_id,
        notification_type,
        message,
        status,
        created_at
    )
    VALUES (
        NEW.user_id,
        NEW.transaction_id,
        'AUTH_REQUEST',
        CONCAT('Authentication requested by ', service_name, 
               '. Please confirm on your device. Transaction ID: ', NEW.transaction_id),
        'PENDING',
        NOW()
    );
END //

-- 6. 만료 시간 검증 트리거
-- 용도: AuthTransaction 삽입/수정 시 expires_at이 created_at보다 미래인지 확인
CREATE TRIGGER trg_validate_expiry_before_insert
BEFORE INSERT ON auth_transactions_authtransaction
FOR EACH ROW
BEGIN
    IF NEW.expires_at <= NEW.created_at THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Expiry time must be after creation time';
    END IF;
END //

CREATE TRIGGER trg_validate_expiry_before_update
BEFORE UPDATE ON auth_transactions_authtransaction
FOR EACH ROW
BEGIN
    IF NEW.expires_at <= NEW.created_at THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Expiry time must be after creation time';
    END IF;
END //

-- 7. 중복 인증 코드 방지 트리거
-- 용도: auth_code가 이미 사용 중인지 확인 (UNIQUE 제약조건 보완)
CREATE TRIGGER trg_prevent_duplicate_auth_code
BEFORE UPDATE ON auth_transactions_authtransaction
FOR EACH ROW
BEGIN
    DECLARE existing_count INT;
    
    -- auth_code가 변경되고, 새 값이 NULL이 아닌 경우에만 검사
    IF NEW.auth_code IS NOT NULL 
       AND (OLD.auth_code IS NULL OR OLD.auth_code != NEW.auth_code) THEN
        
        SELECT COUNT(*) INTO existing_count
        FROM auth_transactions_authtransaction
        WHERE auth_code = NEW.auth_code
          AND transaction_id != NEW.transaction_id;
        
        IF existing_count > 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Duplicate auth_code detected';
        END IF;
    END IF;
END //

-- 8. 서비스 제공자 비활성화 시 진행 중인 트랜잭션 만료 처리 트리거
-- 용도: ServiceProvider가 비활성화되면 해당 서비스의 PENDING 트랜잭션을 EXPIRED로 변경
CREATE TRIGGER trg_expire_transactions_on_service_deactivation
AFTER UPDATE ON services_serviceprovider
FOR EACH ROW
BEGIN
    IF OLD.is_active = 1 AND NEW.is_active = 0 THEN
        -- 해당 서비스의 PENDING 트랜잭션을 EXPIRED로 변경
        UPDATE auth_transactions_authtransaction
        SET status = 'EXPIRED',
            failure_reason = 'Service provider deactivated',
            updated_at = NOW()
        WHERE service_provider_id = NEW.id
          AND status = 'PENDING';
        
        -- 감사 로그 기록
        INSERT INTO audit_logs_auditlog (
            user_id,
            action,
            details,
            ip_address,
            timestamp
        )
        VALUES (
            NULL,
            'ADMIN_ACTION',
            CONCAT('Service provider ', NEW.service_name, 
                   ' deactivated. Pending transactions expired.'),
            '0.0.0.0',
            NOW()
        );
    END IF;
END //

DELIMITER ;

-- ============================================
-- 트리거 테스트 쿼리
-- ============================================

-- 1. 트리거 목록 확인
-- SHOW TRIGGERS;

-- 2. 특정 트리거 상세 정보
-- SHOW CREATE TRIGGER trg_auth_status_change;

-- 3. 트리거 삭제 (필요시)
-- DROP TRIGGER IF EXISTS trg_auth_status_change;

-- ============================================
-- 트리거 동작 테스트 시나리오
-- ============================================

-- 시나리오 1: 인증 상태 변경 감사
-- 1) PENDING 트랜잭션을 COMPLETED로 변경
-- UPDATE auth_transactions_authtransaction 
-- SET status = 'COMPLETED' 
-- WHERE transaction_id = 'some-uuid';
-- 
-- 2) 감사 로그 확인
-- SELECT * FROM audit_logs_auditlog 
-- WHERE action = 'AUTH_STATUS_CHANGE' 
-- ORDER BY timestamp DESC LIMIT 1;

-- 시나리오 2: 사용자 정보 변경 감사
-- 1) 사용자 전화번호 변경
-- UPDATE accounts_user 
-- SET phone_number = '010-9999-9999' 
-- WHERE id = 1;
-- 
-- 2) 감사 로그 확인
-- SELECT * FROM audit_logs_auditlog 
-- WHERE action = 'USER_INFO_UPDATE' AND user_id = 1 
-- ORDER BY timestamp DESC LIMIT 1;

-- 시나리오 3: 로그인 실패 자동 잠금
-- 1) 로그인 실패 로그 5회 생성
-- INSERT INTO audit_logs_auditlog (user_id, action, details, ip_address, timestamp)
-- VALUES (1, 'LOGIN_FAILED', 'Invalid password', '192.168.1.1', NOW());
-- (5회 반복)
-- 
-- 2) 사용자 계정 상태 확인
-- SELECT id, username, is_active FROM accounts_user WHERE id = 1;

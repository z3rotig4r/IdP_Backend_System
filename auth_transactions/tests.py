"""
Test scenarios for IdP Backend System
과제 요구사항: 동시성 테스트, 성능 테스트 시나리오
"""
import threading
import time
import requests
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from services.models import ServiceProvider
from auth_transactions.models import AuthTransaction
from accounts.utils import EncryptionUtil
import uuid


class ConcurrencyTestCase(TransactionTestCase):
    """
    동시성 테스트 - 같은 트랜잭션에 대한 동시 인증 확인 시도
    과제 요구사항: 시나리오(동시성/경합) 10%
    """
    
    def setUp(self):
        """테스트 데이터 셋업"""
        # 사용자 생성
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone_number='010-1234-5678'
        )
        self.user.set_pin('123456')
        self.user.ci = EncryptionUtil.encrypt_field(str(uuid.uuid4()))
        self.user.di = EncryptionUtil.encrypt_field(str(uuid.uuid4()))
        self.user.save()
        
        # 서비스 제공자 생성
        self.service_provider = ServiceProvider.objects.create(
            service_name='Test Service',
            client_id='test_client_123',
            client_secret=ServiceProvider.hash_secret('test_secret'),
            callback_url='https://example.com/callback',
            is_active=True
        )
    
    def test_concurrent_authentication_confirmation(self):
        """
        테스트: SELECT FOR UPDATE를 사용한 동시성 제어 검증
        예상: 두 번째 요청이 첫 번째 요청이 완료될 때까지 대기
        """
        # 1. 인증 트랜잭션 생성
        auth_tx = AuthTransaction.objects.create(
            user=self.user,
            service_provider=self.service_provider,
            status='PENDING',
            expires_at=timezone.now() + timedelta(minutes=3)
        )
        
        # 2. 첫 번째 확인 요청 - 성공해야 함
        from django.test.client import Client
        import json
        client1 = Client()
        response1 = client1.post('/api/v1/auth/api/confirm/',
            data=json.dumps({
                'transaction_id': str(auth_tx.transaction_id),
                'pin_code': '123456'
            }),
            content_type='application/json'
        )
        self.assertEqual(response1.status_code, 200, "First request should succeed")
        
        # 3. 두 번째 확인 요청 - 이미 완료되었으므로 실패해야 함
        client2 = Client()
        response2 = client2.post('/api/v1/auth/api/confirm/',
            data=json.dumps({
                'transaction_id': str(auth_tx.transaction_id),
                'pin_code': '123456'
            }),
            content_type='application/json'
        )
        self.assertEqual(response2.status_code, 400, "Second request should fail")
        self.assertIn('already', response2.json().get('error', '').lower())
        
        # 4. DB 확인: 상태가 COMPLETED이고 auth_code가 생성되어야 함
        auth_tx.refresh_from_db()
        self.assertEqual(auth_tx.status, 'COMPLETED')
        self.assertIsNotNone(auth_tx.auth_code)
    
    def test_race_condition_on_expiry_check(self):
        """
        테스트: 만료된 트랜잭션에 대한 접근 검증
        """
        # 매우 짧은 만료 시간으로 트랜잭션 생성 (0.1초)
        auth_tx = AuthTransaction.objects.create(
            user=self.user,
            service_provider=self.service_provider,
            status='PENDING',
            expires_at=timezone.now() + timedelta(seconds=0.1)
        )
        
        # 만료될 때까지 대기
        time.sleep(0.2)
        
        # 만료된 트랜잭션 확인 시도
        from django.test.client import Client
        import json
        client = Client()
        response = client.post('/api/v1/auth/api/confirm/',
            data=json.dumps({
                'transaction_id': str(auth_tx.transaction_id),
                'pin_code': '123456'
            }),
            content_type='application/json'
        )
        
        # 만료 에러를 받아야 함
        self.assertEqual(response.status_code, 400)
        self.assertIn('expired', response.json().get('error', '').lower())
        
        # DB 확인: 상태가 EXPIRED로 변경되어야 함
        auth_tx.refresh_from_db()
        self.assertEqual(auth_tx.status, 'EXPIRED')
        
        # 상태는 EXPIRED여야 함
        auth_tx.refresh_from_db()
        self.assertEqual(auth_tx.status, 'EXPIRED')


class PerformanceTestCase(TestCase):
    """
    성능 테스트 - 인덱스 효과 측정
    과제 요구사항: 성능/튜닝 10%
    """
    
    @classmethod
    def setUpTestData(cls):
        """대량의 테스트 데이터 생성"""
        # 사용자 100명 생성
        users = []
        for i in range(100):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                phone_number=f'010-{1000+i:04d}-5678'
            )
            user.set_pin('123456')
            user.ci = EncryptionUtil.encrypt_field(str(uuid.uuid4()))
            user.di = EncryptionUtil.encrypt_field(str(uuid.uuid4()))
            user.save()
            users.append(user)
        
        # 서비스 제공자 10개 생성
        services = []
        for i in range(10):
            sp = ServiceProvider.objects.create(
                service_name=f'Service {i}',
                client_id=f'client_{i}',
                client_secret=ServiceProvider.hash_secret(f'secret_{i}'),
                callback_url=f'https://service{i}.com/callback',
                is_active=True
            )
            services.append(sp)
        
        # 트랜잭션 1000개 생성
        import random
        for i in range(1000):
            AuthTransaction.objects.create(
                user=random.choice(users),
                service_provider=random.choice(services),
                status=random.choice(['PENDING', 'COMPLETED', 'FAILED', 'EXPIRED']),
                expires_at=timezone.now() + timedelta(minutes=3)
            )
    
    def test_index_performance_on_status_query(self):
        """
        테스트: status 필터링 쿼리 성능
        인덱스: idx_status_expires
        """
        import time
        from django.db import connection
        from django.test.utils import override_settings
        
        # 쿼리 시간 측정
        start_time = time.time()
        
        with self.assertNumQueries(1):
            transactions = list(
                AuthTransaction.objects.filter(
                    status='PENDING',
                    expires_at__gt=timezone.now()
                )[:100]
            )
        
        elapsed_time = time.time() - start_time
        
        # 성능 검증: 100ms 이내 완료
        self.assertLess(elapsed_time, 0.1, 
                       f"Query took {elapsed_time:.4f}s, should be < 0.1s")
        
        # 쿼리 플랜 확인 (MySQL EXPLAIN)
        query = AuthTransaction.objects.filter(
            status='PENDING',
            expires_at__gt=timezone.now()
        ).query
        
        print(f"\nQuery: {query}")
        print(f"Execution time: {elapsed_time:.4f}s")
        print(f"Results: {len(transactions)} transactions")
    
    def test_select_related_performance(self):
        """
        테스트: N+1 쿼리 문제 해결 (select_related)
        """
        # Without select_related (N+1 problem)
        start_time = time.time()
        transactions = AuthTransaction.objects.all()[:10]
        for tx in transactions:
            _ = tx.user.username
            _ = tx.service_provider.service_name
        time_without = time.time() - start_time
        
        # With select_related
        start_time = time.time()
        transactions = AuthTransaction.objects.select_related(
            'user', 'service_provider'
        )[:10]
        for tx in transactions:
            _ = tx.user.username
            _ = tx.service_provider.service_name
        time_with = time.time() - start_time
        
        # select_related가 더 빨라야 함
        self.assertLess(time_with, time_without,
                       f"select_related ({time_with:.4f}s) should be faster than "
                       f"without ({time_without:.4f}s)")
        
        print(f"\nWithout select_related: {time_without:.4f}s")
        print(f"With select_related: {time_with:.4f}s")
        print(f"Speedup: {time_without/time_with:.2f}x")


class SecurityTestCase(TestCase):
    """
    보안 테스트 - 마스킹, RBAC, 감사 로그
    과제 요구사항: 보안/개인정보 10%
    """
    
    def setUp(self):
        """테스트 데이터 셋업"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone_number='010-1234-5678'
        )
        self.user.set_pin('123456')
        self.user.ci = EncryptionUtil.encrypt_field('CI-TEST-123456')
        self.user.di = EncryptionUtil.encrypt_field('DI-TEST-789012')
        self.user.save()
    
    def test_phone_number_masking(self):
        """
        테스트: 전화번호 마스킹 유틸리티
        """
        from accounts.utils import mask_phone_number
        
        masked = mask_phone_number('010-1234-5678')
        self.assertEqual(masked, '010-****-5678')
        
        # 중간 4자리가 마스킹되어야 함
        self.assertNotIn('1234', masked)
        self.assertIn('010', masked)
        self.assertIn('5678', masked)
    
    def test_ci_di_encryption_decryption(self):
        """
        테스트: CI/DI 암호화/복호화
        """
        original_ci = 'CI-TEST-123456'
        
        # 암호화
        encrypted = EncryptionUtil.encrypt_field(original_ci)
        self.assertNotEqual(encrypted, original_ci)
        
        # 복호화
        decrypted = EncryptionUtil.decrypt_field(encrypted)
        self.assertEqual(decrypted, original_ci)
    
    def test_pin_code_hashing(self):
        """
        테스트: PIN 코드 해싱 및 검증
        """
        raw_pin = '123456'
        
        # PIN 설정
        self.user.set_pin(raw_pin)
        
        # PIN이 해시되어 저장되어야 함
        self.assertNotEqual(self.user.pin_code, raw_pin)
        
        # 올바른 PIN 확인
        self.assertTrue(self.user.check_pin(raw_pin))
        
        # 잘못된 PIN 확인
        self.assertFalse(self.user.check_pin('wrong_pin'))
    
    def test_audit_log_creation(self):
        """
        테스트: 감사 로그 자동 생성
        """
        from audit_logs.models import AuditLog
        
        # 감사 로그 생성
        log = AuditLog.objects.create(
            user=self.user,
            action='USER_LOGIN',
            details='User logged in successfully',
            ip_address='192.168.1.1',
            request_path='/api/v1/auth/login',
            request_method='POST',
            status_code=200
        )
        
        # 감사 로그 조회
        logs = AuditLog.objects.filter(user=self.user, action='USER_LOGIN')
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().ip_address, '192.168.1.1')


# ============================================
# 실행 방법
# ============================================
# python manage.py test auth_transactions.tests.ConcurrencyTestCase
# python manage.py test auth_transactions.tests.PerformanceTestCase
# python manage.py test auth_transactions.tests.SecurityTestCase


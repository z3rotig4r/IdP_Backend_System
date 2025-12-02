"""
Core API views for IdP authentication flow
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
from accounts.models import User
from services.models import ServiceProvider
from auth_transactions.models import AuthTransaction, NotificationLog
from audit_logs.models import AuditLog
from accounts.utils import EncryptionUtil
import json


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_request(request):
    """
    API Endpoint: POST /api/v1/auth/request/
    
    Request authentication from IdP
    Called by Service Provider
    
    Request Body:
    {
        "user_phone_number": "010-1234-5678"
    }
    
    Headers:
    - X-Client-ID: Service Provider client ID
    - X-Client-Secret: Service Provider client secret
    """
    client_id = request.headers.get('X-Client-ID')
    client_secret = request.headers.get('X-Client-Secret')
    user_phone_number = request.data.get('user_phone_number')
    
    # Validate input
    if not all([client_id, client_secret, user_phone_number]):
        return Response(
            {'error': 'Missing required fields'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        with transaction.atomic():
            # 1. Authenticate Service Provider
            try:
                service_provider = ServiceProvider.objects.get(
                    client_id=client_id,
                    is_active=True
                )
            except ServiceProvider.DoesNotExist:
                AuditLog.objects.create(
                    action='AUTH_REQUEST',
                    details=f'Invalid client_id: {client_id}',
                    ip_address=get_client_ip(request),
                    request_path=request.path,
                    request_method=request.method,
                    status_code=401
                )
                return Response(
                    {'error': 'Invalid client credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            if not service_provider.check_secret(client_secret):
                AuditLog.objects.create(
                    action='AUTH_REQUEST',
                    details=f'Invalid client_secret for {client_id}',
                    ip_address=get_client_ip(request),
                    request_path=request.path,
                    request_method=request.method,
                    status_code=401
                )
                return Response(
                    {'error': 'Invalid client credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # 2. Find User
            try:
                user = User.objects.get(phone_number=user_phone_number, is_active=True)
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 3. Create AuthTransaction
            expires_at = timezone.now() + timedelta(minutes=10)
            auth_tx = AuthTransaction.objects.create(
                user=user,
                service_provider=service_provider,
                status='PENDING',
                expires_at=expires_at
            )
            
            # 4. Create Notification (simulated)
            NotificationLog.objects.create(
                user=user,
                transaction=auth_tx,
                notification_type='AUTH_REQUEST',
                message=f'Authentication requested by {service_provider.service_name}',
                status='SENT',
                sent_at=timezone.now()
            )
            
            # 5. Audit Log
            AuditLog.objects.create(
                user=user,
                action='AUTH_REQUEST',
                details=f'Auth request from {service_provider.service_name}',
                ip_address=get_client_ip(request),
                request_path=request.path,
                request_method=request.method,
                status_code=200
            )
            
            return Response({
                'transaction_id': str(auth_tx.transaction_id),
                'expires_at': auth_tx.expires_at.isoformat(),
                'message': 'Authentication request created. User will be notified.'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_confirm(request):
    """
    API Endpoint: POST /api/v1/auth/confirm/
    
    User confirms authentication with PIN
    
    Request Body:
    {
        "transaction_id": "uuid-here",
        "pin_code": "123456"
    }
    """
    transaction_id = request.data.get('transaction_id')
    pin_code = request.data.get('pin_code')
    
    if not all([transaction_id, pin_code]):
        return Response(
            {'error': 'Missing required fields'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        with transaction.atomic():
            # Lock the transaction row for update
            try:
                auth_tx = AuthTransaction.objects.select_for_update().get(
                    transaction_id=transaction_id
                )
            except AuthTransaction.DoesNotExist:
                return Response(
                    {'error': 'Transaction not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if already processed
            if auth_tx.status != 'PENDING':
                return Response(
                    {'error': f'Transaction already {auth_tx.status.lower()}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check expiration
            if auth_tx.is_expired():
                auth_tx.status = 'EXPIRED'
                auth_tx.save()
                AuditLog.objects.create(
                    user=auth_tx.user,
                    action='AUTH_EXPIRED',
                    details=f'Transaction {transaction_id} expired',
                    ip_address=get_client_ip(request),
                    request_path=request.path,
                    request_method=request.method
                )
                return Response(
                    {'error': 'Transaction expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify PIN
            if not auth_tx.user.check_pin(pin_code):
                auth_tx.status = 'FAILED'
                auth_tx.failure_reason = 'Invalid PIN'
                auth_tx.save()
                
                AuditLog.objects.create(
                    user=auth_tx.user,
                    action='AUTH_FAILED',
                    details=f'Invalid PIN for transaction {transaction_id}',
                    ip_address=get_client_ip(request),
                    request_path=request.path,
                    request_method=request.method
                )
                
                return Response(
                    {'error': 'Invalid PIN'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Success - generate auth_code
            auth_tx.status = 'COMPLETED'
            auth_tx.auth_code = AuthTransaction.generate_auth_code()
            auth_tx.save()
            
            # Audit log
            AuditLog.objects.create(
                user=auth_tx.user,
                action='AUTH_COMPLETED',
                details=f'Transaction {transaction_id} completed successfully',
                ip_address=get_client_ip(request),
                request_path=request.path,
                request_method=request.method,
                status_code=200
            )
            
            # TODO: Trigger callback to service provider (async task)
            # For now, service provider needs to poll or we can implement webhook
            
            return Response({
                'status': 'COMPLETED',
                'auth_code': auth_tx.auth_code,
                'message': 'Authentication successful'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def auth_status(request, transaction_id):
    """
    API Endpoint: GET /api/v1/auth/status/<transaction_id>/
    
    Check authentication status
    Called by Service Provider to poll status
    """
    try:
        auth_tx = AuthTransaction.objects.select_related(
            'user', 'service_provider'
        ).get(transaction_id=transaction_id)
        
        response_data = {
            'transaction_id': str(auth_tx.transaction_id),
            'status': auth_tx.status,
            'created_at': auth_tx.created_at.isoformat(),
            'expires_at': auth_tx.expires_at.isoformat(),
        }
        
        if auth_tx.status == 'COMPLETED':
            response_data['auth_code'] = auth_tx.auth_code
            # Include encrypted CI/DI
            try:
                ci_decrypted = EncryptionUtil.decrypt_field(auth_tx.user.ci) if auth_tx.user.ci else None
                di_decrypted = EncryptionUtil.decrypt_field(auth_tx.user.di) if auth_tx.user.di else None
            except Exception:
                # If decryption fails, use masked values
                ci_decrypted = "CI_" + "*" * 80
                di_decrypted = "DI_" + "*" * 80
            
            # Re-encrypt for service provider
            # In production, use service provider's public key
            response_data['ci'] = ci_decrypted  # Should be encrypted
            response_data['di'] = di_decrypted  # Should be encrypted
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except AuthTransaction.DoesNotExist:
        return Response(
            {'error': 'Transaction not found'},
            status=status.HTTP_404_NOT_FOUND
        )

"""
Script to create a test service provider with known credentials
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'idp_backend.settings')
django.setup()

from services.models import ServiceProvider, EncryptionKey
from cryptography.fernet import Fernet

def create_test_sp():
    # Check if test SP exists
    test_sp = ServiceProvider.objects.filter(service_name='API Test Service').first()
    
    if test_sp:
        print(f"Test Service Provider already exists:")
        print(f"  Service: {test_sp.service_name}")
        print(f"  Client ID: {test_sp.client_id}")
        print(f"  Status: {'Active' if test_sp.is_active else 'Inactive'}")
        return
    
    # Generate credentials with known secret
    client_id = ServiceProvider.generate_client_id()
    client_secret_raw = "test_secret_123456789"  # Known test secret
    client_secret_hashed = ServiceProvider.hash_secret(client_secret_raw)
    
    # Create SP
    sp = ServiceProvider.objects.create(
        service_name='API Test Service',
        client_id=client_id,
        client_secret=client_secret_hashed,
        callback_url='https://test.example.com/auth/callback',
        is_active=True
    )
    
    # Create encryption key
    key = Fernet.generate_key()
    EncryptionKey.objects.create(
        service_provider=sp,
        key_name='primary',
        key_value=key.decode(),
        algorithm='AES-256-GCM',
        is_active=True
    )
    
    print("=" * 60)
    print("Test Service Provider Created Successfully!")
    print("=" * 60)
    print(f"Service Name: {sp.service_name}")
    print(f"Client ID: {sp.client_id}")
    print(f"Client Secret (RAW): {client_secret_raw}")
    print(f"Callback URL: {sp.callback_url}")
    print("=" * 60)
    print("\nUse these credentials for API testing:")
    print(f'  -H "X-Client-ID: {sp.client_id}"')
    print(f'  -H "X-Client-Secret: {client_secret_raw}"')
    print("=" * 60)

if __name__ == '__main__':
    create_test_sp()

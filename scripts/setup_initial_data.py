"""
Initial data setup script for IdP Backend System
Creates test users, service providers, and roles
"""
import os
import django
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'idp_backend.settings')
django.setup()

from accounts.models import User, UserRole, UserRoleAssignment
from services.models import ServiceProvider, EncryptionKey
from django.utils import timezone
import hashlib


def create_roles():
    """Create user roles"""
    print("Creating user roles...")
    
    roles_data = [
        {
            'role_name': 'SUPER_ADMIN',
            'description': 'Super Administrator - Full system access',
            'permissions': {
                'manage_users': True,
                'manage_services': True,
                'view_audit_logs': True,
                'manage_roles': True
            }
        },
        {
            'role_name': 'SERVICE_ADMIN',
            'description': 'Service Administrator - Manages service providers',
            'permissions': {
                'manage_services': True,
                'view_statistics': True
            }
        },
        {
            'role_name': 'AUDITOR',
            'description': 'Auditor - Read-only access to logs and statistics',
            'permissions': {
                'view_audit_logs': True,
                'view_statistics': True
            }
        },
        {
            'role_name': 'USER',
            'description': 'Regular User',
            'permissions': {
                'authenticate': True,
                'view_own_transactions': True
            }
        }
    ]
    
    for role_data in roles_data:
        role, created = UserRole.objects.get_or_create(
            role_name=role_data['role_name'],
            defaults={
                'description': role_data['description'],
                'permissions': role_data['permissions']
            }
        )
        if created:
            print(f"✓ Created role: {role.role_name}")
        else:
            print(f"- Role already exists: {role.role_name}")


def create_users():
    """Create test users"""
    print("\nCreating test users...")
    
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@simpleid.com',
            'phone_number': '010-1234-5678',
            'password': 'admin123!@#',
            'pin': '123456',
            'is_staff': True,
            'is_superuser': True,
            'role': 'SUPER_ADMIN'
        },
        {
            'username': 'testuser1',
            'email': 'user1@example.com',
            'phone_number': '010-2345-6789',
            'password': 'user123!@#',
            'pin': '234567',
            'is_staff': False,
            'is_superuser': False,
            'role': 'USER'
        },
        {
            'username': 'testuser2',
            'email': 'user2@example.com',
            'phone_number': '010-3456-7890',
            'password': 'user123!@#',
            'pin': '345678',
            'is_staff': False,
            'is_superuser': False,
            'role': 'USER'
        },
        {
            'username': 'auditor',
            'email': 'auditor@simpleid.com',
            'phone_number': '010-4567-8901',
            'password': 'auditor123!@#',
            'pin': '456789',
            'is_staff': True,
            'is_superuser': False,
            'role': 'AUDITOR'
        }
    ]
    
    for user_data in users_data:
        # Check if user exists
        if User.objects.filter(username=user_data['username']).exists():
            print(f"- User already exists: {user_data['username']}")
            continue
        
        # Generate CI/DI
        unique_string = f"{user_data['username']}_{user_data['phone_number']}_{timezone.now().timestamp()}"
        ci = hashlib.sha256(unique_string.encode()).hexdigest()
        di = hashlib.sha256(f"{ci}_{user_data['email']}".encode()).hexdigest()
        
        # Create user
        user = User.objects.create(
            username=user_data['username'],
            email=user_data['email'],
            phone_number=user_data['phone_number'],
            ci=ci,
            di=di,
            is_staff=user_data['is_staff'],
            is_superuser=user_data['is_superuser']
        )
        
        # Set password
        user.set_password(user_data['password'])
        
        # Set PIN
        user.set_pin(user_data['pin'])
        
        user.save()
        
        # Assign role
        role = UserRole.objects.get(role_name=user_data['role'])
        UserRoleAssignment.objects.create(user=user, role=role)
        
        print(f"✓ Created user: {user.username} (role: {user_data['role']})")


def create_service_providers():
    """Create test service providers"""
    print("\nCreating service providers...")
    
    sps_data = [
        {
            'service_name': 'Test Shopping Mall',
            'callback_url': 'https://shop.example.com/auth/callback',
        },
        {
            'service_name': 'Test Game Platform',
            'callback_url': 'https://game.example.com/auth/callback',
        },
        {
            'service_name': 'Test Finance App',
            'callback_url': 'https://finance.example.com/auth/callback',
        }
    ]
    
    for sp_data in sps_data:
        # Check if SP exists
        if ServiceProvider.objects.filter(service_name=sp_data['service_name']).exists():
            print(f"- Service provider already exists: {sp_data['service_name']}")
            continue
        
        # Generate client credentials
        client_id = ServiceProvider.generate_client_id()
        client_secret_raw = ServiceProvider.generate_client_secret()
        client_secret_hashed = ServiceProvider.hash_secret(client_secret_raw)
        
        # Create SP
        sp = ServiceProvider.objects.create(
            service_name=sp_data['service_name'],
            client_id=client_id,
            client_secret=client_secret_hashed,
            callback_url=sp_data['callback_url'],
            is_active=True
        )
        
        # Create encryption key for SP
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        
        EncryptionKey.objects.create(
            service_provider=sp,
            key_name='primary',
            key_value=key.decode(),
            algorithm='AES-256-GCM',
            is_active=True
        )
        
        print(f"✓ Created service provider: {sp.service_name}")
        print(f"  Client ID: {sp.client_id}")
        print(f"  Client Secret (save this!): {client_secret_raw}")


def main():
    print("=" * 60)
    print("IdP Backend System - Initial Data Setup")
    print("=" * 60)
    
    try:
        create_roles()
        create_users()
        create_service_providers()
        
        print("\n" + "=" * 60)
        print("✓ Initial data setup completed successfully!")
        print("=" * 60)
        
        print("\n📝 Login Credentials:")
        print("-" * 60)
        print("Admin:")
        print("  Username: admin")
        print("  Password: admin123!@#")
        print("  PIN: 123456")
        print()
        print("Test User 1:")
        print("  Username: testuser1")
        print("  Password: user123!@#")
        print("  PIN: 234567")
        print("  Phone: 010-2345-6789")
        print()
        print("Test User 2:")
        print("  Username: testuser2")
        print("  Password: user123!@#")
        print("  PIN: 345678")
        print("  Phone: 010-3456-7890")
        print()
        print("Auditor:")
        print("  Username: auditor")
        print("  Password: auditor123!@#")
        print("  PIN: 456789")
        print("-" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during setup: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

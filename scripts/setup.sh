#!/bin/bash
# IdP Backend System - Quick Start Script

echo "🚀 IdP Backend System - Quick Start"
echo "===================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install django djangorestframework cryptography bcrypt

# Make migrations
echo "🔄 Creating migrations..."
python manage.py makemigrations accounts
python manage.py makemigrations services
python manage.py makemigrations auth_transactions
python manage.py makemigrations audit_logs

# Apply migrations
echo "💾 Applying migrations..."
python manage.py migrate

# Create superuser (interactive)
echo ""
echo "👤 Creating superuser account..."
echo "   (You'll be prompted for username, email, and password)"
python manage.py createsuperuser

# Create initial data
echo ""
echo "📝 Creating initial data..."
python manage.py shell << EOF
from accounts.models import User, UserRole
from services.models import ServiceProvider
from accounts.utils import EncryptionUtil
import uuid

# Create user roles
print("Creating user roles...")
roles_data = [
    ('SUPER_ADMIN', 'Super Administrator', {'all': True}),
    ('SERVICE_ADMIN', 'Service Administrator', {'services': 'read_write', 'stats': 'read'}),
    ('AUDITOR', 'Auditor', {'audit_logs': 'read', 'users': 'read'}),
    ('USER', 'User', {'self': 'read_write'}),
]

for role_name, description, permissions in roles_data:
    role, created = UserRole.objects.get_or_create(
        role_name=role_name,
        defaults={'description': description, 'permissions': permissions}
    )
    if created:
        print(f"  ✓ Created role: {role_name}")

# Create test user
print("Creating test user...")
test_user, created = User.objects.get_or_create(
    username='testuser',
    defaults={
        'email': 'testuser@example.com',
        'phone_number': '010-1234-5678',
        'is_active': True
    }
)
if created:
    test_user.set_password('testpass123')
    test_user.set_pin('123456')
    test_user.ci = EncryptionUtil.encrypt_field(str(uuid.uuid4()))
    test_user.di = EncryptionUtil.encrypt_field(str(uuid.uuid4()))
    test_user.save()
    print("  ✓ Created test user: testuser (password: testpass123, PIN: 123456)")

# Create test service provider
print("Creating test service provider...")
test_sp, created = ServiceProvider.objects.get_or_create(
    client_id='test_client_123',
    defaults={
        'service_name': 'Test Shopping Mall',
        'client_secret': ServiceProvider.hash_secret('test_secret_456'),
        'callback_url': 'https://test-shop.example.com/callback',
        'is_active': True
    }
)
if created:
    print("  ✓ Created service provider: Test Shopping Mall")
    print("    - client_id: test_client_123")
    print("    - client_secret: test_secret_456")

print("")
print("✅ Initial data setup complete!")
EOF

echo ""
echo "================================================"
echo "✅ Setup complete!"
echo ""
echo "📌 Quick Access Info:"
echo "   Admin URL: http://localhost:8000/admin/"
echo "   API Base URL: http://localhost:8000/api/v1/auth/"
echo ""
echo "🔑 Test Credentials:"
echo "   User: testuser"
echo "   Password: testpass123"
echo "   PIN: 123456"
echo ""
echo "🏢 Test Service Provider:"
echo "   client_id: test_client_123"
echo "   client_secret: test_secret_456"
echo ""
echo "🚀 To start the server:"
echo "   python manage.py runserver"
echo ""
echo "📚 For more information, see:"
echo "   - README.md (과제 평가 기준 매핑)"
echo "   - docs/PROJECT_SUMMARY.md (프로젝트 요약)"
echo "   - docs/sql_*.sql (SQL 스크립트)"
echo ""
echo "================================================"

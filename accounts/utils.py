"""
Utility functions for cryptography operations
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings
import os
import base64


class EncryptionUtil:
    """Utility class for encryption/decryption operations"""
    
    @staticmethod
    def generate_key():
        """Generate a new encryption key"""
        return Fernet.generate_key()
    
    @staticmethod
    def encrypt_field(plaintext, key=None):
        """
        Encrypt a field value (CI/DI)
        For demo purposes, we use Fernet (symmetric encryption)
        In production, use proper key management service
        """
        if key is None:
            # Use a default key for demo (should be in environment variable)
            key = settings.SECRET_KEY.encode()[:32]
            key = base64.urlsafe_b64encode(key)
        
        f = Fernet(key)
        encrypted = f.encrypt(plaintext.encode())
        return encrypted.decode()
    
    @staticmethod
    def decrypt_field(encrypted_text, key=None):
        """Decrypt a field value (CI/DI)"""
        if key is None:
            key = settings.SECRET_KEY.encode()[:32]
            key = base64.urlsafe_b64encode(key)
        
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_text.encode())
        return decrypted.decode()
    
    @staticmethod
    def encrypt_with_aes_gcm(plaintext, key):
        """
        Encrypt using AES-256-GCM for service provider callback
        """
        if isinstance(key, str):
            key = key.encode()[:32]  # Ensure 256-bit key
        
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        
        # Return base64-encoded nonce + ciphertext
        combined = nonce + ciphertext
        return base64.b64encode(combined).decode()
    
    @staticmethod
    def decrypt_with_aes_gcm(encrypted_text, key):
        """Decrypt using AES-256-GCM"""
        if isinstance(key, str):
            key = key.encode()[:32]
        
        combined = base64.b64decode(encrypted_text.encode())
        nonce = combined[:12]
        ciphertext = combined[12:]
        
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()


def mask_phone_number(phone):
    """
    Mask phone number for display
    Example: 010-1234-5678 → 010-****-5678
    """
    parts = phone.split('-')
    if len(parts) == 3:
        return f"{parts[0]}-****-{parts[2]}"
    return '***-****-****'


def mask_sensitive_data(data_type='ci'):
    """Return masked string for sensitive data"""
    return '*' * 21

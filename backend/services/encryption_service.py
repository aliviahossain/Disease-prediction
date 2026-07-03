"""
Encryption service for protecting sensitive medical data.

Implements AES-256 encryption/decryption for HIPAA compliance.
"""

from cryptography.fernet import Fernet
import os
import logging

logger = logging.getLogger(__name__)

class EncryptionService:
    """Service for encrypting/decrypting sensitive medical data."""
    
    def __init__(self):
        # Get encryption key from environment (must be 44 characters, base64-encoded)
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            raise ValueError("ENCRYPTION_KEY environment variable not set")
        try:
            self.cipher = Fernet(key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string. Returns encrypted bytes as utf-8 string."""
        if not plaintext:
            return None
        try:
            encrypted = self.cipher.encrypt(plaintext.encode('utf-8'))
            return encrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext string. Returns plaintext string."""
        if not ciphertext:
            return None
        try:
            decrypted = self.cipher.decrypt(ciphertext.encode('utf-8'))
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

# Singleton instance
_encryption_service = None

def get_encryption_service() -> EncryptionService:
    """Get or create the encryption service singleton."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


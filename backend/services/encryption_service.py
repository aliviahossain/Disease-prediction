"""Encryption service for medical data."""

from cryptography.fernet import Fernet
import os, logging

logger = logging.getLogger(__name__)


class EncryptionService:
    def __init__(self):
        self.cipher = None

    def _init(self):
        if self.cipher:
            return
        key = os.environ.get("ENCRYPTION_KEY")
        if key:
            try:
                self.cipher = Fernet(key)
            except:
                pass

    def encrypt(self, text):
        if not text:
            return None
        self._init()
        if not self.cipher:
            return text
        try:
            return self.cipher.encrypt(text.encode()).decode()
        except:
            return text

    def decrypt(self, text):
        if not text:
            return None
        self._init()
        if not self.cipher:
            return text
        try:
            return self.cipher.decrypt(text.encode()).decode()
        except:
            return text


_svc = None


def get_encryption_service():
    global _svc
    if _svc is None:
        _svc = EncryptionService()
    return _svc

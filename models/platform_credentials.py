"""Platform Credentials Model - Store login credentials for hackathon platforms"""
from mongoengine import Document, StringField, DateTimeField, BooleanField
from datetime import datetime
from cryptography.fernet import Fernet
import os
import base64

# Encryption key - in production, use environment variable
ENCRYPTION_KEY = os.environ.get('CREDENTIAL_ENCRYPTION_KEY', 'default-key-change-in-production')

def get_fernet():
    """Get Fernet instance for encryption/decryption"""
    # Pad or truncate key to 32 bytes, then base64 encode
    key = ENCRYPTION_KEY.encode()[:32].ljust(32, b'0')
    key_b64 = base64.urlsafe_b64encode(key)
    return Fernet(key_b64)


class PlatformCredentials(Document):
    """Store encrypted credentials for hackathon platforms"""
    
    meta = {
        'collection': 'platform_credentials',
        'indexes': [
            {'fields': ['user_id', 'platform'], 'unique': True}
        ]
    }
    
    user_id = StringField(required=True)
    platform = StringField(required=True, choices=['devpost', 'unstop', 'mlh', 'hackerearth', 'eventbrite', 'other'])
    
    # Encrypted fields
    encrypted_email = StringField()
    encrypted_password = StringField()
    
    # Metadata
    is_verified = BooleanField(default=False)
    last_used = DateTimeField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def set_credentials(self, email: str, password: str):
        """Encrypt and store credentials"""
        f = get_fernet()
        self.encrypted_email = f.encrypt(email.encode()).decode()
        self.encrypted_password = f.encrypt(password.encode()).decode()
        self.updated_at = datetime.utcnow()
    
    def get_credentials(self) -> tuple:
        """Decrypt and return credentials"""
        f = get_fernet()
        email = f.decrypt(self.encrypted_email.encode()).decode() if self.encrypted_email else None
        password = f.decrypt(self.encrypted_password.encode()).decode() if self.encrypted_password else None
        return email, password
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'platform': self.platform,
            'has_credentials': bool(self.encrypted_email and self.encrypted_password),
            'is_verified': self.is_verified,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

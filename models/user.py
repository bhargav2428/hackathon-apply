"""User Model - MongoDB"""
from datetime import datetime
from mongoengine import Document, StringField, BooleanField, DateTimeField, ListField
from flask_login import UserMixin


class User(Document, UserMixin):
    meta = {'collection': 'users'}
    
    email = StringField(required=True, unique=True)
    password_hash = StringField(required=True)
    name = StringField(required=True)
    is_active = BooleanField(default=True)
    is_admin = BooleanField(default=False)
    telegram_chat_id = StringField()
    auto_apply_enabled = BooleanField(default=False)
    auto_apply_tags = ListField(StringField())  # Filter hackathons by tags
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'email': self.email,
            'name': self.name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'telegram_chat_id': self.telegram_chat_id,
            'auto_apply_enabled': self.auto_apply_enabled,
            'auto_apply_tags': self.auto_apply_tags or [],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_id(self):
        return str(self.id)

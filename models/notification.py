"""Notification Model - MongoDB"""
from datetime import datetime
from mongoengine import Document, StringField, BooleanField, DateTimeField


class Notification(Document):
    meta = {'collection': 'notifications'}
    
    user_id = StringField(required=True)
    title = StringField()
    message = StringField(required=True)
    notification_type = StringField(default='info')
    is_read = BooleanField(default=False)
    read_at = DateTimeField()
    created_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = datetime.utcnow()
        self.save()

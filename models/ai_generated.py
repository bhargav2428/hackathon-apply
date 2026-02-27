"""AI Generated Content Model - MongoDB"""
from datetime import datetime
from mongoengine import Document, StringField, DateTimeField


class AIGeneratedContent(Document):
    meta = {'collection': 'ai_generated_contents'}
    
    user_id = StringField(required=True)
    hackathon_id = StringField()
    content_type = StringField(required=True)
    content = StringField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'hackathon_id': self.hackathon_id,
            'content_type': self.content_type,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

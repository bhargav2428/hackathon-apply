"""Hackathon Model - MongoDB"""
from datetime import datetime
from mongoengine import Document, StringField, BooleanField, DateTimeField, ListField


class Hackathon(Document):
    meta = {'collection': 'hackathons'}
    
    name = StringField(required=True)
    description = StringField()
    url = StringField()
    registration_url = StringField()  # Separate registration URL if different from main URL
    deadline = DateTimeField()
    prize = StringField()
    tags = ListField(StringField())
    themes = ListField(StringField())
    required_skills = ListField(StringField())
    is_active = BooleanField(default=True)
    source = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'url': self.url,
            'registration_url': self.registration_url,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'prize': self.prize,
            'tags': self.tags or [],
            'themes': self.themes or [],
            'required_skills': self.required_skills or [],
            'is_active': self.is_active,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

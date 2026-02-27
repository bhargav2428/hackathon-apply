"""User Profile Model - MongoDB"""
from datetime import datetime
from mongoengine import Document, StringField, ListField, DateTimeField


class UserProfile(Document):
    meta = {'collection': 'user_profiles'}
    
    user_id = StringField(required=True, unique=True)
    bio = StringField()
    skills = ListField(StringField())
    frameworks = ListField(StringField())
    languages = ListField(StringField())
    experience_level = StringField()
    github_url = StringField()
    linkedin_url = StringField()
    portfolio_url = StringField()
    resume_url = StringField()
    interests = ListField(StringField())
    past_hackathons = ListField(StringField())
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'bio': self.bio,
            'skills': self.skills or [],
            'frameworks': self.frameworks or [],
            'languages': self.languages or [],
            'experience_level': self.experience_level,
            'github_url': self.github_url,
            'linkedin_url': self.linkedin_url,
            'portfolio_url': self.portfolio_url,
            'resume_url': self.resume_url,
            'interests': self.interests or [],
            'past_hackathons': self.past_hackathons or []
        }

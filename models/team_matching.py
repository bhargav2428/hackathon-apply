"""
Team Matching Models - For AI-powered team formation
"""
from datetime import datetime
from mongoengine import Document, StringField, ListField, DateTimeField, FloatField, ReferenceField, BooleanField, DictField, IntField


class TeamRequest(Document):
    """User's request to find teammates"""
    meta = {'collection': 'team_requests'}
    
    user_id = StringField(required=True)
    hackathon_id = StringField(required=True)
    
    # What skills the user is looking for
    needed_skills = ListField(StringField())
    
    # User's own skills they bring
    offered_skills = ListField(StringField())
    
    # Team size preference
    preferred_team_size = IntField(default=4)
    current_team_size = IntField(default=1)
    
    # Preferences
    timezone = StringField()
    communication_preference = StringField(choices=['discord', 'slack', 'zoom', 'any'])
    experience_level = StringField(choices=['beginner', 'intermediate', 'advanced', 'any'])
    
    # Status
    status = StringField(default='looking', choices=['looking', 'found', 'closed'])
    
    # Contact info
    contact_discord = StringField()
    contact_email = StringField()
    contact_linkedin = StringField()
    
    message = StringField()  # Personal message to potential teammates
    
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'hackathon_id': self.hackathon_id,
            'needed_skills': self.needed_skills,
            'offered_skills': self.offered_skills,
            'preferred_team_size': self.preferred_team_size,
            'current_team_size': self.current_team_size,
            'timezone': self.timezone,
            'communication_preference': self.communication_preference,
            'experience_level': self.experience_level,
            'status': self.status,
            'contact_discord': self.contact_discord,
            'contact_email': self.contact_email,
            'contact_linkedin': self.contact_linkedin,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TeamMatch(Document):
    """Suggested team matches"""
    meta = {'collection': 'team_matches'}
    
    requester_id = StringField(required=True)
    matched_user_id = StringField(required=True)
    hackathon_id = StringField(required=True)
    
    # Match quality
    compatibility_score = FloatField()  # 0-100
    skill_complement_score = FloatField()
    
    # AI-generated reasons
    match_reasons = ListField(StringField())
    
    # Status
    status = StringField(default='suggested', choices=['suggested', 'accepted', 'declined', 'expired'])
    
    created_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'requester_id': self.requester_id,
            'matched_user_id': self.matched_user_id,
            'hackathon_id': self.hackathon_id,
            'compatibility_score': self.compatibility_score,
            'skill_complement_score': self.skill_complement_score,
            'match_reasons': self.match_reasons,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

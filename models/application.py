"""Application Model - MongoDB"""
from datetime import datetime
from mongoengine import Document, StringField, BooleanField, DateTimeField


class Application(Document):
    meta = {'collection': 'applications'}
    
    user_id = StringField(required=True)
    hackathon_id = StringField(required=True)
    hackathon_name = StringField()
    status = StringField(default='pending')
    generated_project_idea = StringField()
    generated_motivation = StringField()
    submission_url = StringField()
    is_auto_applied = BooleanField(default=False)
    error_message = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    submitted_at = DateTimeField()
    
    # External submission tracking
    external_submitted = BooleanField(default=False)  # Did user actually submit on hackathon website?
    external_confirmation = StringField()  # Confirmation number/email/screenshot reference
    external_submitted_at = DateTimeField()  # When they confirmed external submission
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'hackathon_id': self.hackathon_id,
            'hackathon_name': self.hackathon_name,
            'status': self.status,
            'generated_project_idea': self.generated_project_idea,
            'generated_motivation': self.generated_motivation,
            'submission_url': self.submission_url,
            'is_auto_applied': self.is_auto_applied,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'external_submitted': self.external_submitted,
            'external_confirmation': self.external_confirmation,
            'external_submitted_at': self.external_submitted_at.isoformat() if self.external_submitted_at else None
        }
    
    def mark_submitted(self, auto=False):
        self.status = 'submitted'
        self.is_auto_applied = auto
        self.submitted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.save()
    
    def mark_external_submitted(self, confirmation=None):
        """Mark that user has actually submitted on the hackathon website"""
        self.external_submitted = True
        self.external_confirmation = confirmation
        self.external_submitted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.save()
    
    def mark_error(self, error):
        self.status = 'error'
        self.error_message = error
        self.updated_at = datetime.utcnow()
        self.save()

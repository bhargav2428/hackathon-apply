"""
Success Prediction Models - ML model for predicting hackathon acceptance
"""
from datetime import datetime
from mongoengine import Document, StringField, ListField, DateTimeField, FloatField, IntField, DictField, BooleanField


class SuccessPrediction(Document):
    """Prediction of user's success for a hackathon"""
    meta = {'collection': 'success_predictions'}
    
    user_id = StringField(required=True)
    hackathon_id = StringField(required=True)
    
    # Prediction scores (0-100)
    acceptance_probability = FloatField()
    win_probability = FloatField()
    
    # Factor breakdown
    skill_match_score = FloatField()
    experience_score = FloatField()
    past_performance_score = FloatField()
    competition_level = FloatField()  # Higher = more competitive
    
    # AI analysis
    strengths = ListField(StringField())
    weaknesses = ListField(StringField())
    recommendations = ListField(StringField())
    
    # Metadata
    model_version = StringField(default='v1')
    confidence = FloatField()  # Model confidence in prediction
    
    predicted_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'hackathon_id': self.hackathon_id,
            'acceptance_probability': self.acceptance_probability,
            'win_probability': self.win_probability,
            'skill_match_score': self.skill_match_score,
            'experience_score': self.experience_score,
            'past_performance_score': self.past_performance_score,
            'competition_level': self.competition_level,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'recommendations': self.recommendations,
            'confidence': self.confidence,
            'predicted_at': self.predicted_at.isoformat() if self.predicted_at else None
        }


class HackathonStats(Document):
    """Historical statistics for hackathons"""
    meta = {'collection': 'hackathon_stats'}
    
    hackathon_id = StringField()
    hackathon_name = StringField(required=True)
    source = StringField()
    
    # Historical data
    total_applicants = IntField()
    total_accepted = IntField()
    acceptance_rate = FloatField()
    
    # Competition metrics
    avg_participant_experience = FloatField()  # years
    skill_distribution = DictField()  # {skill: count}
    
    # Prize info
    total_prize_pool = FloatField()
    prize_per_winner = FloatField()
    
    # Engagement
    avg_team_size = FloatField()
    total_submissions = IntField()
    
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'hackathon_id': self.hackathon_id,
            'hackathon_name': self.hackathon_name,
            'total_applicants': self.total_applicants,
            'total_accepted': self.total_accepted,
            'acceptance_rate': self.acceptance_rate,
            'avg_participant_experience': self.avg_participant_experience,
            'skill_distribution': self.skill_distribution,
            'total_prize_pool': self.total_prize_pool,
            'prize_per_winner': self.prize_per_winner,
            'avg_team_size': self.avg_team_size,
            'total_submissions': self.total_submissions,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

"""
ROI Calculator Models - For calculating hackathon prize ROI
"""
from datetime import datetime
from mongoengine import Document, StringField, ListField, DateTimeField, FloatField, IntField, DictField


class ROICalculation(Document):
    """ROI calculation for a hackathon"""
    meta = {'collection': 'roi_calculations'}
    
    user_id = StringField(required=True)
    hackathon_id = StringField(required=True)
    
    # Prize info
    prize_pool = FloatField()
    first_place_prize = FloatField()
    total_prizes = IntField()  # Number of prize categories
    
    # Time investment
    estimated_hours = FloatField()  # Hours to participate
    prep_hours = FloatField()  # Hours for preparation
    total_hours = FloatField()
    
    # Probability estimates
    win_probability = FloatField()  # 0-1
    acceptance_probability = FloatField()  # 0-1
    
    # Calculated values
    expected_prize_value = FloatField()  # prize * probability
    hourly_expected_value = FloatField()  # expected_value / hours
    
    # Non-monetary value
    learning_value = FloatField()  # Estimated learning value (1-10)
    networking_value = FloatField()  # Networking opportunity (1-10)
    portfolio_value = FloatField()  # Portfolio building value (1-10)
    
    # Overall scores
    roi_score = FloatField()  # 0-100 overall ROI score
    recommendation = StringField()  # "Highly Recommended", "Worth It", "Consider", "Skip"
    
    # AI insights
    ai_analysis = StringField()
    
    calculated_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'hackathon_id': self.hackathon_id,
            'prize_pool': self.prize_pool,
            'first_place_prize': self.first_place_prize,
            'total_prizes': self.total_prizes,
            'estimated_hours': self.estimated_hours,
            'prep_hours': self.prep_hours,
            'total_hours': self.total_hours,
            'win_probability': self.win_probability,
            'acceptance_probability': self.acceptance_probability,
            'expected_prize_value': self.expected_prize_value,
            'hourly_expected_value': self.hourly_expected_value,
            'learning_value': self.learning_value,
            'networking_value': self.networking_value,
            'portfolio_value': self.portfolio_value,
            'roi_score': self.roi_score,
            'recommendation': self.recommendation,
            'ai_analysis': self.ai_analysis,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None
        }


class HackathonROIRanking(Document):
    """Ranked list of hackathons by ROI for a user"""
    meta = {'collection': 'roi_rankings'}
    
    user_id = StringField(required=True)
    
    rankings = ListField(DictField())  # [{hackathon_id, roi_score, rank, ...}]
    
    filters_applied = DictField()  # What filters user applied
    
    generated_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'rankings': self.rankings,
            'filters_applied': self.filters_applied,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }

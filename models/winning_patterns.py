"""
Winning Pattern Models - For analyzing winning hackathon projects
"""
from datetime import datetime
from mongoengine import Document, StringField, ListField, DateTimeField, FloatField, IntField, DictField, BooleanField


class WinningProject(Document):
    """Scraped winning projects from hackathons"""
    meta = {'collection': 'winning_projects'}
    
    hackathon_name = StringField(required=True)
    hackathon_source = StringField()  # devpost, mlh, etc.
    hackathon_id = StringField()
    
    project_name = StringField(required=True)
    project_url = StringField()
    demo_url = StringField()
    github_url = StringField()
    
    description = StringField()
    
    # Award info
    prize_category = StringField()  # "Grand Prize", "Best Use of AI", etc.
    prize_amount = FloatField()
    placement = IntField()  # 1st, 2nd, 3rd
    
    # Tech analysis
    tech_stack = ListField(StringField())
    themes = ListField(StringField())
    apis_used = ListField(StringField())
    
    # Team info
    team_size = IntField()
    team_members = ListField(DictField())
    
    # Engagement metrics (if available)
    likes = IntField(default=0)
    comments = IntField(default=0)
    
    # Date
    hackathon_date = DateTimeField()
    scraped_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'hackathon_name': self.hackathon_name,
            'hackathon_source': self.hackathon_source,
            'project_name': self.project_name,
            'project_url': self.project_url,
            'demo_url': self.demo_url,
            'github_url': self.github_url,
            'description': self.description,
            'prize_category': self.prize_category,
            'prize_amount': self.prize_amount,
            'placement': self.placement,
            'tech_stack': self.tech_stack,
            'themes': self.themes,
            'apis_used': self.apis_used,
            'team_size': self.team_size,
            'likes': self.likes,
            'comments': self.comments,
            'hackathon_date': self.hackathon_date.isoformat() if self.hackathon_date else None
        }


class WinningPattern(Document):
    """Analyzed patterns from winning projects"""
    meta = {'collection': 'winning_patterns'}
    
    hackathon_id = StringField()
    hackathon_name = StringField()
    
    # Tech patterns
    top_tech_stacks = ListField(DictField())  # [{tech: 'React', win_rate: 0.4}, ...]
    top_themes = ListField(DictField())
    top_apis = ListField(DictField())
    
    # Project patterns
    avg_team_size = FloatField()
    common_features = ListField(StringField())
    
    # Success factors
    success_factors = ListField(DictField())  # [{factor: 'AI integration', importance: 0.8}, ...]
    
    # AI-generated insights
    ai_insights = StringField()
    recommendations = ListField(StringField())
    
    # Stats
    projects_analyzed = IntField(default=0)
    
    analyzed_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'hackathon_id': self.hackathon_id,
            'hackathon_name': self.hackathon_name,
            'top_tech_stacks': self.top_tech_stacks,
            'top_themes': self.top_themes,
            'top_apis': self.top_apis,
            'avg_team_size': self.avg_team_size,
            'common_features': self.common_features,
            'success_factors': self.success_factors,
            'ai_insights': self.ai_insights,
            'recommendations': self.recommendations,
            'projects_analyzed': self.projects_analyzed,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None
        }

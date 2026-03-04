"""
Post-Hackathon Tracker Models - Track project success after hackathons
"""
from datetime import datetime
from mongoengine import Document, StringField, ListField, DateTimeField, FloatField, IntField, DictField, BooleanField


class PostHackathonProject(Document):
    """Track a project after hackathon ends"""
    meta = {'collection': 'post_hackathon_projects'}
    
    user_id = StringField(required=True)
    hackathon_id = StringField(required=True)
    application_id = StringField()
    
    # Project links
    project_name = StringField(required=True)
    github_url = StringField()
    live_url = StringField()
    demo_video_url = StringField()
    devpost_url = StringField()
    
    # Results
    final_placement = StringField()  # "1st Place", "Best AI", etc.
    prize_won = FloatField()
    prizes_categories = ListField(StringField())
    
    # Engagement metrics (tracked over time)
    github_stars = IntField(default=0)
    github_forks = IntField(default=0)
    github_watchers = IntField(default=0)
    
    # User traction
    total_users = IntField(default=0)
    monthly_active_users = IntField(default=0)
    
    # Career impact
    job_offers_received = IntField(default=0)
    interviews_from_project = IntField(default=0)
    connections_made = IntField(default=0)
    
    # Media coverage
    media_mentions = ListField(DictField())  # [{source: "TechCrunch", url: "...", date: "..."}]
    
    # Continuation
    continued_development = BooleanField(default=False)
    became_startup = BooleanField(default=False)
    startup_funding = FloatField()
    
    # Notes & learnings
    lessons_learned = ListField(StringField())
    what_went_well = ListField(StringField())
    what_to_improve = ListField(StringField())
    
    # Tracking history
    metrics_history = ListField(DictField())  # [{date: "...", stars: X, users: Y, ...}]
    
    hackathon_date = DateTimeField()
    created_at = DateTimeField(default=datetime.utcnow)
    last_updated = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'hackathon_id': self.hackathon_id,
            'application_id': self.application_id,
            'project_name': self.project_name,
            'github_url': self.github_url,
            'live_url': self.live_url,
            'demo_video_url': self.demo_video_url,
            'devpost_url': self.devpost_url,
            'final_placement': self.final_placement,
            'prize_won': self.prize_won,
            'prizes_categories': self.prizes_categories,
            'github_stars': self.github_stars,
            'github_forks': self.github_forks,
            'github_watchers': self.github_watchers,
            'total_users': self.total_users,
            'monthly_active_users': self.monthly_active_users,
            'job_offers_received': self.job_offers_received,
            'interviews_from_project': self.interviews_from_project,
            'connections_made': self.connections_made,
            'media_mentions': self.media_mentions,
            'continued_development': self.continued_development,
            'became_startup': self.became_startup,
            'startup_funding': self.startup_funding,
            'lessons_learned': self.lessons_learned,
            'what_went_well': self.what_went_well,
            'what_to_improve': self.what_to_improve,
            'metrics_history': self.metrics_history,
            'hackathon_date': self.hackathon_date.isoformat() if self.hackathon_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class PortfolioSummary(Document):
    """Aggregated portfolio of all hackathon achievements"""
    meta = {'collection': 'portfolio_summaries'}
    
    user_id = StringField(required=True, unique=True)
    
    # Totals
    total_hackathons = IntField(default=0)
    total_wins = IntField(default=0)
    total_prizes_won = FloatField(default=0)
    total_projects = IntField(default=0)
    
    # Engagement totals
    total_github_stars = IntField(default=0)
    total_users_reached = IntField(default=0)
    
    # Career impact
    total_job_offers = IntField(default=0)
    total_connections = IntField(default=0)
    
    # Best achievements
    best_placement = StringField()
    highest_prize = FloatField()
    most_starred_project = DictField()
    
    # Skills demonstrated
    demonstrated_skills = ListField(StringField())
    tech_used = ListField(StringField())
    
    # Timeline
    first_hackathon_date = DateTimeField()
    last_hackathon_date = DateTimeField()
    
    last_updated = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'total_hackathons': self.total_hackathons,
            'total_wins': self.total_wins,
            'total_prizes_won': self.total_prizes_won,
            'total_projects': self.total_projects,
            'total_github_stars': self.total_github_stars,
            'total_users_reached': self.total_users_reached,
            'total_job_offers': self.total_job_offers,
            'total_connections': self.total_connections,
            'best_placement': self.best_placement,
            'highest_prize': self.highest_prize,
            'most_starred_project': self.most_starred_project,
            'demonstrated_skills': self.demonstrated_skills,
            'tech_used': self.tech_used,
            'first_hackathon_date': self.first_hackathon_date.isoformat() if self.first_hackathon_date else None,
            'last_hackathon_date': self.last_hackathon_date.isoformat() if self.last_hackathon_date else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

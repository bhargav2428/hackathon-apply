"""
Sponsor Models - For connecting with hackathon sponsors
"""
from datetime import datetime
from mongoengine import Document, StringField, ListField, DateTimeField, DictField, BooleanField, IntField, FloatField


class Sponsor(Document):
    """Hackathon sponsor information"""
    meta = {'collection': 'sponsors'}
    
    name = StringField(required=True)
    logo_url = StringField()
    website = StringField()
    
    # Company info
    industry = StringField()
    company_size = StringField()
    description = StringField()
    
    # Tech offerings
    apis = ListField(DictField())  # [{name: "GPT-4 API", description: "...", docs_url: "..."}]
    sdks = ListField(DictField())
    free_credits = DictField()  # {service: "AWS", amount: "$100", code: "HACKATHON2024"}
    
    # Prize categories they sponsor
    prize_categories = ListField(StringField())  # "Best Use of Twilio", etc.
    typical_prize_amount = FloatField()
    
    # Contact
    developer_relations_contact = DictField()  # {name: "...", email: "...", twitter: "..."}
    discord_server = StringField()
    slack_channel = StringField()
    
    # Social
    twitter = StringField()
    linkedin = StringField()
    github = StringField()
    
    # Hackathons they sponsor
    hackathons_sponsored = ListField(StringField())
    
    # Tips for winning their prizes
    winning_tips = ListField(StringField())
    what_they_look_for = ListField(StringField())
    
    last_updated = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'logo_url': self.logo_url,
            'website': self.website,
            'industry': self.industry,
            'company_size': self.company_size,
            'description': self.description,
            'apis': self.apis,
            'sdks': self.sdks,
            'free_credits': self.free_credits,
            'prize_categories': self.prize_categories,
            'typical_prize_amount': self.typical_prize_amount,
            'developer_relations_contact': self.developer_relations_contact,
            'discord_server': self.discord_server,
            'slack_channel': self.slack_channel,
            'twitter': self.twitter,
            'linkedin': self.linkedin,
            'github': self.github,
            'hackathons_sponsored': self.hackathons_sponsored,
            'winning_tips': self.winning_tips,
            'what_they_look_for': self.what_they_look_for,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class SponsorConnection(Document):
    """User's connection/interaction with sponsors"""
    meta = {'collection': 'sponsor_connections'}
    
    user_id = StringField(required=True)
    sponsor_id = StringField(required=True)
    hackathon_id = StringField()
    
    # Status
    connection_type = StringField(choices=['interested', 'connected', 'mentored', 'hired'])
    
    # Interactions
    used_api = BooleanField(default=False)
    applied_for_prize = BooleanField(default=False)
    won_prize = BooleanField(default=False)
    prize_won = StringField()
    
    # Mentorship
    had_mentorship = BooleanField(default=False)
    mentorship_notes = StringField()
    
    # Follow-up
    follow_up_sent = BooleanField(default=False)
    response_received = BooleanField(default=False)
    
    notes = StringField()
    
    created_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'sponsor_id': self.sponsor_id,
            'hackathon_id': self.hackathon_id,
            'connection_type': self.connection_type,
            'used_api': self.used_api,
            'applied_for_prize': self.applied_for_prize,
            'won_prize': self.won_prize,
            'prize_won': self.prize_won,
            'had_mentorship': self.had_mentorship,
            'mentorship_notes': self.mentorship_notes,
            'follow_up_sent': self.follow_up_sent,
            'response_received': self.response_received,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SponsorSuggestion(Document):
    """AI-suggested ways to use sponsor tech in projects"""
    meta = {'collection': 'sponsor_suggestions'}
    
    user_id = StringField(required=True)
    hackathon_id = StringField(required=True)
    sponsor_id = StringField(required=True)
    
    # Suggestion content
    integration_idea = StringField()
    how_to_use = StringField()
    code_example = StringField()
    
    # Resources
    relevant_docs = ListField(StringField())
    tutorial_links = ListField(StringField())
    
    # Prize alignment
    prize_category = StringField()
    alignment_score = IntField()  # How well idea aligns with prize criteria
    
    generated_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'hackathon_id': self.hackathon_id,
            'sponsor_id': self.sponsor_id,
            'integration_idea': self.integration_idea,
            'how_to_use': self.how_to_use,
            'code_example': self.code_example,
            'relevant_docs': self.relevant_docs,
            'tutorial_links': self.tutorial_links,
            'prize_category': self.prize_category,
            'alignment_score': self.alignment_score,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }

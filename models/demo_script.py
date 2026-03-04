"""
Demo Script Models - For generating hackathon demo/pitch scripts
"""
from datetime import datetime
from mongoengine import Document, StringField, ListField, DateTimeField, IntField, DictField


class DemoScript(Document):
    """AI-generated demo/pitch script for hackathon presentations"""
    meta = {'collection': 'demo_scripts'}
    
    user_id = StringField(required=True)
    hackathon_id = StringField(required=True)
    application_id = StringField()
    
    # Project info
    project_name = StringField()
    project_description = StringField()
    
    # Script content
    script_type = StringField(default='3min', choices=['1min', '3min', '5min', 'elevator'])
    
    # Structured script
    hook = StringField()  # Opening hook (10-15 sec)
    problem = StringField()  # Problem statement
    solution = StringField()  # Your solution
    demo_points = ListField(DictField())  # [{time: "0:30", action: "Show login", talking_point: "..."}]
    tech_highlight = StringField()  # Technical achievement
    impact = StringField()  # Impact/results
    call_to_action = StringField()  # Closing CTA
    
    # Full script
    full_script = StringField()
    
    # Timing
    total_duration_seconds = IntField()
    
    # Tips
    presentation_tips = ListField(StringField())
    common_questions = ListField(DictField())  # [{question: "...", suggested_answer: "..."}]
    
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'hackathon_id': self.hackathon_id,
            'application_id': self.application_id,
            'project_name': self.project_name,
            'project_description': self.project_description,
            'script_type': self.script_type,
            'hook': self.hook,
            'problem': self.problem,
            'solution': self.solution,
            'demo_points': self.demo_points,
            'tech_highlight': self.tech_highlight,
            'impact': self.impact,
            'call_to_action': self.call_to_action,
            'full_script': self.full_script,
            'total_duration_seconds': self.total_duration_seconds,
            'presentation_tips': self.presentation_tips,
            'common_questions': self.common_questions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Storyboard(Document):
    """Visual storyboard for demo video"""
    meta = {'collection': 'storyboards'}
    
    demo_script_id = StringField(required=True)
    user_id = StringField(required=True)
    
    scenes = ListField(DictField())  # [{scene_number: 1, duration: "15s", visual: "...", audio: "...", notes: "..."}]
    
    # Visual suggestions
    color_scheme = ListField(StringField())
    font_suggestions = ListField(StringField())
    transition_style = StringField()
    
    # Tools recommendations
    recommended_tools = ListField(DictField())  # [{tool: "Canva", purpose: "slides"}]
    
    created_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'demo_script_id': self.demo_script_id,
            'user_id': self.user_id,
            'scenes': self.scenes,
            'color_scheme': self.color_scheme,
            'font_suggestions': self.font_suggestions,
            'transition_style': self.transition_style,
            'recommended_tools': self.recommended_tools,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

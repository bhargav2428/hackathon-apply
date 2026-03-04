"""
Multi-Language Models - For generating applications in multiple languages
"""
from datetime import datetime
from mongoengine import Document, StringField, ListField, DateTimeField, DictField, BooleanField, FloatField


class TranslatedApplication(Document):
    """Translated hackathon application content"""
    meta = {'collection': 'translated_applications'}
    
    user_id = StringField(required=True)
    hackathon_id = StringField(required=True)
    original_application_id = StringField()
    
    # Language info
    source_language = StringField(default='en')
    target_language = StringField(required=True)  # ISO code: 'ja', 'zh', 'de', etc.
    
    # Translated content
    translated_project_idea = DictField()
    translated_motivation = StringField()
    translated_bio = StringField()
    translated_team_description = StringField()
    
    # Cultural adaptations
    cultural_notes = ListField(StringField())  # Notes about cultural adjustments made
    formality_level = StringField(choices=['casual', 'neutral', 'formal', 'very_formal'])
    
    # Quality
    ai_confidence = FloatField()
    reviewed = BooleanField(default=False)
    
    created_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'hackathon_id': self.hackathon_id,
            'original_application_id': self.original_application_id,
            'source_language': self.source_language,
            'target_language': self.target_language,
            'translated_project_idea': self.translated_project_idea,
            'translated_motivation': self.translated_motivation,
            'translated_bio': self.translated_bio,
            'translated_team_description': self.translated_team_description,
            'cultural_notes': self.cultural_notes,
            'formality_level': self.formality_level,
            'ai_confidence': self.ai_confidence,
            'reviewed': self.reviewed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


from mongoengine import FloatField

class LanguagePreferences(Document):
    """User's language preferences"""
    meta = {'collection': 'language_preferences'}
    
    user_id = StringField(required=True, unique=True)
    
    # Primary language
    primary_language = StringField(default='en')
    
    # Languages user can write applications in
    fluent_languages = ListField(StringField())
    
    # Auto-translation settings
    auto_translate = BooleanField(default=False)
    default_target_languages = ListField(StringField())
    
    # Cultural preferences
    preferred_formality = DictField()  # {language_code: formality_level}
    
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'primary_language': self.primary_language,
            'fluent_languages': self.fluent_languages,
            'auto_translate': self.auto_translate,
            'default_target_languages': self.default_target_languages,
            'preferred_formality': self.preferred_formality,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Supported languages with cultural context
SUPPORTED_LANGUAGES = {
    'en': {'name': 'English', 'formality': 'casual', 'region': 'Global'},
    'zh': {'name': 'Chinese (Simplified)', 'formality': 'formal', 'region': 'China'},
    'zh-tw': {'name': 'Chinese (Traditional)', 'formality': 'formal', 'region': 'Taiwan/HK'},
    'ja': {'name': 'Japanese', 'formality': 'very_formal', 'region': 'Japan'},
    'ko': {'name': 'Korean', 'formality': 'formal', 'region': 'South Korea'},
    'de': {'name': 'German', 'formality': 'neutral', 'region': 'DACH'},
    'fr': {'name': 'French', 'formality': 'neutral', 'region': 'France/Canada'},
    'es': {'name': 'Spanish', 'formality': 'casual', 'region': 'Spain/LATAM'},
    'pt': {'name': 'Portuguese', 'formality': 'casual', 'region': 'Brazil/Portugal'},
    'hi': {'name': 'Hindi', 'formality': 'neutral', 'region': 'India'},
    'ar': {'name': 'Arabic', 'formality': 'formal', 'region': 'MENA'},
    'ru': {'name': 'Russian', 'formality': 'neutral', 'region': 'Russia/CIS'},
}

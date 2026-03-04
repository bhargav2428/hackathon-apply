"""
Multi-Language Routes - Generate applications in multiple languages
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models.multi_language import TranslatedApplication, LanguagePreferences, SUPPORTED_LANGUAGES
from models.hackathon import Hackathon
from models.application import Application
from services.ai_service import AIService
import json

multi_language_bp = Blueprint('multi_language', __name__)


@multi_language_bp.route('/languages', methods=['GET'])
def get_supported_languages():
    """Get list of supported languages"""
    return jsonify({'languages': SUPPORTED_LANGUAGES}), 200


@multi_language_bp.route('/preferences', methods=['GET'])
@login_required
def get_language_preferences():
    """Get user's language preferences"""
    prefs = LanguagePreferences.objects(user_id=str(current_user.id)).first()
    if not prefs:
        prefs = LanguagePreferences(user_id=str(current_user.id))
        prefs.save()
    return jsonify({'preferences': prefs.to_dict()}), 200


@multi_language_bp.route('/preferences', methods=['PUT'])
@login_required
def update_language_preferences():
    """Update language preferences"""
    data = request.get_json()
    
    prefs = LanguagePreferences.objects(user_id=str(current_user.id)).first()
    if not prefs:
        prefs = LanguagePreferences(user_id=str(current_user.id))
    
    for field in ['primary_language', 'fluent_languages', 'auto_translate',
                  'default_target_languages', 'preferred_formality']:
        if field in data:
            setattr(prefs, field, data[field])
    
    prefs.updated_at = datetime.utcnow()
    prefs.save()
    
    return jsonify({'preferences': prefs.to_dict()}), 200


@multi_language_bp.route('/translate', methods=['POST'])
@login_required
def translate_application():
    """Translate application content to another language"""
    data = request.get_json()
    
    application_id = data.get('application_id')
    hackathon_id = data.get('hackathon_id')
    target_language = data.get('target_language')
    
    # Content to translate (either from application or provided directly)
    project_idea = data.get('project_idea')
    motivation = data.get('motivation')
    
    if not target_language:
        return jsonify({'error': 'target_language required'}), 400
    
    if target_language not in SUPPORTED_LANGUAGES:
        return jsonify({'error': f'Unsupported language: {target_language}'}), 400
    
    # Get content from application if not provided
    if application_id and not project_idea:
        app = Application.objects(id=application_id).first()
        if app:
            if app.generated_project_idea:
                try:
                    project_idea = json.loads(app.generated_project_idea)
                except:
                    project_idea = app.generated_project_idea
            motivation = app.generated_motivation
            hackathon_id = app.hackathon_id
    
    if not project_idea and not motivation:
        return jsonify({'error': 'No content to translate'}), 400
    
    # Get user preferences for formality
    prefs = LanguagePreferences.objects(user_id=str(current_user.id)).first()
    formality = prefs.preferred_formality.get(target_language) if prefs and prefs.preferred_formality else None
    
    if not formality:
        # Use default formality for the language
        formality = SUPPORTED_LANGUAGES.get(target_language, {}).get('formality', 'neutral')
    
    try:
        ai = AIService()
        translation = perform_translation(
            project_idea, motivation, target_language, formality, ai
        )
        
        # Save translation
        trans = TranslatedApplication(
            user_id=str(current_user.id),
            hackathon_id=hackathon_id,
            original_application_id=application_id,
            source_language='en',
            target_language=target_language,
            translated_project_idea=translation.get('project_idea'),
            translated_motivation=translation.get('motivation'),
            cultural_notes=translation.get('cultural_notes', []),
            formality_level=formality,
            ai_confidence=translation.get('confidence', 85)
        )
        trans.save()
        
        return jsonify({'translation': trans.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Translation failed: {str(e)}'}), 500


@multi_language_bp.route('/translations', methods=['GET'])
@login_required
def get_my_translations():
    """Get user's translations"""
    hackathon_id = request.args.get('hackathon_id')
    
    query = {'user_id': str(current_user.id)}
    if hackathon_id:
        query['hackathon_id'] = hackathon_id
    
    translations = TranslatedApplication.objects(**query).order_by('-created_at')
    return jsonify({'translations': [t.to_dict() for t in translations]}), 200


@multi_language_bp.route('/translations/<translation_id>', methods=['GET'])
@login_required
def get_translation(translation_id):
    """Get a specific translation"""
    trans = TranslatedApplication.objects(id=translation_id, user_id=str(current_user.id)).first()
    if not trans:
        return jsonify({'error': 'Translation not found'}), 404
    return jsonify({'translation': trans.to_dict()}), 200


@multi_language_bp.route('/batch-translate', methods=['POST'])
@login_required
def batch_translate():
    """Translate to multiple languages at once"""
    data = request.get_json()
    
    application_id = data.get('application_id')
    target_languages = data.get('target_languages', [])
    project_idea = data.get('project_idea')
    motivation = data.get('motivation')
    
    if not target_languages:
        return jsonify({'error': 'target_languages required'}), 400
    
    # Limit to 5 languages
    target_languages = target_languages[:5]
    
    results = []
    
    for lang in target_languages:
        if lang in SUPPORTED_LANGUAGES:
            try:
                # Call single translate
                ai = AIService()
                prefs = LanguagePreferences.objects(user_id=str(current_user.id)).first()
                formality = prefs.preferred_formality.get(lang) if prefs and prefs.preferred_formality else SUPPORTED_LANGUAGES.get(lang, {}).get('formality', 'neutral')
                
                translation = perform_translation(project_idea, motivation, lang, formality, ai)
                
                results.append({
                    'language': lang,
                    'language_name': SUPPORTED_LANGUAGES[lang]['name'],
                    'translation': translation,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'language': lang,
                    'error': str(e),
                    'success': False
                })
    
    return jsonify({'results': results}), 200


@multi_language_bp.route('/detect-language', methods=['POST'])
@login_required
def detect_language():
    """Detect the language of text"""
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'text required'}), 400
    
    try:
        ai = AIService()
        detected = detect_text_language(text, ai)
        return jsonify({'detected': detected}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def perform_translation(project_idea, motivation, target_language, formality, ai):
    """Perform AI-powered translation with cultural adaptation"""
    
    lang_info = SUPPORTED_LANGUAGES.get(target_language, {})
    lang_name = lang_info.get('name', target_language)
    region = lang_info.get('region', '')
    
    formality_instructions = {
        'casual': 'Use casual, friendly language. Use contractions and colloquialisms.',
        'neutral': 'Use professional but approachable language.',
        'formal': 'Use formal language with proper honorifics where applicable.',
        'very_formal': 'Use highly formal language with all appropriate honorifics and politeness markers.'
    }
    
    prompt = f"""Translate and culturally adapt this hackathon application content to {lang_name} ({target_language}).

Target region: {region}
Formality level: {formality} - {formality_instructions.get(formality, '')}

Original Project Idea:
{json.dumps(project_idea) if isinstance(project_idea, dict) else project_idea}

Original Motivation:
{motivation or 'Not provided'}

Requirements:
1. Translate accurately while adapting for cultural context
2. Maintain technical terms that are commonly used in English in tech
3. Adjust formality to match local business culture
4. Note any cultural adaptations made

Return JSON with:
- project_idea: Translated project idea (same structure if dict, or string)
- motivation: Translated motivation statement
- cultural_notes: Array of notes about cultural adaptations made
- confidence: Your confidence in the translation quality (0-100)
"""

    messages = [
        {"role": "system", "content": f"You are an expert translator specializing in technical and business content for {lang_name}. Ensure culturally appropriate communication. Respond with valid JSON only."},
        {"role": "user", "content": prompt}
    ]
    
    response = ai._call_groq(messages, temperature=0.3, max_tokens=3000)
    
    try:
        result = json.loads(response)
        return result
    except:
        return {
            'project_idea': response,
            'motivation': '',
            'cultural_notes': ['Translation performed but JSON parsing failed'],
            'confidence': 70
        }


def detect_text_language(text, ai):
    """Detect the language of given text"""
    prompt = f"""Detect the language of this text and return JSON with:
- language_code: ISO language code (e.g., 'en', 'ja', 'zh')
- language_name: Full language name
- confidence: Detection confidence (0-100)

Text: "{text[:500]}"
"""

    messages = [
        {"role": "system", "content": "You are a language detection expert. Respond with valid JSON only."},
        {"role": "user", "content": prompt}
    ]
    
    response = ai._call_groq(messages, temperature=0.1, max_tokens=100)
    
    try:
        return json.loads(response)
    except:
        return {'language_code': 'en', 'language_name': 'English', 'confidence': 50}

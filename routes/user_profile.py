"""User Profile Routes - MongoDB"""
import os
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models.user_profile import UserProfile
from services.resume_parser import parse_resume
from services.ai_service import AIService

user_profile_bp = Blueprint('user_profile', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'resumes')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@user_profile_bp.route('', methods=['GET'])
@login_required
def get_profile():
    profile = UserProfile.objects(user_id=str(current_user.id)).first()
    if not profile:
        # Return empty profile data instead of 404
        return jsonify({
            'bio': '',
            'skills': [],
            'frameworks': [],
            'languages': [],
            'experience_level': '',
            'github_url': '',
            'linkedin_url': '',
            'portfolio_url': '',
            'interests': []
        }), 200
    return jsonify(profile.to_dict()), 200


@user_profile_bp.route('', methods=['POST', 'PUT'])
@login_required
def update_profile():
    data = request.get_json()
    profile = UserProfile.objects(user_id=str(current_user.id)).first()
    
    if not profile:
        profile = UserProfile(user_id=str(current_user.id))
    
    profile.bio = data.get('bio', profile.bio)
    profile.skills = data.get('skills', profile.skills or [])
    profile.frameworks = data.get('frameworks', profile.frameworks or [])
    profile.languages = data.get('languages', profile.languages or [])
    profile.experience_level = data.get('experience_level', profile.experience_level)
    profile.github_url = data.get('github_url', profile.github_url)
    profile.linkedin_url = data.get('linkedin_url', profile.linkedin_url)
    profile.portfolio_url = data.get('portfolio_url', profile.portfolio_url)
    profile.resume_url = data.get('resume_url', profile.resume_url)
    profile.interests = data.get('interests', profile.interests or [])
    profile.past_hackathons = data.get('past_hackathons', profile.past_hackathons or [])
    
    profile.save()
    return jsonify({'message': 'Profile updated', 'profile': profile.to_dict()}), 200


@user_profile_bp.route('/upload-resume', methods=['POST'])
@login_required
def upload_resume():
    """Upload and parse resume to auto-fill profile with validation"""
    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file provided'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: PDF, DOC, DOCX'}), 400
    
    try:
        # Save file
        filename = secure_filename(f"{current_user.id}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Parse resume with enhanced extraction
        parsed_data = parse_resume(filepath)
        
        if 'error' in parsed_data and not parsed_data.get('text'):
            return jsonify({'error': parsed_data['error']}), 400
        
        # Store validation info before AI enhancement
        pre_ai_validation = parsed_data.get('validation', {})
        
        # Use AI to enhance the parsed data
        ai_enhanced = {}
        try:
            ai_service = AIService()
            ai_enhanced = ai_service.enhance_resume_data(parsed_data)
            parsed_data.update(ai_enhanced)
        except Exception as e:
            print(f"AI enhancement failed: {e}")
        
        # Create validation summary for frontend
        validation_summary = {
            'regex_extraction': {
                'name': parsed_data.get('name'),
                'email': parsed_data.get('email'),
                'phone': parsed_data.get('phone'),
                'github': parsed_data.get('github'),
                'linkedin': parsed_data.get('linkedin'),
                'languages_count': len(parsed_data.get('programming_languages', [])),
                'frameworks_count': len(parsed_data.get('frameworks', [])),
                'skills_count': len(parsed_data.get('skills', [])),
                'databases_count': len(parsed_data.get('databases', [])),
                'tools_count': len(parsed_data.get('tools', [])),
            },
            'ai_enhanced': bool(ai_enhanced),
            'confidence': pre_ai_validation.get('confidence', 0),
            'warnings': pre_ai_validation.get('warnings', []),
            'fields_found': pre_ai_validation.get('fields_found', []),
            'fields_missing': pre_ai_validation.get('fields_missing', []),
        }
        
        return jsonify({
            'success': True,
            'parsed_data': parsed_data,
            'validation': validation_summary,
            'message': 'Resume parsed successfully'
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@user_profile_bp.route('/parse-resume-text', methods=['POST'])
@login_required
def parse_resume_text():
    """Parse resume text using regex + AI to extract profile data with validation"""
    data = request.get_json()
    resume_text = data.get('text', '')
    
    if not resume_text:
        return jsonify({'error': 'No resume text provided'}), 400
    
    try:
        # First, use regex extraction from the resume parser
        from services.resume_parser import _extract_info_enhanced
        regex_parsed = _extract_info_enhanced(resume_text)
        
        # Store validation before AI enhancement
        pre_ai_validation = regex_parsed.get('validation', {})
        
        # Then enhance with AI
        ai_service = AIService()
        ai_enhanced = ai_service.enhance_resume_data(regex_parsed)
        
        # Merge data
        parsed = {**regex_parsed, **ai_enhanced}
        
        # Create validation summary
        validation_summary = {
            'regex_extraction': {
                'name': regex_parsed.get('name'),
                'email': regex_parsed.get('email'),
                'phone': regex_parsed.get('phone'),
                'github': regex_parsed.get('github'),
                'linkedin': regex_parsed.get('linkedin'),
                'languages_count': len(regex_parsed.get('programming_languages', [])),
                'frameworks_count': len(regex_parsed.get('frameworks', [])),
                'skills_count': len(regex_parsed.get('skills', [])),
                'databases_count': len(regex_parsed.get('databases', [])),
                'tools_count': len(regex_parsed.get('tools', [])),
            },
            'ai_enhanced': bool(ai_enhanced),
            'confidence': pre_ai_validation.get('confidence', 50),  # Default 50 for text input
            'warnings': pre_ai_validation.get('warnings', []),
            'fields_found': pre_ai_validation.get('fields_found', []),
            'fields_missing': pre_ai_validation.get('fields_missing', []),
        }
        
        return jsonify({
            'success': True,
            'parsed_data': parsed,
            'validation': validation_summary
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@user_profile_bp.route('/completeness', methods=['GET'])
@login_required
def get_completeness():
    profile = UserProfile.objects(user_id=str(current_user.id)).first()
    if not profile:
        return jsonify({'completeness': 0}), 200
    
    fields = ['bio', 'skills', 'frameworks', 'languages', 'experience_level', 'github_url']
    filled = sum(1 for f in fields if getattr(profile, f, None))
    completeness = int((filled / len(fields)) * 100)
    
    return jsonify({'completeness': completeness}), 200

"""AI Services Routes - MongoDB"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.ai_generated import AIGeneratedContent
from models.hackathon import Hackathon
from models.user_profile import UserProfile
from services.ai_service import AIService

ai_services_bp = Blueprint('ai_services', __name__)


@ai_services_bp.route('/generate/idea', methods=['POST'])
@login_required
def generate_idea():
    data = request.get_json()
    hackathon_id = data.get('hackathon_id')
    
    if not hackathon_id:
        return jsonify({'error': 'hackathon_id is required'}), 400
    
    hackathon = Hackathon.objects(id=hackathon_id).first()
    if not hackathon:
        return jsonify({'error': 'Hackathon not found'}), 404
    
    profile = UserProfile.objects(user_id=str(current_user.id)).first()
    
    try:
        ai = AIService()
        idea = ai.generate_project_idea(hackathon, profile)
        
        content = AIGeneratedContent(
            user_id=str(current_user.id),
            hackathon_id=hackathon_id,
            content_type='project_idea',
            content=str(idea)
        )
        content.save()
        
        return jsonify({'idea': str(idea), 'id': str(content.id)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_services_bp.route('/generate/motivation', methods=['POST'])
@login_required
def generate_motivation():
    data = request.get_json()
    hackathon_id = data.get('hackathon_id')
    
    if not hackathon_id:
        return jsonify({'error': 'hackathon_id is required'}), 400
    
    hackathon = Hackathon.objects(id=hackathon_id).first()
    if not hackathon:
        return jsonify({'error': 'Hackathon not found'}), 404
    
    profile = UserProfile.objects(user_id=str(current_user.id)).first()
    
    try:
        ai = AIService()
        motivation = ai.generate_motivation(hackathon, profile)
        
        content = AIGeneratedContent(
            user_id=str(current_user.id),
            hackathon_id=hackathon_id,
            content_type='motivation',
            content=motivation
        )
        content.save()
        
        return jsonify({'motivation': motivation, 'id': str(content.id)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_services_bp.route('/content', methods=['GET'])
@login_required
def get_generated_content():
    hackathon_id = request.args.get('hackathon_id')
    content_type = request.args.get('type')
    
    query = {'user_id': str(current_user.id)}
    if hackathon_id:
        query['hackathon_id'] = hackathon_id
    if content_type:
        query['content_type'] = content_type
    
    contents = AIGeneratedContent.objects(**query).order_by('-created_at')
    return jsonify({
        'contents': [c.to_dict() for c in contents]
    }), 200


@ai_services_bp.route('/content/<content_id>', methods=['DELETE'])
@login_required
def delete_content(content_id):
    content = AIGeneratedContent.objects(id=content_id, user_id=str(current_user.id)).first()
    if not content:
        return jsonify({'error': 'Content not found'}), 404
    
    content.delete()
    return jsonify({'message': 'Content deleted'}), 200

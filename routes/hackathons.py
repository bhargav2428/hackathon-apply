"""Hackathon Routes - MongoDB"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from models.hackathon import Hackathon
from datetime import datetime

hackathons_bp = Blueprint('hackathons', __name__)


@hackathons_bp.route('', methods=['GET'])
@login_required
def get_hackathons():
    is_active = request.args.get('active', 'true').lower() == 'true'
    
    if is_active:
        hackathons = Hackathon.objects(
            is_active=True,
            deadline__gte=datetime.utcnow()
        ).order_by('-created_at')
    else:
        hackathons = Hackathon.objects().order_by('-created_at')
    
    return jsonify({
        'hackathons': [h.to_dict() for h in hackathons]
    }), 200


@hackathons_bp.route('/<hackathon_id>', methods=['GET'])
@login_required
def get_hackathon(hackathon_id):
    hackathon = Hackathon.objects(id=hackathon_id).first()
    if not hackathon:
        return jsonify({'error': 'Hackathon not found'}), 404
    return jsonify(hackathon.to_dict()), 200


@hackathons_bp.route('', methods=['POST'])
@login_required
def create_hackathon():
    data = request.get_json()
    
    hackathon = Hackathon(
        name=data.get('name'),
        description=data.get('description'),
        url=data.get('url'),
        deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None,
        prize=data.get('prize'),
        tags=data.get('tags', []),
        themes=data.get('themes', []),
        required_skills=data.get('required_skills', [])
    )
    hackathon.save()
    
    return jsonify({'message': 'Hackathon created', 'hackathon': hackathon.to_dict()}), 201


@hackathons_bp.route('/search', methods=['GET'])
@login_required
def search_hackathons():
    q = request.args.get('q', '')
    if not q:
        return jsonify({'hackathons': []}), 200
    
    hackathons = Hackathon.objects(
        __raw__={'$or': [
            {'name': {'$regex': q, '$options': 'i'}},
            {'description': {'$regex': q, '$options': 'i'}},
            {'tags': {'$regex': q, '$options': 'i'}}
        ]}
    )
    
    return jsonify({
        'hackathons': [h.to_dict() for h in hackathons]
    }), 200


@hackathons_bp.route('/ai-search', methods=['POST'])
@login_required
def ai_search_hackathons():
    """Use AI to find the most relevant hackathons based on user query"""
    from services.ai_service import AIService
    import json
    
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    # Get all active hackathons
    all_hackathons = Hackathon.objects(
        is_active=True,
        deadline__gte=datetime.utcnow()
    )
    
    if not all_hackathons:
        return jsonify({
            'hackathons': [],
            'message': 'No active hackathons found'
        }), 200
    
    # Prepare hackathon summaries for AI
    hackathon_list = []
    for h in all_hackathons:
        hackathon_list.append({
            'id': str(h.id),
            'name': h.name,
            'description': h.description or '',
            'tags': h.tags or [],
            'themes': h.themes or [],
            'prize': h.prize or '',
            'deadline': h.deadline.isoformat() if h.deadline else ''
        })
    
    # Use AI to rank hackathons
    ai_service = AIService()
    
    prompt = f"""You are a hackathon matchmaking assistant. Given the user's query and a list of hackathons, 
identify the most relevant hackathons that match what the user is looking for.

User Query: {query}

Available Hackathons:
{json.dumps(hackathon_list, indent=2)}

Return a JSON array of hackathon IDs ranked by relevance (most relevant first).
Only include hackathons that actually match the user's interests.
Format: ["id1", "id2", "id3"]
If no hackathons match, return an empty array: []
Only return the JSON array, no other text."""

    try:
        response = ai_service._call_groq([
            {"role": "system", "content": "You are a helpful assistant that returns only valid JSON arrays."},
            {"role": "user", "content": prompt}
        ], temperature=0.3)
        
        # Parse AI response
        relevant_ids = json.loads(response.strip())
        
        # Get hackathons in order
        result_hackathons = []
        for hid in relevant_ids:
            h = Hackathon.objects(id=hid).first()
            if h:
                result_hackathons.append(h.to_dict())
        
        return jsonify({
            'hackathons': result_hackathons,
            'ai_response': response
        }), 200
        
    except Exception as e:
        # Fall back to regular search
        hackathons = Hackathon.objects(
            __raw__={'$or': [
                {'name': {'$regex': query, '$options': 'i'}},
                {'description': {'$regex': query, '$options': 'i'}},
                {'tags': {'$regex': query, '$options': 'i'}}
            ]}
        )
        return jsonify({
            'hackathons': [h.to_dict() for h in hackathons],
            'error': f'AI search failed, using fallback: {str(e)}'
        }), 200


@hackathons_bp.route('/all', methods=['GET'])
@login_required  
def get_all_hackathons():
    """Get all hackathons without filtering"""
    hackathons = Hackathon.objects().order_by('-created_at')
    return jsonify({
        'hackathons': [h.to_dict() for h in hackathons],
        'total': hackathons.count()
    }), 200

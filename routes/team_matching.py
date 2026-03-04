"""
Team Matching Routes - AI-powered teammate finding
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models.team_matching import TeamRequest, TeamMatch
from models.user_profile import UserProfile
from models.hackathon import Hackathon
from services.ai_service import AIService

team_matching_bp = Blueprint('team_matching', __name__)


@team_matching_bp.route('/requests', methods=['GET'])
@login_required
def get_team_requests():
    """Get all team requests (optionally filtered by hackathon)"""
    hackathon_id = request.args.get('hackathon_id')
    status = request.args.get('status', 'looking')
    
    query = {'status': status}
    if hackathon_id:
        query['hackathon_id'] = hackathon_id
    
    requests = TeamRequest.objects(**query).order_by('-created_at')
    
    # Enrich with user profiles
    enriched_requests = []
    for req in requests:
        req_dict = req.to_dict()
        profile = UserProfile.objects(user_id=req.user_id).first()
        if profile:
            req_dict['user_profile'] = {
                'name': profile.full_name,
                'skills': profile.skills,
                'experience': profile.years_of_experience,
                'location': profile.location
            }
        enriched_requests.append(req_dict)
    
    return jsonify({'requests': enriched_requests}), 200


@team_matching_bp.route('/requests', methods=['POST'])
@login_required
def create_team_request():
    """Create a new team request"""
    data = request.get_json()
    
    hackathon_id = data.get('hackathon_id')
    if not hackathon_id:
        return jsonify({'error': 'hackathon_id is required'}), 400
    
    # Check if user already has an active request for this hackathon
    existing = TeamRequest.objects(
        user_id=str(current_user.id),
        hackathon_id=hackathon_id,
        status='looking'
    ).first()
    
    if existing:
        return jsonify({'error': 'You already have an active team request for this hackathon'}), 400
    
    team_request = TeamRequest(
        user_id=str(current_user.id),
        hackathon_id=hackathon_id,
        needed_skills=data.get('needed_skills', []),
        offered_skills=data.get('offered_skills', []),
        preferred_team_size=data.get('preferred_team_size', 4),
        current_team_size=data.get('current_team_size', 1),
        timezone=data.get('timezone'),
        communication_preference=data.get('communication_preference', 'any'),
        experience_level=data.get('experience_level', 'any'),
        contact_discord=data.get('contact_discord'),
        contact_email=data.get('contact_email'),
        contact_linkedin=data.get('contact_linkedin'),
        message=data.get('message')
    )
    team_request.save()
    
    return jsonify({'request': team_request.to_dict()}), 201


@team_matching_bp.route('/requests/<request_id>', methods=['PUT'])
@login_required
def update_team_request(request_id):
    """Update a team request"""
    team_request = TeamRequest.objects(id=request_id, user_id=str(current_user.id)).first()
    if not team_request:
        return jsonify({'error': 'Team request not found'}), 404
    
    data = request.get_json()
    
    for field in ['needed_skills', 'offered_skills', 'preferred_team_size', 'current_team_size',
                  'timezone', 'communication_preference', 'experience_level', 'status',
                  'contact_discord', 'contact_email', 'contact_linkedin', 'message']:
        if field in data:
            setattr(team_request, field, data[field])
    
    team_request.updated_at = datetime.utcnow()
    team_request.save()
    
    return jsonify({'request': team_request.to_dict()}), 200


@team_matching_bp.route('/requests/<request_id>', methods=['DELETE'])
@login_required
def delete_team_request(request_id):
    """Delete/close a team request"""
    team_request = TeamRequest.objects(id=request_id, user_id=str(current_user.id)).first()
    if not team_request:
        return jsonify({'error': 'Team request not found'}), 404
    
    team_request.status = 'closed'
    team_request.save()
    
    return jsonify({'message': 'Team request closed'}), 200


@team_matching_bp.route('/find-matches', methods=['POST'])
@login_required
def find_matches():
    """AI-powered teammate matching"""
    data = request.get_json()
    hackathon_id = data.get('hackathon_id')
    
    if not hackathon_id:
        return jsonify({'error': 'hackathon_id is required'}), 400
    
    # Get user's profile and request
    user_profile = UserProfile.objects(user_id=str(current_user.id)).first()
    user_request = TeamRequest.objects(
        user_id=str(current_user.id),
        hackathon_id=hackathon_id,
        status='looking'
    ).first()
    
    if not user_request:
        return jsonify({'error': 'Create a team request first'}), 400
    
    # Get other team requests for this hackathon
    other_requests = TeamRequest.objects(
        hackathon_id=hackathon_id,
        status='looking',
        user_id__ne=str(current_user.id)
    )
    
    matches = []
    
    for other_req in other_requests:
        other_profile = UserProfile.objects(user_id=other_req.user_id).first()
        
        # Calculate compatibility score
        compatibility = calculate_compatibility(user_request, other_req, user_profile, other_profile)
        
        if compatibility['score'] >= 50:  # Only return good matches
            match = TeamMatch(
                requester_id=str(current_user.id),
                matched_user_id=other_req.user_id,
                hackathon_id=hackathon_id,
                compatibility_score=compatibility['score'],
                skill_complement_score=compatibility['skill_complement'],
                match_reasons=compatibility['reasons']
            )
            match.save()
            
            match_dict = match.to_dict()
            match_dict['matched_request'] = other_req.to_dict()
            if other_profile:
                match_dict['matched_profile'] = {
                    'name': other_profile.full_name,
                    'skills': other_profile.skills,
                    'experience': other_profile.years_of_experience
                }
            matches.append(match_dict)
    
    # Sort by compatibility score
    matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
    
    return jsonify({'matches': matches[:10]}), 200  # Return top 10 matches


@team_matching_bp.route('/matches/<match_id>/respond', methods=['POST'])
@login_required
def respond_to_match(match_id):
    """Accept or decline a match"""
    data = request.get_json()
    action = data.get('action')  # 'accept' or 'decline'
    
    if action not in ['accept', 'decline']:
        return jsonify({'error': 'Invalid action'}), 400
    
    match = TeamMatch.objects(id=match_id).first()
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    
    # Check if user is part of this match
    if str(current_user.id) not in [match.requester_id, match.matched_user_id]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    match.status = 'accepted' if action == 'accept' else 'declined'
    match.save()
    
    return jsonify({'match': match.to_dict()}), 200


@team_matching_bp.route('/my-requests', methods=['GET'])
@login_required
def get_my_requests():
    """Get current user's team requests"""
    requests = TeamRequest.objects(user_id=str(current_user.id)).order_by('-created_at')
    return jsonify({'requests': [r.to_dict() for r in requests]}), 200


@team_matching_bp.route('/my-matches', methods=['GET'])
@login_required
def get_my_matches():
    """Get current user's matches"""
    # Matches where user is requester or matched
    from mongoengine import Q
    matches = TeamMatch.objects(
        Q(requester_id=str(current_user.id)) | Q(matched_user_id=str(current_user.id))
    ).order_by('-created_at')
    
    enriched_matches = []
    for match in matches:
        match_dict = match.to_dict()
        # Get the other user's info
        other_user_id = match.matched_user_id if match.requester_id == str(current_user.id) else match.requester_id
        other_profile = UserProfile.objects(user_id=other_user_id).first()
        if other_profile:
            match_dict['other_user'] = {
                'name': other_profile.full_name,
                'skills': other_profile.skills,
                'experience': other_profile.years_of_experience
            }
        enriched_matches.append(match_dict)
    
    return jsonify({'matches': enriched_matches}), 200


def calculate_compatibility(user_req, other_req, user_profile, other_profile):
    """Calculate compatibility score between two team requests"""
    score = 0
    reasons = []
    
    # Skill complement: check if other person has skills user needs
    user_needed = set(user_req.needed_skills or [])
    other_offered = set(other_req.offered_skills or [])
    skill_overlap = user_needed.intersection(other_offered)
    
    if skill_overlap:
        skill_complement = len(skill_overlap) / len(user_needed) if user_needed else 0
        score += skill_complement * 40  # Up to 40 points
        reasons.append(f"Has skills you need: {', '.join(skill_overlap)}")
    else:
        skill_complement = 0
    
    # Reverse: check if user has skills other person needs
    other_needed = set(other_req.needed_skills or [])
    user_offered = set(user_req.offered_skills or [])
    reverse_overlap = other_needed.intersection(user_offered)
    
    if reverse_overlap:
        score += len(reverse_overlap) / max(len(other_needed), 1) * 20  # Up to 20 points
        reasons.append(f"You have skills they need: {', '.join(reverse_overlap)}")
    
    # Team size compatibility
    if user_req.preferred_team_size == other_req.preferred_team_size:
        score += 10
        reasons.append("Same team size preference")
    
    # Communication preference
    if user_req.communication_preference == other_req.communication_preference or \
       user_req.communication_preference == 'any' or other_req.communication_preference == 'any':
        score += 10
        reasons.append("Compatible communication preference")
    
    # Experience level
    if user_req.experience_level == other_req.experience_level or \
       user_req.experience_level == 'any' or other_req.experience_level == 'any':
        score += 10
        reasons.append("Compatible experience level")
    
    # Timezone (simple check)
    if user_req.timezone and other_req.timezone and user_req.timezone == other_req.timezone:
        score += 10
        reasons.append("Same timezone")
    
    return {
        'score': min(score, 100),
        'skill_complement': skill_complement * 100,
        'reasons': reasons
    }

"""
ROI Calculator Routes - Calculate hackathon prize ROI
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models.roi_calculator import ROICalculation, HackathonROIRanking
from models.hackathon import Hackathon
from models.user_profile import UserProfile
from models.success_prediction import SuccessPrediction
from services.ai_service import AIService
import json
import re

roi_calculator_bp = Blueprint('roi_calculator', __name__)


@roi_calculator_bp.route('/calculate/<hackathon_id>', methods=['GET'])
@login_required
def calculate_roi(hackathon_id):
    """Calculate ROI for a specific hackathon"""
    hackathon = Hackathon.objects(id=hackathon_id).first()
    if not hackathon:
        return jsonify({'error': 'Hackathon not found'}), 404
    
    profile = UserProfile.objects(user_id=str(current_user.id)).first()
    
    # Get success prediction if available
    prediction = SuccessPrediction.objects(
        user_id=str(current_user.id),
        hackathon_id=hackathon_id
    ).order_by('-predicted_at').first()
    
    roi = perform_roi_calculation(hackathon, profile, prediction, str(current_user.id))
    
    return jsonify({'roi': roi.to_dict()}), 200


@roi_calculator_bp.route('/calculate', methods=['POST'])
@login_required
def calculate_roi_with_params():
    """Calculate ROI with custom parameters"""
    data = request.get_json()
    
    hackathon_id = data.get('hackathon_id')
    if not hackathon_id:
        return jsonify({'error': 'hackathon_id required'}), 400
    
    hackathon = Hackathon.objects(id=hackathon_id).first()
    if not hackathon:
        return jsonify({'error': 'Hackathon not found'}), 404
    
    # Custom parameters override defaults
    estimated_hours = data.get('estimated_hours')
    prep_hours = data.get('prep_hours')
    
    profile = UserProfile.objects(user_id=str(current_user.id)).first()
    prediction = SuccessPrediction.objects(
        user_id=str(current_user.id),
        hackathon_id=hackathon_id
    ).first()
    
    roi = perform_roi_calculation(
        hackathon, profile, prediction, str(current_user.id),
        estimated_hours=estimated_hours,
        prep_hours=prep_hours
    )
    
    return jsonify({'roi': roi.to_dict()}), 200


@roi_calculator_bp.route('/rankings', methods=['GET'])
@login_required
def get_roi_rankings():
    """Get hackathons ranked by ROI score"""
    min_roi_score = float(request.args.get('min_score', 0))
    limit = int(request.args.get('limit', 20))
    
    # Get recent rankings for user
    ranking = HackathonROIRanking.objects(user_id=str(current_user.id)).order_by('-generated_at').first()
    
    # If no recent ranking or older than 24 hours, generate new one
    if not ranking or (datetime.utcnow() - ranking.generated_at).total_seconds() > 86400:
        ranking = generate_roi_rankings(str(current_user.id), min_roi_score, limit)
    
    return jsonify({'rankings': ranking.to_dict()}), 200


@roi_calculator_bp.route('/rankings/refresh', methods=['POST'])
@login_required
def refresh_rankings():
    """Force refresh ROI rankings"""
    data = request.get_json() or {}
    min_roi_score = float(data.get('min_score', 0))
    limit = int(data.get('limit', 20))
    
    ranking = generate_roi_rankings(str(current_user.id), min_roi_score, limit)
    return jsonify({'rankings': ranking.to_dict()}), 200


@roi_calculator_bp.route('/compare', methods=['POST'])
@login_required
def compare_hackathons():
    """Compare ROI of multiple hackathons"""
    data = request.get_json()
    hackathon_ids = data.get('hackathon_ids', [])
    
    if len(hackathon_ids) < 2:
        return jsonify({'error': 'At least 2 hackathon_ids required'}), 400
    
    comparisons = []
    profile = UserProfile.objects(user_id=str(current_user.id)).first()
    
    for hid in hackathon_ids[:5]:  # Limit to 5
        hackathon = Hackathon.objects(id=hid).first()
        if hackathon:
            prediction = SuccessPrediction.objects(
                user_id=str(current_user.id),
                hackathon_id=hid
            ).first()
            roi = perform_roi_calculation(hackathon, profile, prediction, str(current_user.id))
            comparisons.append({
                'hackathon_id': hid,
                'hackathon_name': hackathon.name,
                'roi': roi.to_dict()
            })
    
    # Sort by ROI score
    comparisons.sort(key=lambda x: x['roi']['roi_score'], reverse=True)
    
    return jsonify({'comparisons': comparisons}), 200


def perform_roi_calculation(hackathon, profile, prediction, user_id, estimated_hours=None, prep_hours=None):
    """Perform ROI calculation"""
    
    # Parse prize amount
    prize_pool = 0
    first_place = 0
    
    if hackathon.prize:
        # Extract numbers from prize string
        numbers = re.findall(r'[\d,]+', str(hackathon.prize).replace(',', ''))
        if numbers:
            prize_pool = float(numbers[0])
            first_place = prize_pool * 0.4  # Assume first place is ~40% of pool
    
    # Estimate time investment
    if estimated_hours is None:
        # Typical hackathon: 24-48 hours of coding
        estimated_hours = 36
    
    if prep_hours is None:
        prep_hours = 8  # Learning tech, planning, etc.
    
    total_hours = estimated_hours + prep_hours
    
    # Get or estimate probabilities
    if prediction:
        win_prob = prediction.win_probability / 100
        acceptance_prob = prediction.acceptance_probability / 100
    else:
        win_prob = 0.05  # Default 5% win rate
        acceptance_prob = 0.80  # Default 80% acceptance
    
    # Calculate expected prize value
    # Expected Value = Prize * P(win) * P(acceptance)
    expected_prize = first_place * win_prob * acceptance_prob
    
    # Hourly expected value
    hourly_ev = expected_prize / total_hours if total_hours > 0 else 0
    
    # Non-monetary values (1-10 scale)
    learning_value = calculate_learning_value(hackathon, profile)
    networking_value = calculate_networking_value(hackathon)
    portfolio_value = calculate_portfolio_value(hackathon, profile)
    
    # Overall ROI score (0-100)
    # Weighted: 40% financial, 20% learning, 20% networking, 20% portfolio
    financial_score = min((hourly_ev / 10) * 100, 100)  # $10/hr = max financial score
    
    roi_score = (
        financial_score * 0.4 +
        learning_value * 10 * 0.2 +
        networking_value * 10 * 0.2 +
        portfolio_value * 10 * 0.2
    )
    
    # Generate recommendation
    if roi_score >= 75:
        recommendation = "Highly Recommended"
    elif roi_score >= 50:
        recommendation = "Worth It"
    elif roi_score >= 30:
        recommendation = "Consider"
    else:
        recommendation = "Low ROI"
    
    # AI analysis
    try:
        ai = AIService()
        ai_analysis = generate_ai_analysis(hackathon, roi_score, hourly_ev, ai)
    except:
        ai_analysis = f"ROI Score: {roi_score:.0f}/100. This hackathon {'offers good value' if roi_score >= 50 else 'has lower ROI'}."
    
    # Save calculation
    roi = ROICalculation(
        user_id=user_id,
        hackathon_id=str(hackathon.id),
        prize_pool=prize_pool,
        first_place_prize=first_place,
        total_prizes=5,  # Estimate
        estimated_hours=estimated_hours,
        prep_hours=prep_hours,
        total_hours=total_hours,
        win_probability=win_prob,
        acceptance_probability=acceptance_prob,
        expected_prize_value=expected_prize,
        hourly_expected_value=hourly_ev,
        learning_value=learning_value,
        networking_value=networking_value,
        portfolio_value=portfolio_value,
        roi_score=roi_score,
        recommendation=recommendation,
        ai_analysis=ai_analysis
    )
    roi.save()
    
    return roi


def calculate_learning_value(hackathon, profile):
    """Calculate learning value (1-10)"""
    value = 5  # Base
    
    # Higher if hackathon has specific technologies to learn
    if hackathon.required_skills:
        user_skills = set(profile.skills) if profile and profile.skills else set()
        new_skills = set(hackathon.required_skills) - user_skills
        value += min(len(new_skills) * 0.5, 3)  # Up to +3 for new skills
    
    # Higher for themed hackathons
    if hackathon.themes:
        value += 1
    
    return min(value, 10)


def calculate_networking_value(hackathon):
    """Calculate networking value (1-10)"""
    value = 5  # Base
    
    # Check source - some platforms have better networking
    source = (hackathon.source or '').lower()
    if 'mlh' in source:
        value += 2  # MLH has great networking
    elif 'devpost' in source:
        value += 1
    
    # Higher if online (more accessible networking)
    if hackathon.location and 'online' in hackathon.location.lower():
        value += 1
    
    return min(value, 10)


def calculate_portfolio_value(hackathon, profile):
    """Calculate portfolio building value (1-10)"""
    value = 6  # Most hackathons give good portfolio pieces
    
    # Higher if aligned with profile interests
    if profile and profile.skills and hackathon.required_skills:
        overlap = set(profile.skills).intersection(set(hackathon.required_skills))
        if overlap:
            value += 2  # Builds on existing expertise
    
    # Higher prize pools often attract more attention
    if hackathon.prize:
        try:
            amount = float(re.search(r'\d+', str(hackathon.prize).replace(',', '')).group())
            if amount > 5000:
                value += 1
        except:
            pass
    
    return min(value, 10)


def generate_roi_rankings(user_id, min_score=0, limit=20):
    """Generate ROI rankings for all active hackathons"""
    profile = UserProfile.objects(user_id=user_id).first()
    
    # Get active hackathons
    hackathons = Hackathon.objects(deadline__gte=datetime.utcnow()).limit(50)
    
    rankings_data = []
    
    for hackathon in hackathons:
        prediction = SuccessPrediction.objects(
            user_id=user_id,
            hackathon_id=str(hackathon.id)
        ).first()
        
        roi = perform_roi_calculation(hackathon, profile, prediction, user_id)
        
        if roi.roi_score >= min_score:
            rankings_data.append({
                'hackathon_id': str(hackathon.id),
                'hackathon_name': hackathon.name,
                'roi_score': roi.roi_score,
                'recommendation': roi.recommendation,
                'expected_prize': roi.expected_prize_value,
                'total_hours': roi.total_hours,
                'deadline': hackathon.deadline.isoformat() if hackathon.deadline else None
            })
    
    # Sort by ROI score
    rankings_data.sort(key=lambda x: x['roi_score'], reverse=True)
    
    # Assign ranks
    for i, r in enumerate(rankings_data):
        r['rank'] = i + 1
    
    ranking = HackathonROIRanking(
        user_id=user_id,
        rankings=rankings_data[:limit],
        filters_applied={'min_score': min_score, 'limit': limit}
    )
    ranking.save()
    
    return ranking


def generate_ai_analysis(hackathon, roi_score, hourly_ev, ai):
    """Generate AI analysis of ROI"""
    prompt = f"""Briefly analyze the ROI for hackathon "{hackathon.name}":
- ROI Score: {roi_score:.0f}/100
- Expected hourly value: ${hourly_ev:.2f}/hr
- Prize: {hackathon.prize}

Give a 2-3 sentence analysis of whether this is worth the time investment."""

    messages = [
        {"role": "system", "content": "You are a concise hackathon ROI analyst."},
        {"role": "user", "content": prompt}
    ]
    
    return ai._call_groq(messages, temperature=0.5, max_tokens=200)

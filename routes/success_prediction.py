"""
Success Prediction Routes - ML-powered hackathon success prediction
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models.success_prediction import SuccessPrediction, HackathonStats
from models.hackathon import Hackathon
from models.user_profile import UserProfile
from models.application import Application
from services.ai_service import AIService

success_prediction_bp = Blueprint('success_prediction', __name__)


@success_prediction_bp.route('/predict/<hackathon_id>', methods=['GET'])
@login_required
def predict_success(hackathon_id):
    """Get success prediction for current user and hackathon"""
    # Check for existing recent prediction
    existing = SuccessPrediction.objects(
        user_id=str(current_user.id),
        hackathon_id=hackathon_id
    ).order_by('-predicted_at').first()
    
    # Return existing if less than 24 hours old
    if existing and (datetime.utcnow() - existing.predicted_at).total_seconds() < 86400:
        return jsonify({'prediction': existing.to_dict()}), 200
    
    hackathon = Hackathon.objects(id=hackathon_id).first()
    if not hackathon:
        return jsonify({'error': 'Hackathon not found'}), 404
    
    profile = UserProfile.objects(user_id=str(current_user.id)).first()
    
    try:
        prediction = calculate_prediction(hackathon, profile, str(current_user.id))
        return jsonify({'prediction': prediction.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


@success_prediction_bp.route('/batch-predict', methods=['POST'])
@login_required
def batch_predict():
    """Get predictions for multiple hackathons"""
    data = request.get_json()
    hackathon_ids = data.get('hackathon_ids', [])
    
    if not hackathon_ids:
        return jsonify({'error': 'hackathon_ids required'}), 400
    
    profile = UserProfile.objects(user_id=str(current_user.id)).first()
    predictions = []
    
    for hid in hackathon_ids[:10]:  # Limit to 10
        hackathon = Hackathon.objects(id=hid).first()
        if hackathon:
            try:
                pred = calculate_prediction(hackathon, profile, str(current_user.id))
                predictions.append({
                    'hackathon_id': hid,
                    'hackathon_name': hackathon.name,
                    'acceptance_probability': pred.acceptance_probability,
                    'win_probability': pred.win_probability,
                    'recommendation': get_recommendation_text(pred.acceptance_probability)
                })
            except:
                continue
    
    # Sort by acceptance probability
    predictions.sort(key=lambda x: x['acceptance_probability'], reverse=True)
    
    return jsonify({'predictions': predictions}), 200


@success_prediction_bp.route('/hackathon-stats/<hackathon_id>', methods=['GET'])
@login_required
def get_hackathon_stats(hackathon_id):
    """Get historical stats for a hackathon"""
    hackathon = Hackathon.objects(id=hackathon_id).first()
    if not hackathon:
        return jsonify({'error': 'Hackathon not found'}), 404
    
    stats = HackathonStats.objects(hackathon_id=hackathon_id).first()
    
    if not stats:
        # Generate estimated stats
        stats = estimate_hackathon_stats(hackathon)
    
    return jsonify({'stats': stats.to_dict()}), 200


@success_prediction_bp.route('/improve-chances', methods=['GET'])
@login_required
def get_improvement_suggestions():
    """Get suggestions to improve acceptance chances"""
    hackathon_id = request.args.get('hackathon_id')
    
    if not hackathon_id:
        return jsonify({'error': 'hackathon_id required'}), 400
    
    hackathon = Hackathon.objects(id=hackathon_id).first()
    if not hackathon:
        return jsonify({'error': 'Hackathon not found'}), 404
    
    profile = UserProfile.objects(user_id=str(current_user.id)).first()
    
    try:
        ai = AIService()
        suggestions = generate_improvement_suggestions(hackathon, profile, ai)
        return jsonify({'suggestions': suggestions}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def calculate_prediction(hackathon, profile, user_id):
    """Calculate success prediction using multiple factors"""
    scores = {
        'skill_match': 0,
        'experience': 0,
        'past_performance': 0,
        'competition_level': 50  # Default medium competition
    }
    
    strengths = []
    weaknesses = []
    recommendations = []
    
    # 1. Skill Match Score
    if profile and hackathon.required_skills:
        user_skills = set(profile.skills or [])
        required_skills = set(hackathon.required_skills)
        
        if required_skills:
            match_percent = len(user_skills.intersection(required_skills)) / len(required_skills)
            scores['skill_match'] = match_percent * 100
            
            if match_percent >= 0.7:
                strengths.append(f"Strong skill match ({int(match_percent*100)}%)")
            elif match_percent < 0.3:
                weaknesses.append("Missing key required skills")
                missing = required_skills - user_skills
                recommendations.append(f"Learn: {', '.join(list(missing)[:3])}")
    else:
        scores['skill_match'] = 70  # Default if no requirements
    
    # 2. Experience Score
    if profile:
        years = profile.years_of_experience or 0
        prev_hackathons = profile.previous_hackathons or 0
        
        exp_score = min(years * 10, 40) + min(prev_hackathons * 10, 60)
        scores['experience'] = min(exp_score, 100)
        
        if prev_hackathons >= 5:
            strengths.append(f"Experienced hackathon participant ({prev_hackathons} hackathons)")
        elif prev_hackathons == 0:
            weaknesses.append("No prior hackathon experience")
            recommendations.append("Join beginner-friendly hackathons first")
    else:
        scores['experience'] = 30
        weaknesses.append("Profile incomplete")
        recommendations.append("Complete your profile for better matches")
    
    # 3. Past Performance Score
    past_apps = Application.objects(user_id=user_id, status='submitted').count()
    wins = Application.objects(user_id=user_id, external_submitted=True).count()
    
    if past_apps > 0:
        win_rate = wins / past_apps
        scores['past_performance'] = min(win_rate * 200, 100)  # 50% win rate = 100 score
        
        if win_rate >= 0.3:
            strengths.append(f"Good track record ({int(win_rate*100)}% success rate)")
    else:
        scores['past_performance'] = 50  # Neutral for new users
    
    # 4. Competition Level (estimated)
    # Lower score = more competitive = harder to win
    if hackathon.prize:
        try:
            prize_amount = float(''.join(filter(str.isdigit, str(hackathon.prize))))
            if prize_amount > 10000:
                scores['competition_level'] = 80  # High competition
            elif prize_amount > 1000:
                scores['competition_level'] = 60  # Medium
            else:
                scores['competition_level'] = 40  # Lower competition
        except:
            scores['competition_level'] = 50
    
    # Calculate final probabilities
    base_acceptance = (
        scores['skill_match'] * 0.3 +
        scores['experience'] * 0.3 +
        scores['past_performance'] * 0.2 +
        (100 - scores['competition_level']) * 0.2  # Inverse - less competition = better
    )
    
    # Adjust acceptance probability (most hackathons have high acceptance)
    acceptance_prob = min(base_acceptance * 0.8 + 20, 95)  # 20% base + score
    
    # Win probability is much lower
    win_prob = base_acceptance * 0.15  # About 15% of base at max
    
    # Add recommendations based on weaknesses
    if not recommendations:
        recommendations.append("Your profile looks competitive - apply with confidence!")
    
    # Create and save prediction
    prediction = SuccessPrediction(
        user_id=user_id,
        hackathon_id=str(hackathon.id),
        acceptance_probability=round(acceptance_prob, 1),
        win_probability=round(win_prob, 1),
        skill_match_score=round(scores['skill_match'], 1),
        experience_score=round(scores['experience'], 1),
        past_performance_score=round(scores['past_performance'], 1),
        competition_level=round(scores['competition_level'], 1),
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recommendations,
        confidence=75.0  # Model confidence
    )
    prediction.save()
    
    return prediction


def estimate_hackathon_stats(hackathon):
    """Estimate stats for a hackathon without historical data"""
    stats = HackathonStats(
        hackathon_id=str(hackathon.id),
        hackathon_name=hackathon.name,
        source=hackathon.source,
        total_applicants=500,  # Estimated
        total_accepted=400,  # Most hackathons accept widely
        acceptance_rate=0.8,
        avg_participant_experience=2.5,
        avg_team_size=3.5,
        total_submissions=100
    )
    
    # Estimate based on prize
    if hackathon.prize:
        try:
            prize_amount = float(''.join(filter(str.isdigit, str(hackathon.prize))))
            stats.total_prize_pool = prize_amount
            stats.prize_per_winner = prize_amount / 5  # Assume 5 prize categories
        except:
            pass
    
    stats.save()
    return stats


def get_recommendation_text(probability):
    """Get recommendation text based on probability"""
    if probability >= 80:
        return "Highly Recommended"
    elif probability >= 60:
        return "Good Fit"
    elif probability >= 40:
        return "Worth Trying"
    else:
        return "Challenge Yourself"


def generate_improvement_suggestions(hackathon, profile, ai):
    """Use AI to generate improvement suggestions"""
    profile_context = ""
    if profile:
        profile_context = f"""
User Skills: {profile.skills}
Experience: {profile.years_of_experience} years
Previous Hackathons: {profile.previous_hackathons}
"""
    
    prompt = f"""For hackathon "{hackathon.name}" with requirements: {hackathon.required_skills or 'Not specified'}
Theme: {hackathon.themes or hackathon.tags}

{profile_context}

Give 5 specific, actionable suggestions to improve their chances of winning.
Return as JSON array with 'suggestion' and 'priority' (high/medium/low) keys."""
    
    messages = [
        {"role": "system", "content": "You're a hackathon coach. Give practical advice. Respond with valid JSON only."},
        {"role": "user", "content": prompt}
    ]
    
    response = ai._call_groq(messages, temperature=0.6)
    
    import json
    try:
        return json.loads(response)
    except:
        return [{'suggestion': response, 'priority': 'medium'}]

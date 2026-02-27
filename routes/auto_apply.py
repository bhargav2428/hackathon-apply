"""
Auto Apply Routes - API endpoints for auto-apply functionality
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from models.user import User
from models.hackathon import Hackathon
from models.application import Application
from services.hackathon_monitor import hackathon_monitor

auto_apply_bp = Blueprint('auto_apply', __name__)


@auto_apply_bp.route('/settings', methods=['GET'])
@login_required
def get_auto_apply_settings():
    """Get user's auto-apply settings"""
    user = User.objects(id=current_user.id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "auto_apply_enabled": user.auto_apply_enabled,
        "telegram_chat_id": user.telegram_chat_id,
        "auto_apply_tags": user.auto_apply_tags or []
    })


@auto_apply_bp.route('/settings', methods=['PUT'])
@login_required
def update_auto_apply_settings():
    """Update user's auto-apply settings"""
    data = request.get_json()
    user = User.objects(id=current_user.id).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if 'auto_apply_enabled' in data:
        user.auto_apply_enabled = data['auto_apply_enabled']
    
    if 'telegram_chat_id' in data:
        user.telegram_chat_id = data['telegram_chat_id']
    
    if 'auto_apply_tags' in data:
        user.auto_apply_tags = data['auto_apply_tags']
    
    user.updated_at = datetime.utcnow()
    user.save()
    
    return jsonify({
        "success": True,
        "message": "Settings updated",
        "auto_apply_enabled": user.auto_apply_enabled,
        "telegram_chat_id": user.telegram_chat_id,
        "auto_apply_tags": user.auto_apply_tags or []
    })


@auto_apply_bp.route('/hackathon/<hackathon_id>', methods=['POST'])
@login_required
def auto_apply_to_hackathon(hackathon_id):
    """
    Manually trigger auto-apply for a specific hackathon
    This generates an AI idea and creates an application
    """
    result = hackathon_monitor.process_single_hackathon(hackathon_id, str(current_user.id))
    
    if result.get('success'):
        return jsonify(result)
    else:
        return jsonify(result), 400


@auto_apply_bp.route('/all', methods=['POST'])
@login_required
def auto_apply_to_all():
    """
    Auto-apply to all active hackathons that user hasn't applied to yet
    """
    result = hackathon_monitor.process_all_hackathons_for_user(str(current_user.id))
    
    if result.get('success'):
        return jsonify(result)
    else:
        return jsonify(result), 400


@auto_apply_bp.route('/monitor/start', methods=['POST'])
@login_required
def start_monitor():
    """Start the hackathon monitor service (admin only)"""
    user = User.objects(id=current_user.id).first()
    if not user or not user.is_admin:
        return jsonify({"error": "Admin access required"}), 403
    
    result = hackathon_monitor.start()
    return jsonify(result)


@auto_apply_bp.route('/monitor/stop', methods=['POST'])
@login_required
def stop_monitor():
    """Stop the hackathon monitor service (admin only)"""
    user = User.objects(id=current_user.id).first()
    if not user or not user.is_admin:
        return jsonify({"error": "Admin access required"}), 403
    
    result = hackathon_monitor.stop()
    return jsonify(result)


@auto_apply_bp.route('/monitor/status', methods=['GET'])
@login_required
def monitor_status():
    """Get hackathon monitor status"""
    return jsonify({
        "is_running": hackathon_monitor.is_running,
        "check_interval": hackathon_monitor.check_interval,
        "processed_count": len(hackathon_monitor._processed_hackathons)
    })


@auto_apply_bp.route('/test-telegram', methods=['POST'])
@login_required
def test_telegram():
    """Send a test Telegram message"""
    from services.notification_service import NotificationService
    
    user = User.objects(id=current_user.id).first()
    if not user or not user.telegram_chat_id:
        return jsonify({
            "success": False,
            "error": "Telegram chat ID not configured. Send /start to @YourBotName first."
        }), 400
    
    notification_service = NotificationService()
    result = notification_service.send_telegram(
        user.telegram_chat_id,
        "Test Notification",
        "🎉 Your Telegram notifications are working!\n\nYou will receive alerts when:\n• New hackathons are detected\n• AI generates project ideas\n• Applications are auto-submitted"
    )
    
    return jsonify(result)


@auto_apply_bp.route('/generate-idea/<hackathon_id>', methods=['POST'])
@login_required
def generate_idea_only(hackathon_id):
    """Generate a project idea for a hackathon without applying"""
    from services.ai_service import AIService
    from models.user_profile import UserProfile
    
    hackathon = Hackathon.objects(id=hackathon_id).first()
    if not hackathon:
        return jsonify({"error": "Hackathon not found"}), 404
    
    profile = UserProfile.objects(user_id=str(current_user.id)).first()
    
    ai_service = AIService()
    idea = ai_service.generate_project_idea(hackathon, profile)
    
    return jsonify({
        "success": True,
        "hackathon": hackathon.name,
        "idea": idea
    })

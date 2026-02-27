"""Application Routes - MongoDB"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.application import Application
from models.hackathon import Hackathon

applications_bp = Blueprint('applications', __name__)


@applications_bp.route('', methods=['GET'])
@login_required
def get_applications():
    status = request.args.get('status')
    query = {'user_id': str(current_user.id)}
    if status:
        query['status'] = status
    
    applications = Application.objects(**query).order_by('-created_at')
    return jsonify({
        'applications': [a.to_dict() for a in applications]
    }), 200


@applications_bp.route('', methods=['POST'])
@login_required
def create_application():
    data = request.get_json()
    hackathon_id = data.get('hackathon_id')
    
    if not hackathon_id:
        return jsonify({'error': 'hackathon_id is required'}), 400
    
    hackathon = Hackathon.objects(id=hackathon_id).first()
    if not hackathon:
        return jsonify({'error': 'Hackathon not found'}), 404
    
    existing = Application.objects(user_id=str(current_user.id), hackathon_id=hackathon_id).first()
    if existing:
        return jsonify({'error': 'Already applied to this hackathon'}), 409
    
    application = Application(
        user_id=str(current_user.id),
        hackathon_id=hackathon_id,
        hackathon_name=hackathon.name
    )
    
    # Save generated idea if provided
    if data.get('generated_idea'):
        application.generated_project_idea = data['generated_idea']
        application.status = 'auto_generated'
    
    application.save()
    
    return jsonify({'message': 'Application created', 'application': application.to_dict()}), 201


@applications_bp.route('/<app_id>', methods=['GET'])
@login_required
def get_application(app_id):
    application = Application.objects(id=app_id, user_id=str(current_user.id)).first()
    if not application:
        return jsonify({'error': 'Application not found'}), 404
    return jsonify(application.to_dict()), 200


@applications_bp.route('/<app_id>/generate', methods=['POST'])
@login_required
def generate_content(app_id):
    application = Application.objects(id=app_id, user_id=str(current_user.id)).first()
    if not application:
        return jsonify({'error': 'Application not found'}), 404
    
    from services.ai_service import AIService
    from models.user_profile import UserProfile
    
    ai = AIService()
    hackathon = Hackathon.objects(id=application.hackathon_id).first()
    profile = UserProfile.objects(user_id=str(current_user.id)).first()
    
    try:
        idea = ai.generate_project_idea(hackathon, profile)
        application.generated_project_idea = str(idea)
        
        motivation = ai.generate_motivation(hackathon, profile)
        application.generated_motivation = motivation
        
        application.save()
        return jsonify({'message': 'Content generated', 'application': application.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@applications_bp.route('/<app_id>/submit', methods=['POST'])
@login_required
def submit_application(app_id):
    """Submit an application - marks it as submitted"""
    from datetime import datetime
    from services.notification_service import NotificationService
    
    application = Application.objects(id=app_id, user_id=str(current_user.id)).first()
    if not application:
        return jsonify({'error': 'Application not found'}), 404
    
    hackathon = Hackathon.objects(id=application.hackathon_id).first()
    
    # Generate content if not already generated
    if not application.generated_project_idea:
        try:
            from services.ai_service import AIService
            from models.user_profile import UserProfile
            
            ai = AIService()
            profile = UserProfile.objects(user_id=str(current_user.id)).first()
            
            idea = ai.generate_project_idea(hackathon, profile)
            application.generated_project_idea = str(idea)
            
            motivation = ai.generate_motivation(hackathon, profile)
            application.generated_motivation = motivation
        except Exception as e:
            print(f"Error generating content: {e}")
    
    # Mark as submitted
    application.status = 'submitted'
    application.is_auto_applied = True
    application.submitted_at = datetime.utcnow()
    application.updated_at = datetime.utcnow()
    application.save()
    
    # Send notification
    try:
        notification_service = NotificationService()
        from models.user import User
        user = User.objects(id=current_user.id).first()
        
        if user and user.telegram_chat_id:
            notification_service.send_telegram(
                user.telegram_chat_id,
                "Application Submitted! 🎉",
                f"Your application to *{hackathon.name if hackathon else 'Unknown Hackathon'}* has been submitted successfully!\n\nCheck the hackathon website to complete any remaining steps."
            )
    except Exception as e:
        print(f"Error sending notification: {e}")
    
    return jsonify({
        'message': 'Application submitted successfully',
        'application': application.to_dict()
    }), 200


@applications_bp.route('/<app_id>/auto-apply', methods=['POST'])
@login_required
def auto_apply(app_id):
    application = Application.objects(id=app_id, user_id=str(current_user.id)).first()
    if not application:
        return jsonify({'error': 'Application not found'}), 404
    
    from services.auto_apply import AutoApplyBot
    from models.user_profile import UserProfile
    import asyncio
    
    hackathon = Hackathon.objects(id=application.hackathon_id).first()
    profile = UserProfile.objects(user_id=str(current_user.id)).first()
    
    if not hackathon:
        return jsonify({'error': 'Hackathon not found'}), 404
    
    try:
        bot = AutoApplyBot()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(bot.apply(hackathon, profile, application))
        loop.close()
        
        if result.get('success'):
            application.mark_submitted(auto=True)
            return jsonify({'message': 'Applied successfully', 'result': result}), 200
        else:
            application.mark_error(result.get('error', 'Unknown error'))
            return jsonify({'error': result.get('error')}), 500
    except Exception as e:
        application.mark_error(str(e))
        return jsonify({'error': str(e)}), 500


@applications_bp.route('/<app_id>/confirm-external', methods=['POST'])
@login_required
def confirm_external_submission(app_id):
    """
    Confirm that user has actually submitted on the hackathon website.
    This is a manual confirmation to track real submissions.
    """
    application = Application.objects(id=app_id, user_id=str(current_user.id)).first()
    if not application:
        return jsonify({'error': 'Application not found'}), 404
    
    data = request.get_json() or {}
    confirmation = data.get('confirmation', '')  # Optional confirmation number/notes
    
    # Mark as externally submitted
    application.mark_external_submitted(confirmation=confirmation)
    
    # Also mark as submitted if not already
    if application.status not in ['submitted', 'accepted']:
        application.status = 'submitted'
        application.save()
    
    return jsonify({
        'message': 'External submission confirmed! Good luck with your hackathon!',
        'application': application.to_dict()
    }), 200

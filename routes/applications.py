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
    
    # Filter out applications with missing hackathons and enrich with hackathon data
    result = []
    for app in applications:
        app_dict = app.to_dict()
        hackathon = Hackathon.objects(id=app.hackathon_id).first()
        if hackathon:
            app_dict['hackathon_url'] = getattr(hackathon, 'registration_url', None) or hackathon.url
            app_dict['hackathon_exists'] = True
            result.append(app_dict)
        else:
            # Skip orphaned applications or mark them
            app_dict['hackathon_exists'] = False
            app_dict['hackathon_url'] = None
            # Optionally delete orphaned apps
            # app.delete()
    
    return jsonify({
        'applications': result
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
    
    app_dict = application.to_dict()
    
    # Add hackathon details
    hackathon = Hackathon.objects(id=application.hackathon_id).first()
    if hackathon:
        app_dict['hackathon_url'] = getattr(hackathon, 'registration_url', None) or hackathon.url
        app_dict['hackathon_exists'] = True
        app_dict['hackathon_description'] = hackathon.description
    else:
        app_dict['hackathon_url'] = None
        app_dict['hackathon_exists'] = False
    
    return jsonify(app_dict), 200


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
    """Submit an application - attempts real auto-apply on hackathon website"""
    from datetime import datetime
    from services.notification_service import NotificationService
    from models.user_profile import UserProfile
    
    application = Application.objects(id=app_id, user_id=str(current_user.id)).first()
    if not application:
        return jsonify({'error': 'Application not found'}), 404
    
    hackathon = Hackathon.objects(id=application.hackathon_id).first()
    if not hackathon:
        # Hackathon was deleted - clean up this orphaned application
        application.delete()
        return jsonify({'error': 'Hackathon no longer exists. Application has been removed.'}), 404
    
    profile = UserProfile.objects(user_id=str(current_user.id)).first()
    
    # Generate AI content if not already generated
    if not application.generated_project_idea:
        try:
            from services.ai_service import AIService
            ai = AIService()
            
            idea = ai.generate_project_idea(hackathon, profile)
            application.generated_project_idea = str(idea)
            
            motivation = ai.generate_motivation(hackathon, profile)
            application.generated_motivation = motivation
            application.save()
        except Exception as e:
            print(f"Error generating content: {e}")
    
    # Attempt real auto-apply using browser automation
    auto_apply_result = None
    try:
        from services.auto_apply import AutoApplyBot
        bot = AutoApplyBot()
        auto_apply_result = bot.apply(hackathon, profile, application)
        
        if auto_apply_result.get('success'):
            application.status = 'submitted'
            application.is_auto_applied = True
            application.submitted_at = datetime.utcnow()
            application.auto_apply_result = str(auto_apply_result)
            application.save()
            
            # Send success notification
            try:
                notification_service = NotificationService()
                from models.user import User
                user = User.objects(id=current_user.id).first()
                
                if user and user.telegram_chat_id:
                    notification_service.send_telegram(
                        user.telegram_chat_id,
                        "🎉 Auto-Applied Successfully!",
                        f"Your application to *{hackathon.name}* was automatically submitted!\n\n✅ The bot filled out the form and registered you."
                    )
            except:
                pass
            
            return jsonify({
                'message': 'Successfully auto-applied to hackathon!',
                'auto_applied': True,
                'application': application.to_dict(),
                'result': auto_apply_result
            }), 200
    except Exception as e:
        print(f"Auto-apply failed: {e}")
        auto_apply_result = {'success': False, 'error': str(e)}
    
    # If auto-apply failed or not available, mark as tracked and return URL
    application.status = 'submitted'
    application.submitted_at = datetime.utcnow()
    application.save()
    
    return jsonify({
        'message': 'Application tracked. Auto-apply not available - please complete registration manually.',
        'auto_applied': False,
        'manual_url': (getattr(hackathon, 'registration_url', None) or hackathon.url) if hackathon else None,
        'application': application.to_dict(),
        'auto_apply_error': auto_apply_result.get('error') if auto_apply_result else 'Auto-apply not available'
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

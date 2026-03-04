"""
Alerts Routes - WhatsApp/SMS/Email deadline alerts
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models.alerts import AlertSettings, AlertLog
from models.hackathon import Hackathon
from models.application import Application
import os
import requests

alerts_bp = Blueprint('alerts', __name__)


@alerts_bp.route('/settings', methods=['GET'])
@login_required
def get_alert_settings():
    """Get user's alert settings"""
    settings = AlertSettings.objects(user_id=str(current_user.id)).first()
    
    if not settings:
        # Create default settings
        settings = AlertSettings(user_id=str(current_user.id))
        settings.save()
    
    return jsonify({'settings': settings.to_dict()}), 200


@alerts_bp.route('/settings', methods=['PUT'])
@login_required
def update_alert_settings():
    """Update user's alert settings"""
    data = request.get_json()
    
    settings = AlertSettings.objects(user_id=str(current_user.id)).first()
    if not settings:
        settings = AlertSettings(user_id=str(current_user.id))
    
    # Update fields
    fields = [
        'phone_number', 'whatsapp_enabled', 'sms_enabled', 'email_enabled',
        'telegram_enabled', 'telegram_chat_id', 'alert_24h', 'alert_6h', 'alert_1h',
        'custom_alert_hours', 'alert_deadlines', 'alert_new_hackathons',
        'alert_team_matches', 'alert_application_status', 'timezone',
        'quiet_hours_start', 'quiet_hours_end'
    ]
    
    for field in fields:
        if field in data:
            setattr(settings, field, data[field])
    
    settings.updated_at = datetime.utcnow()
    settings.save()
    
    return jsonify({'settings': settings.to_dict()}), 200


@alerts_bp.route('/test', methods=['POST'])
@login_required
def send_test_alert():
    """Send a test alert to verify settings"""
    data = request.get_json()
    channel = data.get('channel', 'email')  # email, sms, whatsapp, telegram
    
    settings = AlertSettings.objects(user_id=str(current_user.id)).first()
    if not settings:
        return jsonify({'error': 'Please configure alert settings first'}), 400
    
    test_message = "🔔 Test Alert from Hackathon Auto Apply Agent! Your alerts are working correctly."
    
    result = send_alert(
        user_id=str(current_user.id),
        channel=channel,
        message=test_message,
        alert_type='custom'
    )
    
    if result['success']:
        return jsonify({'message': f'Test alert sent via {channel}'}), 200
    else:
        return jsonify({'error': result['error']}), 400


@alerts_bp.route('/logs', methods=['GET'])
@login_required
def get_alert_logs():
    """Get user's alert history"""
    limit = int(request.args.get('limit', 50))
    logs = AlertLog.objects(user_id=str(current_user.id)).order_by('-sent_at').limit(limit)
    return jsonify({'logs': [log.to_dict() for log in logs]}), 200


@alerts_bp.route('/upcoming-deadlines', methods=['GET'])
@login_required
def get_upcoming_deadlines():
    """Get hackathons with upcoming deadlines that need alerts"""
    hours = int(request.args.get('hours', 24))
    
    now = datetime.utcnow()
    deadline_threshold = now + timedelta(hours=hours)
    
    # Get user's applied hackathons
    applications = Application.objects(user_id=str(current_user.id))
    applied_hackathon_ids = [app.hackathon_id for app in applications]
    
    # Get hackathons with upcoming deadlines
    upcoming = Hackathon.objects(
        deadline__gte=now,
        deadline__lte=deadline_threshold,
        id__in=applied_hackathon_ids
    ).order_by('deadline')
    
    return jsonify({
        'deadlines': [{
            'hackathon_id': str(h.id),
            'name': h.name,
            'deadline': h.deadline.isoformat() if h.deadline else None,
            'hours_remaining': (h.deadline - now).total_seconds() / 3600 if h.deadline else None
        } for h in upcoming]
    }), 200


@alerts_bp.route('/send-deadline-alerts', methods=['POST'])
@login_required
def trigger_deadline_alerts():
    """Manually trigger deadline alerts (admin or scheduler)"""
    # This would typically be called by a scheduler
    sent_count = process_deadline_alerts()
    return jsonify({'message': f'Sent {sent_count} alerts'}), 200


def send_alert(user_id, channel, message, alert_type='custom', hackathon_id=None):
    """Send an alert through specified channel"""
    settings = AlertSettings.objects(user_id=user_id).first()
    if not settings:
        return {'success': False, 'error': 'No alert settings configured'}
    
    result = {'success': False, 'error': 'Unknown channel'}
    
    # Log the alert
    log = AlertLog(
        user_id=user_id,
        hackathon_id=hackathon_id,
        alert_type=alert_type,
        channel=channel,
        message=message,
        status='pending'
    )
    
    try:
        if channel == 'telegram' and settings.telegram_enabled:
            result = send_telegram_alert(settings.telegram_chat_id, message)
        elif channel == 'email' and settings.email_enabled:
            result = send_email_alert(user_id, message)
        elif channel == 'whatsapp' and settings.whatsapp_enabled:
            result = send_whatsapp_alert(settings.phone_number, message)
        elif channel == 'sms' and settings.sms_enabled:
            result = send_sms_alert(settings.phone_number, message)
        else:
            result = {'success': False, 'error': f'{channel} not enabled'}
        
        log.status = 'sent' if result['success'] else 'failed'
        if not result['success']:
            log.error_message = result.get('error', 'Unknown error')
        else:
            log.delivered_at = datetime.utcnow()
            
    except Exception as e:
        log.status = 'failed'
        log.error_message = str(e)
        result = {'success': False, 'error': str(e)}
    
    log.save()
    return result


def send_telegram_alert(chat_id, message):
    """Send alert via Telegram"""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        return {'success': False, 'error': 'Telegram bot not configured'}
    
    if not chat_id:
        return {'success': False, 'error': 'Telegram chat ID not set'}
    
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.ok:
            return {'success': True}
        else:
            return {'success': False, 'error': response.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def send_email_alert(user_id, message):
    """Send alert via Email (placeholder - implement with your email service)"""
    # TODO: Implement with SendGrid, AWS SES, or similar
    # For now, log it
    print(f"[EMAIL] To user {user_id}: {message}")
    return {'success': True, 'note': 'Email simulated (configure email service)'}


def send_whatsapp_alert(phone_number, message):
    """Send alert via WhatsApp (using Twilio or similar)"""
    # TODO: Implement with Twilio WhatsApp API
    # Account SID and Auth Token from twilio.com/console
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')
    
    if not all([account_sid, auth_token, from_number]):
        return {'success': False, 'error': 'Twilio not configured'}
    
    if not phone_number:
        return {'success': False, 'error': 'Phone number not set'}
    
    # Twilio WhatsApp API
    url = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'
    
    try:
        response = requests.post(
            url,
            auth=(account_sid, auth_token),
            data={
                'From': f'whatsapp:{from_number}',
                'To': f'whatsapp:{phone_number}',
                'Body': message
            },
            timeout=10
        )
        
        if response.ok:
            return {'success': True}
        else:
            return {'success': False, 'error': response.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def send_sms_alert(phone_number, message):
    """Send alert via SMS (using Twilio or similar)"""
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_number = os.environ.get('TWILIO_PHONE_NUMBER')
    
    if not all([account_sid, auth_token, from_number]):
        return {'success': False, 'error': 'Twilio not configured'}
    
    if not phone_number:
        return {'success': False, 'error': 'Phone number not set'}
    
    url = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'
    
    try:
        response = requests.post(
            url,
            auth=(account_sid, auth_token),
            data={
                'From': from_number,
                'To': phone_number,
                'Body': message
            },
            timeout=10
        )
        
        if response.ok:
            return {'success': True}
        else:
            return {'success': False, 'error': response.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def process_deadline_alerts():
    """Process and send deadline alerts for all users"""
    now = datetime.utcnow()
    sent_count = 0
    
    # Get all users with alert settings
    all_settings = AlertSettings.objects(alert_deadlines=True)
    
    for settings in all_settings:
        # Determine which deadlines to check
        hours_to_check = []
        if settings.alert_24h:
            hours_to_check.append(24)
        if settings.alert_6h:
            hours_to_check.append(6)
        if settings.alert_1h:
            hours_to_check.append(1)
        hours_to_check.extend(settings.custom_alert_hours or [])
        
        for hours in hours_to_check:
            # Find hackathons with deadlines in this window (±30 minutes)
            window_start = now + timedelta(hours=hours, minutes=-30)
            window_end = now + timedelta(hours=hours, minutes=30)
            
            # Get user's applied hackathons
            applications = Application.objects(user_id=settings.user_id)
            applied_ids = [app.hackathon_id for app in applications]
            
            # Find matching hackathons
            hackathons = Hackathon.objects(
                id__in=applied_ids,
                deadline__gte=window_start,
                deadline__lte=window_end
            )
            
            for hackathon in hackathons:
                # Check if we already sent this alert
                existing_alert = AlertLog.objects(
                    user_id=settings.user_id,
                    hackathon_id=str(hackathon.id),
                    alert_type='deadline',
                    sent_at__gte=now - timedelta(hours=1)
                ).first()
                
                if not existing_alert:
                    message = f"⏰ Deadline Alert!\n\n'{hackathon.name}' deadline is in {hours} hour(s)!\n\nDon't miss your chance to submit."
                    
                    # Send through enabled channels
                    for channel in ['telegram', 'email', 'whatsapp', 'sms']:
                        channel_enabled = getattr(settings, f'{channel}_enabled', False)
                        if channel_enabled:
                            send_alert(
                                user_id=settings.user_id,
                                channel=channel,
                                message=message,
                                alert_type='deadline',
                                hackathon_id=str(hackathon.id)
                            )
                            sent_count += 1
    
    return sent_count

"""
Calendar Sync Routes - Sync hackathons to Google/Outlook calendars
"""
from flask import Blueprint, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models.calendar_sync import CalendarSync, CalendarEvent
from models.hackathon import Hackathon
from models.application import Application
import os
import json

calendar_sync_bp = Blueprint('calendar_sync', __name__)


@calendar_sync_bp.route('/settings', methods=['GET'])
@login_required
def get_calendar_settings():
    """Get user's calendar sync settings"""
    settings = CalendarSync.objects(user_id=str(current_user.id)).first()
    if not settings:
        settings = CalendarSync(user_id=str(current_user.id))
        settings.save()
    return jsonify({'settings': settings.to_dict()}), 200


@calendar_sync_bp.route('/settings', methods=['PUT'])
@login_required
def update_calendar_settings():
    """Update calendar sync settings"""
    data = request.get_json()
    
    settings = CalendarSync.objects(user_id=str(current_user.id)).first()
    if not settings:
        settings = CalendarSync(user_id=str(current_user.id))
    
    for field in ['auto_sync', 'sync_applied_only', 'add_hackathon_dates',
                  'add_deadline_reminders', 'add_prep_blocks', 'prep_hours_before',
                  'event_color', 'reminder_minutes']:
        if field in data:
            setattr(settings, field, data[field])
    
    settings.save()
    return jsonify({'settings': settings.to_dict()}), 200


@calendar_sync_bp.route('/google/auth', methods=['GET'])
@login_required
def google_calendar_auth():
    """Initiate Google Calendar OAuth flow"""
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/api/calendar/google/callback')
    
    if not client_id:
        return jsonify({'error': 'Google Calendar not configured'}), 400
    
    scope = 'https://www.googleapis.com/auth/calendar.events'
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&response_type=code&access_type=offline"
    
    return jsonify({'auth_url': auth_url}), 200


@calendar_sync_bp.route('/google/callback', methods=['GET'])
@login_required
def google_calendar_callback():
    """Handle Google OAuth callback"""
    code = request.args.get('code')
    
    if not code:
        return jsonify({'error': 'Authorization failed'}), 400
    
    # Exchange code for token
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI')
    
    import requests
    token_response = requests.post('https://oauth2.googleapis.com/token', data={
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri
    })
    
    if token_response.ok:
        tokens = token_response.json()
        
        # Save tokens
        settings = CalendarSync.objects(user_id=str(current_user.id)).first()
        if not settings:
            settings = CalendarSync(user_id=str(current_user.id))
        
        settings.google_calendar_connected = True
        settings.google_calendar_token = json.dumps(tokens)  # TODO: Encrypt
        settings.save()
        
        return redirect('/dashboard?calendar=connected')
    else:
        return jsonify({'error': 'Failed to get access token'}), 400


@calendar_sync_bp.route('/google/disconnect', methods=['POST'])
@login_required
def disconnect_google():
    """Disconnect Google Calendar"""
    settings = CalendarSync.objects(user_id=str(current_user.id)).first()
    if settings:
        settings.google_calendar_connected = False
        settings.google_calendar_token = None
        settings.save()
    return jsonify({'message': 'Google Calendar disconnected'}), 200


@calendar_sync_bp.route('/sync', methods=['POST'])
@login_required
def sync_to_calendar():
    """Sync hackathons to connected calendars"""
    data = request.get_json() or {}
    hackathon_ids = data.get('hackathon_ids')  # Optional: specific hackathons
    
    settings = CalendarSync.objects(user_id=str(current_user.id)).first()
    if not settings:
        return jsonify({'error': 'Calendar not configured'}), 400
    
    if not settings.google_calendar_connected and not settings.outlook_connected:
        return jsonify({'error': 'No calendar connected'}), 400
    
    # Get hackathons to sync
    if hackathon_ids:
        hackathons = Hackathon.objects(id__in=hackathon_ids)
    elif settings.sync_applied_only:
        # Only sync applied hackathons
        apps = Application.objects(user_id=str(current_user.id))
        applied_ids = [app.hackathon_id for app in apps]
        hackathons = Hackathon.objects(id__in=applied_ids)
    else:
        # Sync all active hackathons
        hackathons = Hackathon.objects(deadline__gte=datetime.utcnow())
    
    synced_count = 0
    
    for hackathon in hackathons:
        try:
            if settings.google_calendar_connected:
                sync_to_google(settings, hackathon, str(current_user.id))
                synced_count += 1
        except Exception as e:
            print(f"Error syncing {hackathon.name}: {e}")
            continue
    
    settings.last_synced = datetime.utcnow()
    settings.save()
    
    return jsonify({
        'message': f'Synced {synced_count} hackathons to calendar',
        'synced_count': synced_count
    }), 200


@calendar_sync_bp.route('/events', methods=['GET'])
@login_required
def get_synced_events():
    """Get list of synced calendar events"""
    events = CalendarEvent.objects(user_id=str(current_user.id)).order_by('-start_time')
    return jsonify({'events': [e.to_dict() for e in events]}), 200


@calendar_sync_bp.route('/export-ics/<hackathon_id>', methods=['GET'])
@login_required
def export_ics(hackathon_id):
    """Export hackathon as ICS file for manual calendar import"""
    hackathon = Hackathon.objects(id=hackathon_id).first()
    if not hackathon:
        return jsonify({'error': 'Hackathon not found'}), 404
    
    ics_content = generate_ics(hackathon)
    
    from flask import Response
    return Response(
        ics_content,
        mimetype='text/calendar',
        headers={'Content-Disposition': f'attachment; filename={hackathon.name.replace(" ", "_")}.ics'}
    )


def sync_to_google(settings, hackathon, user_id):
    """Sync a hackathon to Google Calendar"""
    if not settings.google_calendar_token:
        return False
    
    tokens = json.loads(settings.google_calendar_token)
    access_token = tokens.get('access_token')
    
    # Check if event already exists
    existing = CalendarEvent.objects(
        user_id=user_id,
        hackathon_id=str(hackathon.id),
        event_type='hackathon'
    ).first()
    
    # Prepare event data
    event_data = {
        'summary': f"🚀 {hackathon.name}",
        'description': f"{hackathon.description or ''}\n\nURL: {hackathon.url or hackathon.registration_url or ''}",
        'colorId': '9',  # Blue
    }
    
    if hackathon.deadline:
        event_data['start'] = {'dateTime': hackathon.deadline.isoformat() + 'Z'}
        event_data['end'] = {'dateTime': (hackathon.deadline + timedelta(hours=2)).isoformat() + 'Z'}
    else:
        # All-day event
        event_data['start'] = {'date': datetime.utcnow().strftime('%Y-%m-%d')}
        event_data['end'] = {'date': (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')}
    
    # Add reminder
    event_data['reminders'] = {
        'useDefault': False,
        'overrides': [
            {'method': 'popup', 'minutes': 1440},  # 1 day before
            {'method': 'popup', 'minutes': 60}     # 1 hour before
        ]
    }
    
    import requests
    headers = {'Authorization': f'Bearer {access_token}'}
    
    calendar_id = settings.google_calendar_id or 'primary'
    
    if existing and existing.google_event_id:
        # Update existing event
        url = f'https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{existing.google_event_id}'
        response = requests.put(url, headers=headers, json=event_data)
    else:
        # Create new event
        url = f'https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events'
        response = requests.post(url, headers=headers, json=event_data)
    
    if response.ok:
        event_result = response.json()
        
        # Save to our database
        if existing:
            existing.google_event_id = event_result.get('id')
            existing.synced_at = datetime.utcnow()
            existing.save()
        else:
            CalendarEvent(
                user_id=user_id,
                hackathon_id=str(hackathon.id),
                google_event_id=event_result.get('id'),
                event_type='hackathon',
                title=hackathon.name,
                description=hackathon.description,
                start_time=hackathon.deadline,
                end_time=hackathon.deadline + timedelta(hours=2) if hackathon.deadline else None
            ).save()
        
        return True
    
    return False


def generate_ics(hackathon):
    """Generate ICS file content for a hackathon"""
    from datetime import datetime
    
    uid = f"hackathon-{hackathon.id}@hackathon-agent"
    dtstamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    
    if hackathon.deadline:
        dtstart = hackathon.deadline.strftime('%Y%m%dT%H%M%SZ')
        dtend = (hackathon.deadline + timedelta(hours=2)).strftime('%Y%m%dT%H%M%SZ')
    else:
        dtstart = datetime.utcnow().strftime('%Y%m%d')
        dtend = (datetime.utcnow() + timedelta(days=1)).strftime('%Y%m%d')
    
    description = (hackathon.description or '').replace('\n', '\\n')
    url = hackathon.url or hackathon.registration_url or ''
    
    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Hackathon Auto Apply Agent//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:🚀 {hackathon.name}
DESCRIPTION:{description}\\n\\nURL: {url}
URL:{url}
BEGIN:VALARM
TRIGGER:-P1D
ACTION:DISPLAY
DESCRIPTION:Hackathon deadline tomorrow!
END:VALARM
END:VEVENT
END:VCALENDAR"""
    
    return ics

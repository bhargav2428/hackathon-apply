"""Dashboard Routes - MongoDB"""
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from models.application import Application
from models.hackathon import Hackathon
from models.notification import Notification
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    user_id = str(current_user.id)
    
    total_applications = Application.objects(user_id=user_id).count()
    pending = Application.objects(user_id=user_id, status='pending').count()
    submitted = Application.objects(user_id=user_id, status='submitted').count()
    approved = Application.objects(user_id=user_id, status='approved').count()
    rejected = Application.objects(user_id=user_id, status='rejected').count()
    
    upcoming_hackathons = Hackathon.objects(
        deadline__gte=datetime.utcnow(),
        is_active=True
    ).count()
    
    unread_notifications = Notification.objects(user_id=user_id, is_read=False).count()
    
    return jsonify({
        'total_applications': total_applications,
        'pending': pending,
        'submitted': submitted,
        'approved': approved,
        'rejected': rejected,
        'upcoming_hackathons': upcoming_hackathons,
        'unread_notifications': unread_notifications
    }), 200


@dashboard_bp.route('/recent-applications', methods=['GET'])
@login_required
def get_recent_applications():
    applications = Application.objects(user_id=str(current_user.id)).order_by('-created_at')[:5]
    return jsonify({
        'applications': [a.to_dict() for a in applications]
    }), 200


@dashboard_bp.route('/upcoming-deadlines', methods=['GET'])
@login_required
def get_upcoming_deadlines():
    hackathons = Hackathon.objects(
        deadline__gte=datetime.utcnow(),
        is_active=True
    ).order_by('deadline')[:5]
    
    return jsonify({
        'hackathons': [h.to_dict() for h in hackathons]
    }), 200


@dashboard_bp.route('/activity', methods=['GET'])
@login_required
def get_activity():
    user_id = str(current_user.id)
    
    recent_apps = Application.objects(user_id=user_id).order_by('-updated_at')[:10]
    recent_notifs = Notification.objects(user_id=user_id).order_by('-created_at')[:10]
    
    activities = []
    for app in recent_apps:
        activities.append({
            'type': 'application',
            'message': f'Application to {app.hackathon_name} - {app.status}',
            'timestamp': app.updated_at.isoformat() if app.updated_at else app.created_at.isoformat()
        })
    
    for notif in recent_notifs:
        activities.append({
            'type': 'notification',
            'message': notif.message,
            'timestamp': notif.created_at.isoformat()
        })
    
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({
        'activities': activities[:20]
    }), 200

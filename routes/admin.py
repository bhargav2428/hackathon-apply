"""
Admin Routes - Admin dashboard and management APIs
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from functools import wraps
from models.admin import AdminUser, SystemStats, AdminAuditLog, FeatureFlag, SystemSetting
from models.user import User
from models.hackathon import Hackathon
from models.application import Application
from models.team_matching import TeamRequest
from models.roi_calculator import ROICalculation
from models.demo_script import DemoScript
from models.multi_language import TranslatedApplication

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin = AdminUser.objects(user_id=str(current_user.id), is_active=True).first()
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/check', methods=['GET'])
@login_required
def check_admin():
    """Check if current user is admin"""
    admin = AdminUser.objects(user_id=str(current_user.id), is_active=True).first()
    return jsonify({
        'is_admin': admin is not None,
        'role': admin.role if admin else None,
        'permissions': admin.permissions if admin else []
    }), 200


@admin_bp.route('/make-admin', methods=['POST'])
@login_required
def make_first_admin():
    """Create first admin (only works if no admins exist)"""
    existing_admins = AdminUser.objects().count()
    
    if existing_admins > 0:
        # Check if current user is super_admin
        admin = AdminUser.objects(user_id=str(current_user.id), role='super_admin').first()
        if not admin:
            return jsonify({'error': 'Only super admins can create new admins'}), 403
    
    data = request.get_json()
    target_user_id = data.get('user_id', str(current_user.id))
    role = data.get('role', 'admin')
    
    # Check if already admin
    existing = AdminUser.objects(user_id=target_user_id).first()
    if existing:
        return jsonify({'error': 'User is already an admin'}), 400
    
    admin = AdminUser(
        user_id=target_user_id,
        role=role if existing_admins == 0 else 'admin',  # First admin is super_admin
        permissions=['manage_users', 'manage_hackathons', 'view_analytics', 'manage_settings'],
        created_by=str(current_user.id) if existing_admins > 0 else None
    )
    admin.save()
    
    # Log action
    log_admin_action(str(current_user.id), 'create_admin', 'user', target_user_id)
    
    return jsonify({'admin': admin.to_dict()}), 201


@admin_bp.route('/stats', methods=['GET'])
@login_required
@admin_required
def get_system_stats():
    """Get system-wide statistics"""
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    
    stats = {
        # User stats
        'total_users': User.objects().count(),
        'active_users_24h': User.objects(last_login__gte=day_ago).count() if hasattr(User, 'last_login') else 0,
        'active_users_7d': User.objects(last_login__gte=week_ago).count() if hasattr(User, 'last_login') else 0,
        'new_users_today': User.objects(created_at__gte=day_ago).count() if hasattr(User, 'created_at') else 0,
        
        # Hackathon stats
        'total_hackathons': Hackathon.objects().count(),
        'active_hackathons': Hackathon.objects(deadline__gte=now).count(),
        'hackathons_ending_soon': Hackathon.objects(
            deadline__gte=now,
            deadline__lte=now + timedelta(days=7)
        ).count(),
        
        # Application stats
        'total_applications': Application.objects().count(),
        'applications_today': Application.objects(created_at__gte=day_ago).count(),
        'submitted_applications': Application.objects(status='submitted').count(),
        
        # Feature usage
        'team_matching_requests': TeamRequest.objects().count(),
        'roi_calculations': ROICalculation.objects().count(),
        'demo_scripts_generated': DemoScript.objects().count(),
        'translations_generated': TranslatedApplication.objects().count(),
        
        # By source breakdown
        'hackathons_by_source': get_hackathons_by_source(),
        
        # Recent activity
        'recent_applications': Application.objects().order_by('-created_at').limit(5).count()
    }
    
    # Save stats snapshot
    sys_stats = SystemStats(**stats)
    sys_stats.save()
    
    return jsonify({'stats': stats}), 200


@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """Get all users with stats"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    search = request.args.get('search')
    
    query = {}
    if search:
        query['email__icontains'] = search
    
    users = User.objects(**query).skip((page - 1) * per_page).limit(per_page)
    total = User.objects(**query).count()
    
    users_data = []
    for user in users:
        user_dict = {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
            'applications_count': Application.objects(user_id=str(user.id)).count(),
            'is_admin': AdminUser.objects(user_id=str(user.id)).first() is not None
        }
        users_data.append(user_dict)
    
    return jsonify({
        'users': users_data,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }), 200


@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user and their data"""
    if user_id == str(current_user.id):
        return jsonify({'error': 'Cannot delete yourself'}), 400
    
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Delete user's data
    Application.objects(user_id=user_id).delete()
    TeamRequest.objects(user_id=user_id).delete()
    
    # Delete user
    user.delete()
    
    # Log action
    log_admin_action(str(current_user.id), 'delete_user', 'user', user_id)
    
    return jsonify({'message': 'User deleted'}), 200


@admin_bp.route('/hackathons', methods=['GET'])
@login_required
@admin_required
def get_all_hackathons():
    """Get all hackathons with management info"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    source = request.args.get('source')
    
    query = {}
    if source:
        query['source'] = source
    
    hackathons = Hackathon.objects(**query).order_by('-created_at').skip((page - 1) * per_page).limit(per_page)
    total = Hackathon.objects(**query).count()
    
    hackathons_data = []
    for h in hackathons:
        h_dict = h.to_dict()
        h_dict['applications_count'] = Application.objects(hackathon_id=str(h.id)).count()
        hackathons_data.append(h_dict)
    
    return jsonify({
        'hackathons': hackathons_data,
        'total': total,
        'page': page,
        'per_page': per_page
    }), 200


@admin_bp.route('/hackathons/<hackathon_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_hackathon(hackathon_id):
    """Delete a hackathon"""
    hackathon = Hackathon.objects(id=hackathon_id).first()
    if not hackathon:
        return jsonify({'error': 'Hackathon not found'}), 404
    
    name = hackathon.name
    hackathon.delete()
    
    # Log action
    log_admin_action(str(current_user.id), 'delete_hackathon', 'hackathon', hackathon_id, {'name': name})
    
    return jsonify({'message': 'Hackathon deleted'}), 200


@admin_bp.route('/feature-flags', methods=['GET'])
@login_required
@admin_required
def get_feature_flags():
    """Get all feature flags"""
    flags = FeatureFlag.objects()
    return jsonify({'flags': [f.to_dict() for f in flags]}), 200


@admin_bp.route('/feature-flags', methods=['POST'])
@login_required
@admin_required
def create_feature_flag():
    """Create a new feature flag"""
    data = request.get_json()
    
    flag = FeatureFlag(
        name=data.get('name'),
        description=data.get('description'),
        is_enabled=data.get('is_enabled', True),
        rollout_percentage=data.get('rollout_percentage', 100),
        updated_by=str(current_user.id)
    )
    flag.save()
    
    return jsonify({'flag': flag.to_dict()}), 201


@admin_bp.route('/feature-flags/<flag_id>', methods=['PUT'])
@login_required
@admin_required
def update_feature_flag(flag_id):
    """Update a feature flag"""
    flag = FeatureFlag.objects(id=flag_id).first()
    if not flag:
        return jsonify({'error': 'Feature flag not found'}), 404
    
    data = request.get_json()
    
    for field in ['is_enabled', 'rollout_percentage', 'description', 'allowed_user_ids', 'blocked_user_ids']:
        if field in data:
            setattr(flag, field, data[field])
    
    flag.updated_by = str(current_user.id)
    flag.updated_at = datetime.utcnow()
    flag.save()
    
    # Log action
    log_admin_action(str(current_user.id), 'update_feature_flag', 'feature_flag', flag_id, data)
    
    return jsonify({'flag': flag.to_dict()}), 200


@admin_bp.route('/settings', methods=['GET'])
@login_required
@admin_required
def get_system_settings():
    """Get all system settings"""
    settings = SystemSetting.objects()
    return jsonify({'settings': [s.to_dict() for s in settings]}), 200


@admin_bp.route('/settings', methods=['POST'])
@login_required
@admin_required
def update_system_setting():
    """Create or update a system setting"""
    data = request.get_json()
    key = data.get('key')
    
    if not key:
        return jsonify({'error': 'key required'}), 400
    
    setting = SystemSetting.objects(key=key).first()
    if not setting:
        setting = SystemSetting(key=key)
    
    setting.value = data.get('value')
    setting.value_type = data.get('value_type', 'string')
    setting.description = data.get('description')
    setting.updated_by = str(current_user.id)
    setting.updated_at = datetime.utcnow()
    setting.save()
    
    return jsonify({'setting': setting.to_dict()}), 200


@admin_bp.route('/audit-logs', methods=['GET'])
@login_required
@admin_required
def get_audit_logs():
    """Get admin audit logs"""
    limit = int(request.args.get('limit', 100))
    action = request.args.get('action')
    
    query = {}
    if action:
        query['action'] = action
    
    logs = AdminAuditLog.objects(**query).order_by('-performed_at').limit(limit)
    return jsonify({'logs': [l.to_dict() for l in logs]}), 200


@admin_bp.route('/analytics/overview', methods=['GET'])
@login_required
@admin_required
def get_analytics_overview():
    """Get analytics overview for dashboard"""
    now = datetime.utcnow()
    
    # Daily stats for last 30 days
    daily_stats = []
    for i in range(30):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        stats = {
            'date': day_start.strftime('%Y-%m-%d'),
            'applications': Application.objects(
                created_at__gte=day_start,
                created_at__lt=day_end
            ).count(),
            'hackathons_added': Hackathon.objects(
                created_at__gte=day_start,
                created_at__lt=day_end
            ).count() if hasattr(Hackathon, 'created_at') else 0
        }
        daily_stats.append(stats)
    
    # Top hackathons by applications
    pipeline = [
        {'$group': {'_id': '$hackathon_id', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 10}
    ]
    
    top_hackathons = []
    try:
        results = Application.objects.aggregate(pipeline)
        for r in results:
            hackathon = Hackathon.objects(id=r['_id']).first()
            if hackathon:
                top_hackathons.append({
                    'name': hackathon.name,
                    'applications': r['count']
                })
    except:
        pass
    
    return jsonify({
        'daily_stats': daily_stats,
        'top_hackathons': top_hackathons
    }), 200


def get_hackathons_by_source():
    """Get hackathon count by source"""
    pipeline = [
        {'$group': {'_id': '$source', 'count': {'$sum': 1}}}
    ]
    
    try:
        results = Hackathon.objects.aggregate(pipeline)
        return {r['_id'] or 'Unknown': r['count'] for r in results}
    except:
        return {}


def log_admin_action(admin_user_id, action, target_type=None, target_id=None, details=None):
    """Log an admin action"""
    log = AdminAuditLog(
        admin_user_id=admin_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details or {},
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    log.save()

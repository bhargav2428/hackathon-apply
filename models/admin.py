"""
Admin Models - For admin dashboard and management
"""
from datetime import datetime
from mongoengine import Document, StringField, ListField, DateTimeField, DictField, BooleanField, IntField, FloatField


class AdminUser(Document):
    """Admin user with elevated permissions"""
    meta = {'collection': 'admin_users'}
    
    user_id = StringField(required=True, unique=True)
    
    role = StringField(default='admin', choices=['admin', 'super_admin', 'moderator'])
    
    permissions = ListField(StringField())  # ['manage_users', 'manage_hackathons', 'view_analytics', etc.]
    
    is_active = BooleanField(default=True)
    
    created_by = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    last_login = DateTimeField()
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'role': self.role,
            'permissions': self.permissions,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class SystemStats(Document):
    """System-wide statistics snapshot"""
    meta = {'collection': 'system_stats'}
    
    # User stats
    total_users = IntField(default=0)
    active_users_24h = IntField(default=0)
    active_users_7d = IntField(default=0)
    new_users_today = IntField(default=0)
    
    # Hackathon stats
    total_hackathons = IntField(default=0)
    active_hackathons = IntField(default=0)
    hackathons_ending_soon = IntField(default=0)
    
    # Application stats
    total_applications = IntField(default=0)
    applications_today = IntField(default=0)
    submitted_applications = IntField(default=0)
    
    # AI usage
    ai_generations_today = IntField(default=0)
    ai_generations_total = IntField(default=0)
    
    # Feature usage
    team_matching_requests = IntField(default=0)
    roi_calculations = IntField(default=0)
    demo_scripts_generated = IntField(default=0)
    translations_generated = IntField(default=0)
    
    # Alerts sent
    alerts_sent_today = IntField(default=0)
    
    recorded_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'total_users': self.total_users,
            'active_users_24h': self.active_users_24h,
            'active_users_7d': self.active_users_7d,
            'new_users_today': self.new_users_today,
            'total_hackathons': self.total_hackathons,
            'active_hackathons': self.active_hackathons,
            'hackathons_ending_soon': self.hackathons_ending_soon,
            'total_applications': self.total_applications,
            'applications_today': self.applications_today,
            'submitted_applications': self.submitted_applications,
            'ai_generations_today': self.ai_generations_today,
            'ai_generations_total': self.ai_generations_total,
            'team_matching_requests': self.team_matching_requests,
            'roi_calculations': self.roi_calculations,
            'demo_scripts_generated': self.demo_scripts_generated,
            'translations_generated': self.translations_generated,
            'alerts_sent_today': self.alerts_sent_today,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }


class AdminAuditLog(Document):
    """Audit log for admin actions"""
    meta = {'collection': 'admin_audit_logs'}
    
    admin_user_id = StringField(required=True)
    
    action = StringField(required=True)  # 'delete_user', 'modify_hackathon', etc.
    target_type = StringField()  # 'user', 'hackathon', 'application'
    target_id = StringField()
    
    details = DictField()  # Additional details about the action
    
    ip_address = StringField()
    user_agent = StringField()
    
    performed_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'admin_user_id': self.admin_user_id,
            'action': self.action,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'performed_at': self.performed_at.isoformat() if self.performed_at else None
        }


class FeatureFlag(Document):
    """Feature flags for enabling/disabling features"""
    meta = {'collection': 'feature_flags'}
    
    name = StringField(required=True, unique=True)
    description = StringField()
    
    is_enabled = BooleanField(default=True)
    
    # Rollout percentage (0-100)
    rollout_percentage = IntField(default=100)
    
    # User restrictions
    allowed_user_ids = ListField(StringField())  # If set, only these users can use
    blocked_user_ids = ListField(StringField())
    
    updated_by = StringField()
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'is_enabled': self.is_enabled,
            'rollout_percentage': self.rollout_percentage,
            'allowed_user_ids': self.allowed_user_ids,
            'blocked_user_ids': self.blocked_user_ids,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SystemSetting(Document):
    """System-wide settings"""
    meta = {'collection': 'system_settings'}
    
    key = StringField(required=True, unique=True)
    value = StringField()
    value_type = StringField(default='string', choices=['string', 'int', 'float', 'bool', 'json'])
    
    description = StringField()
    
    updated_by = StringField()
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'key': self.key,
            'value': self.value,
            'value_type': self.value_type,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

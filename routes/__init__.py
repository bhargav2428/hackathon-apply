"""
Routes Package Initialization
"""
from routes.auth import auth_bp
from routes.hackathons import hackathons_bp
from routes.user_profile import user_profile_bp
from routes.applications import applications_bp
from routes.ai_services import ai_services_bp
from routes.notifications import notifications_bp
from routes.dashboard import dashboard_bp

__all__ = [
    'auth_bp',
    'hackathons_bp',
    'user_profile_bp',
    'applications_bp',
    'ai_services_bp',
    'notifications_bp',
    'dashboard_bp'
]

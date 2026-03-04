"""
AI Hackathon Auto Apply Agent - Main Application
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from dotenv import load_dotenv

from config import Config
from database import mongo, init_db
from routes.auth import auth_bp
from routes.hackathons import hackathons_bp
from routes.user_profile import user_profile_bp
from routes.applications import applications_bp
from routes.ai_services import ai_services_bp
from routes.notifications import notifications_bp
from routes.dashboard import dashboard_bp
from routes.auto_apply import auto_apply_bp
from routes.credentials import credentials_bp

# Load environment variables
load_dotenv()

def create_app(config_class=Config):
    """Create and configure the Flask application"""
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')
    
    app.config.from_object(config_class)
    
    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize MongoDB
    init_db(app)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        try:
            return User.objects(id=user_id).first()
        except:
            return None
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(hackathons_bp, url_prefix='/api/hackathons')
    app.register_blueprint(user_profile_bp, url_prefix='/api/profile')
    app.register_blueprint(applications_bp, url_prefix='/api/applications')
    app.register_blueprint(ai_services_bp, url_prefix='/api/ai')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(auto_apply_bp, url_prefix='/api/auto-apply')
    app.register_blueprint(credentials_bp, url_prefix='/api/credentials')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'AI Hackathon Auto Apply Agent is running!'})
    
    # Root route
    @app.route('/')
    def index():
        return app.send_static_file('index.html')
    
    return app

# Create app instance for gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=os.environ.get('DEBUG', 'False').lower() == 'true')

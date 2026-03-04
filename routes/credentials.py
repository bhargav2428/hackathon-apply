"""Platform Credentials Routes - Manage login credentials for auto-apply"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.platform_credentials import PlatformCredentials

credentials_bp = Blueprint('credentials', __name__)


@credentials_bp.route('', methods=['GET'])
@login_required
def get_credentials():
    """Get all stored credentials for user (without passwords)"""
    creds = PlatformCredentials.objects(user_id=str(current_user.id))
    return jsonify({
        'credentials': [c.to_dict() for c in creds]
    }), 200


@credentials_bp.route('', methods=['POST'])
@login_required 
def save_credentials():
    """Save platform credentials"""
    data = request.get_json()
    platform = data.get('platform')
    email = data.get('email')
    password = data.get('password')
    
    if not all([platform, email, password]):
        return jsonify({'error': 'platform, email, and password are required'}), 400
    
    # Check if exists
    cred = PlatformCredentials.objects(
        user_id=str(current_user.id),
        platform=platform
    ).first()
    
    if cred:
        cred.set_credentials(email, password)
        cred.is_verified = False
        cred.save()
    else:
        cred = PlatformCredentials(
            user_id=str(current_user.id),
            platform=platform
        )
        cred.set_credentials(email, password)
        cred.save()
    
    return jsonify({
        'message': f'{platform} credentials saved',
        'credential': cred.to_dict()
    }), 200


@credentials_bp.route('/<platform>', methods=['DELETE'])
@login_required
def delete_credentials(platform):
    """Delete credentials for a platform"""
    deleted = PlatformCredentials.objects(
        user_id=str(current_user.id),
        platform=platform
    ).delete()
    
    if deleted:
        return jsonify({'message': f'{platform} credentials deleted'}), 200
    return jsonify({'error': 'Credentials not found'}), 404


@credentials_bp.route('/<platform>/verify', methods=['POST'])
@login_required
def verify_credentials(platform):
    """Verify credentials work by attempting login"""
    cred = PlatformCredentials.objects(
        user_id=str(current_user.id),
        platform=platform
    ).first()
    
    if not cred:
        return jsonify({'error': 'Credentials not found'}), 404
    
    # Verification would require running browser - mark as unverified for now
    return jsonify({
        'message': 'Credentials saved. Run local auto-apply to verify.',
        'credential': cred.to_dict()
    }), 200

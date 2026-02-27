"""Notification Routes - MongoDB"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.notification import Notification

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('', methods=['GET'])
@login_required
def get_notifications():
    unread_only = request.args.get('unread', 'false').lower() == 'true'
    
    query = {'user_id': str(current_user.id)}
    if unread_only:
        query['is_read'] = False
    
    notifications = Notification.objects(**query).order_by('-created_at')[:50]
    return jsonify({
        'notifications': [n.to_dict() for n in notifications]
    }), 200


@notifications_bp.route('/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    count = Notification.objects(user_id=str(current_user.id), is_read=False).count()
    return jsonify({'count': count}), 200


@notifications_bp.route('/<notification_id>/read', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    notification = Notification.objects(id=notification_id, user_id=str(current_user.id)).first()
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    notification.mark_as_read()
    return jsonify({'message': 'Marked as read'}), 200


@notifications_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_as_read():
    from datetime import datetime
    Notification.objects(user_id=str(current_user.id), is_read=False).update(
        set__is_read=True,
        set__read_at=datetime.utcnow()
    )
    return jsonify({'message': 'All notifications marked as read'}), 200


@notifications_bp.route('/<notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    notification = Notification.objects(id=notification_id, user_id=str(current_user.id)).first()
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    notification.delete()
    return jsonify({'message': 'Notification deleted'}), 200


@notifications_bp.route('/settings', methods=['GET'])
@login_required
def get_notification_settings():
    from models.user import User
    user = User.objects(id=current_user.id).first()
    return jsonify({
        'telegram_enabled': user.telegram_chat_id is not None,
        'telegram_chat_id': user.telegram_chat_id
    }), 200


@notifications_bp.route('/telegram/link', methods=['POST'])
@login_required
def link_telegram():
    data = request.get_json()
    chat_id = data.get('chat_id')
    
    if not chat_id:
        return jsonify({'error': 'chat_id is required'}), 400
    
    from models.user import User
    user = User.objects(id=current_user.id).first()
    user.telegram_chat_id = chat_id
    user.save()
    
    return jsonify({'message': 'Telegram linked successfully'}), 200

"""
Alert Models - For WhatsApp/SMS/Email deadline alerts
"""
from datetime import datetime
from mongoengine import Document, StringField, ListField, DateTimeField, BooleanField, IntField, DictField


class AlertSettings(Document):
    """User's alert preferences"""
    meta = {'collection': 'alert_settings'}
    
    user_id = StringField(required=True, unique=True)
    
    # Contact methods
    phone_number = StringField()  # For WhatsApp/SMS
    whatsapp_enabled = BooleanField(default=False)
    sms_enabled = BooleanField(default=False)
    email_enabled = BooleanField(default=True)
    telegram_enabled = BooleanField(default=False)
    telegram_chat_id = StringField()
    
    # When to alert (hours before deadline)
    alert_24h = BooleanField(default=True)
    alert_6h = BooleanField(default=True)
    alert_1h = BooleanField(default=True)
    custom_alert_hours = ListField(IntField())
    
    # What to alert about
    alert_deadlines = BooleanField(default=True)
    alert_new_hackathons = BooleanField(default=True)
    alert_team_matches = BooleanField(default=True)
    alert_application_status = BooleanField(default=True)
    
    # Timezone
    timezone = StringField(default='UTC')
    
    # Quiet hours (don't disturb)
    quiet_hours_start = IntField()  # 0-23
    quiet_hours_end = IntField()  # 0-23
    
    updated_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'phone_number': self.phone_number,
            'whatsapp_enabled': self.whatsapp_enabled,
            'sms_enabled': self.sms_enabled,
            'email_enabled': self.email_enabled,
            'telegram_enabled': self.telegram_enabled,
            'telegram_chat_id': self.telegram_chat_id,
            'alert_24h': self.alert_24h,
            'alert_6h': self.alert_6h,
            'alert_1h': self.alert_1h,
            'custom_alert_hours': self.custom_alert_hours,
            'alert_deadlines': self.alert_deadlines,
            'alert_new_hackathons': self.alert_new_hackathons,
            'alert_team_matches': self.alert_team_matches,
            'alert_application_status': self.alert_application_status,
            'timezone': self.timezone,
            'quiet_hours_start': self.quiet_hours_start,
            'quiet_hours_end': self.quiet_hours_end,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AlertLog(Document):
    """Log of sent alerts"""
    meta = {'collection': 'alert_logs'}
    
    user_id = StringField(required=True)
    hackathon_id = StringField()
    
    alert_type = StringField(choices=['deadline', 'new_hackathon', 'team_match', 'application_status', 'custom'])
    channel = StringField(choices=['email', 'sms', 'whatsapp', 'telegram', 'push'])
    
    message = StringField()
    
    status = StringField(default='sent', choices=['sent', 'delivered', 'failed', 'pending'])
    error_message = StringField()
    
    sent_at = DateTimeField(default=datetime.utcnow)
    delivered_at = DateTimeField()
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'hackathon_id': self.hackathon_id,
            'alert_type': self.alert_type,
            'channel': self.channel,
            'message': self.message,
            'status': self.status,
            'error_message': self.error_message,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None
        }

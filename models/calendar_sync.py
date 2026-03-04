"""
Calendar Sync Models - For syncing hackathons to calendars
"""
from datetime import datetime
from mongoengine import Document, StringField, IntField, ListField, DateTimeField, BooleanField, DictField


class CalendarSync(Document):
    """User's calendar sync settings"""
    meta = {'collection': 'calendar_syncs'}
    
    user_id = StringField(required=True, unique=True)
    
    # Connected calendars
    google_calendar_connected = BooleanField(default=False)
    google_calendar_token = StringField()  # Encrypted
    google_calendar_id = StringField()
    
    outlook_connected = BooleanField(default=False)
    outlook_token = StringField()  # Encrypted
    
    apple_calendar_connected = BooleanField(default=False)
    
    # Sync preferences
    auto_sync = BooleanField(default=True)
    sync_applied_only = BooleanField(default=False)  # Only sync hackathons user applied to
    
    # What to add
    add_hackathon_dates = BooleanField(default=True)
    add_deadline_reminders = BooleanField(default=True)
    add_prep_blocks = BooleanField(default=True)  # Block time for preparation
    prep_hours_before = IntField(default=24)
    
    # Customization
    event_color = StringField(default='#6366f1')
    reminder_minutes = ListField(IntField())  # [60, 1440] = 1hr and 1 day before
    
    last_synced = DateTimeField()
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'google_calendar_connected': self.google_calendar_connected,
            'outlook_connected': self.outlook_connected,
            'apple_calendar_connected': self.apple_calendar_connected,
            'auto_sync': self.auto_sync,
            'sync_applied_only': self.sync_applied_only,
            'add_hackathon_dates': self.add_hackathon_dates,
            'add_deadline_reminders': self.add_deadline_reminders,
            'add_prep_blocks': self.add_prep_blocks,
            'prep_hours_before': self.prep_hours_before,
            'event_color': self.event_color,
            'reminder_minutes': self.reminder_minutes,
            'last_synced': self.last_synced.isoformat() if self.last_synced else None
        }


from mongoengine import IntField

class CalendarEvent(Document):
    """Synced calendar events"""
    meta = {'collection': 'calendar_events'}
    
    user_id = StringField(required=True)
    hackathon_id = StringField(required=True)
    
    # External calendar references
    google_event_id = StringField()
    outlook_event_id = StringField()
    
    event_type = StringField(choices=['hackathon', 'deadline', 'prep', 'demo'])
    
    title = StringField()
    description = StringField()
    
    start_time = DateTimeField()
    end_time = DateTimeField()
    all_day = BooleanField(default=False)
    
    location = StringField()
    
    synced_at = DateTimeField(default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'hackathon_id': self.hackathon_id,
            'google_event_id': self.google_event_id,
            'outlook_event_id': self.outlook_event_id,
            'event_type': self.event_type,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'all_day': self.all_day,
            'location': self.location,
            'synced_at': self.synced_at.isoformat() if self.synced_at else None
        }

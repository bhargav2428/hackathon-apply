"""
Hackathon Monitor Service - Monitors for new hackathons and auto-applies
"""
import os
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from models.hackathon import Hackathon
from models.application import Application
from models.user import User
from models.user_profile import UserProfile
from models.notification import Notification
from services.ai_service import AIService
from services.notification_service import NotificationService


class HackathonMonitor:
    """Monitors for new hackathons and automatically generates ideas and applies"""
    
    def __init__(self):
        self._ai_service = None
        self._notification_service = None
        self.is_running = False
        self.check_interval = int(os.environ.get('MONITOR_INTERVAL', 300))  # 5 minutes default
        self._thread = None
        self._processed_hackathons = set()
    
    @property
    def ai_service(self):
        """Lazy initialization of AI service"""
        if self._ai_service is None:
            self._ai_service = AIService()
        return self._ai_service
    
    @property
    def notification_service(self):
        """Lazy initialization of notification service"""
        if self._notification_service is None:
            self._notification_service = NotificationService()
        return self._notification_service
    
    def start(self):
        """Start the monitoring service in a background thread"""
        if self._thread and self._thread.is_alive():
            return {"success": False, "message": "Monitor already running"}
        
        self.is_running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        return {"success": True, "message": "Hackathon monitor started"}
    
    def stop(self):
        """Stop the monitoring service"""
        self.is_running = False
        return {"success": True, "message": "Hackathon monitor stopped"}
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                self._check_new_hackathons()
            except Exception as e:
                print(f"Error in monitor loop: {e}")
            time.sleep(self.check_interval)
    
    def _check_new_hackathons(self):
        """Check for new hackathons and process them"""
        # Get hackathons added in the last hour that haven't been processed
        recent_cutoff = datetime.utcnow() - timedelta(hours=1)
        
        new_hackathons = Hackathon.objects(
            is_active=True,
            deadline__gt=datetime.utcnow()
        )
        
        for hackathon in new_hackathons:
            hackathon_id = str(hackathon.id)
            if hackathon_id not in self._processed_hackathons:
                self._process_new_hackathon(hackathon)
                self._processed_hackathons.add(hackathon_id)
    
    def _process_new_hackathon(self, hackathon):
        """Process a new hackathon - generate idea and auto-apply for all users with auto-apply enabled"""
        print(f"Processing new hackathon: {hackathon.name}")
        
        # Get all users with auto-apply enabled (we'll add this field)
        users = User.objects(auto_apply_enabled=True)
        
        for user in users:
            try:
                self.auto_apply_for_user(user, hackathon)
            except Exception as e:
                print(f"Error auto-applying for user {user.id}: {e}")
    
    def auto_apply_for_user(self, user, hackathon) -> Dict[str, Any]:
        """
        Auto-apply to a hackathon for a specific user:
        1. Generate project idea using AI
        2. Create application record
        3. Send Telegram notification
        """
        try:
            # Get user profile
            profile = UserProfile.objects(user_id=str(user.id)).first()
            
            # Check if already applied
            existing_app = Application.objects(
                user_id=str(user.id),
                hackathon_id=str(hackathon.id)
            ).first()
            
            if existing_app:
                return {
                    "success": False,
                    "message": "Already applied to this hackathon"
                }
            
            # Generate project idea using AI
            print(f"Generating project idea for {hackathon.name}...")
            idea = self.ai_service.generate_project_idea(hackathon, profile)
            
            # Generate motivation letter
            motivation = self.ai_service.generate_motivation(
                hackathon, 
                profile,
                idea.get('project_name', 'My Project')
            )
            
            # Create application record
            application = Application(
                user_id=str(user.id),
                hackathon_id=str(hackathon.id),
                hackathon_name=hackathon.name,
                status='auto_generated',
                generated_project_idea=json.dumps(idea) if isinstance(idea, dict) else str(idea),
                generated_motivation=motivation if isinstance(motivation, str) else json.dumps(motivation),
                is_auto_applied=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            application.save()
            
            # Save notification to database
            notification = Notification(
                user_id=str(user.id),
                type='auto_apply',
                title=f'New Hackathon: {hackathon.name}',
                message=self._format_notification_message(hackathon, idea),
                hackathon_id=str(hackathon.id),
                is_read=False,
                created_at=datetime.utcnow()
            )
            notification.save()
            
            # Send Telegram notification
            telegram_result = self._send_telegram_notification(user, hackathon, idea, application)
            
            return {
                "success": True,
                "message": "Auto-applied successfully",
                "application_id": str(application.id),
                "idea": idea,
                "telegram_sent": telegram_result.get('success', False)
            }
            
        except Exception as e:
            print(f"Error in auto_apply_for_user: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_notification_message(self, hackathon, idea: Dict) -> str:
        """Format notification message"""
        return f"""
🎯 A new hackathon matching your profile has been found!

📌 Hackathon: {hackathon.name}
💰 Prize: {hackathon.prize or 'Not specified'}
📅 Deadline: {hackathon.deadline.strftime('%B %d, %Y') if hackathon.deadline else 'Not specified'}

💡 AI Generated Project Idea:
Project Name: {idea.get('project_name', 'N/A')}
Problem: {idea.get('problem_statement', 'N/A')[:200]}...

🔗 URL: {hackathon.url}
"""
    
    def _send_telegram_notification(self, user, hackathon, idea: Dict, application) -> Dict[str, Any]:
        """Send Telegram notification about new hackathon and generated idea"""
        
        # Get telegram chat ID from user or profile
        chat_id = getattr(user, 'telegram_chat_id', None)
        
        if not chat_id:
            profile = UserProfile.objects(user_id=str(user.id)).first()
            if profile:
                chat_id = getattr(profile, 'telegram_chat_id', None)
        
        if not chat_id:
            return {"success": False, "error": "No Telegram chat ID configured"}
        
        # Format the message
        project_name = idea.get('project_name', 'Your Project')
        problem = idea.get('problem_statement', '')[:300]
        features = idea.get('key_features', [])
        features_text = '\n'.join([f"  • {f}" for f in features[:4]]) if features else '  • Check the dashboard for details'
        tech_stack = idea.get('tech_stack', [])
        tech_text = ', '.join(tech_stack[:5]) if tech_stack else 'Various technologies'
        
        message = f"""
🚀 *NEW HACKATHON DETECTED!*

━━━━━━━━━━━━━━━━━━━━━

📌 *{hackathon.name}*

💰 Prize: {hackathon.prize or 'TBA'}
📅 Deadline: {hackathon.deadline.strftime('%B %d, %Y') if hackathon.deadline else 'TBA'}
🏷 Tags: {', '.join(hackathon.tags[:3]) if hackathon.tags else 'N/A'}

━━━━━━━━━━━━━━━━━━━━━

💡 *AI Generated Project Idea:*

🎯 *{project_name}*

📝 *Problem:*
{problem}...

✨ *Key Features:*
{features_text}

🛠 *Tech Stack:*
{tech_text}

━━━━━━━━━━━━━━━━━━━━━

✅ Application has been auto-generated!
📋 Status: Ready for Review

🔗 [View Hackathon]({hackathon.url})

_Visit your dashboard to review and submit!_
"""
        
        return self.notification_service.send_telegram(chat_id, "New Hackathon Found!", message)
    
    def process_single_hackathon(self, hackathon_id: str, user_id: str) -> Dict[str, Any]:
        """
        Manually trigger auto-apply for a single hackathon and user
        """
        try:
            hackathon = Hackathon.objects(id=hackathon_id).first()
            if not hackathon:
                return {"success": False, "error": "Hackathon not found"}
            
            user = User.objects(id=user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            return self.auto_apply_for_user(user, hackathon)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def process_all_hackathons_for_user(self, user_id: str) -> Dict[str, Any]:
        """
        Process all active hackathons for a specific user
        """
        results = []
        user = User.objects(id=user_id).first()
        
        if not user:
            return {"success": False, "error": "User not found"}
        
        hackathons = Hackathon.objects(
            is_active=True,
            deadline__gt=datetime.utcnow()
        )
        
        for hackathon in hackathons:
            result = self.auto_apply_for_user(user, hackathon)
            results.append({
                "hackathon": hackathon.name,
                "result": result
            })
        
        return {
            "success": True,
            "processed": len(results),
            "results": results
        }


# Global instance
hackathon_monitor = HackathonMonitor()

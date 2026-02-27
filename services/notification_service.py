"""
Notification Service - Handles sending notifications via Email, Telegram, and Discord
"""
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from datetime import datetime


class NotificationService:
    """Service for sending notifications through various channels"""
    
    def __init__(self):
        # Email configuration
        self.mail_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        self.mail_port = int(os.environ.get('MAIL_PORT', 587))
        self.mail_use_tls = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
        self.mail_username = os.environ.get('MAIL_USERNAME')
        self.mail_password = os.environ.get('MAIL_PASSWORD')
        
        # Telegram configuration
        self.telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        
        # Discord configuration
        self.discord_webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    
    def send_email(self, to_email: str, subject: str, body: str, html: bool = False) -> Dict[str, Any]:
        """Send email notification"""
        try:
            if not self.mail_username or not self.mail_password:
                return {'success': False, 'error': 'Email not configured'}
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.mail_username
            msg['To'] = to_email
            
            if html:
                part = MIMEText(body, 'html')
            else:
                part = MIMEText(body, 'plain')
            
            msg.attach(part)
            
            with smtplib.SMTP(self.mail_server, self.mail_port) as server:
                if self.mail_use_tls:
                    server.starttls()
                server.login(self.mail_username, self.mail_password)
                server.sendmail(self.mail_username, to_email, msg.as_string())
            
            return {'success': True, 'message': f'Email sent to {to_email}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_telegram(self, profile_or_chat_id, title: str, message: str) -> Dict[str, Any]:
        """Send Telegram notification"""
        try:
            if not self.telegram_bot_token:
                return {'success': False, 'error': 'Telegram bot not configured'}
            
            # Get chat_id from profile or use it directly
            if hasattr(profile_or_chat_id, 'telegram_chat_id'):
                chat_id = profile_or_chat_id.telegram_chat_id
            else:
                chat_id = profile_or_chat_id
            
            if not chat_id:
                return {'success': False, 'error': 'No Telegram chat ID'}
            
            # Format message
            formatted_message = f"""
🚀 *{title}*

{message}

_Sent by AI Hackathon Auto Apply Agent_
"""
            
            url = f'https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage'
            data = {
                'chat_id': chat_id,
                'text': formatted_message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data)
            response_data = response.json()
            
            if response_data.get('ok'):
                return {'success': True, 'message': 'Telegram message sent'}
            else:
                return {'success': False, 'error': response_data.get('description', 'Unknown error')}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_discord(self, profile_or_webhook, title: str, message: str, 
                     color: int = 0x00ff00, url: Optional[str] = None) -> Dict[str, Any]:
        """Send Discord notification via webhook"""
        try:
            # Get webhook URL from profile or use it directly
            if hasattr(profile_or_webhook, 'discord_webhook'):
                webhook_url = profile_or_webhook.discord_webhook
            else:
                webhook_url = profile_or_webhook or self.discord_webhook_url
            
            if not webhook_url:
                return {'success': False, 'error': 'No Discord webhook URL'}
            
            # Create Discord embed
            embed = {
                'title': title,
                'description': message,
                'color': color,
                'timestamp': datetime.utcnow().isoformat(),
                'footer': {
                    'text': 'AI Hackathon Auto Apply Agent'
                }
            }
            
            if url:
                embed['url'] = url
            
            data = {
                'embeds': [embed]
            }
            
            response = requests.post(
                webhook_url,
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 204]:
                return {'success': True, 'message': 'Discord message sent'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def notify_new_hackathon(self, user, hackathon) -> Dict[str, Any]:
        """Send notification about a new hackathon"""
        title = "🎯 New Hackathon Found!"
        
        message = f"""
**{hackathon.name}**

📅 Deadline: {hackathon.registration_deadline.strftime('%Y-%m-%d') if hackathon.registration_deadline else 'Not specified'}
📍 Location: {'Online' if hackathon.is_online else hackathon.location or 'Not specified'}
🏆 Prize: {hackathon.prize_pool or 'Not specified'}
🏷️ Tags: {', '.join(hackathon.tags[:5]) if hackathon.tags else 'None'}

🔗 Apply: {hackathon.url}
"""
        
        results = {}
        profile = user.profile
        
        # Send through enabled channels
        if profile and profile.email_notifications:
            results['email'] = self.send_email(
                user.email,
                f"New Hackathon: {hackathon.name}",
                message
            )
        
        if profile and profile.telegram_notifications and profile.telegram_chat_id:
            results['telegram'] = self.send_telegram(profile, title, message)
        
        if profile and profile.discord_notifications and profile.discord_webhook:
            results['discord'] = self.send_discord(
                profile, title, message,
                color=0x5865F2,
                url=hackathon.url
            )
        
        return results
    
    def notify_application_submitted(self, user, hackathon, auto: bool = False) -> Dict[str, Any]:
        """Send notification about submitted application"""
        title = "✅ Application Submitted!"
        
        message = f"""
Your application to **{hackathon.name}** has been submitted!

Applied: {'Automatically' if auto else 'Manually'}
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

Good luck! 🍀
"""
        
        results = {}
        profile = user.profile
        
        if profile and profile.email_notifications:
            results['email'] = self.send_email(
                user.email,
                f"Application Submitted: {hackathon.name}",
                message
            )
        
        if profile and profile.telegram_notifications and profile.telegram_chat_id:
            results['telegram'] = self.send_telegram(profile, title, message)
        
        if profile and profile.discord_notifications:
            results['discord'] = self.send_discord(
                profile, title, message,
                color=0x00FF00
            )
        
        return results
    
    def notify_deadline_reminder(self, user, hackathon, days_left: int) -> Dict[str, Any]:
        """Send deadline reminder notification"""
        urgency = "⚠️" if days_left <= 3 else "⏰"
        title = f"{urgency} Deadline Reminder"
        
        message = f"""
**{hackathon.name}** deadline is approaching!

⏰ **{days_left} day{'s' if days_left != 1 else ''} left** to register!

📅 Deadline: {hackathon.registration_deadline.strftime('%Y-%m-%d %H:%M UTC') if hackathon.registration_deadline else 'Soon'}

🔗 Apply now: {hackathon.url}
"""
        
        results = {}
        profile = user.profile
        
        if profile and profile.email_notifications:
            results['email'] = self.send_email(
                user.email,
                f"Deadline in {days_left} days: {hackathon.name}",
                message
            )
        
        if profile and profile.telegram_notifications and profile.telegram_chat_id:
            results['telegram'] = self.send_telegram(profile, title, message)
        
        if profile and profile.discord_notifications:
            color = 0xFF0000 if days_left <= 1 else (0xFFA500 if days_left <= 3 else 0xFFFF00)
            results['discord'] = self.send_discord(
                profile, title, message,
                color=color,
                url=hackathon.url
            )
        
        return results
    
    def notify_eligibility_result(self, user, hackathon, result: Dict) -> Dict[str, Any]:
        """Send eligibility check result notification"""
        is_eligible = result.get('is_eligible', False)
        score = result.get('score', 0)
        
        emoji = "✅" if is_eligible else "❌"
        title = f"{emoji} Eligibility Check Result"
        
        message = f"""
**{hackathon.name}**

Eligibility Score: **{int(score * 100)}%**
Status: {"Eligible ✓" if is_eligible else "Not Eligible ✗"}

Reasons:
{chr(10).join(result.get('reasons', [])[:5])}

{chr(10).join('⚠️ ' + w for w in result.get('warnings', [])[:3])}
"""
        
        results = {}
        profile = user.profile
        
        if profile and profile.email_notifications:
            results['email'] = self.send_email(
                user.email,
                f"Eligibility: {hackathon.name}",
                message
            )
        
        if profile and profile.telegram_notifications and profile.telegram_chat_id:
            results['telegram'] = self.send_telegram(profile, title, message)
        
        if profile and profile.discord_notifications:
            color = 0x00FF00 if is_eligible else 0xFF0000
            results['discord'] = self.send_discord(
                profile, title, message,
                color=color
            )
        
        return results
    
    def send_to_all_channels(self, user, title: str, message: str, 
                             color: int = 0x5865F2, url: Optional[str] = None) -> Dict[str, Any]:
        """Send notification to all enabled channels"""
        results = {}
        profile = user.profile
        
        if profile and profile.email_notifications:
            results['email'] = self.send_email(user.email, title, message)
        
        if profile and profile.telegram_notifications and profile.telegram_chat_id:
            results['telegram'] = self.send_telegram(profile, title, message)
        
        if profile and profile.discord_notifications:
            results['discord'] = self.send_discord(profile, title, message, color, url)
        
        return results

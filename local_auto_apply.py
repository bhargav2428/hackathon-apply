"""
🤖 AUTO-APPLY BOT - Automatically applies to hackathons using browser automation
Run this script locally on your machine to auto-apply to hackathons.

Usage:
    python local_auto_apply.py                    # Apply to all pending applications
    python local_auto_apply.py --hackathon <id>  # Apply to specific hackathon
    python local_auto_apply.py --visible          # Run with visible browser (not headless)
    python local_auto_apply.py --setup            # Setup/update platform credentials
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# MongoDB connection
import mongoengine
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://bhargavyaswanth_db_user:9KeEgedtlsrFsZBg@cluster0.bounkpp.mongodb.net/hackathon_agent?retryWrites=true&w=majority')
mongoengine.connect(host=MONGO_URI)

from models.hackathon import Hackathon
from models.application import Application
from models.user_profile import UserProfile
from models.platform_credentials import PlatformCredentials

try:
    from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("❌ Playwright not installed. Install it with:")
    print("   pip install playwright")
    print("   playwright install chromium")
    sys.exit(1)


class AutoApplyBot:
    """Automated hackathon application bot"""
    
    def __init__(self, user_id: str, headless: bool = True):
        self.user_id = user_id
        self.headless = headless
        self.browser = None
        self.context = None
        self.credentials_cache = {}
        
        # Load user profile
        self.profile = UserProfile.objects(user_id=user_id).first()
        if not self.profile:
            raise ValueError(f"No profile found for user {user_id}")
        
        # Load credentials
        creds = PlatformCredentials.objects(user_id=user_id)
        for cred in creds:
            email, password = cred.get_credentials()
            self.credentials_cache[cred.platform] = {'email': email, 'password': password}
        
        print(f"✅ Loaded profile for: {self.profile.name}")
        print(f"✅ Credentials available for: {list(self.credentials_cache.keys())}")
    
    async def start_browser(self):
        """Start the browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            slow_mo=100  # Slow down for visibility
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        print("🌐 Browser started")
    
    async def stop_browser(self):
        """Stop the browser"""
        if self.browser:
            await self.browser.close()
            print("🌐 Browser closed")
    
    async def apply_to_hackathon(self, application: Application) -> Dict[str, Any]:
        """Apply to a single hackathon"""
        hackathon = Hackathon.objects(id=application.hackathon_id).first()
        if not hackathon:
            return {'success': False, 'error': 'Hackathon not found'}
        
        print(f"\n{'='*60}")
        print(f"🎯 Applying to: {hackathon.name}")
        print(f"   Source: {hackathon.source}")
        print(f"   URL: {hackathon.url}")
        print(f"{'='*60}")
        
        source = (hackathon.source or 'unknown').lower()
        
        page = await self.context.new_page()
        
        try:
            if source == 'devpost':
                result = await self._apply_devpost(page, hackathon, application)
            elif source == 'unstop':
                result = await self._apply_unstop(page, hackathon, application)
            elif source == 'mlh':
                result = await self._apply_mlh(page, hackathon, application)
            else:
                result = await self._apply_generic(page, hackathon, application)
            
            # Take screenshot
            screenshot_dir = os.path.join(os.path.dirname(__file__), 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(screenshot_dir, f'{hackathon.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            await page.screenshot(path=screenshot_path, full_page=True)
            result['screenshot'] = screenshot_path
            print(f"📸 Screenshot saved: {screenshot_path}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            await page.close()
    
    async def _apply_devpost(self, page: Page, hackathon: Hackathon, application: Application) -> Dict[str, Any]:
        """Apply to Devpost hackathon"""
        url = hackathon.registration_url or hackathon.url
        
        print(f"📍 Navigating to: {url}")
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state('networkidle', timeout=30000)
        
        # Check if we need to login
        if await page.locator('text=Sign in').count() > 0 or await page.locator('text=Log in').count() > 0:
            print("🔐 Login required...")
            
            creds = self.credentials_cache.get('devpost')
            if not creds:
                return {'success': False, 'error': 'No Devpost credentials saved. Run with --setup first.'}
            
            # Click sign in
            signin_btn = page.locator('a:has-text("Sign in"), a:has-text("Log in")').first
            await signin_btn.click()
            await page.wait_for_load_state('networkidle', timeout=30000)
            
            # Fill login form
            await page.fill('input[name="user[email]"], input[type="email"]', creds['email'])
            await page.fill('input[name="user[password]"], input[type="password"]', creds['password'])
            
            # Submit login
            await page.click('input[type="submit"], button[type="submit"]')
            await page.wait_for_load_state('networkidle', timeout=30000)
            
            # Check if login succeeded
            if await page.locator('text=Invalid').count() > 0:
                return {'success': False, 'error': 'Devpost login failed - check credentials'}
            
            print("✅ Logged in to Devpost")
            
            # Navigate back to hackathon
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state('networkidle', timeout=30000)
        
        # Look for register/join button
        register_btn = page.locator('a:has-text("Register"), a:has-text("Join"), button:has-text("Register"), button:has-text("Join")').first
        
        if await register_btn.count() > 0:
            print("📝 Clicking register button...")
            await register_btn.click()
            await page.wait_for_load_state('networkidle', timeout=30000)
        
        # Fill any forms on the page
        filled_fields = await self._fill_form_fields(page)
        
        # Look for submit button
        submit_btn = page.locator('button[type="submit"]:has-text("Submit"), button[type="submit"]:has-text("Register"), input[type="submit"]').first
        
        if await submit_btn.count() > 0:
            print("📤 Submitting...")
            await submit_btn.click()
            await page.wait_for_timeout(3000)
            
            # Check for success
            success_indicators = ['successfully', 'registered', 'thank you', 'confirmed', 'welcome']
            page_text = await page.content()
            
            for indicator in success_indicators:
                if indicator.lower() in page_text.lower():
                    print(f"✅ SUCCESS! Application submitted")
                    
                    # Update application status
                    application.status = 'submitted'
                    application.is_auto_applied = True
                    application.submitted_at = datetime.utcnow()
                    application.save()
                    
                    return {'success': True, 'message': 'Applied successfully via Devpost', 'filled_fields': filled_fields}
        
        # If we're already registered
        if 'already registered' in (await page.content()).lower() or 'you are registered' in (await page.content()).lower():
            print("✅ Already registered for this hackathon")
            application.status = 'submitted'
            application.is_auto_applied = True
            application.submitted_at = datetime.utcnow()
            application.save()
            return {'success': True, 'message': 'Already registered'}
        
        return {'success': False, 'error': 'Could not complete registration', 'filled_fields': filled_fields}
    
    async def _apply_unstop(self, page: Page, hackathon: Hackathon, application: Application) -> Dict[str, Any]:
        """Apply to Unstop hackathon"""
        url = hackathon.registration_url or hackathon.url
        
        print(f"📍 Navigating to: {url}")
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state('networkidle', timeout=30000)
        
        # Unstop uses "Register" or "Apply" buttons
        apply_btn = page.locator('button:has-text("Register"), button:has-text("Apply"), a:has-text("Register")').first
        
        if await apply_btn.count() > 0:
            await apply_btn.click()
            await page.wait_for_load_state('networkidle', timeout=30000)
        
        # Check for login popup
        creds = self.credentials_cache.get('unstop')
        if creds:
            email_field = page.locator('input[type="email"], input[name="email"]').first
            if await email_field.count() > 0:
                print("🔐 Filling login...")
                await email_field.fill(creds['email'])
                
                password_field = page.locator('input[type="password"]').first
                if await password_field.count() > 0:
                    await password_field.fill(creds['password'])
                
                login_btn = page.locator('button[type="submit"], button:has-text("Login")').first
                if await login_btn.count() > 0:
                    await login_btn.click()
                    await page.wait_for_timeout(3000)
        
        # Fill forms
        filled = await self._fill_form_fields(page)
        
        # Submit
        submit_btn = page.locator('button[type="submit"]:has-text("Submit"), button:has-text("Apply")').first
        if await submit_btn.count() > 0:
            await submit_btn.click()
            await page.wait_for_timeout(3000)
            
            if 'success' in (await page.content()).lower():
                application.status = 'submitted'
                application.is_auto_applied = True
                application.submitted_at = datetime.utcnow()
                application.save()
                return {'success': True, 'message': 'Applied via Unstop'}
        
        return {'success': False, 'error': 'Could not complete Unstop registration', 'filled_fields': filled}
    
    async def _apply_mlh(self, page: Page, hackathon: Hackathon, application: Application) -> Dict[str, Any]:
        """Apply to MLH hackathon - usually redirects to external registration"""
        url = hackathon.registration_url or hackathon.url
        
        print(f"📍 Navigating to: {url}")
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state('networkidle', timeout=30000)
        
        # MLH usually has "Apply" or "Register" links that go to external sites
        register_link = page.locator('a:has-text("Apply"), a:has-text("Register"), a:has-text("Sign Up")').first
        
        if await register_link.count() > 0:
            href = await register_link.get_attribute('href')
            print(f"📍 Following registration link: {href}")
            await register_link.click()
            await page.wait_for_load_state('networkidle', timeout=30000)
        
        # Fill any forms
        filled = await self._fill_form_fields(page)
        
        return {'success': False, 'error': 'MLH hackathons require manual registration on external site', 'filled_fields': filled, 'manual_required': True}
    
    async def _apply_generic(self, page: Page, hackathon: Hackathon, application: Application) -> Dict[str, Any]:
        """Generic application flow"""
        url = hackathon.registration_url or hackathon.url
        
        print(f"📍 Navigating to: {url}")
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state('networkidle', timeout=30000)
        
        # Look for register/apply buttons
        action_btn = page.locator('a:has-text("Register"), a:has-text("Apply"), button:has-text("Register"), button:has-text("Apply"), a:has-text("Sign Up")').first
        
        if await action_btn.count() > 0:
            await action_btn.click()
            await page.wait_for_load_state('networkidle', timeout=30000)
        
        # Fill forms
        filled = await self._fill_form_fields(page)
        
        # Try to submit
        submit_btn = page.locator('button[type="submit"], input[type="submit"]').first
        if await submit_btn.count() > 0:
            print("📤 Attempting submit...")
            await submit_btn.click()
            await page.wait_for_timeout(3000)
        
        return {'success': False, 'error': 'Generic flow - please verify registration manually', 'filled_fields': filled, 'manual_required': True}
    
    async def _fill_form_fields(self, page: Page) -> Dict[str, str]:
        """Fill common form fields with profile data"""
        filled = {}
        profile = self.profile
        
        field_mappings = [
            # Name fields
            (['input[name*="name"]', 'input[placeholder*="name"]', '#name', '#full_name'], profile.name),
            (['input[name*="first_name"]', 'input[placeholder*="first"]', '#first_name'], profile.name.split()[0] if profile.name else ''),
            (['input[name*="last_name"]', 'input[placeholder*="last"]', '#last_name'], profile.name.split()[-1] if profile.name and len(profile.name.split()) > 1 else ''),
            
            # Email
            (['input[type="email"]', 'input[name*="email"]', '#email'], profile.email),
            
            # Phone
            (['input[type="tel"]', 'input[name*="phone"]', '#phone'], profile.phone or ''),
            
            # Location
            (['input[name*="city"]', '#city'], profile.location or ''),
            (['input[name*="country"]', '#country'], 'India'),
            
            # Education
            (['input[name*="school"]', 'input[name*="university"]', 'input[name*="college"]', '#school'], profile.school or ''),
            (['input[name*="major"]', 'input[name*="field"]', '#major'], profile.major or ''),
            (['input[name*="graduation"]', 'input[name*="grad_year"]'], str(profile.graduation_year) if profile.graduation_year else ''),
            
            # Links
            (['input[name*="github"]', 'input[placeholder*="github"]'], profile.github or ''),
            (['input[name*="linkedin"]', 'input[placeholder*="linkedin"]'], profile.linkedin or ''),
            (['input[name*="portfolio"]', 'input[name*="website"]'], profile.portfolio or ''),
            
            # Bio/About
            (['textarea[name*="bio"]', 'textarea[name*="about"]', '#bio'], profile.bio or ''),
        ]
        
        for selectors, value in field_mappings:
            if not value:
                continue
            
            for selector in selectors:
                try:
                    field = page.locator(selector).first
                    if await field.count() > 0 and await field.is_visible():
                        current_value = await field.input_value()
                        if not current_value:  # Only fill if empty
                            await field.fill(str(value))
                            filled[selector] = str(value)
                            print(f"   ✏️ Filled {selector}")
                            break
                except Exception:
                    continue
        
        return filled
    
    async def apply_to_all_pending(self):
        """Apply to all pending applications"""
        applications = Application.objects(user_id=self.user_id, status__in=['pending', 'auto_generated'])
        
        print(f"\n📋 Found {len(applications)} pending applications")
        
        results = []
        for app in applications:
            result = await self.apply_to_hackathon(app)
            results.append({
                'hackathon': app.hackathon_name,
                'result': result
            })
        
        return results


def setup_credentials():
    """Interactive credential setup"""
    print("\n" + "="*60)
    print("🔐 PLATFORM CREDENTIALS SETUP")
    print("="*60)
    
    user_id = input("Enter your user ID: ").strip()
    
    platforms = ['devpost', 'unstop', 'mlh', 'hackerearth']
    
    for platform in platforms:
        print(f"\n--- {platform.upper()} ---")
        setup = input(f"Setup {platform} credentials? (y/n): ").strip().lower()
        
        if setup == 'y':
            email = input("  Email: ").strip()
            password = input("  Password: ").strip()
            
            cred = PlatformCredentials.objects(user_id=user_id, platform=platform).first()
            if not cred:
                cred = PlatformCredentials(user_id=user_id, platform=platform)
            
            cred.set_credentials(email, password)
            cred.save()
            print(f"  ✅ {platform} credentials saved")
    
    print("\n✅ Setup complete!")


async def main():
    parser = argparse.ArgumentParser(description='Auto-apply to hackathons')
    parser.add_argument('--user', type=str, help='User ID')
    parser.add_argument('--hackathon', type=str, help='Specific hackathon ID to apply to')
    parser.add_argument('--visible', action='store_true', help='Run browser in visible mode')
    parser.add_argument('--setup', action='store_true', help='Setup platform credentials')
    
    args = parser.parse_args()
    
    if args.setup:
        setup_credentials()
        return
    
    if not args.user:
        print("❌ Please provide --user <user_id>")
        print("   Or run with --setup to configure credentials")
        return
    
    print("\n" + "="*60)
    print("🤖 AUTO-APPLY BOT")
    print("="*60)
    
    try:
        bot = AutoApplyBot(user_id=args.user, headless=not args.visible)
        await bot.start_browser()
        
        if args.hackathon:
            app = Application.objects(id=args.hackathon, user_id=args.user).first()
            if app:
                result = await bot.apply_to_hackathon(app)
                print(f"\n📊 Result: {result}")
            else:
                print(f"❌ Application {args.hackathon} not found")
        else:
            results = await bot.apply_to_all_pending()
            
            print("\n" + "="*60)
            print("📊 RESULTS SUMMARY")
            print("="*60)
            
            for r in results:
                status = "✅" if r['result'].get('success') else "❌"
                print(f"  {status} {r['hackathon']}: {r['result'].get('message') or r['result'].get('error')}")
        
        await bot.stop_browser()
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == '__main__':
    asyncio.run(main())

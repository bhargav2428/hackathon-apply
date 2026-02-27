"""
Auto Apply Bot - Automatically applies to hackathons using Playwright
"""
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser


class AutoApplyBot:
    """Automated hackathon application bot using Playwright"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.headless = os.environ.get('AUTO_APPLY_HEADLESS', 'true').lower() == 'true'
        self.screenshot_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'screenshots')
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    def apply(self, hackathon, profile, application) -> Dict[str, Any]:
        """
        Apply to a hackathon synchronously (wrapper for async)
        """
        return asyncio.run(self._apply_async(hackathon, profile, application))
    
    async def _apply_async(self, hackathon, profile, application) -> Dict[str, Any]:
        """
        Asynchronously apply to a hackathon
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = await context.new_page()
                
                # Route based on hackathon source
                source = hackathon.source.lower()
                
                if source == 'devpost':
                    result = await self._apply_devpost(page, hackathon, profile, application)
                elif source == 'unstop':
                    result = await self._apply_unstop(page, hackathon, profile, application)
                elif source == 'mlh':
                    result = await self._apply_mlh(page, hackathon, profile, application)
                elif source == 'hack2skill':
                    result = await self._apply_hack2skill(page, hackathon, profile, application)
                elif source == 'eventbrite':
                    result = await self._apply_eventbrite(page, hackathon, profile, application)
                else:
                    result = await self._apply_generic(page, hackathon, profile, application)
                
                # Take screenshot
                screenshot_path = os.path.join(
                    self.screenshot_dir,
                    f'{hackathon.id}_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}.png'
                )
                await page.screenshot(path=screenshot_path, full_page=True)
                result['screenshot_path'] = screenshot_path
                
                await browser.close()
                return result
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'hackathon_id': hackathon.id
            }
    
    async def _apply_devpost(self, page: Page, hackathon, profile, application) -> Dict[str, Any]:
        """Apply to Devpost hackathon"""
        try:
            # Navigate to registration page
            url = hackathon.registration_url or hackathon.url
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            # Check if login is required
            if await page.locator('text=Sign in').count() > 0:
                # Note: Would need user credentials for actual login
                return {
                    'success': False,
                    'error': 'Login required - please login to Devpost manually first',
                    'requires_login': True
                }
            
            # Click register/join button
            register_button = page.locator('a:has-text("Register"), button:has-text("Join")')
            if await register_button.count() > 0:
                await register_button.first.click()
                await page.wait_for_load_state('networkidle')
            
            # Fill form fields
            submitted_data = await self._fill_common_fields(page, profile, application)
            
            # Look for submit button
            submit_button = page.locator('button[type="submit"], input[type="submit"], button:has-text("Submit")')
            
            if await submit_button.count() > 0:
                # Check for confirmation before submitting
                await submit_button.first.click()
                await page.wait_for_timeout(2000)
                
                # Check for success message
                success_indicators = [
                    'text=successfully',
                    'text=registered',
                    'text=Thank you',
                    'text=confirmed'
                ]
                
                for indicator in success_indicators:
                    if await page.locator(indicator).count() > 0:
                        return {
                            'success': True,
                            'submitted_data': submitted_data,
                            'message': 'Application submitted successfully'
                        }
            
            return {
                'success': False,
                'error': 'Could not complete submission',
                'submitted_data': submitted_data
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _apply_unstop(self, page: Page, hackathon, profile, application) -> Dict[str, Any]:
        """Apply to Unstop hackathon"""
        try:
            url = hackathon.registration_url or hackathon.url
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            # Click register button
            register_button = page.locator('button:has-text("Register"), a:has-text("Register")')
            if await register_button.count() > 0:
                await register_button.first.click()
                await page.wait_for_load_state('networkidle')
            
            # Fill form
            submitted_data = await self._fill_common_fields(page, profile, application)
            
            # Submit
            submit_button = page.locator('button[type="submit"], button:has-text("Submit")')
            if await submit_button.count() > 0:
                await submit_button.first.click()
                await page.wait_for_timeout(3000)
                
                if await page.locator('text=successfully').count() > 0:
                    return {
                        'success': True,
                        'submitted_data': submitted_data
                    }
            
            return {
                'success': False,
                'error': 'Could not complete Unstop submission',
                'submitted_data': submitted_data
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _apply_mlh(self, page: Page, hackathon, profile, application) -> Dict[str, Any]:
        """Apply to MLH hackathon"""
        try:
            url = hackathon.registration_url or hackathon.url
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            # MLH often redirects to event-specific registration
            register_button = page.locator('a:has-text("Register"), button:has-text("Apply")')
            if await register_button.count() > 0:
                await register_button.first.click()
                await page.wait_for_load_state('networkidle')
            
            submitted_data = await self._fill_common_fields(page, profile, application)
            
            # Handle MLH checkbox agreements
            checkboxes = page.locator('input[type="checkbox"]')
            checkbox_count = await checkboxes.count()
            for i in range(checkbox_count):
                try:
                    await checkboxes.nth(i).check()
                except:
                    pass
            
            submit_button = page.locator('button[type="submit"], input[type="submit"]')
            if await submit_button.count() > 0:
                await submit_button.first.click()
                await page.wait_for_timeout(3000)
                
                if await page.locator('text=registered, text=success, text=thank').count() > 0:
                    return {
                        'success': True,
                        'submitted_data': submitted_data
                    }
            
            return {
                'success': False,
                'error': 'Could not complete MLH submission',
                'submitted_data': submitted_data
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _apply_hack2skill(self, page: Page, hackathon, profile, application) -> Dict[str, Any]:
        """Apply to Hack2Skill hackathon"""
        try:
            url = hackathon.registration_url or hackathon.url
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            submitted_data = await self._fill_common_fields(page, profile, application)
            
            submit_button = page.locator('button[type="submit"]')
            if await submit_button.count() > 0:
                await submit_button.first.click()
                await page.wait_for_timeout(3000)
                
                if await page.locator('text=success').count() > 0:
                    return {
                        'success': True,
                        'submitted_data': submitted_data
                    }
            
            return {
                'success': False,
                'error': 'Could not complete Hack2Skill submission',
                'submitted_data': submitted_data
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _apply_eventbrite(self, page: Page, hackathon, profile, application) -> Dict[str, Any]:
        """Apply to Eventbrite event"""
        try:
            url = hackathon.registration_url or hackathon.url
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            # Click register/get tickets button
            register_button = page.locator('button:has-text("Register"), button:has-text("Get tickets")')
            if await register_button.count() > 0:
                await register_button.first.click()
                await page.wait_for_load_state('networkidle')
            
            submitted_data = await self._fill_common_fields(page, profile, application)
            
            # Eventbrite checkout flow
            checkout_button = page.locator('button:has-text("Checkout"), button:has-text("Register")')
            if await checkout_button.count() > 0:
                await checkout_button.first.click()
                await page.wait_for_timeout(3000)
            
            return {
                'success': False,
                'error': 'Eventbrite requires manual checkout',
                'submitted_data': submitted_data,
                'requires_manual': True
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _apply_generic(self, page: Page, hackathon, profile, application) -> Dict[str, Any]:
        """Generic application attempt"""
        try:
            url = hackathon.registration_url or hackathon.url
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            submitted_data = await self._fill_common_fields(page, profile, application)
            
            # Try to find and click submit
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Submit")',
                'button:has-text("Register")',
                'button:has-text("Apply")'
            ]
            
            for selector in submit_selectors:
                submit_button = page.locator(selector)
                if await submit_button.count() > 0:
                    await submit_button.first.click()
                    await page.wait_for_timeout(3000)
                    
                    if await page.locator('text=success, text=thank, text=confirmed').count() > 0:
                        return {
                            'success': True,
                            'submitted_data': submitted_data
                        }
                    break
            
            return {
                'success': False,
                'error': 'Could not complete generic submission',
                'submitted_data': submitted_data
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _fill_common_fields(self, page: Page, profile, application) -> Dict[str, str]:
        """Fill common form fields based on profile"""
        submitted_data = {}
        
        field_mappings = [
            # (input_selectors, profile_value, field_name)
            (['input[name*="first"]', 'input[placeholder*="First"]', '#firstName', '#first_name'],
             profile.first_name if profile else '', 'first_name'),
            
            (['input[name*="last"]', 'input[placeholder*="Last"]', '#lastName', '#last_name'],
             profile.last_name if profile else '', 'last_name'),
            
            (['input[type="email"]', 'input[name*="email"]', '#email'],
             profile.user.email if profile and profile.user else '', 'email'),
            
            (['input[name*="phone"]', 'input[type="tel"]', '#phone'],
             profile.phone if profile else '', 'phone'),
            
            (['input[name*="github"]', 'input[placeholder*="GitHub"]'],
             profile.github_url if profile else '', 'github'),
            
            (['input[name*="linkedin"]', 'input[placeholder*="LinkedIn"]'],
             profile.linkedin_url if profile else '', 'linkedin'),
            
            (['input[name*="college"]', 'input[name*="school"]', 'input[name*="university"]'],
             profile.college if profile else '', 'college'),
            
            (['input[name*="portfolio"]', 'input[placeholder*="Portfolio"]', 'input[placeholder*="Website"]'],
             profile.portfolio_url if profile else '', 'portfolio'),
        ]
        
        for selectors, value, field_name in field_mappings:
            if not value:
                continue
                
            for selector in selectors:
                try:
                    field = page.locator(selector).first
                    if await field.count() > 0 and await field.is_visible():
                        await field.fill(value)
                        submitted_data[field_name] = value
                        break
                except:
                    continue
        
        # Fill motivation/about fields with AI-generated content
        text_areas = [
            (['textarea[name*="motivation"]', 'textarea[name*="why"]', 'textarea[placeholder*="Why"]'],
             application.generated_motivation if application else '', 'motivation'),
            
            (['textarea[name*="project"]', 'textarea[name*="idea"]'],
             application.generated_project_idea if application else '', 'project_idea'),
            
            (['textarea[name*="about"]', 'textarea[name*="bio"]'],
             profile.bio if profile else '', 'bio'),
        ]
        
        for selectors, value, field_name in text_areas:
            if not value:
                continue
                
            for selector in selectors:
                try:
                    field = page.locator(selector).first
                    if await field.count() > 0 and await field.is_visible():
                        await field.fill(value)
                        submitted_data[field_name] = value[:100] + '...' if len(value) > 100 else value
                        break
                except:
                    continue
        
        # Handle resume upload if needed
        resume_input = page.locator('input[type="file"]')
        if profile and profile.resume_path and await resume_input.count() > 0:
            try:
                await resume_input.first.set_input_files(profile.resume_path)
                submitted_data['resume'] = 'uploaded'
            except:
                submitted_data['resume'] = 'upload_failed'
        
        return submitted_data

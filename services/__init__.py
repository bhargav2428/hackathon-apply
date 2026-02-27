"""
Services Package Initialization
"""
from services.ai_service import AIService
from services.eligibility_checker import EligibilityChecker
from services.auto_apply import AutoApplyBot
from services.notification_service import NotificationService
from services.resume_parser import parse_resume
from services.scrapers import scrape_all_sources, scrape_source

__all__ = [
    'AIService',
    'EligibilityChecker',
    'AutoApplyBot',
    'NotificationService',
    'parse_resume',
    'scrape_all_sources',
    'scrape_source'
]

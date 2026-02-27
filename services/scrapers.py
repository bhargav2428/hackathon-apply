"""
Hackathon Scrapers - Scrape hackathons from various sources
"""
import os
import re
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from models.hackathon import Hackathon


# User agent for requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}


def scrape_all_sources() -> Dict[str, Any]:
    """Scrape hackathons from all sources"""
    results = {
        'total': 0,
        'new': 0,
        'updated': 0,
        'errors': [],
        'by_source': {}
    }
    
    scrapers = [
        ('devpost', scrape_devpost),
        ('unstop', scrape_unstop),
        ('mlh', scrape_mlh),
        ('hack2skill', scrape_hack2skill),
    ]
    
    for source_name, scraper_func in scrapers:
        try:
            source_result = scraper_func()
            results['by_source'][source_name] = source_result
            results['total'] += source_result.get('total', 0)
            results['new'] += source_result.get('new', 0)
            results['updated'] += source_result.get('updated', 0)
        except Exception as e:
            results['errors'].append({
                'source': source_name,
                'error': str(e)
            })
    
    return results


def scrape_source(source: str) -> Dict[str, Any]:
    """Scrape hackathons from a specific source"""
    scrapers = {
        'devpost': scrape_devpost,
        'unstop': scrape_unstop,
        'mlh': scrape_mlh,
        'hack2skill': scrape_hack2skill,
    }
    
    if source.lower() not in scrapers:
        raise ValueError(f'Unknown source: {source}')
    
    return scrapers[source.lower()]()


def scrape_devpost() -> Dict[str, Any]:
    """Scrape hackathons from Devpost"""
    results = {'total': 0, 'new': 0, 'updated': 0, 'hackathons': []}
    
    try:
        # Devpost hackathons page
        url = 'https://devpost.com/hackathons'
        params = {
            'challenge_type[]': ['online', 'in-person'],
            'status[]': ['upcoming', 'open']
        }
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find hackathon tiles
        hackathon_tiles = soup.select('.hackathon-tile, .challenge-listing')
        
        for tile in hackathon_tiles:
            try:
                hackathon_data = _parse_devpost_tile(tile)
                if hackathon_data:
                    saved = _save_hackathon(hackathon_data, 'devpost')
                    results['total'] += 1
                    if saved == 'new':
                        results['new'] += 1
                    elif saved == 'updated':
                        results['updated'] += 1
                    results['hackathons'].append(hackathon_data['name'])
            except Exception as e:
                print(f"Error parsing Devpost tile: {e}")
                continue
        
        # Also try API endpoint
        api_url = 'https://devpost.com/api/hackathons'
        try:
            api_response = requests.get(api_url, headers=HEADERS, timeout=30)
            if api_response.status_code == 200:
                api_data = api_response.json()
                for hackathon in api_data.get('hackathons', []):
                    hackathon_data = _parse_devpost_api(hackathon)
                    if hackathon_data:
                        saved = _save_hackathon(hackathon_data, 'devpost')
                        if hackathon_data['name'] not in results['hackathons']:
                            results['total'] += 1
                            if saved == 'new':
                                results['new'] += 1
                            elif saved == 'updated':
                                results['updated'] += 1
        except:
            pass
    
    except Exception as e:
        results['error'] = str(e)
    
    return results


def _parse_devpost_tile(tile) -> Optional[Dict[str, Any]]:
    """Parse a Devpost hackathon tile"""
    try:
        name_elem = tile.select_one('h3, .title, .challenge-title')
        name = name_elem.get_text(strip=True) if name_elem else None
        
        if not name:
            return None
        
        link_elem = tile.select_one('a[href*="devpost.com"]')
        url = link_elem.get('href') if link_elem else None
        
        # Extract dates
        date_elem = tile.select_one('.date, .submission-period')
        deadline = None
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            deadline = _parse_date(date_text)
        
        # Extract prize
        prize_elem = tile.select_one('.prize, .prize-amount')
        prize = prize_elem.get_text(strip=True) if prize_elem else None
        
        # Check if online
        is_online = 'online' in tile.get_text().lower()
        
        # Extract tags
        tag_elems = tile.select('.tag, .theme, .technology')
        tags = [t.get_text(strip=True) for t in tag_elems]
        
        return {
            'name': name,
            'url': url,
            'registration_deadline': deadline,
            'prize_pool': prize,
            'is_online': is_online,
            'tags': tags,
            'source_id': url.split('/')[-1] if url else name[:50]
        }
    except Exception as e:
        print(f"Error in _parse_devpost_tile: {e}")
        return None


def _parse_devpost_api(data: Dict) -> Optional[Dict[str, Any]]:
    """Parse Devpost API hackathon data"""
    try:
        return {
            'name': data.get('title', ''),
            'description': data.get('tagline', ''),
            'url': data.get('url', ''),
            'registration_url': data.get('url', ''),
            'source_id': str(data.get('id', '')),
            'start_date': _parse_date(data.get('submission_period_start')),
            'end_date': _parse_date(data.get('submission_period_end')),
            'registration_deadline': _parse_date(data.get('submission_period_end')),
            'is_online': data.get('online', True),
            'location': data.get('location', ''),
            'organizer': data.get('organization_name', ''),
            'prize_pool': data.get('prize_amount', ''),
            'participants_count': data.get('registrations_count'),
            'tags': data.get('themes', []) + data.get('technologies', []),
            'themes': data.get('themes', []),
        }
    except Exception as e:
        print(f"Error in _parse_devpost_api: {e}")
        return None


def scrape_unstop() -> Dict[str, Any]:
    """Scrape hackathons from Unstop (formerly Dare2Compete)"""
    results = {'total': 0, 'new': 0, 'updated': 0, 'hackathons': []}
    
    try:
        # Unstop API endpoint
        url = 'https://unstop.com/api/public/opportunity/search-new'
        params = {
            'opportunity': 'hackathons',
            'per_page': 50,
            'oppstatus': 'open'
        }
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            for item in data.get('data', {}).get('data', []):
                try:
                    hackathon_data = {
                        'name': item.get('title', ''),
                        'description': item.get('seo_description', ''),
                        'url': f"https://unstop.com/{item.get('public_url', '')}",
                        'registration_url': f"https://unstop.com/{item.get('public_url', '')}",
                        'source_id': str(item.get('id', '')),
                        'start_date': _parse_date(item.get('start_date')),
                        'end_date': _parse_date(item.get('end_date')),
                        'registration_deadline': _parse_date(item.get('regnRequirements', {}).get('end_regn_dt')),
                        'is_online': item.get('festival_type', '') == 'online',
                        'location': item.get('region', ''),
                        'organizer': item.get('organisation', {}).get('name', ''),
                        'prize_pool': item.get('prizes', {}).get('prize_money', ''),
                        'participants_count': item.get('registerCount'),
                        'tags': [t.get('name', '') for t in item.get('filters', [])],
                        'is_student_only': item.get('eligibility', '') == 'students'
                    }
                    
                    saved = _save_hackathon(hackathon_data, 'unstop')
                    results['total'] += 1
                    if saved == 'new':
                        results['new'] += 1
                    elif saved == 'updated':
                        results['updated'] += 1
                    results['hackathons'].append(hackathon_data['name'])
                except Exception as e:
                    print(f"Error parsing Unstop item: {e}")
                    continue
        
    except Exception as e:
        results['error'] = str(e)
    
    return results


def scrape_mlh() -> Dict[str, Any]:
    """Scrape hackathons from MLH (Major League Hacking)"""
    results = {'total': 0, 'new': 0, 'updated': 0, 'hackathons': []}
    
    try:
        # MLH season page
        current_year = datetime.now().year
        url = f'https://mlh.io/seasons/{current_year}/events'
        
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find event cards
        event_cards = soup.select('.event, .event-card, [class*="EventCard"]')
        
        for card in event_cards:
            try:
                name_elem = card.select_one('h3, .event-name, .name')
                name = name_elem.get_text(strip=True) if name_elem else None
                
                if not name:
                    continue
                
                link_elem = card.select_one('a[href]')
                url = link_elem.get('href') if link_elem else None
                
                date_elem = card.select_one('.event-date, .date')
                date_text = date_elem.get_text(strip=True) if date_elem else None
                
                location_elem = card.select_one('.event-location, .location')
                location = location_elem.get_text(strip=True) if location_elem else None
                
                hackathon_data = {
                    'name': name,
                    'url': url,
                    'registration_url': url,
                    'source_id': url.split('/')[-1] if url else name[:50],
                    'start_date': _parse_date(date_text),
                    'is_online': 'digital' in (location or '').lower() or 'online' in (location or '').lower(),
                    'location': location,
                    'organizer': 'MLH',
                    'tags': ['MLH', 'Student'],
                    'is_student_only': True
                }
                
                saved = _save_hackathon(hackathon_data, 'mlh')
                results['total'] += 1
                if saved == 'new':
                    results['new'] += 1
                elif saved == 'updated':
                    results['updated'] += 1
                results['hackathons'].append(hackathon_data['name'])
            except Exception as e:
                print(f"Error parsing MLH card: {e}")
                continue
    
    except Exception as e:
        results['error'] = str(e)
    
    return results


def scrape_hack2skill() -> Dict[str, Any]:
    """Scrape hackathons from Hack2Skill"""
    results = {'total': 0, 'new': 0, 'updated': 0, 'hackathons': []}
    
    try:
        url = 'https://hack2skill.com/hackathons'
        
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find hackathon cards
        cards = soup.select('.hackathon-card, .event-card, [class*="hackathon"]')
        
        for card in cards:
            try:
                name_elem = card.select_one('h3, h4, .title')
                name = name_elem.get_text(strip=True) if name_elem else None
                
                if not name:
                    continue
                
                link_elem = card.select_one('a[href]')
                hackathon_url = link_elem.get('href') if link_elem else None
                if hackathon_url and not hackathon_url.startswith('http'):
                    hackathon_url = f'https://hack2skill.com{hackathon_url}'
                
                hackathon_data = {
                    'name': name,
                    'url': hackathon_url,
                    'registration_url': hackathon_url,
                    'source_id': hackathon_url.split('/')[-1] if hackathon_url else name[:50],
                    'is_online': True,
                    'tags': ['Hack2Skill'],
                }
                
                saved = _save_hackathon(hackathon_data, 'hack2skill')
                results['total'] += 1
                if saved == 'new':
                    results['new'] += 1
                elif saved == 'updated':
                    results['updated'] += 1
                results['hackathons'].append(hackathon_data['name'])
            except Exception as e:
                print(f"Error parsing Hack2Skill card: {e}")
                continue
    
    except Exception as e:
        results['error'] = str(e)
    
    return results


def _save_hackathon(data: Dict[str, Any], source: str) -> str:
    """Save hackathon to database, return 'new', 'updated', or 'unchanged'"""
    try:
        name = data.get('name', 'Unknown')
        url = data.get('url', '')
        
        # Check if already exists (by name or url)
        existing = Hackathon.objects(name=name).first()
        if not existing and url:
            existing = Hackathon.objects(url=url).first()
        
        if existing:
            # Update existing
            existing.description = data.get('description', existing.description)
            existing.url = data.get('url', existing.url)
            existing.prize = data.get('prize_pool', existing.prize)
            existing.tags = data.get('tags', existing.tags) or []
            existing.themes = data.get('themes', existing.themes) or []
            existing.updated_at = datetime.utcnow()
            existing.save()
            return 'updated'
        else:
            # Create new
            hackathon = Hackathon(
                name=name,
                description=data.get('description'),
                url=url,
                deadline=data.get('registration_deadline') or data.get('end_date'),
                prize=data.get('prize_pool'),
                tags=data.get('tags', []),
                themes=data.get('themes', []),
                required_skills=[],
                source=source,
                is_active=True
            )
            hackathon.save()
            return 'new'
    except Exception as e:
        print(f"Error saving hackathon: {e}")
        return 'error'


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse various date formats"""
    if not date_str:
        return None
    
    # Common date formats
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%B %d, %Y',
        '%b %d, %Y',
        '%d %B %Y',
        '%d %b %Y',
        '%m/%d/%Y',
        '%d/%m/%Y',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except:
            continue
    
    return None

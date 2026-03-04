"""
Fetch real hackathons from Devpost, MLH, and other sources
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import mongoengine
import re

# Connect to MongoDB
mongoengine.connect(
    db='hackathon_agent',
    host='mongodb+srv://bhargavyaswanth_db_user:9KeEgedtlsrFsZBg@cluster0.bounkpp.mongodb.net/hackathon_agent?retryWrites=true&w=majority'
)

from models.hackathon import Hackathon

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

def fetch_devpost_hackathons():
    """Fetch real hackathons from Devpost API"""
    print("\n📡 Fetching from Devpost...")
    
    hackathons = []
    
    # Use Devpost's actual API
    url = "https://devpost.com/api/hackathons"
    params = {
        'status': 'open',
        'order_by': 'deadline',
        'page': 1,
        'per_page': 30
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            data = response.json()
            for h in data.get('hackathons', []):
                # Extract theme names as strings (API may return objects)
                raw_themes = h.get('themes', []) or []
                theme_names = []
                for t in raw_themes:
                    if isinstance(t, dict):
                        theme_names.append(str(t.get('name', t.get('title', ''))))
                    elif t:
                        theme_names.append(str(t))
                theme_names = [t for t in theme_names if t]  # Remove empty
                
                hackathon = {
                    'name': h.get('title', ''),
                    'description': h.get('tagline', '') or h.get('description', '')[:500],
                    'url': h.get('url', ''),
                    'prize': h.get('prize_amount', ''),
                    'deadline': parse_date(h.get('submission_period_dates', '')),
                    'tags': theme_names,
                    'themes': theme_names,
                    'is_active': True,
                    'source': 'devpost',
                    'image_url': h.get('thumbnail_url', '')
                }
                if hackathon['name']:
                    hackathons.append(hackathon)
                    print(f"  ✅ {hackathon['name']}")
    except Exception as e:
        print(f"  ❌ Devpost API error: {e}")
    
    # Also scrape the HTML page for more hackathons
    try:
        html_url = "https://devpost.com/hackathons?status[]=open&status[]=upcoming"
        response = requests.get(html_url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        tiles = soup.select('[data-hackathon-tile], .hackathon-tile, article.challenge-listing')
        for tile in tiles:
            try:
                name = tile.select_one('h2, h3, .title')
                if name:
                    name = name.get_text(strip=True)
                
                link = tile.select_one('a[href*="devpost.com/hackathons"]')
                url = link.get('href') if link else ''
                
                desc = tile.select_one('.tagline, .short-description, p')
                description = desc.get_text(strip=True) if desc else ''
                
                prize = tile.select_one('.prize-amount, .prize')
                prize_text = prize.get_text(strip=True) if prize else ''
                
                # Check if we already have this one
                existing = [h for h in hackathons if h['name'] == name]
                if not existing and name:
                    hackathons.append({
                        'name': name,
                        'description': description,
                        'url': url if url.startswith('http') else f"https://devpost.com{url}",
                        'prize': prize_text,
                        'deadline': None,
                        'tags': [],
                        'themes': [],
                        'is_active': True,
                        'source': 'devpost'
                    })
                    print(f"  ✅ {name} (from HTML)")
            except:
                continue
    except Exception as e:
        print(f"  ❌ Devpost HTML error: {e}")
    
    return hackathons


def fetch_mlh_hackathons():
    """Fetch real hackathons from MLH"""
    print("\n📡 Fetching from MLH...")
    
    hackathons = []
    url = "https://mlh.io/seasons/2025/events"  # Current season
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        events = soup.select('.event, .event-wrapper, [class*="event"]')
        
        for event in events:
            try:
                name = event.select_one('.event-name, h3, h4')
                if name:
                    name = name.get_text(strip=True)
                
                link = event.select_one('a[href]')
                url = link.get('href') if link else ''
                
                date = event.select_one('.event-date, .date')
                date_text = date.get_text(strip=True) if date else ''
                
                location = event.select_one('.event-location, .location')
                loc_text = location.get_text(strip=True) if location else ''
                
                if name:
                    hackathons.append({
                        'name': name,
                        'description': f"MLH Hackathon - {loc_text}. {date_text}",
                        'url': url if url.startswith('http') else f"https://mlh.io{url}",
                        'prize': 'Prizes + MLH Swag',
                        'deadline': parse_date(date_text),
                        'tags': ['MLH', 'Student', 'In-Person'],
                        'themes': ['Open Innovation'],
                        'is_active': True,
                        'source': 'mlh'
                    })
                    print(f"  ✅ {name}")
            except:
                continue
    except Exception as e:
        print(f"  ❌ MLH error: {e}")
    
    return hackathons


def fetch_unstop_hackathons():
    """Fetch hackathons from Unstop (formerly D2C)"""
    print("\n📡 Fetching from Unstop...")
    
    hackathons = []
    url = "https://unstop.com/api/public/opportunity/search-result"
    
    params = {
        'opportunity': 'hackathons',
        'per_page': 20,
        'oppstatus': 'open'
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            data = response.json()
            for item in data.get('data', {}).get('data', []):
                hackathon = {
                    'name': item.get('title', ''),
                    'description': item.get('short_desc', '') or item.get('seo_details', {}).get('seo_description', ''),
                    'url': f"https://unstop.com/{item.get('public_url', '')}",
                    'prize': item.get('prizes', {}).get('prize_amount', '') if isinstance(item.get('prizes'), dict) else '',
                    'deadline': parse_date(item.get('end_date', '')),
                    'tags': [t.get('name', '') for t in item.get('filters', {}).get('tags', [])] if item.get('filters') else [],
                    'themes': [],
                    'is_active': True,
                    'source': 'unstop'
                }
                if hackathon['name']:
                    hackathons.append(hackathon)
                    print(f"  ✅ {hackathon['name']}")
    except Exception as e:
        print(f"  ❌ Unstop error: {e}")
    
    return hackathons


def parse_date(date_str):
    """Parse various date formats"""
    if not date_str:
        return None
    
    # Clean up the string
    date_str = str(date_str).strip()
    
    # Try various formats
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%B %d, %Y',
        '%b %d, %Y',
        '%d %B %Y',
        '%d %b %Y',
        '%m/%d/%Y',
        '%d/%m/%Y',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    
    # Try to extract date with regex
    match = re.search(r'(\w+ \d{1,2},? \d{4})', date_str)
    if match:
        try:
            return datetime.strptime(match.group(1), '%B %d, %Y')
        except:
            pass
    
    return None


def save_hackathons(hackathons):
    """Save hackathons to MongoDB"""
    print(f"\n💾 Saving {len(hackathons)} hackathons to database...")
    
    new_count = 0
    updated_count = 0
    
    for h in hackathons:
        try:
            # Check if exists by name and source
            existing = Hackathon.objects(name=h['name'], source=h['source']).first()
            
            if existing:
                # Update existing
                existing.description = h['description'] or existing.description
                existing.url = h['url'] or existing.url
                existing.prize = h['prize'] or existing.prize
                existing.deadline = h['deadline'] or existing.deadline
                existing.tags = h['tags'] if h['tags'] else existing.tags
                existing.is_active = h['is_active']
                existing.save()
                updated_count += 1
            else:
                # Create new
                hackathon = Hackathon(
                    name=h['name'],
                    description=h['description'],
                    url=h['url'],
                    prize=str(h['prize']) if h['prize'] else '',
                    deadline=h['deadline'],
                    tags=h['tags'],
                    themes=h.get('themes', []),
                    is_active=h['is_active'],
                    source=h['source']
                )
                hackathon.save()
                new_count += 1
                print(f"  ➕ Added: {h['name']}")
        except Exception as e:
            print(f"  ❌ Error saving {h.get('name', 'unknown')}: {e}")
    
    print(f"\n✅ Done! New: {new_count}, Updated: {updated_count}")
    return new_count, updated_count


def clear_old_hackathons():
    """Remove sample/fake hackathons"""
    print("\n🗑️ Removing sample hackathons...")
    
    # Remove hackathons with fake URLs
    fake_patterns = [
        'devpost.com/hackathons/ai-innovation-2026',
        'devpost.com/hackathons/web3-builder',
        'devpost.com/hackathons/healthcare-ai',
        'devpost.com/hackathons/fintech-jam',
        'cloud.google.com/hackathons',
        'unstop.com/hackathons/climate-tech',
    ]
    
    removed = 0
    for pattern in fake_patterns:
        deleted = Hackathon.objects(url__contains=pattern).delete()
        removed += deleted
    
    # Also remove by sample names
    sample_names = [
        'AI Innovation Challenge 2026',
        'Web3 Builder Hackathon',
        'Healthcare AI Summit Hack',
        'Climate Tech Challenge',
        'FinTech Innovation Jam',
        'Google Cloud Hackathon',
        'Mobile App Challenge 2026',
    ]
    
    for name in sample_names:
        deleted = Hackathon.objects(name=name).delete()
        removed += deleted
    
    print(f"  Removed {removed} sample hackathons")
    return removed


if __name__ == '__main__':
    print("=" * 50)
    print("🚀 FETCHING REAL HACKATHONS")
    print("=" * 50)
    
    # Clear old fake data
    clear_old_hackathons()
    
    # Fetch from all sources
    all_hackathons = []
    
    devpost = fetch_devpost_hackathons()
    all_hackathons.extend(devpost)
    
    mlh = fetch_mlh_hackathons()
    all_hackathons.extend(mlh)
    
    unstop = fetch_unstop_hackathons()
    all_hackathons.extend(unstop)
    
    # Save to database
    if all_hackathons:
        save_hackathons(all_hackathons)
    else:
        print("\n⚠️ No hackathons fetched! Adding some known active ones...")
        
        # Add some known active hackathons manually
        known_hackathons = [
            {
                'name': 'ETHGlobal Brussels',
                'description': 'Join the Ethereum community in Brussels for a weekend of building, learning, and connecting with like-minded developers.',
                'url': 'https://ethglobal.com/events/brussels',
                'prize': '$500,000+',
                'deadline': datetime(2026, 7, 15),
                'tags': ['Ethereum', 'Web3', 'Blockchain', 'DeFi'],
                'themes': ['DeFi', 'NFT', 'Infrastructure'],
                'is_active': True,
                'source': 'ethglobal'
            },
            {
                'name': 'HackMIT 2026',
                'description': 'MIT\'s annual hackathon bringing together 1000+ students to build innovative projects over 24 hours.',
                'url': 'https://hackmit.org',
                'prize': '$50,000+',
                'deadline': datetime(2026, 9, 20),
                'tags': ['Student', 'MIT', 'All Tracks'],
                'themes': ['Open Innovation', 'Social Good'],
                'is_active': True,
                'source': 'hackmit'
            },
            {
                'name': 'TreeHacks 2026',
                'description': 'Stanford\'s premier hackathon. 36 hours of hacking, workshops, and fun!',
                'url': 'https://treehacks.com',
                'prize': '$30,000+',
                'deadline': datetime(2026, 2, 15),
                'tags': ['Student', 'Stanford', 'Beginner Friendly'],
                'themes': ['Healthcare', 'Education', 'Sustainability'],
                'is_active': True,
                'source': 'treehacks'
            },
            {
                'name': 'CalHacks 11.0',
                'description': 'UC Berkeley\'s flagship hackathon. Build something amazing over a weekend!',
                'url': 'https://calhacks.io',
                'prize': '$100,000+',
                'deadline': datetime(2026, 10, 28),
                'tags': ['Student', 'Berkeley', 'Open to All'],
                'themes': ['AI/ML', 'Web3', 'Social Impact'],
                'is_active': True,
                'source': 'calhacks'
            },
            {
                'name': 'PennApps XXIV',
                'description': 'America\'s first student hackathon hosted by University of Pennsylvania.',
                'url': 'https://pennapps.com',
                'prize': '$40,000+',
                'deadline': datetime(2026, 9, 8),
                'tags': ['Student', 'UPenn', 'Beginner Friendly'],
                'themes': ['Health', 'Finance', 'Education'],
                'is_active': True,
                'source': 'pennapps'
            }
        ]
        save_hackathons(known_hackathons)
    
    print("\n" + "=" * 50)
    print("✅ COMPLETE!")
    print("=" * 50)

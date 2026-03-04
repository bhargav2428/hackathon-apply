"""Hackathon Routes - MongoDB"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from models.hackathon import Hackathon
from datetime import datetime

hackathons_bp = Blueprint('hackathons', __name__)


@hackathons_bp.route('', methods=['GET'])
@login_required
def get_hackathons():
    is_active = request.args.get('active', 'true').lower() == 'true'
    
    if is_active:
        # Get hackathons that are active AND either have no deadline OR deadline is in the future
        hackathons = Hackathon.objects(
            is_active=True
        ).order_by('-created_at')
        # Filter in Python to handle None deadlines
        hackathons = [h for h in hackathons if h.deadline is None or h.deadline >= datetime.utcnow()]
    else:
        hackathons = list(Hackathon.objects().order_by('-created_at'))
    
    return jsonify({
        'hackathons': [h.to_dict() for h in hackathons]
    }), 200


@hackathons_bp.route('/<hackathon_id>', methods=['GET'])
@login_required
def get_hackathon(hackathon_id):
    hackathon = Hackathon.objects(id=hackathon_id).first()
    if not hackathon:
        return jsonify({'error': 'Hackathon not found'}), 404
    return jsonify(hackathon.to_dict()), 200


@hackathons_bp.route('', methods=['POST'])
@login_required
def create_hackathon():
    data = request.get_json()
    
    hackathon = Hackathon(
        name=data.get('name'),
        description=data.get('description'),
        url=data.get('url'),
        deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None,
        prize=data.get('prize'),
        tags=data.get('tags', []),
        themes=data.get('themes', []),
        required_skills=data.get('required_skills', [])
    )
    hackathon.save()
    
    return jsonify({'message': 'Hackathon created', 'hackathon': hackathon.to_dict()}), 201


@hackathons_bp.route('/search', methods=['GET'])
@login_required
def search_hackathons():
    q = request.args.get('q', '')
    if not q:
        return jsonify({'hackathons': []}), 200
    
    hackathons = Hackathon.objects(
        __raw__={'$or': [
            {'name': {'$regex': q, '$options': 'i'}},
            {'description': {'$regex': q, '$options': 'i'}},
            {'tags': {'$regex': q, '$options': 'i'}}
        ]}
    )
    
    return jsonify({
        'hackathons': [h.to_dict() for h in hackathons]
    }), 200


@hackathons_bp.route('/ai-search', methods=['POST'])
@login_required
def ai_search_hackathons():
    """Use AI to find the most relevant hackathons based on user query"""
    from services.ai_service import AIService
    import json
    
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    # Get all active hackathons
    all_hackathons = Hackathon.objects(
        is_active=True,
        deadline__gte=datetime.utcnow()
    )
    
    if not all_hackathons:
        return jsonify({
            'hackathons': [],
            'message': 'No active hackathons found'
        }), 200
    
    # Prepare hackathon summaries for AI
    hackathon_list = []
    for h in all_hackathons:
        hackathon_list.append({
            'id': str(h.id),
            'name': h.name,
            'description': h.description or '',
            'tags': h.tags or [],
            'themes': h.themes or [],
            'prize': h.prize or '',
            'deadline': h.deadline.isoformat() if h.deadline else ''
        })
    
    # Use AI to rank hackathons
    ai_service = AIService()
    
    prompt = f"""You are a hackathon matchmaking assistant. Given the user's query and a list of hackathons, 
identify the most relevant hackathons that match what the user is looking for.

User Query: {query}

Available Hackathons:
{json.dumps(hackathon_list, indent=2)}

Return a JSON array of hackathon IDs ranked by relevance (most relevant first).
Only include hackathons that actually match the user's interests.
Format: ["id1", "id2", "id3"]
If no hackathons match, return an empty array: []
Only return the JSON array, no other text."""

    try:
        response = ai_service._call_groq([
            {"role": "system", "content": "You are a helpful assistant that returns only valid JSON arrays."},
            {"role": "user", "content": prompt}
        ], temperature=0.3)
        
        # Parse AI response
        relevant_ids = json.loads(response.strip())
        
        # Get hackathons in order
        result_hackathons = []
        for hid in relevant_ids:
            h = Hackathon.objects(id=hid).first()
            if h:
                result_hackathons.append(h.to_dict())
        
        return jsonify({
            'hackathons': result_hackathons,
            'ai_response': response
        }), 200
        
    except Exception as e:
        # Fall back to regular search
        hackathons = Hackathon.objects(
            __raw__={'$or': [
                {'name': {'$regex': query, '$options': 'i'}},
                {'description': {'$regex': query, '$options': 'i'}},
                {'tags': {'$regex': query, '$options': 'i'}}
            ]}
        )
        return jsonify({
            'hackathons': [h.to_dict() for h in hackathons],
            'error': f'AI search failed, using fallback: {str(e)}'
        }), 200


@hackathons_bp.route('/all', methods=['GET'])
@login_required  
def get_all_hackathons():
    """Get all hackathons without filtering"""
    hackathons = Hackathon.objects().order_by('-created_at')
    return jsonify({
        'hackathons': [h.to_dict() for h in hackathons],
        'total': hackathons.count()
    }), 200


@hackathons_bp.route('/clear-and-refresh', methods=['POST'])
@login_required
def clear_and_refresh_hackathons():
    """Delete all hackathons and fetch fresh data"""
    try:
        deleted = Hackathon.objects.delete()
        return jsonify({
            'message': f'Deleted {deleted} hackathons. Click Refresh to fetch new ones.',
            'deleted': deleted
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@hackathons_bp.route('/seed', methods=['POST'])
@login_required
def seed_hackathons():
    """Add sample hackathons for testing"""
    sample_hackathons = [
        {
            'name': 'Amazon Nova AI Hackathon',
            'description': 'Build innovative AI solutions using Amazon Nova',
            'url': 'https://amazon-nova.devpost.com/',
            'prize': '$30,000',
            'tags': ['AI', 'Machine Learning', 'AWS'],
            'themes': ['Artificial Intelligence'],
            'is_active': True,
            'source': 'devpost'
        },
        {
            'name': 'Gemini Live Agent Challenge',
            'description': 'Create live agents powered by Gemini',
            'url': 'https://geminiliveagentchallenge.devpost.com/',
            'prize': '$50,000',
            'tags': ['AI', 'Agents', 'Google'],
            'themes': ['AI Agents'],
            'is_active': True,
            'source': 'devpost'
        },
        {
            'name': 'GitLab AI Hackathon',
            'description': 'Build AI-powered DevOps tools',
            'url': 'https://gitlab.devpost.com/',
            'prize': '$25,000',
            'tags': ['DevOps', 'AI', 'GitLab'],
            'themes': ['Developer Tools'],
            'is_active': True,
            'source': 'devpost'
        },
        {
            'name': 'DigitalOcean Gradient AI Hackathon',
            'description': 'Use DigitalOcean GPU Droplets to build AI apps',
            'url': 'https://gradient.devpost.com/',
            'prize': '$15,000',
            'tags': ['Cloud', 'AI', 'GPU'],
            'themes': ['Cloud Computing'],
            'is_active': True,
            'source': 'devpost'
        },
        {
            'name': 'Airia AI Agents Hackathon',
            'description': 'Build autonomous AI agents',
            'url': 'https://airia.devpost.com/',
            'prize': '$20,000',
            'tags': ['AI', 'Agents', 'Autonomous'],
            'themes': ['Artificial Intelligence'],
            'is_active': True,
            'source': 'devpost'
        }
    ]
    
    added = 0
    for h_data in sample_hackathons:
        existing = Hackathon.objects(name=h_data['name']).first()
        if not existing:
            hackathon = Hackathon(**h_data)
            hackathon.save()
            added += 1
    
    return jsonify({
        'message': f'Added {added} sample hackathons',
        'added': added
    }), 200


@hackathons_bp.route('/fetch-from-web', methods=['POST'])
@login_required
def fetch_hackathons_from_web():
    """Fetch new hackathons from multiple sources: Devpost, MLH, Unstop, HackerEarth"""
    import requests
    from bs4 import BeautifulSoup
    
    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception as e:
        print(f"Error getting JSON: {e}")
        data = {}
    
    query = data.get('query', '')
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    new_hackathons = []
    sources_fetched = []
    
    # Helper to save or update hackathon
    def save_hackathon(hackathon_data):
        if not hackathon_data.get('name'):
            return None
        existing = Hackathon.objects(name=hackathon_data['name']).first()
        if existing:
            # Update URL if missing or empty
            if hackathon_data.get('url') and not existing.url:
                existing.url = hackathon_data['url']
                existing.save()
            return None  # Not new, so don't count it
        else:
            hackathon = Hackathon(**hackathon_data)
            hackathon.save()
            return hackathon.to_dict()
    
    # 1. DEVPOST
    try:
        url = "https://devpost.com/api/hackathons"
        params = {'status': 'open', 'order_by': 'deadline', 'page': 1, 'per_page': 30}
        if query:
            params['search'] = query
        
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            api_data = response.json()
            for h in api_data.get('hackathons', []):
                raw_themes = h.get('themes', []) or []
                theme_names = [str(t.get('name', '')) if isinstance(t, dict) else str(t) for t in raw_themes if t]
                
                saved = save_hackathon({
                    'name': h.get('title', ''),
                    'description': h.get('tagline', '') or '',
                    'url': h.get('url', ''),
                    'prize': str(h.get('prize_amount', '')) if h.get('prize_amount') else '',
                    'tags': theme_names,
                    'themes': theme_names,
                    'is_active': True,
                    'source': 'devpost'
                })
                if saved:
                    new_hackathons.append(saved)
            sources_fetched.append('Devpost')
    except Exception as e:
        print(f"Devpost error: {e}")
    
    # 2. MLH (Major League Hacking)
    try:
        mlh_url = "https://mlh.io/seasons/2025/events"
        response = requests.get(mlh_url, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            events = soup.select('.event, .event-wrapper, [data-event]')
            
            for event in events[:20]:
                try:
                    name_el = event.select_one('.event-name, h3, h4, .name')
                    name = name_el.get_text(strip=True) if name_el else ''
                    
                    link_el = event.select_one('a[href]')
                    url = link_el.get('href', '') if link_el else ''
                    if url and not url.startswith('http'):
                        url = f"https://mlh.io{url}"
                    
                    date_el = event.select_one('.event-date, .date')
                    date_text = date_el.get_text(strip=True) if date_el else ''
                    
                    loc_el = event.select_one('.event-location, .location')
                    loc_text = loc_el.get_text(strip=True) if loc_el else ''
                    
                    if name and (not query or query.lower() in name.lower()):
                        saved = save_hackathon({
                            'name': name,
                            'description': f"MLH Hackathon - {loc_text}. {date_text}",
                            'url': url,
                            'prize': 'MLH Prizes + Swag',
                            'tags': ['MLH', 'Student', 'In-Person'],
                            'themes': ['Open Innovation'],
                            'is_active': True,
                            'source': 'mlh'
                        })
                        if saved:
                            new_hackathons.append(saved)
                except:
                    continue
            sources_fetched.append('MLH')
    except Exception as e:
        print(f"MLH error: {e}")
    
    # 3. UNSTOP (formerly Dare2Compete)
    try:
        unstop_url = "https://unstop.com/api/public/opportunity/search-new"
        unstop_data = {
            "opportunity": ["hackathons"],
            "oppstatus": ["open"],
            "size": 30,
            "page": 1
        }
        if query:
            unstop_data["searchTerm"] = query
        
        response = requests.post(unstop_url, json=unstop_data, headers={**HEADERS, 'Content-Type': 'application/json'}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get('data', {}).get('data', []) if isinstance(data.get('data'), dict) else []
            
            for opp in opportunities[:20]:
                if isinstance(opp, dict):
                    name = opp.get('title', '') or opp.get('name', '')
                    saved = save_hackathon({
                        'name': name,
                        'description': opp.get('seo_details', {}).get('seo_description', '') if isinstance(opp.get('seo_details'), dict) else '',
                        'url': f"https://unstop.com/{opp.get('public_url', '')}" if opp.get('public_url') else '',
                        'prize': opp.get('prizes', ''),
                        'tags': ['Unstop', 'Online'],
                        'themes': [],
                        'is_active': True,
                        'source': 'unstop'
                    })
                    if saved:
                        new_hackathons.append(saved)
            sources_fetched.append('Unstop')
    except Exception as e:
        print(f"Unstop error: {e}")
    
    # 4. HACKEREARTH
    try:
        he_url = "https://www.hackerearth.com/challenges/hackathon/"
        response = requests.get(he_url, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            challenges = soup.select('.challenge-card, .challenge, .event-card')
            
            for card in challenges[:20]:
                try:
                    name_el = card.select_one('.challenge-name, .title, h3, h4')
                    name = name_el.get_text(strip=True) if name_el else ''
                    
                    link_el = card.select_one('a[href]')
                    url = link_el.get('href', '') if link_el else ''
                    if url and not url.startswith('http'):
                        url = f"https://www.hackerearth.com{url}"
                    
                    desc_el = card.select_one('.challenge-desc, .description, p')
                    desc = desc_el.get_text(strip=True) if desc_el else ''
                    
                    if name and (not query or query.lower() in name.lower()):
                        saved = save_hackathon({
                            'name': name,
                            'description': desc,
                            'url': url,
                            'prize': '',
                            'tags': ['HackerEarth', 'Online'],
                            'themes': [],
                            'is_active': True,
                            'source': 'hackerearth'
                        })
                        if saved:
                            new_hackathons.append(saved)
                except:
                    continue
            sources_fetched.append('HackerEarth')
    except Exception as e:
        print(f"HackerEarth error: {e}")
    
    # 5. HACKATHON.COM
    try:
        hcom_url = "https://www.hackathon.com/online"
        response = requests.get(hcom_url, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            events = soup.select('.ht-eb-card, .event-card, article')
            
            for event in events[:15]:
                try:
                    name_el = event.select_one('h2, h3, .title, .event-name')
                    name = name_el.get_text(strip=True) if name_el else ''
                    
                    link_el = event.select_one('a[href]')
                    url = link_el.get('href', '') if link_el else ''
                    
                    if name and (not query or query.lower() in name.lower()):
                        saved = save_hackathon({
                            'name': name,
                            'description': '',
                            'url': url if url.startswith('http') else f"https://www.hackathon.com{url}",
                            'prize': '',
                            'tags': ['Online', 'Global'],
                            'themes': [],
                            'is_active': True,
                            'source': 'hackathon.com'
                        })
                        if saved:
                            new_hackathons.append(saved)
                except:
                    continue
            sources_fetched.append('Hackathon.com')
    except Exception as e:
        print(f"Hackathon.com error: {e}")
    
    # Get all matching hackathons
    if query:
        all_matching = Hackathon.objects(
            __raw__={'$or': [
                {'name': {'$regex': query, '$options': 'i'}},
                {'description': {'$regex': query, '$options': 'i'}},
                {'tags': {'$regex': query, '$options': 'i'}},
                {'themes': {'$regex': query, '$options': 'i'}}
            ]}
        ).order_by('-created_at')
    else:
        all_matching = Hackathon.objects(is_active=True).order_by('-created_at')
    
    return jsonify({
        'hackathons': [h.to_dict() for h in all_matching],
        'hackathons_added': len(new_hackathons),
        'total': all_matching.count(),
        'sources_checked': sources_fetched,
        'message': f'Fetched from {", ".join(sources_fetched)}. Found {all_matching.count()} hackathons, {len(new_hackathons)} new.'
    }), 200

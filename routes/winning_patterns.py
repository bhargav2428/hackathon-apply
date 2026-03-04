"""
Winning Patterns Routes - Analyze winning hackathon projects
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models.winning_patterns import WinningProject, WinningPattern
from models.hackathon import Hackathon
from services.ai_service import AIService
import requests
from bs4 import BeautifulSoup
import re

winning_patterns_bp = Blueprint('winning_patterns', __name__)


@winning_patterns_bp.route('/projects', methods=['GET'])
@login_required
def get_winning_projects():
    """Get winning projects with optional filters"""
    hackathon_name = request.args.get('hackathon')
    tech = request.args.get('tech')
    limit = int(request.args.get('limit', 50))
    
    query = {}
    if hackathon_name:
        query['hackathon_name__icontains'] = hackathon_name
    if tech:
        query['tech_stack__icontains'] = tech
    
    projects = WinningProject.objects(**query).order_by('-hackathon_date').limit(limit)
    return jsonify({'projects': [p.to_dict() for p in projects]}), 200


@winning_patterns_bp.route('/analyze/<hackathon_id>', methods=['POST'])
@login_required
def analyze_hackathon_patterns(hackathon_id):
    """Analyze winning patterns for a specific hackathon"""
    hackathon = Hackathon.objects(id=hackathon_id).first()
    if not hackathon:
        return jsonify({'error': 'Hackathon not found'}), 404
    
    # Get or create pattern analysis
    pattern = WinningPattern.objects(hackathon_id=hackathon_id).first()
    
    if not pattern:
        # Try to analyze based on similar hackathons
        try:
            ai = AIService()
            pattern = analyze_patterns_with_ai(hackathon, ai)
        except Exception as e:
            return jsonify({'error': f'Failed to analyze: {str(e)}'}), 500
    
    return jsonify({'patterns': pattern.to_dict()}), 200


@winning_patterns_bp.route('/scrape-devpost', methods=['POST'])
@login_required
def scrape_devpost_winners():
    """Scrape winning projects from Devpost"""
    data = request.get_json()
    hackathon_url = data.get('url')
    
    if not hackathon_url or 'devpost.com' not in hackathon_url:
        return jsonify({'error': 'Valid Devpost URL required'}), 400
    
    try:
        projects = scrape_devpost_winning_projects(hackathon_url)
        return jsonify({
            'message': f'Scraped {len(projects)} winning projects',
            'projects': projects
        }), 200
    except Exception as e:
        return jsonify({'error': f'Scraping failed: {str(e)}'}), 500


@winning_patterns_bp.route('/recommendations', methods=['GET'])
@login_required
def get_recommendations():
    """Get AI recommendations based on winning patterns"""
    hackathon_id = request.args.get('hackathon_id')
    
    if not hackathon_id:
        return jsonify({'error': 'hackathon_id is required'}), 400
    
    hackathon = Hackathon.objects(id=hackathon_id).first()
    if not hackathon:
        return jsonify({'error': 'Hackathon not found'}), 404
    
    try:
        ai = AIService()
        recommendations = generate_recommendations(hackathon, ai)
        return jsonify({'recommendations': recommendations}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to generate recommendations: {str(e)}'}), 500


@winning_patterns_bp.route('/tech-trends', methods=['GET'])
@login_required
def get_tech_trends():
    """Get trending technologies from winning projects"""
    # Aggregate tech stack usage
    pipeline = [
        {'$unwind': '$tech_stack'},
        {'$group': {'_id': '$tech_stack', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 20}
    ]
    
    try:
        from models.winning_patterns import WinningProject
        results = WinningProject.objects.aggregate(pipeline)
        trends = [{'tech': r['_id'], 'count': r['count']} for r in results]
        return jsonify({'trends': trends}), 200
    except Exception as e:
        return jsonify({'trends': []}), 200


def scrape_devpost_winning_projects(hackathon_url):
    """Scrape winning projects from a Devpost hackathon page"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Get the project gallery with winners
    gallery_url = hackathon_url.rstrip('/') + '/project-gallery?filter=winners'
    response = requests.get(gallery_url, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    projects = []
    
    # Find project cards
    for card in soup.select('.gallery-item, .software-entry'):
        try:
            project_data = {}
            
            # Project name and URL
            title_elem = card.select_one('h5 a, .software-entry-name a')
            if title_elem:
                project_data['project_name'] = title_elem.get_text(strip=True)
                project_data['project_url'] = 'https://devpost.com' + title_elem.get('href', '')
            
            # Tagline/description
            tagline = card.select_one('.tagline, .software-entry-tagline')
            if tagline:
                project_data['description'] = tagline.get_text(strip=True)
            
            # Prize info
            prize_elem = card.select_one('.winner-label, .prize')
            if prize_elem:
                project_data['prize_category'] = prize_elem.get_text(strip=True)
            
            # Extract hackathon name from URL
            match = re.search(r'devpost\.com/([^/]+)', hackathon_url)
            if match:
                project_data['hackathon_name'] = match.group(1).replace('-', ' ').title()
            
            project_data['hackathon_source'] = 'devpost'
            
            if project_data.get('project_name'):
                # Save to database
                wp = WinningProject(**project_data)
                wp.save()
                projects.append(project_data)
                
        except Exception as e:
            continue
    
    return projects


def analyze_patterns_with_ai(hackathon, ai):
    """Use AI to analyze winning patterns"""
    # Get similar winning projects
    similar_projects = WinningProject.objects(
        hackathon_name__icontains=hackathon.name[:20]
    ).limit(20)
    
    if not similar_projects:
        # Use general patterns
        similar_projects = WinningProject.objects().order_by('-scraped_at').limit(50)
    
    # Build context
    projects_context = "\n".join([
        f"- {p.project_name}: {p.tech_stack}, Prize: {p.prize_category}"
        for p in similar_projects
    ])
    
    prompt = f"""Analyze winning patterns for hackathon: {hackathon.name}

Theme/Tags: {hackathon.themes or hackathon.tags}
Description: {hackathon.description}

Similar winning projects:
{projects_context}

Provide analysis in JSON format with:
- top_tech_stacks: [{{"tech": "name", "win_rate": 0.X}}, ...]
- common_features: ["feature1", "feature2", ...]
- success_factors: [{{"factor": "name", "importance": 0.X}}, ...]
- recommendations: ["rec1", "rec2", ...]
- ai_insights: "Your analysis"
"""
    
    messages = [
        {"role": "system", "content": "You are a hackathon winning pattern analyst. Respond with valid JSON only."},
        {"role": "user", "content": prompt}
    ]
    
    response = ai._call_groq(messages, temperature=0.5)
    
    import json
    try:
        analysis = json.loads(response)
    except:
        analysis = {
            'top_tech_stacks': [],
            'common_features': [],
            'success_factors': [],
            'recommendations': [response],
            'ai_insights': response
        }
    
    pattern = WinningPattern(
        hackathon_id=str(hackathon.id),
        hackathon_name=hackathon.name,
        top_tech_stacks=analysis.get('top_tech_stacks', []),
        common_features=analysis.get('common_features', []),
        success_factors=analysis.get('success_factors', []),
        recommendations=analysis.get('recommendations', []),
        ai_insights=analysis.get('ai_insights', ''),
        projects_analyzed=len(list(similar_projects))
    )
    pattern.save()
    
    return pattern


def generate_recommendations(hackathon, ai):
    """Generate personalized recommendations"""
    prompt = f"""Based on the hackathon "{hackathon.name}" with themes {hackathon.themes or hackathon.tags}, 
    provide 5 specific recommendations for winning. Consider:
    1. Technology choices that tend to win
    2. Project scope that's achievable in hackathon time
    3. Presentation strategies
    4. Features that impress judges
    5. Common mistakes to avoid
    
    Return as JSON array of recommendation objects with 'title' and 'description' keys."""
    
    messages = [
        {"role": "system", "content": "You are a hackathon winning strategist. Respond with valid JSON only."},
        {"role": "user", "content": prompt}
    ]
    
    response = ai._call_groq(messages, temperature=0.7)
    
    import json
    try:
        recommendations = json.loads(response)
    except:
        recommendations = [{'title': 'Analysis', 'description': response}]
    
    return recommendations

"""
Post-Hackathon Tracker Routes - Track project success after hackathons
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models.post_hackathon import PostHackathonProject, PortfolioSummary
from models.hackathon import Hackathon
from models.application import Application
import requests
import re

post_hackathon_bp = Blueprint('post_hackathon', __name__)


@post_hackathon_bp.route('/projects', methods=['GET'])
@login_required
def get_my_projects():
    """Get all user's post-hackathon projects"""
    projects = PostHackathonProject.objects(user_id=str(current_user.id)).order_by('-hackathon_date')
    return jsonify({'projects': [p.to_dict() for p in projects]}), 200


@post_hackathon_bp.route('/projects', methods=['POST'])
@login_required
def create_project():
    """Track a new post-hackathon project"""
    data = request.get_json()
    
    hackathon_id = data.get('hackathon_id')
    project_name = data.get('project_name')
    
    if not project_name:
        return jsonify({'error': 'project_name required'}), 400
    
    project = PostHackathonProject(
        user_id=str(current_user.id),
        hackathon_id=hackathon_id,
        application_id=data.get('application_id'),
        project_name=project_name,
        github_url=data.get('github_url'),
        live_url=data.get('live_url'),
        demo_video_url=data.get('demo_video_url'),
        devpost_url=data.get('devpost_url'),
        final_placement=data.get('final_placement'),
        prize_won=data.get('prize_won'),
        prizes_categories=data.get('prizes_categories', []),
        lessons_learned=data.get('lessons_learned', []),
        what_went_well=data.get('what_went_well', []),
        what_to_improve=data.get('what_to_improve', [])
    )
    
    # Try to get hackathon date
    if hackathon_id:
        hackathon = Hackathon.objects(id=hackathon_id).first()
        if hackathon and hackathon.deadline:
            project.hackathon_date = hackathon.deadline
    
    project.save()
    
    # Update portfolio summary
    update_portfolio_summary(str(current_user.id))
    
    return jsonify({'project': project.to_dict()}), 201


@post_hackathon_bp.route('/projects/<project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    """Get a specific project"""
    project = PostHackathonProject.objects(id=project_id, user_id=str(current_user.id)).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    return jsonify({'project': project.to_dict()}), 200


@post_hackathon_bp.route('/projects/<project_id>', methods=['PUT'])
@login_required
def update_project(project_id):
    """Update a project"""
    project = PostHackathonProject.objects(id=project_id, user_id=str(current_user.id)).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    data = request.get_json()
    
    fields = ['project_name', 'github_url', 'live_url', 'demo_video_url', 'devpost_url',
              'final_placement', 'prize_won', 'prizes_categories', 'github_stars',
              'github_forks', 'total_users', 'monthly_active_users', 'job_offers_received',
              'interviews_from_project', 'connections_made', 'media_mentions',
              'continued_development', 'became_startup', 'startup_funding',
              'lessons_learned', 'what_went_well', 'what_to_improve']
    
    for field in fields:
        if field in data:
            setattr(project, field, data[field])
    
    project.last_updated = datetime.utcnow()
    project.save()
    
    # Update portfolio summary
    update_portfolio_summary(str(current_user.id))
    
    return jsonify({'project': project.to_dict()}), 200


@post_hackathon_bp.route('/projects/<project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    """Delete a project"""
    project = PostHackathonProject.objects(id=project_id, user_id=str(current_user.id)).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    project.delete()
    
    # Update portfolio summary
    update_portfolio_summary(str(current_user.id))
    
    return jsonify({'message': 'Project deleted'}), 200


@post_hackathon_bp.route('/projects/<project_id>/refresh-github', methods=['POST'])
@login_required
def refresh_github_stats(project_id):
    """Refresh GitHub stats for a project"""
    project = PostHackathonProject.objects(id=project_id, user_id=str(current_user.id)).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    if not project.github_url:
        return jsonify({'error': 'No GitHub URL set'}), 400
    
    try:
        stats = fetch_github_stats(project.github_url)
        
        # Add to history
        history_entry = {
            'date': datetime.utcnow().isoformat(),
            'stars': stats.get('stars', 0),
            'forks': stats.get('forks', 0),
            'watchers': stats.get('watchers', 0)
        }
        
        if not project.metrics_history:
            project.metrics_history = []
        project.metrics_history.append(history_entry)
        
        # Update current values
        project.github_stars = stats.get('stars', project.github_stars)
        project.github_forks = stats.get('forks', project.github_forks)
        project.github_watchers = stats.get('watchers', project.github_watchers)
        project.last_updated = datetime.utcnow()
        project.save()
        
        # Update portfolio
        update_portfolio_summary(str(current_user.id))
        
        return jsonify({'project': project.to_dict(), 'stats': stats}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch GitHub stats: {str(e)}'}), 500


@post_hackathon_bp.route('/portfolio', methods=['GET'])
@login_required
def get_portfolio():
    """Get user's portfolio summary"""
    summary = PortfolioSummary.objects(user_id=str(current_user.id)).first()
    
    if not summary:
        summary = update_portfolio_summary(str(current_user.id))
    
    return jsonify({'portfolio': summary.to_dict()}), 200


@post_hackathon_bp.route('/portfolio/refresh', methods=['POST'])
@login_required
def refresh_portfolio():
    """Force refresh portfolio summary"""
    summary = update_portfolio_summary(str(current_user.id))
    return jsonify({'portfolio': summary.to_dict()}), 200


@post_hackathon_bp.route('/insights', methods=['GET'])
@login_required
def get_insights():
    """Get insights from hackathon history"""
    projects = PostHackathonProject.objects(user_id=str(current_user.id))
    
    insights = {
        'total_projects': projects.count(),
        'total_prize_money': sum(p.prize_won or 0 for p in projects),
        'win_rate': 0,
        'most_used_tech': [],
        'best_performing': None,
        'growth_trend': []
    }
    
    # Calculate win rate
    if projects.count() > 0:
        wins = sum(1 for p in projects if p.prize_won and p.prize_won > 0)
        insights['win_rate'] = wins / projects.count()
    
    # Find best performing project (by stars)
    best = projects.order_by('-github_stars').first()
    if best:
        insights['best_performing'] = {
            'name': best.project_name,
            'stars': best.github_stars,
            'hackathon': best.hackathon_id
        }
    
    return jsonify({'insights': insights}), 200


def fetch_github_stats(github_url):
    """Fetch stats from GitHub API"""
    # Extract owner/repo from URL
    match = re.search(r'github\.com/([^/]+)/([^/]+)', github_url)
    if not match:
        raise ValueError('Invalid GitHub URL')
    
    owner, repo = match.groups()
    repo = repo.replace('.git', '')
    
    api_url = f'https://api.github.com/repos/{owner}/{repo}'
    response = requests.get(api_url, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    return {
        'stars': data.get('stargazers_count', 0),
        'forks': data.get('forks_count', 0),
        'watchers': data.get('watchers_count', 0),
        'open_issues': data.get('open_issues_count', 0),
        'language': data.get('language'),
        'description': data.get('description')
    }


def update_portfolio_summary(user_id):
    """Update or create portfolio summary"""
    projects = PostHackathonProject.objects(user_id=user_id)
    
    summary = PortfolioSummary.objects(user_id=user_id).first()
    if not summary:
        summary = PortfolioSummary(user_id=user_id)
    
    # Calculate totals
    summary.total_hackathons = projects.count()
    summary.total_wins = sum(1 for p in projects if p.prize_won and p.prize_won > 0)
    summary.total_prizes_won = sum(p.prize_won or 0 for p in projects)
    summary.total_projects = projects.count()
    summary.total_github_stars = sum(p.github_stars or 0 for p in projects)
    summary.total_users_reached = sum(p.total_users or 0 for p in projects)
    summary.total_job_offers = sum(p.job_offers_received or 0 for p in projects)
    summary.total_connections = sum(p.connections_made or 0 for p in projects)
    
    # Find best achievements
    prizes = [(p.prize_won, p.final_placement) for p in projects if p.prize_won]
    if prizes:
        summary.highest_prize = max(p[0] for p in prizes)
        summary.best_placement = min((p[1] for p in prizes if p[1]), default=None)
    
    # Most starred project
    most_starred = projects.order_by('-github_stars').first()
    if most_starred and most_starred.github_stars:
        summary.most_starred_project = {
            'name': most_starred.project_name,
            'stars': most_starred.github_stars,
            'url': most_starred.github_url
        }
    
    # Date range
    dates = [p.hackathon_date for p in projects if p.hackathon_date]
    if dates:
        summary.first_hackathon_date = min(dates)
        summary.last_hackathon_date = max(dates)
    
    summary.last_updated = datetime.utcnow()
    summary.save()
    
    return summary

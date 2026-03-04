"""
Demo Script Routes - Generate pitch/demo scripts for hackathon presentations
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models.demo_script import DemoScript, Storyboard
from models.hackathon import Hackathon
from models.application import Application
from services.ai_service import AIService
import json

demo_script_bp = Blueprint('demo_script', __name__)


@demo_script_bp.route('/generate', methods=['POST'])
@login_required
def generate_demo_script():
    """Generate a demo/pitch script"""
    data = request.get_json()
    
    hackathon_id = data.get('hackathon_id')
    application_id = data.get('application_id')
    script_type = data.get('script_type', '3min')  # 1min, 3min, 5min, elevator
    project_name = data.get('project_name')
    project_description = data.get('project_description')
    
    if not hackathon_id:
        return jsonify({'error': 'hackathon_id required'}), 400
    
    hackathon = Hackathon.objects(id=hackathon_id).first()
    if not hackathon:
        return jsonify({'error': 'Hackathon not found'}), 404
    
    # Try to get project info from application if not provided
    if application_id and not project_description:
        app = Application.objects(id=application_id).first()
        if app and app.generated_project_idea:
            try:
                idea = json.loads(app.generated_project_idea)
                project_name = project_name or idea.get('project_name')
                project_description = idea.get('solution') or idea.get('problem_statement')
            except:
                pass
    
    try:
        ai = AIService()
        script = generate_script_with_ai(
            hackathon, project_name, project_description, script_type, ai
        )
        
        # Save to database
        demo = DemoScript(
            user_id=str(current_user.id),
            hackathon_id=hackathon_id,
            application_id=application_id,
            project_name=project_name,
            project_description=project_description,
            script_type=script_type,
            **script
        )
        demo.save()
        
        return jsonify({'script': demo.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate script: {str(e)}'}), 500


@demo_script_bp.route('/scripts', methods=['GET'])
@login_required
def get_my_scripts():
    """Get user's demo scripts"""
    hackathon_id = request.args.get('hackathon_id')
    
    query = {'user_id': str(current_user.id)}
    if hackathon_id:
        query['hackathon_id'] = hackathon_id
    
    scripts = DemoScript.objects(**query).order_by('-created_at')
    return jsonify({'scripts': [s.to_dict() for s in scripts]}), 200


@demo_script_bp.route('/scripts/<script_id>', methods=['GET'])
@login_required
def get_script(script_id):
    """Get a specific demo script"""
    script = DemoScript.objects(id=script_id, user_id=str(current_user.id)).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    return jsonify({'script': script.to_dict()}), 200


@demo_script_bp.route('/scripts/<script_id>', methods=['PUT'])
@login_required
def update_script(script_id):
    """Update a demo script"""
    script = DemoScript.objects(id=script_id, user_id=str(current_user.id)).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    
    data = request.get_json()
    
    for field in ['hook', 'problem', 'solution', 'demo_points', 'tech_highlight',
                  'impact', 'call_to_action', 'full_script', 'presentation_tips']:
        if field in data:
            setattr(script, field, data[field])
    
    script.updated_at = datetime.utcnow()
    script.save()
    
    return jsonify({'script': script.to_dict()}), 200


@demo_script_bp.route('/storyboard/generate', methods=['POST'])
@login_required
def generate_storyboard():
    """Generate a visual storyboard for demo video"""
    data = request.get_json()
    
    script_id = data.get('script_id')
    if not script_id:
        return jsonify({'error': 'script_id required'}), 400
    
    script = DemoScript.objects(id=script_id, user_id=str(current_user.id)).first()
    if not script:
        return jsonify({'error': 'Script not found'}), 404
    
    try:
        ai = AIService()
        storyboard = generate_storyboard_with_ai(script, ai)
        
        sb = Storyboard(
            demo_script_id=script_id,
            user_id=str(current_user.id),
            **storyboard
        )
        sb.save()
        
        return jsonify({'storyboard': sb.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate storyboard: {str(e)}'}), 500


@demo_script_bp.route('/practice-questions', methods=['GET'])
@login_required
def get_practice_questions():
    """Get common judge questions for practice"""
    hackathon_id = request.args.get('hackathon_id')
    project_type = request.args.get('project_type', 'general')
    
    try:
        ai = AIService()
        questions = generate_practice_questions(hackathon_id, project_type, ai)
        return jsonify({'questions': questions}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def generate_script_with_ai(hackathon, project_name, project_description, script_type, ai):
    """Generate demo script using AI"""
    
    duration_map = {
        'elevator': {'seconds': 30, 'description': '30-second elevator pitch'},
        '1min': {'seconds': 60, 'description': '1-minute pitch'},
        '3min': {'seconds': 180, 'description': '3-minute demo'},
        '5min': {'seconds': 300, 'description': '5-minute presentation'}
    }
    
    duration = duration_map.get(script_type, duration_map['3min'])
    
    prompt = f"""Create a {duration['description']} script for a hackathon presentation.

Hackathon: {hackathon.name}
Theme: {hackathon.themes or hackathon.tags}

Project: {project_name or 'Hackathon Project'}
Description: {project_description or 'An innovative solution for the hackathon challenge'}

Generate a compelling presentation script with:
1. hook: A powerful opening line (5-10 seconds)
2. problem: Clear problem statement (15-20 seconds)
3. solution: Your solution explanation (20-30 seconds)
4. demo_points: Array of demo moments with timing, action, and talking points
5. tech_highlight: One impressive technical achievement
6. impact: Real-world impact/results
7. call_to_action: Strong closing
8. presentation_tips: Array of delivery tips
9. common_questions: Array of likely judge questions with suggested answers
10. full_script: The complete word-for-word script

Return as JSON with these exact keys."""

    messages = [
        {"role": "system", "content": "You are an expert pitch coach who has helped teams win major hackathons. Create engaging, memorable presentations. Respond with valid JSON only."},
        {"role": "user", "content": prompt}
    ]
    
    response = ai._call_groq(messages, temperature=0.7, max_tokens=3000)
    
    try:
        script = json.loads(response)
    except:
        script = {
            'hook': '',
            'problem': '',
            'solution': response,
            'demo_points': [],
            'tech_highlight': '',
            'impact': '',
            'call_to_action': '',
            'full_script': response,
            'presentation_tips': [],
            'common_questions': []
        }
    
    script['total_duration_seconds'] = duration['seconds']
    
    return script


def generate_storyboard_with_ai(script, ai):
    """Generate visual storyboard using AI"""
    
    prompt = f"""Create a visual storyboard for this demo presentation:

Project: {script.project_name}
Duration: {script.total_duration_seconds} seconds

Script hook: {script.hook}
Problem: {script.problem}
Solution: {script.solution}

Generate a storyboard with:
1. scenes: Array of scene objects, each with:
   - scene_number
   - duration (e.g., "15s")
   - visual: What should be on screen
   - audio: What is being said
   - notes: Production notes
2. color_scheme: Array of 3-5 hex colors that match the project vibe
3. font_suggestions: 2-3 font recommendations
4. transition_style: Recommended transition style
5. recommended_tools: Array of tools with name and purpose

Return as JSON."""

    messages = [
        {"role": "system", "content": "You are a video production expert creating storyboards for demo videos. Respond with valid JSON only."},
        {"role": "user", "content": prompt}
    ]
    
    response = ai._call_groq(messages, temperature=0.6, max_tokens=2000)
    
    try:
        return json.loads(response)
    except:
        return {
            'scenes': [],
            'color_scheme': ['#6366f1', '#8b5cf6', '#ec4899'],
            'font_suggestions': ['Inter', 'Poppins'],
            'transition_style': 'smooth fade',
            'recommended_tools': [
                {'tool': 'Canva', 'purpose': 'Slides and graphics'},
                {'tool': 'Loom', 'purpose': 'Screen recording'}
            ]
        }


def generate_practice_questions(hackathon_id, project_type, ai):
    """Generate practice questions for Q&A"""
    
    prompt = f"""Generate 10 common questions that hackathon judges ask about {project_type} projects.
Include:
- Technical depth questions
- Business viability questions
- Future plans questions
- Team questions

For each question, provide:
- question: The judge's question
- category: (technical/business/future/team)
- difficulty: (easy/medium/hard)
- suggested_answer_tips: Tips for answering well

Return as JSON array."""

    messages = [
        {"role": "system", "content": "You are a hackathon judge with 10+ years experience. Respond with valid JSON only."},
        {"role": "user", "content": prompt}
    ]
    
    response = ai._call_groq(messages, temperature=0.6)
    
    try:
        return json.loads(response)
    except:
        return [{'question': 'Tell us about your technical implementation', 'category': 'technical', 'difficulty': 'medium', 'suggested_answer_tips': 'Be specific about technologies used'}]

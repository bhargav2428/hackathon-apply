"""
Sponsors Routes - Connect with hackathon sponsors
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models.sponsors import Sponsor, SponsorConnection, SponsorSuggestion
from models.hackathon import Hackathon
from services.ai_service import AIService
import json

sponsors_bp = Blueprint('sponsors', __name__)


@sponsors_bp.route('/', methods=['GET'])
@login_required
def get_sponsors():
    """Get all sponsors with optional filters"""
    industry = request.args.get('industry')
    hackathon_id = request.args.get('hackathon_id')
    
    query = {}
    if industry:
        query['industry'] = industry
    if hackathon_id:
        query['hackathons_sponsored__contains'] = hackathon_id
    
    sponsors = Sponsor.objects(**query).order_by('name')
    return jsonify({'sponsors': [s.to_dict() for s in sponsors]}), 200


@sponsors_bp.route('/<sponsor_id>', methods=['GET'])
@login_required
def get_sponsor(sponsor_id):
    """Get sponsor details"""
    sponsor = Sponsor.objects(id=sponsor_id).first()
    if not sponsor:
        return jsonify({'error': 'Sponsor not found'}), 404
    return jsonify({'sponsor': sponsor.to_dict()}), 200


@sponsors_bp.route('/', methods=['POST'])
@login_required
def create_sponsor():
    """Add a new sponsor (admin feature)"""
    data = request.get_json()
    
    sponsor = Sponsor(
        name=data.get('name'),
        logo_url=data.get('logo_url'),
        website=data.get('website'),
        industry=data.get('industry'),
        company_size=data.get('company_size'),
        description=data.get('description'),
        apis=data.get('apis', []),
        sdks=data.get('sdks', []),
        free_credits=data.get('free_credits', {}),
        prize_categories=data.get('prize_categories', []),
        typical_prize_amount=data.get('typical_prize_amount'),
        developer_relations_contact=data.get('developer_relations_contact', {}),
        discord_server=data.get('discord_server'),
        slack_channel=data.get('slack_channel'),
        twitter=data.get('twitter'),
        linkedin=data.get('linkedin'),
        github=data.get('github'),
        winning_tips=data.get('winning_tips', []),
        what_they_look_for=data.get('what_they_look_for', [])
    )
    sponsor.save()
    
    return jsonify({'sponsor': sponsor.to_dict()}), 201


@sponsors_bp.route('/for-hackathon/<hackathon_id>', methods=['GET'])
@login_required
def get_hackathon_sponsors(hackathon_id):
    """Get sponsors for a specific hackathon"""
    hackathon = Hackathon.objects(id=hackathon_id).first()
    if not hackathon:
        return jsonify({'error': 'Hackathon not found'}), 404
    
    # Get sponsors that sponsor this hackathon
    sponsors = Sponsor.objects(hackathons_sponsored__contains=hackathon_id)
    
    return jsonify({
        'hackathon': hackathon.name,
        'sponsors': [s.to_dict() for s in sponsors]
    }), 200


@sponsors_bp.route('/connections', methods=['GET'])
@login_required
def get_my_connections():
    """Get user's sponsor connections"""
    connections = SponsorConnection.objects(user_id=str(current_user.id)).order_by('-created_at')
    
    # Enrich with sponsor info
    enriched = []
    for conn in connections:
        conn_dict = conn.to_dict()
        sponsor = Sponsor.objects(id=conn.sponsor_id).first()
        if sponsor:
            conn_dict['sponsor'] = sponsor.to_dict()
        enriched.append(conn_dict)
    
    return jsonify({'connections': enriched}), 200


@sponsors_bp.route('/connections', methods=['POST'])
@login_required
def create_connection():
    """Track a sponsor connection"""
    data = request.get_json()
    
    sponsor_id = data.get('sponsor_id')
    if not sponsor_id:
        return jsonify({'error': 'sponsor_id required'}), 400
    
    connection = SponsorConnection(
        user_id=str(current_user.id),
        sponsor_id=sponsor_id,
        hackathon_id=data.get('hackathon_id'),
        connection_type=data.get('connection_type', 'interested'),
        used_api=data.get('used_api', False),
        applied_for_prize=data.get('applied_for_prize', False),
        notes=data.get('notes')
    )
    connection.save()
    
    return jsonify({'connection': connection.to_dict()}), 201


@sponsors_bp.route('/connections/<connection_id>', methods=['PUT'])
@login_required
def update_connection(connection_id):
    """Update a sponsor connection"""
    connection = SponsorConnection.objects(id=connection_id, user_id=str(current_user.id)).first()
    if not connection:
        return jsonify({'error': 'Connection not found'}), 404
    
    data = request.get_json()
    
    for field in ['connection_type', 'used_api', 'applied_for_prize', 'won_prize',
                  'prize_won', 'had_mentorship', 'mentorship_notes', 'follow_up_sent',
                  'response_received', 'notes']:
        if field in data:
            setattr(connection, field, data[field])
    
    connection.save()
    
    return jsonify({'connection': connection.to_dict()}), 200


@sponsors_bp.route('/suggest-integration', methods=['POST'])
@login_required
def suggest_sponsor_integration():
    """AI-powered suggestion for using sponsor tech"""
    data = request.get_json()
    
    hackathon_id = data.get('hackathon_id')
    sponsor_id = data.get('sponsor_id')
    project_idea = data.get('project_idea')
    
    if not all([hackathon_id, sponsor_id]):
        return jsonify({'error': 'hackathon_id and sponsor_id required'}), 400
    
    hackathon = Hackathon.objects(id=hackathon_id).first()
    sponsor = Sponsor.objects(id=sponsor_id).first()
    
    if not hackathon or not sponsor:
        return jsonify({'error': 'Hackathon or Sponsor not found'}), 404
    
    try:
        ai = AIService()
        suggestion = generate_integration_suggestion(hackathon, sponsor, project_idea, ai)
        
        # Save suggestion
        sugg = SponsorSuggestion(
            user_id=str(current_user.id),
            hackathon_id=hackathon_id,
            sponsor_id=sponsor_id,
            **suggestion
        )
        sugg.save()
        
        return jsonify({'suggestion': sugg.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate suggestion: {str(e)}'}), 500


@sponsors_bp.route('/seed', methods=['POST'])
@login_required
def seed_sponsors():
    """Seed database with common hackathon sponsors"""
    sponsors_data = [
        {
            'name': 'Google Cloud',
            'website': 'https://cloud.google.com',
            'industry': 'Cloud Computing',
            'apis': [
                {'name': 'Cloud Vision API', 'description': 'Image analysis', 'docs_url': 'https://cloud.google.com/vision'},
                {'name': 'Cloud Natural Language', 'description': 'NLP', 'docs_url': 'https://cloud.google.com/natural-language'},
                {'name': 'Firebase', 'description': 'Backend as a Service', 'docs_url': 'https://firebase.google.com'}
            ],
            'free_credits': {'service': 'Google Cloud', 'amount': '$300', 'validity': '90 days'},
            'prize_categories': ['Best Use of Google Cloud', 'Best AI/ML Project'],
            'winning_tips': ['Use multiple GCP services', 'Show scalability', 'Integrate Gemini AI'],
            'what_they_look_for': ['Innovation', 'Technical complexity', 'Real-world applicability']
        },
        {
            'name': 'AWS',
            'website': 'https://aws.amazon.com',
            'industry': 'Cloud Computing',
            'apis': [
                {'name': 'Amazon Bedrock', 'description': 'Generative AI', 'docs_url': 'https://aws.amazon.com/bedrock'},
                {'name': 'Lambda', 'description': 'Serverless compute', 'docs_url': 'https://aws.amazon.com/lambda'},
                {'name': 'S3', 'description': 'Object storage', 'docs_url': 'https://aws.amazon.com/s3'}
            ],
            'free_credits': {'service': 'AWS', 'amount': '$100', 'validity': '12 months'},
            'prize_categories': ['Best Use of AWS'],
            'winning_tips': ['Use serverless architecture', 'Show cost optimization', 'Leverage AI services'],
            'what_they_look_for': ['Scalability', 'Security best practices', 'Creative use of services']
        },
        {
            'name': 'Twilio',
            'website': 'https://www.twilio.com',
            'industry': 'Communications',
            'apis': [
                {'name': 'SMS API', 'description': 'Send text messages', 'docs_url': 'https://www.twilio.com/docs/sms'},
                {'name': 'Voice API', 'description': 'Make calls', 'docs_url': 'https://www.twilio.com/docs/voice'},
                {'name': 'WhatsApp API', 'description': 'WhatsApp messaging', 'docs_url': 'https://www.twilio.com/whatsapp'}
            ],
            'free_credits': {'service': 'Twilio', 'amount': '$50', 'code': 'HACKATHON'},
            'prize_categories': ['Best Use of Twilio'],
            'winning_tips': ['Combine multiple Twilio products', 'Show real-time communication', 'Consider accessibility'],
            'what_they_look_for': ['User experience', 'Practical application', 'Communication innovation']
        },
        {
            'name': 'MongoDB',
            'website': 'https://www.mongodb.com',
            'industry': 'Database',
            'apis': [
                {'name': 'MongoDB Atlas', 'description': 'Cloud database', 'docs_url': 'https://www.mongodb.com/atlas'},
                {'name': 'Atlas Search', 'description': 'Full-text search', 'docs_url': 'https://www.mongodb.com/atlas/search'},
                {'name': 'Atlas Vector Search', 'description': 'Vector search for AI', 'docs_url': 'https://www.mongodb.com/products/platform/atlas-vector-search'}
            ],
            'free_credits': {'service': 'MongoDB Atlas', 'amount': 'Free tier + $200', 'code': 'HACK2024'},
            'prize_categories': ['Best Use of MongoDB'],
            'winning_tips': ['Use Atlas features', 'Show data modeling skills', 'Leverage aggregation pipeline'],
            'what_they_look_for': ['Data architecture', 'Query optimization', 'Scalable design']
        },
        {
            'name': 'OpenAI',
            'website': 'https://openai.com',
            'industry': 'AI',
            'apis': [
                {'name': 'GPT-4 API', 'description': 'Large language model', 'docs_url': 'https://platform.openai.com/docs'},
                {'name': 'DALL-E API', 'description': 'Image generation', 'docs_url': 'https://platform.openai.com/docs/guides/images'},
                {'name': 'Whisper API', 'description': 'Speech to text', 'docs_url': 'https://platform.openai.com/docs/guides/speech-to-text'}
            ],
            'free_credits': {'service': 'OpenAI', 'amount': '$100', 'code': 'Various'},
            'prize_categories': ['Best AI Application', 'Most Innovative Use of LLMs'],
            'winning_tips': ['Show novel prompting techniques', 'Fine-tune for specific use case', 'Combine multiple models'],
            'what_they_look_for': ['Creativity', 'Responsible AI use', 'User value']
        }
    ]
    
    created = 0
    for data in sponsors_data:
        existing = Sponsor.objects(name=data['name']).first()
        if not existing:
            sponsor = Sponsor(**data)
            sponsor.save()
            created += 1
    
    return jsonify({'message': f'Created {created} sponsors'}), 200


def generate_integration_suggestion(hackathon, sponsor, project_idea, ai):
    """Generate AI suggestion for sponsor integration"""
    prompt = f"""For hackathon "{hackathon.name}" with theme {hackathon.themes or hackathon.tags},
suggest how to integrate {sponsor.name}'s technology to win their prize.

Sponsor APIs available: {[api.get('name') for api in sponsor.apis]}
Their prize categories: {sponsor.prize_categories}
What they look for: {sponsor.what_they_look_for}

{f'Project idea: {project_idea}' if project_idea else ''}

Generate:
1. integration_idea: A specific integration concept
2. how_to_use: Step-by-step implementation guide
3. code_example: A brief code snippet showing the integration
4. relevant_docs: List of documentation URLs
5. prize_category: Which prize to target
6. alignment_score: 1-100 how well this aligns with their criteria

Return as JSON."""

    messages = [
        {"role": "system", "content": "You are a hackathon strategy expert who helps teams win sponsor prizes. Respond with valid JSON only."},
        {"role": "user", "content": prompt}
    ]
    
    response = ai._call_groq(messages, temperature=0.7, max_tokens=2000)
    
    try:
        return json.loads(response)
    except:
        return {
            'integration_idea': response,
            'how_to_use': '',
            'code_example': '',
            'relevant_docs': [],
            'prize_category': sponsor.prize_categories[0] if sponsor.prize_categories else '',
            'alignment_score': 70
        }

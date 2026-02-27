"""
AI Service - Handles all AI-related operations using Groq Cloud API
"""
import os
import json
from typing import Dict, List, Optional, Any
from groq import Groq


class AIService:
    """Service for AI-powered features using Groq Cloud API"""
    
    def __init__(self):
        self._client = None
        self._model = None
    
    @property
    def client(self):
        """Lazy initialization of Groq client"""
        if self._client is None:
            api_key = os.environ.get('GROQ_API_KEY')
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable is not set")
            self._client = Groq(api_key=api_key)
        return self._client
    
    @property
    def model(self):
        """Get the model name"""
        if self._model is None:
            self._model = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')
        return self._model
    
    def _call_groq(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Make a call to Groq API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_completion_tokens=max_tokens,
            top_p=1,
            stream=False
        )
        return response.choices[0].message.content
    
    def generate_project_idea(self, hackathon, profile, additional_context: str = '') -> Dict[str, Any]:
        """Generate a project idea based on hackathon theme and user profile"""
        
        # Build context from hackathon
        hackathon_context = f"""
Hackathon: {hackathon.name}
Description: {hackathon.description or 'Not specified'}
Themes: {', '.join(hackathon.themes) if hackathon.themes else 'Not specified'}
Tags: {', '.join(hackathon.tags) if hackathon.tags else 'Not specified'}
Required Skills: {', '.join(hackathon.required_skills) if hackathon.required_skills else 'Open'}
"""
        
        # Build context from profile
        profile_context = ""
        if profile:
            profile_context = f"""
Developer Skills: {', '.join(profile.skills) if profile.skills else 'Not specified'}
Programming Languages: {', '.join(profile.programming_languages) if profile.programming_languages else 'Not specified'}
Frameworks: {', '.join(profile.frameworks) if profile.frameworks else 'Not specified'}
Experience: {profile.years_of_experience or 0} years
Previous Hackathons: {profile.previous_hackathons or 0}
"""
        
        prompt = f"""You are an expert hackathon mentor helping developers create winning project ideas.

Based on the following hackathon and developer profile, generate a creative and feasible project idea.

{hackathon_context}

{profile_context}

{f'Additional Context: {additional_context}' if additional_context else ''}

Generate a comprehensive project idea with the following structure:
1. Project Name: A catchy, memorable name
2. Problem Statement: What problem does this solve?
3. Solution: How does your project solve this problem?
4. Key Features: List 3-5 main features
5. Tech Stack: Recommended technologies
6. Architecture: High-level architecture description
7. MVP Plan: What can be built in the hackathon timeframe
8. Unique Value Proposition: What makes this project stand out

Format your response as JSON with the following keys:
- project_name
- problem_statement
- solution
- key_features (array)
- tech_stack (array)
- architecture
- mvp_features
- unique_value_proposition
"""
        
        messages = [
            {"role": "system", "content": "You are a creative hackathon project ideation assistant. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_groq(messages, temperature=0.8)
        
        try:
            # Try to parse as JSON
            idea = json.loads(response)
        except json.JSONDecodeError:
            # If not valid JSON, create structured response
            idea = {
                'project_name': 'Generated Project',
                'problem_statement': response,
                'solution': '',
                'key_features': [],
                'tech_stack': [],
                'architecture': '',
                'mvp_features': '',
                'unique_value_proposition': ''
            }
        
        idea['full_content'] = response
        return idea
    
    def generate_motivation(self, hackathon, profile, project_idea: Optional[str] = None) -> str:
        """Generate motivation statement for hackathon application"""
        
        context = f"""
Hackathon: {hackathon.name}
Description: {hackathon.description or 'Not specified'}
Themes: {', '.join(hackathon.themes) if hackathon.themes else 'General'}
"""
        
        profile_info = ""
        if profile:
            profile_info = f"""
About the applicant:
- Name: {profile.full_name}
- Skills: {', '.join(profile.skills[:5]) if profile.skills else 'Various technical skills'}
- Experience: {profile.years_of_experience or 0} years in tech
- Previous Hackathons: {profile.previous_hackathons or 0}
- Education: {profile.college or 'Not specified'}, {profile.degree or 'Not specified'}
- Bio: {profile.bio or 'Passionate developer'}
"""
        
        prompt = f"""Write a compelling motivation statement for a hackathon application.

{context}

{profile_info}

{f'Project Idea: {project_idea}' if project_idea else ''}

Write a 150-200 word motivation statement that:
1. Shows genuine enthusiasm for the hackathon theme
2. Highlights relevant skills and experience
3. Explains what you hope to learn/achieve
4. Demonstrates understanding of the hackathon's goals
5. Is professional yet personable

Write in first person from the applicant's perspective.
"""
        
        messages = [
            {"role": "system", "content": "You are an expert at writing compelling hackathon applications. Write naturally and authentically."},
            {"role": "user", "content": prompt}
        ]
        
        return self._call_groq(messages, temperature=0.7)
    
    def generate_team_description(self, profile) -> str:
        """Generate team description based on profile"""
        
        prompt = f"""Write a brief team/individual introduction for a hackathon application.

Profile:
- Name: {profile.full_name if profile else 'Developer'}
- Skills: {', '.join(profile.skills[:5]) if profile and profile.skills else 'Full-stack development'}
- Languages: {', '.join(profile.programming_languages[:5]) if profile and profile.programming_languages else 'Python, JavaScript'}
- Experience: {profile.years_of_experience if profile else 0} years
- Previous Hackathons: {profile.previous_hackathons if profile else 0}

Write a 50-100 word team description that:
1. Introduces the developer(s)
2. Highlights key strengths
3. Shows hackathon readiness
4. Is professional and confident

Write in third person.
"""
        
        messages = [
            {"role": "system", "content": "You are writing a professional team introduction for a hackathon."},
            {"role": "user", "content": prompt}
        ]
        
        return self._call_groq(messages, temperature=0.6)
    
    def suggest_tech_stack(self, hackathon, profile) -> Dict[str, List[str]]:
        """Suggest optimal tech stack based on hackathon requirements and user skills"""
        
        prompt = f"""Suggest an optimal tech stack for a hackathon project.

Hackathon: {hackathon.name}
Themes: {', '.join(hackathon.themes) if hackathon.themes else 'General'}
Tags: {', '.join(hackathon.tags) if hackathon.tags else 'Not specified'}
Required Skills: {', '.join(hackathon.required_skills) if hackathon.required_skills else 'Open'}

Developer Skills:
- Known Languages: {', '.join(profile.programming_languages) if profile and profile.programming_languages else 'Various'}
- Known Frameworks: {', '.join(profile.frameworks) if profile and profile.frameworks else 'Various'}
- Skills: {', '.join(profile.skills[:10]) if profile and profile.skills else 'Full-stack development'}

Suggest a tech stack that:
1. Matches the hackathon theme
2. Leverages the developer's existing skills
3. Can be built quickly (hackathon timeframe)
4. Is modern and impressive

Format as JSON with categories: frontend, backend, database, deployment, ai_ml (if applicable), other
"""
        
        messages = [
            {"role": "system", "content": "You are a technical architect. Respond with valid JSON only."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_groq(messages, temperature=0.5)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                'frontend': ['React', 'TailwindCSS'],
                'backend': ['Python', 'Flask'],
                'database': ['PostgreSQL'],
                'deployment': ['Docker', 'Vercel'],
                'suggestion': response
            }
    
    def analyze_resume(self, resume_text: str) -> Dict[str, Any]:
        """Analyze resume and extract insights"""
        
        prompt = f"""Analyze this resume for hackathon optimization:

{resume_text[:5000]}

Provide analysis including:
1. Key strengths for hackathons
2. Technical skills identified
3. Notable projects/achievements
4. Suggested improvements
5. Hackathon-ready score (1-10)
6. Recommended hackathon types

Format as JSON.
"""
        
        messages = [
            {"role": "system", "content": "You are a career advisor specializing in hackathons. Respond with valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_groq(messages, temperature=0.5)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {'analysis': response}
    
    def skill_gap_analysis(self, hackathon, profile) -> Dict[str, Any]:
        """Analyze skill gaps for a specific hackathon"""
        
        required = hackathon.required_skills or []
        user_skills = (profile.skills or []) + (profile.programming_languages or []) + (profile.frameworks or [])
        
        prompt = f"""Perform a skill gap analysis for a hackathon.

Hackathon: {hackathon.name}
Required/Preferred Skills: {', '.join(required) if required else 'Not specified'}
Tags/Themes: {', '.join(hackathon.tags + hackathon.themes)}

User Skills: {', '.join(user_skills) if user_skills else 'Not specified'}

Analyze:
1. Matching skills
2. Missing skills
3. Skills to improve
4. Learning recommendations
5. Overall readiness score (1-10)

Format as JSON.
"""
        
        messages = [
            {"role": "system", "content": "You are a skill assessment expert. Respond with valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_groq(messages, temperature=0.5)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {'analysis': response}
    
    def predict_hackathon_success(self, hackathon, profile) -> Dict[str, Any]:
        """Predict success probability for a hackathon"""
        
        prompt = f"""Predict hackathon success probability.

Hackathon: {hackathon.name}
Themes: {', '.join(hackathon.themes) if hackathon.themes else 'General'}
Prize Pool: {hackathon.prize_pool or 'Not specified'}
Participant Count: {hackathon.participants_count or 'Unknown'}

Applicant Profile:
- Experience: {profile.years_of_experience if profile else 0} years
- Previous Hackathons: {profile.previous_hackathons if profile else 0}
- Wins: {profile.hackathon_wins if profile else 0}
- Skills: {', '.join(profile.skills[:10]) if profile and profile.skills else 'Various'}

Provide:
1. Success probability (0-100%)
2. Key factors in favor
3. Key challenges
4. Recommendations to improve chances
5. Similar hackathons won by similar profiles

Format as JSON.
"""
        
        messages = [
            {"role": "system", "content": "You are a hackathon success predictor. Be realistic but encouraging. Respond with valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_groq(messages, temperature=0.6)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {'prediction': response}
    
    def get_recommendations(self, hackathons: List, profile, limit: int = 10) -> List[Dict]:
        """Get personalized hackathon recommendations"""
        
        hackathon_list = "\n".join([
            f"- {h.name}: {', '.join(h.tags[:3]) if h.tags else 'General'} | {'Online' if h.is_online else h.location}"
            for h in hackathons[:30]  # Limit to 30 for context
        ])
        
        prompt = f"""Recommend the best hackathons for this developer.

Available Hackathons:
{hackathon_list}

Developer Profile:
- Skills: {', '.join(profile.skills[:10]) if profile and profile.skills else 'Various'}
- Preferred Types: {', '.join(profile.preferred_hackathon_types[:5]) if profile and profile.preferred_hackathon_types else 'Any'}
- Experience: {profile.years_of_experience if profile else 0} years
- Previous Hackathons: {profile.previous_hackathons if profile else 0}

Recommend {limit} hackathons with:
1. Hackathon name
2. Match score (1-100)
3. Why it's recommended
4. Potential project idea

Format as JSON array.
"""
        
        messages = [
            {"role": "system", "content": "You are a hackathon matchmaker. Respond with valid JSON array."},
            {"role": "user", "content": prompt}
        ]
        
        response = self._call_groq(messages, temperature=0.6)
        
        try:
            recommendations = json.loads(response)
            if isinstance(recommendations, list):
                return recommendations[:limit]
            return [recommendations]
        except json.JSONDecodeError:
            return [{'recommendation': response}]

    def enhance_resume_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to enhance and clean up parsed resume data with better accuracy"""
        
        text = parsed_data.get('text', '')[:6000]  # Increase context
        
        # Build context from already extracted data
        extracted_info = []
        if parsed_data.get('name'):
            extracted_info.append(f"Name: {parsed_data['name']}")
        if parsed_data.get('email'):
            extracted_info.append(f"Email: {parsed_data['email']}")
        if parsed_data.get('programming_languages'):
            extracted_info.append(f"Programming Languages: {', '.join(parsed_data['programming_languages'])}")
        if parsed_data.get('frameworks'):
            extracted_info.append(f"Frameworks: {', '.join(parsed_data['frameworks'])}")
        if parsed_data.get('databases'):
            extracted_info.append(f"Databases: {', '.join(parsed_data['databases'])}")
        if parsed_data.get('tools'):
            extracted_info.append(f"Tools: {', '.join(parsed_data['tools'])}")
        if parsed_data.get('skills'):
            extracted_info.append(f"Skills: {', '.join(parsed_data['skills'])}")
        
        extracted_context = '\n'.join(extracted_info) if extracted_info else 'No data extracted yet'

        prompt = f"""You are an expert resume analyzer. Analyze this resume text and extract/enhance the profile information.

RESUME TEXT:
{text}

ALREADY EXTRACTED DATA:
{extracted_context}

Return a valid JSON object with these exact fields:
{{
    "bio": "A professional 2-3 sentence summary highlighting key strengths and experience",
    "skills": ["array", "of", "top", "15", "technical", "skills"],
    "frameworks": ["array", "of", "frameworks", "and", "libraries"],
    "programming_languages": ["array", "of", "programming", "languages"],
    "experience_level": "one of: beginner, intermediate, advanced, expert",
    "interests": ["array", "of", "professional", "interests", "and", "domains"],
    "years_of_experience": "estimated years (number or null)",
    "specializations": ["main", "areas", "of", "expertise"]
}}

Instructions:
1. The bio should be engaging and highlight unique qualities
2. Include ALL skills found in the resume, not just the obvious ones
3. Experience level should be based on years and complexity of projects
4. Look for certifications, courses, and achievements
5. Return ONLY valid JSON, no markdown, no explanations"""

        try:
            response = self._call_groq([
                {"role": "system", "content": "You are a precise resume data extractor. You only output valid JSON objects. Never include markdown formatting or code blocks."},
                {"role": "user", "content": prompt}
            ], temperature=0.2)  # Lower temperature for more consistent output
            
            # Clean up response - remove any markdown code blocks
            response = response.strip()
            if response.startswith('```'):
                response = response.split('\n', 1)[1] if '\n' in response else response[3:]
            if response.endswith('```'):
                response = response.rsplit('```', 1)[0]
            response = response.strip()
            
            enhanced = json.loads(response)
            
            # Merge with existing data, preferring non-empty values
            merged = {}
            for key in ['bio', 'skills', 'frameworks', 'programming_languages', 'experience_level', 'interests', 'years_of_experience', 'specializations']:
                ai_value = enhanced.get(key)
                parsed_value = parsed_data.get(key)
                
                if isinstance(ai_value, list) and isinstance(parsed_value, list):
                    # Merge lists and deduplicate
                    merged[key] = list(set(ai_value + parsed_value))
                elif ai_value:
                    merged[key] = ai_value
                elif parsed_value:
                    merged[key] = parsed_value
            
            return merged
        except json.JSONDecodeError as e:
            print(f"JSON decode error in enhance_resume_data: {e}")
            print(f"Response was: {response[:500]}")
            return {}
        except Exception as e:
            print(f"Error in enhance_resume_data: {e}")
            return {}


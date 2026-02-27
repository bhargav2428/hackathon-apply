"""Script to add sample hackathons to MongoDB"""
import mongoengine
from datetime import datetime, timedelta

# Connect to MongoDB
mongoengine.connect(
    db='hackathon_agent',
    host='mongodb+srv://bhargavyaswanth_db_user:9KeEgedtlsrFsZBg@cluster0.bounkpp.mongodb.net/hackathon_agent?retryWrites=true&w=majority'
)

from models.hackathon import Hackathon

# Sample hackathons from various sources
hackathons_data = [
    {
        'name': 'AI Innovation Challenge 2026',
        'description': 'Build innovative AI solutions that solve real-world problems. Open to all skill levels. Cash prizes and mentorship opportunities.',
        'url': 'https://devpost.com/hackathons/ai-innovation-2026',
        'deadline': datetime.now() + timedelta(days=30),
        'prize': '$50,000',
        'tags': ['AI', 'Machine Learning', 'Deep Learning'],
        'themes': ['Healthcare', 'Education', 'Environment'],
        'required_skills': ['Python', 'TensorFlow', 'PyTorch'],
        'is_active': True,
        'source': 'devpost'
    },
    {
        'name': 'Web3 Builder Hackathon',
        'description': 'Create decentralized applications on blockchain. Build the future of internet with Web3 technologies.',
        'url': 'https://devpost.com/hackathons/web3-builder',
        'deadline': datetime.now() + timedelta(days=45),
        'prize': '$100,000',
        'tags': ['Blockchain', 'Web3', 'DeFi', 'NFT'],
        'themes': ['Finance', 'Gaming', 'Social'],
        'required_skills': ['Solidity', 'JavaScript', 'React'],
        'is_active': True,
        'source': 'devpost'
    },
    {
        'name': 'MLH Spring Hack 2026',
        'description': 'Major League Hacking presents the biggest student hackathon of the spring. 48 hours of building, learning, and fun!',
        'url': 'https://mlh.io/seasons/2026/events',
        'deadline': datetime.now() + timedelta(days=20),
        'prize': '$25,000',
        'tags': ['Student', 'Beginner Friendly', 'All Tracks'],
        'themes': ['Open Innovation', 'Social Good', 'Best Use of API'],
        'required_skills': ['Any Language', 'Creativity'],
        'is_active': True,
        'source': 'mlh'
    },
    {
        'name': 'Healthcare AI Summit Hack',
        'description': 'Use AI to transform healthcare. Build solutions for diagnosis, treatment, patient care, and medical research.',
        'url': 'https://devpost.com/hackathons/healthcare-ai',
        'deadline': datetime.now() + timedelta(days=60),
        'prize': '$75,000',
        'tags': ['AI', 'Healthcare', 'Medical', 'ML'],
        'themes': ['Diagnosis', 'Drug Discovery', 'Patient Care'],
        'required_skills': ['Python', 'Data Science', 'NLP'],
        'is_active': True,
        'source': 'devpost'
    },
    {
        'name': 'Climate Tech Challenge',
        'description': 'Build technology solutions to fight climate change. Help create a sustainable future for our planet.',
        'url': 'https://unstop.com/hackathons/climate-tech',
        'deadline': datetime.now() + timedelta(days=35),
        'prize': '$40,000',
        'tags': ['Climate', 'Sustainability', 'GreenTech'],
        'themes': ['Renewable Energy', 'Carbon Tracking', 'Conservation'],
        'required_skills': ['IoT', 'Data Analysis', 'Web Dev'],
        'is_active': True,
        'source': 'unstop'
    },
    {
        'name': 'FinTech Innovation Jam',
        'description': 'Revolutionize financial services with cutting-edge technology. Build the next generation of banking and payments.',
        'url': 'https://devpost.com/hackathons/fintech-jam',
        'deadline': datetime.now() + timedelta(days=25),
        'prize': '$60,000',
        'tags': ['FinTech', 'Banking', 'Payments', 'API'],
        'themes': ['Digital Banking', 'Crypto', 'InsurTech'],
        'required_skills': ['API Integration', 'Security', 'Mobile Dev'],
        'is_active': True,
        'source': 'devpost'
    },
    {
        'name': 'Google Cloud Hackathon',
        'description': 'Build scalable applications on Google Cloud Platform. Win prizes and get recognition from Google engineers.',
        'url': 'https://cloud.google.com/hackathons',
        'deadline': datetime.now() + timedelta(days=40),
        'prize': '$30,000',
        'tags': ['Cloud', 'GCP', 'Serverless', 'Big Data'],
        'themes': ['Machine Learning', 'Data Analytics', 'DevOps'],
        'required_skills': ['GCP', 'Python', 'SQL'],
        'is_active': True,
        'source': 'google'
    },
    {
        'name': 'Mobile App Challenge 2026',
        'description': 'Create innovative mobile applications for iOS and Android. Focus on user experience and innovative features.',
        'url': 'https://devpost.com/hackathons/mobile-challenge',
        'deadline': datetime.now() + timedelta(days=50),
        'prize': '$35,000',
        'tags': ['Mobile', 'iOS', 'Android', 'Flutter'],
        'themes': ['Productivity', 'Entertainment', 'Utility'],
        'required_skills': ['Swift', 'Kotlin', 'React Native'],
        'is_active': True,
        'source': 'devpost'
    },
    {
        'name': 'Hack2Skill AI Agents Challenge',
        'description': 'Build autonomous AI agents that can perform complex tasks. Push the boundaries of what AI can accomplish.',
        'url': 'https://hack2skill.com/hackathons/ai-agents',
        'deadline': datetime.now() + timedelta(days=28),
        'prize': '$80,000',
        'tags': ['AI Agents', 'LLM', 'Automation', 'GPT'],
        'themes': ['Productivity', 'Customer Service', 'Research'],
        'required_skills': ['Python', 'LangChain', 'OpenAI API'],
        'is_active': True,
        'source': 'hack2skill'
    },
    {
        'name': 'Open Source India Hackathon',
        'description': 'Contribute to open source projects and win exciting prizes. Collaborate with developers worldwide.',
        'url': 'https://unstop.com/hackathons/opensource-india',
        'deadline': datetime.now() + timedelta(days=15),
        'prize': '$20,000',
        'tags': ['Open Source', 'Community', 'Collaboration'],
        'themes': ['Developer Tools', 'Infrastructure', 'Libraries'],
        'required_skills': ['Git', 'GitHub', 'Any Programming Language'],
        'is_active': True,
        'source': 'unstop'
    },
    {
        'name': 'EdTech Revolution Hack',
        'description': 'Transform education with technology. Build tools that make learning accessible, engaging, and effective.',
        'url': 'https://devpost.com/hackathons/edtech-revolution',
        'deadline': datetime.now() + timedelta(days=42),
        'prize': '$45,000',
        'tags': ['EdTech', 'Education', 'Learning', 'AI Tutoring'],
        'themes': ['K-12', 'Higher Education', 'Professional Training'],
        'required_skills': ['Full Stack', 'AI/ML', 'UX Design'],
        'is_active': True,
        'source': 'devpost'
    },
    {
        'name': 'Cybersecurity CTF Hackathon',
        'description': 'Test your security skills in this capture-the-flag style hackathon. Find vulnerabilities and secure systems.',
        'url': 'https://mlh.io/seasons/2026/security-ctf',
        'deadline': datetime.now() + timedelta(days=18),
        'prize': '$30,000',
        'tags': ['Security', 'CTF', 'Ethical Hacking', 'Pentesting'],
        'themes': ['Network Security', 'Web Security', 'Cryptography'],
        'required_skills': ['Python', 'Linux', 'Network Protocols'],
        'is_active': True,
        'source': 'mlh'
    }
]

if __name__ == '__main__':
    print("Adding hackathons to MongoDB...")
    
    added = 0
    exists = 0
    
    for h_data in hackathons_data:
        # Check if already exists
        existing = Hackathon.objects(name=h_data['name']).first()
        if not existing:
            hackathon = Hackathon(**h_data)
            hackathon.save()
            print(f"  + Added: {h_data['name']}")
            added += 1
        else:
            print(f"  - Already exists: {h_data['name']}")
            exists += 1
    
    total = Hackathon.objects.count()
    print(f"\nDone! Added {added} new hackathons. {exists} already existed.")
    print(f"Total hackathons in database: {total}")

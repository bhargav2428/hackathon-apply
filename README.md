# AI Hackathon Auto Apply Agent

An intelligent automation platform that discovers hackathons, checks eligibility, generates AI-powered applications, and auto-applies on your behalf.

## 🚀 Features

- **Multi-Platform Scraping**: Devpost, Unstop, MLH, Hack2Skill
- **AI-Powered Eligibility Checking**: Automatic profile matching
- **Project Idea Generation**: GPT-4 powered creative ideas
- **Auto-Apply Bot**: Playwright browser automation
- **Smart Notifications**: Email, Telegram, Discord
- **n8n Workflow Automation**: Scheduled scraping and processing
- **Modern Dashboard**: Dark theme responsive UI

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+ (for n8n)
- OpenAI API Key
- Docker & Docker Compose (optional)

## 🛠️ Quick Start

### Option 1: Local Development

1. **Clone and setup**:
```bash
cd "hackathon apply"
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
copy .env.example .env
# Edit .env with your API keys
```

3. **Install Playwright browsers**:
```bash
playwright install chromium
```

4. **Run the application**:
```bash
python app.py
```

5. **Access the dashboard**: http://localhost:5000

### Option 2: Docker Compose

1. **Configure environment**:
```bash
copy .env.example .env
# Edit .env with your API keys
```

2. **Start all services**:
```bash
docker-compose up -d
```

3. **Access services**:
   - Dashboard: http://localhost:5000
   - n8n Workflows: http://localhost:5678

## ⚙️ Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask secret key |
| `OPENAI_API_KEY` | OpenAI API key for AI features |

### Optional Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL URL (default: SQLite) |
| `TELEGRAM_BOT_TOKEN` | Telegram notifications |
| `SMTP_HOST` | Email server host |
| `SMTP_USER` | Email username |
| `SMTP_PASSWORD` | Email password |

## 📁 Project Structure

```
hackathon apply/
├── app.py                 # Main Flask application
├── config.py              # Configuration classes
├── database.py            # Database setup
├── models/                # SQLAlchemy models
│   ├── user.py
│   ├── user_profile.py
│   ├── hackathon.py
│   ├── application.py
│   └── ...
├── routes/                # API endpoints
│   ├── auth.py
│   ├── hackathons.py
│   ├── applications.py
│   └── ...
├── services/              # Business logic
│   ├── ai_service.py
│   ├── scrapers.py
│   ├── auto_apply.py
│   └── ...
├── static/                # Frontend files
│   ├── index.html
│   ├── css/styles.css
│   └── js/
├── n8n_workflow.json      # n8n automation workflow
├── Dockerfile
└── docker-compose.yml
```

## 🔄 n8n Workflow Setup

1. Access n8n at http://localhost:5678
2. Import `n8n_workflow.json`
3. Configure credentials:
   - HTTP Header Auth with your API token
4. Activate the workflow

## 📖 API Endpoints

### Authentication
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout

### Hackathons
- `GET /api/hackathons` - List hackathons
- `POST /api/hackathons/scrape` - Trigger scraping

### Applications
- `GET /api/applications` - List applications
- `POST /api/applications` - Create application
- `POST /api/applications/:id/auto-apply` - Auto-apply

### AI Services
- `POST /api/ai/ideas/:hackathon_id` - Generate project idea
- `POST /api/ai/eligibility/:hackathon_id` - Check eligibility

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

MIT License

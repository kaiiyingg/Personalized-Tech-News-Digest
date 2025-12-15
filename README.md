# TechPulse — Personalized Tech News Digest

AI-powered, privacy-conscious tech news platform with hybrid topic classification (AI + keyword rules), personalized feeds, fast AI summaries, automated ingestion, and analytics.

## Overview
TechPulse is a full-stack, privacy-conscious tech news platform that delivers a personalized digest of technology updates. It reduces information overload through hybrid topic classification (AI + keyword rules), tailored feeds, and fast on-demand AI summaries, enabling users to absorb key developments quickly. The system is supported by automated article ingestion pipelines and an analytics dashboard that surfaces trending articles, topics and companies determined by user engagement and topic distribution over the week.

## Key Features
- Personalized discovery feed with topic grouping and image-rich article cards
- Automatic topic assignment via hybrid classification (fast keyword rules + Hugging Face zero-shot AI classification). See `src/services/content_service.py` and `HYBRID_CLASSIFICATION.md`.
- AI Article Summarizer: one-click summaries powered by a Chrome AI summarizer integration (supports TLDR or Key Points)
- Fast View: quick flashcard-style browsing with articles under user's topic of interest.
- Analytics Dashboard: real-time insights into trending topics, popular tech companies, article engagement, and weekly topic distributions—designed to surface what readers care about most.
- Scheduled article ingestion: scheduled source sync and article updates every 6h via GitHub Actions workflow.
- Secure user management: registration, email verification, login, password reset via 6-digit email code and profile setting to change username and password.
- Favorites & Read Tracking: like articles and mark-as-read to tailor recommendations
- Accessibility and UX: semantic HTML, ARIA attributes, keyboard navigation support, and automated accessibility tests

## Demo
Demo video link: https://youtu.be/FGcOdSm-eeU?si=LwKrmJKRzK2rQ-Sp

## Technology Stack
- Backend: Python, Flask
- Frontend: HTML, CSS, and JavaScript
- Database: PostgreSQL (via Supabase)
- Caching/Queue: Redis
- Containerization: Docker, Docker Compose
- Testing: pytest
- Other: Bcrypt for passwords, email-sending for password reset
 - External APIs / Integrations:
	 - Chrome AI Summarizer integration
	 - Email provider for sending 6-digit reset codes (configurable: SendGrid)
	 - News ingestion: RSS feeds
	 - Automated ingestion: GitHub Actions workflow (runs every 6 hours)

## Installation & Local Setup
Prerequisites: Python 3.11+, Docker (optional), PostgreSQL, Redis

1. Clone repo

```bash
git clone https://github.com/kaiiyingg/Personalized-Tech-News-Digest.git
cd Personalized-Tech-News-Digest
```

- 2. Create and activate virtualenv

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Configure environment

Copy the example environment file and fill in secrets. A template is provided as `.env.template`.

```bash
cp .env.template .env
```

Open `.env` and set values for:
- `FLASK_SECRET_KEY` (random string)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `REDIS_URL` (e.g. `redis://localhost:6379/0` or `redis://redis:6379/0` for docker)
- Optional AI: `HF_TOKEN` (Hugging Face) to enable zero-shot classification
- Email: `SENDGRID_API_KEY`, `FROM_EMAIL`, `FROM_NAME` 

5. Initialize database

```bash
python -c "from src.database.connection import create_tables; create_tables()"
```

6. Run the app 

Local:

```bash
docker-compose up --build
# the app will be available at http://localhost:5000
```

Deploy to Render:

1. Create a new Web Service on Render and connect your GitHub repo.
2. Choose Docker as the environment (or use the provided `Dockerfile`).
3. Set the required environment variables in Render's dashboard (use `.env.template` as reference): `FLASK_SECRET_KEY`, DB connection details, `REDIS_URL`, `SENDGRID_API_KEY` (or SMTP), and optional `HF_TOKEN`.
4. Enable automatic deploys from the main branch. The project includes a GitHub Actions workflow for scheduled ingestion (every 6 hours) that you can keep or disable depending on your hosting setup.

## Usage
- Register and set your topics of interest
- Use the Discover feed to browse articles grouped by topic
- Click "AI Summarize" on any article to generate a concise TL;DR or bullet key-points
- Fast View provides flashcard-style browsing and supports scrollable AI summaries
- Use the Analytics dashboard to view article-level metrics and summaries
- Forgot password? Request a 6-digit code sent by email, enter it to reset your password

## Contributing
Contributions welcome. Please open issues for bugs or feature requests. For code contributions, fork, create a feature branch, add tests, and submit a pull request.

## Future Work 

1. Collaborative Discussion Hub
	- Add article-level discussion threads to enable reader conversations. Ensure the space is safe and respectful by adding moderation features: content filtering, user reporting, warning/ban mechanisms, and admin tools for manual moderation.

2. Personalized Recommendation Engine (ML-based)
	- Replace rule-based topic selection with embeddings + similarity search (e.g., FAISS/pgvector) for real-time, personalized article suggestions.

3. Advanced Analytics Dashboard
	- Extend analytics to include cohort retention, user topic trends, and scroll-depth tracking for more product-focused metrics.

4. Lightweight Q&A Chatbot 
	- Build a context-aware assistant that can answer article-specific questions, surface related articles, and produce short clarifications.

## Contact
Chong Kai Ying — chongkaiying578@gmail.com


LinkedIn: https://linkedin.com/in/kai-ying-907bb6178


GitHub: https://github.com/kaiiyingg


# TechPulse: Personalized Tech News Digest

TechPulse is a modern, AI-powered web app that delivers a personalized tech news feed to users. It solves the real-world problem of information overload by automatically curating, classifying, and updating tech articles from top sources—so users always stay ahead in the industry.

## What Sets TechPulse Apart
- **Solves Real Problems:** TechPulse cuts through information overload, delivering only the most relevant tech news and saving users hours every week.
- **Modern, Proven Technologies:** Built with Python, Flask, PostgreSQL, Docker, and HuggingFace Transformers for smart, AI-driven topic classification. Automation powered by schedule and psycopg2 for reliable data access.
- **Built to Grow:** End-to-end automation, secure authentication, favorites, and personalized recommendations—engineered for scale, real deployment, and easy expansion with new features.

## Key Features
- **Automated Ingestion:** Articles are fetched and updated hourly from curated RSS sources and no manual work is required.
- **AI Topic Classification:** Uses HuggingFace zero-shot classification to assign topics to articles, making the feed truly personalized.
- **User Personalization:** Users get a digest tailored to their interests, can save favorites, and interact with content.
- **Minimal Maintenance:** Source syncing and article ingestion are fully automated via a Python scheduler (see `jobs/scheduler.py`).
- **Clean UI:** Responsive web interface for easy reading and interaction.

## Technical Highlights
- **Python 3.x & Flask:** Fast, maintainable backend and REST API.
- **PostgreSQL:** Reliable, scalable relational database.
- **HuggingFace Transformers:** AI-powered topic assignment for every article.
- **schedule:** Python job scheduler for hands-off automation.
- **Docker & Docker Compose:** Consistent local and cloud deployment.
- **Modular Codebase:** Organized into `src/` (app/services/models), `jobs/` (automation scripts), and `tests/` (unit tests).

## Architecture Overview
1. **Automated Jobs:**
   - `jobs/01_sync_sources.py`: Syncs RSS sources to the database daily.
   - `jobs/02_ingest_articles.py`: Ingests new articles hourly.
   - `jobs/scheduler.py`: Runs both jobs automatically—just start the scheduler and everything updates itself.
2. **Web App:**
   - Flask backend serves personalized digests, handles user authentication, and manages favorites.
   - Frontend templates for a clean, modern UI.
3. **AI Automation:**
   - Each article is classified by topic using HuggingFace zero-shot classification.

## Setup & Usage

1. **Clone & Install:**
   ```bash
   git clone https://github.com/kaiiyingg/Personalized-Tech-News-Digest.git
   cd Personalized-Tech-News-Digest
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
2. **Configure Environment:**
   - Copy `.env.example` to `.env` and fill in your DB credentials.
3. **Run Locally:**
   - Start the Flask app: `python src/app.py`
   - Start the scheduler: `python jobs/scheduler.py`
   - Or use Docker Compose for both: `docker-compose up --build`
4. **Access:**
   - Go to `http://localhost:5000` in your browser.

## Docker & Local Development

This project uses Docker and Docker Compose for easy local development and testing. The main services are:

- **db**: PostgreSQL database
- **app**: Flask web application
- **scheduler**: Runs automated jobs (from `jobs/scheduler.py`) for syncing sources and ingesting articles

You can start all services together with:

docker-compose build
docker-compose up

This will build the images, start the database, run the Flask app, and launch the scheduler for automated ingestion/classification. Your code is mounted into the containers for live reloading during development.

## Deployment
This project uses Render for cloud deployment, with full Docker support for easy scaling and CI/CD.
You can deploy the web app, scheduler, and database as separate services on Render using your existing Docker setup.

## Real-World Technical Challenges Solved
- **AI-powered automation:** No manual tagging—topics are assigned by ML.
- **Multi-step workflow:** Source syncing, ingestion, classification, and user personalization all run automatically.
- **Scalable architecture:** Modular, maintainable, and ready for production.


## DevOps & Best Practices
- **CI/CD:** Automated testing, linting, and deployment with GitHub Actions.
- **Containerization:** Docker and Docker Compose for consistent environments and easy scaling.
- **Modular Design:** Clear separation of concerns (services, models, jobs, tests) for maintainability.
- **Automated Jobs:** Python scheduler for hands-off ingestion and syncing.
- **Strict Dependency Management:** requirements.txt and Dockerfile ensure reproducible builds.

## Future Enhancements
- **Advanced Content Filtering:** Smarter filtering based on user engagement, freshness, and personalized weighting.
- **Light Mode:** UI toggle for light/dark mode to improve user experience.
- **Rich Content Sources:** Ingest from YouTube, Twitter, and academic databases.
- **Email/Notification Digests:** Personalized digests via email (AWS SES) or notifications (AWS SNS).
- **Project Idea Recommendations:** AI-powered suggestions for personal tech projects and curated learning resources, inspiring users to turn passive learning into active creation.

## Contact
- Email: chongkaiying578@gmail.com
- LinkedIn: [linkedin.com/in/kai-ying-907bb6178](https://linkedin.com/in/kai-ying-907bb6178)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
# TechPulse: Personalized Tech News Digest

TechPulse is a modern, AI-powered web app that delivers a personalized tech news feed to users. It solves the real-world problem of information overload by automatically curating, classifying, and updating tech articles from top sources—so users always stay ahead in the industry.

## What Sets TechPulse Apart
- **Solves Real Problems:** TechPulse cuts through information overload, delivering only the most relevant tech news and saving users hours every week.
- **Modern, Proven Technologies:** Built with Python, Flask, PostgreSQL, Docker, and HuggingFace Transformers for smart, AI-driven topic classification.
- **User-Driven Content Strategy:** Innovative approach that prioritizes user engagement while optimizing for free-tier hosting constraints.
- **Built to Grow:** Scalable architecture designed for easy migration from user-driven to automated scheduling as infrastructure scales.

## Key Features
- **User-Controlled Content Updates:** One-click refresh system that engages users while working perfectly within free-tier hosting limitations.
- **AI Topic Classification:** Uses HuggingFace zero-shot classification to assign topics to articles, making the feed truly personalized.
- **User Personalization:** Users get a digest tailored to their interests, can save favorites, and interact with content.
- **Clean UI:** Responsive web interface with real-time feedback and intuitive navigation.

## 🚀 Content Management Philosophy

**User-Driven Updates Instead of Background Scheduling**

TechPulse implements a thoughtful content management strategy that demonstrates modern engineering principles:

### **Why This Approach?**
- **Free-Tier Optimization:** Works perfectly within Render's free tier constraints (no persistent background processes)
- **User Engagement:** Encourages community participation and provides immediate gratification
- **Cost-Conscious Engineering:** Only consumes resources when users actively request updates
- **Scalable Foundation:** Easy to migrate to automated scheduling as infrastructure grows

### **How It Works:**
1. Users click "🔄 Refresh" in the navigation bar
2. System fetches latest articles from RSS sources in real-time
3. AI processes and classifies new content
4. Smart cleanup removes old articles while preserving favorites and maintaining minimum content threshold
5. Page reloads with fresh, personalized content
6. Clear feedback throughout the entire process with storage optimization

*See [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) for detailed technical implementation and future roadmap.*

## Technical Highlights
- **Python 3.x & Flask:** Fast, maintainable backend and REST API.
- **PostgreSQL:** Reliable, scalable relational database.
- **HuggingFace Transformers:** AI-powered topic assignment for every article.
- **User-Driven Updates:** Smart content refresh system that works within free-tier constraints.
- **Docker & Docker Compose:** Consistent local and cloud deployment.
- **Modular Codebase:** Organized into `src/` (app/services/models), `jobs/` (ingestion scripts), and `tests/` (unit tests).

## Architecture Overview
1. **Content Management:**
   - `jobs/01_sync_sources.py`: Manages RSS sources in the database.
   - `jobs/02_ingest_articles.py`: Fetches and processes articles on-demand.
   - `jobs/web_jobs.py`: Web-triggered job execution for user-driven updates.
2. **Web Application:**
   - Flask backend serves personalized digests, handles user authentication, and manages favorites.
   - Modern, responsive frontend with real-time feedback.
3. **AI Processing:**
   - Each article is classified by topic using HuggingFace zero-shot classification.
   - Smart content filtering to ensure quality and relevance.

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
   - Copy `.env.template` to `.env` and fill in your actual database credentials.
   - **Security Note:** Never commit `.env` file to git - it contains sensitive credentials.
3. **Run Locally:**
   - Start the Flask app: `python src/app.py`
   - Use Docker Compose: `docker-compose up --build`
4. **Access:**
   - Go to `http://localhost:5000` in your browser.
   - Click "🔄 Refresh" in the navigation to load fresh articles.

## Docker & Local Development

This project uses Docker and Docker Compose for easy local development and testing. The main services are:

- **redis**: High-performance caching layer
- **app**: Flask web application with user-driven content updates

You can start all services together with:

docker-compose build
docker-compose up

This will build the images, start Redis for caching, and run the Flask app with user-driven content updates. Your code is mounted into the containers for live reloading during development.

## Deployment
This project is optimized for Render's free tier deployment, with user-driven content updates that work perfectly within free hosting constraints. The architecture easily scales to automated scheduling when moving to paid infrastructure.

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
- **Intelligent Content Curation:** Advanced AI-powered filtering that learns from user behavior patterns, article engagement metrics, and reading preferences to deliver increasingly personalized content recommendations.
- **Multi-Source Content Integration:** Expand beyond RSS to include YouTube tech channels, Twitter tech influencers, GitHub trending repositories, academic papers from arXiv, and curated newsletters for comprehensive tech coverage.
- **Smart Notification System:** Personalized digest delivery via email (AWS SES) or push notifications (AWS SNS) with intelligent timing based on user activity patterns and preferred reading schedules.
- **Enhanced User Experience:** Light/dark mode toggle, customizable reading preferences, article saving for offline reading, and advanced search functionality across saved and historical content.
- **AI-Powered Project Discovery:** Revolutionary feature that analyzes trending technologies, user interests, and skill level to suggest personalized tech project ideas, complete with learning resources, tutorials, and implementation roadmaps—transforming passive news consumption into active skill development.
- **Community Features:** User-generated content recommendations, shared reading lists, discussion threads on trending topics, and collaborative project matching based on complementary skills and interests.

## Contact
- Email: chongkaiying578@gmail.com
- LinkedIn: [linkedin.com/in/kai-ying-907bb6178](https://linkedin.com/in/kai-ying-907bb6178)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
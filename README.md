# TechPulse: Personalized Tech News Platform

**Production-ready full-stack web application delivering personalized tech news with enterprise-level reliability. Features comprehensive testing, security hardening, and optimized performance. Built for scalability while maintaining cost-effective deployment on free-tier hosting.**

## 🚀 Key Features & Technical Highlights

- **🧠 Smart Content Processing:** Keyword-based classification across 10+ tech domains with intelligent text excerpt generation
- **🏗️ Production Architecture:** Flask REST API, PostgreSQL, Docker containerization, comprehensive test coverage (9 modules, 95%+ coverage)
- **💡 Resource-Conscious Design:** Redis fallback system with graceful degradation for free-tier compatibility
- **🔒 Enterprise Security:** TOTP two-factor authentication, XSS prevention, input sanitization, bcrypt password hashing
- **📊 Real-Time Performance:** Sub-second response times with database optimization, connection pooling, and caching strategies
- **🎯 Enhanced UX:** Fast view optimization with improved pagination and interactive heart button functionality

## 🛠️ Technical Stack

### **Backend**
- **Framework:** Flask REST API with modular service architecture
- **Database:** PostgreSQL with optimized schemas, indexes, and connection pooling
- **Processing:** Keyword-based topic classification with intelligent content filtering
- **Security:** TOTP two-factor authentication, bcrypt password hashing, input sanitization
- **Caching:** Redis with memory fallback for production reliability
- **Testing:** Comprehensive pytest suite with 95%+ coverage across all modules

### **Frontend**
- **Design:** Responsive mobile-first CSS with semantic HTML5 structure and accessibility compliance
- **Interactions:** Asynchronous JavaScript with real-time feedback and optimized pagination
- **UX:** Fast article browsing, interactive heart buttons, seamless user experience

### **DevOps & Quality**
- **Testing:** Comprehensive pytest suite (9 modules) with unit, integration, performance, security, and accessibility tests
- **Code Quality:** Black formatting, Flake8 linting, Bandit security scanning with automated test runner
- **Containerization:** Docker multi-stage builds with environment-specific configuration

## 📁 Project Structure

```
TechPulse/
├── src/                          # Core application code
│   ├── models/                   # Data models (User, Content, Source, Interactions)
│   ├── services/                 # Business logic with comprehensive error handling
│   ├── utils/                    # Caching, HTML cleaning, security utilities
│   ├── database/                 # Schema migrations and optimized connections
│   ├── templates/                # Responsive Jinja2 templates
│   ├── static/                   # Optimized CSS, JavaScript, and assets
│   └── app.py                    # Flask application with production configurations
├── tests/                        # Complete test suite (9 modules, 95%+ coverage)
│   ├── test_content_service.py   # Article processing and favorites
│   ├── test_user_service.py      # Authentication and user management
│   ├── test_fast_view.py         # UI interactions and heart button functionality
│   ├── test_html_cleaning.py     # Security and content sanitization
│   ├── test_improvements.py      # Performance and load testing
│   └── test_optimizations.py     # Caching and query optimization
├── jobs/                         # Background RSS processing and ingestion
├── docker-compose.yml            # Multi-environment orchestration
└── requirements.txt              # Pinned dependencies with security updates
```

## ⚡ Quick Start

```bash
# Clone and setup
git clone https://github.com/kaiiyingg/Personalized-Tech-News-Digest.git
cd Personalized-Tech-News-Digest
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt

# Run comprehensive tests locally
pytest --cov=src --cov-report=html  # Generate coverage report
run_tests.bat                       # Full test suite with code quality checks

# Configure environment and database
cp .env.template .env  # Edit with your credentials
python -c "from src.database.connection import create_tables; create_tables()"

# Run application
docker-compose up --build  # or python src/app.py
```

**Live Demo:** [TechPulse on Render](https://personalized-tech-news-digest.onrender.com)  
**Local Access:** http://localhost:5000 → Register → Click "Refresh" to load articles

## 🔧 Engineering Solutions & Roadmap

### **Challenge 1: Storage Constraints (1GB Hosting Limit)**
- **Problem:** AI models (460MB+) and accumulated data exceeded hosting storage limits causing deployment issues
- **Current Solution:** Keyword-based classification maintaining 90% functionality with efficient data management
- **Future Enhancement:** HuggingFace Transformers integration when upgraded hosting becomes available (tested locally, deployment limited by current hosting tier)

### **Challenge 2: Free-Tier Infrastructure Limitations**
- **Problem:** No persistent background processes, cron jobs, or advanced caching
- **Current Solution:** User-driven refresh system with real-time feedback and efficient on-demand processing
- **Future Enhancement:** Automated scheduling, Redis caching, real-time WebSocket updates (tested locally, deployment limited by current hosting tier) 

### **Challenge 3: Scalability & Advanced Features**
- **Problem:** Production constraints limit feature implementation despite technical feasibility
- **Current Solution:** Environment-specific configuration with graceful degradation strategies
- **Future Enhancement:** Advanced search, team collaboration, analytics dashboard, progressive web app

## 🤝 Contact & Skills Demonstrated

**Chong Kai Ying**

- **Email:** [chongkaiying578@gmail.com](mailto:chongkaiying578@gmail.com)
- **LinkedIn:** [linkedin.com/in/kai-ying-907bb6178](https://linkedin.com/in/kai-ying-907bb6178)
- **GitHub:** [github.com/kaiiyingg](https://github.com/kaiiyingg)

### **Technical Expertise Demonstrated**
✅ **Full-Stack Development:** Modern web architecture, REST APIs, responsive frontend with semantic HTML5  
✅ **Database Engineering:** PostgreSQL optimization, connection pooling, performance tuning  
✅ **Testing & Quality:** 95%+ test coverage across 9 modules, performance testing, security validation  
✅ **Production Engineering:** Error handling, Redis fallback systems, resource optimization  
✅ **Security Implementation:** TOTP authentication, XSS prevention, input sanitization  
✅ **Problem-Solving:** Graceful degradation, fallback systems, constraint-based solutions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for complete terms and conditions.

---

**MIT Licensed** | **Production-Ready Codebase** | **Scalable Architecture**
# TechPulse: Personalized Tech News Platform

**Production-ready full-stack web application that solves information overload by intelligently curating tech news from dozens of sources. Delivers personalized, relevant content while operating efficiently within budget hosting constraints to provide affordable access to quality tech journalism.**

## 🚀 Key Features & Technical Highlights

- **🧠 Smart Content Processing:** Keyword-based classification across 10+ tech domains with intelligent text excerpt generation
- **🏗️ Production Architecture:** Flask REST API, PostgreSQL, Docker containerization, comprehensive test coverage
- **💡 Resource-Conscious Design:** Optimized for 1GB storage limits through efficient algorithms and lightweight processing
- **🔒 Enterprise Security:** TOTP two-factor authentication, bcrypt password hashing, environment-based configuration
- **📊 Real-Time Performance:** Sub-second response times with database optimization and connection pooling

## 🛠️ Technical Stack

### **Backend**
- **Framework:** Flask REST API with modular service architecture
- **Database:** PostgreSQL with optimized schemas, indexes, and migrations
- **Processing:** Keyword-based topic classification, intelligent content filtering
- **Security:** TOTP authentication, secure session management, input validation
- **Testing:** Comprehensive pytest suite covering services, models, and API endpoints

### **Frontend**
- **Design:** Responsive mobile-first CSS with progressive enhancement
- **Interactions:** Asynchronous JavaScript, real-time feedback, progressive loading
- **UX:** Intuitive navigation, interactive notifications, seamless user experience

### **DevOps**
- **Containerization:** Docker multi-stage builds with optimized image layers
- **Deployment:** Environment variable configuration, automatic database migrations
- **Quality:** Structured logging, error handling, code quality standards

## 📁 Project Structure

```
TechPulse/
├── src/                          # Core application code
│   ├── models/                   # Data models (User, Content, Source, Interactions)
│   ├── services/                 # Business logic layer
│   ├── database/                 # Schema migrations and connection management
│   ├── templates/                # Jinja2 HTML templates
│   ├── static/                   # CSS, JavaScript, and assets
│   └── app.py                    # Flask application entry point
├── jobs/                         # Background processing and ingestion
├── tests/                        # Comprehensive test suite
├── docker-compose.yml            # Development environment orchestration
└── requirements.txt              # Python dependencies with version pinning
```

## ⚡ Quick Start

```bash
# Clone and setup
git clone https://github.com/kaiiyingg/Personalized-Tech-News-Digest.git
cd Personalized-Tech-News-Digest
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt

# Configure environment and database
cp .env.template .env  # Edit with your credentials
python -c "from src.database.connection import create_tables; create_tables()"

# Run application
docker-compose up --build  # or python src/app.py
```

**Access:** http://localhost:5000 → Register → Click "Refresh" to load articles

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
✅ **Full-Stack Development:** Modern web architecture, REST APIs, responsive frontend  
✅ **Database Engineering:** PostgreSQL optimization, migrations, performance tuning  
✅ **Memory-Optimized Engineering:** Resource-conscious development for constrained environments  
✅ **DevOps & Testing:** Docker containerization, comprehensive test suites, CI/CD practices  
✅ **Security Implementation:** Authentication systems, data protection, secure configuration  
✅ **Problem-Solving:** Practical solutions within real-world hosting limitations

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for complete terms and conditions.

---

**MIT Licensed** | **Production-Ready Codebase** | **Scalable Architecture**
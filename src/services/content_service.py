"""
Content Service Module

Provides content management functionality for the tech news digest application:
- Content creation, retrieval, and classification
- Topic-based content filtering and categorization
- User content interactions (likes, read status)
- Article ingestion pipeline support
- Memory-optimized operations for 512MB hosting environments

Content Classification:
    Uses keyword-based classification instead of AI models for memory efficiency.
    Supports 9 tech topic categories with strict filtering for quality content.
"""

from src.database.connection import get_db_connection, close_db_connection
from src.models.content import Content
from .user_service import get_user_topics
from typing import List, Optional, Dict, Any, Union
from psycopg2 import errors as pg_errors
from datetime import datetime
import re

# Import caching utility
try:
    from src.utils.cache import cache_result
except ImportError:
    # Fallback if cache module doesn't exist
    def cache_result():
        def decorator(func):
            return func
        return decorator

# ===== TOPIC CLASSIFICATION CONSTANTS =====

AI_ML_TOPIC = "AI & ML"
AI_ML_SHORT = "AI & ML"
CYBERSECURITY_TOPIC = "Cybersecurity & Privacy"
CLOUD_DEVOPS_TOPIC = "Cloud Computing & DevOps"
SOFTWARE_DEV_TOPIC = "Software Development & Web Technologies"
DATA_SCIENCE_TOPIC = "Data Science & Analytics"
EMERGING_TECH_TOPIC = "Emerging Technologies"
BIG_TECH_TOPIC = "Big Tech & Industry Trends"
TECH_CULTURE_TOPIC = "Tech Culture & Work"
OPEN_SOURCE_TOPIC = "Open Source"

TOPIC_LABELS = [
    AI_ML_TOPIC, CYBERSECURITY_TOPIC, CLOUD_DEVOPS_TOPIC, 
    SOFTWARE_DEV_TOPIC, DATA_SCIENCE_TOPIC, EMERGING_TECH_TOPIC,
    BIG_TECH_TOPIC, TECH_CULTURE_TOPIC, OPEN_SOURCE_TOPIC
]

# ===== UTILITY FUNCTIONS =====

def format_datetime(dt) -> Optional[str]:
    """
    Format datetime objects to ISO string format consistently.
    
    Args:
        dt: Datetime object or string to format
        
    Returns:
        Optional[str]: ISO formatted datetime string or None
    """
    if dt and hasattr(dt, 'isoformat'):
        return dt.isoformat()
    elif dt:
        return str(dt)
    else:
        return None

# ===== DATA TRANSFORMATION HELPERS =====

def build_article_dict(row, custom_topic=None) -> Dict[str, Any]:
    """
    Transform database row into standardized article dictionary.
    
    Args:
        row: Database row tuple with article data
        custom_topic: Optional override for article topic
        
    Returns:
        Dict[str, Any]: Standardized article dictionary with metadata
    """
    published_at = format_datetime(row[5])
    interaction_at = format_datetime(row[10]) if len(row) > 10 else None
    
    # Handle topic display logic
    topic = custom_topic if custom_topic else row[6]
    if topic == AI_ML_TOPIC:
        topic = AI_ML_SHORT
    
    article = {
        'id': row[0],
        'source_id': row[1],
        'title': row[2],
        'summary': row[3],
        'article_url': row[4],
        'published_at': published_at,
        'topic': topic,
        'image_url': row[7],
        'source_name': row[8] if len(row) > 8 else None,
        'source_feed_url': row[9] if len(row) > 9 else None
    }
    
    # Add interaction data if available
    if len(row) > 10:
        article.update({
            'is_read': row[8] if row[8] is not None else False,
            'is_liked': row[9] if row[9] is not None else False,
            'is_saved': row[9] if row[9] is not None else False,
            'interaction_at': interaction_at,
            'source_name': row[11],
            'source_feed_url': row[12]
        })
    
    return article

def build_simple_article_dict(row) -> Dict[str, Any]:
    """
    Build simplified article dictionary without user interaction data.
    
    Args:
        row: Database row tuple with basic article data
        
    Returns:
        Dict[str, Any]: Article dictionary without interaction metadata
    """
    published_at = format_datetime(row[5])
    
    return {
        'id': row[0],
        'source_id': row[1],
        'title': row[2],
        'summary': row[3],
        'article_url': row[4],
        'published_at': published_at,
        'topic': row[6],
        'image_url': row[7],
        'source_name': row[8],
        'source_feed_url': row[9]
    }

# ===== CONTENT CLASSIFICATION =====

def classify_topic_by_keywords(text: str, title: str) -> str:
    """
    Classify content into tech topics using keyword matching.
    Memory-optimized alternative to AI models for 512MB hosting.
    
    Args:
        text (str): Article content/summary
        title (str): Article title
        
    Returns:
        str: Classified topic category from TOPIC_LABELS
    """
    combined_text = (title + " " + text).lower()

    # Open Source keywords (expanded)
    opensource_keywords = [
        "open source", "github", "gitlab", "linux", "ubuntu", "debian", "fedora", "arch linux", "red hat", "centos",
        "apache", "mozilla", "gnu", "copyleft", "mit license", "gpl", "bsd license", "apache license", "eclipse foundation",
        "fork", "pull request", "contributor", "maintainer", "foss", "oss", "openstack", "kde", "gnome", "freebsd", "openbsd"
    ]

    # Big Tech & Industry keywords (expanded)
    bigtech_keywords = [
        "google", "microsoft", "apple", "amazon", "meta", "facebook", "twitter", "tesla", "nvidia", "intel", "amd", "samsung",
        "startup", "venture capital", "vc", "funding", "investment", "ipo", "acquisition", "merger", "spinoff", "spac",
        "silicon valley", "entrepreneur", "business model", "revenue", "unicorn", "series a", "series b", "industry", "market", "stock",
        "bytedance", "tiktok", "baidu", "alibaba", "xiaomi", "huawei", "oracle", "ibm", "sap", "salesforce", "adobe", "paypal"
    ]

    # Tech Culture & Work keywords (expanded)
    culture_keywords = [
        "remote work", "work from home", "developer survey", "salary", "job", "career", "hiring", "interview", "workplace", "team",
        "culture", "burnout", "productivity", "diversity", "inclusion", "tech workers", "engineers", "engineering", "stackoverflow",
        "stack overflow", "survey", "trends", "skills", "layoff", "fired", "promotion", "onboarding", "exit interview", "work visa"
    ]

    # AI & ML keywords (expanded)
    ai_keywords = [
        "ai", "artificial intelligence", "machine learning", "ml", "neural network", "deep learning", "nlp", "computer vision",
        "tensorflow", "pytorch", "chatgpt", "llm", "gpt", "bert", "transformer", "openai", "anthropic", "claude", "gemini", "copilot",
        "chatbot", "automation", "robotics", "algorithm", "mistral", "llama", "llama 2", "llama 3", "sora", "stable diffusion", "midjourney",
        "dalle", "dall-e", "slm", "small language model", "large language model", "prompt engineering", "vector db", "embedding", "inference"
    ]

    # Cybersecurity keywords (expanded)
    security_keywords = [
        "security", "cybersecurity", "hack", "hacker", "breach", "vulnerability", "exploit", "cve", "encryption", "privacy", "malware",
        "ransomware", "phishing", "zero-day", "firewall", "antivirus", "vpn", "authentication", "password", "biometric", "two-factor",
        "ssl", "tls", "pentest", "penetration test", "red team", "blue team", "infosec", "threat", "mitre", "cisa", "nist", "iso 27001",
        "cryptography", "crypto", "public key", "private key", "certificate", "token", "access control", "siem", "ids", "ips", "forensics",
        "incident response", "bug bounty", "security audit", "rootkit", "keylogger", "spyware", "trojan", "worm", "backdoor", "botnet",
        "cyberattack", "cybercrime", "cyberwarfare", "cyber defense", "cyber offense", "zero trust", "mfa", "sso", "xss", "csrf", "sql injection"
    ]

    # Cloud & DevOps keywords (expanded)
    cloud_keywords = [
        "cloud", "aws", "azure", "gcp", "docker", "kubernetes", "devops", "ci/cd", "deployment", "infrastructure", "serverless",
        "microservices", "containerization", "orchestration", "scalability", "load balancing", "terraform", "ansible", "helm", "istio",
        "cloudflare", "alb", "elb", "s3", "ec2", "lambda", "cloud run", "cloud function", "cloud storage", "cloud sql", "cloud native",
        "service mesh", "argo", "argo cd", "prometheus", "grafana", "monitoring", "observability", "opsgenie", "pagerduty"
    ]

    # Software Development keywords (expanded)
    dev_keywords = [
        "programming", "coding", "developer", "software", "web development", "javascript", "python", "react", "node.js", "framework",
        "api", "frontend", "backend", "fullstack", "typescript", "angular", "vue", "php", "ruby", "java", "c++", "rust", "go", "scala",
        "kotlin", "mobile", "app", "application", "ios", "android", "smartphone", "swift", "objective-c", "flutter", "dart", "svelte",
        "next.js", "nuxt.js", "express.js", "django", "flask", "spring", "dotnet", ".net", "c#", "perl", "matlab", "assembly", "shell script"
    ]

    # Data Science keywords (expanded)
    data_keywords = [
        "data science", "analytics", "big data", "database", "sql", "visualization", "statistics", "analysis", "pandas", "numpy",
        "matplotlib", "tableau", "power bi", "data mining", "etl", "data warehouse", "nosql", "mongodb", "postgresql", "mysql",
        "data lake", "data pipeline", "data engineer", "data analyst", "feature engineering", "data cleaning", "data wrangling",
        "jupyter", "notebook", "spark", "hadoop", "presto", "snowflake", "redshift", "bigquery", "superset", "looker"
    ]

    def has_keyword(keywords):
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', combined_text, re.IGNORECASE):
                return True
        return False

    # Prioritize: security > cloud > open source > ai/ml > bigtech > dev > data > culture
    if has_keyword(security_keywords):
        return CYBERSECURITY_TOPIC
    if has_keyword(cloud_keywords):
        return CLOUD_DEVOPS_TOPIC
    if has_keyword(opensource_keywords):
        return OPEN_SOURCE_TOPIC
    if has_keyword(ai_keywords):
        return AI_ML_TOPIC
    if has_keyword(bigtech_keywords):
        return BIG_TECH_TOPIC
    if has_keyword(dev_keywords):
        return SOFTWARE_DEV_TOPIC
    if has_keyword(data_keywords):
        return DATA_SCIENCE_TOPIC
    if has_keyword(culture_keywords):
        return TECH_CULTURE_TOPIC
    return EMERGING_TECH_TOPIC  # Default fallback

# --- Get article by ID (regardless of user/read status) ---
def get_article_by_id(article_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch a single article by its ID from the content table, including source info.
    Returns None if not found.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = """
            SELECT
                c.id, c.source_id, c.title, c.summary, c.article_url,
                c.published_at, c.topic, c.image_url,
                s.source_name AS source_name, s.feed_url AS source_feed_url
            FROM
                content c
            JOIN
                sources s ON c.source_id = s.id
            WHERE c.id = %s
        """
        cur.execute(query, (article_id,))
        row = cur.fetchone()
        if row:
            published_at = format_datetime(row[5])
            return {
                'id': row[0],
                'source_id': row[1],
                'title': row[2],
                'summary': row[3],
                'article_url': row[4],
                'published_at': published_at,
                'topic': row[6],
                'image_url': row[7],
                'source_name': row[8],
                'source_feed_url': row[9]
            }
        return None
    except Exception as e:
        print(f"Error fetching article by id {article_id}: {e}")
        return None
    finally:
        close_db_connection(conn)

def assign_topic(title: str, summary: str) -> Optional[str]:
    """
    Assigns a topic to content using zero-shot classification with STRICT tech filtering.
    Returns None if content is not tech-related, which prevents ingestion.
    """
    text = f"{title} {summary}".lower()
    
    # OPTIMIZED tech keyword requirements - relaxed for speed and accuracy
    tech_keywords = [
        'technology', 'tech', 'software', 'hardware', 'artificial intelligence', 'ai',
        'machine learning', 'ml', 'programming', 'coding', 'developer', 'development',
        'computer', 'computing', 'digital', 'internet', 'web', 'app', 'application',
        'startup', 'silicon valley', 'google', 'microsoft', 'apple', 'amazon', 'meta',
        'facebook', 'twitter', 'tesla', 'nvidia', 'cybersecurity', 'security',
        'blockchain', 'cryptocurrency', 'bitcoin', 'cloud', 'data science', 'analytics',
        'algorithm', 'api', 'database', 'framework', 'open source', 'github', 'linux',
        'windows', 'android', 'ios', 'mobile', 'smartphone', 'robotics', 'automation',
        'fintech', 'edtech', 'saas', 'platform', 'gaming', 'virtual reality', 'vr',
        'augmented reality', 'ar', 'quantum computing', 'semiconductor', 'chip',
        'processor', 'server', 'network', 'wifi', 'bluetooth', 'electronic', 'device',
        'python', 'javascript', 'java', 'react', 'node', 'typescript', 'rust', 'go',
        'kubernetes', 'docker', 'aws', 'azure', 'gcp', 'devops', 'ci/cd', 'agile',
        'scrum', 'bug', 'feature', 'release', 'version', 'update', 'upgrade', 'patch',
        'chatbot', 'gpt', 'llm', 'neural', 'model', 'training', 'dataset', 'inference',
        'survey', 'stackoverflow', 'stack overflow', 'code', 'engineers', 'engineering'
    ]
    
    # COMPREHENSIVE reject keywords - filter out clearly non-tech content
    reject_keywords = [
        # Adult/NSFW content
        'vibrator', 'sex', 'adult', 'porn', 'explicit', 'nsfw', 'erotic', 'sexual',
        'nude', 'naked', 'strip', 'escort', 'prostitution', 'xxx',
        
        # Promotional/Sales/Marketing content
        'lifetime subscription', 'lifetime access', 'limited time offer', 'special deal',
        'discount', 'sale price', 'reg. price', 'half off', 'save money', 'cheap price',
        'bargain', 'promotion', 'promo code', 'coupon', 'deal of the day', 'flash sale',
        'subscription service', 'streaming service', 'membership deal', 'annual plan',
        'get it now', 'buy now', 'order today', 'free trial', 'trial offer',
        'documentary subscription', 'movie subscription', 'tv subscription',
        'binge-watching', 'binge watch', 'entertainment subscription',
        'curiosity stream', 'netflix', 'hulu', 'disney plus', 'amazon prime',
        
        # Government/Policy/Housing/Real Estate
        'government policy', 'housing policy', 'public housing', 'income ceiling',
        'eligibility criteria', 'bto', 'built to order', 'hdb', 'housing board',
        'minister', 'ministry', 'parliament', 'senator', 'congressman', 'mp',
        'national development', 'urban planning', 'housing scheme', 'property prices',
        'housing supply', 'housing demand', 'affordable housing', 'subsidized housing',
        'residential property', 'property market', 'real estate market', 'home ownership',
        'first-time buyers', 'housing grants', 'housing loan', 'mortgage rates',
        'singles scheme', 'flat application', 'ballot results', 'housing queue',
        
        # Sports & Recreation
        'sports', 'football', 'basketball', 'baseball', 'soccer', 'golf', 'tennis',
        'hockey', 'rugby', 'cricket', 'swimming', 'racing', 'olympics', 'fifa',
        'nfl', 'nba', 'mlb', 'athlete', 'stadium', 'tournament', 'championship',
        
        # Health & Medical (non-tech)
        'medical', 'health', 'doctor', 'hospital', 'patient', 'disease', 'virus',
        'vaccine', 'medicine', 'therapy', 'treatment', 'surgery', 'clinic',
        'prescription', 'pharmaceutical', 'symptoms', 'diagnosis', 'cancer',
        'diabetes', 'heart disease', 'mental health', 'depression', 'anxiety',
        
        # Lifestyle & Personal
        'parenting', 'autism', 'disability', 'pregnancy', 'baby', 'children',
        'marriage', 'wedding', 'divorce', 'relationship', 'dating', 'romance',
        'family', 'mother', 'father', 'parent', 'kids', 'toddler', 'infant',
        
        # Food & Cooking
        'recipe', 'cooking', 'kitchen', 'restaurant', 'food', 'dining', 'chef',
        'nutrition', 'diet', 'meal', 'calories', 'ingredients', 'baking',
        'grocery', 'supermarket', 'fast food', 'delivery', 'takeout',
        
        # Fashion & Beauty
        'fashion', 'beauty', 'makeup', 'skincare', 'clothing', 'style', 'outfit',
        'jewelry', 'accessories', 'cosmetics', 'perfume', 'hair', 'salon',
        'designer', 'brand', 'luxury', 'boutique', 'shopping',
        
        # Politics & Government (general)
        'politics', 'election', 'government', 'president', 'senator', 'congress',
        'parliament', 'democracy', 'republican', 'democrat', 'vote', 'ballot',
        'campaign', 'policy', 'legislation', 'law', 'court', 'justice', 'legal',
        
        # Religion & Spirituality
        'religion', 'church', 'prayer', 'spiritual', 'bible', 'god', 'faith',
        'christian', 'muslim', 'jewish', 'buddhist', 'hindu', 'mosque', 'temple',
        'worship', 'holy', 'sacred', 'divine', 'prophet', 'priest', 'pastor',
        
        # Travel & Tourism
        'travel', 'vacation', 'tourism', 'hotel', 'flight', 'airline', 'airport',
        'destination', 'cruise', 'resort', 'trip', 'journey', 'adventure',
        'passport', 'visa', 'booking', 'accommodation', 'sightseeing',
        
        # Finance (non-fintech) & Insurance
        'real estate', 'property', 'mortgage', 'insurance', 'loan', 'debt',
        'credit card', 'bank account', 'savings', 'retirement', 'pension',
        'broker', 'realtor', 'apartment', 'house', 'rent', 'lease',
        'investment advice', 'stock tips', 'forex trading', 'commodity trading',
        
        # Entertainment (non-tech)
        'celebrity', 'entertainment', 'movie', 'film', 'music', 'concert', 'album',
        'actor', 'actress', 'singer', 'musician', 'band', 'tv show', 'series',
        'drama', 'comedy', 'horror', 'romance', 'documentary', 'theater',
        'streaming content', 'video content', 'television', 'cable tv',
        
        # Traditional Education (non-edtech)
        'school', 'teacher', 'student', 'university', 'college', 'classroom',
        'homework', 'exam', 'grade', 'diploma', 'degree', 'tuition', 'campus',
        'dormitory', 'scholarship', 'academic', 'curriculum', 'syllabus',
        
        # Weather & Environment (non-tech)
        'weather', 'rain', 'snow', 'storm', 'hurricane', 'tornado', 'flood',
        'drought', 'temperature', 'climate change', 'global warming', 'pollution',
        'earthquake', 'tsunami', 'volcano', 'wildfire', 'natural disaster',
        'air quality', 'outdoor air', 'environmental monitoring', 'atmosphere',
        'air pollution', 'smog', 'particulate matter', 'pm2.5', 'ozone',
        
        # Automotive (non-tech aspects)
        'car accident', 'traffic jam', 'speeding', 'parking', 'gas station',
        'oil change', 'tire', 'engine repair', 'mechanic', 'insurance claim',
        
        # Agriculture & Farming
        'farming', 'agriculture', 'crop', 'harvest', 'livestock', 'cattle',
        'chicken', 'pig', 'farm', 'farmer', 'tractor', 'fertilizer', 'pesticide',
        
        # Arts & Crafts
        'painting', 'drawing', 'sculpture', 'pottery', 'knitting', 'sewing',
        'craft', 'art gallery', 'museum', 'exhibition', 'artist', 'canvas',
        
        # Non-tech DIY and making
        'welding', 'aluminum welding', 'metalworking', 'woodworking', 'carpentry',
        'construction', 'building materials', 'diy project', 'handmade', 'crafting',
        'workshop', 'tools', 'hammer', 'drill', 'saw', 'materials',
        
        # Games and puzzles (non-tech)
        'wordle', 'crossword', 'puzzle', 'game hints', 'game answers', 'strands',
        'connections', 'nyt games', 'word games', 'brain games', 'sudoku',
        
        # Internet services (non-tech business)
        'internet provider', 'internet service', 'broadband', 'cable', 'fiber internet',
        'isp', 'home internet', 'wifi plan', 'internet speed', 'internet deals',
        
        # Shopping and consumer advice
        'shopping addiction', 'fake store', 'consumer advice', 'buying guide',
        'product review', 'best deals', 'shopping tips', 'retail therapy',
        
        # News/Current Events (non-tech)
        'breaking news', 'latest news', 'current events', 'local news', 'world news',
        'crime news', 'police report', 'court case', 'lawsuit', 'legal battle',
        'scandal', 'controversy', 'investigation', 'arrest', 'charges filed',
        
        # Social Issues (non-tech)
        'social issues', 'community problems', 'social welfare', 'poverty',
        'homelessness', 'unemployment', 'social services', 'charity', 'donation',
        'volunteer work', 'social activism', 'protest', 'demonstration',
        
        # Content that's clearly promotional or spam-like
        'tl;dr', 'tldr', 'elevate your', 'get access to', 'exclusive access',
        'limited offer', 'act now', 'dont miss out', "don't miss out",
        'while supplies last', 'hurry up', 'last chance', 'final days',
        'expires soon', 'time sensitive', 'urgent', 'important notice'
    ]
    
    # Count tech vs non-tech indicators
    tech_score = sum(1 for keyword in tech_keywords if keyword in text)
    reject_score = sum(1 for keyword in reject_keywords if keyword in text)
    
    # Additional pattern-based rejection (regex patterns for common non-tech content)
    import re
    
    # Promotional patterns
    promotional_patterns = [
        r'get .* for \$\d+',  # "get a lifetime of documentaries for $200"
        r'lifetime .* for \$\d+',  # "lifetime subscription for $99"
        r'reg\. \$\d+',  # "reg. $399.99"
        r'now \$\d+.*reg\. \$\d+',  # "now $199.99 (reg. $399.99)"
        r'half off.*price',  # "half off the regular price"
        r'tl;?dr:.*subscription',  # "TL;DR: ... subscription"
        r'\$\d+.*reg\. \$\d+',  # "$199.99 (reg. $399.99)"
        r'subscription.*plan.*off',  # "subscription to ... plan, now half off"
        r'save \$\d+',  # "save $200"
        r'discount.*\$\d+',  # "discount of $100"
        r'special.*offer.*\$\d+',  # "special offer for $99"
    ]
    
    # Government/policy patterns
    policy_patterns = [
        r'minister.*says?',  # "minister says"
        r'government.*policy',  # "government policy"
        r'policy.*review',  # "policy under review"
        r'eligibility.*age.*review',  # "eligibility age for singles under review"
        r'income.*ceiling.*review',  # "income ceilings under review"
        r'public.*housing.*policy',  # "public housing policies"
        r'national.*development.*minister',  # "National Development Minister"
        r'housing.*supply.*demand',  # "housing supply and demand"
        r'appropriate.*time.*depending',  # "appropriate time depending on supply and demand"
    ]
    
    # Check for promotional patterns
    promotional_matches = sum(1 for pattern in promotional_patterns if re.search(pattern, text, re.IGNORECASE))
    
    # Check for policy patterns  
    policy_matches = sum(1 for pattern in policy_patterns if re.search(pattern, text, re.IGNORECASE))
    
    # Enhanced rejection logic
    total_rejection_signals = reject_score + promotional_matches + policy_matches
    
    # STRICTER filtering: Reject if ANY rejection signals are found
    if total_rejection_signals > 0:
        print(f"REJECTED: Non-tech content detected in '{title[:50]}...' (keyword_score: {reject_score}, promotional: {promotional_matches}, policy: {policy_matches})")
        return None
    
    # Additional checks for edge cases
    # Check if title/summary contains mostly price/promotional information
    price_mentions = len(re.findall(r'\$\d+', text))
    percentage_mentions = len(re.findall(r'\d+%\s*off', text))
    
    if price_mentions >= 2 or percentage_mentions >= 1:
        print(f"REJECTED: Promotional content detected (prices: {price_mentions}, percentages: {percentage_mentions}) in '{title[:50]}...'")
        return None
    
    # Check for subscription service names that are typically entertainment
    entertainment_services = [
        'curiosity stream', 'netflix', 'hulu', 'disney plus', 'amazon prime video',
        'paramount plus', 'hbo max', 'apple tv', 'peacock', 'discovery plus',
        'crunchyroll', 'funimation', 'showtime', 'starz', 'epix'
    ]
    
    for service in entertainment_services:
        if service in text:
            print(f"REJECTED: Entertainment service content detected ('{service}') in '{title[:50]}...'")
            return None
    
    # Require at least 2 tech keywords for acceptance
    if tech_score < 2:
        print(f"REJECTED: Insufficient tech keywords ({tech_score}) in '{title[:50]}...'")
        return None
    
    # Memory optimization: Use simple keyword-based topic classification instead of AI
    # to avoid loading large transformer models that exceed 512MB memory limit
    topic = classify_topic_by_keywords(text, title)
    print(f"ACCEPTED: Tech article classified as '{topic}' for '{title[:50]}...'")
    
    return topic

def create_content_item(source_id: int, title: str, summary: str,
                        article_url: str, published_at: Optional[datetime], topic: Optional[str] = None, image_url: Optional[str] = None) -> Optional[Content]:
    """
    Creates a new content item in the database. Used by the ingestion pipeline.

    Args:
        source_id (int): The ID of the source from which this content was fetched.
        title (str): The title of the content.
        summary (str): A summary or snippet of the content.
        article_url (str): The URL to the full article.
        published_at (Optional[datetime]): The original publication date/time.

    Returns:
        Optional[content]: The created content object if successful, None if article_url already exists.
    """
    # Clean HTML from summary before storing in database
    import re
    from bs4 import BeautifulSoup
    
    # Multi-stage HTML cleaning
    clean_soup = BeautifulSoup(summary, "html.parser")
    cleaned_summary = clean_soup.get_text(separator=" ", strip=True)
    
    # Additional regex cleaning for any remaining HTML
    cleaned_summary = re.sub(r'<[^>]+>', '', cleaned_summary)  # Remove any remaining tags
    cleaned_summary = re.sub(r'&[a-zA-Z0-9#]+;', ' ', cleaned_summary)  # Remove HTML entities
    cleaned_summary = re.sub(r'\s+', ' ', cleaned_summary).strip()  # Clean up whitespace
    cleaned_summary = cleaned_summary.replace('"', '').replace("'", "")  # Remove quotes from attributes
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Assign topic if not provided
        topic_val = topic if topic else assign_topic(title, cleaned_summary)
        
        # If topic assignment returns None, reject the content (not tech-related)
        if topic_val is None:
            print(f"Content rejected - not tech-related: {title[:50]}...")
            return None
            
        cur.execute(
            """
            INSERT INTO content (source_id, title, summary, article_url, published_at, topic, image_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, topic, image_url;
            """,
            (source_id, title, cleaned_summary, article_url, published_at, topic_val, image_url)
        )
        row = cur.fetchone()
        if row is None:
            if conn: conn.rollback()
            return None
        content_id, topic_db, image_url_db = row
        conn.commit()
        return Content(content_id, source_id, title, cleaned_summary, article_url, published_at, topic_db, image_url_db)
    except pg_errors.UniqueViolation as e:
        print(f"Error: Content item with URL '{article_url}' already exists. {e}")
        if conn: conn.rollback()
        return None
    except Exception as e:
        print(f"An error occurred during content item creation: {e}")
        if conn: conn.rollback()
        return None
    finally:
        close_db_connection(conn)

def get_personalized_digest(user_id: int, limit: int = 20, offset: int = 0,
                             include_read: bool = False) -> List[Dict[str, Any]]:
    """
    Retrieves a general digest of content items for a user, based on all sources the user is subscribed to,
    and returns the latest articles from all sources the user follows, regardless of topic. This is used for the
    discover page.

    Args:
        user_id (int): The ID of the logged-in user.
        limit (int): Maximum number of articles to return.
        offset (int): Offset for pagination.
        include_read (bool): If True, includes articles already marked as read.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each representing an article
            with its content details and user interaction status.
    """
    conn = None
    digest_items = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Base query: Join content with user_content_interactions
        # LEFT JOIN ensures all content items are included, even if no interaction yet
        query = """
            SELECT
                c.id, c.source_id, c.title, c.summary, c.article_url,
                c.published_at, c.topic, c.image_url,
                uci.is_read, uci.is_liked, uci.interaction_at,
                s.source_name AS source_name, s.feed_url AS source_feed_url
            FROM
                content c
            JOIN
                sources s ON c.source_id = s.id
            LEFT JOIN
                user_content_interactions uci ON c.id = uci.content_id AND uci.user_id = %s
        """
        params: List[Any] = [user_id] # Only user_id for user_content_interactions

        # Add filters
        where_clauses = []
        if not include_read:
            where_clauses.append("(uci.is_read IS NULL OR uci.is_read = FALSE)")
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        query += " ORDER BY c.published_at DESC LIMIT %s OFFSET %s;"
        params.extend([limit, offset])

        cur.execute(query, tuple(params))

        for row in cur.fetchall():
            # Double-check article still exists (paranoia, but ensures no ghost cards)
            if row[0] is not None:
                digest_items.append(build_article_dict(row))
        # Add an aesthetic instruction for the user (for frontend display)
        digest_items.insert(0, {
            'instruction': "<div style='background: linear-gradient(90deg, #232526 0%, #414345 100%); color: #fff; border-radius: 10px; padding: 18px 24px; margin-bottom: 18px; font-size: 1.1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.12); text-align: center;'>\u2B50 Like the articles you enjoy! The more you like, the smarter your recommendations become. Your personalized tech digest will adapt to your interests. \u2B50</div>"
        })
    except Exception as e:
        print(f"An error occurred while fetching personalized digest for user {user_id}: {e}")
    finally:
        close_db_connection(conn)
    return digest_items

def get_articles_by_user_topics(user_id: int, topics: list, limit: int = 100, offset: int = 0) -> list:
    """
    Fetches articles matching the user's selected topics.

    Args:
        user_id (int): The ID of the logged-in user (used for user interactions, not for filtering sources).
        topics (list): List of topic strings the user is interested in (from user_topics table).
        limit (int): Maximum number of articles to return.
        offset (int): Offset for pagination (used only if batching/pagination is needed).
    """
    if not topics:
        return []
    conn = None
    articles = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Only fetch articles from the last 24 hours (today)
        query = """
            SELECT
                c.id, c.source_id, c.title, c.summary, c.article_url,
                c.published_at, c.topic, c.image_url,
                uci.is_read, uci.is_liked, uci.interaction_at,
                s.source_name AS source_name, s.feed_url AS source_feed_url
            FROM
                content c
            JOIN
                sources s ON c.source_id = s.id
            LEFT JOIN
                user_content_interactions uci ON c.id = uci.content_id AND uci.user_id = %s
            WHERE
                c.topic = ANY(%s)
                AND c.published_at >= (NOW() - INTERVAL '24 hours')
            ORDER BY c.published_at DESC
            LIMIT %s OFFSET %s;
        """
        cur.execute(query, (user_id, topics, limit, offset))
        for row in cur.fetchall():
            articles.append(build_article_dict(row))
    except Exception as e:
        print(f"Error fetching articles by user topics: {e}")
    finally:
        close_db_connection(conn)
    return articles

def get_articles_by_user_topics_extended(user_id: int, topics: list, limit: int = 100, offset: int = 0) -> list:
    """
    Fetches articles matching the user's selected topics with extended time range (7 days).
    This ensures Fast View shows content even if no articles from last 24h.
    """
    if not topics:
        return []
    conn = None
    articles = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Fetch articles from the last 7 days to ensure content availability
        query = """
            SELECT
                c.id, c.source_id, c.title, c.summary, c.article_url,
                c.published_at, c.topic, c.image_url,
                uci.is_read, uci.is_liked, uci.interaction_at,
                s.source_name AS source_name, s.feed_url AS source_feed_url
            FROM
                content c
            JOIN
                sources s ON c.source_id = s.id
            LEFT JOIN
                user_content_interactions uci ON c.id = uci.content_id AND uci.user_id = %s
            WHERE
                c.topic = ANY(%s)
                AND c.published_at >= (NOW() - INTERVAL '7 days')
            ORDER BY c.published_at DESC
            LIMIT %s OFFSET %s;
        """
        cur.execute(query, (user_id, topics, limit, offset))
        for row in cur.fetchall():
            articles.append(build_article_dict(row))
    except Exception as e:
        print(f"Error fetching articles by user topics (extended): {e}")
    finally:
        close_db_connection(conn)
    return articles

def _upsert_user_content_interaction(user_id: int, content_item_id: int,
                                     is_read: Optional[bool] = None,
                                     is_liked: Optional[bool] = None) -> bool:
    """
    Helper function to insert or update a user's interaction with a content item.
    Uses ON CONFLICT (UPSERT) to handle existing records.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Build the query dynamically based on which fields are being updated
        update_fields = []
        update_values = []
        
        if is_read is not None:
            update_fields.append("is_read")
            update_values.append(is_read)
        if is_liked is not None:
            update_fields.append("is_liked")
            update_values.append(is_liked)
        
        if not update_fields:  # No fields to update
            return False
            
        # Always update interaction_at to current time
        update_fields.append("interaction_at")
        update_values.append(datetime.now())

        # Build INSERT columns and values
        insert_columns = ["user_id", "content_id"] + update_fields
        insert_placeholders = ["%s"] * len(insert_columns)

        # Build UPDATE SET clause
        update_set_clauses = []
        for field in update_fields:
            if field == "interaction_at":
                update_set_clauses.append("interaction_at = EXCLUDED.interaction_at")
            else:
                update_set_clauses.append(f"{field} = EXCLUDED.{field}")

        query = f"""
            INSERT INTO user_content_interactions ({', '.join(insert_columns)})
            VALUES ({', '.join(insert_placeholders)})
            ON CONFLICT (user_id, content_id) DO UPDATE SET
                {', '.join(update_set_clauses)}
        """

        params = [user_id, content_item_id] + update_values

        print(f"Executing query: {query}")
        print(f"With params: {params}")

        cur.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        print(f"An error occurred during upserting user content interaction: {e}")
        if conn: 
            conn.rollback()
        return False
    finally:
        close_db_connection(conn)

def mark_content_as_read(user_id: int, content_item_id: int, is_read: bool = True) -> bool:
    """Marks a content item as read/unread for a specific user."""
    return _upsert_user_content_interaction(user_id, content_item_id, is_read=is_read)


def toggle_content_liked(user_id: int, content_item_id: int, is_liked: bool) -> bool:
    """Toggles the liked (and saved) status of a content item for a specific user."""
    print(f"[Like/Unlike] toggle_content_liked called: user_id={user_id}, content_item_id={content_item_id}, is_liked={is_liked}")
    result = _upsert_user_content_interaction(user_id, content_item_id, is_liked=is_liked)
    print(f"[Like/Unlike] toggle_content_liked result: user_id={user_id}, content_item_id={content_item_id}, is_liked={is_liked}, success={result}")
    return result

def update_content_liked(user_id: int, content_item_id: int, is_liked: bool = True) -> bool:
    """Marks a content item as liked (and saved) for a specific user."""
    print(f"[Like/Unlike] update_content_liked called: user_id={user_id}, content_item_id={content_item_id}, is_liked={is_liked}")
    result = _upsert_user_content_interaction(user_id, content_item_id, is_liked=is_liked)
    print(f"[Like/Unlike] update_content_liked result: user_id={user_id}, content_item_id={content_item_id}, is_liked={is_liked}, success={result}")
    return result

def get_articles_by_topics(user_id: int, limit_per_topic: int = 10) -> Dict[str, Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]]:
    """
    Get articles grouped by topics for the main page display.
    Returns a dictionary with 'fast_view' as a list of articles and 'topics' as a dictionary of topic lists.
    """
    # Get user's selected topics from user_topics table
    user_topics = get_user_topics(user_id)

    # Fast View: Show articles based on user's selected topics or general articles
    if user_topics:
        # User has selected topics, show topic-based articles (from last 7 days, not just 24h)
        all_topic_articles = get_articles_by_user_topics_extended(user_id, user_topics, limit=30, offset=0)
        fast_view_articles = [a for a in all_topic_articles if not a.get('is_read', False)]
        
        # If no unread articles from user topics, show some recent unread articles as fallback
        if not fast_view_articles:
            fallback_articles = get_personalized_digest(user_id, limit=15, offset=0, include_read=False)
            fast_view_articles = [a for a in fallback_articles if not a.get('is_read', False)][:10]
    else:
        # User hasn't selected topics yet, show recent unread articles from all topics
        all_recent_articles = get_personalized_digest(user_id, limit=30, offset=0, include_read=False)
        fast_view_articles = [a for a in all_recent_articles if not a.get('is_read', False)]

    # For topic and recommended sections, use smaller limit - reduced from 200 to 80
    all_articles = get_personalized_digest(user_id, limit=80, offset=0, include_read=True)
    # Remove the expensive N+1 query verification - trust the data
    articles = [a for a in all_articles if a.get('id')]

    # Recommended For You: articles matching user topics, both read and unread
    recommended_articles = [a for a in articles if a.get('topic') in user_topics]

    # Group articles by their assigned topics (including those in recommended)
    topic_order = [
        "Recommended For You",
        AI_ML_TOPIC,
        CYBERSECURITY_TOPIC,
        CLOUD_DEVOPS_TOPIC,
        SOFTWARE_DEV_TOPIC,
        DATA_SCIENCE_TOPIC,
        EMERGING_TECH_TOPIC,
        BIG_TECH_TOPIC,
        TECH_CULTURE_TOPIC,
        OPEN_SOURCE_TOPIC
    ]
    topics_dict = {topic: [] for topic in topic_order}
    topics_dict["Recommended For You"] = recommended_articles[:limit_per_topic]

    # Place articles in their topic section as well (allowing overlap with recommended)
    for article in articles:
        topic = article.get('topic', 'Other')
        if topic and topic in topic_order:
            topics_dict[topic].append(article)

    # Limit articles per topic and return all topics (even empty ones)
    for topic in topic_order:
        if len(topics_dict[topic]) > limit_per_topic:
            topics_dict[topic] = topics_dict[topic][:limit_per_topic]

    # Return both fast_view_articles and topics_dict (no mutual exclusion)
    return {"fast_view": fast_view_articles, "topics": topics_dict}

def cleanup_old_articles():
    """
    Smart cleanup that removes old articles only if fresh content is available.
    
    Rules:
    1. Only removes articles older than 24 hours if we have articles from today
    2. If no fresh articles today, keeps yesterday's articles to prevent empty site
    3. Always preserves user-liked articles regardless of age
    4. Ensures minimum content threshold is maintained
    
    Returns:
        dict: Cleanup results with statistics
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if we have fresh articles from today
        cur.execute("""
            SELECT COUNT(*) FROM content 
            WHERE DATE(published_at) = CURRENT_DATE
            AND id NOT IN (
                SELECT DISTINCT content_id 
                FROM user_content_interactions 
                WHERE is_liked = true
            )
        """)
        result_fresh = cur.fetchone()
        fresh_articles_today = result_fresh[0] if result_fresh else 0
        
        # Check total available articles (excluding liked)
        cur.execute("""
            SELECT COUNT(*) FROM content 
            WHERE id NOT IN (
                SELECT DISTINCT content_id 
                FROM user_content_interactions 
                WHERE is_liked = true
            )
        """)
        result_total = cur.fetchone()
        total_unloved_articles = result_total[0] if result_total else 0
        
        # Check articles from yesterday
        cur.execute("""
            SELECT COUNT(*) FROM content 
            WHERE DATE(published_at) = CURRENT_DATE - INTERVAL '1 day'
            AND id NOT IN (
                SELECT DISTINCT content_id 
                FROM user_content_interactions 
                WHERE is_liked = true
            )
        """)
        result_yesterday = cur.fetchone()
        yesterday_articles = result_yesterday[0] if result_yesterday else 0
        
        # Minimum content threshold to maintain
        MIN_ARTICLES = 10
        
        result = {
            'fresh_today': fresh_articles_today,
            'yesterday_count': yesterday_articles,
            'total_available': total_unloved_articles,
            'deleted_count': 0,
            'action_taken': 'none',
            'reason': ''
        }
        
        # Decision logic for cleanup
        if fresh_articles_today >= MIN_ARTICLES:
            # We have enough fresh content, safe to clean old articles
            cur.execute("""
                DELETE FROM content 
                WHERE published_at < NOW() - INTERVAL '24 hours'
                AND id NOT IN (
                    SELECT DISTINCT content_id 
                    FROM user_content_interactions 
                    WHERE is_liked = true
                )
            """)
            deleted_count = cur.rowcount
            conn.commit()
            
            result.update({
                'deleted_count': deleted_count,
                'action_taken': 'cleanup_performed',
                'reason': f'Fresh content available ({fresh_articles_today} new articles)'
            })
            
        elif fresh_articles_today > 0 and total_unloved_articles > 20:
            # Some fresh content, but clean conservatively
            cur.execute("""
                DELETE FROM content 
                WHERE published_at < NOW() - INTERVAL '48 hours'
                AND id NOT IN (
                    SELECT DISTINCT content_id 
                    FROM user_content_interactions 
                    WHERE is_liked = true
                )
            """)
            deleted_count = cur.rowcount
            conn.commit()
            
            result.update({
                'deleted_count': deleted_count,
                'action_taken': 'conservative_cleanup',
                'reason': f'Limited fresh content ({fresh_articles_today} new), extended retention to 48h'
            })
            
        else:
            # No fresh content or insufficient articles, skip cleanup
            result.update({
                'action_taken': 'cleanup_skipped',
                'reason': f'Insufficient fresh content ({fresh_articles_today} new articles). Preserving existing content to prevent empty site.'
            })
        
        # Log the decision
        print("=== Smart Cleanup Results ===")
        print(f"Fresh articles today: {result['fresh_today']}")
        print(f"Yesterday's articles: {result['yesterday_count']}")
        print(f"Total available: {result['total_available']}")
        print(f"Action: {result['action_taken']}")
        print(f"Reason: {result['reason']}")
        print(f"Articles removed: {result['deleted_count']}")
        print("=" * 30)
        
        return result
        
    except Exception as e:
        error_msg = f"Error during smart cleanup: {e}"
        print(error_msg)
        if conn:
            conn.rollback()
        return {
            'error': error_msg,
            'action_taken': 'error',
            'deleted_count': 0
        }
    finally:
        close_db_connection(conn)

def get_general_digest(limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Retrieves a general digest of content items for all users (not personalized).
    Returns the most recent articles from all sources, without user-specific filtering.

    Args:
        limit (int): Maximum number of articles to return.
        offset (int): Offset for pagination.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each representing an article
                               with its content details.
    """
    conn = None
    digest_items = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = """
            SELECT
                c.id, c.source_id, c.title, c.summary, c.article_url,
                c.published_at, c.topic, c.image_url,
                s.source_name AS source_name, s.feed_url AS source_feed_url
            FROM
                content c
            JOIN
                sources s ON c.source_id = s.id
            ORDER BY c.published_at DESC
            LIMIT %s OFFSET %s;
        """
        cur.execute(query, (limit, offset))
        for row in cur.fetchall():
            digest_items.append(build_simple_article_dict(row))
        # Add an instruction for the user (for frontend display)
        digest_items.insert(0, {
            'instruction': "<div style='background: linear-gradient(90deg, #232526 0%, #414345 100%); color: #fff; border-radius: 10px; padding: 18px 24px; margin-bottom: 18px; font-size: 1.1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.12); text-align: center;'>\u2B50 This is the global tech digest. Like articles to save them to your favorites. \u2B50</div>"
        })
    except Exception as e:
        print(f"An error occurred while fetching general digest: {e}")
    finally:
        close_db_connection(conn)
    return digest_items

def get_content_stats():
    """
    Get basic statistics about content for job monitoring.
    Returns info about total articles, recent articles, etc.
    """
    conn = get_db_connection()
    stats = {}
    
    try:
        cur = conn.cursor()
        
        # Get total article count
        cur.execute("SELECT COUNT(*) FROM content")
        stats['total_articles'] = cur.fetchone()[0]
        
        # Get articles from last 24 hours
        cur.execute("""
            SELECT COUNT(*) FROM content 
            WHERE published_at >= NOW() - INTERVAL '24 hours'
        """)
        stats['articles_last_24h'] = cur.fetchone()[0]
        
        # Get articles from last week
        cur.execute("""
            SELECT COUNT(*) FROM content 
            WHERE published_at >= NOW() - INTERVAL '7 days'
        """)
        stats['articles_last_week'] = cur.fetchone()[0]
        
        # Get most recent article timestamp
        cur.execute("""
            SELECT MAX(published_at) FROM content
        """)
        result = cur.fetchone()[0]
        stats['most_recent_article'] = format_datetime(result) if result else None
        
        # Get articles by topic (top 5)
        cur.execute("""
            SELECT topic, COUNT(*) as count 
            FROM content 
            GROUP BY topic 
            ORDER BY count DESC 
            LIMIT 5
        """)
        stats['top_topics'] = [{'topic': row[0], 'count': row[1]} for row in cur.fetchall()]
        
    except Exception as e:
        print(f"Error getting content stats: {e}")
        stats['error'] = str(e)
    finally:
        close_db_connection(conn)
    
    return stats

def cleanup_irrelevant_articles():
    """
    Remove articles that don't meet current filtering standards.
    This ensures that articles that slipped through old filters are cleaned up.
    
    Returns:
        dict: Cleanup results with statistics
    """
    conn = None
    removed_count = 0
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get all articles that need to be re-evaluated
        cur.execute("""
            SELECT id, title, summary, article_url 
            FROM content 
            WHERE id NOT IN (
                SELECT DISTINCT content_id 
                FROM user_content_interactions 
                WHERE interaction_type = 'like'
            )
            ORDER BY published_at DESC
        """)

        articles_to_check = cur.fetchall()
        articles_to_remove = []
        
        print(f"[cleanup_irrelevant_articles] Checking {len(articles_to_check)} articles for relevance...")
        
        # Re-evaluate each article using current filtering standards
        for article_id, title, summary, url in articles_to_check:
            combined_text = f"{title} {summary}".lower()
            
            # Use the same comprehensive rejection logic as in assign_topic function
            reject_keywords = [
                # Non-tech content
                'welding', 'wedding', 'puzzle', 'crossword', 'sudoku', 'chess', 'poker', 'gambling',
                'recipe', 'cooking', 'food', 'restaurant', 'diet', 'nutrition', 'fitness', 'exercise',
                'fashion', 'beauty', 'makeup', 'clothing', 'style', 'shoes', 'jewelry',
                'travel', 'vacation', 'hotel', 'flight', 'tourism', 'destination',
                'sports', 'football', 'basketball', 'soccer', 'baseball', 'tennis', 'golf',
                'movie', 'film', 'cinema', 'actor', 'actress', 'hollywood', 'celebrity',
                'music', 'concert', 'album', 'song', 'band', 'singer', 'artist',
                'real estate', 'property', 'mortgage', 'rent', 'lease', 'housing',
                'insurance', 'loan', 'credit', 'debt', 'mortgage', 'finance',
                'weather', 'climate', 'temperature', 'rain', 'snow', 'storm',
                'health', 'medical', 'doctor', 'hospital', 'medicine', 'drug',
                'politics', 'election', 'vote', 'politician', 'government', 'congress',
                'war', 'military', 'army', 'navy', 'conflict', 'battle',
                'religion', 'church', 'faith', 'prayer', 'bible', 'god',
                
                # Specific non-tech terms that slip through
                'autism', 'disability', 'mental health', 'therapy', 'counseling',
                'shopping', 'sale', 'discount', 'coupon', 'deal', 'bargain',
                'wordle', 'puzzle game', 'word game', 'trivia', 'quiz',
                'investment', 'stock market', 'forex', 'trading', 'broker',
                'car', 'vehicle', 'automotive', 'driving', 'traffic',
                'education', 'school', 'university', 'student', 'teacher',
                'job', 'career', 'employment', 'resume', 'interview',
                'baby', 'child', 'parent', 'family', 'pregnancy',
                'pet', 'dog', 'cat', 'animal', 'veterinary',
                
                # Enhanced promotional and sales content rejection
                'lifetime access', 'limited time', 'exclusive offer', 'get now', 'buy now',
                'save money', 'best deal', 'cheapest', 'lowest price', 'free shipping',
                'order now', 'click here', 'don\'t miss', 'hurry up', 'act fast',
                'special price', 'mega sale', 'clearance', 'liquidation', 'closeout',
                'promotional', 'advertisement', 'sponsored', 'affiliate',
                'subscription', 'membership', 'premium plan', 'upgrade now',
                'trial period', 'money back', 'guarantee', 'refund',
                'documentary collection', 'streaming service', 'entertainment bundle',
                'video library', 'movie collection', 'tv shows', 'series',
                'bundle deal', 'package offer', 'combo deal', 'all-in-one',
                'register now', 'sign up', 'join today', 'enroll',
                'promo code', 'discount code', 'voucher', 'cashback',
                
                # Government and policy content  
                'minister says', 'government announces', 'policy review', 'regulation',
                'eligibility criteria', 'income ceiling', 'housing policy', 'bto',
                'hdb', 'public housing', 'affordable housing', 'social housing',
                'singles scheme', 'married couples', 'family nucleus', 'balloting',
                'flat allocation', 'resale market', 'property cooling measures',
                'stamp duty', 'additional buyer stamp duty', 'absd',
                'citizenship requirement', 'permanent resident', 'foreigner',
                'age requirement', 'household income', 'cpf', 'medisave',
                'parliamentary', 'legislation', 'bill passed', 'amendment',
                'public consultation', 'feedback exercise', 'committee',
                'taskforce', 'working group', 'advisory panel',
                
                # Social and cultural issues
                'racial harmony', 'religious freedom', 'multicultural', 'diversity',
                'social cohesion', 'community integration', 'ethnic group',
                'cultural sensitivity', 'interfaith', 'secular',
                'human rights', 'civil liberties', 'freedom of speech',
                'demonstration', 'protest', 'rally', 'activism',
                'social justice', 'inequality', 'discrimination', 'prejudice',
                'mental wellness', 'suicide prevention', 'counselling services',
                'family violence', 'domestic abuse', 'child protection',
                'eldercare', 'aging population', 'silver generation',
                
                # Entertainment and lifestyle
                'netflix', 'disney+', 'streaming platform', 'subscription service',
                'entertainment package', 'premium content', 'exclusive shows',
                'binge watching', 'tv series', 'drama series', 'reality show',
                'game show', 'talk show', 'variety show', 'comedy',
                'romance', 'thriller', 'horror', 'action movie',
                'documentary film', 'nature documentary', 'history channel',
                'discovery channel', 'national geographic', 'animal planet',
                'lifestyle magazine', 'fashion week', 'celebrity news',
                'gossip', 'scandal', 'paparazzi', 'red carpet',
                'awards ceremony', 'oscar', 'emmy', 'golden globe'
            ]
            
            # Pattern-based rejection (same as assign_topic)
            promotional_patterns = [
                r'get .* for \$\d+',
                r'save \d+%',
                r'only \$\d+',
                r'reg\. \$\d+',
                r'was \$\d+',
                r'now \$\d+',
                r'limited time',
                r'expires .* \d+',
                r'order within',
                r'click to .* now',
                r'don\'t wait',
                r'lifetime .* for',
                r'get .* lifetime',
                r'bundle .* \$\d+'
            ]
            
            policy_patterns = [
                r'minister .* says',
                r'government .* announces',
                r'eligibility .* age .* review',
                r'income ceiling .* raised',
                r'policy .* under review',
                r'criteria .* updated',
                r'scheme .* enhanced',
                r'measures .* implemented',
                r'framework .* revised',
                r'guidelines .* issued'
            ]
            
            # Check for rejection keywords
            reject_score = sum(1 for keyword in reject_keywords if keyword in combined_text)
            
            # Check for promotional patterns
            promotional_matches = sum(1 for pattern in promotional_patterns 
                                    if re.search(pattern, combined_text, re.IGNORECASE))
            
            # Check for policy patterns  
            policy_matches = sum(1 for pattern in policy_patterns 
                               if re.search(pattern, combined_text, re.IGNORECASE))
            
            # Multi-signal rejection (same threshold as assign_topic)
            total_rejection_signals = reject_score + promotional_matches + policy_matches
            
            if total_rejection_signals > 0:
                articles_to_remove.append(article_id)
                print(f"[cleanup_irrelevant_articles] Marking for removal: {title[:50]}... "
                      f"(reject: {reject_score}, promo: {promotional_matches}, policy: {policy_matches})")
        
        # Remove irrelevant articles
        if articles_to_remove:
            # Delete in batches to avoid query length limits
            batch_size = 100
            for i in range(0, len(articles_to_remove), batch_size):
                batch = articles_to_remove[i:i + batch_size]
                placeholders = ','.join(['%s'] * len(batch))
                
                # First remove related interactions
                cur.execute(f"""
                    DELETE FROM user_content_interactions 
                    WHERE content_id IN ({placeholders})
                """, batch)
                
                # Then remove the articles
                cur.execute(f"""
                    DELETE FROM content 
                    WHERE id IN ({placeholders})
                """, batch)
                
                removed_count += len(batch)
        
        conn.commit()
        
        print(f"[cleanup_irrelevant_articles] Removed {removed_count} irrelevant articles")
        
        return {
            "success": True,
            "message": f"Removed {removed_count} irrelevant articles",
            "articles_checked": len(articles_to_check),
            "articles_removed": removed_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error during irrelevant articles cleanup: {e}")
        return {
            "success": False,
            "error": str(e),
            "articles_removed": removed_count,
            "timestamp": datetime.now().isoformat()
        }
    finally:
        close_db_connection(conn)

def get_last_ingestion_time():
    """Return the last global ingestion timestamp (UTC) or None if not set."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT last_ingested_at FROM ingestion_metadata ORDER BY id ASC LIMIT 1;")
        row = cur.fetchone()
        if row:
            return row[0]
        return None
    finally:
        close_db_connection(conn)

def update_last_ingestion_time():
    """Update the last global ingestion timestamp to now (UTC)."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE ingestion_metadata SET last_ingested_at = CURRENT_TIMESTAMP WHERE id = (SELECT id FROM ingestion_metadata ORDER BY id ASC LIMIT 1);")
        conn.commit()
    finally:
        close_db_connection(conn)
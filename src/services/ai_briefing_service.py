"""
AI-powered briefing service using Hugging Face API.
Generates summaries for trending articles using free models.
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.database.connection import get_db_connection, close_db_connection


HF_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HF_TOKEN = os.getenv('HF_TOKEN', '')


def generate_article_summary(title: str, content: str, max_length: int = 130) -> Optional[str]:
    """
    Generate concise summary using Hugging Face BART model.
    
    Args:
        title: Article title.
        content: Article content or description.
        max_length: Maximum tokens in output.
    
    Returns:
        Generated summary or None on failure.
    """
    if not HF_TOKEN:
        return None
    
    try:
        text = f"{title}. {content[:800]}"
        
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {
            "inputs": text,
            "parameters": {
                "max_length": max_length,
                "min_length": 30,
                "do_sample": False
            }
        }
        
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('summary_text', '').strip()
        
        return None
    except Exception as e:
        print(f"HF summary error: {e}")
        return None


def generate_trending_briefing(articles: List[Dict]) -> str:
    """
    Generate simple briefing text from trending articles.
    
    Args:
        articles: List of article dictionaries with title, summary, topic.
    
    Returns:
        Generated briefing text.
    """
    if not articles:
        return "No trending articles today."
    
    topics = {}
    for art in articles[:5]:
        topic = art.get('topic', 'Tech News')
        if topic not in topics:
            topics[topic] = []
        topics[topic].append(art['title'])
    
    briefing_parts = []
    for topic, titles in topics.items():
        count = len(titles)
        briefing_parts.append(f"{count} article{'s' if count > 1 else ''} in {topic}")
    
    return f"Top stories today: {', '.join(briefing_parts)}."


def get_user_top_articles(user_id: int, limit: int = 5) -> List[Dict]:
    """
    Fetch top articles for user based on interests.
    
    Args:
        user_id: User identifier.
        limit: Number of articles to return.
    
    Returns:
        List of article dictionaries.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT c.id, c.title, c.summary, c.topic, c.article_url
            FROM content c
            JOIN user_topics ut ON c.topic = ut.topic_name
            WHERE ut.user_id = %s
            AND c.published_at >= CURRENT_DATE
            AND c.id NOT IN (
                SELECT content_id 
                FROM user_content_interactions 
                WHERE user_id = %s AND is_read = TRUE
            )
            ORDER BY c.published_at DESC
            LIMIT %s
        """, (user_id, user_id, limit))
        
        rows = cur.fetchall()
        return [
            {
                'id': row[0],
                'title': row[1],
                'summary': row[2],
                'topic': row[3],
                'url': row[4]
            }
            for row in rows
        ]
    finally:
        close_db_connection(conn)


def get_trending_articles_with_summaries(hours: int = 24, limit: int = 5) -> List[Dict]:
    """
    Get trending articles and generate AI summaries for them.
    
    Args:
        hours: Timeframe in hours.
        limit: Maximum articles to return.
    
    Returns:
        List of articles with AI-generated summaries.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        interval_str = f"{hours} hours"
        cur.execute("""
            SELECT c.id, c.title, c.summary, c.topic, c.article_url, c.image_url,
                   COUNT(i.user_id) as interaction_count
            FROM content c
            LEFT JOIN user_content_interactions i ON c.id = i.content_id
            WHERE c.published_at >= NOW() - INTERVAL %s
            AND c.topic IS NOT NULL
            GROUP BY c.id
            ORDER BY interaction_count DESC, c.published_at DESC
            LIMIT %s
        """, (interval_str, limit))
        
        rows = cur.fetchall()
        articles = []
        
        for row in rows:
            article = {
                'id': row[0],
                'title': row[1],
                'summary': row[2],
                'topic': row[3],
                'url': row[4],
                'image_url': row[5],
                'interactions': row[6],
                'ai_summary': None
            }
            
            ai_summary = generate_article_summary(row[1], row[2])
            if ai_summary:
                article['ai_summary'] = ai_summary
            
            articles.append(article)
        
        return articles
    finally:
        close_db_connection(conn)




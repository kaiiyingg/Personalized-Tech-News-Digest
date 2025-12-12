"""
Content processing service for trending articles.
Cleans article content and provides data for client-side Chrome AI Summarizer.
"""

import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.database.connection import get_db_connection, close_db_connection


def clean_article_content(content: str) -> str:
    """
    Clean article content by removing URLs, metadata, and formatting issues.
    
    Args:
        content: Raw article content
        
    Returns:
        Cleaned content suitable for display
    """
    if not content:
        return "No summary available."
    
    # Remove URLs (http/https links)
    content = re.sub(r'https?://[^\s,]+', '', content)
    
    # Remove "Comments URL:" and similar metadata
    content = re.sub(r'Comments URL:\s*', '', content)
    content = re.sub(r'URL:\s*', '', content)
    content = re.sub(r'Source:\s*', '', content)
    
    # Remove "See also:" patterns
    content = re.sub(r'See also:\s*', '', content)
    
    # Remove standalone commas and clean up spacing
    content = re.sub(r'\s*,\s*,\s*', ', ', content)
    content = re.sub(r'^,\s*', '', content)
    content = re.sub(r'\s*,$', '', content)
    
    # Clean up multiple spaces and newlines
    content = re.sub(r'\s+', ' ', content)
    content = content.strip()
    
    # If content is too short or just punctuation, return a generic message
    if len(content) < 20 or re.match(r'^[^\w]*$', content):
        return "Article summary not available."
    
    return content





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
    Get trending articles with cleaned content for display.
    
    Args:
        hours: Timeframe in hours.
        limit: Maximum articles to return.
    
    Returns:
        List of articles with cleaned summaries for Chrome AI processing.
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
            # Clean the article summary content
            cleaned_summary = clean_article_content(row[2])
            
            article = {
                'id': row[0],
                'title': row[1],
                'summary': cleaned_summary,
                'topic': row[3],
                'url': row[4],
                'image_url': row[5],
                'interactions': row[6]
            }
            
            articles.append(article)
        
        return articles
    finally:
        close_db_connection(conn)




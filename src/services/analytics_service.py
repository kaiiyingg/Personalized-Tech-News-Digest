"""
Analytics service for trend tracking and statistics.
Provides data aggregation for dashboard visualizations.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from src.database.connection import get_db_connection, close_db_connection


def update_topic_trends(date: Optional[datetime] = None) -> None:
    """
    Aggregate daily topic statistics from content table.
    
    Args:
        date: Target date for aggregation. Defaults to today.
    """
    if date is None:
        date = datetime.now().date()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO topic_trends (date, topic, article_count, view_count, interaction_count)
            SELECT 
                DATE(c.published_at) as date,
                c.topic,
                COUNT(DISTINCT c.id) as article_count,
                COALESCE(SUM(CASE WHEN i.is_read = TRUE THEN 1 ELSE 0 END), 0) as view_count,
                COALESCE(COUNT(i.user_id), 0) as interaction_count
            FROM content c
            LEFT JOIN user_content_interactions i ON c.id = i.content_id
            WHERE DATE(c.published_at) = %s
            GROUP BY DATE(c.published_at), c.topic
            ON CONFLICT (date, topic) 
            DO UPDATE SET 
                article_count = EXCLUDED.article_count,
                view_count = EXCLUDED.view_count,
                interaction_count = EXCLUDED.interaction_count
        """, (date,))
        
        conn.commit()
    finally:
        close_db_connection(conn)


def get_topic_trends(days: int = 7) -> List[Dict]:
    """
    Fetch topic trends for the last N days.
    
    Args:
        days: Number of days to retrieve.
    
    Returns:
        List of trend records with date, topic, and counts.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        interval_str = f"{days} days"
        cur.execute("""
            SELECT date, topic, article_count, view_count, interaction_count
            FROM topic_trends
            WHERE date >= CURRENT_DATE - INTERVAL %s
            ORDER BY date DESC, article_count DESC
        """, (interval_str,))
        
        rows = cur.fetchall()
        return [
            {
                'date': row[0].isoformat(),
                'topic': row[1],
                'article_count': row[2],
                'view_count': row[3],
                'interaction_count': row[4]
            }
            for row in rows
        ]
    finally:
        close_db_connection(conn)


def get_trending_topics(hours: int = 24, limit: int = 5) -> List[Dict]:
    """
    Get most active topics in recent timeframe.
    
    Args:
        hours: Timeframe in hours.
        limit: Maximum topics to return.
    
    Returns:
        List of topics with article counts.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        interval_str = f"{hours} hours"
        cur.execute("""
            SELECT topic, COUNT(*) as article_count
            FROM content
            WHERE published_at >= NOW() - INTERVAL %s
            AND topic IS NOT NULL
            GROUP BY topic
            ORDER BY article_count DESC
            LIMIT %s
        """, (interval_str, limit))
        
        rows = cur.fetchall()
        return [{'topic': row[0], 'count': row[1]} for row in rows]
    finally:
        close_db_connection(conn)


def get_topic_distribution() -> List[Dict]:
    """
    Get distribution of articles across all topics.
    
    Returns:
        List of topics with total article counts.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT topic, COUNT(*) as total
            FROM content
            WHERE topic IS NOT NULL
            GROUP BY topic
            ORDER BY total DESC
        """)
        
        rows = cur.fetchall()
        return [{'topic': row[0], 'total': row[1]} for row in rows]
    finally:
        close_db_connection(conn)


def get_ingestion_stats(days: int = 7) -> Dict:
    """
    Get article ingestion statistics.
    
    Args:
        days: Number of days to analyze.
    
    Returns:
        Dictionary with daily counts and totals.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        interval_str = f"{days} days"
        cur.execute("""
            SELECT 
                DATE(published_at) as date,
                COUNT(*) as count
            FROM content
            WHERE published_at >= CURRENT_DATE - INTERVAL %s
            GROUP BY DATE(published_at)
            ORDER BY date DESC
        """, (interval_str,))
        
        daily = [{'date': row[0].isoformat(), 'count': row[1]} for row in cur.fetchall()]
        
        cur.execute("""
            SELECT COUNT(*) as total
            FROM content
            WHERE published_at >= CURRENT_DATE - INTERVAL %s
        """, (interval_str,))
        
        total = cur.fetchone()[0]
        
        return {'daily': daily, 'total': total}
    finally:
        close_db_connection(conn)


def get_user_reading_stats(user_id: int, days: int = 30) -> Dict:
    """
    Get reading statistics for a specific user.
    
    Args:
        user_id: User identifier.
        days: Time period to analyze.
    
    Returns:
        Dictionary with reading counts and streaks.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        interval_str = f"{days} days"
        cur.execute("""
            SELECT 
                COUNT(DISTINCT content_id) as articles_read,
                COUNT(DISTINCT DATE(interaction_at)) as active_days,
                MAX(interaction_at) as last_read
            FROM user_content_interactions
            WHERE user_id = %s
            AND is_read = TRUE
            AND interaction_at >= CURRENT_DATE - INTERVAL %s
        """, (user_id, interval_str))
        
        row = cur.fetchone()
        
        return {
            'articles_read': row[0] or 0,
            'active_days': row[1] or 0,
            'last_read': row[2].isoformat() if row[2] else None
        }
    finally:
        close_db_connection(conn)

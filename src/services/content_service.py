from src.database.connection import get_db_connection, close_db_connection
from src.models.content import Content
from typing import List, Optional, Dict, Any
from psycopg2 import errors as pg_errors
from datetime import datetime
from transformers import pipeline #type: ignore

# Define topic labels for zero-shot classification
TOPIC_LABELS = [
    "Artificial Intelligence (AI) & Machine Learning (ML)",
    "Cloud Computing & DevOps",
    "Software Development & Web Technologies",
    "Cybersecurity & Privacy",
    "Data Science & Analytics",
    "Emerging Technologies",
    "Big Tech & Industry Trends",
    "Fintech & Crypto",
    "Tech Policy & Regulation",
    "Tech Culture & Work",
    "Open Source",
    "Other"
]

# Load zero-shot classifier once (global)
zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def assign_topic(title: str, summary: str) -> str:
    """
    Assigns a topic to content using zero-shot classification (HuggingFace).
    """
    text = f"{title} {summary}"
    result = zero_shot_classifier(text, TOPIC_LABELS)
    # Return the highest scoring topic
    return result['labels'][0] if result['labels'] else "Other"

def create_content_item(source_id: int, title: str, summary: str,
                        article_url: str, published_at: Optional[datetime], topic: Optional[str] = None) -> Optional[Content]:
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
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Assign topic if not provided
        topic_val = topic if topic else assign_topic(title, summary)
        cur.execute(
            """
            INSERT INTO content (source_id, title, summary, article_url, published_at, topic)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, topic;
            """,
            (source_id, title, summary, article_url, published_at, topic_val)
        )
        row = cur.fetchone()
        if row is None:
            if conn: conn.rollback()
            return None
        content_id, topic_db = row
        conn.commit()
        return Content(content_id, source_id, title, summary, article_url, published_at, topic_db)
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
    Retrieves a personalized digest of content items for a user.
    Includes user-specific interaction status (read, saved, liked, disliked).

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
                c.published_at, c.topic,
                uci.is_read, uci.is_liked, uci.interaction_at,
                s.source_name AS source_name, s.feed_url AS source_feed_url
            FROM
                content c
            JOIN
                sources s ON c.source_id = s.id
            LEFT JOIN
                user_content_interactions uci ON c.id = uci.content_id AND uci.user_id = %s
            WHERE
                s.user_id = %s -- Only show content from sources this user subscribed to
        """
        params: List[Any] = [user_id, user_id] # Parameters for the WHERE clause

        # Add filters
        if not include_read:
            query += " AND (uci.is_read IS NULL OR uci.is_read = FALSE)" # Filter out read articles

        query += " ORDER BY c.published_at DESC LIMIT %s OFFSET %s;"
        params.extend([limit, offset])

        cur.execute(query, tuple(params))

        for row in cur.fetchall():
            # Map row data to a dictionary for easier consumption by Flask/frontend
            digest_items.append({
                'id': row[0],
                'source_id': row[1],
                'title': row[2],
                'summary': row[3],
                'article_url': row[4],
                'published_at': row[5].isoformat() if row[5] and hasattr(row[5], 'isoformat') else str(row[5]) if row[5] else None,
                'topic': row[6],
                'is_read': row[7] if row[7] is not None else False, # Default to False if no interaction record
                'is_liked': row[8] if row[8] is not None else False, # Default to False
                'is_saved': row[8] if row[8] is not None else False, # is_liked means saved
                'interaction_at': row[9].isoformat() if row[9] and hasattr(row[9], 'isoformat') else str(row[9]) if row[9] else None,
                'source_name': row[10],
                'source_feed_url': row[11]
            })
        # Add an aesthetic instruction for the user (for frontend display)
        digest_items.insert(0, {
            'instruction': "<div style='background: linear-gradient(90deg, #232526 0%, #414345 100%); color: #fff; border-radius: 10px; padding: 18px 24px; margin-bottom: 18px; font-size: 1.1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.12); text-align: center;'>\u2B50 Like the articles you enjoy! The more you like, the smarter your recommendations become. Your personalized tech digest will adapt to your interests. \u2B50</div>"
        })
    except Exception as e:
        print(f"An error occurred while fetching personalized digest for user {user_id}: {e}")
    finally:
        close_db_connection(conn)
    return digest_items

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
            
        # Always update interaction_at
        update_fields.append("interaction_at")
        update_values.append(None)  # Will use NOW() in query
        
        # Build INSERT columns and values
        insert_columns = ["user_id", "content_id"] + update_fields
        insert_placeholders = ["%s", "%s"] + ["%s" if field != "interaction_at" else "NOW()" for field in update_fields]
        
        # Build UPDATE SET clause
        update_set_clauses = []
        for field in update_fields:
            if field == "interaction_at":
                update_set_clauses.append("interaction_at = NOW()")
            else:
                update_set_clauses.append(f"{field} = EXCLUDED.{field}")
        
        query = f"""
            INSERT INTO user_content_interactions ({', '.join(insert_columns)})
            VALUES ({', '.join(insert_placeholders)})
            ON CONFLICT (user_id, content_id) DO UPDATE SET
                {', '.join(update_set_clauses)}
        """
        
        # Parameters for the query (excluding interaction_at since it uses NOW())
        params = [user_id, content_item_id] + [v for v in update_values if v is not None]
        
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
    return _upsert_user_content_interaction(user_id, content_item_id, is_liked=is_liked)

def update_content_liked(user_id: int, content_item_id: int, is_liked: bool = True) -> bool:
    """Marks a content item as liked (and saved) for a specific user."""
    return _upsert_user_content_interaction(user_id, content_item_id, is_liked=is_liked)


def get_articles_by_topics(user_id: int, limit_per_topic: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get articles grouped by topics for the main page display.
    Returns a dictionary with topic names as keys and lists of articles as values.
    """
    # Get all articles for the user (including read ones to show with dimmed effect)
    all_articles = get_personalized_digest(user_id, limit=100, offset=0, include_read=True)
    
    # Filter out instruction items
    articles = [a for a in all_articles if a.get('id')]
    
    # Define topic order 
    topic_order = [
        "Recommended For You",
        "Artificial Intelligence (AI) & Machine Learning (ML)",
        "Cybersecurity & Privacy", 
        "Cloud Computing & DevOps",
        "Software Development & Web Technologies",
        "Data Science & Analytics",
        "Emerging Technologies",
        "Big Tech & Industry Trends",
        "Fintech & Crypto",
        "Tech Policy & Regulation",
        "Tech Culture & Work",
        "Open Source",
        "Other"
    ]
    
    # Initialize topics dictionary with empty lists for all topics
    topics_dict = {topic: [] for topic in topic_order}
    
    # Get user's liked topics for recommendations
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get topics the user has liked before
        cur.execute("""
            SELECT c.topic, COUNT(*) as like_count
            FROM content c
            JOIN sources s ON c.source_id = s.id
            JOIN user_content_interactions uci ON c.id = uci.content_id
            WHERE s.user_id = %s AND uci.user_id = %s AND uci.is_liked = TRUE
            GROUP BY c.topic
            ORDER BY like_count DESC
        """, (user_id, user_id))
        
        liked_topics = [row[0] for row in cur.fetchall()]
        
    except Exception as e:
        print(f"Error getting liked topics: {e}")
        liked_topics = []
    finally:
        if conn:
            close_db_connection(conn)
    
    # Create "Recommended For You" section
    recommended_articles = []
    
    # Add recent articles from user's favorite topics
    for topic in liked_topics[:3]:  # Top 3 liked topics
        topic_articles = [a for a in articles if a.get('topic') == topic]
        recommended_articles.extend(topic_articles[:3])  # 3 articles per favorite topic
    
    # Fill remaining with most recent articles if needed
    if len(recommended_articles) < limit_per_topic:
        recent_articles = [a for a in articles if a not in recommended_articles]
        recommended_articles.extend(recent_articles[:limit_per_topic - len(recommended_articles)])
    
    topics_dict["Recommended For You"] = recommended_articles[:limit_per_topic]
    
    # Group remaining articles by their assigned topics
    for article in articles:
        topic = article.get('topic', 'Other')
        # Allow articles to appear in both recommendations and their original topics
        if topic and topic in topic_order:
            topics_dict[topic].append(article)
    
    # Limit articles per topic and return all topics (even empty ones)
    for topic in topic_order:
        if len(topics_dict[topic]) > limit_per_topic:
            topics_dict[topic] = topics_dict[topic][:limit_per_topic]
    
    return topics_dict

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
        print(f"=== Smart Cleanup Results ===")
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
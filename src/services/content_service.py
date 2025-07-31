from src.database.connection import get_db_connection, close_db_connection
from src.models.content import Content
from .user_service import get_user_topics
from typing import List, Optional, Dict, Any
from psycopg2 import errors as pg_errors
from datetime import datetime
from typing import Union

from transformers import pipeline #type: ignore

# Define topic labels for zero-shot classification
TOPIC_LABELS = [
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

# Load zero-shot classifier once (global)
zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

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
            return {
                'id': row[0],
                'source_id': row[1],
                'title': row[2],
                'summary': row[3],
                'article_url': row[4],
                'published_at': row[5].isoformat() if row[5] and hasattr(row[5], 'isoformat') else str(row[5]) if row[5] else None,
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

def assign_topic(title: str, summary: str) -> str:
    """
    Assigns a topic to content using zero-shot classification (HuggingFace).
    """
    text = f"{title} {summary}"
    try:
        result = zero_shot_classifier(text, TOPIC_LABELS)
        # HuggingFace pipeline may return a dict or a list of dicts
        labels = []
        if isinstance(result, dict):
            labels = result.get('labels', [])
        elif isinstance(result, list) and result and isinstance(result[0], dict):
            labels = result[0].get('labels', [])
        if labels and isinstance(labels[0], str):
            return labels[0]
        else:
            return "Other"
    except Exception:
        return "Other"

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
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Assign topic if not provided
        topic_val = topic if topic else assign_topic(title, summary)
        cur.execute(
            """
            INSERT INTO content (source_id, title, summary, article_url, published_at, topic, image_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, topic, image_url;
            """,
            (source_id, title, summary, article_url, published_at, topic_val, image_url)
        )
        row = cur.fetchone()
        if row is None:
            if conn: conn.rollback()
            return None
        content_id, topic_db, image_url_db = row
        conn.commit()
        return Content(content_id, source_id, title, summary, article_url, published_at, topic_db, image_url_db)
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
                digest_items.append({
                    'id': row[0],
                    'source_id': row[1],
                    'title': row[2],
                    'summary': row[3],
                    'article_url': row[4],
                    'published_at': row[5].isoformat() if row[5] and hasattr(row[5], 'isoformat') else str(row[5]) if row[5] else None,
                    'topic': row[6],
                    'image_url': row[7],
                    'is_read': row[8] if row[8] is not None else False,
                    'is_liked': row[9] if row[9] is not None else False,
                    'is_saved': row[9] if row[9] is not None else False,
                    'interaction_at': row[10].isoformat() if row[10] and hasattr(row[10], 'isoformat') else str(row[10]) if row[10] else None,
                    'source_name': row[11],
                    'source_feed_url': row[12]
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
            topic_display = row[6]
            if topic_display == "Artificial Intelligence (AI) & Machine Learning (ML)":
                topic_display = "AI & ML"
            articles.append({
                'id': row[0],
                'source_id': row[1],
                'title': row[2],
                'summary': row[3],
                'article_url': row[4],
                'published_at': row[5].isoformat() if row[5] and hasattr(row[5], 'isoformat') else str(row[5]) if row[5] else None,
                'topic': topic_display,
                'image_url': row[7],
                'is_read': row[8] if row[8] is not None else False,
                'is_liked': row[9] if row[9] is not None else False,
                'is_saved': row[9] if row[9] is not None else False,
                'interaction_at': row[10].isoformat() if row[10] and hasattr(row[10], 'isoformat') else str(row[10]) if row[10] else None,
                'source_name': row[11],
                'source_feed_url': row[12]
            })
    except Exception as e:
        print(f"Error fetching articles by user topics: {e}")
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
    return _upsert_user_content_interaction(user_id, content_item_id, is_liked=is_liked)

def update_content_liked(user_id: int, content_item_id: int, is_liked: bool = True) -> bool:
    """Marks a content item as liked (and saved) for a specific user."""
    return _upsert_user_content_interaction(user_id, content_item_id, is_liked=is_liked)

def get_articles_by_topics(user_id: int, limit_per_topic: int = 10) -> Dict[str, Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]]:
    """
    Get articles grouped by topics for the main page display.
    Returns a dictionary with 'fast_view' as a list of articles and 'topics' as a dictionary of topic lists.
    """
    # Get user's selected topics from user_topics table
    user_topics = get_user_topics(user_id)

    # Fast View: unread articles from user topics (last 24h, unread only)
    all_topic_articles = get_articles_by_user_topics(user_id, user_topics, limit=200, offset=0)
    fast_view_articles = [a for a in all_topic_articles if not a.get('is_read', False)]

    # For topic and recommended sections, use all articles (read and unread) from personalized digest
    all_articles = get_personalized_digest(user_id, limit=200, offset=0, include_read=True)
    articles = []
    for a in all_articles:
        if a.get('id') and get_article_by_id(a['id']) is not None:
            articles.append(a)

    # Recommended For You: articles matching user topics, both read and unread
    recommended_articles = [a for a in articles if a.get('topic') in user_topics]

    # Group articles by their assigned topics (including those in recommended)
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
            digest_items.append({
                'id': row[0],
                'source_id': row[1],
                'title': row[2],
                'summary': row[3],
                'article_url': row[4],
                'published_at': row[5].isoformat() if row[5] and hasattr(row[5], 'isoformat') else str(row[5]) if row[5] else None,
                'topic': row[6],
                'image_url': row[7],
                'source_name': row[8],
                'source_feed_url': row[9]
            })
        # Add an instruction for the user (for frontend display)
        digest_items.insert(0, {
            'instruction': "<div style='background: linear-gradient(90deg, #232526 0%, #414345 100%); color: #fff; border-radius: 10px; padding: 18px 24px; margin-bottom: 18px; font-size: 1.1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.12); text-align: center;'>\u2B50 This is the global tech digest. Like articles to save them to your favorites. \u2B50</div>"
        })
    except Exception as e:
        print(f"An error occurred while fetching general digest: {e}")
    finally:
        close_db_connection(conn)
    return digest_items
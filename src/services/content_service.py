from src.database.connection import get_db_connection, close_db_connection
from src.models.content import Content
from typing import List, Optional, Dict, Any
from psycopg2 import errors as pg_errors
from datetime import datetime

def assign_topic(title: str, summary: str) -> str:
    """
    Assigns a topic to content based on keywords in the title or summary.
    """
    text = f"{title} {summary}".lower()
    if any(word in text for word in ["apple", "google", "microsoft", "amazon", "meta"]):
        return "Big Tech & Industry Trends"
    if any(word in text for word in ["launch", "update", "release", "feature"]):
        return "Product Launches & Updates"
    if any(word in text for word in ["startup", "funding", "acquisition", "vc", "unicorn"]):
        return "Startups & Funding"
    if any(word in text for word in ["ai", "machine learning", "deep learning", "model", "gpt", "llm"]):
        return "AI & Machine Learning"
    if any(word in text for word in ["security", "cyber", "breach", "privacy", "threat"]):
        return "Cybersecurity & Privacy"
    if any(word in text for word in ["fintech", "crypto", "blockchain", "defi", "bitcoin", "ethereum"]):
        return "FinTech & Crypto"
    if any(word in text for word in ["web", "javascript", "react", "vue", "angular", "dev tool", "library", "framework"]):
        return "Web Development & Dev Tools"
    if any(word in text for word in ["cloud", "aws", "azure", "gcp", "devops", "infrastructure", "ci/cd"]):
        return "Cloud, DevOps & Infrastructure"
    if any(word in text for word in ["policy", "regulation", "antitrust", "law", "ban", "government"]):
        return "Policy, Regulation & Antitrust"
    if any(word in text for word in ["culture", "work", "layoff", "remote", "productivity", "diversity"]):
        return "Tech Culture & Work"
    return "Other"

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
                             include_read: bool = False, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves a personalized digest of content items for a user.
    Includes user-specific interaction status (read, saved, liked, disliked).

    Args:
        user_id (int): The ID of the logged-in user.
        limit (int): Maximum number of articles to return.
        offset (int): Offset for pagination.
        include_read (bool): If True, includes articles already marked as read.
        search_query (Optional[str]): A keyword to search in title/summary.

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
        if search_query:
            query += " AND (c.title ILIKE %s OR c.summary ILIKE %s)" # Case-insensitive search
            params.extend([f"%{search_query}%", f"%{search_query}%"])

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

        # Build SET clause dynamically for UPDATE part of UPSERT
        set_clauses = []
        params = []

        if is_read is not None:
            set_clauses.append("is_read = %s")
            params.append(is_read)
        if is_liked is not None:
            set_clauses.append("is_liked = %s")
            params.append(is_liked)

        if not set_clauses: # No fields to update
            return False

        # Add interaction_at update
        set_clauses.append("interaction_at = NOW()")

        query = f"""
            INSERT INTO user_content_interactions (user_id, content_item_id, {', '.join([c.split('=')[0].strip() for c in set_clauses])})
            VALUES (%s, %s, {', '.join(['%s'] * len(set_clauses))})
            ON CONFLICT (user_id, content_item_id) DO UPDATE SET
                {', '.join([f"{c.split('=')[0].strip()} = EXCLUDED.{c.split('=')[0].strip()}" for c in set_clauses])};
        """
        # Parameters for INSERT part: user_id, content_item_id, then the values for set_clauses
        insert_params = [user_id, content_item_id] + params

        cur.execute(query, tuple(insert_params))
        conn.commit()
        return True
    except Exception as e:
        print(f"An error occurred during upserting user content interaction: {e}")
        if conn: conn.rollback()
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
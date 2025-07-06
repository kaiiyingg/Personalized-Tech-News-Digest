from src.database.connection import get_db_connection, close_db_connection
from src.models.content import Content
from src.models.user_content_interaction import UserContentInteraction # NEW import
from typing import List, Optional, Dict, Any
from psycopg2 import errors as pg_errors
from datetime import datetime

def create_content_item(source_id: int, original_id: str, title: str, summary: str,
                        article_url: str, published_at: Optional[datetime]) -> Optional[Content]:
    """
    Creates a new content item in the database. Used by the ingestion pipeline.

    Args:
        source_id (int): The ID of the source from which this content was fetched.
        original_id (str): A unique ID for the content from its original source (for deduplication).
        title (str): The title of the content.
        summary (str): A summary or snippet of the content.
        article_url (str): The URL to the full article.
        published_at (Optional[datetime]): The original publication date/time.

    Returns:
        Optional[Content]: The created Content object if successful, None if original_id/url already exists.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO content_items (source_id, original_id, title, summary, article_url, published_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, ingested_at, updated_at;
            """,
            (source_id, original_id, title, summary, article_url, published_at)
        )
        content_id, ingested_at, updated_at = cur.fetchone()
        conn.commit()
        return Content(content_id, source_id, title, summary, article_url, published_at, ingested_at, updated_at)
    except pg_errors.UniqueViolation as e:
        print(f"Error: Content item with original_id '{original_id}' or URL '{article_url}' already exists. {e}")
        if conn: conn.rollback()
        return None
    except Exception as e:
        print(f"An error occurred during content item creation: {e}")
        if conn: conn.rollback()
        return None
    finally:
        close_db_connection(conn)

def get_personalized_digest(user_id: int, limit: int = 20, offset: int = 0,
                             include_read: bool = False, search_query: Optional[str] = None,
                             interest_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """
    Retrieves a personalized digest of content items for a user.
    Includes user-specific interaction status (read, saved, feedback).

    Args:
        user_id (int): The ID of the logged-in user.
        limit (int): Maximum number of articles to return.
        offset (int): Offset for pagination.
        include_read (bool): If True, includes articles already marked as read.
        search_query (Optional[str]): A keyword to search in title/summary.
        interest_ids (Optional[List[int]]): List of interest IDs to filter by (future feature).

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each representing an article
                               with its content details and user interaction status.
    """
    conn = None
    digest_items = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Base query: Join content_items with user_content_interactions
        # LEFT JOIN ensures all content items are included, even if no interaction yet
        query = """
            SELECT
                ci.id, ci.source_id, ci.title, ci.summary, ci.article_url,
                ci.published_at, ci.ingested_at, ci.updated_at,
                uci.is_read, uci.is_saved, uci.feedback_rating, uci.interaction_at,
                s.name AS source_name, s.feed_url AS source_feed_url
            FROM
                content_items ci
            JOIN
                sources s ON ci.source_id = s.id
            LEFT JOIN
                user_content_interactions uci ON ci.id = uci.content_item_id AND uci.user_id = %s
            WHERE
                s.user_id = %s -- Only show content from sources this user subscribed to
        """
        params = [user_id, user_id] # Parameters for the WHERE clause

        # Add filters
        if not include_read:
            query += " AND (uci.is_read IS NULL OR uci.is_read = FALSE)" # Filter out read articles
        if search_query:
            query += " AND (ci.title ILIKE %s OR ci.summary ILIKE %s)" # Case-insensitive search
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        # TODO: Add interest_ids filtering logic here later (requires interests table and join)

        query += " ORDER BY ci.published_at DESC, ci.ingested_at DESC LIMIT %s OFFSET %s;"
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
                'published_at': row[5].isoformat() if row[5] else None,
                'ingested_at': row[6].isoformat(),
                'updated_at': row[7].isoformat() if row[7] else None,
                'is_read': row[8] if row[8] is not None else False, # Default to False if no interaction record
                'is_saved': row[9] if row[9] is not None else False, # Default to False
                'feedback_rating': row[10] if row[10] is not None else 0, # Default to 0
                'interaction_at': row[11].isoformat() if row[11] else None,
                'source_name': row[12],
                'source_feed_url': row[13]
            })
    except Exception as e:
        print(f"An error occurred while fetching personalized digest for user {user_id}: {e}")
    finally:
        close_db_connection(conn)
    return digest_items

def _upsert_user_content_interaction(user_id: int, content_item_id: int,
                                     is_read: Optional[bool] = None,
                                     is_saved: Optional[bool] = None,
                                     feedback_rating: Optional[int] = None) -> bool:
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
        if is_saved is not None:
            set_clauses.append("is_saved = %s")
            params.append(is_saved)
        if feedback_rating is not None:
            set_clauses.append("feedback_rating = %s")
            params.append(feedback_rating)

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

def toggle_content_saved(user_id: int, content_item_id: int, is_saved: bool) -> bool:
    """Toggles the saved status of a content item for a specific user."""
    return _upsert_user_content_interaction(user_id, content_item_id, is_saved=is_saved)

def update_content_feedback(user_id: int, content_item_id: int, feedback_rating: int) -> bool:
    """Updates the feedback rating for a content item for a specific user."""
    # Ensure feedback_rating is -1, 0, or 1
    if feedback_rating not in [-1, 0, 1]:
        print("Invalid feedback_rating. Must be -1, 0, or 1.")
        return False
    return _upsert_user_content_interaction(user_id, content_item_id, feedback_rating=feedback_rating)
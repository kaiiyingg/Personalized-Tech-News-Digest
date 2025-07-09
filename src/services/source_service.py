from src.database.connection import get_db_connection, close_db_connection
from src.models.source import Source
from typing import List, Optional
from psycopg2 import errors as pg_errors

def create_source(user_id: int, name: str, feed_url: str, type: str) -> Optional[Source]:
    """
    Creates a new content source in the database.

    Args:
        user_id (int): The ID of the user adding the source.
        name (str): The name of the source.
        feed_url (str): The URL of the content feed.
        type (str): The type of the source (e.g., 'rss', 'subreddit').

    Returns:
        Optional[Source]: The created Source object if successful, None otherwise.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sources (user_id, name, feed_url, type) VALUES (%s, %s, %s, %s) RETURNING id, last_fetched_at, created_at, updated_at;",
            (user_id, name, feed_url, type)
        )
        result = cur.fetchone()
        if result:
            source_id, last_fetched_at, created_at, updated_at = result
            conn.commit()
            return Source(source_id, user_id, name, feed_url, type, last_fetched_at, created_at, updated_at)
        else:
            print("No row returned from INSERT.")
            conn.rollback()
            return None
    except pg_errors.UniqueViolation as e:
        print(f"Error: Source URL already exists for this user or globally. {e}")
        if conn: conn.rollback()
        return None
    except Exception as e:
        print(f"An error occurred during source creation: {e}")
        if conn: conn.rollback()
        return None
    finally:
        close_db_connection(conn)

def get_sources_by_user(user_id: int) -> List[Source]:
    """
    Retrieves all sources for a specific user.

    Args:
        user_id (int): The ID of the user.

    Returns:
        List[Source]: A list of Source objects.
    """
    conn = None
    sources = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, user_id, name, feed_url, type, last_fetched_at, created_at, updated_at FROM sources WHERE user_id = %s ORDER BY name;",
            (user_id,)
        )
        for row in cur.fetchall():
            sources.append(Source(*row))
    except Exception as e:
        print(f"An error occurred while fetching sources for user {user_id}: {e}")
    finally:
        close_db_connection(conn)
    return sources

def get_source_by_id(source_id: int, user_id: int) -> Optional[Source]:
    """
    Retrieves a specific source by its ID, ensuring it belongs to the given user.

    Args:
        source_id (int): The ID of the source.
        user_id (int): The ID of the user who owns the source.

    Returns:
        Optional[Source]: The Source object if found and owned by the user, None otherwise.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, user_id, name, feed_url, type, last_fetched_at, created_at, updated_at FROM sources WHERE id = %s AND user_id = %s;",
            (source_id, user_id)
        )
        source_data = cur.fetchone()
        if source_data:
            return Source(*source_data)
        return None
    except Exception as e:
        print(f"An error occurred while fetching source {source_id} for user {user_id}: {e}")
        return None
    finally:
        close_db_connection(conn)

def update_source(source_id: int, user_id: int, name: Optional[str] = None, feed_url: Optional[str] = None, type: Optional[str] = None) -> bool:
    """
    Updates details of an existing source. Only updates fields that are not None.

    Args:
        source_id (int): The ID of the source to update.
        user_id (int): The ID of the user who owns the source (for authorization).
        name (Optional[str]): New name for the source.
        feed_url (Optional[str]): New feed URL for the source.
        type (Optional[str]): New type for the source.

    Returns:
        bool: True if the source was updated, False otherwise.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        set_clauses = []
        params = []

        if name is not None:
            set_clauses.append("name = %s")
            params.append(name)
        if feed_url is not None:
            set_clauses.append("feed_url = %s")
            params.append(feed_url)
        if type is not None:
            set_clauses.append("type = %s")
            params.append(type)

        if not set_clauses:
            return False # No fields to update

        params.append(source_id)
        params.append(user_id) # For WHERE clause

        query = f"UPDATE sources SET {', '.join(set_clauses)}, updated_at = NOW() WHERE id = %s AND user_id = %s;"
        cur.execute(query, tuple(params))
        conn.commit()
        return cur.rowcount > 0 # Returns True if a row was updated
    except Exception as e:
        print(f"An error occurred while updating source {source_id}: {e}")
        if conn: conn.rollback()
        return False
    finally:
        close_db_connection(conn)

def delete_source(source_id: int, user_id: int) -> bool:
    """
    Deletes a source from the database, ensuring it belongs to the given user.

    Args:
        source_id (int): The ID of the source to delete.
        user_id (int): The ID of the user who owns the source.

    Returns:
        bool: True if the source was deleted, False otherwise.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM sources WHERE id = %s AND user_id = %s;", (source_id, user_id))
        conn.commit()
        return cur.rowcount > 0 # Returns True if a row was deleted
    except Exception as e:
        print(f"An error occurred while deleting source {source_id}: {e}")
        if conn: conn.rollback()
        return False
    finally:
        close_db_connection(conn)
"""
Source Service Module

Manages RSS news sources for the tech news digest:
- Source creation and retrieval
- Feed URL validation and management
- Source metadata tracking (last fetch times, creation dates)
- Database operations for source management

Supports multiple tech news sources with automatic deduplication.
"""

from src.database.connection import get_db_connection, close_db_connection
from src.models.source import Source
from typing import List, Optional
from psycopg2 import errors as pg_errors

# ===== SOURCE MANAGEMENT FUNCTIONS =====

def create_source(name: str, feed_url: str) -> Optional[Source]:
    """
    Create a new RSS source or return existing one if URL already exists.
    
    Args:
        name (str): Display name for the RSS source
        feed_url (str): RSS feed URL (must be unique)
        
    Returns:
        Optional[Source]: Created or existing Source object, None on error
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, last_fetched_at, created_at, updated_at FROM sources WHERE feed_url = %s;",
            (feed_url,)
        )
        existing = cur.fetchone()
        if existing:
            # Source already exists, return existing Source
            source_id, last_fetched_at, created_at, updated_at = existing
            return Source(source_id, name, feed_url, last_fetched_at, created_at, updated_at)
        cur.execute(
            "INSERT INTO sources (source_name, feed_url) VALUES (%s, %s) RETURNING id, last_fetched_at, created_at, updated_at;",
            (name, feed_url)
        )
        row = cur.fetchone()
        if row is None:
            if conn: conn.rollback()
            return None
        source_id, last_fetched_at, created_at, updated_at = row
        conn.commit()
        return Source(source_id, name, feed_url, last_fetched_at, created_at, updated_at)
    except Exception as e:
        print(f"An error occurred during source creation: {e}")
        if conn: conn.rollback()
        return None
    finally:
        close_db_connection(conn)

def get_all_sources() -> List[Source]:
    """
    Retrieve all RSS sources from the database.
    
    Returns:
        List[Source]: List of all Source objects, sorted by name
    """
    conn = None
    sources = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, source_name, feed_url, last_fetched_at, created_at, updated_at FROM sources ORDER BY source_name;"
        )
        for row in cur.fetchall():
            sources.append(Source(row[0], row[1], row[2], row[3], row[4], row[5]))
    except Exception as e:
        print(f"An error occurred while fetching sources: {e}")
    finally:
        close_db_connection(conn)
    return sources

def get_source_by_id(source_id: int) -> Optional[Source]:
    """
    Retrieve a specific RSS source by its unique ID.
    
    Args:
        source_id (int): The unique identifier of the source
        
    Returns:
        Optional[Source]: Source object if found, None otherwise
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, source_name, feed_url, last_fetched_at, created_at, updated_at FROM sources WHERE id = %s;",
            (source_id,)
        )
        row = cur.fetchone()
        if row:
            return Source(row[0], row[1], row[2], row[3], row[4], row[5])
        return None
    except Exception as e:
        print(f"An error occurred while fetching source {source_id}: {e}")
        return None
    finally:
        close_db_connection(conn)

def update_source(source_id: int, name: Optional[str] = None, feed_url: Optional[str] = None) -> bool:
    """
    Updates an existing global RSS source.
    Args:
        source_id (int): The ID of the source to update.
        name (Optional[str]): The new name for the source (optional).
        feed_url (Optional[str]): The new feed URL for the source (optional).
    Returns:
        bool: True if update was successful, False otherwise.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        set_clauses = []
        params = []
        if name:
            set_clauses.append("source_name = %s")
            params.append(name)
        if feed_url:
            set_clauses.append("feed_url = %s")
            params.append(feed_url)
        if not set_clauses:
            return False
        params.append(source_id) # For WHERE clause
        query = f"UPDATE sources SET {', '.join(set_clauses)}, updated_at = NOW() WHERE id = %s;"
        cur.execute(query, params)
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        print(f"An error occurred while updating source {source_id}: {e}")
        if conn: conn.rollback()
        return False
    finally:
        close_db_connection(conn)

def delete_source(source_id: int) -> bool:
    """
    Deletes a global RSS source.
    Args:
        source_id (int): The ID of the source to delete.
    Returns:
        bool: True if deletion was successful, False otherwise.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM sources WHERE id = %s;", (source_id,))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        print(f"An error occurred while deleting source {source_id}: {e}")
        if conn: conn.rollback()
        return False
    finally:
        close_db_connection(conn)
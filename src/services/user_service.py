"""
User Service Module

This module provides comprehensive user management functionality including:
- User authentication and authorization
- User profile management (username, email, password updates)
- TOTP (Two-Factor Authentication) support
- User topic preferences management

Dependencies:
    - Flask-Bcrypt for secure password hashing
    - PyOTP for TOTP secret generation
    - PostgreSQL database connection
"""

from typing import Optional, List
from src.models.user import User
from flask_bcrypt import Bcrypt
from src.database.connection import get_db_connection, close_db_connection
from psycopg2 import errors as pg_errors
import pyotp

bcrypt = Bcrypt()

# ===== USER RETRIEVAL FUNCTIONS =====

def find_user_by_id(user_id: int) -> Optional[User]:
    """
    Retrieve a user by their unique user ID.
    
    Args:
        user_id (int): The unique identifier for the user
        
    Returns:
        Optional[User]: User object if found, None if not found or error occurs
        
    Example:
        >>> user = find_user_by_id(123)
        >>> if user:
        >>>     print(f"Found user: {user.username}")
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, email, password_hash, totp_secret, created_at, updated_at FROM users WHERE id = %s;",
            (user_id,)
        )
        user_data = cur.fetchone()
        if user_data:
            return User(*user_data)
        return None
    except Exception as e:
        print(f"An error occurred while finding user by id: {e}")
        return None
    finally:
        close_db_connection(conn)

def find_user_by_username(username: str) -> Optional[User]:
    """
    Retrieve a user by their username (used for login).
    
    Args:
        username (str): The username to search for
        
    Returns:
        Optional[User]: User object if found, None if not found or error occurs
        
    Example:
        >>> user = find_user_by_username("john_doe")
        >>> if user:
        >>>     print(f"User ID: {user.id}")
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, email, password_hash, totp_secret, created_at, updated_at FROM users WHERE username = %s;",
            (username,)
        )
        user_data = cur.fetchone()
        if user_data:
            return User(*user_data)
        return None
    except Exception as e:
        print(f"An error occurred while finding user by username: {e}")
        return None
    finally:
        close_db_connection(conn)

def find_user_by_email(email: str) -> Optional[User]:
    """
    Retrieve a user by their email address (used for password reset).
    
    Args:
        email (str): The email address to search for
        
    Returns:
        Optional[User]: User object if found, None if not found or error occurs
        
    Example:
        >>> user = find_user_by_email("john@example.com")
        >>> if user:
        >>>     print(f"Found user: {user.username}")
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, email, password_hash, totp_secret, created_at, updated_at FROM users WHERE email = %s;",
            (email,)
        )
        user_data = cur.fetchone()
        if user_data:
            return User(*user_data)
        return None
    except Exception as e:
        print(f"An error occurred while finding user by email: {e}")
        return None
    finally:
        close_db_connection(conn)

# ===== USER CREATION AND AUTHENTICATION =====
# ===== USER CREATION AND AUTHENTICATION =====

def create_user(username: str, password: str, email: str) -> Optional[User]:
    """
    Create a new user account with secure password hashing and TOTP setup.
    
    Args:
        username (str): Unique username for the account
        password (str): Plain text password (will be hashed securely)
        email (str): User's email address (must be unique)
        
    Returns:
        Optional[User]: Created User object if successful, None if creation fails
        
    Raises:
        - UniqueViolation: If username or email already exists
        - Exception: For other database or validation errors
        
    Example:
        >>> new_user = create_user("john_doe", "secure123", "john@example.com")
        >>> if new_user:
        >>>     print(f"User created with ID: {new_user.id}")
        >>> else:
        >>>     print("User creation failed")
    """
    conn = None
    try:
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        totp_secret = pyotp.random_base32()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password_hash, totp_secret) VALUES (%s, %s, %s, %s) RETURNING id, username, email, password_hash, totp_secret, created_at, updated_at;",
            (username, email, hashed_password, totp_secret)
        )
        result = cur.fetchone()
        if result is None:
            if conn:
                conn.rollback()
            print("Error: Failed to insert user or retrieve user data.")
            return None
        user = User(*result)
        conn.commit()
        return user
    except pg_errors.UniqueViolation as e:
        print(f"Error: Username or email already exists. {e}")
        if conn:
            conn.rollback()
        return None
    except Exception as e:
        print(f"An error occurred during user creation: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        close_db_connection(conn)

def check_password(user_obj: User, password: str) -> bool:
    """
    Verify if a plain text password matches the user's stored hashed password.
    
    Args:
        user_obj (User): The User object containing the hashed password
        password (str): Plain text password to verify
        
    Returns:
        bool: True if password matches, False otherwise
        
    Security:
        Uses bcrypt for secure password comparison with timing attack protection
        
    Example:
        >>> user = find_user_by_username("john_doe")
        >>> if user and check_password(user, "user_input_password"):
        >>>     print("Login successful")
        >>> else:
        >>>     print("Invalid credentials")
    """
    # Bcrypt handles the hashing and comparison securely
    return bcrypt.check_password_hash(user_obj.password_hash, password)

# ===== USER PROFILE UPDATE FUNCTIONS =====
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET username = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s;",
            (new_username, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"An error occurred while updating username: {e}")
        if conn:
            conn.rollback()
        return False
# ===== USER PROFILE UPDATE FUNCTIONS =====

def update_user_username(user_id: int, new_username: str) -> bool:
    """
    Update a user's username.
    
    Args:
        user_id (int): The ID of the user to update
        new_username (str): The new username to set
        
    Returns:
        bool: True if update successful, False if failed
        
    Note:
        - Automatically updates the updated_at timestamp
        - Performs database rollback on error
        
    Example:
        >>> success = update_user_username(123, "new_username")
        >>> if success:
        >>>     print("Username updated successfully")
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET username = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s;",
            (new_username, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"An error occurred while updating username: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        close_db_connection(conn)

def update_user_email(user_id: int, new_email: str) -> bool:
    """
    Update a user's email address.
    
    Args:
        user_id (int): The ID of the user to update
        new_email (str): The new email address to set
        
    Returns:
        bool: True if update successful, False if failed
        
    Note:
        - Automatically updates the updated_at timestamp
        - Performs database rollback on error
        - Email must be unique across all users
        
    Example:
        >>> success = update_user_email(123, "newemail@example.com")
        >>> if success:
        >>>     print("Email updated successfully")
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET email = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s;",
            (new_email, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"An error occurred while updating email: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        close_db_connection(conn)

def update_user_password(user_id: int, new_password: str) -> bool:
    """
    Update a user's password with secure hashing.
    
    Args:
        user_id (int): The ID of the user to update
        new_password (str): The new plain text password (will be hashed)
        
    Returns:
        bool: True if update successful, False if failed
        
    Security:
        - Password is securely hashed using bcrypt before storage
        - Automatically updates the updated_at timestamp
        - Performs database rollback on error
        
    Example:
        >>> success = update_user_password(123, "new_secure_password")
        >>> if success:
        >>>     print("Password updated successfully")
    """
    conn = None
    try:
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s;",
            (hashed_password, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"An error occurred while updating user password: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        close_db_connection(conn)

# ===== USER TOPIC PREFERENCES MANAGEMENT =====
# ===== USER TOPIC PREFERENCES MANAGEMENT =====

def get_user_topics(user_id: int) -> List[str]:
    """
    Retrieve all topics selected by a specific user.
    
    Args:
        user_id (int): The user's unique identifier
        
    Returns:
        List[str]: List of topic names, empty list if none found or error occurs
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT topic FROM user_topics WHERE user_id = %s;", (user_id,))
        rows = cur.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"Error fetching user topics: {e}")
        return []
    finally:
        close_db_connection(conn)

def set_user_topics(user_id: int, topics: List[str]) -> None:
    """
    Replace all user's topic preferences with a new list.
    
    Args:
        user_id (int): The user's unique identifier
        topics (List[str]): New list of topic names to set
        
    Note:
        Removes all existing topics before inserting new ones (atomic operation)
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Remove old topics
        cur.execute("DELETE FROM user_topics WHERE user_id = %s;", (user_id,))
        # Insert new topics
        for topic in topics:
            cur.execute("INSERT INTO user_topics (user_id, topic) VALUES (%s, %s);", (user_id, topic))
        conn.commit()
    except Exception as e:
        print(f"Error setting user topics: {e}")
        if conn:
            conn.rollback()
    finally:
        close_db_connection(conn)
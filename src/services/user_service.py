"""
User Service Module

This module provides comprehensive user management functionality including:
- User authentication and authorization
- User profile management (username, email, password updates)
- User topic preferences management
- Password reset via email verification codes

Dependencies:
    - Flask-Bcrypt for secure password hashing
    - PostgreSQL database connection
    - SendGrid for email delivery
"""

from typing import Optional, List
from src.models.user import User
from flask_bcrypt import Bcrypt
from src.database.connection import get_db_connection, close_db_connection
from psycopg2 import errors as pg_errors
import random
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SendGrid integration
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

bcrypt = Bcrypt()

# ===== USER RETRIEVAL FUNCTIONS =====

def find_user_by_id(user_id: int) -> Optional[User]:
    """
    Retrieve a user by their unique user ID.
    
    Args:
        user_id (int): The unique identifier for the user
        
    Returns:
        Optional[User]: User object if found, None if not found or error occurs
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, email, password_hash, created_at, updated_at FROM users WHERE id = %s;",
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
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, email, password_hash, created_at, updated_at FROM users WHERE username = %s;",
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
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, email, password_hash, created_at, updated_at FROM users WHERE email = %s;",
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

def create_user(username: str, password: str, email: str) -> Optional[User]:
    """
    Create a new user account with secure password hashing.
    
    Args:
        username (str): Unique username for the account
        password (str): Plain text password (will be hashed securely)
        email (str): User's email address (must be unique)
        
    Returns:
        Optional[User]: Created User object if successful, None if creation fails
    """
    conn = None
    try:
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id, username, email, password_hash, created_at, updated_at;",
            (username, email, hashed_password)
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
    """
    # Bcrypt handles the hashing and comparison securely
    return bcrypt.check_password_hash(user_obj.password_hash, password)

# ===== USER PROFILE UPDATE FUNCTIONS =====

def update_user_username(user_id: int, new_username: str) -> bool:
    """
    Update a user's username.
    
    Args:
        user_id (int): The ID of the user to update
        new_username (str): The new username to set
        
    Returns:
        bool: True if update successful, False if failed
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


# ===== PASSWORD RESET FUNCTIONS =====

def has_valid_reset_code(user_id: int) -> bool:
    """
    Check if user already has a valid unexpired reset code.
    
    Args:
        user_id (int): The user's unique identifier
        
    Returns:
        bool: True if valid code exists, False otherwise
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id FROM password_reset_codes 
            WHERE user_id = %s AND used = FALSE AND expires_at > NOW()
        """, (user_id,))
        
        return cur.fetchone() is not None
        
    except Exception as e:
        logger.error(f"Error checking existing reset code: {e}")
        return False
    finally:
        close_db_connection(conn)

def generate_reset_code(user_id: int) -> Optional[str]:
    """
    Generate and store a 6-digit password reset code for a user.
    Only generates if no valid unexpired code exists.
    
    Args:
        user_id (int): The user's unique identifier
        
    Returns:
        Optional[str]: The 6-digit code if successful, "EXISTS" if code already exists, None if failed
    """
    logger.info(f"Attempting to generate reset code for user_id: {user_id}")
    
    # Check if user already has a valid code
    if has_valid_reset_code(user_id):
        logger.info(f"User {user_id} already has a valid reset code")
        return "EXISTS"
    
    conn = None
    try:
        # Generate 6-digit code
        code = f"{random.randint(100000, 999999)}"
        logger.info(f"Generated code: {code}")
        
        conn = get_db_connection()
        logger.info("Database connection established")
        cur = conn.cursor()
        
        # Invalidate any existing reset codes for this user
        cur.execute(
            "UPDATE password_reset_codes SET used = TRUE WHERE user_id = %s AND used = FALSE;",
            (user_id,)
        )
        
        # Insert new reset code
        cur.execute(
            "INSERT INTO password_reset_codes (user_id, code) VALUES (%s, %s);",
            (user_id, code)
        )
        
        conn.commit()
        logger.info(f"Reset code generated successfully for user_id: {user_id}")
        return code
        
    except Exception as e:
        logger.error(f"Error generating reset code for user_id {user_id}: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        if hasattr(e, 'pgcode'):
            logger.error(f"PostgreSQL error code: {e.pgcode}")
        if conn:
            conn.rollback()
        return None
    finally:
        close_db_connection(conn)


def verify_reset_code(user_id: int, code: str) -> bool:
    """
    Verify a password reset code for a user.
    
    Args:
        user_id (int): The user's unique identifier
        code (str): The 6-digit verification code
        
    Returns:
        bool: True if code is valid and not expired, False otherwise
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Find valid, unused, unexpired code
        cur.execute("""
            SELECT id FROM password_reset_codes 
            WHERE user_id = %s AND code = %s AND used = FALSE AND expires_at > NOW()
        """, (user_id, code))
        
        result = cur.fetchone()
        
        if result:
            # Mark code as used
            cur.execute(
                "UPDATE password_reset_codes SET used = TRUE WHERE id = %s;",
                (result[0],)
            )
            conn.commit()
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error verifying reset code: {e}")
        return False
    finally:
        close_db_connection(conn)


def send_reset_code_email(user_email: str, code: str, username: str = None) -> bool:
    """
    Send password reset code via SendGrid email service.
    
    Args:
        user_email (str): User's email address
        code (str): The 6-digit verification code
        username (str, optional): User's username for personalization
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not SENDGRID_AVAILABLE:
        logger.error("SendGrid not available. Install with: pip install sendgrid")
        return False
    
    # Get configuration
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('FROM_EMAIL')
    from_name = os.getenv('FROM_NAME')
    
    if not sendgrid_api_key:
        logger.error("SENDGRID_API_KEY not configured in .env file")
        return False
    
    # Create email content
    greeting = f"Hi {username}," if username else "Hello,"
    
    try:
        message = Mail(
            from_email=(from_email, from_name),
            to_emails=user_email,
            subject="Password Reset Code - TechPulse",
            html_content=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Password Reset Request</h2>
                <p>{greeting}</p>
                <p>You requested a password reset for your TechPulse account.</p>
                
                <div style="background: #f8f9fa; border: 2px solid #007bff; border-radius: 8px; 
                           padding: 20px; text-align: center; margin: 20px 0;">
                    <p>Your verification code is:</p>
                    <div style="font-size: 32px; font-weight: bold; color: #007bff; letter-spacing: 3px;">
                        {code}
                    </div>
                </div>
                
                <p><strong>Important:</strong> This code will expire in 15 minutes.</p>
                <p>If you didn't request this, please ignore this email.</p>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    Best regards,<br>TechPulse Support
                </p>
            </div>
            """,
            plain_text_content=f"""
{greeting}

You requested a password reset for your TechPulse account.

Your verification code is: {code}

This code will expire in 15 minutes for security reasons.

If you didn't request this password reset, please ignore this email.

Best regards,
TechPulse Support
            """
        )
        
        sg = SendGridAPIClient(api_key=sendgrid_api_key)
        response = sg.send(message)
        
        logger.info(f"Password reset code sent to {user_email} (Status: {response.status_code})")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send reset code: {e}")
        return False


def cleanup_expired_reset_codes() -> int:
    """
    Remove expired and used password reset codes from database.
    
    Returns:
        int: Number of codes cleaned up
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM password_reset_codes WHERE expires_at < NOW() OR used = TRUE;")
        deleted_count = cur.rowcount
        conn.commit()
        
        print(f"Cleaned up {deleted_count} expired/used reset codes")
        return deleted_count
        
    except Exception as e:
        print(f"Error cleaning up reset codes: {e}")
        return 0
    finally:
        close_db_connection(conn)
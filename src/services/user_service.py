from typing import Optional
from src.models.user import User
# Find user by user_id
def find_user_by_id(user_id: int) -> Optional[User]:
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
# Update username by user id
def update_user_username(user_id: int, new_username: str) -> bool:
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

# Update email by user id
def update_user_email(user_id: int, new_email: str) -> bool:
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
from typing import Optional
from src.models.user import User
from flask_bcrypt import Bcrypt
from src.database.connection import get_db_connection, close_db_connection
from psycopg2 import errors as pg_errors
import pyotp

bcrypt = Bcrypt()

def create_user(username: str, password: str, email: str) -> Optional[User]:
    """
    Creates a new user in the database after hashing the password and generating a TOTP secret.
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
    Checks if the provided plain text password matches the hashed password of a User object.

    Args:
        user_obj (User): The User object containing the hashed password.
        password (str): The plain text password to check.

    Returns:
        bool: True if passwords match, False otherwise.
    """
    # Bcrypt handles the hashing and comparison securely
    return bcrypt.check_password_hash(user_obj.password_hash, password)

def find_user_by_username(username: str) -> Optional[User]:
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

#Forget password functionality
def find_user_by_email(email: str) -> Optional[User]:
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
# Update user password by user id
def update_user_password(user_id: int, new_password: str) -> bool:
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

# --- User Topics Management ---
def get_user_topics(user_id: int) -> list:
    """Return a list of topics selected by the user."""
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

def set_user_topics(user_id: int, topics: list):
    """Replace the user's topics with the provided list."""
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
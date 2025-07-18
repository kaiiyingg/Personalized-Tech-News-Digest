from typing import Optional
from src.models.user import User
from flask_bcrypt import Bcrypt #type: ignore
from src.database.connection import get_db_connection, close_db_connection
from src.models.user import User 
from psycopg2 import errors as pg_errors # To catch specific database errors
import pyotp # type: ignore

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
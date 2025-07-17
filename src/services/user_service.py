from typing import Optional
from flask_bcrypt import Bcrypt #type: ignore
from src.database.connection import get_db_connection, close_db_connection
from src.models.user import User 
from psycopg2 import errors as pg_errors # To catch specific database errors

bcrypt = Bcrypt()

def create_user(username: str, password: str) -> Optional[User]:
    """
    Creates a new user in the database after hashing the password.
    Args:
        username (str): The user's username.
        password (str): The user's password.
    Returns:
        Optional[User]: The created User object if successful, None if user already exists.
    """
    conn = None
    try:
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id, created_at, updated_at;",
            (username, hashed_password)
        )
        result = cur.fetchone()
        if result is None:
            if conn:
                conn.rollback()
            print("Error: Failed to insert user or retrieve user data.")
            return None
        user_id, created_at, updated_at = result
        conn.commit()
        return User(user_id, username, hashed_password, created_at, updated_at)
    
    except pg_errors.UniqueViolation as e:
        # Handle unique constraint violation (username already exists)
        print(f"Error: Username already exists. {e}")
        if conn:
            conn.rollback() # Rollback the transaction
        return None
    except Exception as e:
        print(f"An error occurred during user creation: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        close_db_connection(conn)


def find_user_by_username(username: str) -> Optional[User]:
    """
    Finds a user in the database by their username.

    Args:
        username (str): The username to search for.

    Returns:
        Optional[User]: The User object if found, None otherwise.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, password_hash, created_at, updated_at FROM users WHERE username = %s;",
            (username,)
        )
        user_data = cur.fetchone()
        if user_data:
            # Unpack tuple into arguments for User constructor
            return User(*user_data) # This unpacks the tuple directly
        return None
    except Exception as e:
        print(f"An error occurred while finding user: {e}")
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
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file
# Database connection details from .env
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', 5432)

# Good practice: Add a module-level docstring to explain what this file does.
"""
This module handles database connections and table creation for the Learning Stream application.
It loads database credentials from environment variables and uses psycopg2 to interact with PostgreSQL.
"""

def get_db_connection():
    """Establishes and returns a database connection."""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,      
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

def close_db_connection(conn):
    """Closes the database connection."""
    if conn:
        conn.close()
   

def create_tables():
    """Creates necessary tables in the database."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create 'users' table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Create 'courses' table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Create 'enrollments' table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                user_id INTEGER REFERENCES users(id),
                course_id INTEGER REFERENCES courses(id),
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, course_id)
            );
        ''')

        conn.commit()  # Commit the changes
        print("Tables created successfully.")
    except Exception as e:
        print(f"An error occurred while creating tables: {e}")
    finally:
        close_db_connection(conn)

if __name__ == '__main__':
    # This block runs when you execute the script directly (e.g., 'python src/database/connection.py' or 'make setup-db-local').
    load_dotenv() # Load env variables here so they are available when run directly.
    print("Attempting to create database tables...")
    create_tables()
    print("Database table creation process completed.")
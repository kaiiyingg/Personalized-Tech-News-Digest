import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
# Database connection details from .env
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', 5432)

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
    """
    Executes all .sql files in the current directory to create tables and other schema objects.
    Reads each .sql file, executes its content, and commits the changes.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Get all .sql files in the same directory as this script
        sql_dir = os.path.dirname(os.path.abspath(__file__))
        sql_files = [f for f in os.listdir(sql_dir) if f.endswith('.sql')]
        sql_files.sort()  # Ensure a consistent order (e.g., 01_users.sql, 02_sources.sql, ...)
        for sql_file in sql_files:
            file_path = os.path.join(sql_dir, sql_file)
            with open(file_path, 'r', encoding='utf-8') as f:
                sql = f.read()
                cursor.execute(sql)
                print(f"Executed {sql_file}")
        conn.commit()
        print("All SQL scripts executed and tables created successfully.")
    except Exception as e:
        print(f"An error occurred while creating tables: {e}")
    finally:
        close_db_connection(conn)

if __name__ == '__main__':
    load_dotenv()  # Load env variables here so they are available when run directly.
    print("Attempting to create database tables from SQL files...")
    create_tables()
    print("Database table creation process completed.")
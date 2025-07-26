import os
import psycopg2
from dotenv import load_dotenv # type: ignore

load_dotenv()  # Load environment variables from .env file

# Supabase/PostgreSQL connection details from .env
PG_DATABASE = os.getenv('PG_DATABASE')
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_HOST = os.getenv('PG_HOST')
PG_PORT = os.getenv('PG_PORT', 5432)

"""
This module handles database connections and table creation for the TechPulse application.
It loads database credentials from environment variables and uses psycopg2 to interact with PostgreSQL.
Run "python src/database/connection.py" to create tables based on SQL scripts in the same directory.
"""

def get_db_connection():
    """Establishes and returns a database connection."""
    conn = psycopg2.connect(
        dbname=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD,
        host=PG_HOST,
        port=PG_PORT
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
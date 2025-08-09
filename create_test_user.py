#!/usr/bin/env python3
"""
Quick script to create a test user for development
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from src.services.user_service import create_user
from src.database.connection import get_db_connection, close_db_connection

def create_test_user():
    """Create a test user for development"""
    try:
        # Test user credentials
        username = "testuser"
        email = "test@example.com"
        password = "password123"
        
        print("Creating test user...")
        user = create_user(username, email, password)
        
        if user:
            print(f"✅ Test user created successfully!")
            print(f"Username: {username}")
            print(f"Email: {email}")
            print(f"Password: {password}")
            print(f"User ID: {user.id}")
        else:
            print("❌ Failed to create test user")
            
    except Exception as e:
        print(f"Error creating test user: {e}")

if __name__ == "__main__":
    create_test_user()

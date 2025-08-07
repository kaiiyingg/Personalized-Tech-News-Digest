#!/usr/bin/env python3
"""
Test script to verify database connection to Supabase
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.database.connection import get_db_connection
    print("🔄 Testing database connection...")
    
    conn = get_db_connection()
    print("✅ Database connection successful!")
    
    # Test a simple query
    cursor = conn.cursor()
    cursor.execute("SELECT current_database(), current_user;")
    result = cursor.fetchone()
    print(f"📊 Connected to database: {result[0]} as user: {result[1]}")
    
    cursor.close()
    conn.close()
    print("🔒 Connection closed successfully")
    
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print("\nTroubleshooting steps:")
    print("1. Check if .env file exists and has correct credentials")
    print("2. Verify Supabase database is running")
    print("3. Check network connectivity")

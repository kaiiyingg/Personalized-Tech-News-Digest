#!/usr/bin/env python3
"""
Script to clean existing articles from the database.

This script removes all existing articles from the content table since you're using 
AWS CloudWatch to automatically inject articles daily from your RSS sources.

Instructions:
1. Run: python clean_articles.py
2. This will remove all existing articles from the database
3. Your RSS sources will remain intact
4. AWS CloudWatch will repopulate articles on its next scheduled run
"""

import sys
import os

# Add the project root to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import get_db_connection, close_db_connection

def clean_articles():
    """Remove all articles from the content table."""
    user_id = 1  # All content belongs to user ID 1
    
    print("🧹 Starting article cleanup...")
    print("⚠️  This will remove ALL existing articles from the database!")
    print("-" * 60)
    
    # Confirm with user
    confirm = input("Are you sure you want to delete all articles? (yes/no): ").lower().strip()
    if confirm not in ['yes', 'y']:
        print("❌ Operation cancelled by user.")
        return False
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # First, count existing articles
        cur.execute("SELECT COUNT(*) FROM content WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        article_count = result[0] if result else 0
        
        if article_count == 0:
            print("ℹ️  No articles found in database. Nothing to clean.")
            return True
        
        print(f"📊 Found {article_count} articles to remove...")
        
        # Delete all user content interactions first (to maintain referential integrity)
        cur.execute("DELETE FROM user_content_interactions WHERE user_id = %s", (user_id,))
        interactions_deleted = cur.rowcount
        
        # Delete all content for this user
        cur.execute("DELETE FROM content WHERE user_id = %s", (user_id,))
        articles_deleted = cur.rowcount
        
        conn.commit()
        
        print(f"✅ Successfully cleaned database:")
        print(f"   🗑️  Removed {articles_deleted} articles")
        print(f"   🗑️  Removed {interactions_deleted} user interactions")
        print(f"📊 Database is now clean and ready for AWS CloudWatch ingestion!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        close_db_connection(conn)

def verify_sources_intact():
    """Verify that RSS sources are still intact after cleanup."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM sources WHERE user_id = %s", (1,))
        result = cur.fetchone()
        source_count = result[0] if result else 0
        
        print(f"📋 Verified: {source_count} RSS sources remain intact")
        
        if source_count > 0:
            cur.execute("SELECT source_name FROM sources WHERE user_id = %s ORDER BY source_name LIMIT 5", (1,))
            sample_sources = cur.fetchall()
            print("📝 Sample sources:")
            for source in sample_sources:
                print(f"   • {source[0]}")
            if source_count > 5:
                print(f"   ... and {source_count - 5} more")
        
        return source_count > 0
        
    except Exception as e:
        print(f"❌ Error verifYying sources: {e}")
        return False
    finally:
        close_db_connection(conn)

if __name__ == "__main__":
    try:
        print("🔄 Article Cleanup Tool for AWS CloudWatch Integration")
        print("="*60)
        
        # Clean articles
        if clean_articles():
            print()
            # Verify sources are intact
            verify_sources_intact()
            print()
            print("🎉 Cleanup complete! Your database is ready for AWS CloudWatch.")
            print("💡 Your RSS sources are preserved and CloudWatch will repopulate articles.")
        else:
            print("❌ Cleanup failed. Please check the error messages above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

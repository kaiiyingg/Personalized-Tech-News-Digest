#!/usr/bin/env python3
"""Clean up inappropriate content from database"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import get_db_connection, close_db_connection

def cleanup_inappropriate_content():
    """Remove articles with inappropriate keywords"""
    
    # Keywords that indicate inappropriate content
    inappropriate_keywords = [
        'vibrator', 'sex', 'adult', 'porn', 'explicit', 'nsfw', 'erotic', 'sexual'
    ]
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check for articles with inappropriate content
        for keyword in inappropriate_keywords:
            cur.execute("""
                SELECT id, title, summary FROM content 
                WHERE LOWER(title) LIKE %s OR LOWER(summary) LIKE %s
            """, (f'%{keyword}%', f'%{keyword}%'))
            
            inappropriate_articles = cur.fetchall()
            
            if inappropriate_articles:
                print(f"Found {len(inappropriate_articles)} articles with keyword '{keyword}':")
                for article_id, title, summary in inappropriate_articles:
                    print(f"  ID {article_id}: {title[:50]}...")
                
                # Delete these articles
                for article_id, _, _ in inappropriate_articles:
                    # First delete from user_content_interactions
                    cur.execute("DELETE FROM user_content_interactions WHERE content_id = %s", (article_id,))
                    # Then delete from content
                    cur.execute("DELETE FROM content WHERE id = %s", (article_id,))
                    print(f"  Deleted article ID {article_id}")
                
                conn.commit()
        
        print("Cleanup completed!")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        if conn:
            conn.rollback()
    finally:
        close_db_connection(conn)

if __name__ == "__main__":
    cleanup_inappropriate_content()

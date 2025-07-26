# src/lambdas/ingestion_orchestrator.py
# This Lambda queries RDS for active sources and sends messages to SQS.
import os
import json
import boto3 
import psycopg2
from datetime import datetime
from typing import List, Dict, Any, Optional

# Re-use connection functions, or copy relevant parts if you want Lambdas completely standalone
# For simplicity, we'll assume a direct connection setup here.
# In a real project, you might package these utility functions into a Lambda layer.

# Environment variables will be set in CloudFormation
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL') # This SQS_QUEUE_URL will be passed from ingestion.yaml output

# SQS client should be initialized outside the handler for warm starts
sqs_client = boto3.client('sqs')

def smart_cleanup_old_articles(conn):
    """
    Smart cleanup that removes old articles only if fresh content is available.
    
    Rules:
    1. Only removes articles older than 24 hours if we have articles from today
    2. If no fresh articles today, keeps yesterday's articles to prevent empty site
    3. Always preserves user-liked articles regardless of age
    4. Ensures minimum content threshold is maintained
    
    Returns:
        dict: Cleanup results with statistics
    """
    try:
        cur = conn.cursor()
        
        # Check if we have fresh articles from today
        cur.execute("""
            SELECT COUNT(*) FROM content 
            WHERE DATE(published_at) = CURRENT_DATE
            AND id NOT IN (
                SELECT DISTINCT content_id 
                FROM user_content_interactions 
                WHERE is_liked = true
            )
        """)
        result_fresh = cur.fetchone()
        fresh_articles_today = result_fresh[0] if result_fresh else 0
        
        # Check total available articles (excluding liked)
        cur.execute("""
            SELECT COUNT(*) FROM content 
            WHERE id NOT IN (
                SELECT DISTINCT content_id 
                FROM user_content_interactions 
                WHERE is_liked = true
            )
        """)
        result_total = cur.fetchone()
        total_unloved_articles = result_total[0] if result_total else 0
        
        # Minimum content threshold to maintain
        MIN_ARTICLES = 10
        
        result = {
            'fresh_today': fresh_articles_today,
            'total_available': total_unloved_articles,
            'deleted_count': 0,
            'action_taken': 'none',
            'reason': ''
        }
        
        # Decision logic for cleanup
        if fresh_articles_today >= MIN_ARTICLES:
            # We have enough fresh content, safe to clean old articles
            cur.execute("""
                DELETE FROM content 
                WHERE published_at < NOW() - INTERVAL '24 hours'
                AND id NOT IN (
                    SELECT DISTINCT content_id 
                    FROM user_content_interactions 
                    WHERE is_liked = true
                )
            """)
            deleted_count = cur.rowcount
            conn.commit()
            
            result.update({
                'deleted_count': deleted_count,
                'action_taken': 'cleanup_performed',
                'reason': f'Fresh content available ({fresh_articles_today} new articles)'
            })
            
        elif fresh_articles_today > 0 and total_unloved_articles > 20:
            # Some fresh content, but clean conservatively
            cur.execute("""
                DELETE FROM content 
                WHERE published_at < NOW() - INTERVAL '48 hours'
                AND id NOT IN (
                    SELECT DISTINCT content_id 
                    FROM user_content_interactions 
                    WHERE is_liked = true
                )
            """)
            deleted_count = cur.rowcount
            conn.commit()
            
            result.update({
                'deleted_count': deleted_count,
                'action_taken': 'conservative_cleanup',
                'reason': f'Limited fresh content ({fresh_articles_today} new), extended retention to 48h'
            })
            
        else:
            # No fresh content or insufficient articles, skip cleanup
            result.update({
                'action_taken': 'cleanup_skipped',
                'reason': f'Insufficient fresh content ({fresh_articles_today} new articles). Preserving existing content to prevent empty site.'
            })
        
        print(f"=== Lambda Smart Cleanup Results ===")
        print(f"Fresh articles today: {result['fresh_today']}")
        print(f"Total available: {result['total_available']}")
        print(f"Action: {result['action_taken']}")
        print(f"Reason: {result['reason']}")
        print(f"Articles removed: {result['deleted_count']}")
        print("=" * 40)
        
        return result
        
    except Exception as e:
        error_msg = f"Error during smart cleanup: {e}"
        print(error_msg)
        conn.rollback()
        return {
            'error': error_msg,
            'action_taken': 'error',
            'deleted_count': 0
        }

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for the Ingestion Orchestrator.
    1. Performs smart cleanup of old articles
    2. Queries RDS for sources and sends messages to SQS for fresh content ingestion
    """
    print("Ingestion Orchestrator Lambda triggered.")
    conn = None
    try:
        conn = get_db_connection()
        
        # Step 1: Perform smart cleanup before ingesting new content
        print("Starting smart cleanup before content ingestion...")
        cleanup_result = smart_cleanup_old_articles(conn)
        
        # Step 2: Query for sources and trigger content ingestion
        cur = conn.cursor()
        cur.execute("SELECT id, user_id, source_name, feed_url, type FROM sources;")
        sources = cur.fetchall()
        print(f"Found {len(sources)} sources to process for fresh content.")

        if not SQS_QUEUE_URL:
            raise ValueError("SQS_QUEUE_URL environment variable is not set.")

        messages_sent_count = 0
        for source in sources:
            source_id, user_id, name, feed_url, source_type = source
            message_body = {
                'source_id': source_id,
                'user_id': user_id,
                'source_name': name,
                'feed_url': feed_url,
                'type': source_type
            }
            # Send message to SQS
            sqs_client.send_message(
                QueueUrl=SQS_QUEUE_URL,
                MessageBody=json.dumps(message_body)
            )
            messages_sent_count += 1
            print(f"Sent message for source ID: {source_id} ({name})")

        print(f"Successfully sent {messages_sent_count} messages to SQS for content processing.")
        
        # Return comprehensive results
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully processed {len(sources)} sources. Sent {messages_sent_count} messages.',
                'cleanup_result': cleanup_result,
                'sources_processed': len(sources),
                'messages_sent': messages_sent_count
            })
        }

    except Exception as e:
        print(f"Error in Ingestion Orchestrator: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error in Ingestion Orchestrator: {e}')
        }
    finally:
        if conn:
            conn.close()
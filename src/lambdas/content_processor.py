# src/lambdas/content_processor.py
# This Lambda processes SQS messages, fetches content from sources, and stores it in RDS.
import os
import json
import requests
import feedparser 
from datetime import datetime
from typing import Dict, Any

# Assuming create_content_item is accessible. In a real Lambda deployment,
# you'd zip your entire 'src' directory, or put services in a Lambda layer.
# For simplicity, we'll assume a direct import.
from src.services.content_service import create_content_item
from src.database.connection import get_db_connection, close_db_connection # Re-use DB connection


# Environment variables will be set in CloudFormation
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Max characters for summary to fit TEXT column or avoid excessive size
MAX_SUMMARY_LENGTH = 1000

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for the Content Processor.
    Processes messages from SQS, fetches content, and stores it.
    """
    print(f"Content Processor Lambda triggered with {len(event['Records'])} records.")
    
    conn = None 
    try:
        conn = get_db_connection()
        
        for record in event['Records']:
            message_body = json.loads(record['body'])
            source_id = message_body['source_id']
            feed_url = message_body['feed_url']
            source_type = message_body['type']
            source_name = message_body.get('source_name', feed_url)  

            print(f"Processing source: {source_name} (ID: {source_id}, URL: {feed_url})")

            if source_type == 'rss':
                try:
                    response = requests.get(feed_url, timeout=10)
                    response.raise_for_status()
                    feed = feedparser.parse(response.text)

                    articles_processed = 0
                    for entry in feed.entries:
                        title = getattr(entry, 'title', 'No Title').strip()
                        article_url = getattr(entry, 'link', None)
                        summary = getattr(entry, 'summary', getattr(entry, 'description', '')).strip()
                        published_at_str = getattr(entry, 'published', None)
                        
                        if not article_url or not title:
                            print(f"Skipping entry from {source_name} due to missing URL or title.")
                            continue

                        summary = summary[:MAX_SUMMARY_LENGTH] if len(summary) > MAX_SUMMARY_LENGTH else summary

                        published_at = None
                        if published_at_str:
                            try:
                                published_parsed = getattr(entry, 'published_parsed', None)
                                # Only convert if published_parsed is a struct_time
                                import time
                                if published_parsed and isinstance(published_parsed, time.struct_time):
                                    published_at = datetime(*published_parsed[:6])
                                else:
                                    published_at = None
                            except Exception as dt_e:
                                print(f"Warning: Could not parse published date '{published_at_str}': {dt_e}")
                                published_at = None

                        new_content = create_content_item(
                            source_id,
                            title,
                            summary,
                            article_url,
                            published_at
                        )
                        if new_content:
                            articles_processed += 1
                            print(f"  Added/Processed article: {new_content.title[:50]}...")
                        else:
                            print(f"  Failed to add article '{title}' (likely duplicate).")
                    
                    print(f"Finished processing {source_name}. Added/updated {articles_processed} articles.")

                except requests.exceptions.RequestException as req_e:
                    print(f"HTTP/Network error fetching {feed_url}: {req_e}")
                except Exception as e:
                    print(f"Error processing RSS feed {feed_url}: {e}")
            else:
                print(f"Source type '{source_type}' not supported yet. Skipping.")

    except Exception as e:
        print(f"Error in Content Processor Lambda handler: {e}")
        raise e

    finally:
        if conn:
            close_db_connection(conn)

    return {
        'statusCode': 200,
        'body': json.dumps('Content processing finished for batch.')
    }
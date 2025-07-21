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
    Queries RDS for sources and sends messages to SQS.
    """
    print("Ingestion Orchestrator Lambda triggered.")
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Query for all active sources
        # (Assuming 'sources' table contains user_id, name, feed_url, type)
        cur.execute("SELECT id, user_id, source_name, feed_url, type FROM sources;")
        sources = cur.fetchall()
        print(f"Found {len(sources)} sources to process.")

        if not SQS_QUEUE_URL:
            raise ValueError("SQS_QUEUE_URL environment variable is not set.")

        messages_sent_count = 0
        for source in sources:
            source_id, user_id, name, feed_url, source_type = source
            message_body = {
                'source_id': source_id,
                'user_id': user_id, # Pass user_id for potential personalized processing
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

        print(f"Successfully sent {messages_sent_count} messages to SQS.")
        return {
            'statusCode': 200,
            'body': json.dumps(f'Successfully processed {len(sources)} sources. Sent {messages_sent_count} messages.')
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
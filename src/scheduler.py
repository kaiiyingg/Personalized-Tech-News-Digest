#!/usr/bin/env python3
"""
Daily Article Cleanup Scheduler

This script handles the automatic cleanup of old articles while preserving
user favorites. It's designed to run as a daily cron job or scheduled task.

Key Features:
- Removes articles older than 24 hours
- Preserves articles that users have liked (favorites)
- Logs cleanup activities
- Safe error handling
"""

import os
import sys
import schedule #type:ignore
import time
from datetime import datetime, timedelta

# Add the src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from services.content_service import cleanup_old_articles
except ImportError:
    from src.services.content_service import cleanup_old_articles

def run_daily_cleanup():
    """
    Executes the smart daily article cleanup process.
    
    This function:
    1. Checks for fresh content availability
    2. Only removes old articles if fresh content exists
    3. Preserves user-liked articles regardless of age
    4. Prevents the website from becoming empty
    5. Logs detailed cleanup results
    """
    print(f"\n=== Smart Daily Article Cleanup Started at {datetime.now()} ===")
    
    try:
        result = cleanup_old_articles()
        
        if 'error' in result:
            print(f"❌ Cleanup failed: {result['error']}")
            log_cleanup_result(result, success=False)
            return
        
        print(f"✅ Smart cleanup completed successfully")
        print(f"📊 Action taken: {result['action_taken']}")
        print(f"🔍 Reason: {result['reason']}")
        print(f"📈 Fresh articles today: {result['fresh_today']}")
        print(f"📉 Articles removed: {result['deleted_count']}")
        print(f"💖 Favorite articles preserved (regardless of age)")
        
        # Log to file for monitoring
        log_cleanup_result(result, success=True)
        
    except Exception as e:
        error_msg = f"Cleanup script error: {e}"
        print(f"❌ {error_msg}")
        log_cleanup_result({'error': error_msg, 'deleted_count': 0}, success=False)
    
    print(f"=== Smart Daily Article Cleanup Completed at {datetime.now()} ===\n")

def log_cleanup_result(result, success=True):
    """
    Logs detailed cleanup results to a file for monitoring and debugging.
    
    Args:
        result (dict): Cleanup result dictionary with statistics
        success (bool): Whether cleanup was successful
    """
    try:
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'cleanup.log')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if success:
            log_entry = (
                f"{timestamp} - SUCCESS: {result.get('action_taken', 'unknown')} | "
                f"Deleted: {result.get('deleted_count', 0)} | "
                f"Fresh today: {result.get('fresh_today', 0)} | "
                f"Reason: {result.get('reason', 'N/A')}\n"
            )
        else:
            error_msg = result.get('error', 'Unknown error')
            log_entry = f"{timestamp} - ERROR: Cleanup failed - {error_msg}\n"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
            
    except Exception as e:
        print(f"Warning: Could not write to log file: {e}")

def start_scheduler():
    """
    Starts the cleanup scheduler.
    
    Schedules daily cleanup at 3:00 AM when server load is typically low.
    You can modify the time by changing the schedule.every().day.at() parameter.
    """
    print("🚀 TechPulse Article Cleanup Scheduler Starting...")
    print("📅 Scheduled to run daily at 3:00 AM")
    print("💡 Tip: Run this script continuously or set up as a system service")
    print("-" * 60)
    
    # Schedule daily cleanup at 3:00 AM
    schedule.every().day.at("03:00").do(run_daily_cleanup)
    
    # Optional: Run cleanup immediately on startup for testing
    # Uncomment the line below if you want to test the cleanup immediately
    # run_daily_cleanup()
    
    print("⏰ Scheduler active. Waiting for next scheduled cleanup...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    try:
        start_scheduler()
    except KeyboardInterrupt:
        print("\n🛑 Scheduler stopped by user")
    except Exception as e:
        print(f"\n❌ Scheduler error: {e}")

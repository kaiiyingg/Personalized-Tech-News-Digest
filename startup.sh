#!/bin/bash

# Production startup script for TechPulse
set -e

echo "🚀 Starting TechPulse in production mode..."

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
python -c "
import time
import os
import sys
sys.path.append('/app/src')
from database.connection import get_connection

max_attempts = 30
for attempt in range(max_attempts):
    try:
        conn = get_connection()
        if conn:
            conn.close()
            print('✅ Database connection successful')
            break
    except Exception as e:
        if attempt == max_attempts - 1:
            print(f'❌ Database connection failed after {max_attempts} attempts: {e}')
            sys.exit(1)
        print(f'⏳ Database connection attempt {attempt + 1}/{max_attempts} failed, retrying...')
        time.sleep(2)
"

# Wait for Redis to be ready (optional)
echo "⏳ Checking Redis connection..."
python -c "
try:
    import redis
    import os
    redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379/0'))
    redis_client.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'⚠️ Redis not available: {e}')
    print('📝 Will use memory cache as fallback')
"

# Run database migrations/setup if needed
if [ -f "/app/src/database/06_indexes.sql" ]; then
    echo "🗄️ Setting up database indexes..."
    # This would run in a real deployment with proper DB credentials
    echo "📝 Note: Run 'psql -f src/database/06_indexes.sql' manually for index setup"
fi

# Set production environment
export FLASK_ENV=production
export PYTHONPATH="/app/src:$PYTHONPATH"

# Start Gunicorn with optimized settings
echo "🌟 Starting Gunicorn server..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class gevent \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance \
    src.app:app

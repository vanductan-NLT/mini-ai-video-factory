#!/bin/bash
# Simple startup script for Mini Video Factory

echo "Starting Mini Video Factory..."

# Create directories
mkdir -p /app/data/uploads /app/data/temp /app/data/output /app/logs

# Check required environment variables
if [ -z "$SECRET_KEY" ] || [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
    echo "ERROR: Missing required environment variables (SECRET_KEY, SUPABASE_URL, SUPABASE_KEY)"
    exit 1
fi

# Start application
if [ "${FLASK_DEBUG:-False}" = "True" ]; then
    echo "Starting in development mode..."
    exec python3 app.py
else
    echo "Starting in production mode..."
    exec gunicorn \
        --bind 0.0.0.0:${PORT:-5000} \
        --workers ${GUNICORN_WORKERS:-2} \
        --timeout ${GUNICORN_TIMEOUT:-300} \
        --log-level info \
        app:app
fi
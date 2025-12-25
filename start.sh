#!/bin/bash
# Simple startup script for Mini Video Factory

echo "Starting Mini Video Factory..."

# Create directories with proper permissions
mkdir -p /app/data/uploads /app/data/temp /app/data/output /app/logs 2>/dev/null || true

# Check required environment variables
if [ -z "$SECRET_KEY" ]; then
    echo "ERROR: Missing required environment variable: SECRET_KEY"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: Missing required environment variable: DATABASE_URL"
    exit 1
fi

# Skip migrations for now
echo "Skipping database migrations for now..."

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
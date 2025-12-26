#!/bin/bash
# Simple startup script for Mini Video Factory

echo "Starting Mini Video Factory..."

# Create directories with proper permissions (if they don't exist)
echo "Creating data directories..."
mkdir -p /app/data/uploads /app/data/temp /app/data/output /app/logs 2>/dev/null || {
    echo "Warning: Could not create some directories, they may already exist"
}

# Set permissions if we can
chmod 755 /app/data/uploads /app/data/temp /app/data/output /app/logs 2>/dev/null || {
    echo "Warning: Could not set directory permissions"
}

# Check required environment variables
if [ -z "$SECRET_KEY" ]; then
    echo "ERROR: Missing required environment variable: SECRET_KEY"
    exit 1
fi

# Check database configuration - DATABASE_URL is required for local PostgreSQL
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: Missing required environment variable: DATABASE_URL"
    echo "Please set DATABASE_URL to your PostgreSQL connection string"
    exit 1
fi

echo "Using local PostgreSQL database"

# Run database migrations
echo "Running database migrations..."
python3 migrate.py || {
    echo "Warning: Migration script failed, continuing startup..."
}

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
#!/bin/bash
set -e

echo "Starting Mini Video Factory..."

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if running as root (should not be in production)
if [ "$EUID" -eq 0 ]; then
    log "WARNING: Running as root user. This is not recommended for production."
fi

# Validate required environment variables
log "Validating environment configuration..."

required_vars=(
    "SECRET_KEY"
    "SUPABASE_URL"
    "SUPABASE_KEY"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    log "ERROR: Missing required environment variables: ${missing_vars[*]}"
    log "Please check your .env file or environment configuration."
    exit 1
fi

# Optional Wasabi configuration check
if [ -n "$WASABI_ACCESS_KEY_ID" ] && [ -n "$WASABI_SECRET_ACCESS_KEY" ]; then
    log "Wasabi storage configuration detected"
else
    log "WARNING: Wasabi storage not configured. Using local storage only."
fi

# Create necessary directories
log "Creating application directories..."
mkdir -p /app/data/uploads /app/data/temp /app/data/output /app/logs

# Set proper permissions
chmod 755 /app/data/uploads /app/data/temp /app/data/output /app/logs

# Check disk space
log "Checking available disk space..."
df -h /app/data

# Test database connectivity
log "Testing database connectivity..."
python3 -c "
import os
from supabase import create_client, Client
try:
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY')
    supabase = create_client(url, key)
    # Simple test query
    result = supabase.table('users').select('count').limit(1).execute()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
"

# Test Wasabi connectivity (if configured)
if [ -n "$WASABI_ACCESS_KEY_ID" ] && [ -n "$WASABI_SECRET_ACCESS_KEY" ]; then
    log "Testing Wasabi storage connectivity..."
    python3 -c "
import os
import boto3
from botocore.exceptions import ClientError
try:
    client = boto3.client(
        's3',
        endpoint_url=os.environ.get('WASABI_ENDPOINT'),
        aws_access_key_id=os.environ.get('WASABI_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('WASABI_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('WASABI_REGION', 'us-east-1')
    )
    bucket = os.environ.get('WASABI_BUCKET')
    client.head_bucket(Bucket=bucket)
    print('Wasabi storage connection successful')
except Exception as e:
    print(f'Wasabi storage connection failed: {e}')
    print('Continuing with local storage only...')
"
fi

# Check required tools
log "Checking required tools..."
tools=("ffmpeg" "python3" "pip")
for tool in "${tools[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        log "ERROR: Required tool '$tool' not found"
        exit 1
    else
        log "$tool: $(command -v "$tool")"
    fi
done

# Check Python packages
log "Checking Python packages..."
python3 -c "
import sys
required_packages = [
    'flask', 'supabase', 'boto3', 'whisper', 
    'auto_editor', 'magic', 'PIL'
]
missing = []
for pkg in required_packages:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    print(f'Missing Python packages: {missing}')
    sys.exit(1)
else:
    print('All required Python packages are available')
"

# Initialize Whisper model (download if needed)
log "Initializing Whisper model..."
python3 -c "
import whisper
import os
model_name = os.environ.get('WHISPER_MODEL', 'base')
try:
    model = whisper.load_model(model_name)
    print(f'Whisper model {model_name} loaded successfully')
except Exception as e:
    print(f'Failed to load Whisper model: {e}')
    exit(1)
"

# Start the application
log "Starting Flask application..."

# Use gunicorn for production deployment
if [ "${FLASK_DEBUG:-False}" = "True" ]; then
    log "Starting in development mode..."
    exec python3 app.py
else
    log "Starting in production mode with gunicorn..."
    exec gunicorn \
        --bind 0.0.0.0:${PORT:-5000} \
        --workers ${GUNICORN_WORKERS:-2} \
        --worker-class sync \
        --worker-connections ${GUNICORN_WORKER_CONNECTIONS:-1000} \
        --max-requests ${GUNICORN_MAX_REQUESTS:-1000} \
        --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-100} \
        --timeout ${GUNICORN_TIMEOUT:-300} \
        --keep-alive ${GUNICORN_KEEPALIVE:-5} \
        --log-level ${LOG_LEVEL:-info} \
        --access-logfile /app/logs/access.log \
        --error-logfile /app/logs/error.log \
        --capture-output \
        app:app
fi
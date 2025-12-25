# Mini Video Factory - Docker Deployment Guide

This guide provides complete instructions for deploying Mini Video Factory using Docker.

## Prerequisites

- Docker Engine 20.10+ installed
- Docker Compose 2.0+ installed
- 4GB+ RAM available
- 20GB+ free disk space
- Internet connection for downloading dependencies

## Quick Deployment

### 1. Prepare Environment

```bash
# Copy environment template
cp .env.docker .env

# Edit configuration (required)
nano .env
```

**Required Configuration:**
- `SECRET_KEY` - Generate with: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anonymous key
- `WASABI_*` - Wasabi storage credentials (optional, falls back to local storage)

### 2. Deploy Application

```bash
# Validate configuration
./docker/validate.sh

# Deploy in development mode
./docker/deploy.sh

# Or deploy in production mode with Nginx
./docker/deploy.sh production
```

### 3. Access Application

- **Development mode:** http://localhost:8080
- **Production mode:** http://localhost (port 80)

## Configuration Files

### Docker Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build with all dependencies |
| `docker-compose.yml` | Service orchestration |
| `.dockerignore` | Build optimization |

### Scripts

| Script | Purpose |
|--------|---------|
| `docker/startup.sh` | Container initialization and health checks |
| `docker/deploy.sh` | Automated deployment with validation |
| `docker/healthcheck.sh` | Comprehensive health monitoring |
| `docker/validate.sh` | Configuration validation |

### Configuration

| File | Purpose |
|------|---------|
| `.env.docker` | Docker environment template |
| `docker/nginx.conf` | Production reverse proxy configuration |

## Deployment Modes

### Development Mode

```bash
./docker/deploy.sh development
```

**Features:**
- Single container deployment
- Direct Flask application access
- Development-friendly logging
- Hot reload support (if enabled)

**Access:** http://localhost:8080

### Production Mode

```bash
./docker/deploy.sh production
```

**Features:**
- Multi-container with Nginx reverse proxy
- Load balancing and rate limiting
- Enhanced security headers
- SSL/TLS ready (requires certificate setup)
- Optimized for performance

**Access:** http://localhost (port 80)

## Management Commands

### Basic Operations

```bash
# Start services
./docker/deploy.sh

# Stop services
./docker/deploy.sh stop

# View logs
./docker/deploy.sh logs

# Restart services
./docker/deploy.sh restart

# Update application
./docker/deploy.sh update

# Clean up everything
./docker/deploy.sh clean
```

### Advanced Operations

```bash
# Manual Docker Compose commands
docker-compose up -d
docker-compose down
docker-compose logs -f mini-video-factory
docker-compose exec mini-video-factory bash

# Health checks
curl http://localhost:8080/health
docker exec mini-video-factory /app/docker/healthcheck.sh
```

## Volume Mapping

Data persistence is handled through Docker volumes:

```yaml
volumes:
  - ./data:/app/data          # Video files and processing data
  - ./logs:/app/logs          # Application logs
  - ./.env:/app/.env:ro       # Environment configuration
```

**Host Directories:**
- `./data/uploads/` - Uploaded video files
- `./data/temp/` - Temporary processing files
- `./data/output/` - Processed video files
- `./logs/` - Application and access logs

## Environment Variables

### Required Variables

```bash
# Application Security
SECRET_KEY=your-secure-secret-key

# Database (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Storage (Wasabi - Optional)
WASABI_ENDPOINT=https://s3.region.wasabisys.com
WASABI_REGION=us-east-1
WASABI_BUCKET=your-bucket-name
WASABI_ACCESS_KEY_ID=your-access-key
WASABI_SECRET_ACCESS_KEY=your-secret-key
```

### Optional Variables

```bash
# Application Configuration
HOST_PORT=8080                    # Host port mapping
MAX_FILE_SIZE=104857600          # 100MB file size limit
MAX_DURATION=600                 # 10 minute duration limit

# Processing Configuration
WHISPER_MODEL=base               # Whisper model: tiny, base, small, medium, large
AUTO_EDITOR_ARGS=--no_open --margin 0.2

# Production Configuration
GUNICORN_WORKERS=2               # Number of worker processes
GUNICORN_TIMEOUT=300             # Request timeout in seconds
LOG_LEVEL=INFO                   # Logging level

# Nginx Configuration (Production mode)
NGINX_PORT=80                    # HTTP port
NGINX_SSL_PORT=443              # HTTPS port
```

## Resource Requirements

### Minimum Requirements

- **CPU:** 1 core (2.0 GHz)
- **Memory:** 1GB RAM
- **Storage:** 10GB free space
- **Network:** Broadband internet

### Recommended Requirements

- **CPU:** 2+ cores (2.5+ GHz)
- **Memory:** 4GB+ RAM
- **Storage:** 50GB+ free space
- **Network:** High-speed internet for video processing

### Resource Limits

The Docker configuration includes resource limits:

```yaml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2.0'
    reservations:
      memory: 1G
      cpus: '0.5'
```

## Monitoring and Health Checks

### Built-in Health Checks

The application includes comprehensive health monitoring:

- **HTTP Health Check:** `GET /health`
- **Container Health Check:** Every 30 seconds
- **Startup Grace Period:** 60 seconds
- **Failure Threshold:** 3 consecutive failures

### Manual Health Checks

```bash
# Application health
curl -f http://localhost:8080/health

# Comprehensive system check
docker exec mini-video-factory /app/docker/healthcheck.sh

# Resource usage
docker stats mini-video-factory
```

### Log Monitoring

```bash
# Application logs
docker-compose logs -f mini-video-factory

# Nginx logs (production mode)
docker-compose logs -f nginx

# Real-time log monitoring
tail -f ./logs/app.log
tail -f ./logs/error.log
```

## Security Considerations

### Production Security

1. **Strong Secrets:**
   ```bash
   # Generate secure secret key
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **SSL/TLS Configuration:**
   - Obtain SSL certificates (Let's Encrypt recommended)
   - Update `docker/nginx.conf` with SSL configuration
   - Redirect HTTP to HTTPS

3. **Network Security:**
   - Use firewall rules to limit access
   - Consider VPN for administrative access
   - Regularly update base images and dependencies

4. **File Permissions:**
   ```bash
   chmod 750 ./data
   chmod 640 ./logs/*.log
   ```

### Data Protection

1. **Regular Backups:**
   ```bash
   # Backup data and logs
   tar -czf backup-$(date +%Y%m%d).tar.gz ./data ./logs
   ```

2. **Secure Storage:**
   - Use Wasabi storage for production
   - Enable encryption at rest
   - Implement retention policies

## Troubleshooting

### Common Issues

1. **Container Won't Start:**
   ```bash
   # Check logs
   docker-compose logs mini-video-factory
   
   # Verify configuration
   ./docker/validate.sh
   ```

2. **Database Connection Failed:**
   ```bash
   # Test Supabase connection
   docker exec mini-video-factory python3 -c "
   import os
   from supabase import create_client
   client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
   print('Connection successful')
   "
   ```

3. **Storage Issues:**
   ```bash
   # Check disk space
   df -h ./data
   
   # Check permissions
   ls -la ./data
   
   # Test Wasabi connection
   docker exec mini-video-factory python3 -c "
   import boto3, os
   client = boto3.client('s3',
       endpoint_url=os.getenv('WASABI_ENDPOINT'),
       aws_access_key_id=os.getenv('WASABI_ACCESS_KEY_ID'),
       aws_secret_access_key=os.getenv('WASABI_SECRET_ACCESS_KEY'))
   print('Wasabi connection successful')
   "
   ```

4. **Processing Failures:**
   ```bash
   # Check tool availability
   docker exec mini-video-factory which ffmpeg
   docker exec mini-video-factory which auto-editor
   
   # Test Whisper model
   docker exec mini-video-factory python3 -c "
   import whisper
   model = whisper.load_model('base')
   print('Whisper model loaded successfully')
   "
   ```

### Performance Issues

1. **Increase Resources:**
   ```yaml
   # In docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 8G
         cpus: '4.0'
   ```

2. **Optimize Processing:**
   ```bash
   # Use smaller Whisper model for faster processing
   WHISPER_MODEL=tiny
   
   # Increase worker processes
   GUNICORN_WORKERS=4
   ```

3. **Storage Optimization:**
   ```bash
   # Clean up old files
   find ./data/temp -type f -mtime +7 -delete
   ```

## Backup and Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup.sh - Automated backup script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"

# Stop services
docker-compose down

# Create backup
tar -czf "$BACKUP_DIR/mini-video-factory-$DATE.tar.gz" \
    ./data \
    ./logs \
    ./.env \
    ./docker-compose.yml

# Restart services
docker-compose up -d

echo "Backup created: $BACKUP_DIR/mini-video-factory-$DATE.tar.gz"
```

### Recovery Process

```bash
#!/bin/bash
# restore.sh - Recovery script

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file>"
    exit 1
fi

# Stop services
docker-compose down

# Restore data
tar -xzf "$BACKUP_FILE"

# Restart services
docker-compose up -d

echo "Recovery completed from: $BACKUP_FILE"
```

## Updates and Maintenance

### Regular Updates

```bash
# Update application
./docker/deploy.sh update

# Update base images
docker-compose pull
docker-compose up -d

# Clean up old images
docker image prune -f
```

### Maintenance Tasks

```bash
# Weekly maintenance script
#!/bin/bash

# Clean up temporary files
find ./data/temp -type f -mtime +7 -delete

# Rotate logs
find ./logs -name "*.log" -size +100M -exec gzip {} \;

# Update containers
./docker/deploy.sh update

# Health check
./docker/validate.sh
```

## Support and Documentation

- **Docker Documentation:** `docker/README.md`
- **Application Logs:** `./logs/app.log`
- **Health Check:** `http://localhost:8080/health`
- **Configuration Validation:** `./docker/validate.sh`

For additional support, check the application logs and verify the configuration using the provided validation tools.
# Mini Video Factory Docker Deployment

This directory contains all the necessary files for deploying Mini Video Factory using Docker.

## Quick Start

1. **Copy environment configuration:**
   ```bash
   cp .env.docker .env
   ```

2. **Edit configuration:**
   ```bash
   nano .env  # Update with your actual values
   ```

3. **Deploy:**
   ```bash
   ./docker/deploy.sh
   ```

4. **Access the application:**
   Open http://localhost:8080 in your browser

## Files Overview

### Core Docker Files

- **`Dockerfile`** - Multi-stage Docker image definition
- **`docker-compose.yml`** - Service orchestration configuration
- **`.dockerignore`** - Files to exclude from Docker build context

### Configuration Files

- **`.env.docker`** - Docker environment template
- **`nginx.conf`** - Nginx reverse proxy configuration (production)

### Scripts

- **`startup.sh`** - Container startup and initialization script
- **`deploy.sh`** - Automated deployment script
- **`healthcheck.sh`** - Comprehensive health check script

## Deployment Modes

### Development Mode (Default)

```bash
./docker/deploy.sh development
```

- Single container deployment
- Direct access to Flask application
- Suitable for testing and development

### Production Mode

```bash
./docker/deploy.sh production
```

- Multi-container deployment with Nginx reverse proxy
- Load balancing and rate limiting
- SSL/TLS support (requires certificate configuration)
- Enhanced security headers

## Environment Configuration

### Required Variables

```bash
# Authentication
SECRET_KEY=your-secret-key-here
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# Storage (Optional - falls back to local storage)
WASABI_ENDPOINT=your_wasabi_endpoint
WASABI_REGION=your_wasabi_region
WASABI_BUCKET=your_bucket_name
WASABI_ACCESS_KEY_ID=your_access_key
WASABI_SECRET_ACCESS_KEY=your_secret_key
```

### Optional Variables

```bash
# Application
HOST_PORT=8080          # Host port mapping
MAX_FILE_SIZE=104857600 # 100MB file size limit
MAX_DURATION=600        # 10 minute duration limit

# Processing
WHISPER_MODEL=base      # Whisper model size
GUNICORN_WORKERS=2      # Number of worker processes

# Nginx (Production mode)
NGINX_PORT=80           # HTTP port
NGINX_SSL_PORT=443      # HTTPS port
```

## Volume Mapping

The following directories are mapped for data persistence:

- **`./data`** → `/app/data` - Uploaded and processed videos
- **`./logs`** → `/app/logs` - Application logs

## Resource Requirements

### Minimum Requirements

- **CPU:** 1 core
- **Memory:** 1GB RAM
- **Storage:** 10GB free space
- **Network:** Internet access for Supabase and Wasabi

### Recommended Requirements

- **CPU:** 2+ cores
- **Memory:** 4GB+ RAM
- **Storage:** 50GB+ free space
- **Network:** High-speed internet for video processing

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
```

### Advanced Operations

```bash
# Clean up everything
./docker/deploy.sh clean

# Manual Docker Compose commands
docker-compose up -d
docker-compose down
docker-compose logs -f mini-video-factory
```

## Monitoring and Health Checks

### Built-in Health Check

The container includes automatic health checks:

- **Endpoint:** `http://localhost:5000/health`
- **Interval:** 30 seconds
- **Timeout:** 10 seconds
- **Retries:** 3

### Manual Health Check

```bash
# Run comprehensive health check
docker exec mini-video-factory /app/docker/healthcheck.sh

# Check specific service status
curl http://localhost:8080/health
```

### Log Monitoring

```bash
# Application logs
docker-compose logs -f mini-video-factory

# Nginx logs (production mode)
docker-compose logs -f nginx

# System logs
docker exec mini-video-factory tail -f /app/logs/app.log
```

## Troubleshooting

### Common Issues

1. **Container won't start:**
   ```bash
   # Check logs
   docker-compose logs mini-video-factory
   
   # Verify environment configuration
   docker-compose config
   ```

2. **Database connection failed:**
   ```bash
   # Verify Supabase credentials
   docker exec mini-video-factory python3 -c "
   import os
   from supabase import create_client
   client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
   print('Connection successful')
   "
   ```

3. **Storage issues:**
   ```bash
   # Check disk space
   df -h ./data
   
   # Check permissions
   ls -la ./data
   ```

4. **Processing failures:**
   ```bash
   # Check tool availability
   docker exec mini-video-factory which ffmpeg
   docker exec mini-video-factory which auto-editor
   
   # Test Whisper model
   docker exec mini-video-factory python3 -c "import whisper; whisper.load_model('base')"
   ```

### Performance Tuning

1. **Increase worker processes:**
   ```bash
   # In .env file
   GUNICORN_WORKERS=4
   ```

2. **Adjust memory limits:**
   ```yaml
   # In docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 8G
   ```

3. **Enable Nginx caching:**
   ```nginx
   # Add to nginx.conf
   proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=video_cache:10m;
   ```

## Security Considerations

### Production Deployment

1. **Use strong secrets:**
   ```bash
   # Generate secure secret key
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Enable SSL/TLS:**
   - Obtain SSL certificates
   - Update nginx.conf with SSL configuration
   - Redirect HTTP to HTTPS

3. **Network security:**
   - Use firewall rules
   - Limit exposed ports
   - Consider VPN access

4. **Regular updates:**
   ```bash
   # Update base image and dependencies
   ./docker/deploy.sh update
   ```

### Data Protection

1. **Backup data directory:**
   ```bash
   tar -czf backup-$(date +%Y%m%d).tar.gz ./data ./logs
   ```

2. **Secure file permissions:**
   ```bash
   chmod 750 ./data
   chmod 640 ./logs/*.log
   ```

## Support

For issues and questions:

1. Check the application logs
2. Review the troubleshooting section
3. Verify environment configuration
4. Test individual components

## License

This Docker configuration is part of the Mini Video Factory project.
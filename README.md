# Mini Video Factory

A simple web application for automated video processing with silence removal and subtitle generation.

## Features

- **Auto-editing**: Removes silent segments using auto-editor
- **Subtitle generation**: Creates subtitles using OpenAI Whisper
- **Web interface**: Simple upload, process, and download workflow
- **Cloud storage**: Integrates with Wasabi S3-compatible storage
- **Docker deployment**: Easy deployment with Docker

## Quick Start

### Docker Deployment (Recommended)

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd mini-video-factory
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   nano .env  # Add your Supabase and Wasabi credentials
   ```

3. **Deploy**:
   ```bash
   docker-compose up -d
   ```

4. **Access**: http://localhost:8080

### Production with Domain

1. **Setup server** (Ubuntu/Debian):
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Install Nginx
   sudo apt install nginx certbot python3-certbot-nginx -y
   ```

2. **Deploy application**:
   ```bash
   git clone <repository-url>
   cd mini-video-factory
   cp .env.example .env
   nano .env  # Configure for production
   docker-compose --profile production up -d
   ```

3. **Configure Nginx**:
   ```bash
   # Copy nginx config
   sudo cp nginx.conf /etc/nginx/sites-available/mini-video-factory
   sudo ln -s /etc/nginx/sites-available/mini-video-factory /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   
   # Get SSL certificate
   sudo certbot --nginx -d your-domain.com
   ```

### Manual Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   nano .env
   ```

3. **Run**:
   ```bash
   python app.py
   ```

## Environment Variables

Required variables in `.env`:

```bash
# Application
SECRET_KEY=your-secret-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Storage (Optional - falls back to local storage)
WASABI_ENDPOINT=https://s3.region.wasabisys.com
WASABI_REGION=us-east-1
WASABI_BUCKET=your-bucket-name
WASABI_ACCESS_KEY_ID=your-access-key
WASABI_SECRET_ACCESS_KEY=your-secret-key

# Optional
HOST_PORT=8080          # External port for Docker
MAX_FILE_SIZE=104857600 # 100MB file size limit
MAX_DURATION=600        # 10 minute duration limit
```

## Management

```bash
# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down

# Update
git pull && docker-compose up -d --build
```

## Development

This project follows a spec-driven development approach. See `.kiro/specs/mini-video-factory/` for detailed requirements, design, and implementation tasks.
# Mini Video Factory 🎬

**Self-hosted video processing tool** - Remove silence + Generate subtitles automatically

Like n8n but for video processing! Deploy once, use forever.

## ⚡ Quick Start

### Option 1: One-Click VPS Deploy
```bash
curl -fsSL https://raw.githubusercontent.com/your-username/mini-video-factory/main/install.sh | bash
```

### Option 2: Railway (Easiest)
1. Fork this repo
2. Connect to [Railway](https://railway.app)
3. Add environment variables
4. Deploy!

### Option 3: Local/VPS with Docker
```bash
git clone https://github.com/your-username/mini-video-factory.git
cd mini-video-factory
cp .env.example .env
# Edit .env with your credentials
./deploy.sh production
```

## 🔧 Required Setup

### 1. Database (Supabase)
- Go to [supabase.com](https://supabase.com)
- Create project → Get URL & Key from Settings → API

### 2. Storage (Optional - Wasabi)
- Go to [wasabi.com](https://wasabi.com) 
- Create bucket → Get access keys
- *Skip this to use local storage*

## 🌍 Environment Variables

```bash
# Required
SECRET_KEY=your-secret-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Optional (for cloud storage)
WASABI_ENDPOINT=https://s3.region.wasabisys.com
WASABI_BUCKET=your-bucket
WASABI_ACCESS_KEY_ID=your-key
WASABI_SECRET_ACCESS_KEY=your-secret
```

## 📋 Management

```bash
# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Update
git pull && docker-compose up -d --build

# Stop
docker-compose down
```

## 🚀 Features

- **Auto-editing**: Removes silent segments using auto-editor
- **Subtitle generation**: Creates subtitles using OpenAI Whisper  
- **Web interface**: Simple upload, process, and download workflow
- **Cloud storage**: Integrates with Wasabi S3-compatible storage
- **Docker deployment**: Easy deployment with Docker
- **Self-hosted**: Full control over your data

## 📖 Detailed Docs

- [Deployment Guide](DEPLOYMENT.md) - Detailed setup instructions
- [Processing Guide](processing/README.md) - How video processing works

---

**Made for creators who want control over their video processing pipeline** 🎯
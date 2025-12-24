# Mini Video Factory

A self-hosted web application for automated video processing with silence removal and subtitle generation.

## Features

- **Auto-editing**: Automatically removes silent segments from videos using auto-editor
- **Subtitle generation**: Creates subtitles using OpenAI Whisper
- **Web interface**: Simple upload, process, and download workflow
- **Cloud storage**: Integrates with Wasabi S3-compatible storage
- **Docker deployment**: Easy deployment with Docker container

## Project Structure

```
mini-video-factory/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── config/               # Configuration modules
│   ├── logging.py        # Logging configuration
│   └── storage.py        # Wasabi storage configuration
├── static/               # CSS, JS, and static assets
├── templates/            # HTML templates
└── data/                 # Data directories
    ├── uploads/          # Uploaded videos
    ├── temp/             # Temporary processing files
    └── output/           # Processed videos
```

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd mini-video-factory
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase and Wasabi credentials
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run application**:
   ```bash
   python app.py
   ```

## Environment Variables

Key configuration variables in `.env`:

- `SECRET_KEY`: Flask secret key for sessions
- `SUPABASE_URL`: Supabase database URL
- `SUPABASE_KEY`: Supabase anonymous key
- `WASABI_ENDPOINT`: Wasabi storage endpoint
- `WASABI_BUCKET`: Wasabi bucket name
- `WASABI_ACCESS_KEY_ID`: Wasabi access key
- `WASABI_SECRET_ACCESS_KEY`: Wasabi secret key

## Development

This project follows a spec-driven development approach. See `.kiro/specs/mini-video-factory/` for detailed requirements, design, and implementation tasks.

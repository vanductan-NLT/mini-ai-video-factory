# Mini Video Factory Dockerfile
# Multi-stage build for optimized production image

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Essential build tools
    build-essential \
    pkg-config \
    # FFmpeg for video processing
    ffmpeg \
    # Audio processing libraries
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    # File type detection
    libmagic1 \
    # Additional video codecs and tools
    x264 \
    x265 \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data/uploads /app/data/temp /app/data/output /app/logs && \
    chown -R app:app /app

# Copy startup script
COPY docker/startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# Switch to app user
USER app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command
CMD ["/app/startup.sh"]
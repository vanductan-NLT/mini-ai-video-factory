# Mini Video Factory - Production Ready Dockerfile

FROM python:3.11-slim

# Install system dependencies including Node.js and Chromium deps
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    libmagic1 \
    curl \
    pkg-config \
    libpq-dev \
    gcc \
    g++ \
    # Remotion / Chromium dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    librandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    # Node.js setup
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Check Node version
RUN node --version && npm --version

# Set working directory
WORKDIR /app

# Upgrade pip and install wheel
RUN pip install --upgrade pip setuptools wheel

# Copy and install Python dependencies with better error handling
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=300 -r requirements.txt

# Copy application code
COPY . .

# Install Remotion dependencies
# We do this after copying code so we have the remotion-video directory
RUN cd remotion-video && npm ci && npm run build


# Copy startup script and make it executable
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Create directories as root first, then change ownership
RUN mkdir -p /app/data/uploads /app/data/temp /app/data/output /app/logs && \
    chmod -R 755 /app/data /app/logs

# Create app user and change ownership
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

# Switch to app user
USER app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start application
CMD ["/app/start.sh"]
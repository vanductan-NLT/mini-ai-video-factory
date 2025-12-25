#!/bin/bash
# Simple deployment script for Mini Video Factory MVP

set -e

echo "🚀 Mini Video Factory - Simple Deployment"
echo "========================================="

# Check if .env exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📝 Creating .env from .env.example..."
        cp .env.example .env
        echo "⚠️  Please edit .env file with your configuration:"
        echo "   - SECRET_KEY"
        echo "   - SUPABASE_URL" 
        echo "   - SUPABASE_KEY"
        echo "   - WASABI credentials (optional)"
        echo ""
        read -p "Press Enter after configuring .env file..."
    else
        echo "❌ .env.example not found!"
        exit 1
    fi
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p data/uploads data/temp data/output logs

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found! Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found! Please install Docker Compose first."
    exit 1
fi

# Deploy based on argument
case "${1:-dev}" in
    "prod"|"production")
        echo "🏭 Starting production deployment with Nginx..."
        docker-compose --profile production up -d --build
        echo ""
        echo "✅ Production deployment completed!"
        echo "🌐 Access your app at: http://localhost"
        echo "📊 Nginx reverse proxy is running"
        ;;
    *)
        echo "🔧 Starting development deployment..."
        docker-compose up -d --build
        echo ""
        echo "✅ Development deployment completed!"
        echo "🌐 Access your app at: http://localhost:8080"
        ;;
esac

echo ""
echo "📋 Management commands:"
echo "   View logs:    docker-compose logs -f"
echo "   Restart:      docker-compose restart"
echo "   Stop:         docker-compose down"
echo "   Update:       git pull && docker-compose up -d --build"
echo ""
echo "🎉 Happy video processing!"
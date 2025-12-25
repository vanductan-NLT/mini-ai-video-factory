#!/bin/bash

# Mini Video Factory - One-Click Installation Script
# Usage: curl -fsSL https://raw.githubusercontent.com/your-username/mini-video-factory/main/install.sh | bash

set -e

echo "🚀 Mini Video Factory - One-Click Installation"
echo "=============================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "⚠️  Please run this script as a regular user, not root"
   exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "🐙 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Install Nginx and Certbot
echo "🌐 Installing Nginx and SSL tools..."
sudo apt install -y nginx certbot python3-certbot-nginx

# Clone repository
echo "📥 Downloading Mini Video Factory..."
if [ -d "mini-video-factory" ]; then
    cd mini-video-factory
    git pull
else
    git clone https://github.com/your-username/mini-video-factory.git
    cd mini-video-factory
fi
# Get domain name
echo ""
read -p "🌍 Enter your domain name (e.g., yourdomain.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    echo "❌ Domain name is required"
    exit 1
fi

# Setup environment file
echo "⚙️  Setting up environment configuration..."
cp .env.example .env

# Generate secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
sed -i "s/your-secret-key-here/$SECRET_KEY/" .env

# Get Supabase credentials
echo ""
echo "📊 Supabase Database Setup"
echo "Go to https://supabase.com, create a project, then get your credentials from Settings → API"
read -p "Supabase URL: " SUPABASE_URL
read -p "Supabase Anon Key: " SUPABASE_KEY

sed -i "s|your_supabase_url|$SUPABASE_URL|" .env
sed -i "s/your_supabase_anon_key/$SUPABASE_KEY/" .env

# Optional Wasabi setup
echo ""
echo "💾 Wasabi Storage Setup (Optional - press Enter to skip)"
read -p "Wasabi Endpoint (optional): " WASABI_ENDPOINT
if [ ! -z "$WASABI_ENDPOINT" ]; then
    read -p "Wasabi Region: " WASABI_REGION
    read -p "Wasabi Bucket: " WASABI_BUCKET
    read -p "Wasabi Access Key: " WASABI_ACCESS_KEY
    read -p "Wasabi Secret Key: " WASABI_SECRET_KEY
    
    sed -i "s/your_wasabi_endpoint_here/$WASABI_ENDPOINT/" .env
    sed -i "s/your_wasabi_region_here/$WASABI_REGION/" .env
    sed -i "s/your_bucket_name_here/$WASABI_BUCKET/" .env
    sed -i "s/your_wasabi_access_key_id_here/$WASABI_ACCESS_KEY/" .env
    sed -i "s/your_wasabi_secret_access_key_here/$WASABI_SECRET_KEY/" .env
fi

# Setup Nginx configuration
echo "🌐 Setting up Nginx..."
sudo cp nginx.conf /etc/nginx/sites-available/mini-video-factory
sed -i "s/your-domain.com/$DOMAIN/g" /etc/nginx/sites-available/mini-video-factory
sudo ln -sf /etc/nginx/sites-available/mini-video-factory /etc/nginx/sites-enabled/
sudo nginx -t

# Start application
echo "🚀 Starting Mini Video Factory..."
docker-compose up -d

# Wait for application to start
echo "⏳ Waiting for application to start..."
sleep 30

# Setup SSL certificate
echo "🔒 Setting up SSL certificate..."
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# Restart Nginx
sudo systemctl restart nginx

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "🎉 Your Mini Video Factory is now running at:"
echo "   https://$DOMAIN"
echo ""
echo "📋 Management commands:"
echo "   View logs:    docker-compose logs -f"
echo "   Restart:      docker-compose restart"
echo "   Stop:         docker-compose down"
echo "   Update:       git pull && docker-compose up -d --build"
echo ""
echo "📁 Important directories:"
echo "   Data:         $(pwd)/data"
echo "   Logs:         $(pwd)/logs"
echo "   Config:       $(pwd)/.env"
echo ""
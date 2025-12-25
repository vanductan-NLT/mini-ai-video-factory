#!/bin/bash
set -e

# Mini Video Factory Docker Deployment Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are available"
}

# Check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found"
        if [ -f ".env.docker" ]; then
            print_status "Copying .env.docker to .env"
            cp .env.docker .env
            print_warning "Please edit .env file with your actual configuration values"
            return 1
        elif [ -f ".env.example" ]; then
            print_status "Copying .env.example to .env"
            cp .env.example .env
            print_warning "Please edit .env file with your actual configuration values"
            return 1
        else
            print_error "No environment template found. Please create .env file manually."
            exit 1
        fi
    fi
    
    print_success ".env file found"
    return 0
}

# Validate required environment variables
validate_env() {
    print_status "Validating environment configuration..."
    
    source .env
    
    required_vars=(
        "SECRET_KEY"
        "SUPABASE_URL"
        "SUPABASE_KEY"
    )
    
    missing_vars=()
    placeholder_vars=()
    
    for var in "${required_vars[@]}"; do
        value="${!var}"
        if [ -z "$value" ]; then
            missing_vars+=("$var")
        elif [[ "$value" == *"your_"* ]] || [[ "$value" == *"change"* ]] || [[ "$value" == *"here"* ]]; then
            placeholder_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required environment variables: ${missing_vars[*]}"
        return 1
    fi
    
    if [ ${#placeholder_vars[@]} -ne 0 ]; then
        print_warning "Placeholder values detected for: ${placeholder_vars[*]}"
        print_warning "Please update these values in .env file before deployment"
        return 1
    fi
    
    print_success "Environment configuration is valid"
    return 0
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    directories=(
        "./data"
        "./data/uploads"
        "./data/temp"
        "./data/output"
        "./logs"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "Created directory: $dir"
        fi
    done
    
    # Set proper permissions
    chmod 755 ./data ./data/uploads ./data/temp ./data/output ./logs
    
    print_success "Directories created successfully"
}

# Build and start services
deploy_services() {
    local mode=${1:-"development"}
    
    print_status "Building Docker image..."
    docker-compose build
    
    if [ "$mode" = "production" ]; then
        print_status "Starting services in production mode (with nginx)..."
        docker-compose --profile production up -d
    else
        print_status "Starting services in development mode..."
        docker-compose up -d
    fi
    
    print_success "Services started successfully"
}

# Check service health
check_health() {
    print_status "Checking service health..."
    
    # Wait for services to start
    sleep 10
    
    # Check if container is running
    if docker-compose ps | grep -q "mini-video-factory.*Up"; then
        print_success "Mini Video Factory container is running"
    else
        print_error "Mini Video Factory container is not running"
        docker-compose logs mini-video-factory
        return 1
    fi
    
    # Check health endpoint
    local port=$(grep "HOST_PORT" .env | cut -d'=' -f2 | tr -d ' ' || echo "8080")
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
            print_success "Health check passed"
            return 0
        fi
        
        print_status "Waiting for service to be ready... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    print_error "Health check failed after $max_attempts attempts"
    print_status "Container logs:"
    docker-compose logs --tail=20 mini-video-factory
    return 1
}

# Show deployment information
show_info() {
    local port=$(grep "HOST_PORT" .env | cut -d'=' -f2 | tr -d ' ' || echo "8080")
    
    print_success "Deployment completed successfully!"
    echo
    print_status "Access your Mini Video Factory at:"
    echo "  http://localhost:$port"
    echo
    print_status "Useful commands:"
    echo "  View logs:           docker-compose logs -f"
    echo "  Stop services:       docker-compose down"
    echo "  Restart services:    docker-compose restart"
    echo "  Update application:  docker-compose pull && docker-compose up -d"
    echo
    print_status "Data is persisted in:"
    echo "  ./data/    - Uploaded and processed videos"
    echo "  ./logs/    - Application logs"
}

# Main deployment function
main() {
    local mode=${1:-"development"}
    
    echo "Mini Video Factory Docker Deployment"
    echo "====================================="
    echo
    
    # Validate mode
    if [ "$mode" != "development" ] && [ "$mode" != "production" ]; then
        print_error "Invalid mode. Use 'development' or 'production'"
        exit 1
    fi
    
    print_status "Deploying in $mode mode..."
    echo
    
    # Run deployment steps
    check_docker
    
    if ! check_env_file; then
        print_error "Please configure .env file and run the script again"
        exit 1
    fi
    
    if ! validate_env; then
        print_error "Please fix environment configuration and run the script again"
        exit 1
    fi
    
    create_directories
    deploy_services "$mode"
    
    if check_health; then
        show_info
    else
        print_error "Deployment failed. Check the logs above for details."
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    "production")
        main "production"
        ;;
    "development"|"dev"|"")
        main "development"
        ;;
    "stop")
        print_status "Stopping services..."
        docker-compose down
        print_success "Services stopped"
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "restart")
        print_status "Restarting services..."
        docker-compose restart
        print_success "Services restarted"
        ;;
    "update")
        print_status "Updating application..."
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
        print_success "Application updated"
        ;;
    "clean")
        print_warning "This will remove all containers, images, and volumes"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v --rmi all
            print_success "Cleanup completed"
        fi
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  development  Deploy in development mode (default)"
        echo "  production   Deploy in production mode with nginx"
        echo "  stop         Stop all services"
        echo "  logs         Show service logs"
        echo "  restart      Restart services"
        echo "  update       Update and restart services"
        echo "  clean        Remove all containers and images"
        echo "  help         Show this help message"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
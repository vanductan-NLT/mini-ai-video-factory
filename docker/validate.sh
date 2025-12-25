#!/bin/bash
# Docker configuration validation script

set -e

echo "Validating Docker configuration for Mini Video Factory..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if Docker is available
check_docker() {
    print_status "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        return 1
    fi
    
    print_success "Docker is available and running"
    return 0
}

# Check Docker Compose
check_docker_compose() {
    print_status "Checking Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose (standalone) is available"
        return 0
    elif docker compose version &> /dev/null; then
        print_success "Docker Compose (plugin) is available"
        return 0
    else
        print_error "Docker Compose is not available"
        return 1
    fi
}

# Validate docker-compose.yml
validate_compose_file() {
    print_status "Validating docker-compose.yml..."
    
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found"
        return 1
    fi
    
    if docker-compose config &> /dev/null; then
        print_success "docker-compose.yml is valid"
        return 0
    else
        print_error "docker-compose.yml has syntax errors"
        docker-compose config
        return 1
    fi
}

# Validate Dockerfile
validate_dockerfile() {
    print_status "Validating Dockerfile..."
    
    if [ ! -f "Dockerfile" ]; then
        print_error "Dockerfile not found"
        return 1
    fi
    
    # Basic syntax check by parsing the file
    if grep -q "FROM python:" Dockerfile && grep -q "WORKDIR /app" Dockerfile; then
        print_success "Dockerfile appears to be valid"
        return 0
    else
        print_error "Dockerfile may have issues"
        return 1
    fi
}

# Check required files
check_required_files() {
    print_status "Checking required files..."
    
    local required_files=(
        "Dockerfile"
        "docker-compose.yml"
        "docker/startup.sh"
        "docker/healthcheck.sh"
        "docker/deploy.sh"
        "requirements.txt"
        "app.py"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        print_success "All required files are present"
        return 0
    else
        print_error "Missing required files: ${missing_files[*]}"
        return 1
    fi
}

# Check script permissions
check_permissions() {
    print_status "Checking script permissions..."
    
    local scripts=(
        "docker/startup.sh"
        "docker/healthcheck.sh"
        "docker/deploy.sh"
    )
    
    local non_executable=()
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ] && [ ! -x "$script" ]; then
            non_executable+=("$script")
        fi
    done
    
    if [ ${#non_executable[@]} -eq 0 ]; then
        print_success "All scripts have correct permissions"
        return 0
    else
        print_warning "Scripts need execute permissions: ${non_executable[*]}"
        print_status "Run: chmod +x ${non_executable[*]}"
        return 1
    fi
}

# Check environment configuration
check_environment() {
    print_status "Checking environment configuration..."
    
    if [ -f ".env" ]; then
        print_success ".env file exists"
        
        # Check for placeholder values
        if grep -q "your_" .env || grep -q "change" .env; then
            print_warning ".env file contains placeholder values"
            print_status "Please update .env with actual configuration values"
        else
            print_success ".env file appears to be configured"
        fi
    elif [ -f ".env.docker" ]; then
        print_warning ".env file not found, but .env.docker template exists"
        print_status "Copy .env.docker to .env and configure it"
    else
        print_error "No environment configuration found"
        return 1
    fi
    
    return 0
}

# Main validation function
main() {
    echo "Docker Configuration Validation"
    echo "==============================="
    echo
    
    local exit_code=0
    
    # Run all checks
    if ! check_docker; then
        exit_code=1
    fi
    
    if ! check_docker_compose; then
        exit_code=1
    fi
    
    if ! validate_compose_file; then
        exit_code=1
    fi
    
    if ! validate_dockerfile; then
        exit_code=1
    fi
    
    if ! check_required_files; then
        exit_code=1
    fi
    
    if ! check_permissions; then
        # Don't fail for permission issues, just warn
        print_status "Fixing permissions..."
        chmod +x docker/*.sh 2>/dev/null || true
    fi
    
    if ! check_environment; then
        # Don't fail for environment issues, just warn
        print_status "Environment configuration needs attention"
    fi
    
    echo
    if [ $exit_code -eq 0 ]; then
        print_success "All validation checks passed!"
        print_status "You can now deploy with: ./docker/deploy.sh"
    else
        print_error "Some validation checks failed"
        print_status "Please fix the issues above before deploying"
    fi
    
    return $exit_code
}

# Run validation
main "$@"
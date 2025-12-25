#!/bin/bash
# Health check script for Mini Video Factory Docker container

set -e

# Configuration
HEALTH_URL="http://localhost:5000/health"
TIMEOUT=10
MAX_RETRIES=3

# Function to check health endpoint
check_health() {
    local attempt=1
    
    while [ $attempt -le $MAX_RETRIES ]; do
        echo "Health check attempt $attempt/$MAX_RETRIES..."
        
        if curl -f -s --max-time $TIMEOUT "$HEALTH_URL" > /dev/null 2>&1; then
            echo "Health check passed"
            return 0
        fi
        
        echo "Health check failed (attempt $attempt)"
        ((attempt++))
        
        if [ $attempt -le $MAX_RETRIES ]; then
            sleep 2
        fi
    done
    
    echo "Health check failed after $MAX_RETRIES attempts"
    return 1
}

# Function to check disk space
check_disk_space() {
    local usage=$(df /app/data | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -gt 90 ]; then
        echo "WARNING: Disk usage is at ${usage}%"
        return 1
    elif [ "$usage" -gt 80 ]; then
        echo "INFO: Disk usage is at ${usage}%"
    fi
    
    return 0
}

# Function to check memory usage
check_memory() {
    local mem_info=$(cat /proc/meminfo)
    local mem_total=$(echo "$mem_info" | grep MemTotal | awk '{print $2}')
    local mem_available=$(echo "$mem_info" | grep MemAvailable | awk '{print $2}')
    local mem_used=$((mem_total - mem_available))
    local mem_percent=$((mem_used * 100 / mem_total))
    
    if [ "$mem_percent" -gt 90 ]; then
        echo "WARNING: Memory usage is at ${mem_percent}%"
        return 1
    elif [ "$mem_percent" -gt 80 ]; then
        echo "INFO: Memory usage is at ${mem_percent}%"
    fi
    
    return 0
}

# Function to check required processes
check_processes() {
    local required_processes=("python" "gunicorn")
    
    for process in "${required_processes[@]}"; do
        if ! pgrep -f "$process" > /dev/null; then
            echo "ERROR: Required process '$process' not running"
            return 1
        fi
    done
    
    echo "All required processes are running"
    return 0
}

# Main health check
main() {
    echo "Starting comprehensive health check..."
    
    local exit_code=0
    
    # Check application health endpoint
    if ! check_health; then
        exit_code=1
    fi
    
    # Check system resources
    if ! check_disk_space; then
        exit_code=1
    fi
    
    if ! check_memory; then
        exit_code=1
    fi
    
    # Check processes
    if ! check_processes; then
        exit_code=1
    fi
    
    if [ $exit_code -eq 0 ]; then
        echo "All health checks passed"
    else
        echo "Some health checks failed"
    fi
    
    return $exit_code
}

# Run health check
main "$@"
#!/bin/bash

# ================================================
# Production-ready Locust Load Test Launcher
# Tools: Locust with Enhanced Route Loading & Monitoring
# Author: M.Noermoehammad
# Version: 2.0.0
# ================================================

# Exit on any error
set -e

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VENV_DIR="venv"
LOCUST_FILE="locustfile.py"
ROUTE_FILE="routes.json"
REQUIREMENTS_FILE="loadrequirements.txt"
DEFAULT_HOST="http://localhost:8080"
DEFAULT_WEB_PORT="8089"
DEFAULT_USERS="50"
DEFAULT_SPAWN_RATE="5"

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

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is not installed or not in PATH"
        exit 1
    fi
    
    # Check Locust file exists
    if [ ! -f "$LOCUST_FILE" ]; then
        print_error "Locust file '$LOCUST_FILE' not found"
        exit 1
    fi
    
    # Check route file exists
    if [ ! -f "$ROUTE_FILE" ]; then
        print_warning "Route file '$ROUTE_FILE' not found - run export_routes.php first"
        print_status "Some features may not work without route definitions"
    else
        ROUTE_COUNT=$(jq length "$ROUTE_FILE" 2>/dev/null || echo "unknown")
        print_success "Route file found with $ROUTE_COUNT routes"
    fi
    
    print_success "Prerequisites check completed"
}

# Function to setup virtual environment
setup_venv() {
    print_status "Setting up virtual environment..."
    
    if [ ! -d "$VENV_DIR" ]; then
        print_status "Creating virtual environment in '$VENV_DIR'..."
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi

    # Activate virtual environment
    print_status "Activating virtual environment..."
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    # Install dependencies
    if [ -f "$REQUIREMENTS_FILE" ]; then
        print_status "Installing dependencies from $REQUIREMENTS_FILE..."
        pip install -r "$REQUIREMENTS_FILE"
    else
        print_warning "$REQUIREMENTS_FILE not found, installing default dependencies..."
        pip install locust beautifulsoup4
    fi
    
    print_success "Environment setup completed"
}

# Function to validate configuration
validate_config() {
    print_status "Validating configuration..."
    
    # Check if Locust file has valid syntax
    if python3 -m py_compile "$LOCUST_FILE"; then
        print_success "Locust file syntax is valid"
    else
        print_error "Locust file has syntax errors"
        exit 1
    fi
    
    # Validate route file if it exists
    if [ -f "$ROUTE_FILE" ]; then
        if python3 -c "import json; json.load(open('$ROUTE_FILE'))"; then
            print_success "Route file JSON syntax is valid"
        else
            print_error "Route file has invalid JSON"
            exit 1
        fi
    fi
}

# Function to display configuration summary
show_config() {
    echo
    echo "================================================"
    echo "PRODUCTION LOAD TEST CONFIGURATION"
    echo "================================================"
    echo "  Virtual Environment: $VENV_DIR"
    echo "  Locust File: $LOCUST_FILE"
    echo "  Route File: $ROUTE_FILE"
    echo "  Target Host: $TARGET_HOST"
    echo "  Web Interface: http://localhost:$WEB_PORT"
    echo "  Default Users: $USERS"
    echo "  Default Spawn Rate: $SPAWN_RATE"
    echo "================================================"
    echo
}

# Function to run pre-flight checks
pre_flight_checks() {
    print_status "Running pre-flight checks..."
    
    # Test if target host is reachable (optional)
    if command -v curl &> /dev/null; then
        print_status "Testing connection to $TARGET_HOST..."
        if curl -s --head --connect-timeout 5 "$TARGET_HOST" > /dev/null; then
            print_success "Target host is reachable"
        else
            print_warning "Target host may not be reachable - check your URL"
        fi
    fi
    
    # Check available memory
    if command -v free &> /dev/null; then
        MEM_AVAILABLE=$(free -m | awk 'NR==2{print $7}')
        print_status "Available memory: ${MEM_AVAILABLE}MB"
        
        if [ "$MEM_AVAILABLE" -lt 500 ]; then
            print_warning "Low memory available - consider closing other applications"
        fi
    fi
}

# Function to start Locust
start_locust() {
    print_status "Starting Locust load test..."
    echo
    print_success "Target: $TARGET_HOST"
    print_success "Dashboard: http://localhost:$WEB_PORT"
    print_success "Press Ctrl+C to stop the test"
    echo
    print_warning "Note: Open the dashboard URL in your browser to control the test"
    echo
    
    # Construct Locust command
    LOCUST_CMD="locust -f $LOCUST_FILE --host=$TARGET_HOST --web-host=0.0.0.0 --web-port=$WEB_PORT"
    
    # Add tags filter if specified
    if [ -n "$TAGS" ]; then
        LOCUST_CMD="$LOCUST_CMD --tags $TAGS"
        print_status "Filtering tests by tags: $TAGS"
    fi
    
    # Add exclude tags if specified
    if [ -n "$EXCLUDE_TAGS" ]; then
        LOCUST_CMD="$LOCUST_CMD --exclude-tags $EXCLUDE_TAGS"
        print_status "Excluding tests with tags: $EXCLUDE_TAGS"
    fi
    
    print_status "Command: $LOCUST_CMD"
    echo
    
    # Execute Locust
    eval "$LOCUST_CMD"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --host HOST        Target host URL (default: $DEFAULT_HOST)"
    echo "  -p, --port PORT        Web interface port (default: $DEFAULT_WEB_PORT)"
    echo "  -u, --users USERS      Number of users (default: $DEFAULT_USERS)"
    echo "  -r, --spawn-rate RATE  Spawn rate (default: $DEFAULT_SPAWN_RATE)"
    echo "  -t, --tags TAGS        Run only tasks with these tags (comma-separated)"
    echo "  -x, --exclude-tags TAGS Exclude tasks with these tags (comma-separated)"
    echo "  --headless            Run in headless mode without web UI"
    echo "  --check-only          Only check configuration without running"
    echo "  --help                Show this help message"
    echo
    echo "Examples:"
    echo "  $0 --host https://staging.example.com"
    echo "  $0 --host https://prod.example.com --users 100 --spawn-rate 10"
    echo "  $0 --tags admin --port 9090"
    echo "  $0 --exclude-tags admin --tags browse,public"
    echo
}

# Parse command line arguments
TARGET_HOST="$DEFAULT_HOST"
WEB_PORT="$DEFAULT_WEB_PORT"
USERS="$DEFAULT_USERS"
SPAWN_RATE="$DEFAULT_SPAWN_RATE"
TAGS=""
EXCLUDE_TAGS=""
HEADLESS=false
CHECK_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            TARGET_HOST="$2"
            shift 2
            ;;
        -p|--port)
            WEB_PORT="$2"
            shift 2
            ;;
        -u|--users)
            USERS="$2"
            shift 2
            ;;
        -r|--spawn-rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        -t|--tags)
            TAGS="$2"
            shift 2
            ;;
        -x|--exclude-tags)
            EXCLUDE_TAGS="$2"
            shift 2
            ;;
        --headless)
            HEADLESS=true
            shift
            ;;
        --check-only)
            CHECK_ONLY=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    echo
    print_status " Starting Production Locust Load Test"
    echo "================================================"
    
    # Run checks and setup
    check_prerequisites
    setup_venv
    validate_config
    pre_flight_checks
    
    if [ "$CHECK_ONLY" = true ]; then
        print_success "Configuration check completed successfully"
        exit 0
    fi
    
    show_config
    
    # Wait for user confirmation if not headless
    if [ "$HEADLESS" = false ]; then
        read -r -p "Press Enter to start Locust or Ctrl+C to cancel..."
    fi
    
    start_locust
}

# Handle script interruption
cleanup() {
    echo
    print_status "Cleaning up..."
    deactivate 2>/dev/null || true
    print_success "Load test completed"
}

trap cleanup EXIT

# Run main function
main "$@"
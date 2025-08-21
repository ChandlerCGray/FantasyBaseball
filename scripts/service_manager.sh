#!/bin/bash

# Fantasy Baseball Service Manager
# Usage: ./service_manager.sh [install|start|stop|restart|status|enable|disable|logs]

SERVICE_NAME="fantasy-baseball"
SERVICE_FILE="fantasy-baseball.service"
PROJECT_DIR="/home/chandlergray/FantasyBaseball"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== Fantasy Baseball Service Manager ===${NC}"
}

# Check if running as root for system operations
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root"
        exit 1
    fi
}

# Install the service
install_service() {
    print_header
    print_status "Installing Fantasy Baseball service..."
    
    # Check if service file exists
    if [[ ! -f "$SERVICE_FILE" ]]; then
        print_error "Service file $SERVICE_FILE not found in current directory"
        exit 1
    fi
    
    # Copy service file to systemd directory
    sudo cp "$SERVICE_FILE" /etc/systemd/system/
    sudo systemctl daemon-reload
    
    print_status "Service installed successfully"
    print_status "Use 'sudo systemctl enable $SERVICE_NAME' to enable auto-start"
    print_status "Use 'sudo systemctl start $SERVICE_NAME' to start the service"
}

# Start the service
start_service() {
    print_header
    print_status "Starting Fantasy Baseball service..."
    sudo systemctl start "$SERVICE_NAME"
    
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Service started successfully"
        print_status "Access the dashboard at: http://localhost:8000"
    else
        print_error "Failed to start service"
        sudo systemctl status "$SERVICE_NAME" --no-pager -l
    fi
}

# Stop the service
stop_service() {
    print_header
    print_status "Stopping Fantasy Baseball service..."
    sudo systemctl stop "$SERVICE_NAME"
    
    if ! sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Service stopped successfully"
    else
        print_error "Failed to stop service"
        sudo systemctl status "$SERVICE_NAME" --no-pager -l
    fi
}

# Restart the service
restart_service() {
    print_header
    print_status "Restarting Fantasy Baseball service..."
    sudo systemctl restart "$SERVICE_NAME"
    
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Service restarted successfully"
        print_status "Access the dashboard at: http://localhost:8000"
    else
        print_error "Failed to restart service"
        sudo systemctl status "$SERVICE_NAME" --no-pager -l
    fi
}

# Check service status
status_service() {
    print_header
    print_status "Fantasy Baseball service status:"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
    
    echo ""
    print_status "Recent logs:"
    sudo journalctl -u "$SERVICE_NAME" --no-pager -l -n 20
}

# Enable service to start on boot
enable_service() {
    print_header
    print_status "Enabling Fantasy Baseball service to start on boot..."
    sudo systemctl enable "$SERVICE_NAME"
    print_status "Service enabled successfully"
}

# Disable service from starting on boot
disable_service() {
    print_header
    print_status "Disabling Fantasy Baseball service from starting on boot..."
    sudo systemctl disable "$SERVICE_NAME"
    print_status "Service disabled successfully"
}

# Show service logs
show_logs() {
    print_header
    print_status "Showing Fantasy Baseball service logs:"
    sudo journalctl -u "$SERVICE_NAME" --no-pager -l -f
}

# Show usage
show_usage() {
    print_header
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  install   - Install the service file"
    echo "  start     - Start the service"
    echo "  stop      - Stop the service"
    echo "  restart   - Restart the service"
    echo "  status    - Show service status and recent logs"
    echo "  enable    - Enable service to start on boot"
    echo "  disable   - Disable service from starting on boot"
    echo "  logs      - Show live service logs"
    echo ""
    echo "Examples:"
    echo "  $0 install   # Install the service"
    echo "  $0 start     # Start the service"
    echo "  $0 status    # Check service status"
}

# Main script logic
case "${1:-}" in
    install)
        check_root
        install_service
        ;;
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    enable)
        enable_service
        ;;
    disable)
        disable_service
        ;;
    logs)
        show_logs
        ;;
    *)
        show_usage
        exit 1
        ;;
esac

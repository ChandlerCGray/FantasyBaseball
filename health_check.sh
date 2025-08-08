#!/bin/bash

# Fantasy Baseball Hub Health Check Script

APP_URL="http://localhost:8501"
SERVICE_NAME="fantasy-baseball.service"
LOG_FILE="/tmp/fantasy_baseball_health.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

# Check if service is running
check_service() {
    if systemctl is-active --quiet $SERVICE_NAME; then
        log_message "✅ Service is running"
        return 0
    else
        log_message "❌ Service is not running"
        return 1
    fi
}

# Check if app is responding
check_app() {
    if curl -s --max-time 10 $APP_URL > /dev/null; then
        log_message "✅ App is responding on $APP_URL"
        return 0
    else
        log_message "❌ App is not responding on $APP_URL"
        return 1
    fi
}

# Main health check
log_message "Starting health check..."

service_ok=false
app_ok=false

if check_service; then
    service_ok=true
fi

if check_app; then
    app_ok=true
fi

# Summary
if $service_ok && $app_ok; then
    log_message "🎉 All systems operational!"
    exit 0
else
    log_message "⚠️  Issues detected - check logs for details"
    exit 1
fi

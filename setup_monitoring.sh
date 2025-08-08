#!/bin/bash

# Setup automated monitoring for Fantasy Baseball Hub

SCRIPT_DIR="/home/chandlergray/FantasyBaseball"
HEALTH_CHECK="$SCRIPT_DIR/health_check.sh"
MANAGE_SCRIPT="$SCRIPT_DIR/manage_app.sh"

echo "Setting up automated monitoring for Fantasy Baseball Hub..."

# Create a monitoring script that restarts the service if health check fails
cat > /tmp/fantasy_baseball_monitor.sh << 'EOF'
#!/bin/bash

# Fantasy Baseball Hub Auto-Restart Monitor
SERVICE_NAME="fantasy-baseball.service"
HEALTH_CHECK="/home/chandlergray/FantasyBaseball/health_check.sh"
MANAGE_SCRIPT="/home/chandlergray/FantasyBaseball/manage_app.sh"
LOG_FILE="/tmp/fantasy_baseball_monitor.log"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

# Run health check
if ! $HEALTH_CHECK > /dev/null 2>&1; then
    log_message "Health check failed - restarting service..."
    $MANAGE_SCRIPT restart
    sleep 30
    
    # Check again after restart
    if $HEALTH_CHECK > /dev/null 2>&1; then
        log_message "Service restarted successfully"
    else
        log_message "Service restart failed - manual intervention required"
    fi
else
    log_message "Health check passed - service is healthy"
fi
EOF

chmod +x /tmp/fantasy_baseball_monitor.sh

# Add cron job to run health check every 5 minutes
(crontab -l 2>/dev/null; echo "*/5 * * * * /tmp/fantasy_baseball_monitor.sh") | crontab -

# Add cron job to update data daily at 6 AM
(crontab -l 2>/dev/null; echo "0 6 * * * $MANAGE_SCRIPT update") | crontab -

echo "✅ Monitoring setup complete!"
echo ""
echo "Cron jobs added:"
echo "  - Health check every 5 minutes"
echo "  - Data update daily at 6 AM"
echo ""
echo "Monitor logs:"
echo "  - Health check: tail -f /tmp/fantasy_baseball_health.log"
echo "  - Monitor: tail -f /tmp/fantasy_baseball_monitor.log"
echo "  - Service: sudo journalctl -u fantasy-baseball.service -f"

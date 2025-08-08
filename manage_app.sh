#!/bin/bash

# Fantasy Baseball Hub Management Script
# Usage: ./manage_app.sh [start|stop|restart|status|logs|update]

SERVICE_NAME="fantasy-baseball.service"
APP_DIR="/home/chandlergray/FantasyBaseball"

case "$1" in
    start)
        echo "Starting Fantasy Baseball Hub..."
        sudo systemctl start $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    stop)
        echo "Stopping Fantasy Baseball Hub..."
        sudo systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo "Restarting Fantasy Baseball Hub..."
        sudo systemctl restart $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    status)
        echo "Fantasy Baseball Hub Status:"
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    logs)
        echo "Fantasy Baseball Hub Logs:"
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    update)
        echo "Updating Fantasy Baseball data..."
        cd $APP_DIR
        source venv/bin/activate
        cd src
        PYTHONPATH=$APP_DIR/src python main.py
        echo "Data update complete!"
        ;;
    enable)
        echo "Enabling Fantasy Baseball Hub to start on boot..."
        sudo systemctl enable $SERVICE_NAME
        ;;
    disable)
        echo "Disabling Fantasy Baseball Hub from starting on boot..."
        sudo systemctl disable $SERVICE_NAME
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|update|enable|disable}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the Fantasy Baseball Hub"
        echo "  stop    - Stop the Fantasy Baseball Hub"
        echo "  restart - Restart the Fantasy Baseball Hub"
        echo "  status  - Show current status"
        echo "  logs    - Show live logs"
        echo "  update  - Update fantasy baseball data"
        echo "  enable  - Enable auto-start on boot"
        echo "  disable - Disable auto-start on boot"
        echo ""
        echo "App URLs:"
        echo "  Local:  http://localhost:8501"
        echo "  Network: http://192.168.0.46:8501"
        exit 1
        ;;
esac

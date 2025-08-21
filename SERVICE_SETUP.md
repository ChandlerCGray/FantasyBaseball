# Fantasy Baseball Service Setup

This guide will help you set up your Fantasy Baseball dashboard as a systemd service that runs automatically in the background.

## Prerequisites

- Python virtual environment is set up and dependencies are installed
- The application runs successfully when started manually
- You have sudo privileges on the system

## Quick Setup

1. **Install the service:**
   ```bash
   ./scripts/service_manager.sh install
   ```

2. **Start the service:**
   ```bash
   ./scripts/service_manager.sh start
   ```

3. **Enable auto-start on boot (optional):**
   ```bash
   ./scripts/service_manager.sh enable
   ```

## Service Management Commands

The service manager script provides several commands for managing your Fantasy Baseball service:

### Basic Commands
- `./scripts/service_manager.sh install` - Install the service file
- `./scripts/service_manager.sh start` - Start the service
- `./scripts/service_manager.sh stop` - Stop the service
- `./scripts/service_manager.sh restart` - Restart the service
- `./scripts/service_manager.sh status` - Show service status and recent logs

### Advanced Commands
- `./scripts/service_manager.sh enable` - Enable service to start on boot
- `./scripts/service_manager.sh disable` - Disable service from starting on boot
- `./scripts/service_manager.sh logs` - Show live service logs

## Manual Systemd Commands

You can also use standard systemd commands directly:

```bash
# Check service status
sudo systemctl status fantasy-baseball

# Start the service
sudo systemctl start fantasy-baseball

# Stop the service
sudo systemctl stop fantasy-baseball

# Restart the service
sudo systemctl restart fantasy-baseball

# Enable auto-start
sudo systemctl enable fantasy-baseball

# Disable auto-start
sudo systemctl disable fantasy-baseball

# View logs
sudo journalctl -u fantasy-baseball -f
```

## Service Configuration

The service is configured with the following settings:

- **User**: chandlergray
- **Working Directory**: /home/chandlergray/FantasyBaseball
- **Port**: 8000
- **Address**: 0.0.0.0 (accessible from any IP)
- **Auto-restart**: Enabled with 10-second delay
- **Security**: Restricted permissions and sandboxing

## Accessing the Dashboard

Once the service is running, you can access your Fantasy Baseball dashboard at:

- **Local**: http://localhost:8000
- **Network**: http://YOUR_SERVER_IP:8000

## Troubleshooting

### Service Won't Start

1. Check the service status:
   ```bash
   ./scripts/service_manager.sh status
   ```

2. View detailed logs:
   ```bash
   ./scripts/service_manager.sh logs
   ```

3. Common issues:
   - Virtual environment not found
   - Port 8000 already in use
   - Missing dependencies
   - Permission issues

### Port Already in Use

If port 8000 is already in use, you can modify the service file:

1. Edit `fantasy-baseball.service`
2. Change the port in the ExecStart line
3. Reinstall the service:
   ```bash
   ./scripts/service_manager.sh install
   ```

### Virtual Environment Issues

Make sure your virtual environment is properly set up:

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test the app manually
streamlit run src/main_app.py
```

## Security Considerations

The service is configured with several security measures:

- Runs as a non-root user
- Restricted file system access
- No new privileges
- Private temporary directories
- Protected system directories

## Monitoring

You can monitor the service using:

```bash
# Real-time logs
sudo journalctl -u fantasy-baseball -f

# Recent logs
sudo journalctl -u fantasy-baseball --no-pager -l -n 50

# Service status
sudo systemctl status fantasy-baseball
```

## Updating the Service

When you update your application:

1. Stop the service:
   ```bash
   ./scripts/service_manager.sh stop
   ```

2. Update your code

3. Restart the service:
   ```bash
   ./scripts/service_manager.sh restart
   ```

## Uninstalling the Service

To completely remove the service:

```bash
# Stop and disable the service
sudo systemctl stop fantasy-baseball
sudo systemctl disable fantasy-baseball

# Remove the service file
sudo rm /etc/systemd/system/fantasy-baseball.service

# Reload systemd
sudo systemctl daemon-reload
```

# Fantasy Baseball Hub - 24/7 Production Setup

Your Fantasy Baseball Hub is now configured to run 24/7 with automatic monitoring and recovery!

## 🚀 Current Status

- ✅ **Service**: Running as systemd service
- ✅ **Auto-start**: Enabled on boot
- ✅ **Monitoring**: Health checks every 5 minutes
- ✅ **Auto-recovery**: Automatic restart on failure
- ✅ **Data updates**: Daily at 6 AM

## 📍 Access URLs

- **Local**: http://localhost:8501
- **Network**: http://192.168.0.46:8501
- **External**: http://47.41.83.158:8501

## 🛠️ Management Commands

### Quick Commands
```bash
# Check status
./manage_app.sh status

# View logs
./manage_app.sh logs

# Restart app
./manage_app.sh restart

# Update data manually
./manage_app.sh update
```

### Service Control
```bash
# Start the service
sudo systemctl start fantasy-baseball.service

# Stop the service
sudo systemctl stop fantasy-baseball.service

# Restart the service
sudo systemctl restart fantasy-baseball.service

# Check status
sudo systemctl status fantasy-baseball.service

# View logs
sudo journalctl -u fantasy-baseball.service -f
```

## 📊 Monitoring

### Health Check
```bash
# Run health check manually
./health_check.sh

# View health check logs
tail -f /tmp/fantasy_baseball_health.log
```

### Auto-Monitoring
- **Health checks**: Every 5 minutes
- **Auto-restart**: If health check fails
- **Data updates**: Daily at 6 AM
- **Logs**: All activities logged

### View Monitoring Logs
```bash
# Health check history
tail -f /tmp/fantasy_baseball_health.log

# Monitor activity
tail -f /tmp/fantasy_baseball_monitor.log

# Service logs
sudo journalctl -u fantasy-baseball.service -f
```

## 🔧 Configuration

### Environment Variables
The app uses your ESPN credentials from `.env`:
- `LEAGUE_ID=762334118`
- `SEASON=2025`
- `SWID` and `ESPN_S2` cookies

**✅ Real Data**: The app is now connected to live ESPN and FanGraphs data!
- **ESPN**: 3,427 players from your league
- **FanGraphs**: 5,534 batters and 6,196 pitchers with projections
- **Data Size**: ~32MB of comprehensive fantasy baseball data

### Service Configuration
- **User**: chandlergray
- **Working Directory**: /home/chandlergray/FantasyBaseball
- **Port**: 8501
- **Auto-restart**: Always
- **Restart delay**: 10 seconds

## 📈 Features Available

1. **Add/Drop Recommendations** - Smart roster upgrades
2. **Best Free Agents** - Top available players
3. **Drop Candidates** - Underperforming players
4. **Team Analysis** - Team strength insights
5. **Player Comparison** - Side-by-side stats
6. **Draft Strategy** - Interactive draft board
7. **Waiver Trends** - Player movement tracking
8. **League Analysis** - Competitive insights

## 🔄 Data Updates

### Automatic Updates
- **Daily at 6 AM**: Fresh ESPN and FanGraphs data
- **Manual updates**: Use "Update Data" button in app
- **Command line**: `./manage_app.sh update`

**Latest Data**: Updated on 2025-08-08 16:02
- **ESPN Players**: 3,427 (rostered + free agents)
- **FanGraphs Batters**: 5,534 with projections
- **FanGraphs Pitchers**: 6,196 with projections
- **Total Data**: Comprehensive fantasy baseball analysis

### Data Sources
- **ESPN Fantasy**: Live league rosters and settings
- **FanGraphs**: Professional projections and stats
- **Local storage**: CSV files in `output/` directory

## 🚨 Troubleshooting

### If the app stops responding:
1. Check service status: `./manage_app.sh status`
2. View logs: `./manage_app.sh logs`
3. Restart manually: `./manage_app.sh restart`

### If health checks fail:
1. Check health logs: `tail -f /tmp/fantasy_baseball_health.log`
2. Check monitor logs: `tail -f /tmp/fantasy_baseball_monitor.log`
3. Restart service: `sudo systemctl restart fantasy-baseball.service`

### If data is stale:
1. Update manually: `./manage_app.sh update`
2. Check ESPN credentials in `.env`
3. Verify network connectivity

## 📝 Log Locations

- **Service logs**: `sudo journalctl -u fantasy-baseball.service`
- **Health checks**: `/tmp/fantasy_baseball_health.log`
- **Monitor activity**: `/tmp/fantasy_baseball_monitor.log`
- **Cron logs**: Check system cron logs

## 🔒 Security Notes

- Service runs as user `chandlergray`
- App accessible on localhost and network
- ESPN credentials stored in `.env` file
- No external authentication required

## 🎯 Next Steps

1. **Test the app**: Visit http://localhost:8501
2. **Configure alerts**: Set up notifications for failures
3. **Monitor usage**: Check logs for performance
4. **Update data**: Use the app's update button
5. **Customize**: Modify analysis parameters as needed

---

**Your Fantasy Baseball Hub is now running 24/7! 🎉**

The app will automatically:
- Start on boot
- Monitor its own health
- Restart if it fails
- Update data daily
- Log all activities

Enjoy your data-driven fantasy baseball analysis!

# Fantasy Baseball Hub — Setup Guide

## Prerequisites

- Python 3.10+ (3.12 recommended)
- Git
- An ESPN Fantasy Baseball account with access to a private or public league

## Installation

### 1. Clone and navigate

```bash
git clone <your-repo-url>
cd FantasyBaseball
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create environment file

```bash
cp env.example .env
```

Edit `.env` with your ESPN credentials:

```bash
LEAGUE_ID=your_league_id_here
SEASON=2026
SWID={your_swid_cookie_here}
ESPN_S2=your_espn_s2_cookie_here
```

### 5. Get ESPN credentials

#### Browser method
1. Go to [ESPN Fantasy Baseball](https://www.espn.com/fantasy/baseball/) and log in
2. Navigate to your league
3. Open Developer Tools (F12) → **Application** → **Cookies** → **espn.com**
4. Copy:
   - `SWID` — looks like `{GUID-GUID-GUID}`
   - `espn_s2` — a long encoded string

#### Helper script
```bash
python scripts/update_credentials.py
```

### 6. Getting your League ID

Look at your ESPN league URL:
```
https://fantasy.espn.com/baseball/team?leagueId=123456789&teamId=1
```
The number after `leagueId=` is your League ID.

### 7. Create output directory

```bash
mkdir -p output
```

### 8. Launch the application

```bash
# Option A: direct uvicorn (recommended)
source venv/bin/activate
uvicorn src.server.main:app --host 0.0.0.0 --port 8000

# Option B: helper script
./start
```

The app will be available at:
- **Local**: http://localhost:8000
- **Network**: http://your-ip:8000

## Running as a systemd service

A `fantasy-baseball.service` unit file is included for running the app persistently on Linux.

1. Copy the unit file and reload systemd:
   ```bash
   sudo cp fantasy-baseball.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable fantasy-baseball
   sudo systemctl start fantasy-baseball
   ```

2. Check status:
   ```bash
   sudo systemctl status fantasy-baseball
   journalctl -u fantasy-baseball -f
   ```

## Automated data refresh

To keep data fresh without manual clicks, add a cron job that hits the update endpoint:

```bash
# Example: refresh at 3:20 AM daily
20 3 * * * curl -s -X POST http://localhost:8000/update
```

## Environment variables

| Variable    | Description                     | Example            |
|-------------|----------------------------------|--------------------|
| `LEAGUE_ID` | Your ESPN league ID              | `123456789`        |
| `SEASON`    | Fantasy season year              | `2026`             |
| `SWID`      | ESPN SWID cookie                 | `{GUID}`           |
| `ESPN_S2`   | ESPN S2 cookie                   | `encoded_string`   |

## Troubleshooting

### "No module named 'unidecode'"
```bash
pip install unidecode
```

### "No module named 'espn_api'"
```bash
pip install espn-api
```

### "No data available for this view."
- Confirm the `output/` directory exists and contains `free_agents_ranked_*.csv` files
- Click **Update Data** in the sidebar to pull fresh data
- Check that your ESPN credentials are correct and not expired

### ESPN authentication errors
- **Cookies expired**: grab fresh cookies from your browser (they expire periodically)
- **Wrong League ID**: verify the `leagueId=` value in your ESPN league URL
- **Wrong season**: update `SEASON` in `.env` to the current year
- **Private league**: ensure your ESPN account has access to the league

## File structure

```
FantasyBaseball/
├── src/
│   ├── server/main.py           # FastAPI app and all routes
│   ├── app_pages/               # Page-level rendering modules
│   ├── analysis.py              # Statistical analysis
│   ├── config.py                # Constants
│   ├── data_utils.py            # Data loading utilities
│   ├── draft_strategy_generator.py
│   ├── espn_data.py             # ESPN API integration
│   └── fangraphs_api.py         # FanGraphs API integration
├── templates/                   # Jinja2 HTML templates
├── static/css/base.css          # Global dark theme CSS
├── output/                      # Generated CSVs and Excel draft files
├── scripts/
│   └── update_credentials.py
├── .env                         # Your credentials (not committed)
├── env.example                  # Credential template
├── requirements.txt
├── start                        # uvicorn launcher
├── fantasy-baseball.service     # systemd unit file
└── docs/
    ├── SETUP.md                 # This file
    └── API.md                   # Developer reference
```

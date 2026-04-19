# Fantasy Baseball Hub - Setup Guide

## Prerequisites

- Python 3.10+
- Git
- ESPN Fantasy Baseball account access to your league

## Installation

### 1. Clone and enter project

```bash
git clone <your-repo-url>
cd FantasyBaseball
```

### 2. Create and activate virtualenv

```bash
python3 -m venv venv
source venv/bin/activate
# Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create `.env`

```bash
cp env.example .env
```

Set required values:

```bash
LEAGUE_ID=123456789
SEASON=2026
SWID={YOUR-SWID}
ESPN_S2=your_espn_s2_cookie
```

Optional app config:

```bash
DEFAULT_TEAM=My Team Name
PROJECTION_MODEL=steamer
DEBUG=False
LOG_LEVEL=INFO
```

### 5. Get ESPN cookies (`SWID`, `ESPN_S2`)

Browser method:
1. Sign in at https://www.espn.com/fantasy/baseball/
2. Open your league page
3. Open DevTools -> Application -> Cookies -> `espn.com`
4. Copy `SWID` and `espn_s2`

Helper script (updates `.env` in place):

```bash
python scripts/update_credentials.py
```

### 6. Find your `LEAGUE_ID`

From your league URL:

```text
https://fantasy.espn.com/baseball/team?leagueId=123456789&teamId=1
```

`123456789` is your `LEAGUE_ID`.

### 7. Start the app

```bash
# Option A
uvicorn src.server.main:app --host 0.0.0.0 --port 8000

# Option B (activates venv if present, runs with --reload)
./start
```

App URLs:
- Local: http://localhost:8000
- LAN: http://<your-ip>:8000

## First data refresh

If no CSV exists yet, pages will show `no_data`. Generate data once:

```bash
python src/main.py
```

Or use the UI button / endpoint after startup:

```bash
curl -X POST http://localhost:8000/update
```

## Automated refresh (cron example)

```bash
# Daily at 3:20 AM
20 3 * * * curl -s -X POST http://localhost:8000/update
```

## systemd note

`fantasy-baseball.service` is included as a sample, but it contains machine-specific paths/user values. Update `User`, `Group`, `WorkingDirectory`, and `ExecStart` for your host before enabling it.

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `LEAGUE_ID` | Yes | ESPN league ID |
| `SEASON` | Yes | Season year (for example `2026`) |
| `SWID` | Yes | ESPN `SWID` cookie |
| `ESPN_S2` | Yes | ESPN `espn_s2` cookie |
| `DEFAULT_TEAM` | No | Default selected team in UI |
| `PROJECTION_MODEL` | No | One of: `steamer`, `zips`, `thebat`, `thebatx`, `atc`, `fangraphsdc` |
| `DEBUG` | No | App/debug flag used by local config |
| `LOG_LEVEL` | No | Logging level for scripts/config |

## Troubleshooting

### `No data available for this view`

- Ensure `output/free_agents_ranked_*.csv` exists
- Run `python src/main.py` or `POST /update`
- Verify `.env` credentials are valid

### ESPN auth failures

- Cookies expired: refresh `SWID` / `ESPN_S2`
- Wrong `LEAGUE_ID`: re-check ESPN URL
- Wrong `SEASON`: use current fantasy season
- Account access: confirm your ESPN login can view the league

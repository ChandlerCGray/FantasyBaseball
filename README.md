# Fantasy Baseball Hub

A comprehensive, interactive fantasy baseball analysis platform that combines ESPN league data with FanGraphs projections to deliver recommendations, an interactive draft board, and detailed player analytics.

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd FantasyBaseball
   ```

2. **Set up the environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp env.example .env
   # Edit .env with your ESPN credentials
   mkdir -p output
   ```

3. **Launch the application**
   ```bash
   # Recommended
   source venv/bin/activate
   uvicorn src.server.main:app --host 0.0.0.0 --port 8000

   # Or via helper script
   ./start
   ```

4. **Open in your browser**
   - Local: http://localhost:8000
   - Network: http://your-ip:8000

**For detailed setup instructions, see [docs/SETUP.md](docs/SETUP.md)**

## Pages

### Dashboard (`/`)
Position-by-position strength overview for your team. Each position card shows your team's composite score vs. the league average, a +/- percentage badge, player count, and your best/worst player. Links directly to filtered roster and upgrade views per position.

### Add/Drop (`/add-drop`)
Free agent rankings sorted by projected composite score. Filter by position to find targeted upgrades for your roster.

### My Team (`/team`)
Your full roster with projected and current composite scores. Filter by position tab. Each row links to the player detail page and has a "vs" shortcut for head-to-head comparison, plus a "Find upgrade" link to the relevant Add/Drop filter.

### All Players (`/players`)
Paginated table of every player in the league (25–200 per page). Filter by name search, position, roster status (free agent or specific team), and sort by projected score, current score, or name.

### Compare (`/compare`)
Side-by-side comparison of any two players by name. Shows team, position, projected composite score, and current composite score.

### Draft Board (`/draft`)
Full interactive draft interface:
- **Position filter tabs**: All, Hitters, Pitchers, C, 1B, 2B, 3B, SS, OF, MI, CI, UTIL, SP, RP, P
- **Tier filter**: dropdown to narrow by tier
- **Player search**: filter by name within the board
- **Position Supply panel**: shows available players vs. league demand per position
- **Draft actions**: click to pick, skip, or undo picks
- **Compact / Show Drafted toggles**: clean up the view mid-draft
- **Persistent state**: draft progress auto-saves to an Excel file in `output/`
- **Regenerate**: re-rank players based on current board state

Player columns: Rank, Player, Pos, Tier, ADP, Rec, Norm, Par

### League (`/league`)
All teams ranked by average projected composite score, with average current score alongside. Click any team to drill into their full roster breakdown (`/league/team`).

## Sidebar & Filters

The collapsible sidebar (toggle with the filter icon on mobile) is present on every page:
- **Data file**: shows which timestamped CSV is currently loaded
- **Team selector**: switch between any of the 10 league teams
- **Hide Injured**: toggle to exclude injured players from all views
- **Update Data**: triggers a live refresh from ESPN and FanGraphs APIs

## Technology Stack

- **Backend**: FastAPI + Jinja2 (server-rendered HTML)
- **Data Processing**: Pandas, NumPy
- **APIs**: ESPN Fantasy Baseball API (via `espn-api`), FanGraphs
- **Frontend**: Custom CSS (dark IDE theme), vanilla JS
- **Data Storage**: CSV files (`output/`), Excel export for draft state

## Configuration

Create a `.env` file from `env.example`:

```bash
LEAGUE_ID=your_league_id
SEASON=2026
SWID={your_swid_cookie}
ESPN_S2=your_espn_s2_cookie
```

### Getting ESPN Credentials

1. Go to ESPN Fantasy Baseball and log in to your league
2. Open Developer Tools (F12) → Application → Cookies → espn.com
3. Copy `SWID` (looks like `{GUID}`) and `espn_s2` (long encoded string)

Or use the helper:
```bash
python scripts/update_credentials.py
```

### Getting Your League ID

Look at your ESPN league URL: `https://fantasy.espn.com/baseball/team?leagueId=123456789`
The number after `leagueId=` is your League ID.

## Data Sources

- **ESPN Fantasy**: Live league rosters, player ownership, team assignments
- **FanGraphs**: Season projections and current stats
- **Data refresh**: Click "Update Data" in the sidebar, or automate with a cron job pointing at `POST /update`

## Acknowledgements

Special thanks to the open-source `espn-api` project by cwendt94, which makes interacting with ESPN Fantasy data easier. See [espn-api on GitHub](https://github.com/cwendt94/espn-api).

## License

MIT License

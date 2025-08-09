# Fantasy Baseball Hub API Documentation

This document provides an overview of the key modules and functions in the Fantasy Baseball Hub application.

## Core Modules

### `src/server/main.py`
FastAPI application and routes for the server-rendered UI.

**Key Routes:**
- `GET /` Add/Drop (with Free Agents section)
- `POST /update` Trigger data refresh
- `GET /drop-candidates`
- `GET /team`
- `GET /compare`
- `GET /league`
- `GET /league/team` Team breakdown (hitters/pitchers averages)
- `GET /players`
- `GET /player`

### `src/config.py`
Configuration constants and settings (legacy Streamlit config still present, unused in FastAPI UI).

**Key Variables:**
- `PAGE_CONFIG` - Streamlit page configuration
- `DEFAULT_TEAM` - Default team selection
- `COLORS` - Color scheme for the rainbow tile system

### `src/data_utils.py`
Data loading and management utilities.

**Key Functions:**
- `load_data()` - Load the latest player data from CSV files
- `run_data_update()` - Trigger a data update from ESPN and FanGraphs APIs
- `get_latest_csv_file()` - Find the most recent data file

### `src/espn_data.py`
ESPN Fantasy Baseball API integration.

**Key Functions:**
- `get_all_players(league_id, season, espn_s2, swid)` - Fetch all players from ESPN league
- `get_league_info(league_id, season, espn_s2, swid)` - Get league settings and team info

### `src/fangraphs_api.py`
FanGraphs API integration for projections and statistics.

**Key Functions:**
- `get_fangraphs_merged_data()` - Fetch batting and pitching projections
- `get_batting_projections()` - Get hitter projections
- `get_pitching_projections()` - Get pitcher projections

## App Pages

### `src/app_pages/add_drop_recommendations.py`
Add/drop analysis and recommendations.

### `src/app_pages/best_free_agents.py`
Free agent analysis and rankings.

### `src/app_pages/drop_candidates.py`
Drop candidate identification.

### `src/app_pages/team_overview.py`
Team roster analysis.

### `src/app_pages/player_comparison.py`
Player comparison tools.

### `src/app_pages/draft_strategy.py`
Interactive draft board and strategy tools.

### `src/app_pages/waiver_trends.py`
Waiver wire analysis.

### `src/app_pages/league_analysis.py`
League-wide analysis and insights.

## Data Structures

### Player Data Format
The main data structure used throughout the application:

```python
{
    'Name': str,                    # Player name
    'Team': str,                    # MLB team
    'position': str,                # Primary position
    'fantasy_team': str,            # Fantasy team owner
    'fantasy_points': float,        # Current fantasy points
    'proj_CompositeScore': float,   # Projected composite score
    'curr_CompositeScore': float,   # Current composite score
    'injury_status': str,           # Injury status
    'eligible_positions': list,     # All eligible positions
}
```

## Environment Variables

Required environment variables (see `env.example`):

- `LEAGUE_ID`: ESPN Fantasy Baseball league ID
- `SEASON`: Fantasy season year
- `SWID`: ESPN SWID cookie
- `ESPN_S2`: ESPN S2 cookie 
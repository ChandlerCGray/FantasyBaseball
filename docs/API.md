# Fantasy Baseball Hub — API & Developer Reference

## Routes

### UI Pages

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Dashboard — position strength overview for selected team |
| `GET` | `/add-drop` | Free agent rankings, filterable by position |
| `GET` | `/team` | Roster for the selected team, filterable by position tab |
| `GET` | `/players` | Paginated, searchable table of all league players |
| `GET` | `/compare` | Side-by-side player comparison |
| `GET` | `/draft` | Interactive draft board |
| `GET` | `/league` | League standings ranked by projected composite score |
| `GET` | `/league/team` | Roster breakdown for a specific league team |
| `GET` | `/player` | Individual player detail page |
| `GET` | `/drop-candidates` | Players on your roster recommended for dropping |
| `GET` | `/free-agents` | Free agent list (alternative to add-drop view) |

### Data & Actions

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/update` | Trigger a data refresh from ESPN and FanGraphs |
| `GET` | `/api/players/search` | JSON player search (used by compare autocomplete) |

### Draft Sub-routes

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/draft/generate` | Generate or regenerate draft rankings |
| `POST` | `/draft/pick` | Mark a player as drafted |
| `POST` | `/draft/skip` | Skip a player in the draft order |
| `POST` | `/draft/unpick` | Undo a draft pick |
| `GET` | `/api/draft/advisor` | Draft advisor recommendations (JSON) |
| `GET` | `/api/draft/ideal` | Ideal draft targets (JSON) |

### Common Query Parameters

Most UI pages accept these query parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `team` | string | Selected fantasy team name |
| `hideInjured` | `true`/`false` | Exclude injured players |
| `pos` | string | Filter by position (e.g. `OF`, `1B`, `P`) |
| `minScore` | float | Minimum composite score threshold (default `-1.0`) |

`/players` additionally supports:

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Name search query |
| `roster` | string | Filter by fantasy team or `Free Agent` |
| `sort` | string | Sort field (`proj`, `curr`, or `name`) |
| `per` | int | Results per page (`25`, `50`, `100`, `200`) |
| `page` | int | Page number |

## Core Modules

### `src/server/main.py`
FastAPI application. All routes live here. Reads from the latest `output/free_agents_ranked_*.csv` file and builds server-rendered HTML responses via Jinja2 templates.

### `src/espn_data.py`
ESPN Fantasy Baseball API integration (built on `espn-api` by cwendt94).

Key functions:
- `get_all_players(league_id, season, espn_s2, swid)` — fetch all players with ownership and roster data
- `get_league_info(league_id, season, espn_s2, swid)` — fetch league settings and team info

### `src/fangraphs_api.py`
FanGraphs projections and current stats.

Key functions:
- `get_fangraphs_merged_data()` — merged batting + pitching data
- `get_batting_projections()` — hitter projections
- `get_pitching_projections()` — pitcher projections

### `src/analysis.py`
Statistical analysis: z-score normalization, composite score calculations, position scarcity adjustments.

### `src/data_utils.py`
Data loading and normalization.

Key functions:
- `load_data()` — load the latest CSV from `output/`
- `run_data_update()` — trigger ESPN + FanGraphs refresh and write a new CSV
- `get_latest_csv_file()` — find the most recent data file
- `expand_positions(position)` — normalize position strings to a list
- `format_player_name(row)` — format display name (with injury tag if applicable)

### `src/draft_strategy_generator.py`
Draft ranking logic: VADP calculations, tier assignments, position scarcity modeling, and ideal pick recommendations.

Key function:
- `analyze_and_adjust_rankings(df, ...)` — produces the ranked draft board DataFrame

## Data Format

The main DataFrame used across all pages is loaded from `output/free_agents_ranked_*.csv`:

```python
{
    'display_name': str,              # Player name (with injury status if applicable)
    'Name': str,                      # Raw player name
    'Team': str,                      # MLB team abbreviation
    'position': str,                  # Raw position string from ESPN
    'norm_positions': list[str],      # Normalized list of eligible positions
    'fantasy_team': str,              # Fantasy team name, or NaN / "Free Agent"
    'proj_CompositeScore': float,     # Projected composite score (FanGraphs projections)
    'curr_CompositeScore': float,     # Current composite score (season stats to date)
    'ScoreDelta': float,              # curr - proj (performance vs. expectation)
    'injury_status': str,             # Injury designation (e.g. "DTD", "IL10")
    'has_valid_position': bool,       # Whether norm_positions is non-empty
}
```

## Output Files

| Path pattern | Description |
|---|---|
| `output/free_agents_ranked_YYYYMMDD_HHMMSS.csv` | Timestamped player data snapshot |
| `output/draft_strategy_YYYYMMDD_HHMMSS.xlsx` | Draft board state (picks, skips, rankings) |
| `output/roster_settings.json` | Cached ESPN roster slot configuration |
| `output/scoring_settings.json` | Cached ESPN scoring category configuration |

The app always reads the most recently modified CSV. Draft state is always read from the most recently modified Excel file.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LEAGUE_ID` | ESPN Fantasy Baseball league ID |
| `SEASON` | Fantasy season year |
| `SWID` | ESPN SWID cookie |
| `ESPN_S2` | ESPN S2 cookie |

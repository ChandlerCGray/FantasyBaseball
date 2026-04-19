# Fantasy Baseball Hub - API & Developer Reference

## Route Reference

### HTML pages

| Method | Path | Notes |
|---|---|---|
| `GET` | `/` | Dashboard |
| `GET` | `/add-drop` | Add/drop analysis view |
| `GET` | `/free-agents` | Free-agent list view |
| `GET` | `/drop-candidates` | Drop-candidate view |
| `GET` | `/league` | League summary |
| `GET` | `/league/team` | Team breakdown within league view |
| `GET` | `/compare` | Player-vs-player comparison |
| `GET` | `/players` | Searchable/paginated player list |
| `GET` | `/draft` | Draft board UI |
| `GET` | `/player` | Player detail page (`player.html`) |
| `GET` | `/team` | Team roster view |

### JSON/action endpoints

| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/players/search` | Autocomplete-style player search |
| `POST` | `/update` | Runs `python src/main.py` to refresh CSV output |
| `POST` | `/draft/generate` | Rebuilds draft workbook, then redirects to `/draft` |
| `POST` | `/draft/pick` | Marks one player drafted |
| `POST` | `/draft/skip` | Adds a skipped pick entry |
| `POST` | `/draft/unpick` | Clears drafted state for one player |
| `GET` | `/api/draft/advisor` | Draft advisor JSON |
| `GET` | `/api/draft/ideal` | Ideal draft simulation JSON |

## Query/Form Parameters

### Common UI query params

Supported on most page routes:

| Parameter | Type | Description |
|---|---|---|
| `team` | string | Selected fantasy team |
| `hideInjured` | `true`/`false` | Defaults to `true` |
| `minScore` | float | Parsed from query string, passed through route context |

`minScore` is currently not applied as an active filter in the main route helpers.

### Route-specific params

| Route | Parameters |
|---|---|
| `/add-drop` | `pos`, `faSort`, `faRoster`, `faUpg` |
| `/drop-candidates` | `pos` |
| `/team` | `pos` |
| `/players` | `q`, `pos`, `roster`, `sort` (`proj`/`curr`/`name`), `per` (clamped 5-200), `page` |
| `/compare` | `p1`, `p2` |
| `/player` | `name` |
| `POST /update` | query: `model` (`steamer`, `zips`, `thebat`, `thebatx`, `atc`, `fangraphsdc`) |
| `POST /draft/pick` | form: `name` (required), `drafted_by` (optional), `total_teams` (default `10`) |
| `POST /draft/unpick` | form: `name` (required) |
| `GET /api/draft/advisor` | query: `position` (optional filter) |
| `GET /api/draft/ideal` | query: `pick` (default `1`), `teams` (default `10`) |

## Response Behavior

- Most page routes render `index.html`; `/player` renders `player.html`.
- If no ranked CSV exists, page routes return `no_data.html`.
- `/api/players/search` returns `[]` for queries shorter than 2 chars.
- `/update` returns JSON:
  - success: `{"status":"ok"}`
  - failure: `{"status":"error","detail":"..."}` with HTTP 500
- `/draft/generate` returns HTTP `303` redirect to `/draft`.

## Core Modules

### `src/server/main.py`

Primary FastAPI app and all routes. Loads latest `output/free_agents_ranked_*.csv`, prepares derived columns, and renders Jinja templates.

### `src/main.py`

Data refresh pipeline used by `/update`: ESPN pull -> FanGraphs pull -> merge/rank -> timestamped CSV output.

### `src/espn_data.py`

ESPN integration using `espn-api` plus raw ESPN endpoints.

Key functions:
- `get_all_players(...)`
- `get_roster_settings(...)`
- `get_scoring_settings(...)`
- `fetch_espn_adp_map(...)`

### `src/fangraphs_api.py`

FanGraphs fetch/merge logic and projection model mapping.

Key items:
- `PROJECTION_MODELS`
- `get_fangraphs_merged_data(model="steamer")`

### `src/analysis.py`

Data merge and ranking logic used during refresh.

### `src/draft_strategy_generator.py`

Draft workbook generation and ranking adjustments.

Key function:
- `analyze_and_adjust_rankings(...)`

### `src/data_utils.py`

Shared data helpers (position expansion, display-name formatting, and legacy Streamlit helpers).

## Data & Output Files

### Primary files

| Pattern | Purpose |
|---|---|
| `output/free_agents_ranked_YYYYMMDD_HHMMSS.csv` | Ranked player snapshot consumed by FastAPI pages |
| `output/draft_strategy_YYYYMMDD_HHMMSS.xlsx` | Draft board state and pick log |
| `output/roster_settings.json` | League roster slot config |
| `output/scoring_settings.json` | League scoring config |

App behavior:
- Ranked CSV: latest file matching `free_agents_ranked_*.csv`
- Draft workbook: latest file matching `draft_strategy_*.xlsx`

## Environment Variables

| Variable | Purpose |
|---|---|
| `LEAGUE_ID` | ESPN league id |
| `SEASON` | Fantasy season year |
| `SWID` | ESPN SWID cookie |
| `ESPN_S2` | ESPN espn_s2 cookie |
| `DEFAULT_TEAM` | Optional default selected team |
| `PROJECTION_MODEL` | Projection source model used for refresh |

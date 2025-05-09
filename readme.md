# ⚾ Fantasy Baseball Analyzer

A powerful, customizable fantasy baseball analysis toolkit. This project ingests ESPN league data and FanGraphs stats, merges and normalizes projections with current performance, and produces tailored free-agent suggestions, draft strategies, and league dashboards.

## Features

- **Custom Team Analyzer**: Compares free agents to your roster using weighted projections and current stats.
- **Draft Strategy Generator**: Applies position scarcity, depth, VADP, and adjusted scores for smarter drafting.
- **Dynamic Dashboard**: Built with Streamlit and Plotly, including dark-mode themed performance tiles and detailed player comparisons.
- **Z-score Based Normalization**: Ensures performance metrics are context-aware across different stat categories.
- **Excel GUI**: Desktop-friendly PySide6 GUI for reviewing and drafting from saved player pools.

## Installation

You'll need:

- Python 3.10+
- A `.env` file with your ESPN credentials (`LEAGUE_ID`, `SEASON`, `SWID`, `ESPN_S2`)
- Packages listed in `requirements.txt` (Streamlit, pandas, numpy, requests, PySide6, etc.)

```bash
pip install -r requirements.txt
```

## Usage

**1. Load Data**

Fetch ESPN and FanGraphs data and merge them:

```bash
python main.py
```

This creates timestamped `free_agents_ranked_*.csv` files in the `output/` folder.

**2. Run the Web App**

Launch the Streamlit dashboard:

```bash
streamlit run team_analyzer.py
```

Explore roster suggestions, stat breakdowns, and live comparisons.

**3. Use the Draft GUI**

Run the GUI:

```bash
python gui.py
```

Load an `.xlsx` workbook from the `output/` folder to manage drafts and compare players by tab (C, P, OF, etc.).

## Folder Structure

```
├── analysis.py                  # Data merge, normalization, z-scores
├── main.py                     # Entry point: fetches and processes data
├── team_analyzer.py            # Streamlit UI for roster suggestions
├── gui.py                      # PySide6-based draft workbook interface
├── draft_strategy_generator.py # Draft scoring logic (ADP, position scarcity)
├── espn_data.py                # Pulls current league rosters + free agents
├── fangraphs_api.py            # Scrapes FanGraphs projections + current stats
├── db_loader.py                # (Optional) Load into SQL Server star schema
├── free_agent_finder.py        # Standalone FA suggestion logic
├── output/                     # Generated CSV and Excel files
├── .env                        # Secrets and config (not checked in)
└── requirements.txt            # Dependencies
```

## Notes

- ESPN rate limits aggressively—consider adding retry logic or caching if you expand the tool.
- `output/` is timestamped; the most recent file is always used unless specified.
- GUI and web app can be used independently or in tandem depending on your workflow.

## License

MIT. No warranty. Fantasy heartbreak not included.

---

Made for those of us who want our fantasy league to run like a data pipeline.

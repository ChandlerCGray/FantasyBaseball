# Fantasy Baseball Hub

A comprehensive, interactive fantasy baseball analysis platform that combines ESPN league data with FanGraphs projections to deliver smart recommendations, interactive draft boards, and detailed player analytics through a beautiful, mobile-optimized interface.

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd FantasyBaseball
   ```

2. **Follow the setup guide**
   ```bash
   # See docs/SETUP.md for detailed instructions
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp env.example .env
   # Edit .env with your ESPN credentials
   mkdir -p output
   ```

3. **Launch the application**
   ```bash
   # FastAPI (recommended)
   source venv/bin/activate
   uvicorn src.server.main:app --host 0.0.0.0 --port 8000

   # Or via helper
   ./start
   ```

4. **Access the application**
   - Local: http://localhost:8000
   - Network: http://your-ip:8000

**For detailed setup instructions, see [docs/SETUP.md](docs/SETUP.md)**

## Features

### Smart Recommendations
- **Add/Drop Suggestions** - Instant roster upgrade recommendations with clear visual hierarchy
- **Best Free Agents** - Top available players by position with detailed stats
- **Drop Candidates** - Identify underperforming roster players with upgrade potential

### Advanced Analytics
- **Player Comparison** - Side-by-side stat analysis with projected vs current performance
- **League Analysis** - Team strength analysis and competitive insights
- **Waiver Trends** - Track player movement and availability patterns

### Interactive Draft Board
- **Live Draft Interface** - Professional draft room experience with click-to-draft functionality
- **Position Scarcity Analysis** - VADP calculations and tier-based rankings
- **Persistent Draft State** - Auto-saves to Excel, resume drafts across sessions
- **Real-time Updates** - Immediate visual feedback and summary statistics

### Modern UI/UX
- **Dark IDE Theme** - Muted, per-page accents; no emojis
- **Mobile Optimized** - Off-canvas Filters sidebar with icon toggle
- **Professional Styling** - Clean typography, compact cards, gradient stat indicators
- **Interactive Components** - Sortable tables, drill-down links, compare flows

## Technology Stack

- **Frontend**: FastAPI + Jinja2 (server-rendered UI)
- **Data Processing**: Pandas, NumPy
- **APIs**: ESPN Fantasy Baseball API, FanGraphs API
- **Visualization**: Plotly, Custom CSS
- **Data Storage**: CSV files, Excel export

## Project Structure

```
FantasyBaseball/
├── src/                    # Application source code
│   ├── app_pages/         # Individual analysis pages
│   │   ├── add_drop_recommendations.py
│   │   ├── best_free_agents.py
│   │   ├── drop_candidates.py
│   │   ├── team_overview.py
│   │   ├── player_comparison.py
│   │   ├── draft_strategy.py
│   │   ├── waiver_trends.py
│   │   └── league_analysis.py
│   ├── server/
│   │   └── main.py        # FastAPI app and routes
│   ├── config.py          # Configuration constants
│   ├── data_utils.py      # Data loading utilities
│   ├── espn_data.py       # ESPN API integration
│   ├── fangraphs_api.py   # FanGraphs API integration
│   ├── analysis.py        # Statistical analysis
│   ├── styles.py          # CSS styling
│   └── ui_components.py   # Reusable UI components
├── output/                # Generated data files
├── sql/                   # Database schema (optional)
├── .env                   # Environment variables (create from env.example)
├── env.example           # Example environment file
├── requirements.txt       # Python dependencies
├── app.py                 # Application entry point
├── start                  # Cross-platform launcher
├── scripts/               # Utility scripts
│   ├── start.py          # Unified startup script
│   └── update_credentials.py  # ESPN credentials helper
├── docs/                  # Documentation
│   ├── API.md            # API documentation
│   └── SETUP.md          # Detailed setup guide
└── README.md             # This file
```

## Configuration

### Environment Variables

Create a `.env` file with your ESPN Fantasy Baseball credentials:

```bash
LEAGUE_ID=your_league_id
SEASON=2024
SWID={your_swid_cookie}
ESPN_S2=your_espn_s2_cookie
```

### Getting ESPN Credentials

1. **Browser Method**: 
   - Go to ESPN Fantasy Baseball
   - Open Developer Tools (F12)
   - Application → Cookies → espn.com
   - Copy `SWID` and `espn_s2` values

2. **Helper Script**:
   ```bash
   python scripts/update_credentials.py
   ```

## Data Sources

- **ESPN Fantasy**: Live league rosters, player ownership, league settings
- **FanGraphs**: Professional projections, current stats, advanced metrics
- **Automated Updates**: Fresh data pulled automatically or on-demand

## Key Features Explained

### Interactive Draft Board
The crown jewel of the application - a fully interactive draft interface that rivals professional draft software:
- **Click-to-Draft**: Mark players as drafted with team assignments
- **Persistent State**: All draft actions auto-save to Excel files
- **Position Scarcity**: Advanced VADP calculations and tier analysis
- **Real-time Updates**: Live summary statistics and availability tracking

### Rainbow Tile System
A unique, beautiful design system that makes data analysis enjoyable:
- **Color-coded Tiers**: Instant visual hierarchy for player rankings
- **Consistent Design**: Unified interface across all analysis tools
- **Mobile Optimized**: Perfect experience on phones, tablets, and desktops
- **Accessibility**: Proper contrast ratios and readable typography

### Smart Analytics
Advanced statistical analysis that goes beyond basic projections:
- **Z-score Normalization**: Context-aware performance metrics
- **Composite Scoring**: Weighted projections combined with current stats
- **Position Adjustments**: Scarcity-based value calculations
- **Trend Analysis**: Historical performance and projection accuracy

## Important Notes

- **ESPN Rate Limits**: The app respects ESPN's API limits with built-in retry logic
- **Data Persistence**: All analysis results are timestamped and saved to `output/`
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Browser Compatibility**: Optimized for Chrome, Firefox, Safari, and Edge
- **Draft Continuity**: Draft state persists across sessions and app restarts

## Contributing

This project is built for fantasy baseball enthusiasts who love data-driven decisions. Feel free to:
- Report bugs or request features via GitHub issues
- Submit pull requests for improvements
- Share your league success stories

## Documentation

- **[Setup Guide](docs/SETUP.md)** - Detailed installation and configuration
- **[Production Setup](PRODUCTION_SETUP.md)** - 24/7 service, monitoring, and management
- **[API Documentation](docs/API.md)** - Developer reference

## Acknowledgements

- Special thanks to the open-source `espn-api` project by cwendt94, which makes interacting with ESPN Fantasy data possible. See `espn-api` on GitHub: https://github.com/cwendt94/espn-api

## License

MIT License - Use it, modify it, win your league with it!

**Disclaimer**: No warranty provided. Fantasy heartbreak, championship glory, and data addiction not included but highly likely.

---

*Built for those who believe fantasy baseball should run like a data pipeline*

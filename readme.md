# Fantasy Baseball Hub

A comprehensive, interactive fantasy baseball analysis platform. This modern web application combines ESPN league data with FanGraphs projections to deliver smart recommendations, interactive draft boards, and detailed player analytics through a clean, mobile-optimized interface.

## Features

### Smart Recommendations
- **Quick Wins**: Instant add/drop suggestions with clear visual hierarchy and rainbow-themed tiles
- **Best Free Agents**: Expandable player cards with detailed stats and position rankings  
- **Drop Candidates**: Identify underperforming roster players with upgrade potential

### Advanced Analytics
- **Player Comparison**: Side-by-side stat analysis with rainbow tiles showing projected vs current performance in collapsible sections
- **League Analysis**: Team strength analysis and competitive insights
- **Waiver Trends**: Track player movement and availability patterns

### Interactive Draft Board
- **Live Draft Interface**: Professional draft room experience with click-to-draft functionality
- **Position Scarcity Analysis**: VADP calculations and tier-based rankings
- **Persistent Draft State**: Auto-saves to Excel, resume drafts across sessions
- **Real-time Updates**: Immediate visual feedback and summary statistics
- **All Player Analysis**: Includes entire player pool, not just free agents

### Modern UI/UX
- **Rainbow Tile System**: Beautiful, color-coded interface with consistent design language
- **Mobile Optimized**: Responsive design that works perfectly on all devices
- **Professional Styling**: Clean interface with proper contrast and accessibility
- **Interactive Components**: Collapsible sections, expandable cards, and intuitive navigation

## Quick Start

### Prerequisites
- Python 3.10+
- ESPN Fantasy League credentials
- `.env` file with your league settings

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd fantasy-baseball-hub

# Install dependencies
pip install -r requirements.txt

# Set up your environment variables
cp .env.example .env
# Edit .env with your ESPN credentials
```

### Launch the Application

```bash
python run_new_app.py
```

This launches the complete Fantasy Baseball Hub with all 8 analysis tools:

1. **Add/Drop Recommendations** - Smart roster upgrade suggestions
2. **Best Free Agents** - Top available players by position
3. **Drop Candidates** - Underperforming roster players
4. **Team Analysis** - Comprehensive roster overview
5. **Player Comparison** - Side-by-side player analytics
6. **Draft Strategy** - Interactive draft board with live drafting
7. **Waiver Trends** - Player movement analysis
8. **League Analysis** - Competitive landscape insights

### Data Updates

The app automatically fetches fresh data, or manually update:

```bash
python src/main_app.py
```

This creates timestamped CSV files in the `output/` folder with the latest ESPN and FanGraphs data.

## Project Structure

```
├── src/
│   ├── app_pages/              # Modular page components
│   │   ├── add_drop_recommendations.py  # Quick wins analysis
│   │   ├── best_free_agents.py         # Top available players
│   │   ├── drop_candidates.py          # Roster optimization
│   │   ├── team_overview.py            # Team analysis dashboard
│   │   ├── player_comparison.py        # Side-by-side player stats
│   │   ├── draft_strategy.py           # Interactive draft board
│   │   ├── waiver_trends.py            # Player movement tracking
│   │   └── league_analysis.py          # League-wide insights
│   ├── main_app.py             # Main Streamlit application
│   ├── config.py               # App configuration and constants
│   ├── styles.py               # Rainbow tile CSS and styling
│   ├── ui_components.py        # Reusable UI components
│   ├── data_utils.py           # Data processing utilities
│   ├── draft_strategy_generator.py  # Draft logic (VADP, scarcity)
│   ├── espn_data.py            # ESPN league data integration
│   ├── fangraphs_api.py        # FanGraphs projections API
│   ├── analysis.py             # Statistical analysis and normalization
│   └── db_loader.py            # Database integration (optional)
├── output/                     # Generated CSV and Excel files
├── sql/                        # Database schema files
├── run_new_app.py              # Application launcher
├── .env                        # Environment variables (not in repo)
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
└── readme.md                   # This file
```

## Key Features Explained

### Interactive Draft Board
The crown jewel of the application - a fully interactive draft interface that rivals professional draft software:
- **Click-to-Draft**: Mark players as drafted with team assignments
- **Persistent State**: All draft actions auto-save to Excel files
- **Position Scarcity**: Advanced VADP calculations and tier analysis
- **Real-time Updates**: Live summary statistics and availability tracking
- **Auto-Load**: Automatically loads the most recent draft file on startup

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

### Enhanced Player Comparison
Redesigned comparison interface with improved usability:
- **Collapsible Stats Section**: All stats organized in a single expandable section
- **Grouped Statistics**: Projected and current stats matched together in rainbow tiles
- **Visual Hierarchy**: Clear organization with proper text contrast
- **Mobile-Friendly**: Responsive design that works well on all devices

## Configuration

### Environment Variables (.env)
```bash
# ESPN League Settings
LEAGUE_ID=your_league_id
SEASON=2024
SWID=your_swid_cookie
ESPN_S2=your_espn_s2_cookie

# Optional Database Settings
DB_SERVER=your_server
DB_NAME=your_database
```

### Customization
- **Team Selection**: Choose your team from the sidebar dropdown
- **Filters**: Adjust minimum projected scores and hide injured players
- **Position Settings**: Modify position eligibility in `config.py`
- **Styling**: Customize colors and themes in `styles.py`

## Data Sources

- **ESPN Fantasy**: Live league rosters, player ownership, and league settings
- **FanGraphs**: Professional projections, current stats, and advanced metrics
- **Automated Updates**: Fresh data pulled automatically or on-demand

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

## License

MIT License - Use it, modify it, win your league with it!

**Disclaimer**: No warranty provided. Fantasy heartbreak, championship glory, and data addiction not included but highly likely.

---

*Built for those who believe fantasy baseball should run like a data pipeline*

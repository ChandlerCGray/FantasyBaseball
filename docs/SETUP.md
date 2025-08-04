# Fantasy Baseball Hub - Setup Guide

This guide will help you get the Fantasy Baseball Hub up and running quickly.

## Prerequisites

- **Python 3.10+** (3.12 recommended)
- **Git** (for cloning the repository)
- **ESPN Fantasy Baseball account** with access to a league

## Quick Start

### 1. Clone and Navigate
```bash
git clone <your-repo-url>
cd FantasyBaseball
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Create Environment File
```bash
cp env.example .env
```

### 5. Configure ESPN Credentials
Edit `.env` with your ESPN Fantasy Baseball credentials:

```bash
# ESPN Fantasy Baseball API Configuration
LEAGUE_ID=your_league_id_here
SEASON=2024
SWID=your_swid_cookie_here
ESPN_S2=your_espn_s2_cookie_here
```

### 6. Get ESPN Credentials

#### Method 1: Browser Developer Tools
1. Go to [ESPN Fantasy Baseball](https://www.espn.com/fantasy/baseball/)
2. Log into your account
3. Navigate to your specific league
4. Open Developer Tools (F12)
5. Go to **Application** → **Cookies** → **espn.com**
6. Copy these values:
   - `SWID` (should look like `{GUID}`)
   - `espn_s2` (long encoded string)

#### Method 2: Use the Helper Script
```bash
python scripts/update_credentials.py
```

### 7. Create Output Directory
```bash
mkdir -p output
```

### 8. Launch the Application

#### Option A: Use Startup Script (Recommended)
```bash
./start
```

#### Option B: Manual Launch
```bash
python app.py
```

The app will be available at:
- **Local**: http://localhost:8501
- **Network**: http://your-ip:8501

## Troubleshooting

### Common Issues

#### 1. "No module named 'unidecode'"
```bash
pip install unidecode
```

#### 2. "No module named 'espn_api'"
```bash
pip install espn-api
```

#### 3. "No data files found"
- Make sure you've created the `output/` directory
- Run the data update: Click "Update Data" in the app sidebar
- Check that your ESPN credentials are correct

#### 4. ESPN Authentication Errors
- **Cookies expired**: Get fresh cookies from your browser
- **Wrong League ID**: Verify the league ID in your ESPN league URL
- **Wrong Season**: Try changing SEASON to 2024 in `.env`
- **League Privacy**: Ensure your league allows API access

### Getting Your League ID

1. Go to your ESPN Fantasy Baseball league
2. Look at the URL: `https://fantasy.espn.com/baseball/team?leagueId=123456789&teamId=1`
3. The number after `leagueId=` is your League ID

## File Structure

```
FantasyBaseball/
├── src/                    # Application source code
│   ├── app_pages/         # Individual analysis pages
│   ├── main_app.py        # Main Streamlit application
│   ├── config.py          # Configuration constants
│   ├── data_utils.py      # Data loading utilities
│   ├── espn_data.py       # ESPN API integration
│   └── fangraphs_api.py   # FanGraphs API integration
├── output/                # Generated data files
├── sql/                   # Database schema (optional)
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
├── app.py                 # Application entry point
└── docs/SETUP.md         # This file
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `LEAGUE_ID` | Your ESPN league ID | `123456789` |
| `SEASON` | Fantasy season year | `2024` |
| `SWID` | ESPN SWID cookie | `{GUID}` |
| `ESPN_S2` | ESPN S2 cookie | `encoded_string` |

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your ESPN credentials are fresh
3. Ensure your league ID is correct
4. Try changing the season to 2024

## Features Available

Once set up, you'll have access to:

- **Add/Drop Recommendations** - Smart roster suggestions
- **Best Free Agents** - Top available players
- **Drop Candidates** - Underperforming players
- **Team Analysis** - Roster overview
- **Player Comparison** - Side-by-side stats
- **Draft Strategy** - Interactive draft board
- **Waiver Trends** - Player movement
- **League Analysis** - Competitive insights 
"""
Data loading and processing utilities for the Fantasy Baseball App
"""

import os
import glob
import pandas as pd
import streamlit as st
import subprocess
import sys
from config import PITCHER_ROLES, HITTER_ROLES, POSITION_VARIATIONS

def get_newest_csv(folder="./output", pattern="free_agents_ranked_*.csv"):
    """Get the most recent CSV file"""
    # Get the absolute path to the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder_path = os.path.join(project_root, folder)
    files = glob.glob(os.path.join(folder_path, pattern))
    return max(files, key=os.path.getmtime) if files else None

def expand_positions(pos_str):
    """Convert position string to list of positions"""
    if not isinstance(pos_str, str) or pos_str.strip() == "":
        return []
    
    # Clean up the position string
    pos_str = pos_str.upper().replace("\n", " ").replace("/", " ").replace(",", " ")
    positions = [p.strip() for p in pos_str.split() if p.strip()]
    
    normalized = set()
    
    for pos in positions:
        pos = pos.strip()
        if pos in PITCHER_ROLES:
            normalized.add("P")
        elif pos in HITTER_ROLES:
            normalized.add(pos)
        elif pos in POSITION_VARIATIONS:
            normalized.add(POSITION_VARIATIONS[pos])
    
    return list(normalized)

def can_play_position(player_positions, target_position):
    """Check if player can play target position"""
    if not isinstance(player_positions, list):
        return False
    return target_position in player_positions

def format_player_name(row):
    """Format player name with injury status"""
    name = row.get("Name", "Unknown")
    injury = row.get("injury_status", "")
    
    # Handle NaN values and convert to string
    if pd.isna(injury) or injury == "":
        return name
    
    injury_str = str(injury).strip()
    if injury_str and injury_str.upper() not in ["ACTIVE", "HEALTHY", ""]:
        return f"{name} ({injury_str})"
    return name

def get_player_stats(df, is_pitcher=False):
    """Get relevant stats for display"""
    base_cols = ["Name", "Team", "fantasy_team", "position"]
    
    if is_pitcher:
        stat_cols = [
            "proj_CompositeScore", "curr_CompositeScore", "ScoreDelta",
            "proj_IP", "proj_FIP", "proj_WHIP", "proj_K-BB%", "proj_SV",
            "curr_IP", "curr_FIP", "curr_WHIP", "curr_K-BB%", "curr_SV"
        ]
    else:
        stat_cols = [
            "proj_CompositeScore", "curr_CompositeScore", "ScoreDelta",
            "proj_AB", "proj_wOBA", "proj_wRC+", "proj_ISO", "proj_wBsR",
            "curr_AB", "curr_wOBA", "curr_wRC+", "curr_ISO", "curr_wBsR"
        ]
    
    available_cols = [col for col in base_cols + stat_cols if col in df.columns]
    return df[available_cols].round(3)

def run_data_update():
    """Run the main.py script to update data"""
    if st.button("Update Data", help="Fetch latest data from ESPN and FanGraphs"):
        with st.spinner("Updating data..."):
            try:
                result = subprocess.run(
                    [sys.executable, "./src/main.py"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd="."
                )
                st.success("✅ Data updated successfully!")
                st.rerun()
            except subprocess.CalledProcessError as e:
                st.error("❌ Update failed")
                st.code(e.stderr or "No error output")

def load_data():
    """Load and process the data - cache based on file modification time"""
    csv_path = get_newest_csv()
    if not csv_path:
        st.error("No data files found. Please run the data update first.")
        st.stop()
    
    # Get file modification time to use as cache key
    file_mtime = os.path.getmtime(csv_path)
    
    return _load_data_cached(csv_path, file_mtime)

@st.cache_data
def _load_data_cached(csv_path, file_mtime):
    """Internal cached function that loads data with file modification time as cache key"""
    # Load with low_memory=False to handle mixed types
    df = pd.read_csv(csv_path, low_memory=False)
    
    # Add formatted names and position lists
    df["display_name"] = df.apply(format_player_name, axis=1)
    df["norm_positions"] = df["position"].apply(expand_positions)
    
    # Calculate score delta if not present
    if "ScoreDelta" not in df.columns:
        df["ScoreDelta"] = df["curr_CompositeScore"] - df["proj_CompositeScore"]
    
    # Filter out players with no valid positions for most operations
    df["has_valid_position"] = df["norm_positions"].apply(lambda x: len(x) > 0)
    
    return df, csv_path
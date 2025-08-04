import os
import logging
import datetime
import pandas as pd
from dotenv import load_dotenv
from analysis import (
    merge_data,
    rank_free_agents,
    determine_position
)
from espn_data import get_all_players
from fangraphs_api import get_fangraphs_merged_data

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Environment config
load_dotenv()
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Configuration ---
def get_env_var(name, default=None, required=True, var_type=str):
    val = os.getenv(name, default)
    if required and val is None:
        raise ValueError(f"{name} is required but missing from .env.")
    try:
        return var_type(val)
    except ValueError:
        raise ValueError(f"{name} must be of type {var_type.__name__}.")

league_id = get_env_var("LEAGUE_ID", var_type=int)
season = get_env_var("SEASON", var_type=int)
swid = get_env_var("SWID")
espn_s2 = get_env_var("ESPN_S2")

# --- Helpers ---
def add_clean_position(df):
    if "eligible_positions" in df.columns:
        df["clean_position"] = df["eligible_positions"].apply(determine_position)
    elif "position" in df.columns:
        logger.warning("Missing 'eligible_positions'. Using 'position'.")
        df["clean_position"] = df["position"].apply(lambda p: determine_position([p]))
    else:
        logger.warning("Missing both 'eligible_positions' and 'position'. Defaulting to Unknown.")
        df["clean_position"] = "Unknown"
    return df

def filter_position_groups(df):
    df = add_clean_position(df)
    hitters = df[~df["clean_position"].str.contains("Pitcher", na=False)].copy()
    pitchers = df[df["clean_position"].str.contains("Pitcher", na=False)].copy()
    return hitters, pitchers

def remove_redundant_columns(df):
    to_remove = ["clean_name", "clean_team", "name_fa", "name_proj",
                 "team_fa", "team_proj", "position_fa", "position_proj", "eligible_positions"]
    return df.drop(columns=[col for col in to_remove if col in df.columns], errors="ignore")

def prepare_output_dataframe(df, all_columns=False):
    df = remove_redundant_columns(df)
    preferred = ["Name", "Team", "fantasy_team", "position", "injury_status", "fantasy_points"]
    proj = ["proj_CompositeScore", "proj_ADP", "proj_AB", "proj_wOBA", "proj_ISO", "proj_wBsR",
            "proj_FIP", "proj_K-BB%", "proj_WHIP", "proj_IP", "proj_SV"]
    curr = ["curr_CompositeScore", "curr_AB", "curr_wOBA", "curr_ISO", "curr_wBsR",
            "curr_FIP", "curr_K-BB%", "curr_WHIP", "curr_IP", "curr_SV"]
    
    columns = [c for c in preferred if c in df.columns] + [c for c in proj + curr if c in df.columns]
    if all_columns:
        columns += [col for col in df.columns if col not in columns]
    
    df = df[columns]
    round_map = {"proj_CompositeScore": 2, "proj_wOBA": 3, "proj_ISO": 3, "proj_wBsR": 2,
                 "proj_FIP": 2, "proj_K-BB%": 2, "proj_WHIP": 2, "proj_IP": 1, "proj_SV": 1,
                 "curr_CompositeScore": 2, "curr_wOBA": 3, "curr_ISO": 3, "curr_wBsR": 2,
                 "curr_FIP": 2, "curr_K-BB%": 2, "curr_WHIP": 2, "curr_IP": 1, "curr_SV": 1}
    return df.round({col: digits for col, digits in round_map.items() if col in df.columns})

def save_dataframe(df, prefix, all_columns=False):
    if df.empty:
        logger.warning(f"No data to save for: {prefix}")
        return
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_DIR, f"{prefix}_{timestamp}.csv")
    formatted = prepare_output_dataframe(df, all_columns=all_columns)
    formatted.to_csv(filename, index=False)
    logger.info(f"Saved: {filename}")

# --- Data Flow ---
def fetch_data():
    logger.info("Fetching players from ESPN...")
    fa_df = get_all_players(league_id, season, espn_s2, swid)
    if fa_df.empty:
        logger.error("No players retrieved from ESPN.")
        return None, None, None
    
    logger.info("Fetching FanGraphs projections and stats...")
    bat_df, pit_df = get_fangraphs_merged_data()
    if bat_df.empty and pit_df.empty:
        logger.error("FanGraphs returned empty data.")
        return None, None, None
    
    return fa_df, bat_df, pit_df

def process_data(fa_df, bat_df, pit_df):
    hitters, pitchers = filter_position_groups(fa_df)
    merged_hitters = merge_data(hitters, bat_df)
    merged_pitchers = merge_data(pitchers, pit_df)
    
    if merged_hitters.empty and merged_pitchers.empty:
        logger.error("Merged datasets are empty.")
        return None
    
    merged_all = pd.concat([merged_hitters, merged_pitchers], ignore_index=True)
    return rank_free_agents(merged_all)

# --- Orchestration ---
def main():
    try:
        fa_df, bat_df, pit_df = fetch_data()
        if fa_df is None or fa_df.empty or (bat_df is None and pit_df is None):
            return
        
        ranked = process_data(fa_df, bat_df, pit_df)
        if ranked is not None:
            save_dataframe(ranked, "free_agents_ranked", all_columns=True)
            logger.info("Free agent rankings complete.")
    except Exception as e:
        logger.exception(f"Fatal error during execution: {e}")

if __name__ == "__main__":
    main()
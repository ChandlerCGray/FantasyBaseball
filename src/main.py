import os
import logging
import datetime
import pandas as pd
from dotenv import load_dotenv
from typing import TypeVar, Type, Optional

from analysis import merge_data, rank_free_agents, determine_position
from espn_data import get_all_players
from fangraphs_api import get_fangraphs_merged_data

# — Logging setup —
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# — Load environment variables from .env —
load_dotenv()

# — Generic environment‐loader —
T = TypeVar("T")
def get_env_var(
    name: str,
    default: Optional[str] = None,
    required: bool = True,
    var_type: Type[T] = str
) -> T:
    val = os.getenv(name, default)
    if required and val is None:
        raise ValueError(f"{name} is required but missing from .env.")
    try:
        return var_type(val)  # type: ignore
    except ValueError:
        raise ValueError(f"{name} must be of type {var_type.__name__}.")

# — Read required variables once —
league_id  = get_env_var("LEAGUE_ID", var_type=int)
season     = get_env_var("SEASON",    var_type=int)
swid       = get_env_var("SWID")
espn_s2    = get_env_var("ESPN_S2")
OUTPUT_DIR = get_env_var("OUTPUT_DIR", default="output", required=False)

os.makedirs(OUTPUT_DIR, exist_ok=True)


# — Helpers for cleaning and preparing data —
def add_clean_position(df: pd.DataFrame) -> pd.DataFrame:
    if "eligible_positions" in df.columns:
        df["clean_position"] = df["eligible_positions"].apply(determine_position)
    elif "position" in df.columns:
        logger.warning("Missing 'eligible_positions'. Using 'position'.")
        df["clean_position"] = df["position"].apply(lambda p: determine_position([p]))
    else:
        logger.warning(
            "Missing both 'eligible_positions' and 'position'. Defaulting to Unknown."
        )
        df["clean_position"] = "Unknown"
    return df

def filter_position_groups(df: pd.DataFrame):
    df = add_clean_position(df)
    hitters  = df[~df["clean_position"].str.contains("Pitcher", na=False)].copy()
    pitchers = df[df["clean_position"].str.contains("Pitcher", na=False)].copy()
    return hitters, pitchers

def remove_redundant_columns(df: pd.DataFrame) -> pd.DataFrame:
    to_remove = [
        "clean_name", "clean_team", "name_fa", "name_proj",
        "team_fa", "team_proj", "position_fa", "position_proj",
        "eligible_positions"
    ]
    return df.drop(columns=[c for c in to_remove if c in df.columns], errors="ignore")

def prepare_output_dataframe(df: pd.DataFrame, all_columns: bool = False) -> pd.DataFrame:
    df = remove_redundant_columns(df)
    preferred = [
        "Name", "Team", "fantasy_team", "position",
        "injury_status", "fantasy_points"
    ]
    proj = [
        "proj_CompositeScore", "proj_ADP", "proj_AB", "proj_wOBA",
        "proj_ISO", "proj_wBsR", "proj_FIP", "proj_K-BB%",
        "proj_WHIP", "proj_IP", "proj_SV"
    ]
    curr = [
        "curr_CompositeScore", "curr_AB", "curr_wOBA", "curr_ISO",
        "curr_wBsR", "curr_FIP", "curr_K-BB%", "curr_WHIP",
        "curr_IP", "curr_SV"
    ]

    cols = [c for c in preferred if c in df.columns] \
         + [c for c in proj + curr if c in df.columns]

    if all_columns:
        cols += [c for c in df.columns if c not in cols]

    df = df[cols]

    round_map = {
        "proj_CompositeScore": 2,
        "proj_wOBA": 3,
        "proj_ISO": 3,
        "proj_wBsR": 2,
        "proj_FIP": 2,
        "proj_K-BB%": 2,
        "proj_WHIP": 2,
        "proj_IP": 1,
        "proj_SV": 1,
        "curr_CompositeScore": 2,
        "curr_wOBA": 3,
        "curr_ISO": 3,
        "curr_wBsR": 2,
        "curr_FIP": 2,
        "curr_K-BB%": 2,
        "curr_WHIP": 2,
        "curr_IP": 1,
        "curr_SV": 1
    }
    applicable = {col: digs for col, digs in round_map.items() if col in df.columns}
    return df.round(applicable)

def save_dataframe(df: pd.DataFrame, prefix: str, all_columns: bool = False) -> None:
    if df.empty:
        logger.warning(f"No data to save for: {prefix}")
        return
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_DIR, f"{prefix}_{ts}.csv")
    formatted = prepare_output_dataframe(df, all_columns=all_columns)
    formatted.to_csv(filename, index=False)
    logger.info(f"Saved: {filename}")


# — Data fetching and processing —
def fetch_data():
    logger.info("Fetching players from ESPN...")
    fa_df = get_all_players(league_id, season, espn_s2, swid)
    if fa_df is None or fa_df.empty:
        logger.error("No players retrieved from ESPN.")
        return None, None, None

    logger.info("Fetching FanGraphs projections and stats...")
    bat_df, pit_df = get_fangraphs_merged_data()
    if (bat_df is None or bat_df.empty) and (pit_df is None or pit_df.empty):
        logger.error("FanGraphs returned empty data.")
        return None, None, None

    return fa_df, bat_df, pit_df

def process_data(fa_df, bat_df, pit_df):
    hitters, pitchers = filter_position_groups(fa_df)
    mh = merge_data(hitters, bat_df)
    mp = merge_data(pitchers, pit_df)
    if mh.empty and mp.empty:
        logger.error("Merged datasets are empty.")
        return None

    combined = pd.concat([mh, mp], ignore_index=True)
    return rank_free_agents(combined)


# — Main orchestration —
def main():
    try:
        fa_df, bat_df, pit_df = fetch_data()
        if fa_df is None:
            return

        ranked = process_data(fa_df, bat_df, pit_df)
        if ranked is not None:
            save_dataframe(ranked, "free_agents_ranked", all_columns=True)
            logger.info("Free agent rankings complete.")
    except Exception as e:
        logger.exception(f"Fatal error during execution: {e}")


if __name__ == "__main__":
    main()

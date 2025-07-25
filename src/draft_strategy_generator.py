import os
import glob
import re
import datetime
import logging
from typing import Set, List, Dict, Tuple, Optional
import pandas as pd
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Configuration parameters for thresholds and factors.
CONFIG = {
    'scarceness': {'base': 10, 'bonus': 8},
    'depth': {'base': 30, 'bonus': 8},
    'adjustment': {
        'scarce_multiplier': 0.15,
        'scarce_rank_weight': 0.75,
        'deep_multiplier': 0.25,
    },
    'draft_round': {
        'weights': {'adp': 0.7, 'rank': 0.3},
        'vadp_factors': [(50, 0.1), (100, 0.2), (float('inf'), 0.3)],
        'movement_caps': [(50, 0.3), (100, 0.2), (float('inf'), 0.1)]
    },
    'top_n_players': 250,
    'min_composite_score': 0,
    'league_positions': ["1B", "2B", "3B", "SS", "P", "C", "OF", "MI", "CI"]
}

def sanitize_filename(name: str) -> str:
    """
    Remove characters that are invalid in Windows filenames.
    """
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def get_latest_free_agents_file(directory: str = "output") -> str:
    """
    Find the most recently created free_agents_ranked CSV file.
    """
    pattern = os.path.join(directory, "free_agents_ranked_*.csv")
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError("No free_agents_ranked_*.csv files found.")
    latest_file = max(files, key=os.path.getctime)
    logging.info("Latest file determined: %s", latest_file)
    return latest_file

def load_data(file_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load CSV data from the provided file or from the latest file in the output directory.
    Insert a placeholder 'Drafted' column.
    """
    if file_path is None:
        file_path = get_latest_free_agents_file()
    df = pd.read_csv(file_path)
    df.insert(3, "Drafted", "")
    return df

def map_position_eligibility(position: str) -> Set[str]:
    """
    Map a player's position string to a set of eligible positions.
    """
    eligible = set()
    if "C" in position:
        eligible.add("C")
    if "1B" in position:
        eligible.update(["1B", "CI"])
    if "2B" in position:
        eligible.update(["2B", "MI"])
    if "SS" in position:
        eligible.update(["SS", "MI"])
    if "3B" in position:
        eligible.update(["3B", "CI"])
    if "OF" in position:
        eligible.add("OF")
    if "P" in position:
        eligible.add("P")
    else:
        eligible.add("UTIL")
    return eligible

def add_eligibility_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add the 'Eligible_Positions' column to the DataFrame.
    """
    df["Eligible_Positions"] = df["position"].apply(map_position_eligibility)
    return df

def filter_players(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter players: Include all players with valid positions and composite scores.
    """
    # Debug: Check what columns we have
    logging.info(f"Available columns: {list(df.columns)}")
    logging.info(f"Total players before filtering: {len(df)}")
    
    # Check if AB column exists and what values it has
    if 'AB' in df.columns:
        ab_stats = df['AB'].describe()
        logging.info(f"AB column stats: {ab_stats}")
        logging.info(f"AB null count: {df['AB'].isnull().sum()}")
    else:
        logging.warning("AB column not found in dataframe")
    
    # For now, let's just filter by having a valid CompositeScore
    # This should include both hitters and pitchers
    valid_players = df[df['CompositeScore'].notna() & (df['CompositeScore'] != 0)]
    
    logging.info(f"Players with valid CompositeScore: {len(valid_players)}")
    
    # Check position distribution
    if 'Eligible_Positions' in valid_players.columns:
        pitcher_count = valid_players['Eligible_Positions'].apply(lambda pos: "P" in pos).sum()
        non_pitcher_count = len(valid_players) - pitcher_count
        logging.info(f"Pitchers: {pitcher_count}, Non-pitchers: {non_pitcher_count}")
    
    return valid_players

# def restrict_to_top_players(df: pd.DataFrame, top_n: int = CONFIG['top_n_players']) -> pd.DataFrame:
#     """
#     Limit the DataFrame to the top players based on CompositeScore.
#     """
#     df = df.sort_values(by="CompositeScore", ascending=False).head(top_n).reset_index(drop=True)
#     return df

def restrict_to_top_players(df: pd.DataFrame, top_n: int = CONFIG['top_n_players']) -> pd.DataFrame:
    # Filter out any players with a CompositeScore less than the minimum.
    df = df[df["CompositeScore"] >= CONFIG['min_composite_score']]
    df = df.sort_values(by="CompositeScore", ascending=False).head(top_n).reset_index(drop=True)
    return df


def compute_positional_depth(df: pd.DataFrame) -> Tuple[Dict[str, int], List[str], List[str]]:
    """
    Compute counts of eligible positions and determine scarce and deep positions.
    """
    all_positions = set().union(*df["Eligible_Positions"].apply(set))
    position_counts = {
        pos: df["Eligible_Positions"].apply(lambda positions: pos in positions).sum() 
        for pos in all_positions
    }
    scarcity_threshold = CONFIG['scarceness']['base'] + CONFIG['scarceness']['bonus']
    deep_threshold = CONFIG['depth']['base'] + CONFIG['depth']['bonus']
    scarce_positions = [pos for pos, count in position_counts.items() if count <= scarcity_threshold]
    deep_positions = [pos for pos, count in position_counts.items() if count >= deep_threshold]
    logging.info("Scarce positions: %s, Deep positions: %s", scarce_positions, deep_positions)
    return position_counts, scarce_positions, deep_positions

def adjust_score_for_scarce_positions(row: pd.Series, max_rank: float, scarce_positions: List[str]) -> float:
    """
    Increase CompositeScore for players eligible at scarce positions.
    """
    if any(pos in scarce_positions for pos in row["Eligible_Positions"]):
        rank_factor = (max_rank - row["Real_Rank"]) / max_rank
        return CONFIG['adjustment']['scarce_multiplier'] * row["CompositeScore"] * (1 + CONFIG['adjustment']['scarce_rank_weight'] * rank_factor)
    return 0.0

def adjust_score_for_deep_positions(row: pd.Series, deep_positions: List[str]) -> float:
    """
    Decrease CompositeScore for players eligible at deep positions.
    """
    if any(pos in deep_positions for pos in row["Eligible_Positions"]):
        return -CONFIG['adjustment']['deep_multiplier'] * row["CompositeScore"]
    return 0.0

def add_ranking_and_adjust_scores(df: pd.DataFrame, scarce_positions: List[str], deep_positions: List[str]) -> pd.DataFrame:
    """
    Compute initial rankings and then adjust CompositeScore based on position eligibility.
    """
    # Rank players based on their original CompositeScore.
    df["Real_Rank"] = df["CompositeScore"].rank(ascending=False, method='min')
    max_rank = df["Real_Rank"].max()

    def compute_adjusted_score(row):
        base_score = row["CompositeScore"]
        adjustment = (
            adjust_score_for_scarce_positions(row, max_rank, scarce_positions) +
            adjust_score_for_deep_positions(row, deep_positions)
        )
        return base_score + adjustment

    df["Adjusted_CompositeScore"] = df.apply(compute_adjusted_score, axis=1)
    df = df.sort_values(by="Adjusted_CompositeScore", ascending=False).reset_index(drop=True)
    df["Adjusted_Rank"] = df["Adjusted_CompositeScore"].rank(ascending=False, method='min')
    return df

def add_vadp_and_tiers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate VADP (Value Over ADP) and assign tiers based on CompositeScore thresholds.
    """
    df["VADP"] = df["Adjusted_Rank"] - df["ADP"]
    sorted_scores = df["CompositeScore"].sort_values(ascending=False).reset_index(drop=True)

    tier_1_cutoff = sorted_scores.iloc[max(10, int(len(sorted_scores) * 0.03))]
    tier_2_cutoff = sorted_scores.iloc[max(30, int(len(sorted_scores) * 0.15))]
    tier_3_cutoff = sorted_scores.iloc[int(len(sorted_scores) * 0.50)]
    tier_4_cutoff = sorted_scores.iloc[int(len(sorted_scores) * 0.80)]
    thresholds = [tier_1_cutoff, tier_2_cutoff, tier_3_cutoff, tier_4_cutoff]

    def assign_tier(score: float) -> int:
        if score >= thresholds[0]:
            return 1
        elif score >= thresholds[1]:
            return 2
        elif score >= thresholds[2]:
            return 3
        elif score >= thresholds[3]:
            return 4
        else:
            return 5

    df["Tier"] = df["CompositeScore"].apply(assign_tier)
    return df

def get_vadp_factor(adp: float) -> float:
    """
    Determine the VADP factor based on ADP value.
    """
    for threshold, factor in CONFIG['draft_round']['vadp_factors']:
        if adp < threshold:
            return factor
    return 0.3

def get_movement_cap(adp: float) -> float:
    """
    Determine the cap on draft movement based on ADP.
    """
    for threshold, cap_factor in CONFIG['draft_round']['movement_caps']:
        if adp < threshold:
            return adp * cap_factor
    return adp * 0.1

def calculate_draft_position(row: pd.Series) -> float:
    """
    Calculate the adjusted draft position based on ADP, adjusted rank, and VADP.
    """
    adp = row["ADP"]
    adjusted_rank = row["Adjusted_Rank"]
    vadp = row["VADP"]
    
    if pd.isna(adp) or pd.isna(adjusted_rank) or pd.isna(vadp):
        return np.nan

    base_weights = CONFIG['draft_round']['weights']
    base_pick = adp * base_weights['adp'] + adjusted_rank * base_weights['rank']
    
    vadp_factor = get_vadp_factor(adp)
    movement_cap = get_movement_cap(adp)
    
    # Adjust pick based on the magnitude and direction of VADP.
    adjustment = vadp_factor * vadp if vadp >= 0 else -vadp_factor * abs(vadp)
    new_pick = base_pick + adjustment
    # Cap the adjustment.
    new_pick = max(new_pick, adp - movement_cap)
    new_pick = min(new_pick, adp + movement_cap)
    return new_pick

def add_suggested_draft_round(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the suggested draft round by adjusting the pick position and converting it.
    """
    df["Suggested_Draft_Round"] = np.ceil(df.apply(calculate_draft_position, axis=1) / 10)
    return df

def create_views(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, pd.DataFrame]]:
    """
    Create multiple views of the DataFrame: overall players, hitters, pitchers, and individual positions.
    """
    common_columns = ["Name", "position", "Team", "Drafted", "Eligible_Positions", "CompositeScore",
                      "Adjusted_CompositeScore", "Suggested_Draft_Round", "Real_Rank",
                      "Adjusted_Rank", "Tier", "VADP", "ADP", "fantasy_team"]
    batting_columns = ["AB", "wOBA", "ISO", "wBsR", "wRC+"]
    pitching_columns = ["IP", "FIP", "WHIP", "K-BB%", "SV"]

    all_players_df = df[common_columns + batting_columns + pitching_columns]

    overall_hitters = df[~df["Eligible_Positions"].apply(lambda pos: "P" in pos)]
    overall_pitchers = df[df["Eligible_Positions"].apply(lambda pos: "P" in pos)]
    hitters_df = overall_hitters[common_columns + batting_columns]
    pitchers_df = overall_pitchers[common_columns + pitching_columns]

    position_dfs = {}
    for pos in CONFIG['league_positions']:
        pos_df = df[df["Eligible_Positions"].apply(lambda positions: pos in positions)]
        if pos_df.empty:
            continue
        if pos == "P":
            filtered = pos_df[common_columns + pitching_columns]
        else:
            filtered = pos_df[common_columns + batting_columns]
        position_dfs[pos] = filtered

    return all_players_df, hitters_df, pitchers_df, position_dfs

def export_to_excel(all_players_df: pd.DataFrame, hitters_df: pd.DataFrame, pitchers_df: pd.DataFrame,
                    position_dfs: Dict[str, pd.DataFrame], output_directory: str = "output") -> str:
    """
    Export the different views into an Excel workbook with multiple sheets.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    xlsx_file = os.path.join(output_directory, f"draft_strategy_{timestamp}.xlsx")
    with pd.ExcelWriter(xlsx_file, engine='openpyxl') as writer:
        all_players_df.to_excel(writer, sheet_name='All players', index=False)
        if not hitters_df.empty:
            hitters_df.to_excel(writer, sheet_name='Overall Hitters', index=False)
        if not pitchers_df.empty:
            pitchers_df.to_excel(writer, sheet_name='Overall Pitchers', index=False)
        for pos, pos_df in position_dfs.items():
            if pos == "P":
                continue  # Already included in pitchers view.
            sheet_name = sanitize_filename(str(pos))[:31]
            pos_df.to_excel(writer, sheet_name=sheet_name, index=False)
    logging.info("Excel workbook saved to %s", xlsx_file)
    return xlsx_file

def analyze_and_adjust_rankings(file_path: Optional[str] = None) -> pd.DataFrame:
    """
    Orchestrate the data processing steps: load, process, adjust scores, and export.
    """
    df = load_data(file_path)
    df = add_eligibility_column(df)
    df = filter_players(df)
    df = restrict_to_top_players(df)

    _, scarce_positions, deep_positions = compute_positional_depth(df)
    df = add_ranking_and_adjust_scores(df, scarce_positions, deep_positions)
    df = add_vadp_and_tiers(df)
    df = add_suggested_draft_round(df)
    
    all_players_df, hitters_df, pitchers_df, position_dfs = create_views(df)
    export_to_excel(all_players_df, hitters_df, pitchers_df, position_dfs)
    
    return df

if __name__ == "__main__":
    analyze_and_adjust_rankings()

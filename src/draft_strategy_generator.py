import os
import glob
import re
import datetime
import logging
import json
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
        'scarce_multiplier': 0.08,
        'scarce_rank_weight': 0.5,
        'deep_multiplier': 0.05,
    },
    'draft_round': {
        'weights': {'adp': 0.7, 'rank': 0.3},
        'vadp_factors': [(50, 0.1), (100, 0.2), (float('inf'), 0.3)],
        'movement_caps': [(50, 0.3), (100, 0.2), (float('inf'), 0.1)]
    },
    'top_n_hitters': 150,
    'top_n_pitchers': 100,
    'top_n_adp': 120,
    'adp_keep_threshold': 120,
    'min_composite_score': 0,
    'league_positions': ["1B", "2B", "3B", "SS", "SP", "RP", "P", "C", "OF", "MI", "CI"],
    'value_normalization': {
        # Composite z-score remains primary; FPTS only helps align hitter/pitcher scales.
        'weights': {'composite_z': 0.75, 'fpts_z': 0.20, 'var_z': 0.05},
    },
}


def _num_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(0.0, index=df.index, dtype=float)
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0)

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
    Insert a placeholder 'Drafted' column and normalize column names.
    """
    if file_path is None:
        file_path = get_latest_free_agents_file()
    df = pd.read_csv(file_path)
    if "Drafted" not in df.columns:
        df.insert(3, "Drafted", "")
    # Map prefixed column names to unprefixed names the generator expects
    col_map = {
        "proj_CompositeScore": "CompositeScore",
        "proj_PositionZScore": "PositionZScore",
        "proj_VAR": "PositionVAR",
        "proj_ADP": "ADP",
        "proj_AB": "AB",
        "proj_wOBA": "wOBA",
        "proj_ISO": "ISO",
        "proj_wBsR": "wBsR",
        "proj_wRC+": "wRC+",
        "proj_IP": "IP",
        "proj_FIP": "FIP",
        "proj_WHIP": "WHIP",
        "proj_K-BB%": "K-BB%",
        "proj_SV": "SV",
        "proj_GS": "GS",
        "proj_HLD": "HLD",
    }
    for old, new in col_map.items():
        if old in df.columns and new not in df.columns:
            df[new] = df[old]
    return df

def calculate_league_fpts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate projected fantasy points using the league's actual ESPN scoring rules.
    Maps ESPN scoring categories to FanGraphs projection columns.
    Falls back gracefully if scoring_settings.json doesn't exist.
    """
    import json
    settings_path = os.path.join("output", "scoring_settings.json")
    if not os.path.exists(settings_path):
        logging.warning("No scoring_settings.json found — cannot calculate league FPTS")
        return df

    with open(settings_path) as f:
        scoring = json.load(f)

    # Map ESPN stat names → FanGraphs projection columns
    # Hitter stats (only apply to non-pitchers)
    hitter_map = {
        "H":    "proj_H",
        "1B":   "proj_1B",
        "2B":   "proj_2B",
        "3B":   "proj_3B",
        "HR":   "proj_HR",
        "R":    "proj_R",
        "RBI":  "proj_RBI",
        "B_BB": "proj_BB",
        "SB":   "proj_SB",
        "CS":   "proj_CS",
        "B_SO": "proj_SO",
        "HBP":  "proj_HBP",
    }
    # Pitcher stats (only apply to pitchers)
    pitcher_map = {
        "K":    "proj_SO",     # Strikeouts thrown
        "W":    "proj_W",
        "L":    "proj_L",
        "SV":   "proj_SV",
        "HLD":  "proj_HLD",
        "QS":   "proj_QS",
        "ER":   "proj_ER",
        "P_H":  "proj_H",     # Hits allowed
        "P_BB": "proj_BB",    # Walks allowed
    }
    # OUTS is special: IP * 3
    has_outs = "OUTS" in scoring

    pos_series = df["position"].astype(str) if "position" in df.columns else pd.Series("", index=df.index, dtype=str)
    has_pitcher_tag = pos_series.str.contains(r"Pitcher|(?:^|[,\s])P(?:$|[,\s])", regex=True, na=False)
    has_hitter_tag = pos_series.str.contains(r"C|1B|2B|3B|SS|OF|DH", regex=True, na=False)
    gs = _num_series(df, "proj_GS")
    sv = _num_series(df, "proj_SV")
    hld = _num_series(df, "proj_HLD")
    ip = _num_series(df, "proj_IP")
    pa = _num_series(df, "proj_PA")
    # Handle ESPN "Unknown" position rows by inferring role from projections.
    inferred_pitcher_tag = has_pitcher_tag | (
        ((gs > 0.1) | (sv > 0.5) | (hld > 0.5) | (ip >= 15.0)) & (pa < 100.0)
    )
    inferred_hitter_tag = has_hitter_tag | (pa >= 100.0)
    is_two_way = inferred_pitcher_tag & inferred_hitter_tag
    is_pitcher_only = inferred_pitcher_tag & ~inferred_hitter_tag
    is_hitter_only = ~inferred_pitcher_tag

    hitter_pts = pd.Series(0.0, index=df.index)
    pitcher_pts = pd.Series(0.0, index=df.index)

    # Calculate hitter points
    for espn_stat, fg_col in hitter_map.items():
        if espn_stat in scoring and fg_col in df.columns:
            vals = pd.to_numeric(df[fg_col], errors="coerce").fillna(0)
            hitter_pts += vals * scoring[espn_stat]

    # Calculate pitcher points
    for espn_stat, fg_col in pitcher_map.items():
        if espn_stat in scoring and fg_col in df.columns:
            vals = pd.to_numeric(df[fg_col], errors="coerce").fillna(0)
            pitcher_pts += vals * scoring[espn_stat]

    # OUTS = IP * 3
    if has_outs and "proj_IP" in df.columns:
        ip_vals = pd.to_numeric(df["proj_IP"], errors="coerce").fillna(0)
        pitcher_pts += ip_vals * 3 * scoring["OUTS"]

    # Assign:
    # - hitter-only players get hitter points
    # - pitcher-only players get pitcher points
    # - two-way players get their stronger side so they aren't artificially suppressed
    df["League_FPTS"] = 0.0
    df.loc[is_hitter_only, "League_FPTS"] = hitter_pts[is_hitter_only]
    df.loc[is_pitcher_only, "League_FPTS"] = pitcher_pts[is_pitcher_only]
    if is_two_way.any():
        tw_h = hitter_pts[is_two_way]
        tw_p = pitcher_pts[is_two_way]
        df.loc[is_two_way, "League_FPTS"] = np.maximum(tw_h, tw_p)
        df.loc[is_two_way, "FPTS_Source"] = np.where(tw_h >= tw_p, "TW_H", "TW_P")
    df.loc[is_hitter_only, "FPTS_Source"] = "H"
    df.loc[is_pitcher_only, "FPTS_Source"] = "P"

    # Log summary
    h_pts = df.loc[~is_pitcher_only & (df["League_FPTS"] > 0), "League_FPTS"]
    p_pts = df.loc[is_pitcher_only & (df["League_FPTS"] != 0), "League_FPTS"]
    logging.info("Two-way players detected: %d", int(is_two_way.sum()))
    if not h_pts.empty:
        logging.info("Hitter League FPTS: top=%s, median=%s", round(h_pts.max(), 1), round(h_pts.median(), 1))
    if not p_pts.empty:
        logging.info("Pitcher League FPTS: top=%s, median=%s", round(p_pts.max(), 1), round(p_pts.median(), 1))

    return df


# Fallback positions for players ESPN labels "Unknown" (pre-season issue)
KNOWN_POSITIONS = {
    "Shohei Ohtani": "DH, OF",
    "Fernando Tatis Jr.": "OF, SS",
    "Nick Kurtz": "1B, DH",
    "CJ Abrams": "SS",
    "James Wood": "OF",
    "Brent Rooker": "DH, OF",
    "Manny Machado": "3B, DH",
    "Jackson Merrill": "OF",
    "Shea Langeliers": "C",
    "Lawrence Butler": "OF, 1B",
    "Teoscar Hernandez": "OF, DH",
    "Yordan Alvarez": "DH, OF",
    "Adley Rutschman": "C",
    "Salvador Perez": "C, DH",
    "Willy Adames": "SS",
}


def map_position_eligibility(row) -> Set[str]:
    """
    Map a player's position string to a set of eligible positions.
    Uses projected GS/SV/HLD to distinguish SP vs RP for pitchers.
    Falls back to KNOWN_POSITIONS and FanGraphs proj_Pos for Unknown players.
    """
    position = str(row["position"]) if "position" in row.index else ""

    # Fix Unknown positions
    if position in ("Unknown", "", "nan"):
        name = str(row.get("Name", ""))
        if name in KNOWN_POSITIONS:
            position = KNOWN_POSITIONS[name]
        else:
            # Try FanGraphs projected position
            fg_pos = str(row.get("proj_Pos", row.get("Pos", "")))
            if fg_pos and fg_pos not in ("nan", "", "None"):
                position = fg_pos

    eligible = set()
    has_hitter_elig = False
    if "C" in position:
        eligible.add("C")
        has_hitter_elig = True
    if "1B" in position:
        eligible.update(["1B", "CI"])
        has_hitter_elig = True
    if "2B" in position:
        eligible.update(["2B", "MI"])
        has_hitter_elig = True
    if "SS" in position:
        eligible.update(["SS", "MI"])
        has_hitter_elig = True
    if "3B" in position:
        eligible.update(["3B", "CI"])
        has_hitter_elig = True
    if "OF" in position:
        eligible.add("OF")
        has_hitter_elig = True
    if "DH" in position:
        has_hitter_elig = True

    # Infer pitcher role for "Unknown" rows when projections strongly indicate pitcher usage.
    # Prefer raw projection columns for role inference; normalized score columns
    # (SV/GS/HLD/IP/PA) are not reliable for this purpose.
    def _row_num(primary: str, fallback: str) -> float:
        val = row.get(primary, row.get(fallback, 0))
        if pd.isna(val):
            return 0.0
        try:
            return float(val)
        except Exception:
            return 0.0

    gs = _row_num("proj_GS", "GS")
    sv = _row_num("proj_SV", "SV")
    hld = _row_num("proj_HLD", "HLD")
    ip = _row_num("proj_IP", "IP")
    pa = _row_num("proj_PA", "PA")
    inferred_pitcher_signal = ((gs > 0.1) or (sv > 0.5) or (hld > 0.5) or (ip >= 15.0)) and (pa < 100.0)
    has_pitcher_elig = ("P" in position or "Pitcher" in position or inferred_pitcher_signal)
    if has_pitcher_elig:
        eligible.add("P")
        if gs > 0:
            eligible.add("SP")
        if sv > 0 or hld > 0 or gs == 0:
            eligible.add("RP")
    if has_hitter_elig:
        # Keep all hitters (including two-way players) eligible for UTIL.
        eligible.add("UTIL")
    return eligible

def add_eligibility_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add the 'Eligible_Positions' column to the DataFrame.
    """
    df["Eligible_Positions"] = df.apply(map_position_eligibility, axis=1)
    return df


def _is_pitcher_mask(df: pd.DataFrame) -> pd.Series:
    """Identify pitchers using parsed eligibility when available."""
    if "Eligible_Positions" in df.columns:
        hitter_tags = {"C", "1B", "2B", "3B", "SS", "OF", "MI", "CI", "UTIL"}
        return df["Eligible_Positions"].apply(
            lambda pos: (
                isinstance(pos, (set, list, tuple))
                and ("P" in pos)
                and not bool(set(pos) & hitter_tags)
            )
        )
    if "position" in df.columns:
        return df["position"].astype(str).str.contains("Pitcher|P", na=False)
    return pd.Series(False, index=df.index)


def _group_zscore(values: pd.Series) -> pd.Series:
    """Safe z-score transform that returns 0s for empty/constant groups."""
    vals = pd.to_numeric(values, errors="coerce")
    mean = vals.mean()
    std = vals.std()
    if pd.isna(std) or std < 1e-6:
        return pd.Series(0.0, index=vals.index)
    return ((vals - mean) / std).fillna(0.0)


def add_cross_position_value_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a cross-position value score for draft decisions:
    - Primary: position-relative composite z-score
    - Secondary: position-relative fantasy point z-score
    - Tertiary: position-relative VAR z-score when available
    """
    if df.empty:
        return df

    is_pitcher = _is_pitcher_mask(df)
    composite_z = pd.Series(0.0, index=df.index, dtype=float)
    fpts_z = pd.Series(0.0, index=df.index, dtype=float)
    var_z = pd.Series(0.0, index=df.index, dtype=float)

    existing_comp_z_col = None
    if "PositionZScore" in df.columns:
        existing_comp_z_col = "PositionZScore"
    elif "proj_PositionZScore" in df.columns:
        existing_comp_z_col = "proj_PositionZScore"

    existing_var_col = None
    if "PositionVAR" in df.columns:
        existing_var_col = "PositionVAR"
    elif "proj_VAR" in df.columns:
        existing_var_col = "proj_VAR"

    for mask in (is_pitcher, ~is_pitcher):
        idx = df.index[mask]
        if len(idx) == 0:
            continue

        group_fpts_z = pd.Series(0.0, index=idx, dtype=float)
        if "League_FPTS" in df.columns:
            group_fpts_z = _group_zscore(df.loc[idx, "League_FPTS"])
            fpts_z.loc[idx] = group_fpts_z

        if existing_comp_z_col is not None:
            comp_vals = pd.to_numeric(df.loc[idx, existing_comp_z_col], errors="coerce")
            comp_filled = comp_vals.fillna(0.0)
            composite_z.loc[idx] = comp_filled

            # Some merged rows (notably certain relievers) can have stale/zero composite
            # despite strong scoring projections. Recover their composite signal from
            # league-scoring FPTS within role group.
            if "CompositeScore" in df.columns and "League_FPTS" in df.columns:
                comp_score = pd.to_numeric(df.loc[idx, "CompositeScore"], errors="coerce").fillna(0.0)
                fallback_mask = (comp_filled.abs() < 1e-9) & (comp_score <= 0) & (group_fpts_z > 0)
                if fallback_mask.any():
                    fallback_idx = fallback_mask[fallback_mask].index
                    composite_z.loc[fallback_idx] = group_fpts_z.loc[fallback_idx]
        else:
            composite_z.loc[idx] = _group_zscore(df.loc[idx, "CompositeScore"])

        if existing_var_col is not None:
            var_z.loc[idx] = _group_zscore(df.loc[idx, existing_var_col])

    w = CONFIG["value_normalization"]["weights"]
    df["Composite_ZScore"] = composite_z.round(4)
    df["FPTS_ZScore"] = fpts_z.round(4)
    df["VAR_ZScore"] = var_z.round(4)
    df["CompositeValueScore"] = (
        w["composite_z"] * df["Composite_ZScore"] +
        w["fpts_z"] * df["FPTS_ZScore"] +
        w["var_z"] * df["VAR_ZScore"]
    ).round(4)

    logging.info(
        "Cross-position value score built: CompositeValueScore (w_comp=%.2f, w_fpts=%.2f, w_var=%.2f)",
        w["composite_z"], w["fpts_z"], w["var_z"]
    )
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
    
    # Keep players with non-zero composite OR meaningful market signal (good ADP).
    adp_vals = pd.to_numeric(df.get("ADP"), errors="coerce")
    valid_players = df[
        df['CompositeScore'].notna() &
        ((df['CompositeScore'] != 0) | ((adp_vals > 0) & (adp_vals <= CONFIG['adp_keep_threshold'])))
    ]
    
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

def restrict_to_top_players(df: pd.DataFrame) -> pd.DataFrame:
    """Keep the full eligible pool; position caps are applied later."""
    working = df[df["CompositeScore"] >= CONFIG['min_composite_score']].copy()
    rank_col = "CompositeValueScore" if "CompositeValueScore" in working.columns else "CompositeScore"
    working = working.sort_values(rank_col, ascending=False).reset_index(drop=True)
    logging.info("Player pool before position caps: %d", len(working))
    return working


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

def adjust_score_for_scarce_positions(row: pd.Series, max_rank: float, scarce_positions: List[str], base_col: str) -> float:
    """
    Increase CompositeScore for players eligible at scarce positions.
    """
    if any(pos in scarce_positions for pos in row["Eligible_Positions"]):
        rank_factor = (max_rank - row["Real_Rank"]) / max_rank
        return CONFIG['adjustment']['scarce_multiplier'] * row[base_col] * (1 + CONFIG['adjustment']['scarce_rank_weight'] * rank_factor)
    return 0.0

def adjust_score_for_deep_positions(row: pd.Series, deep_positions: List[str], base_col: str) -> float:
    """
    Decrease CompositeScore for players eligible at deep positions.
    """
    if any(pos in deep_positions for pos in row["Eligible_Positions"]):
        return -CONFIG['adjustment']['deep_multiplier'] * row[base_col]
    return 0.0

def add_ranking_and_adjust_scores(df: pd.DataFrame, scarce_positions: List[str], deep_positions: List[str]) -> pd.DataFrame:
    """
    Compute initial rankings and then adjust CompositeScore based on position eligibility.
    """
    base_col = "CompositeValueScore" if "CompositeValueScore" in df.columns else "CompositeScore"
    df["Ranking_BaseScore"] = pd.to_numeric(df[base_col], errors="coerce").fillna(0.0)
    # Rank players based on the cross-position normalized score.
    df["Real_Rank"] = df["Ranking_BaseScore"].rank(ascending=False, method='min')
    max_rank = df["Real_Rank"].max()

    def compute_adjusted_score(row):
        base_score = row["Ranking_BaseScore"]
        adjustment = (
            adjust_score_for_scarce_positions(row, max_rank, scarce_positions, "Ranking_BaseScore") +
            adjust_score_for_deep_positions(row, deep_positions, "Ranking_BaseScore")
        )
        return base_score + adjustment

    # Keep existing column name for app/API compatibility.
    df["Adjusted_CompositeScore"] = df.apply(compute_adjusted_score, axis=1)
    df["Adjusted_ValueScore"] = df["Adjusted_CompositeScore"]
    df = df.sort_values(by="Adjusted_CompositeScore", ascending=False).reset_index(drop=True)
    df["Adjusted_Rank"] = df["Adjusted_CompositeScore"].rank(ascending=False, method='min')
    return df

def _assign_tiers_for_group(scores: pd.Series) -> pd.Series:
    """Assign tiers 1-5 based on CompositeScore distribution within a group."""
    sorted_scores = scores.sort_values(ascending=False).reset_index(drop=True)
    n = len(sorted_scores)
    if n == 0:
        return pd.Series(dtype=int)
    tier_1_cutoff = sorted_scores.iloc[max(0, min(n - 1, max(5, int(n * 0.05))))]
    tier_2_cutoff = sorted_scores.iloc[max(0, min(n - 1, max(15, int(n * 0.20))))]
    tier_3_cutoff = sorted_scores.iloc[max(0, min(n - 1, int(n * 0.50)))]
    tier_4_cutoff = sorted_scores.iloc[max(0, min(n - 1, int(n * 0.80)))]
    thresholds = [tier_1_cutoff, tier_2_cutoff, tier_3_cutoff, tier_4_cutoff]

    def assign(score):
        if score >= thresholds[0]: return 1
        elif score >= thresholds[1]: return 2
        elif score >= thresholds[2]: return 3
        elif score >= thresholds[3]: return 4
        else: return 5

    return scores.apply(assign)


def add_vadp_and_tiers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate VADP (Value Over ADP) and assign tiers independently for hitters and pitchers.
    """
    df["VADP"] = df["Adjusted_Rank"] - df["ADP"]
    is_pitcher = _is_pitcher_mask(df)
    tier_col = "CompositeValueScore" if "CompositeValueScore" in df.columns else "CompositeScore"
    df.loc[is_pitcher, "Tier"] = _assign_tiers_for_group(df.loc[is_pitcher, tier_col])
    df.loc[~is_pitcher, "Tier"] = _assign_tiers_for_group(df.loc[~is_pitcher, tier_col])
    df["Tier"] = df["Tier"].astype(int)
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
    df["Recommended_Pick"] = df.apply(calculate_draft_position, axis=1).round(0).astype("Int64")
    df["Suggested_Draft_Round"] = np.ceil(df["Recommended_Pick"] / 10)
    return df

def calculate_fpts_par(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Points Above Replacement (PAR) using League_FPTS.
    Replacement level = the Nth-best player at each position, where N = league demand.
    PAR normalizes hitters and pitchers onto the same value scale.
    """
    if "League_FPTS" not in df.columns:
        logging.warning("League_FPTS missing — skipping PAR calculation")
        df["PAR"] = 0.0
        return df

    roster_slots = _load_roster_slots()

    total_teams = 10

    # For each player, find replacement level at their best position
    replacement_levels: Dict[str, float] = {}
    for pos, slots in roster_slots.items():
        if pos in ("UTIL", "P"):
            continue
        pos_players = df[df["Eligible_Positions"].apply(lambda ep: pos in ep)]
        league_demand = slots * total_teams
        sorted_fpts = pos_players["League_FPTS"].sort_values(ascending=False).reset_index(drop=True)
        if len(sorted_fpts) > league_demand:
            replacement_levels[pos] = float(sorted_fpts.iloc[league_demand])
        elif not sorted_fpts.empty:
            replacement_levels[pos] = float(sorted_fpts.iloc[-1])
        else:
            replacement_levels[pos] = 0.0

    # Handle P/RP: pitchers
    for pos in ("RP", "SP", "P"):
        if pos in roster_slots:
            pos_players = df[df["Eligible_Positions"].apply(lambda ep: pos in ep)]
            demand = roster_slots[pos] * total_teams
            sorted_fpts = pos_players["League_FPTS"].sort_values(ascending=False).reset_index(drop=True)
            if len(sorted_fpts) > demand:
                replacement_levels[pos] = float(sorted_fpts.iloc[demand])
            elif not sorted_fpts.empty:
                replacement_levels[pos] = float(sorted_fpts.iloc[-1])

    logging.info("Replacement levels (FPTS): %s",
                 {k: round(v, 1) for k, v in sorted(replacement_levels.items())})

    # Calculate PAR: player's FPTS minus the best replacement level among their positions
    def calc_par(row):
        fpts = row["League_FPTS"]
        if pd.isna(fpts):
            return 0.0
        best_repl = None
        for pos in row["Eligible_Positions"]:
            if pos in replacement_levels:
                repl = replacement_levels[pos]
                if best_repl is None or repl > best_repl:
                    best_repl = repl
        if best_repl is None:
            return 0.0
        return fpts - best_repl

    df["PAR"] = df.apply(calc_par, axis=1).round(1)

    h_par = df.loc[~df["Eligible_Positions"].apply(lambda ep: "P" in ep), "PAR"]
    p_par = df.loc[df["Eligible_Positions"].apply(lambda ep: "P" in ep), "PAR"]
    logging.info("Hitter PAR: top=%.1f, median=%.1f", h_par.max(), h_par.median())
    logging.info("Pitcher PAR: top=%.1f, median=%.1f", p_par.max(), p_par.median())

    return df


def _load_roster_slots() -> Dict[str, int]:
    """Load roster slot configuration with sensible defaults."""
    settings_path = os.path.join("output", "roster_settings.json")
    if os.path.exists(settings_path):
        with open(settings_path) as f:
            raw_slots = json.load(f)
        name_map = {"2B/SS": "MI", "1B/3B": "CI"}
        skip = {"BE", "IL", "IL+", "IR", "IR+"}
        roster_slots: Dict[str, int] = {}
        for k, v in raw_slots.items():
            try:
                vv = int(v)
            except Exception:
                continue
            if k not in skip and vv > 0:
                roster_slots[name_map.get(k, k)] = vv
        if roster_slots:
            return roster_slots
    return {"C": 1, "1B": 1, "2B": 1, "3B": 1, "SS": 1,
            "OF": 3, "MI": 1, "CI": 1, "UTIL": 1, "P": 6, "RP": 3}


def _slot_accepts_player(slot: str, eligible: Set[str]) -> bool:
    if slot == "MI":
        return bool(eligible & {"MI", "2B", "SS"})
    if slot == "CI":
        return bool(eligible & {"CI", "1B", "3B"})
    if slot == "UTIL":
        return bool(eligible & {"C", "1B", "2B", "3B", "SS", "OF", "MI", "CI", "UTIL"})
    if slot == "P":
        return bool(eligible & {"P", "SP", "RP"})
    return slot in eligible


def cap_to_roster_demand(df: pd.DataFrame, total_teams: int = 10) -> pd.DataFrame:
    """
    Keep only realistically draftable players:
    union of top N players per roster slot where N = slot_count * teams.
    """
    if df.empty or "Eligible_Positions" not in df.columns:
        return df

    roster_slots = _load_roster_slots()
    teams = max(1, int(total_teams))

    # Dynamic caps by summing slots a position can fill.
    # This mirrors "eligible spot" demand:
    # - 1B/3B include CI
    # - 2B/SS include MI
    # - OF includes UTIL
    # - SP/RP include generic P
    # - C remains C-only (per your preference)
    target_caps = {
        "C": int(roster_slots.get("C", 0)) * teams,
        "1B": int(roster_slots.get("1B", 0) + roster_slots.get("CI", 0)) * teams,
        "2B": int(roster_slots.get("2B", 0) + roster_slots.get("MI", 0)) * teams,
        "3B": int(roster_slots.get("3B", 0) + roster_slots.get("CI", 0)) * teams,
        "SS": int(roster_slots.get("SS", 0) + roster_slots.get("MI", 0)) * teams,
        "OF": int(roster_slots.get("OF", 0) + roster_slots.get("UTIL", 0)) * teams,
        "SP": int(roster_slots.get("SP", 0) + roster_slots.get("P", 0)) * teams,
        "RP": int(roster_slots.get("RP", 0) + roster_slots.get("P", 0)) * teams,
    }
    rank_col = "Adjusted_CompositeScore" if "Adjusted_CompositeScore" in df.columns else (
        "CompositeValueScore" if "CompositeValueScore" in df.columns else "CompositeScore"
    )
    working = df.copy()
    working["Eligible_Positions"] = working["Eligible_Positions"].apply(
        lambda p: set(p) if isinstance(p, (set, list, tuple)) else set()
    )
    working[rank_col] = pd.to_numeric(working.get(rank_col), errors="coerce").fillna(-9999.0)

    preferred_order = ["C", "1B", "2B", "3B", "SS", "OF", "SP", "RP"]
    slot_order = [s for s in preferred_order if int(target_caps.get(s, 0) or 0) > 0]

    keep_idx: Set[int] = set()
    for slot in slot_order:
        demand = int(target_caps.get(slot, 0) or 0)
        if demand <= 0:
            continue
        slot_pool = working[working["Eligible_Positions"].apply(lambda ep: _slot_accepts_player(slot, ep))]
        if slot_pool.empty:
            continue
        top_slot = slot_pool.sort_values(rank_col, ascending=False).head(demand)
        keep_idx.update(top_slot.index.tolist())

    # Always keep already-drafted players if present.
    if "Drafted" in working.columns:
        drafted_idx = working[working["Drafted"].fillna("").astype(str).str.strip() != ""].index.tolist()
        keep_idx.update(drafted_idx)

    if not keep_idx:
        return working.sort_values(rank_col, ascending=False).head(200).reset_index(drop=True)

    capped = working.loc[sorted(keep_idx)].copy()
    capped = capped.sort_values(rank_col, ascending=False).reset_index(drop=True)
    logging.info("Capped player pool to roster demand: %d -> %d", len(df), len(capped))
    return capped


def create_views(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, pd.DataFrame]]:
    """
    Create multiple views of the DataFrame: overall players, hitters, pitchers, and individual positions.
    """
    common_columns = ["Name", "position", "Team", "Drafted", "Eligible_Positions", "CompositeScore",
                      "Composite_ZScore", "FPTS_ZScore", "VAR_ZScore", "CompositeValueScore",
                      "Adjusted_CompositeScore", "Adjusted_ValueScore", "Ranking_BaseScore",
                      "Suggested_Draft_Round", "Recommended_Pick", "Real_Rank",
                      "Adjusted_Rank", "Tier", "VADP", "ADP", "fantasy_team", "League_FPTS", "PAR"]
    batting_columns = ["AB", "wOBA", "ISO", "wBsR", "wRC+"]
    pitching_columns = ["IP", "FIP", "WHIP", "K-BB%", "SV"]

    all_players_df = df[[c for c in (common_columns + batting_columns + pitching_columns) if c in df.columns]]

    overall_hitters = df[~df["Eligible_Positions"].apply(lambda pos: "P" in pos)]
    overall_pitchers = df[df["Eligible_Positions"].apply(lambda pos: "P" in pos)]
    hitters_df = overall_hitters[[c for c in (common_columns + batting_columns) if c in overall_hitters.columns]]
    pitchers_df = overall_pitchers[[c for c in (common_columns + pitching_columns) if c in overall_pitchers.columns]]

    position_dfs = {}
    for pos in CONFIG['league_positions']:
        pos_df = df[df["Eligible_Positions"].apply(lambda positions: pos in positions)]
        if pos_df.empty:
            continue
        if pos == "P":
            filtered = pos_df[[c for c in (common_columns + pitching_columns) if c in pos_df.columns]]
        else:
            filtered = pos_df[[c for c in (common_columns + batting_columns) if c in pos_df.columns]]
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
    df = calculate_league_fpts(df)
    df = add_eligibility_column(df)
    df = filter_players(df)
    df = add_cross_position_value_scores(df)
    df = restrict_to_top_players(df)
    df = calculate_fpts_par(df)

    _, scarce_positions, deep_positions = compute_positional_depth(df)
    df = add_ranking_and_adjust_scores(df, scarce_positions, deep_positions)
    df = add_vadp_and_tiers(df)
    df = add_suggested_draft_round(df)
    df = cap_to_roster_demand(df)
    
    all_players_df, hitters_df, pitchers_df, position_dfs = create_views(df)
    export_to_excel(all_players_df, hitters_df, pitchers_df, position_dfs)
    
    return df

if __name__ == "__main__":
    analyze_and_adjust_rankings()

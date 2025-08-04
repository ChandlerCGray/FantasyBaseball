#!/usr/bin/env python3
"""
Fantasy Baseball Analysis Script
"""
import pandas as pd
import re
import unidecode
import logging
from warnings import simplefilter

logger = logging.getLogger(__name__)
pd.set_option('future.no_silent_downcasting', True)
simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

# Comprehensive team abbreviation mapping (all common aliases to 3-letter codes)
TEAM_ABBREVIATION_MAP = {
    # Arizona Diamondbacks
    "ari": "ari", "az": "ari", "arizona": "ari", "diamondbacks": "ari", "d-backs": "ari", "dbacks": "ari",
    # Atlanta Braves
    "atl": "atl", "atlanta": "atl", "braves": "atl",
    # Baltimore Orioles
    "bal": "bal", "baltimore": "bal", "orioles": "bal",
    # Boston Red Sox
    "bos": "bos", "boston": "bos", "red sox": "bos", "redsox": "bos",
    # Chicago Cubs
    "chc": "chc", "cubs": "chc", "chi": "chc",
    # Chicago White Sox
    "cws": "cws", "white sox": "cws", "whitesox": "cws",
    # Cincinnati Reds
    "cin": "cin", "reds": "cin", "cincinnati": "cin",
    # Cleveland Guardians
    "cle": "cle", "cleveland": "cle", "guardians": "cle", "indians": "cle",
    # Colorado Rockies
    "col": "col", "rockies": "col", "colorado": "col",
    # Detroit Tigers
    "det": "det", "tigers": "det", "detroit": "det",
    # Houston Astros
    "hou": "hou", "astros": "hou", "houston": "hou",
    # Kansas City Royals
    "kc": "kcr", "kcr": "kcr", "royals": "kcr", "kansas city": "kcr",
    # Los Angeles Angels
    "laa": "ana", "ana": "ana", "angels": "ana", "los angeles angels": "ana",
    # Los Angeles Dodgers
    "lad": "lad", "dodgers": "lad", "los angeles dodgers": "lad",
    # Miami Marlins
    "mia": "mia", "marlins": "mia", "miami": "mia",
    # Milwaukee Brewers
    "mil": "mil", "brewers": "mil", "milwaukee": "mil",
    # Minnesota Twins
    "min": "min", "twins": "min", "minnesota": "min",
    # New York Yankees
    "nyy": "nyy", "yankees": "nyy", "new york yankees": "nyy",
    # New York Mets
    "nym": "nym", "mets": "nym", "new york mets": "nym",
    # Oakland Athletics
    "oak": "oak", "athletics": "oak", "a's": "oak", "as": "oak", "oakland": "oak",
    # Philadelphia Phillies
    "phi": "phi", "phillies": "phi", "philadelphia": "phi",
    # Pittsburgh Pirates
    "pit": "pit", "pirates": "pit", "pittsburgh": "pit",
    # San Diego Padres
    "sd": "sdg", "sdg": "sdg", "padres": "sdg", "san diego": "sdg",
    # Seattle Mariners
    "sea": "sea", "mariners": "sea", "seattle": "sea",
    # San Francisco Giants
    "sf": "sf", "sfg": "sf", "giants": "sf", "san francisco": "sf",
    # St. Louis Cardinals
    "stl": "stl", "cards": "stl", "cardinals": "stl", "st. louis": "stl",
    # Tampa Bay Rays
    "tbr": "tb", "tb": "tb", "rays": "tb", "tampa bay": "tb",
    # Texas Rangers
    "tex": "tex", "rangers": "tex", "texas": "tex",
    # Toronto Blue Jays
    "tor": "tor", "blue jays": "tor", "bluejays": "tor", "toronto": "tor",
    # Washington Nationals
    "was": "wsh", "wsh": "wsh", "nationals": "wsh", "washington": "wsh"
}

VALID_POSITIONS = {"C", "1B", "2B", "3B", "SS", "OF", "DH"}
IGNORE_KEYWORDS = {"DL", "IL"}


def classify_player(norm_positions):
    roles = set()
    for slot in norm_positions:
        try:
            slot = str(slot).upper()
            if any(kw in slot for kw in IGNORE_KEYWORDS):
                continue
            if '/' in slot:
                continue
            if slot in {"SP", "RP"}:
                roles.add("Pitcher")
            elif slot in VALID_POSITIONS:
                roles.add(slot)
        except Exception:
            continue

    if not roles:
        return "Unknown"
    if roles == {"Pitcher"}:
        return "Pitcher"
    return ", ".join(sorted(roles))


def z_score(series):
    mean, std = series.mean(), series.std()
    std = std if std > 1e-6 else 1e-6
    return (series - mean) / std


def normalize_stats(df, metrics, prefix, invert_metrics=None):
    if invert_metrics is None:
        invert_metrics = set()
    for metric in metrics:
        col = prefix + metric
        if col in df:
            series = df[col]
            if metric in invert_metrics:
                series = -series
            df[col] = z_score(series)
    return df


def composite_score(row, weights, prefix):
    score = 0.0
    stats_used = 0
    for stat, weight in weights.items():
        col = prefix + stat
        if col in row.index and pd.notna(row[col]):
            score += row[col] * weight
            stats_used += 1
    return score, stats_used


def merge_on_name_team(fa_df, fg_df):
    for df in (fa_df, fg_df):
        df['clean_name'] = df['name'].apply(lambda x: unidecode.unidecode(str(x)).lower().strip())
        df['clean_team'] = df['team'].str.lower().map(TEAM_ABBREVIATION_MAP)

    merged = pd.merge(
        fa_df,
        fg_df,
        on=['clean_name', 'clean_team'],
        how='outer',
        suffixes=('_fa', '_fg')
    )
    return fa_df, fg_df, merged


def merge_with_fallback(fa_df, fg_df, merged):
    unmatched = merged[merged["team_fg"].isna()]
    if unmatched.empty:
        return merged
    fallback = pd.merge(
        fa_df,
        fg_df.drop(columns=["clean_team"]),
        on="clean_name",
        how="left",
        suffixes=("_fa", "_fg"),
    )
    for col in fallback.columns:
        if isinstance(col, str) and col.endswith("_fg"):
            merged[col] = merged[col].combine_first(fallback[col])
    return merged


def determine_position(row):
    slots = row if isinstance(row, (list, tuple, pd.Series)) else []
    return classify_player(slots)


def merge_data(fa_df, fg_df):
    if fa_df.empty or fg_df.empty:
        logger.warning("Merge aborted: one or both datasets are empty.")
        return pd.DataFrame()

    fa_df, fg_df, merged = merge_on_name_team(fa_df, fg_df)
    merged = merge_with_fallback(fa_df, fg_df, merged)

    if "eligible_positions" in merged.columns:
        pos_series = merged["eligible_positions"]
    elif "position" in merged.columns:
        pos_series = merged["position"]
    else:
        pos_series = pd.Series(["Unknown"] * len(merged), index=merged.index)
    merged["position"] = pos_series.apply(determine_position)

    stat_cols = merged.select_dtypes(include=["number"]).columns
    merged[stat_cols] = merged[stat_cols].fillna(0)

    return merged


def rank_free_agents(merged_df):
    if "position" not in merged_df:
        logger.error("'position' column not found.")
        return pd.DataFrame()

    # Normalized weights that sum to 1.0 for consistency
    hitter_weights = {'wOBA': 0.26, 'ISO': 0.22, 'wBsR': 0.04, 'AB': 0.30, 'wRC+': 0.17}  # Sum: 1.00
    pitcher_weights = {'K-BB%': 0.10, 'IP': 0.40, 'WHIP': 0.05, 'FIP': 0.35, 'SV': 0.10}  # Sum: 1.00

    hitters = merged_df[~merged_df["position"].str.contains("Pitcher", na=False)].copy()
    pitchers = merged_df[merged_df["position"].str.contains("Pitcher", na=False)].copy()

    if "AB" in hitters.columns:
        hitters = hitters[hitters["AB"] >= 250]
    if all(col in pitchers.columns for col in ["IP", "SV"]):
        ip = pitchers["IP"]
        sv = pitchers["SV"]
        pitchers = pitchers[(ip >= 10) & ((sv > 20) | (ip >= 100))]

    invert_pitcher = {"FIP", "WHIP"}

    hitters = normalize_stats(hitters, list(hitter_weights), "proj_")
    pitchers = normalize_stats(pitchers, list(pitcher_weights), "proj_", invert_metrics=invert_pitcher)
    
    # Calculate projected scores and track data completeness
    hitter_proj_results = hitters.apply(lambda r: composite_score(r, hitter_weights, "proj_"), axis=1)
    hitters["proj_CompositeScore"] = [result[0] for result in hitter_proj_results]
    hitters["proj_stats_used"] = [result[1] for result in hitter_proj_results]
    
    pitcher_proj_results = pitchers.apply(lambda r: composite_score(r, pitcher_weights, "proj_"), axis=1)
    pitchers["proj_CompositeScore"] = [result[0] for result in pitcher_proj_results]
    pitchers["proj_stats_used"] = [result[1] for result in pitcher_proj_results]

    hitters = normalize_stats(hitters, list(hitter_weights), "curr_")
    pitchers = normalize_stats(pitchers, list(pitcher_weights), "curr_", invert_metrics=invert_pitcher)
    
    # Calculate current scores and track data completeness
    hitter_curr_results = hitters.apply(lambda r: composite_score(r, hitter_weights, "curr_"), axis=1)
    hitters["curr_CompositeScore"] = [result[0] for result in hitter_curr_results]
    hitters["curr_stats_used"] = [result[1] for result in hitter_curr_results]
    
    pitcher_curr_results = pitchers.apply(lambda r: composite_score(r, pitcher_weights, "curr_"), axis=1)
    pitchers["curr_CompositeScore"] = [result[0] for result in pitcher_curr_results]
    pitchers["curr_stats_used"] = [result[1] for result in pitcher_curr_results]

    df = pd.concat([hitters, pitchers], ignore_index=True)

    if "name_fa" in df.columns and "name_fg" in df.columns:
        df["Name"] = df["name_fa"].combine_first(df["name_fg"])
    elif "name_fa" in df.columns:
        df["Name"] = df["name_fa"]
    else:
        df["Name"] = df["name_fg"]

    if "team_fa" in df.columns and "team_fg" in df.columns:
        df["Team"] = df["team_fa"].combine_first(df["team_fg"])
    elif "team_fa" in df.columns:
        df["Team"] = df["team_fa"]
    else:
        df["Team"] = df["team_fg"]

    df["ScoreDelta"] = df["curr_CompositeScore"] - df["proj_CompositeScore"]
    
    # Add normalized value scores for better cross-position comparison
    df = add_normalized_value_scores(df)
    
    return df.sort_values(by="proj_CompositeScore", ascending=False)


def add_normalized_value_scores(df):
    """Add normalized value scores that allow fair comparison between hitters and pitchers"""
    if df.empty:
        return df
    
    # Separate hitters and pitchers
    is_pitcher = df["position"].str.contains("Pitcher", na=False)
    hitters = df[~is_pitcher].copy()
    pitchers = df[is_pitcher].copy()
    
    # Calculate position-relative z-scores (how many standard deviations above/below average)
    if not hitters.empty:
        hitter_mean = hitters["proj_CompositeScore"].mean()
        hitter_std = hitters["proj_CompositeScore"].std()
        hitter_std = hitter_std if hitter_std > 1e-6 else 1e-6
        df.loc[~is_pitcher, "proj_PositionZScore"] = (hitters["proj_CompositeScore"] - hitter_mean) / hitter_std
        
        hitter_curr_mean = hitters["curr_CompositeScore"].mean()
        hitter_curr_std = hitters["curr_CompositeScore"].std()
        hitter_curr_std = hitter_curr_std if hitter_curr_std > 1e-6 else 1e-6
        df.loc[~is_pitcher, "curr_PositionZScore"] = (hitters["curr_CompositeScore"] - hitter_curr_mean) / hitter_curr_std
    
    if not pitchers.empty:
        pitcher_mean = pitchers["proj_CompositeScore"].mean()
        pitcher_std = pitchers["proj_CompositeScore"].std()
        pitcher_std = pitcher_std if pitcher_std > 1e-6 else 1e-6
        df.loc[is_pitcher, "proj_PositionZScore"] = (pitchers["proj_CompositeScore"] - pitcher_mean) / pitcher_std
        
        pitcher_curr_mean = pitchers["curr_CompositeScore"].mean()
        pitcher_curr_std = pitchers["curr_CompositeScore"].std()
        pitcher_curr_std = pitcher_curr_std if pitcher_curr_std > 1e-6 else 1e-6
        df.loc[is_pitcher, "curr_PositionZScore"] = (pitchers["curr_CompositeScore"] - pitcher_curr_mean) / pitcher_curr_std
    
    # Calculate percentile ranks within position groups (0-100 scale)
    if not hitters.empty:
        df.loc[~is_pitcher, "proj_PositionPercentile"] = hitters["proj_CompositeScore"].rank(pct=True) * 100
        df.loc[~is_pitcher, "curr_PositionPercentile"] = hitters["curr_CompositeScore"].rank(pct=True) * 100
    
    if not pitchers.empty:
        df.loc[is_pitcher, "proj_PositionPercentile"] = pitchers["proj_CompositeScore"].rank(pct=True) * 100
        df.loc[is_pitcher, "curr_PositionPercentile"] = pitchers["curr_CompositeScore"].rank(pct=True) * 100
    
    # Calculate Value Above Replacement (VAR) - using 25th percentile as "replacement level"
    if not hitters.empty:
        hitter_replacement = hitters["proj_CompositeScore"].quantile(0.25)
        df.loc[~is_pitcher, "proj_VAR"] = hitters["proj_CompositeScore"] - hitter_replacement
        
        hitter_curr_replacement = hitters["curr_CompositeScore"].quantile(0.25)
        df.loc[~is_pitcher, "curr_VAR"] = hitters["curr_CompositeScore"] - hitter_curr_replacement
    
    if not pitchers.empty:
        pitcher_replacement = pitchers["proj_CompositeScore"].quantile(0.25)
        df.loc[is_pitcher, "proj_VAR"] = pitchers["proj_CompositeScore"] - pitcher_replacement
        
        pitcher_curr_replacement = pitchers["curr_CompositeScore"].quantile(0.25)
        df.loc[is_pitcher, "curr_VAR"] = pitchers["curr_CompositeScore"] - pitcher_curr_replacement
    
    # Fill any NaN values with 0
    value_columns = ["proj_PositionZScore", "curr_PositionZScore", "proj_PositionPercentile", 
                    "curr_PositionPercentile", "proj_VAR", "curr_VAR"]
    for col in value_columns:
        if col not in df.columns:
            df[col] = 0
        else:
            df[col] = df[col].fillna(0)
    
    return df

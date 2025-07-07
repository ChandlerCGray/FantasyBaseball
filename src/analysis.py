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
    for stat, weight in weights.items():
        col = prefix + stat
        if col in row.index:
            score += row[col] * weight
    return score


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

    hitter_weights = {'wOBA': 0.30, 'ISO': 0.25, 'wBsR': 0.05, 'AB': 0.35, 'wRC+': 0.20}
    pitcher_weights = {'K-BB%': 0.10, 'IP': 0.40, 'WHIP': 0.05, 'FIP': 0.35, 'SV': 0.10}

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
    hitters["proj_CompositeScore"] = hitters.apply(lambda r: composite_score(r, hitter_weights, "proj_"), axis=1)
    pitchers["proj_CompositeScore"] = pitchers.apply(lambda r: composite_score(r, pitcher_weights, "proj_"), axis=1)

    hitters = normalize_stats(hitters, list(hitter_weights), "curr_")
    pitchers = normalize_stats(pitchers, list(pitcher_weights), "curr_", invert_metrics=invert_pitcher)
    hitters["curr_CompositeScore"] = hitters.apply(lambda r: composite_score(r, hitter_weights, "curr_"), axis=1)
    pitchers["curr_CompositeScore"] = pitchers.apply(lambda r: composite_score(r, pitcher_weights, "curr_"), axis=1)

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
    return df.sort_values(by="proj_CompositeScore", ascending=False)

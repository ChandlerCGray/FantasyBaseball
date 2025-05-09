import pandas as pd
import re
import unidecode
import logging
from warnings import simplefilter

logger = logging.getLogger(__name__)
pd.set_option('future.no_silent_downcasting', True)
simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

TEAM_ABBREVIATION_MAP = {
    "ari": "ari", "az": "ari", "dbacks": "ari", "d-backs": "ari",
    "atl": "atl", "braves": "atl",
    "bal": "bal", "orioles": "bal",
    "bos": "bos", "redsox": "bos",
    "chc": "chc", "chi": "chc", "cubs": "chc",
    "chw": "chw", "cws": "chw", "whitesox": "chw", "white sox": "chw",
    "cin": "cin", "reds": "cin",
    "cle": "cle", "clv": "cle", "ind": "cle", "guardians": "cle", "indians": "cle",
    "col": "col", "rockies": "col",
    "det": "det", "tigers": "det",
    "hou": "hou", "astros": "hou",
    "kc": "kc", "royals": "kc",
    "laa": "laa", "ana": "laa", "angels": "laa",
    "lad": "lad", "dodgers": "lad",
    "mia": "mia", "fla": "mia", "marlins": "mia",
    "mil": "mil", "brewers": "mil",
    "min": "min", "twins": "min",
    "nym": "nym", "mets": "nym",
    "nyy": "nyy", "yankees": "nyy",
    "oak": "ath", "athletics": "ath",
    "phi": "phi", "phillies": "phi",
    "pit": "pit", "pirates": "pit",
    "sd": "sd", "padres": "sd",
    "sf": "sf", "giants": "sf",
    "sea": "sea", "mariners": "sea",
    "stl": "stl", "cards": "stl",
    "tb": "tb", "rays": "tb", "tbr":"tb",
    "tex": "tex", "rangers": "tex",
    "tor": "tor", "blue jays": "tor",
    "wsh": "wsh", "nationals": "wsh"
}


def clean_name(name):
    if not isinstance(name, str): return ""
    name = unidecode.unidecode(name).lower()
    name = re.sub(r"[.\-]", " ", name)
    name = re.sub(r"\bjr\b", "junior", name)
    return re.sub(r"\s+", " ", name).strip()


def clean_team(team):
    if not isinstance(team, str): return ""
    team = unidecode.unidecode(team).lower()
    team = re.sub(r"[.\-]", " ", team)
    team = re.sub(r"\s+", " ", team).strip()
    return TEAM_ABBREVIATION_MAP.get(team, team)

def determine_position(slots):
    if not isinstance(slots, list):
        return "Unknown"

    valid_positions = {"C", "1B", "2B", "3B", "SS", "OF", "DH", "SP", "RP"}
    ignore_keywords = {"UTIL", "UT", "IF", "MI", "CI", "BE", "IL", "IL+", "NA", "Bench"}

    roles = set()
    for slot in slots:
        try:
            slot = str(slot).upper()
            if any(kw in slot for kw in ignore_keywords):
                continue
            if '/' in slot:
                continue  # ignore compound positions
            if slot in {"SP", "RP"}:
                roles.add("Pitcher")
            elif slot in valid_positions:
                roles.add(slot)
        except Exception as e:
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
        col = f"{prefix}{metric}"
        if col in df.columns:
            values = pd.to_numeric(df[col], errors='coerce').fillna(0)
            if metric in invert_metrics:
                values = -values
            df[f"{col}_Z"] = z_score(values)
    return df


def composite_score(row, weights, prefix):
    return sum(row.get(f"{prefix}{k}_Z", 0) * v for k, v in weights.items())


def standardize_fg_df(df):
    df = df.rename(columns={"PlayerName": "name", "TeamName": "team"}) if "PlayerName" in df.columns else df
    if "name" not in df.columns:
        raise ValueError("Missing required column: 'name'")
    df["clean_name"] = df["name"].apply(clean_name)
    if "team" in df.columns:
        df["clean_team"] = df["team"].apply(clean_team)
    return df


def merge_on_name_team(fa_df, fg_df):
    fa_df["clean_name"] = fa_df["name"].apply(clean_name)
    fa_df["clean_team"] = fa_df["team"].apply(clean_team)
    fg_df = standardize_fg_df(fg_df)
    merged = pd.merge(fa_df, fg_df, on=["clean_name", "clean_team"], how="left", suffixes=("_fa", "_fg"))
    return fa_df, fg_df, merged


def merge_with_fallback(fa_df, fg_df, merged):
    unmatched = merged[merged["team_fg"].isna()]
    if unmatched.empty:
        return merged
    fallback = pd.merge(fa_df, fg_df.drop(columns=["clean_team"]), on="clean_name", how="left", suffixes=("_fa", "_fg"))
    for col in fallback:
        if col.endswith("_fg"):
            merged[col] = merged[col].combine_first(fallback[col])
    return merged


def merge_data(fa_df, fg_df):
    if fa_df.empty or fg_df.empty:
        logger.warning("Merge aborted: one or both datasets are empty.")
        return pd.DataFrame()
    
    fa_df, fg_df, merged = merge_on_name_team(fa_df, fg_df)
    merged = merge_with_fallback(fa_df, fg_df, merged)

    merged["position"] = merged.get("eligible_positions", merged.get("position")).apply(determine_position)

    # Fill all stat (non-object) columns with 0
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

    # Hitter eligibility filter
    if "AB" in hitters.columns:
        hitters = hitters[hitters["AB"] >= 250]

    # Pitcher eligibility filter
    if all(col in pitchers.columns for col in ["IP", "SV"]):
        ip = pitchers["IP"]
        sv = pitchers["SV"]
        pitchers = pitchers[(ip >= 10) & ((sv > 20) | (ip >= 100))]

    # Metrics to invert for pitchers so that lower FIP/WHIP become higher Z-scores
    invert_pitcher = {"FIP", "WHIP"}

    # Normalize projected stats
    hitters = normalize_stats(hitters, list(hitter_weights), "proj_")
    pitchers = normalize_stats(
        pitchers,
        list(pitcher_weights),
        "proj_",
        invert_metrics=invert_pitcher
    )

    # Compute projected composite scores
    hitters["proj_CompositeScore"] = hitters.apply(
        lambda r: composite_score(r, hitter_weights, "proj_"), axis=1
    )
    pitchers["proj_CompositeScore"] = pitchers.apply(
        lambda r: composite_score(r, pitcher_weights, "proj_"), axis=1
    )

    # Normalize current stats
    hitters = normalize_stats(hitters, list(hitter_weights), "curr_")
    pitchers = normalize_stats(
        pitchers,
        list(pitcher_weights),
        "curr_",
        invert_metrics=invert_pitcher
    )

    # Compute current composite scores
    hitters["curr_CompositeScore"] = hitters.apply(
        lambda r: composite_score(r, hitter_weights, "curr_"), axis=1
    )
    pitchers["curr_CompositeScore"] = pitchers.apply(
        lambda r: composite_score(r, pitcher_weights, "curr_"), axis=1
    )

    # Combine and finalize output
    df = pd.concat([hitters, pitchers], ignore_index=True)
    df["Name"] = df.get("name_fa").combine_first(df.get("name_fg"))
    df["Team"] = df.get("team_fa").combine_first(df.get("team_fg"))
    df["ScoreDelta"] = df["curr_CompositeScore"] - df["proj_CompositeScore"]

    return df.sort_values(by="proj_CompositeScore", ascending=False)

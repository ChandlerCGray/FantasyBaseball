import pandas as pd
import requests

def fetch_json_df(url, root_key=None):
    """Fetch and return a DataFrame from a JSON API."""
    try:
        data = requests.get(url).json()
        return pd.DataFrame(data if root_key is None else data.get(root_key, []))
    except Exception as e:
        print(f"ERROR: Failed to fetch {url}: {e}")
        return pd.DataFrame()

def prefix_stat_columns(df, prefix, exclude=("playerid", "name", "team", "position")):
    """Prefix all stat columns except identifiers."""
    return df.rename(columns={col: f"{prefix}{col}" for col in df.columns if col not in exclude})

def normalize_identifiers(df, mapping):
    """Standardize column names using a given mapping."""
    return df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})

def unify_identifiers(df):
    """Unify identifier columns after a merge with suffixes."""
    for col in ["name", "team", "position"]:
        x, y = f"{col}_x", f"{col}_y"
        if x in df.columns or y in df.columns:
            df[col] = df.get(x).combine_first(df.get(y))
    return df.drop(columns=[col for col in df.columns if col.endswith("_x") or col.endswith("_y")], errors="ignore")

def preprocess_fangraphs(df, mapping, prefix, position_value=None):
    df = normalize_identifiers(df, mapping)
    df = df.dropna(axis=1, how="all")
    df = df.loc[:, ~df.columns.duplicated()]

    if position_value:
        df["position"] = position_value

    df = prefix_stat_columns(df, prefix)

    if "playerid" in df.columns:
        df["playerid"] = df["playerid"].astype(str)

    return df

PROJECTION_MODELS = {
    "steamer":     {"label": "Steamer",       "ros": "steamerr",       "full": "steamer"},
    "zips":        {"label": "ZiPS",          "ros": "zipss",          "full": "zips"},
    "thebat":      {"label": "THE BAT",       "ros": "thebats",        "full": "thebat"},
    "atc":         {"label": "ATC",           "ros": "atc",            "full": "atc"},
    "fangraphsdc": {"label": "Depth Charts",  "ros": "fangraphsdcros", "full": "fangraphsdc"},
}

def get_fangraphs_merged_data(model: str = "steamer"):
    import os
    from datetime import datetime

    season = os.getenv("SEASON", str(datetime.now().year))

    cfg = PROJECTION_MODELS.get(model, PROJECTION_MODELS["steamer"])
    ros_type, full_type = cfg["ros"], cfg["full"]

    # Try rest-of-season first; fall back to full-season preseason projections
    test = fetch_json_df(f"https://www.fangraphs.com/api/projections?type={ros_type}&stats=bat&pos=all&team=0&players=0&lg=all")
    if test.empty:
        proj_type = full_type
        print(f"INFO: {ros_type} empty — using preseason {full_type} projections")
    else:
        proj_type = ros_type

    urls = {
        "proj_bat": f"https://www.fangraphs.com/api/projections?type={proj_type}&stats=bat&pos=all&team=0&players=0&lg=all",
        "proj_pit": f"https://www.fangraphs.com/api/projections?type={proj_type}&stats=pit&pos=all&team=0&players=0&lg=all",
        "curr_bat": f"https://www.fangraphs.com/api/leaders/major-league/data?age=&pos=all&stats=bat&lg=all&qual=0&season={season}&season1={season}&startdate={season}-03-01&enddate={season}-11-01&month=0&hand=&team=0&pageitems=2000000000&pagenum=1&ind=0&rost=0&players=&type=26&postseason=&sortdir=default&sortstat=WAR",
        "curr_pit": f"https://www.fangraphs.com/api/leaders/major-league/data?age=&pos=all&stats=pit&lg=all&qual=0&season={season}&season1={season}&startdate={season}-03-01&enddate={season}-11-01&month=0&hand=&team=0&pageitems=2000000000&pagenum=1&ind=0&rost=0&players=&type=26&postseason=&sortdir=default&sortstat=WAR",
    }

    try:
        # --- Fetch raw data ---
        proj_bat = fetch_json_df(urls["proj_bat"])
        proj_pit = fetch_json_df(urls["proj_pit"])
        curr_bat = fetch_json_df(urls["curr_bat"], root_key="data")
        curr_pit = fetch_json_df(urls["curr_pit"], root_key="data")

        # --- Normalize and preprocess ---
        proj_bat = preprocess_fangraphs(proj_bat, {"PlayerName": "name", "minpos": "position", "Team": "team"}, "proj_")
        proj_pit = preprocess_fangraphs(proj_pit, {"PlayerName": "name", "Team": "team"}, "proj_", position_value="Pitcher")
        curr_bat = preprocess_fangraphs(curr_bat, {"PlayerName": "name", "TeamName": "team", "Position": "position"}, "curr_")
        curr_pit = preprocess_fangraphs(curr_pit, {"PlayerName": "name", "TeamName": "team"}, "curr_", position_value="Pitcher")

        # --- Merge on playerid (handle empty current stats for preseason) ---
        if curr_bat.empty or "playerid" not in curr_bat.columns:
            bat_df = proj_bat.copy()
            print("INFO: No current batting stats available (preseason) — using projections only")
        else:
            bat_df = pd.merge(proj_bat, curr_bat, on="playerid", how="outer")
            bat_df = unify_identifiers(bat_df)

        if curr_pit.empty or "playerid" not in curr_pit.columns:
            pit_df = proj_pit.copy()
            print("INFO: No current pitching stats available (preseason) — using projections only")
        else:
            pit_df = pd.merge(proj_pit, curr_pit, on="playerid", how="outer")
            pit_df = unify_identifiers(pit_df)

        print(f"INFO: Merged {len(bat_df)} batters and {len(pit_df)} pitchers.")
        return bat_df, pit_df

    except Exception as e:
        print(f"ERROR: Failed to process FanGraphs data: {e}")
        return pd.DataFrame(), pd.DataFrame()

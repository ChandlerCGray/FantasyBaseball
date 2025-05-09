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

def get_fangraphs_merged_data():
    urls = {
        "proj_bat": "https://www.fangraphs.com/api/projections?type=steamerr&stats=bat&pos=all&team=0&players=0&lg=all",
        "proj_pit": "https://www.fangraphs.com/api/projections?type=steamerr&stats=pit&pos=all&team=0&players=0&lg=all",
        "curr_bat": "https://www.fangraphs.com/api/leaders/major-league/data?age=&pos=all&stats=bat&lg=all&qual=0&season=2025&season1=2025&startdate=2025-03-01&enddate=2025-11-01&month=0&hand=&team=0&pageitems=2000000000&pagenum=1&ind=0&rost=0&players=&type=26&postseason=&sortdir=default&sortstat=WAR",
        "curr_pit": "https://www.fangraphs.com/api/leaders/major-league/data?age=&pos=all&stats=pit&lg=all&qual=0&season=2025&season1=2025&startdate=2025-03-01&enddate=2025-11-01&month=0&hand=&team=0&pageitems=2000000000&pagenum=1&ind=0&rost=0&players=&type=26&postseason=&sortdir=default&sortstat=WAR",
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

        # --- Merge on playerid ---
        bat_df = pd.merge(proj_bat, curr_bat, on="playerid", how="outer")
        pit_df = pd.merge(proj_pit, curr_pit, on="playerid", how="outer")

        # --- Unify name, team, position ---
        bat_df = unify_identifiers(bat_df)
        pit_df = unify_identifiers(pit_df)

        print(f"INFO: Merged {len(bat_df)} batters and {len(pit_df)} pitchers.")
        return bat_df, pit_df

    except Exception as e:
        print(f"ERROR: Failed to process FanGraphs data: {e}")
        return pd.DataFrame(), pd.DataFrame()

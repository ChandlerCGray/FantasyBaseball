from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import pandas as pd
import numpy as np
import os
import re, subprocess, sys, tempfile
sys.path.insert(0, str((Path(__file__).resolve().parent.parent)))
from data_utils import expand_positions, format_player_name  # type: ignore
from draft_strategy_generator import analyze_and_adjust_rankings  # type: ignore
from fangraphs_api import PROJECTION_MODELS  # type: ignore

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent

from dotenv import load_dotenv  # type: ignore
load_dotenv(ROOT_DIR / ".env")
TEMPLATES_DIR = ROOT_DIR / "templates"
STATIC_DIR = ROOT_DIR / "static"

app = FastAPI(title="Fantasy Baseball Hub")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

_PROJ_MODEL_LIST = [(k, v["label"]) for k, v in PROJECTION_MODELS.items()]
templates.env.globals["PROJECTION_MODELS"] = _PROJ_MODEL_LIST
templates.env.globals["get_projection_model"] = lambda: os.getenv("PROJECTION_MODEL", "steamer").strip("'\"")


def get_latest_csv() -> str | None:
    out_dir = ROOT_DIR / "output"
    if not out_dir.exists():
        return None
    csvs = sorted(out_dir.glob("free_agents_ranked_*.csv"))
    return str(csvs[-1]) if csvs else None


def _filters_from_qp(qp, teams: list[str]):
    default_team = os.getenv("DEFAULT_TEAM", "")
    fallback = next((t for t in teams if t == default_team), teams[0] if teams else "")
    selected_team = qp.get("team", fallback)
    hide_inj = qp.get("hideInjured", "true").lower() == "true"
    try:
        min_score = float(qp.get("minScore", "-1.0"))
    except ValueError:
        min_score = -1.0
    return selected_team, hide_inj, min_score


def _add_ci_mi(positions: list) -> list:
    """Expand position list with CI/MI eligibility."""
    extra = []
    if any(p in positions for p in ("1B", "3B")):
        extra.append("CI")
    if any(p in positions for p in ("2B", "SS")):
        extra.append("MI")
    return positions + [p for p in extra if p not in positions]

def _prepare_dataframe(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, low_memory=False)
    if "display_name" not in df.columns:
        df["display_name"] = df.apply(format_player_name, axis=1)
    if "norm_positions" not in df.columns:
        df["norm_positions"] = df["position"].apply(expand_positions)
    df["norm_positions"] = df["norm_positions"].apply(lambda xs: _add_ci_mi(xs) if isinstance(xs, list) else xs)
    if "ScoreDelta" not in df.columns and {"curr_CompositeScore","proj_CompositeScore"}.issubset(df.columns):
        df["ScoreDelta"] = df["curr_CompositeScore"] - df["proj_CompositeScore"]
    df["has_valid_position"] = df["norm_positions"].apply(lambda x: isinstance(x, list) and len(x) > 0)
    return df


def _compute_upgrades(df: pd.DataFrame, team: str, hide_injured: bool, min_score: float, filter_pos: str = ""):
    # Don't hide injured from FAs — an injured FA can still be worth picking up
    team_df = df[(df["fantasy_team"] == team) & (df["has_valid_position"])].copy()
    fa_df = df[(df["has_valid_position"]) & ((df["fantasy_team"].isna()) | (df["fantasy_team"].isin(["Free Agent","FA"])))].copy()

    if team_df.empty or fa_df.empty:
        return []

    candidates = fa_df.sort_values("proj_CompositeScore", ascending=False).head(150)
    upgrades = []
    for _, fa in candidates.iterrows():
        for fa_pos in (fa.get("norm_positions") or []):
            eligible = team_df[team_df["norm_positions"].apply(lambda xs: isinstance(xs, list) and fa_pos in xs)]
            if eligible.empty:
                continue
            drops = eligible[eligible["proj_CompositeScore"] < fa["proj_CompositeScore"]]
            if drops.empty:
                continue
            drop = drops.nsmallest(1, "proj_CompositeScore").iloc[0]
            gain = float(fa["proj_CompositeScore"]) - float(drop["proj_CompositeScore"])
            if gain < 0.05:
                continue
            key = (fa_pos, str(drop.get("display_name")))
            existing_idx = next((i for i, u in enumerate(upgrades) if (u["pos"], u["drop"]["display_name"]) == key), None)
            item = {"pos": fa_pos, "add": fa.to_dict(), "drop": drop.to_dict(), "gain": round(gain, 2)}
            if existing_idx is not None:
                if upgrades[existing_idx]["gain"] < gain:
                    upgrades[existing_idx] = item
            else:
                upgrades.append(item)

    result = sorted(upgrades, key=lambda x: x["gain"], reverse=True)
    if filter_pos:
        result = [u for u in result if u["pos"] == filter_pos]
    return result


def _attach_pos_ranks(target_df: pd.DataFrame, all_df: pd.DataFrame) -> pd.DataFrame:
    """Add pos_ranks_str column: e.g. '#4 1B · #12 CI · #7 OF'"""
    # Build per-position rank lookup across all valid players
    all_valid = all_df[all_df["has_valid_position"]].copy()
    rank_maps = {}
    for pos in ("C","1B","2B","3B","SS","OF","DH","P","CI","MI"):
        eligible = all_valid[all_valid["norm_positions"].apply(lambda xs: isinstance(xs, list) and pos in xs)]
        if eligible.empty:
            continue
        rank_maps[pos] = eligible["proj_CompositeScore"].rank(ascending=False, method="min").astype(int)

    def build_str(row):
        parts = []
        for pos in (row.get("norm_positions") or []):
            if pos in rank_maps and row.name in rank_maps[pos].index:
                parts.append(f"#{rank_maps[pos][row.name]} {pos}")
        return " · ".join(parts)

    target_df = target_df.copy()
    target_df["pos_ranks_str"] = target_df.apply(build_str, axis=1)

    def best_rank(row):
        ranks = []
        for pos in (row.get("norm_positions") or []):
            if pos in rank_maps and row.name in rank_maps[pos].index:
                ranks.append(rank_maps[pos][row.name])
        return min(ranks) if ranks else 9999

    target_df["best_pos_rank"] = target_df.apply(best_rank, axis=1)
    return target_df

_FA_COLS = [
    "display_name", "Team", "position", "injury_status", "fantasy_points",
    "proj_CompositeScore", "curr_CompositeScore",
    "proj_HR", "proj_R", "proj_RBI", "proj_SB", "proj_AVG",
    "proj_ERA", "proj_WHIP", "proj_SV", "proj_IP", "proj_K-BB%",
]

def _free_agents(df: pd.DataFrame, hide_injured: bool, min_score: float, pos: str = "", limit: int = 100):
    if hide_injured:
        df = df[~df["display_name"].str.contains(r"\(", na=False)]
    all_fa = df[(df["has_valid_position"]) & ((df["fantasy_team"].isna()) | (df["fantasy_team"].isin(["Free Agent","FA"])))].copy()
    all_fa = _attach_pos_ranks(all_fa, df)

    fa_df = all_fa.copy()
    if pos:
        fa_df = fa_df[fa_df["norm_positions"].apply(lambda xs: isinstance(xs, list) and pos in xs)]
    cols = [c for c in _FA_COLS + ["pos_ranks_str", "best_pos_rank"] if c in fa_df.columns]
    fa_df = fa_df.sort_values("proj_CompositeScore", ascending=False)
    return fa_df[cols].head(limit).to_dict(orient="records")


_ROSTER_COLS = [
    "Name", "display_name", "Team", "position", "injury_status", "fantasy_points",
    "proj_CompositeScore", "curr_CompositeScore", "ScoreDelta",
    "proj_HR", "proj_R", "proj_RBI", "proj_SB", "proj_AVG",
    "proj_ERA", "proj_WHIP", "proj_SV", "proj_IP", "proj_K-BB%",
]

def _team_roster(df: pd.DataFrame, team: str, hide_injured: bool, pos: str = ""):
    if hide_injured:
        df = df[~df["display_name"].str.contains(r"\(", na=False)]
    team_df = df[(df["fantasy_team"] == team) & (df["has_valid_position"])].copy()
    if pos:
        team_df = team_df[team_df["norm_positions"].apply(lambda xs: isinstance(xs, list) and pos in xs)]
    team_df = _attach_pos_ranks(team_df, df)
    cols = [c for c in _ROSTER_COLS + ["pos_ranks_str", "best_pos_rank"] if c in team_df.columns]
    return team_df[cols].sort_values("proj_CompositeScore", ascending=False).to_dict(orient="records")


def _drop_candidates(df: pd.DataFrame, team: str, hide_injured: bool, pos: str = "", limit: int = 20):
    if hide_injured:
        df = df[~df["display_name"].str.contains(r"\(", na=False)]
    team_df = df[(df["fantasy_team"] == team) & (df["has_valid_position"])].copy()
    if pos:
        team_df = team_df[team_df["norm_positions"].apply(lambda xs: isinstance(xs, list) and pos in xs)]
    # "Weakest" should be based on projected value, not short-term delta.
    # ScoreDelta is still useful as a tiebreaker.
    if "proj_CompositeScore" in team_df.columns:
        if "ScoreDelta" in team_df.columns:
            team_df = team_df.sort_values(
                by=["proj_CompositeScore", "ScoreDelta"],
                ascending=[True, True],
                na_position="last",
            )
        else:
            team_df = team_df.sort_values("proj_CompositeScore", ascending=True, na_position="last")
    elif "ScoreDelta" in team_df.columns:
        team_df = team_df.sort_values("ScoreDelta", ascending=True, na_position="last")
    cols = [c for c in ["display_name","Team","position","proj_CompositeScore","curr_CompositeScore","ScoreDelta"] if c in team_df.columns]
    return team_df[cols].head(limit).to_dict(orient="records")


def _dashboard_data(df: pd.DataFrame, team: str, hide_injured: bool) -> dict:
    working = df.copy()
    if hide_injured:
        working = working[~working["display_name"].str.contains(r"\(", na=False)]

    playable = working[working["has_valid_position"]].copy()
    rostered = playable[~playable["fantasy_team"].fillna("").isin(["", "Free Agent", "FA"])]
    team_df = rostered[rostered["fantasy_team"] == team]

    positions_out = []
    for pos in ["C", "1B", "2B", "3B", "SS", "OF", "DH", "P"]:
        pos_team = team_df[team_df["norm_positions"].apply(lambda xs: isinstance(xs, list) and pos in xs)]
        pos_league = rostered[rostered["norm_positions"].apply(lambda xs: isinstance(xs, list) and pos in xs)]

        team_avg = float(pos_team["proj_CompositeScore"].mean()) if not pos_team.empty else 0.0
        league_avg = float(pos_league["proj_CompositeScore"].mean()) if not pos_league.empty else 0.0
        strength_pct = int((team_avg / league_avg) * 100) if league_avg > 0 else 0

        if strength_pct >= 110:
            badge = "great"
        elif strength_pct >= 95:
            badge = "good"
        elif strength_pct >= 80:
            badge = "avg"
        else:
            badge = "concern"

        best = pos_team.nlargest(1, "proj_CompositeScore").iloc[0]["display_name"] if not pos_team.empty else ""
        worst = pos_team.nsmallest(1, "proj_CompositeScore").iloc[0]["display_name"] if not pos_team.empty else ""

        positions_out.append({
            "pos": pos,
            "team_avg": round(team_avg, 3),
            "league_avg": round(league_avg, 3),
            "strength_pct": strength_pct,
            "badge": badge,
            "count": len(pos_team),
            "best": best,
            "worst": worst,
        })

    # Team rank
    team_means = rostered.groupby("fantasy_team")["proj_CompositeScore"].mean().sort_values(ascending=False)
    team_rank = list(team_means.index).index(team) + 1 if team in team_means.index else 0

    # Injured players on this team
    injured_mask = df["display_name"].str.contains(r"\(", na=False)
    injured_rows = df[(df["fantasy_team"] == team) & injured_mask][["display_name", "position"]].to_dict(orient="records")

    # All top upgrades (up to 5)
    top_upgrades = _compute_upgrades(df, team, hide_injured, -1.0)

    return {
        "positions": positions_out,
        "team_rank": team_rank,
        "total_teams": len(team_means),
        "upgrades": top_upgrades,
        "injured": injured_rows,
    }


def _league_summary(df: pd.DataFrame, hide_injured: bool):
    if hide_injured:
        df = df[~df["display_name"].str.contains(r"\(", na=False)]
    playable = df[df["has_valid_position"]].copy()
    playable = playable[~playable["fantasy_team"].fillna("").str.lower().isin(["", "free agent", "fa"])]
    if playable.empty:
        return []
    group = playable.groupby("fantasy_team", dropna=True)
    proj = group["proj_CompositeScore"].mean().rename("proj_mean") if "proj_CompositeScore" in playable.columns else None
    cur = group["curr_CompositeScore"].mean().rename("curr_mean") if "curr_CompositeScore" in playable.columns else None
    size = group.size().rename("players")
    out = pd.concat([proj, cur, size], axis=1).reset_index().fillna(0)
    return out.sort_values("proj_mean", ascending=False).to_dict(orient="records")


def _league_team_breakdown(df: pd.DataFrame, team: str, hide_injured: bool):
    if hide_injured:
        df = df[~df["display_name"].str.contains(r"\(", na=False)]
    team_df = df[(df["fantasy_team"] == team) & (df["has_valid_position"])].copy()
    if team_df.empty:
        return {"hitters": [], "pitchers": []}
    # Build qualified universe for normalization
    playable = df[df.get("has_valid_position", True) == True].copy()
    hitters_univ = playable[~playable.get("norm_positions", []).apply(lambda xs: isinstance(xs, list) and any("P" in p for p in xs))]
    pitchers_univ = playable[playable.get("norm_positions", []).apply(lambda xs: isinstance(xs, list) and any("P" in p for p in xs))]
    if "curr_AB" in hitters_univ.columns:
        hitters_univ = hitters_univ[pd.to_numeric(hitters_univ["curr_AB"], errors="coerce").fillna(0) >= 50]
    if "curr_IP" in pitchers_univ.columns:
        pitchers_univ = pitchers_univ[pd.to_numeric(pitchers_univ["curr_IP"], errors="coerce").fillna(0) >= 20]

    def series_for(base_df: pd.DataFrame, fallback_df: pd.DataFrame, column: str) -> pd.Series:
        if column in base_df.columns:
            s = pd.to_numeric(base_df[column], errors="coerce").dropna()
            if not s.empty:
                return s
        if column in fallback_df.columns:
            s = pd.to_numeric(fallback_df[column], errors="coerce").dropna()
            if not s.empty:
                return s
        return pd.Series([0.0, 1.0])

    def minmax_pct(series: pd.Series, value, invert: bool = False) -> float:
        try:
            x = float(value)
        except (TypeError, ValueError):
            return 0.0
        s = pd.to_numeric(series, errors="coerce").dropna()
        if s.empty:
            return 0.0
        vmin = s.min(); vmax = s.max()
        if vmax == vmin:
            return 0.0
        t = (x - vmin) / (vmax - vmin)
        t = max(0.0, min(1.0, t))
        return 1.0 - t if invert else t
    # split hitters/pitchers by positions list
    team_df["is_pitcher"] = team_df["norm_positions"].apply(lambda xs: isinstance(xs, list) and any("P" in p for p in xs))
    hitters = team_df[~team_df["is_pitcher"]]
    pitchers = team_df[team_df["is_pitcher"]]

    def avg_block(frame: pd.DataFrame, columns: list[str]):
        cols = [c for c in columns if c in frame.columns]
        if not cols or frame.empty:
            return []
        mean_row = frame[cols].apply(pd.to_numeric, errors="coerce").mean().round(3).to_dict()
        return [(k, mean_row[k]) for k in cols]

    hitter_stats = [
        ("AB", "int"), ("wOBA", ""), ("wRC+", "int"), ("ISO", ""), ("wBsR", "")
    ]
    pitcher_stats = [
        ("IP", ""), ("FIP", ""), ("WHIP", ""), ("K-BB%", "%"), ("SV", "int")
    ]
    hitters_avg = avg_block(hitters, [f"curr_{k}" for k,_ in hitter_stats])
    pitchers_avg = avg_block(pitchers, [f"curr_{k}" for k,_ in pitcher_stats])
    # Build pct for each stat using universe distributions
    hitter_items = []
    for k,v in hitters_avg:
        label = k.replace("curr_", "")
        s = series_for(hitters_univ, playable, k)
        pct = int(minmax_pct(s, v, invert=False) * 100)
        hitter_items.append({"label": label, "value": v, "pct": pct})
    pitcher_items = []
    for k,v in pitchers_avg:
        label = k.replace("curr_", "")
        invert = label in ("FIP", "WHIP")
        s = series_for(pitchers_univ, playable, k)
        pct = int(minmax_pct(s, v, invert=invert) * 100)
        pitcher_items.append({"label": label, "value": v, "pct": pct})
    return {"hitters": hitter_items, "pitchers": pitcher_items}


def _compare_data(df: pd.DataFrame, name1: str, name2: str):
    def pick(name: str):
        if not name:
            return None
        # strip injury suffix like " (TEN_DAY_DL)" before searching
        clean = re.sub(r"\s*\(.*?\)\s*$", "", name).strip()
        m = df[df["display_name"].str.contains(re.escape(clean), case=False, na=False)]
        if m.empty:
            return None
        sub = _attach_pos_ranks(m.head(1), df)
        return sub.to_dict(orient="records")[0]
    return pick(name1), pick(name2)


_POS_ORDER = ["C","1B","2B","3B","SS","CI","MI","OF","DH","P"]

def _positions_list(df: pd.DataFrame):
    pos_set = set()
    for xs in df.get("norm_positions", []):
        if isinstance(xs, list):
            pos_set.update(xs)
    return [p for p in _POS_ORDER if p in pos_set]


def _players_filtered(
    df: pd.DataFrame,
    search: str,
    pos: str,
    roster_team: str,
    hide_injured: bool,
    min_score: float,
    page: int,
    per_page: int,
    sort: str,
):
    data = df.copy()
    if hide_injured:
        data = data[~data["display_name"].str.contains(r"\(", na=False)]
    data = data[data["has_valid_position"]]
    if search:
        data = data[data["display_name"].str.contains(search, case=False, na=False)]
    if pos:
        data = data[data["norm_positions"].apply(lambda xs: isinstance(xs, list) and pos in xs)]
    if roster_team:
        data = data[data["fantasy_team"].fillna("") == roster_team]
    # no minimum projected score filter

    # sorting
    sort_map = {
        "proj": ("proj_CompositeScore", False),
        "curr": ("curr_CompositeScore", False),
        "name": ("display_name", True),
    }
    col, asc = sort_map.get(sort, ("proj_CompositeScore", False))
    if col in data.columns:
        data = data.sort_values(col, ascending=asc)

    total = len(data)
    start = max((page - 1) * per_page, 0)
    end = start + per_page
    # Attach pos ranks before slicing so index matches all_df
    data = _attach_pos_ranks(data, df)
    cols = [
        "Name", "display_name",
        "Team", "position", "fantasy_team",
        "injury_status", "fantasy_points",
        "proj_CompositeScore", "curr_CompositeScore",
        "proj_HR", "proj_R", "proj_RBI", "proj_SB", "proj_AVG",
        "proj_ERA", "proj_WHIP", "proj_SV", "proj_IP", "proj_K-BB%",
        "pos_ranks_str", "best_pos_rank",
    ]
    present = [c for c in cols if c in data.columns]
    page_df = data[present].iloc[start:end].copy()
    return page_df.to_dict(orient="records"), total


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    csv_path = get_latest_csv()
    if not csv_path:
        return templates.TemplateResponse("no_data.html", {"request": request})
    df = _prepare_dataframe(csv_path)
    teams = sorted([t for t in df["fantasy_team"].dropna().unique() if str(t).lower() not in ["fa", "free agent"]])
    selected_team, hide_inj, min_score = _filters_from_qp(request.query_params, teams)
    dash = _dashboard_data(df, selected_team, hide_inj)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "teams": teams,
            "data_file": os.path.basename(csv_path),
            "selected_team": selected_team,
            "hide_injured": hide_inj,
            "min_score": min_score,
            "view": "dashboard",
            "dash": dash,
        },
    )


@app.get("/add-drop", response_class=HTMLResponse)
def add_drop_view(request: Request):
    csv_path = get_latest_csv()
    if not csv_path:
        return templates.TemplateResponse("no_data.html", {"request": request})
    df = _prepare_dataframe(csv_path)
    teams = sorted([t for t in df["fantasy_team"].dropna().unique() if str(t).lower() not in ["fa", "free agent"]])
    selected_team, hide_inj, min_score = _filters_from_qp(request.query_params, teams)
    pos = request.query_params.get("pos", "")
    fa_sort = request.query_params.get("faSort", "proj")
    fa_roster = request.query_params.get("faRoster", "0")
    fa_upg = request.query_params.get("faUpg", "0")
    positions = _positions_list(df)
    upgrades = _compute_upgrades(df, selected_team, hide_inj, min_score, pos)
    fa = _free_agents(df, hide_inj, min_score, pos)
    roster = _team_roster(df, selected_team, hide_inj, pos)
    upgrade_names = {u["add"]["display_name"] for u in upgrades} if upgrades else set()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "teams": teams,
            "data_file": os.path.basename(csv_path),
            "selected_team": selected_team,
            "hide_injured": hide_inj,
            "min_score": min_score,
            "upgrades": upgrades,
            "view": "add_drop",
            "fa": fa,
            "roster": roster,
            "positions": positions,
            "pos": pos,
            "fa_sort": fa_sort,
            "fa_roster": fa_roster,
            "fa_upg": fa_upg,
            "upgrade_names": upgrade_names,
        },
    )

@app.get("/api/players/search")
def player_search(q: str = ""):
    if not q or len(q) < 2:
        return JSONResponse([])
    csv_path = get_latest_csv()
    if not csv_path:
        return JSONResponse([])
    df = _prepare_dataframe(csv_path)
    matches = df[df["display_name"].str.contains(q, case=False, na=False)]
    names = matches.sort_values("proj_CompositeScore", ascending=False)["Name"].head(10).tolist()
    return JSONResponse(names)


@app.post("/update")
def update_data(model: str = Query(default=None)):
    if model and model in PROJECTION_MODELS:
        try:
            from dotenv import set_key
            set_key(str(ROOT_DIR / ".env"), "PROJECTION_MODEL", model)
        except Exception:
            pass
        os.environ["PROJECTION_MODEL"] = model
    try:
        subprocess.run([sys.executable, str(ROOT_DIR / "src" / "main.py")], check=True)
        return JSONResponse({"status": "ok"})
    except subprocess.CalledProcessError as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


@app.get("/free-agents", response_class=HTMLResponse)
def free_agents(request: Request):
    csv_path = get_latest_csv()
    if not csv_path:
        return templates.TemplateResponse("no_data.html", {"request": request})
    df = _prepare_dataframe(csv_path)
    teams = sorted([t for t in df["fantasy_team"].dropna().unique() if str(t).lower() not in ["fa", "free agent"]])
    selected_team, hide_inj, min_score = _filters_from_qp(request.query_params, teams)
    fa = _free_agents(df, hide_inj, min_score)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "teams": teams,
            "data_file": os.path.basename(csv_path),
            "selected_team": selected_team,
            "hide_injured": hide_inj,
            "min_score": min_score,
            "fa": fa,
            "view": "free_agents",
        },
    )


@app.get("/drop-candidates", response_class=HTMLResponse)
def drop_candidates(request: Request):
    csv_path = get_latest_csv()
    if not csv_path:
        return templates.TemplateResponse("no_data.html", {"request": request})
    df = _prepare_dataframe(csv_path)
    teams = sorted([t for t in df["fantasy_team"].dropna().unique() if str(t).lower() not in ["fa", "free agent"]])
    selected_team, hide_inj, min_score = _filters_from_qp(request.query_params, teams)
    pos = request.query_params.get("pos", "")
    positions = _positions_list(df)
    drops = _drop_candidates(df, selected_team, hide_inj, pos)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "teams": teams, "data_file": os.path.basename(csv_path),
         "selected_team": selected_team, "hide_injured": hide_inj, "min_score": min_score,
         "drops": drops, "view": "drop_candidates", "positions": positions, "pos": pos}
    )


    


@app.get("/league", response_class=HTMLResponse)
def league(request: Request):
    csv_path = get_latest_csv()
    if not csv_path:
        return templates.TemplateResponse("no_data.html", {"request": request})
    df = _prepare_dataframe(csv_path)
    teams = sorted([t for t in df["fantasy_team"].dropna().unique() if str(t).lower() not in ["fa", "free agent"]])
    selected_team, hide_inj, min_score = _filters_from_qp(request.query_params, teams)
    league_rows = _league_summary(df, hide_inj)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "teams": teams, "data_file": os.path.basename(csv_path),
         "selected_team": selected_team, "hide_injured": hide_inj, "min_score": min_score,
         "league": league_rows, "view": "league"}
    )


@app.get("/league/team", response_class=HTMLResponse)
def league_team(request: Request):
    csv_path = get_latest_csv()
    if not csv_path:
        return templates.TemplateResponse("no_data.html", {"request": request})
    df = _prepare_dataframe(csv_path)
    teams = sorted([t for t in df["fantasy_team"].dropna().unique() if str(t).lower() not in ["fa", "free agent"]])
    selected_team, hide_inj, min_score = _filters_from_qp(request.query_params, teams)
    breakdown = _league_team_breakdown(df, selected_team, hide_inj)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "teams": teams, "data_file": os.path.basename(csv_path),
         "selected_team": selected_team, "hide_injured": hide_inj, "min_score": min_score,
         "breakdown": breakdown, "view": "league_team"}
    )


@app.get("/compare", response_class=HTMLResponse)
def compare(request: Request):
    csv_path = get_latest_csv()
    if not csv_path:
        return templates.TemplateResponse("no_data.html", {"request": request})
    df = _prepare_dataframe(csv_path)
    teams = sorted([t for t in df["fantasy_team"].dropna().unique() if str(t).lower() not in ["fa", "free agent"]])
    selected_team, hide_inj, min_score = _filters_from_qp(request.query_params, teams)
    def _clean_name(s: str) -> str:
        return re.sub(r"\s*\(.*?\)\s*$", "", s).strip()
    p1 = _clean_name(request.query_params.get("p1", ""))
    p2 = _clean_name(request.query_params.get("p2", ""))
    a, b = _compare_data(df, p1, p2)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "teams": teams, "data_file": os.path.basename(csv_path),
         "selected_team": selected_team, "hide_injured": hide_inj, "min_score": min_score,
         "p1": p1, "p2": p2, "cmp1": a, "cmp2": b, "view": "compare"}
    )


@app.get("/players", response_class=HTMLResponse)
def players(request: Request):
    csv_path = get_latest_csv()
    if not csv_path:
        return templates.TemplateResponse("no_data.html", {"request": request})
    df = _prepare_dataframe(csv_path)
    teams = sorted([t for t in df["fantasy_team"].dropna().unique() if str(t).lower() not in ["fa", "free agent"]])
    selected_team, hide_inj, min_score = _filters_from_qp(request.query_params, teams)
    search = request.query_params.get("q", "")
    pos = request.query_params.get("pos", "")
    roster_team = request.query_params.get("roster", "")
    try:
        page = max(int(request.query_params.get("page", "1")), 1)
    except ValueError:
        page = 1
    try:
        per_page = min(max(int(request.query_params.get("per", "25")), 5), 200)
    except ValueError:
        per_page = 25
    sort = request.query_params.get("sort", "proj")

    rows, total = _players_filtered(df, search, pos, roster_team, hide_inj, min_score, page, per_page, sort)
    positions = _positions_list(df)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "teams": teams,
            "data_file": os.path.basename(csv_path),
            "selected_team": selected_team,
            "hide_injured": hide_inj,
            "min_score": min_score,
            "players": rows,
            "total": total,
            "page": page,
            "per": per_page,
            "q": search,
            "pos": pos,
            "roster": roster_team,
            "positions": positions,
            "sort": sort,
            "view": "players",
        },
    )


## ── Draft Strategy ──────────────────────────────────────────────────

def _get_draft_excel() -> str | None:
    out_dir = ROOT_DIR / "output"
    if not out_dir.exists():
        return None
    files = sorted(out_dir.glob("draft_strategy_*.xlsx"))
    return str(files[-1]) if files else None


def _load_draft_df() -> pd.DataFrame | None:
    path = _get_draft_excel()
    if not path:
        return None
    try:
        df = pd.read_excel(path, sheet_name="All players")
        # Excel serializes sets as strings like "{'SS', 'MI'}" — parse them back
        if "Eligible_Positions" in df.columns:
            import ast
            def _parse_set(val):
                if isinstance(val, set):
                    return val
                try:
                    parsed = ast.literal_eval(str(val))
                    return set(parsed) if isinstance(parsed, (set, list)) else {str(parsed)}
                except Exception:
                    return set()
            df["Eligible_Positions"] = df["Eligible_Positions"].apply(_parse_set)
        return df
    except Exception:
        return None


def _save_draft_df(df: pd.DataFrame, path: str | None = None) -> str:
    import datetime as _dt
    if path and os.path.exists(path):
        target = path
    else:
        os.makedirs(str(ROOT_DIR / "output"), exist_ok=True)
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        target = str(ROOT_DIR / "output" / f"draft_strategy_{ts}.xlsx")
    with pd.ExcelWriter(target, engine="openpyxl") as w:
        df.to_excel(w, sheet_name="All players", index=False)
    return target


def _draft_board(draft_df: pd.DataFrame) -> list[dict]:
    drafted_count = len(draft_df[draft_df["Drafted"].fillna("") != ""])
    filtered = draft_df.copy()

    # Sort by adjusted rank
    if "Adjusted_Rank" in filtered.columns:
        filtered = filtered.sort_values("Adjusted_Rank")

    stat_cols = ["AB", "wOBA", "ISO", "wBsR", "wRC+",
                 "IP", "FIP", "WHIP", "K-BB%", "SV"]
    cols_wanted = ["Adjusted_Rank", "Name", "position", "Team", "Drafted",
                   "Tier", "Suggested_Draft_Round", "Recommended_Pick", "CompositeScore",
                   "Composite_ZScore", "Adjusted_CompositeScore", "VADP", "ADP", "League_FPTS", "PAR",
                   "Draft_Pick", "Eligible_Positions"] + stat_cols
    cols = [c for c in cols_wanted if c in filtered.columns]

    # Precompute percentiles for stat bars (use full draft_df, not filtered)
    invert_stats = {"FIP", "WHIP"}  # lower is better
    stat_ranges: dict[str, tuple[float, float]] = {}
    for sc in stat_cols:
        if sc in draft_df.columns:
            s = pd.to_numeric(draft_df[sc], errors="coerce").dropna()
            if not s.empty and s.max() != s.min():
                stat_ranges[sc] = (float(s.min()), float(s.max()))

    rows = []
    for _, r in filtered[cols].iterrows():
        d = r.to_dict()
        # clean up NaN
        for k, v in d.items():
            if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
                d[k] = None
        elig = d.get("Eligible_Positions")
        if isinstance(elig, set):
            d["eligible_positions"] = sorted(str(p) for p in elig)
        elif isinstance(elig, (list, tuple)):
            d["eligible_positions"] = sorted(str(p) for p in elig)
        else:
            d["eligible_positions"] = []
        d["is_drafted"] = bool(d.get("Drafted") and str(d["Drafted"]).strip())
        elig = d.get("Eligible_Positions")
        if isinstance(elig, set):
            d["is_pitcher"] = bool({"P", "SP", "RP"} & elig)
        else:
            pos_str = str(d.get("position", ""))
            d["is_pitcher"] = "P" in pos_str or "Pitcher" in pos_str
        # Value pick: how far past their ADP they've fallen
        adp = d.get("ADP")
        d["adp_diff"] = None
        if adp is not None and not d["is_drafted"]:
            d["adp_diff"] = int(drafted_count - adp) if drafted_count > adp else None
        # Compute pct for each stat
        pcts = {}
        for sc in stat_cols:
            val = d.get(sc)
            if val is not None and sc in stat_ranges:
                vmin, vmax = stat_ranges[sc]
                pct = (float(val) - vmin) / (vmax - vmin)
                pct = max(0.0, min(1.0, pct))
                if sc in invert_stats:
                    pct = 1.0 - pct
                pcts[sc] = int(pct * 100)
        d["pcts"] = pcts
        rows.append(d)
    return rows


def _draft_summary(draft_df: pd.DataFrame) -> dict:
    total = len(draft_df)
    drafted = len(draft_df[draft_df["Drafted"].fillna("") != ""])
    available = total - drafted
    tiers = {}
    if "Tier" in draft_df.columns:
        for t in sorted(draft_df["Tier"].dropna().unique()):
            t_int = int(t)
            tier_df = draft_df[draft_df["Tier"] == t]
            tier_avail = len(tier_df[tier_df["Drafted"].fillna("") == ""])
            tiers[t_int] = {"total": len(tier_df), "available": tier_avail}

    # Position supply: available player count vs required league demand.
    total_teams = 10
    pitcher_tags = {"P", "SP", "RP"}

    def _slot_accepts_player(slot: str, eligible_positions: set[str]) -> bool:
        if slot == "MI":
            return bool(eligible_positions & {"MI", "2B", "SS"})
        if slot == "CI":
            return bool(eligible_positions & {"CI", "1B", "3B"})
        if slot == "UTIL":
            return not bool(eligible_positions & pitcher_tags)
        if slot == "P":
            return bool(eligible_positions & pitcher_tags)
        return slot in eligible_positions

    working = draft_df.copy()
    if "Eligible_Positions" in working.columns:
        working["Eligible_Positions"] = working["Eligible_Positions"].apply(_parse_eligible)
    else:
        working["Eligible_Positions"] = [set() for _ in range(len(working))]
    available_df = working[working["Drafted"].fillna("").str.strip() == ""].copy()

    preferred_order = ["C", "1B", "2B", "3B", "SS", "OF", "MI", "CI", "UTIL", "SP", "RP", "P"]
    ordered_slots = [s for s in preferred_order if s in ROSTER_SLOTS]
    ordered_slots += [s for s in sorted(ROSTER_SLOTS.keys()) if s not in ordered_slots]

    position_supply: list[dict] = []
    for slot in ordered_slots:
        slots_per_team = int(ROSTER_SLOTS.get(slot, 0) or 0)
        if slots_per_team <= 0:
            continue
        demand = slots_per_team * total_teams
        avail_count = int(
            available_df["Eligible_Positions"].apply(lambda ep: _slot_accepts_player(slot, ep)).sum()
        )
        ratio = (avail_count / demand) if demand > 0 else 0.0
        if ratio < 1.0:
            status = "low"
        elif ratio < 1.5:
            status = "mid"
        else:
            status = "high"
        position_supply.append({
            "slot": slot,
            "available": avail_count,
            "demand": demand,
            "ratio": round(ratio, 2),
            "pct": max(0, min(100, int(round(ratio * 100)))) if demand > 0 else 0,
            "status": status,
        })

    return {
        "total": total,
        "drafted": drafted,
        "available": available,
        "tiers": tiers,
        "position_supply": position_supply,
        "total_teams": total_teams,
    }


def _pick_to_round_and_slot(overall_pick: int, total_teams: int = 10) -> tuple[int, int]:
    """Convert overall pick number to snake-draft (round, team slot)."""
    if overall_pick <= 0 or total_teams <= 0:
        return 0, 0
    draft_round = ((overall_pick - 1) // total_teams) + 1
    in_round = ((overall_pick - 1) % total_teams) + 1
    if draft_round % 2 == 1:
        team_slot = in_round
    else:
        team_slot = total_teams - in_round + 1
    return draft_round, team_slot


def _draft_log(draft_df: pd.DataFrame) -> list[dict]:
    if "Draft_Pick" not in draft_df.columns:
        return []
    drafted = draft_df[draft_df["Draft_Pick"].fillna(0) > 0].copy()
    if drafted.empty:
        return []
    drafted = drafted.sort_values("Draft_Pick")
    log = []
    for _, r in drafted.iterrows():
        pick_num = int(r["Draft_Pick"])
        round_num, team_slot = _pick_to_round_and_slot(pick_num, total_teams=10)
        if pd.notna(r.get("Draft_Round")):
            round_num = int(r.get("Draft_Round"))
        if pd.notna(r.get("Draft_Team_Slot")):
            team_slot = int(r.get("Draft_Team_Slot"))
        log.append({
            "pick": pick_num,
            "round": round_num,
            "team_slot": team_slot,
            "name": r.get("Name", ""),
            "position": r.get("position", ""),
            "team": r.get("Team", ""),
            "drafted_by": r.get("Drafted", ""),
            "rank": int(r["Adjusted_Rank"]) if pd.notna(r.get("Adjusted_Rank")) else None,
            "score": float(r["Adjusted_CompositeScore"]) if pd.notna(r.get("Adjusted_CompositeScore")) else None,
        })
    return log


def _draft_positions(draft_df: pd.DataFrame) -> list[str]:
    pos_set: set[str] = set()
    if "Eligible_Positions" in draft_df.columns:
        for p in draft_df["Eligible_Positions"]:
            pos_set.update(_parse_eligible(p))

    # Always include configured roster slots so chips don't disappear if
    # no current rows parse cleanly for a specific slot.
    pos_set.update(ROSTER_SLOTS.keys())

    preferred_order = ["C", "1B", "2B", "3B", "SS", "OF", "MI", "CI", "UTIL", "SP", "RP", "P"]
    ordered = [p for p in preferred_order if p in pos_set]
    remainder = sorted(p for p in pos_set if p not in ordered)
    return ordered + remainder


def _draft_tiers(draft_df: pd.DataFrame) -> list[int]:
    if "Tier" in draft_df.columns:
        return sorted(int(t) for t in draft_df["Tier"].dropna().unique())
    return []


def _merge_draft_state(previous_df: pd.DataFrame | None, refreshed_df: pd.DataFrame) -> pd.DataFrame:
    """
    Carry forward draft progress (picks, skipped picks, drafted flags) when a new
    draft workbook is generated.
    """
    if previous_df is None or previous_df.empty:
        return refreshed_df

    out = refreshed_df.copy()
    for col, default in (("Drafted", ""), ("Draft_Pick", 0), ("Draft_Round", 0), ("Draft_Team_Slot", 0)):
        if col not in out.columns:
            out[col] = default

    prev = previous_df.copy()
    for col, default in (("Drafted", ""), ("Draft_Pick", 0), ("Draft_Round", 0), ("Draft_Team_Slot", 0)):
        if col not in prev.columns:
            prev[col] = default

    out["Drafted"] = ""
    out["Draft_Pick"] = 0
    out["Draft_Round"] = 0
    out["Draft_Team_Slot"] = 0

    prev["Draft_Pick"] = pd.to_numeric(prev["Draft_Pick"], errors="coerce").fillna(0).astype(int)
    prev_log = prev[prev["Draft_Pick"] > 0].sort_values("Draft_Pick")
    if prev_log.empty:
        return out

    used_idx: set[int] = set()
    extra_rows: list[dict] = []
    out_name = out["Name"].astype(str) if "Name" in out.columns else pd.Series([], dtype=str)
    out_pos = out["position"].astype(str) if "position" in out.columns else pd.Series([], dtype=str)

    for _, r in prev_log.iterrows():
        name = str(r.get("Name", ""))
        if not name:
            continue

        is_skip = name.startswith("[Skipped Pick")
        if is_skip:
            row_obj = {c: "" for c in out.columns}
            row_obj["Name"] = name
            row_obj["Drafted"] = str(r.get("Drafted", "Skipped") or "Skipped")
            row_obj["Draft_Pick"] = int(r.get("Draft_Pick", 0) or 0)
            row_obj["Draft_Round"] = int(r.get("Draft_Round", 0) or 0)
            row_obj["Draft_Team_Slot"] = int(r.get("Draft_Team_Slot", 0) or 0)
            extra_rows.append(row_obj)
            continue

        candidates = out.index[out_name == name].tolist()
        chosen = None
        pos = str(r.get("position", ""))
        if pos and candidates:
            exact = [i for i in candidates if i not in used_idx and out_pos.iloc[i] == pos]
            if exact:
                chosen = exact[0]
        if chosen is None and candidates:
            rem = [i for i in candidates if i not in used_idx]
            if rem:
                chosen = rem[0]

        if chosen is not None:
            used_idx.add(chosen)
            out.loc[chosen, "Drafted"] = str(r.get("Drafted", "") or "Drafted")
            out.loc[chosen, "Draft_Pick"] = int(r.get("Draft_Pick", 0) or 0)
            out.loc[chosen, "Draft_Round"] = int(r.get("Draft_Round", 0) or 0)
            out.loc[chosen, "Draft_Team_Slot"] = int(r.get("Draft_Team_Slot", 0) or 0)
            continue

        # If a drafted player no longer exists in refreshed top-N board, keep a
        # placeholder entry so pick history stays consistent.
        row_obj = {c: "" for c in out.columns}
        for c in out.columns:
            if c in r.index and pd.notna(r[c]):
                row_obj[c] = r[c]
        row_obj["Name"] = name
        row_obj["Drafted"] = str(r.get("Drafted", "") or "Drafted")
        row_obj["Draft_Pick"] = int(r.get("Draft_Pick", 0) or 0)
        row_obj["Draft_Round"] = int(r.get("Draft_Round", 0) or 0)
        row_obj["Draft_Team_Slot"] = int(r.get("Draft_Team_Slot", 0) or 0)
        extra_rows.append(row_obj)

    if extra_rows:
        out = pd.concat([out, pd.DataFrame(extra_rows, columns=out.columns)], ignore_index=True)

    return out


@app.get("/draft", response_class=HTMLResponse)
def draft_view(request: Request):
    csv_path = get_latest_csv()
    if not csv_path:
        return templates.TemplateResponse("no_data.html", {"request": request})
    df = _prepare_dataframe(csv_path)
    teams = sorted([t for t in df["fantasy_team"].dropna().unique() if str(t).lower() not in ["fa", "free agent"]])
    selected_team, hide_inj, min_score = _filters_from_qp(request.query_params, teams)

    draft_df = _load_draft_df()
    has_draft = draft_df is not None

    board = []
    summary = {}
    positions = []
    tier_list = []
    draft_file = ""
    log = []
    if has_draft:
        board = _draft_board(draft_df)
        summary = _draft_summary(draft_df)
        positions = _draft_positions(draft_df)
        tier_list = _draft_tiers(draft_df)
        draft_file = os.path.basename(_get_draft_excel() or "")
        log = _draft_log(draft_df)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "teams": teams,
            "data_file": os.path.basename(csv_path),
            "selected_team": selected_team,
            "hide_injured": hide_inj,
            "min_score": min_score,
            "view": "draft",
            "has_draft": has_draft,
            "board": board,
            "draft_summary": summary,
            "draft_positions": positions,
            "draft_tiers": tier_list,
            "draft_file": draft_file,
            "draft_log": log,
        },
    )


@app.post("/draft/generate", response_class=HTMLResponse)
def draft_generate(request: Request):
    csv_path = get_latest_csv()
    if not csv_path:
        return RedirectResponse("/draft", status_code=303)
    df = _prepare_dataframe(csv_path)
    # Prepare data for the generator.
    # Do not pre-filter Unknown positions here: the generator has name-based/FG fallbacks
    # (critical for two-way players like Shohei) and will handle eligibility itself.
    prep = df.copy()
    col_map = {"display_name": "Name", "proj_CompositeScore": "CompositeScore"}
    for old, new in col_map.items():
        if old in prep.columns:
            prep[new] = prep[old]
    # Prefer ESPN ADP when present; otherwise fall back to existing ADP/projection ADP.
    if "ADP" not in prep.columns:
        adp_candidates = ["espn_ADP", "proj_ADP", "ADP"]
        for src in adp_candidates:
            if src in prep.columns:
                adp_vals = pd.to_numeric(prep[src], errors="coerce")
                # Treat non-positive values as missing.
                adp_vals = adp_vals.where(adp_vals > 0)
                if adp_vals.notna().any():
                    prep["ADP"] = adp_vals
                    break

    stat_map = {
        "AB": "proj_AB", "ADP": "ADP", "wOBA": "proj_wOBA", "ISO": "proj_ISO",
        "wBsR": "proj_wBsR", "wRC+": "proj_wRC+", "IP": "proj_IP", "FIP": "proj_FIP",
        "WHIP": "proj_WHIP", "K-BB%": "proj_K-BB%", "SV": "proj_SV",
    }
    for req_col, src_col in stat_map.items():
        if req_col not in prep.columns:
            if src_col in prep.columns:
                prep[req_col] = prep[src_col]
            elif req_col == "AB":
                prep[req_col] = prep.apply(
                    lambda r: 450 if "P" not in str(r.get("position", "")) else 0, axis=1)
            elif req_col == "ADP":
                prep[req_col] = range(1, len(prep) + 1)
            else:
                prep[req_col] = 0.0

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
        prep.to_csv(tmp.name, index=False)
        tmp_path = tmp.name
    previous_df = _load_draft_df()
    try:
        analyze_and_adjust_rankings(tmp_path)
    finally:
        os.unlink(tmp_path)

    refreshed_df = _load_draft_df()
    if refreshed_df is not None:
        merged = _merge_draft_state(previous_df, refreshed_df)
        _save_draft_df(merged, _get_draft_excel())

    return RedirectResponse("/draft", status_code=303)


@app.post("/draft/pick")
def draft_pick(name: str = Form(...), drafted_by: str = Form(""), total_teams: int = Form(10)):
    draft_df = _load_draft_df()
    if draft_df is None:
        return JSONResponse({"error": "No draft data"}, status_code=400)
    if "Draft_Pick" not in draft_df.columns:
        draft_df["Draft_Pick"] = 0
    if "Draft_Round" not in draft_df.columns:
        draft_df["Draft_Round"] = 0
    if "Draft_Team_Slot" not in draft_df.columns:
        draft_df["Draft_Team_Slot"] = 0
    mask = draft_df["Name"] == name
    if mask.any():
        draft_df.loc[mask, "Drafted"] = drafted_by if drafted_by else "Drafted"
        current_max = int(draft_df["Draft_Pick"].fillna(0).max())
        pick_num = current_max + 1
        round_num, team_slot = _pick_to_round_and_slot(pick_num, total_teams=max(1, int(total_teams)))
        draft_df.loc[mask, "Draft_Pick"] = pick_num
        draft_df.loc[mask, "Draft_Round"] = round_num
        draft_df.loc[mask, "Draft_Team_Slot"] = team_slot
    _save_draft_df(draft_df, _get_draft_excel())
    pick_num = int(draft_df.loc[mask, "Draft_Pick"].iloc[0]) if mask.any() else 0
    round_num = int(draft_df.loc[mask, "Draft_Round"].iloc[0]) if mask.any() and "Draft_Round" in draft_df.columns else 0
    team_slot = int(draft_df.loc[mask, "Draft_Team_Slot"].iloc[0]) if mask.any() and "Draft_Team_Slot" in draft_df.columns else 0
    return JSONResponse({"ok": True, "pick": pick_num, "round": round_num, "team_slot": team_slot})


@app.post("/draft/skip")
def draft_skip():
    """Skip a pick — increments the draft counter without marking any player."""
    draft_df = _load_draft_df()
    if draft_df is None:
        return JSONResponse({"error": "No draft data"}, status_code=400)
    if "Draft_Pick" not in draft_df.columns:
        draft_df["Draft_Pick"] = 0
    if "Draft_Round" not in draft_df.columns:
        draft_df["Draft_Round"] = 0
    if "Draft_Team_Slot" not in draft_df.columns:
        draft_df["Draft_Team_Slot"] = 0
    current_max = int(draft_df["Draft_Pick"].fillna(0).max())
    pick_num = current_max + 1
    round_num, team_slot = _pick_to_round_and_slot(pick_num, total_teams=10)
    # Add a dummy row to track the skip
    skip_row = pd.Series({col: "" for col in draft_df.columns})
    skip_row["Name"] = f"[Skipped Pick {pick_num}]"
    skip_row["Drafted"] = "Skipped"
    skip_row["Draft_Pick"] = pick_num
    skip_row["Draft_Round"] = round_num
    skip_row["Draft_Team_Slot"] = team_slot
    draft_df = pd.concat([draft_df, pd.DataFrame([skip_row])], ignore_index=True)
    _save_draft_df(draft_df, _get_draft_excel())
    return JSONResponse({"ok": True, "pick": pick_num, "round": round_num, "team_slot": team_slot})


@app.post("/draft/unpick")
def draft_unpick(name: str = Form(...)):
    draft_df = _load_draft_df()
    if draft_df is None:
        return JSONResponse({"error": "No draft data"}, status_code=400)
    mask = draft_df["Name"] == name
    if mask.any():
        draft_df.loc[mask, "Drafted"] = ""
        if "Draft_Pick" in draft_df.columns:
            draft_df.loc[mask, "Draft_Pick"] = 0
        if "Draft_Round" in draft_df.columns:
            draft_df.loc[mask, "Draft_Round"] = 0
        if "Draft_Team_Slot" in draft_df.columns:
            draft_df.loc[mask, "Draft_Team_Slot"] = 0
    _save_draft_df(draft_df, _get_draft_excel())
    return JSONResponse({"ok": True})


# ── Draft Advisor ──────────────────────────────────────────────

def _load_roster_slots() -> dict[str, int]:
    """Load roster slot settings from ESPN config, with sensible defaults."""
    import json
    settings_path = ROOT_DIR / "output" / "roster_settings.json"
    defaults = {"C": 1, "1B": 1, "2B": 1, "3B": 1, "SS": 1,
                "OF": 3, "MI": 1, "CI": 1, "UTIL": 1, "P": 6, "RP": 3}
    # ESPN uses different slot names than our internal format
    name_map = {"2B/SS": "MI", "1B/3B": "CI"}
    try:
        if settings_path.exists():
            with open(settings_path) as f:
                raw = json.load(f)
            skip = {"BE", "IL", "IL+", "IR", "IR+"}
            result = {}
            for k, v in raw.items():
                if k in skip or v <= 0:
                    continue
                mapped = name_map.get(k, k)
                result[mapped] = v
            if result:
                return result
    except Exception:
        pass
    return defaults


ROSTER_SLOTS = _load_roster_slots()

def _parse_eligible(val):
    """Parse Eligible_Positions from various formats."""
    if isinstance(val, set):
        return val
    try:
        import ast
        parsed = ast.literal_eval(str(val))
        if isinstance(parsed, (set, list, tuple)):
            return {str(p) for p in parsed if str(p).strip()}
        if isinstance(parsed, str) and parsed.strip():
            return {parsed.strip()}
        return set()
    except Exception:
        return set()


def _draft_advisor(draft_df: pd.DataFrame, position_filter: str = "") -> dict:
    """
    Draft strategy advisor focused on value timing — when to grab vs wait.

    Instead of ranking "best player available," this answers:
    - Grab Now: players falling past ADP or at positions drying up — you'll lose them
    - Value Targets: players whose ADP is later but score like earlier picks — mid-round winners
    - Wait: high-score players whose ADP says they'll still be there in later rounds
    """
    df = draft_df.copy()
    df["Eligible_Positions"] = df["Eligible_Positions"].apply(_parse_eligible)
    df["_is_drafted"] = df["Drafted"].fillna("").str.strip() != ""

    available = df[~df["_is_drafted"]].copy()
    drafted_count = int(df["_is_drafted"].sum())
    total_teams = 10
    current_round = (drafted_count // total_teams) + 1

    # ── Positional scarcity ──
    scarcity: dict[str, dict] = {}
    for pos in ROSTER_SLOTS:
        pos_avail = available[available["Eligible_Positions"].apply(lambda ep: pos in ep)]
        total_avail = len(pos_avail)
        league_demand = ROSTER_SLOTS[pos] * total_teams
        replacement_idx = min(league_demand, max(0, len(pos_avail) - 1))
        sorted_avail = pos_avail.nlargest(max(1, replacement_idx + 1), "Adjusted_CompositeScore")
        replacement_level = float(sorted_avail["Adjusted_CompositeScore"].iloc[-1]) if not sorted_avail.empty else 0
        scarcity[pos] = {
            "available": total_avail,
            "demand": league_demand,
            "replacement": round(replacement_level, 3),
            "drying_up": total_avail < league_demand * 2,
        }

    # ── Filter by position if set ──
    candidates = available
    if position_filter:
        candidates = available[available["Eligible_Positions"].apply(lambda ep: position_filter in ep)]

    # ── Analyze each available player ──
    grab_now = []    # falling past ADP or scarce position — act now
    value_targets = []  # ADP is later but score punches above weight — wait and profit
    wait = []        # great players whose ADP says they'll be there later

    for _, row in candidates.iterrows():
        elig = row["Eligible_Positions"]
        score = float(row.get("Adjusted_CompositeScore", 0) or 0)
        par = float(row.get("PAR", 0) or 0)
        adp = row.get("ADP")
        rec_pick = row.get("Recommended_Pick")
        name = row.get("Name", "")
        position = row.get("position", "")
        tier = int(row["Tier"]) if pd.notna(row.get("Tier")) else 0
        team = row.get("Team", "")

        if adp is None or pd.isna(adp):
            continue

        adp = int(adp)
        adp_round = (adp // total_teams) + 1
        picks_until_adp = adp - drafted_count  # positive = ADP is later, negative = fallen past

        # Value above replacement at best position
        best_var = 0
        best_pos = ""
        for pos in elig:
            if pos in scarcity and pos not in ("UTIL", "P"):
                var = score - scarcity[pos]["replacement"]
                if var > best_var:
                    best_var = var
                    best_pos = pos

        # Is this player's position drying up?
        pos_scarce = False
        scarce_pos = ""
        for pos in elig:
            if pos in scarcity and pos not in ("UTIL", "P") and scarcity[pos]["drying_up"]:
                pos_scarce = True
                scarce_pos = pos
                break

        # Score relative to their ADP tier — how much are they outperforming?
        # Compare their score to the average score of players with similar ADP
        nearby = available[
            (available["ADP"].notna()) &
            (available["ADP"].between(adp - 10, adp + 10))
        ]
        tier_avg_score = float(nearby["Adjusted_CompositeScore"].mean()) if len(nearby) > 2 else score
        score_vs_tier = score - tier_avg_score  # positive = outperforming their ADP range

        vadp = row.get("VADP")
        vadp_val = int(vadp) if vadp is not None and not pd.isna(vadp) else None

        player_info = {
            "name": name,
            "position": position,
            "tier": tier,
            "score": round(score, 3),
            "par": round(par, 1),
            "adp": adp,
            "rec_pick": int(rec_pick) if rec_pick and not pd.isna(rec_pick) else None,
            "vadp": vadp_val,
            "insight": "",
        }

        # ── Categorize ──
        if picks_until_adp < -5:
            # Fallen well past ADP — someone missed them
            player_info["insight"] = f"Fallen {abs(picks_until_adp)} picks past ADP {adp}"
            player_info["urgency"] = abs(picks_until_adp)
            grab_now.append(player_info)
        elif pos_scarce and best_var > 0.2 and current_round >= 3:
            # Position is drying up and they're well above replacement (skip early rounds)
            avail_at_pos = scarcity[scarce_pos]["available"]
            player_info["insight"] = f"Only {avail_at_pos} {scarce_pos} left, +{best_var:.2f} over replacement"
            player_info["urgency"] = best_var * 10
            grab_now.append(player_info)
        elif picks_until_adp >= 20 and score_vs_tier > 0.1 and adp <= 250:
            # ADP says they'll be around a while AND they outperform peers at that ADP
            # Estimate what round their score matches by finding ADP of similar-scored players
            similar = available[
                (available["Adjusted_CompositeScore"].between(score - 0.15, score + 0.15)) &
                (available["ADP"].notna())
            ]
            score_round = current_round
            if len(similar) > 0:
                median_adp = similar["ADP"].median()
                score_round = max(1, int(median_adp // total_teams) + 1)
            player_info["insight"] = f"ADP R{adp_round} but scores like R{score_round} talent — wait for value"
            player_info["value"] = round(score_vs_tier, 3)
            value_targets.append(player_info)
        elif picks_until_adp >= 10 and adp <= 250:
            # Good player but ADP is comfortably ahead — safe to wait
            player_info["insight"] = f"ADP {adp} (R{adp_round}) — likely available for {picks_until_adp}+ more picks"
            player_info["value"] = round(score, 3)
            wait.append(player_info)

    # Sort each bucket
    grab_now.sort(key=lambda x: x.get("urgency", 0), reverse=True)
    value_targets.sort(key=lambda x: x.get("value", 0), reverse=True)
    wait.sort(key=lambda x: x.get("score", 0), reverse=True)

    return {
        "grab_now": grab_now[:5],
        "value_targets": value_targets[:5],
        "wait": wait[:5],
        "scarcity": {k: v for k, v in scarcity.items() if k not in ("UTIL", "P")},
        "drafted_count": drafted_count,
        "current_round": current_round,
    }


@app.get("/api/draft/advisor")
def draft_advisor_api(position: str = ""):
    draft_df = _load_draft_df()
    if draft_df is None:
        return JSONResponse({"error": "No draft data"}, status_code=400)
    result = _draft_advisor(draft_df, position_filter=position)
    return JSONResponse(result)


def _ideal_draft(draft_df: pd.DataFrame, pick_position: int, total_teams: int = 10, total_rounds: int = 21) -> dict:
    """
    Simulate a snake draft and plan an ideal roster.

    Continues from the current real draft state:
    - already drafted players are removed from the pool
    - your already-made picks are inferred from snake slot + Draft_Pick
    - future picks optimize slot-aware value (PAR by slot when PAR is available)
    """
    df = draft_df.copy()
    if "Eligible_Positions" in df.columns:
        df["Eligible_Positions"] = df["Eligible_Positions"].apply(_parse_eligible)
    else:
        df["Eligible_Positions"] = [set() for _ in range(len(df))]

    if "Draft_Pick" not in df.columns:
        df["Draft_Pick"] = 0
    df["Draft_Pick"] = pd.to_numeric(df["Draft_Pick"], errors="coerce").fillna(0).astype(int)
    df["_is_skip"] = df["Name"].astype(str).str.startswith("[Skipped Pick", na=False)
    df["_is_drafted"] = (df["Drafted"].fillna("").str.strip() != "") | (df["Draft_Pick"] > 0)

    # Blend normalized cross-position composite talent with slot-specific PAR context.
    composite_col = "Adjusted_CompositeScore"
    if composite_col not in df.columns:
        if "CompositeValueScore" in df.columns:
            composite_col = "CompositeValueScore"
        elif "CompositeScore" in df.columns:
            composite_col = "CompositeScore"
        else:
            composite_col = "PAR"
    composite_weight = 0.65
    slot_par_weight = 0.35

    pitcher_tags = {"P", "SP", "RP"}
    slot_needs = {k: int(v) for k, v in ROSTER_SLOTS.items()}

    hitter_priority = [p for p in ["C", "1B", "2B", "3B", "SS", "OF", "MI", "CI"] if p in slot_needs]
    hitter_priority += [p for p in slot_needs if p not in hitter_priority and p not in {"UTIL", "P", "SP", "RP"}]
    pitcher_priority = [p for p in ["SP", "RP", "P"] if p in slot_needs]

    def _is_pitcher_player(eligible_positions: set[str]) -> bool:
        return bool(eligible_positions & pitcher_tags)

    def _remaining_required_hitters() -> int:
        return int(sum(max(0, slot_needs.get(p, 0)) for p in hitter_priority))

    def _can_fill_slot(eligible_positions: set[str]) -> str | None:
        """Assign slots with UTIL delayed so we only take minimum hitters first."""
        if not eligible_positions:
            return None
        if _is_pitcher_player(eligible_positions):
            for slot in pitcher_priority:
                if slot_needs.get(slot, 0) <= 0:
                    continue
                if slot == "P" or slot in eligible_positions:
                    return slot
            return None

        # Required hitter slots first.
        for slot in hitter_priority:
            if slot_needs.get(slot, 0) <= 0:
                continue
            if slot == "MI":
                if eligible_positions & {"MI", "2B", "SS"}:
                    return "MI"
            elif slot == "CI":
                if eligible_positions & {"CI", "1B", "3B"}:
                    return "CI"
            elif slot in eligible_positions:
                return slot

        # Only fill UTIL after all required hitter slots are filled.
        if slot_needs.get("UTIL", 0) > 0 and _remaining_required_hitters() == 0:
            return "UTIL"
        return None

    def _safe_float(val, default: float = 0.0) -> float:
        try:
            if pd.isna(val):
                return default
            return float(val)
        except Exception:
            return default

    def _safe_int(val):
        try:
            if pd.isna(val):
                return None
            return int(float(val))
        except Exception:
            return None

    def _slot_accepts_player(slot: str, eligible_positions: set[str]) -> bool:
        if slot == "MI":
            return bool(eligible_positions & {"MI", "2B", "SS"})
        if slot == "CI":
            return bool(eligible_positions & {"CI", "1B", "3B"})
        if slot == "UTIL":
            return not _is_pitcher_player(eligible_positions)
        if slot == "P":
            return bool(eligible_positions & pitcher_tags)
        return slot in eligible_positions

    slot_replacement_levels: dict[str, float] = {}
    slot_par_stats: dict[str, tuple[float, float]] = {}
    composite_mean = 0.0
    composite_std = 1.0

    def _slot_for_value(slot: str) -> str:
        if slot == "BENCH_P":
            return "P"
        if slot == "BENCH_H":
            return "UTIL"
        return slot

    def _build_slot_replacement_levels(source_df: pd.DataFrame) -> dict[str, float]:
        """
        Build replacement-level FPTS by roster slot so PAR can be evaluated
        for the specific slot being filled (e.g., MI PAR when filling MI).
        """
        if "League_FPTS" not in source_df.columns:
            return {}

        levels: dict[str, float] = {}
        for slot, slots_per_team in ROSTER_SLOTS.items():
            demand = max(1, int(slots_per_team)) * max(1, int(total_teams))
            slot_mask = source_df["Eligible_Positions"].apply(
                lambda ep: _slot_accepts_player(
                    slot,
                    ep if isinstance(ep, set) else _parse_eligible(ep),
                )
            )
            slot_fpts = pd.to_numeric(
                source_df.loc[slot_mask, "League_FPTS"], errors="coerce"
            ).dropna().sort_values(ascending=False).reset_index(drop=True)
            if len(slot_fpts) > demand:
                levels[slot] = float(slot_fpts.iloc[demand])
            elif not slot_fpts.empty:
                levels[slot] = float(slot_fpts.iloc[-1])
            else:
                levels[slot] = 0.0
        return levels

    def _build_slot_par_stats(source_df: pd.DataFrame, replacements: dict[str, float]) -> dict[str, tuple[float, float]]:
        stats: dict[str, tuple[float, float]] = {}
        if "League_FPTS" not in source_df.columns:
            return stats
        for slot in ROSTER_SLOTS:
            repl = replacements.get(slot)
            if repl is None:
                continue
            slot_mask = source_df["Eligible_Positions"].apply(
                lambda ep: _slot_accepts_player(
                    slot,
                    ep if isinstance(ep, set) else _parse_eligible(ep),
                )
            )
            vals = pd.to_numeric(source_df.loc[slot_mask, "League_FPTS"], errors="coerce").dropna()
            if vals.empty:
                continue
            slot_par_vals = vals - repl
            mean = float(slot_par_vals.mean())
            std = float(slot_par_vals.std())
            if std <= 1e-6 or np.isnan(std):
                std = 1.0
            stats[slot] = (mean, std)
        return stats

    def _par_for_slot(row: dict, slot: str) -> float:
        slot_key = _slot_for_value(slot)
        fpts_raw = row.get("League_FPTS")
        if fpts_raw is None or pd.isna(fpts_raw):
            return _safe_float(row.get("PAR", 0.0))
        fpts = _safe_float(fpts_raw, default=np.nan)
        if pd.isna(fpts):
            return _safe_float(row.get("PAR", 0.0))
        repl = slot_replacement_levels.get(slot_key)
        if repl is None:
            return _safe_float(row.get("PAR", 0.0))
        return fpts - repl

    def _composite_z(row: dict) -> float:
        raw = _safe_float(row.get("_composite", row.get(composite_col, 0.0)))
        return (raw - composite_mean) / composite_std

    def _slot_par_z(row: dict, slot: str) -> float:
        slot_key = _slot_for_value(slot)
        mean, std = slot_par_stats.get(slot_key, (0.0, 1.0))
        return (_par_for_slot(row, slot) - mean) / std

    def _score_for_slot(row: dict, slot: str) -> float:
        return composite_weight * _composite_z(row) + slot_par_weight * _slot_par_z(row, slot)

    def _row_to_roster_entry(row: dict, assigned_slot: str, pick_num: int, existing: bool = False) -> dict:
        round_num, _ = _pick_to_round_and_slot(pick_num, total_teams=total_teams)
        slot_score = _score_for_slot(row, assigned_slot)
        slot_par = _par_for_slot(row, assigned_slot)
        return {
            "pick": pick_num,
            "round": round_num,
            "name": row.get("Name", ""),
            "position": row.get("position", ""),
            "slot": assigned_slot,
            "score": round(slot_score, 3),
            "par": round(slot_par, 1),
            "fpts": round(_safe_float(row.get("League_FPTS", 0.0)), 1),
            "adp": _safe_int(row.get("ADP")),
            "recommended_pick": _safe_int(row.get("Recommended_Pick")),
            "tier": _safe_int(row.get("Tier")),
            "vadp": _safe_int(row.get("VADP")),
            "existing": existing,
        }

    def _best_future_score_for_slot(slot: str, candidate_name: str, picks_until_next: int) -> float | None:
        """
        Estimate the best score we'll still be able to get at this slot on our next pick
        after other teams make `picks_until_next` selections by queue order.
        """
        if picks_until_next <= 0:
            return None

        projected_taken: set[str] = set()
        taken_count = 0
        for row in pool:
            nm = str(row.get("Name", ""))
            if not nm or nm in taken_names or nm == candidate_name:
                continue
            projected_taken.add(nm)
            taken_count += 1
            if taken_count >= picks_until_next:
                break

        best = None
        for row in pool:
            nm = str(row.get("Name", ""))
            if not nm or nm in taken_names or nm == candidate_name or nm in projected_taken:
                continue
            elig = row.get("_elig", set())
            if not _slot_accepts_player(slot, elig):
                continue
            score = _score_for_slot(row, slot)
            if best is None or score > best:
                best = score
        return best

    def _zscore_map(values: dict[str, float]) -> dict[str, float]:
        if not values:
            return {}
        arr = np.array(list(values.values()), dtype=float)
        mean = float(arr.mean()) if arr.size else 0.0
        std = float(arr.std()) if arr.size else 1.0
        if std <= 1e-6 or np.isnan(std):
            std = 1.0
        return {k: (float(v) - mean) / std for k, v in values.items()}

    # Build all your scheduled picks for the full draft window.
    my_picks = []
    for rd in range(1, total_rounds + 1):
        if rd % 2 == 1:
            pick = (rd - 1) * total_teams + pick_position
        else:
            pick = rd * total_teams - pick_position + 1
        my_picks.append(pick)
    my_pick_set = set(my_picks)

    current_pick = int(df["Draft_Pick"].max()) if not df.empty else 0
    total_picks = total_teams * total_rounds

    players_df = df[~df["_is_skip"]].copy()
    drafted_with_pick = players_df[players_df["Draft_Pick"] > 0].sort_values("Draft_Pick")
    drafted_without_pick = players_df[(players_df["_is_drafted"]) & (players_df["Draft_Pick"] <= 0)]

    taken_names: set[str] = set(drafted_with_pick["Name"].astype(str))
    taken_names.update(drafted_without_pick["Name"].astype(str))

    available_for_replacement = players_df[~players_df["Name"].astype(str).isin(taken_names)].copy()
    available_for_replacement["_composite"] = pd.to_numeric(
        available_for_replacement.get(composite_col), errors="coerce"
    )
    comp_vals = available_for_replacement["_composite"].dropna()
    if not comp_vals.empty:
        composite_mean = float(comp_vals.mean())
        composite_std = float(comp_vals.std())
        if composite_std <= 1e-6 or np.isnan(composite_std):
            composite_std = 1.0
    slot_replacement_levels = _build_slot_replacement_levels(available_for_replacement)
    slot_par_stats = _build_slot_par_stats(available_for_replacement, slot_replacement_levels)

    # "Your rank" based on normalized composite across all positions.
    comp_rank_map: dict[str, int] = {}
    comp_rank_df = available_for_replacement[["Name", "_composite"]].copy()
    comp_rank_df = comp_rank_df.dropna(subset=["Name", "_composite"]).sort_values("_composite", ascending=False)
    for idx, nm in enumerate(comp_rank_df["Name"].astype(str).tolist(), start=1):
        if nm and nm not in comp_rank_map:
            comp_rank_map[nm] = idx

    my_roster: list[dict] = []
    for _, r in drafted_with_pick.iterrows():
        pick_num = int(r["Draft_Pick"])
        _, inferred_slot = _pick_to_round_and_slot(pick_num, total_teams=total_teams)
        slot_from_data = _safe_int(r.get("Draft_Team_Slot"))
        team_slot = slot_from_data if slot_from_data is not None and slot_from_data > 0 else inferred_slot
        if team_slot != pick_position:
            continue
        elig = r.get("Eligible_Positions", set())
        elig = elig if isinstance(elig, set) else _parse_eligible(elig)
        assigned_slot = _can_fill_slot(elig)
        if assigned_slot is None:
            assigned_slot = "BENCH_P" if _is_pitcher_player(elig) else "BENCH_H"
        else:
            slot_needs[assigned_slot] = max(0, slot_needs.get(assigned_slot, 0) - 1)
        my_roster.append(_row_to_roster_entry(r.to_dict(), assigned_slot, pick_num, existing=True))

    available = players_df[~players_df["Name"].astype(str).isin(taken_names)].copy()
    available["Adjusted_Rank"] = pd.to_numeric(available.get("Adjusted_Rank"), errors="coerce")
    available["_composite"] = pd.to_numeric(available.get(composite_col), errors="coerce")
    available = available.sort_values(
        by=["Adjusted_Rank", "_composite"],
        ascending=[True, False],
        na_position="last",
    ).reset_index(drop=True)
    pool = available.to_dict(orient="records")
    for row in pool:
        elig = row.get("Eligible_Positions", set())
        row["_elig"] = elig if isinstance(elig, set) else _parse_eligible(elig)
        row["_composite"] = _safe_float(row.get(composite_col, np.nan), default=np.nan)
        nm = str(row.get("Name", ""))
        fallback_rank = _safe_int(row.get("Adjusted_Rank")) or 999
        row["_my_rank"] = int(comp_rank_map.get(nm, fallback_rank))
    pool_idx = 0

    for overall_pick in range(current_pick + 1, total_picks + 1):
        if overall_pick in my_pick_set:
            best_player = None
            best_slot = None
            best_value = -1e9

            next_my_pick = next((p for p in my_picks if p > overall_pick), None)
            picks_until_next = (next_my_pick - overall_pick - 1) if next_my_pick is not None else 0
            candidate_rows: list[dict] = []

            for row in pool:
                name = str(row.get("Name", ""))
                if not name or name in taken_names:
                    continue
                elig = row.get("_elig", set())
                slot = _can_fill_slot(elig)
                if slot is None:
                    continue

                base_value = _score_for_slot(row, slot)  # composite+slotPAR blend
                future_best = _best_future_score_for_slot(slot, name, picks_until_next)
                dropoff = 0.0
                if future_best is not None:
                    dropoff = max(0.0, base_value - future_best)

                candidate_rows.append({
                    "row": row,
                    "slot": slot,
                    "base_value": base_value,
                    "dropoff": dropoff,
                })

            composite_z = _zscore_map({
                str(c["row"].get("Name", "")): _composite_z(c["row"])
                for c in candidate_rows
            })
            availability_urgency_z = _zscore_map({
                str(c["row"].get("Name", "")): float(c.get("dropoff", 0.0))
                for c in candidate_rows
            })

            for c in candidate_rows:
                row = c["row"]
                name = str(row.get("Name", ""))
                slot = c["slot"]
                # Requested strategy: weighted availability (dropoff risk) + composite only.
                value = (
                    0.75 * composite_z.get(name, 0.0) +
                    0.25 * availability_urgency_z.get(name, 0.0)
                )

                if value > best_value:
                    best_value = value
                    best_player = row
                    best_slot = slot

            if best_player is not None and best_slot is not None:
                taken_names.add(str(best_player.get("Name", "")))
                if best_slot in slot_needs:
                    slot_needs[best_slot] = max(0, slot_needs.get(best_slot, 0) - 1)
                my_roster.append(_row_to_roster_entry(best_player, best_slot, overall_pick, existing=False))
            else:
                # If no open starter slot can be filled, take best bench value.
                bench_pitcher = None
                bench_hitter = None
                bench_pitcher_score = -1e9
                bench_hitter_score = -1e9
                for row in pool:
                    name = str(row.get("Name", ""))
                    if not name or name in taken_names:
                        continue
                    elig = row.get("_elig", set())
                    bench_slot = "P" if _is_pitcher_player(elig) else "UTIL"
                    base_value = _score_for_slot(row, bench_slot)
                    if _is_pitcher_player(elig):
                        if base_value > bench_pitcher_score:
                            bench_pitcher_score = base_value
                            bench_pitcher = row
                    else:
                        if base_value > bench_hitter_score:
                            bench_hitter_score = base_value
                            bench_hitter = row

                if bench_pitcher is not None and bench_hitter is not None:
                    fallback = bench_pitcher if bench_pitcher_score >= bench_hitter_score else bench_hitter
                else:
                    fallback = bench_pitcher if bench_pitcher is not None else bench_hitter
                if fallback is not None:
                    taken_names.add(str(fallback.get("Name", "")))
                    slot = "BENCH_P" if fallback is bench_pitcher else "BENCH_H"
                    my_roster.append(_row_to_roster_entry(fallback, slot, overall_pick, existing=False))
        else:
            # Other teams pick by model rank queue (no ADP-based behavior).
            while pool_idx < len(pool):
                candidate = pool[pool_idx]
                pool_idx += 1
                cand_name = str(candidate.get("Name", ""))
                if cand_name and cand_name not in taken_names:
                    taken_names.add(cand_name)
                    break

    my_roster = sorted(my_roster, key=lambda x: x["pick"])
    return {
        "pick_position": pick_position,
        "total_teams": total_teams,
        "total_rounds": total_rounds,
        "current_pick": current_pick,
        "roster": my_roster,
        "picks": my_picks,
        "remaining_needs": {k: int(v) for k, v in slot_needs.items()},
        "score_column": "0.75*composite_z + 0.25*availability_dropoff_z (no ADP)",
    }


@app.get("/api/draft/ideal")
def ideal_draft_api(pick: int = 1, teams: int = 10):
    draft_df = _load_draft_df()
    if draft_df is None:
        return JSONResponse({"error": "No draft data"}, status_code=400)
    pick = max(1, min(pick, teams))
    max_pick_logged = 0
    if "Draft_Pick" in draft_df.columns:
        max_pick_logged = int(pd.to_numeric(draft_df["Draft_Pick"], errors="coerce").fillna(0).max())
    rounds_from_log = (max_pick_logged // teams) + 1 if max_pick_logged > 0 else 0
    total_rounds = max(sum(ROSTER_SLOTS.values()), rounds_from_log)
    result = _ideal_draft(draft_df, pick, total_teams=teams, total_rounds=total_rounds)
    return JSONResponse(result)


def _player_detail(df: pd.DataFrame, name: str):
    if not name:
        return None
    m = df[df["display_name"].str.fullmatch(name, case=False, na=False)]
    if m.empty:
        m = df[df["display_name"].str.contains(name, case=False, na=False)]
    if m.empty:
        return None
    row = m.iloc[0].to_dict()
    # Build organized sections
    identity = {
        k: row.get(k)
        for k in [
            "display_name",
            "Team",
            "position",
            "fantasy_team",
            "injury_status",
        ]
        if k in row
    }
    projections = {k.replace("proj_", ""): row[k] for k in row.keys() if k.startswith("proj_")}
    current = {k.replace("curr_", ""): row[k] for k in row.keys() if k.startswith("curr_")}

    # key metrics with bar normalization and clarity
    pos_str = str(identity.get("position", ""))
    is_pitcher = ("P" in pos_str) or ("Pitcher" in pos_str)

    def minmax_pct(series: pd.Series, value, invert: bool = False) -> float:
        try:
            x = float(value)
        except (TypeError, ValueError):
            return 0.0
        s = pd.to_numeric(series, errors="coerce").dropna()
        if s.empty:
            return 0.0
        vmin = s.min()
        vmax = s.max()
        if vmax == vmin:
            return 0.0
        t = (x - vmin) / (vmax - vmin)
        t = max(0.0, min(1.0, t))
        return 1.0 - t if invert else t

    def series_for(base_df: pd.DataFrame, fallback_df: pd.DataFrame, column: str) -> pd.Series:
        if column in base_df.columns:
            s = pd.to_numeric(base_df[column], errors="coerce").dropna()
            if not s.empty:
                return s
        if column in fallback_df.columns:
            s = pd.to_numeric(fallback_df[column], errors="coerce").dropna()
            if not s.empty:
                return s
        # ensure non-empty range to avoid division by zero elsewhere
        return pd.Series([0.0, 1.0])

    def value_for(row_dict: dict, column: str, dict_value):
        val = row_dict.get(column)
        return dict_value if (val is None) else val

    def badge_for(pct: float):
        if pct >= 0.75:
            return "great"
        if pct >= 0.5:
            return "good"
        if pct >= 0.35:
            return "avg"
        return "concern"


    # Build per-stat pct dictionaries for projections/current tables
    proj_pcts: dict[str, int] = {}
    curr_pcts: dict[str, int] = {}
    
    # Build qualified subsets and compute dynamic min/max percentiles per stat
    playable = df[df.get("has_valid_position", True) == True].copy()
    hitters_df = playable[~playable.get("norm_positions", []).apply(lambda xs: isinstance(xs, list) and any("P" in p for p in xs))]
    pitchers_df = playable[playable.get("norm_positions", []).apply(lambda xs: isinstance(xs, list) and any("P" in p for p in xs))]

    # Qualifiers: prefer current season usage if available
    if "curr_AB" in hitters_df.columns:
        hitters_df = hitters_df[pd.to_numeric(hitters_df["curr_AB"], errors="coerce").fillna(0) >= 50]
    if "curr_IP" in pitchers_df.columns:
        pitchers_df = pitchers_df[pd.to_numeric(pitchers_df["curr_IP"], errors="coerce").fillna(0) >= 20]

    def fill_pct(label: str, curr_col: str | None, proj_col: str | None, invert: bool = False, use_pitchers: bool = False):
        base_df = pitchers_df if use_pitchers else hitters_df
        if curr_col and label:
            s = series_for(base_df, playable, curr_col)
            val = value_for(row, curr_col, current.get(label))
            curr_pcts[label] = int(minmax_pct(s, val, invert) * 100)
        if proj_col and label:
            s = series_for(base_df, playable, proj_col)
            val = value_for(row, proj_col, projections.get(label))
            proj_pcts[label] = int(minmax_pct(s, val, invert) * 100)

    if is_pitcher:
        fill_pct("IP", "curr_IP", "proj_IP", invert=False, use_pitchers=True)
        fill_pct("FIP", "curr_FIP", "proj_FIP", invert=True, use_pitchers=True)
        fill_pct("WHIP", "curr_WHIP", "proj_WHIP", invert=True, use_pitchers=True)
        fill_pct("K-BB%", "curr_K-BB%", "proj_K-BB%", invert=False, use_pitchers=True)
        fill_pct("SV", "curr_SV", "proj_SV", invert=False, use_pitchers=True)
    else:
        fill_pct("AB", "curr_AB", "proj_AB", invert=False, use_pitchers=False)
        fill_pct("wOBA", "curr_wOBA", "proj_wOBA", invert=False, use_pitchers=False)
        fill_pct("wRC+", "curr_wRC+", "proj_wRC+", invert=False, use_pitchers=False)
        fill_pct("ISO", "curr_ISO", "proj_ISO", invert=False, use_pitchers=False)
        fill_pct("wBsR", "curr_wBsR", "proj_wBsR", invert=False, use_pitchers=False)

    return {
        "identity": identity,
        "projections": projections,
        "current": current,
        "is_pitcher": is_pitcher,
        # filtered rows for display-only relevant stats
        "proj_rows": (
            [("IP", projections.get("IP")), ("FIP", projections.get("FIP")), ("WHIP", projections.get("WHIP")), ("K-BB%", projections.get("K-BB%")), ("SV", projections.get("SV"))]
            if is_pitcher
            else [("AB", projections.get("AB")), ("wOBA", projections.get("wOBA")), ("wRC+", projections.get("wRC+")), ("ISO", projections.get("ISO")), ("wBsR", projections.get("wBsR"))]
        ),
        "curr_rows": (
            [("IP", current.get("IP")), ("FIP", current.get("FIP")), ("WHIP", current.get("WHIP")), ("K-BB%", current.get("K-BB%")), ("SV", current.get("SV"))]
            if is_pitcher
            else [("AB", current.get("AB")), ("wOBA", current.get("wOBA")), ("wRC+", current.get("wRC+")), ("ISO", current.get("ISO")), ("wBsR", current.get("wBsR"))]
        ),
        "proj_pcts": proj_pcts,
        "curr_pcts": curr_pcts,
    }


@app.get("/player", response_class=HTMLResponse)
def player(request: Request):
    csv_path = get_latest_csv()
    if not csv_path:
        return templates.TemplateResponse("no_data.html", {"request": request})
    df = _prepare_dataframe(csv_path)
    name = request.query_params.get("name", "")
    details = _player_detail(df, name)
    return templates.TemplateResponse(
        "player.html",
        {"request": request, "data_file": os.path.basename(csv_path), "player": details, "name": name},
    )


@app.get("/team", response_class=HTMLResponse)
def team_view(request: Request):
    csv_path = get_latest_csv()
    if not csv_path:
        return templates.TemplateResponse("no_data.html", {"request": request})
    df = _prepare_dataframe(csv_path)
    teams = sorted([t for t in df["fantasy_team"].dropna().unique() if str(t).lower() not in ["fa", "free agent"]])
    selected_team, hide_inj, min_score = _filters_from_qp(request.query_params, teams)
    pos = request.query_params.get("pos", "")
    positions = _positions_list(df)
    roster = _team_roster(df, selected_team, hide_inj, pos)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "teams": teams,
            "data_file": os.path.basename(csv_path),
            "selected_team": selected_team,
            "hide_injured": hide_inj,
            "min_score": min_score,
            "roster": roster,
            "view": "team",
            "positions": positions,
            "pos": pos,
        },
    )

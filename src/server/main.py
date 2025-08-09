from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import pandas as pd
import os
import subprocess, sys
sys.path.insert(0, str((Path(__file__).resolve().parent.parent)))
from data_utils import expand_positions, format_player_name  # type: ignore

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent
TEMPLATES_DIR = ROOT_DIR / "templates"
STATIC_DIR = ROOT_DIR / "static"

app = FastAPI(title="Fantasy Baseball Hub")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def get_latest_csv() -> str | None:
    out_dir = ROOT_DIR / "output"
    if not out_dir.exists():
        return None
    csvs = sorted(out_dir.glob("free_agents_ranked_*.csv"))
    return str(csvs[-1]) if csvs else None


def _filters_from_qp(qp, teams: list[str]):
    selected_team = qp.get("team", teams[0] if teams else "")
    hide_inj = qp.get("hideInjured", "true").lower() == "true"
    try:
        min_score = float(qp.get("minScore", "-1.0"))
    except ValueError:
        min_score = -1.0
    return selected_team, hide_inj, min_score


def _prepare_dataframe(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, low_memory=False)
    if "display_name" not in df.columns:
        df["display_name"] = df.apply(format_player_name, axis=1)
    if "norm_positions" not in df.columns:
        df["norm_positions"] = df["position"].apply(expand_positions)
    if "ScoreDelta" not in df.columns and {"curr_CompositeScore","proj_CompositeScore"}.issubset(df.columns):
        df["ScoreDelta"] = df["curr_CompositeScore"] - df["proj_CompositeScore"]
    df["has_valid_position"] = df["norm_positions"].apply(lambda x: isinstance(x, list) and len(x) > 0)
    return df


def _compute_upgrades(df: pd.DataFrame, team: str, hide_injured: bool, min_score: float):
    if hide_injured:
        df = df[~df["display_name"].str.contains(r"\(", na=False)]

    # Split team vs FA
    team_df = df[(df["fantasy_team"] == team) & (df["has_valid_position"])].copy()
    fa_df = df[(df["has_valid_position"]) & ((df["fantasy_team"].isna()) | (df["fantasy_team"].isin(["Free Agent","FA"])))]

    if team_df.empty or fa_df.empty:
        return []

    candidates = fa_df.sort_values("proj_CompositeScore", ascending=False).head(50)
    upgrades = []
    for _, fa in candidates.iterrows():
        for pos in fa.get("norm_positions", []):
            eligible = team_df[team_df["norm_positions"].apply(lambda xs: isinstance(xs, list) and pos in xs)]
            if eligible.empty:
                continue
            drops = eligible[eligible["proj_CompositeScore"] < fa["proj_CompositeScore"]]
            if drops.empty:
                continue
            drop = drops.nsmallest(1, "proj_CompositeScore").iloc[0]
            gain = float(fa["proj_CompositeScore"]) - float(drop["proj_CompositeScore"])
            if gain <= 0.15:
                continue
            key = (pos, str(drop.get("display_name")))
            existing_idx = next((i for i, u in enumerate(upgrades) if (u["pos"], u["drop"]["display_name"]) == key), None)
            item = {"pos": pos, "add": fa.to_dict(), "drop": drop.to_dict(), "gain": round(gain, 2)}
            if existing_idx is not None:
                if upgrades[existing_idx]["gain"] < gain:
                    upgrades[existing_idx] = item
            else:
                upgrades.append(item)
    return sorted(upgrades, key=lambda x: x["gain"], reverse=True)[:5]


def _free_agents(df: pd.DataFrame, hide_injured: bool, min_score: float, limit: int = 100):
    if hide_injured:
        df = df[~df["display_name"].str.contains(r"\(", na=False)]
    fa_df = df[(df["has_valid_position"]) & ((df["fantasy_team"].isna()) | (df["fantasy_team"].isin(["Free Agent","FA"])))]
    cols = [c for c in ["display_name","Team","position","proj_CompositeScore","curr_CompositeScore"] if c in fa_df.columns]
    fa_df = fa_df.sort_values("proj_CompositeScore", ascending=False)
    return fa_df[cols].head(limit).to_dict(orient="records")


def _team_roster(df: pd.DataFrame, team: str, hide_injured: bool):
    if hide_injured:
        df = df[~df["display_name"].str.contains(r"\(", na=False)]
    team_df = df[(df["fantasy_team"] == team) & (df["has_valid_position"])].copy()
    cols = [c for c in ["display_name","Team","position","proj_CompositeScore","curr_CompositeScore"] if c in team_df.columns]
    return team_df[cols].sort_values("proj_CompositeScore", ascending=False).to_dict(orient="records")


def _drop_candidates(df: pd.DataFrame, team: str, hide_injured: bool, limit: int = 20):
    if hide_injured:
        df = df[~df["display_name"].str.contains(r"\(", na=False)]
    team_df = df[(df["fantasy_team"] == team) & (df["has_valid_position"])].copy()
    if "ScoreDelta" in team_df.columns:
        team_df = team_df.sort_values("ScoreDelta")  # most negative first
    else:
        team_df = team_df.sort_values("proj_CompositeScore")
    cols = [c for c in ["display_name","Team","position","proj_CompositeScore","curr_CompositeScore","ScoreDelta"] if c in team_df.columns]
    return team_df[cols].head(limit).to_dict(orient="records")


    


def _league_summary(df: pd.DataFrame, hide_injured: bool):
    if hide_injured:
        df = df[~df["display_name"].str.contains(r"\(", na=False)]
    playable = df[df["has_valid_position"]].copy()
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
        m = df[df["display_name"].str.contains(name, case=False, na=False)]
        return m.head(1).to_dict(orient="records")[0] if not m.empty else None
    return pick(name1), pick(name2)


def _positions_list(df: pd.DataFrame):
    pos_set = set()
    for xs in df.get("norm_positions", []):
        if isinstance(xs, list):
            pos_set.update(xs)
    return sorted(pos_set)


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
    cols = [
        "display_name",
        "Team",
        "position",
        "fantasy_team",
        "proj_CompositeScore",
        "curr_CompositeScore",
        "proj_AB",
        "proj_wOBA",
        "proj_wRC+",
        "proj_ISO",
        "proj_wBsR",
        "proj_IP",
        "proj_FIP",
        "proj_WHIP",
        "proj_K-BB%",
        "proj_SV",
        "injury_status",
    ]
    present = [c for c in cols if c in data.columns]
    page_df = data[present].iloc[start:end].copy()
    return page_df.to_dict(orient="records"), total


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    csv_path = get_latest_csv()
    if not csv_path:
        return templates.TemplateResponse("no_data.html", {"request": request})

    df = _prepare_dataframe(csv_path)
    # Basic filters to send to UI
    teams = sorted([t for t in df["fantasy_team"].dropna().unique() if str(t).lower() not in ["fa", "free agent"]])
    selected_team, hide_inj, min_score = _filters_from_qp(request.query_params, teams)
    upgrades = _compute_upgrades(df, selected_team, hide_inj, min_score)
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
            "upgrades": upgrades,
            "view": "add_drop",
            "fa": fa,
        },
    )

@app.post("/update")
def update_data():
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
    drops = _drop_candidates(df, selected_team, hide_inj)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "teams": teams, "data_file": os.path.basename(csv_path),
         "selected_team": selected_team, "hide_injured": hide_inj, "min_score": min_score,
         "drops": drops, "view": "drop_candidates"}
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
    p1 = request.query_params.get("p1", "")
    p2 = request.query_params.get("p2", "")
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
            "view": "players",
        },
    )


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

    def fmt(val, kind: str):
        try:
            x = float(val)
        except (TypeError, ValueError):
            return ""
        if kind == "%":
            return f"{x:.3f}%"
        if kind == "int":
            return f"{x:.0f}"
        # default: always 3 decimals for visibility consistency
        return f"{x:.3f}"

    metrics = []
    # Build qualified subsets and compute dynamic min/max percentiles per stat
    playable = df[df.get("has_valid_position", True) == True].copy()
    hitters_df = playable[~playable.get("norm_positions", []).apply(lambda xs: isinstance(xs, list) and any("P" in p for p in xs))]
    pitchers_df = playable[playable.get("norm_positions", []).apply(lambda xs: isinstance(xs, list) and any("P" in p for p in xs))]

    # Qualifiers: prefer current season usage if available
    if "curr_AB" in hitters_df.columns:
        hitters_df = hitters_df[pd.to_numeric(hitters_df["curr_AB"], errors="coerce").fillna(0) >= 50]
    if "curr_IP" in pitchers_df.columns:
        pitchers_df = pitchers_df[pd.to_numeric(pitchers_df["curr_IP"], errors="coerce").fillna(0) >= 20]

    # CompositeScore (use overall distribution)
    proj_c = projections.get("CompositeScore")
    curr_c = current.get("CompositeScore")
    comp_series_curr = series_for(playable, playable, "curr_CompositeScore")
    comp_series_proj = series_for(playable, playable, "proj_CompositeScore") if "proj_CompositeScore" in playable.columns else comp_series_curr
    curr_c_pct = minmax_pct(comp_series_curr, value_for(row, "curr_CompositeScore", curr_c), invert=False)
    proj_c_pct = minmax_pct(comp_series_proj, value_for(row, "proj_CompositeScore", proj_c), invert=False)
    metrics.append({
        "label": "Composite",
        "hint": "Overall value (higher is better)",
        "proj": fmt(proj_c, ""),
        "curr": fmt(curr_c, ""),
        "curr_bar": int(curr_c_pct * 100),
        "curr_badge": badge_for(curr_c_pct),
        "proj_bar": int(proj_c_pct * 100),
        "proj_badge": badge_for(proj_c_pct),
        "delta": fmt((float(curr_c) - float(proj_c)) if (curr_c is not None and proj_c is not None) else None, ""),
        "delta_class": ("pos" if (curr_c is not None and proj_c is not None and float(curr_c)-float(proj_c) > 0) else ("neg" if (curr_c is not None and proj_c is not None and float(curr_c)-float(proj_c) < 0) else "neutral")),
    })
    if is_pitcher:
        kbb_p = projections.get("K-BB%")
        kbb_c = current.get("K-BB%")
        whip_p = projections.get("WHIP")
        whip_c = current.get("WHIP")
        fip_p = projections.get("FIP")
        fip_c = current.get("FIP")
        kbb_c_pct = minmax_pct(series_for(pitchers_df, playable, "curr_K-BB%"), value_for(row, "curr_K-BB%", kbb_c), invert=False)
        kbb_p_pct = minmax_pct(series_for(pitchers_df, playable, "proj_K-BB%"), value_for(row, "proj_K-BB%", kbb_p), invert=False)
        whip_c_pct = minmax_pct(series_for(pitchers_df, playable, "curr_WHIP"), value_for(row, "curr_WHIP", whip_c), invert=True)
        whip_p_pct = minmax_pct(series_for(pitchers_df, playable, "proj_WHIP"), value_for(row, "proj_WHIP", whip_p), invert=True)
        fip_c_pct = minmax_pct(series_for(pitchers_df, playable, "curr_FIP"), value_for(row, "curr_FIP", fip_c), invert=True)
        fip_p_pct = minmax_pct(series_for(pitchers_df, playable, "proj_FIP"), value_for(row, "proj_FIP", fip_p), invert=True)
        metrics += [
            {"label": "K-BB%", "hint": "Strikeouts minus walks (higher is better)",
             "proj": fmt(kbb_p, "%"), "curr": fmt(kbb_c, "%"),
             "curr_bar": int(kbb_c_pct * 100),
             "curr_badge": badge_for(kbb_c_pct),
             "proj_bar": int(kbb_p_pct * 100),
             "proj_badge": badge_for(kbb_p_pct),
             "delta": fmt((float(kbb_c) - float(kbb_p)) if (kbb_c is not None and kbb_p is not None) else None, "%"),
             "delta_class": ("pos" if (kbb_c is not None and kbb_p is not None and float(kbb_c)-float(kbb_p) > 0) else ("neg" if (kbb_c is not None and kbb_p is not None and float(kbb_c)-float(kbb_p) < 0) else "neutral"))},
            {"label": "WHIP", "hint": "Walks + hits per inning (lower is better)",
             "proj": fmt(whip_p, ""), "curr": fmt(whip_c, ""),
             "curr_bar": int(whip_c_pct * 100),
             "curr_badge": badge_for(whip_c_pct),
             "proj_bar": int(whip_p_pct * 100),
             "proj_badge": badge_for(whip_p_pct),
             "delta": fmt((float(whip_c) - float(whip_p)) if (whip_c is not None and whip_p is not None) else None, ""),
             "delta_class": ("pos" if (whip_c is not None and whip_p is not None and float(whip_c)-float(whip_p) < 0) else ("neg" if (whip_c is not None and whip_p is not None and float(whip_c)-float(whip_p) > 0) else "neutral"))},
            {"label": "FIP", "hint": "Fielding independent pitching (lower is better)",
             "proj": fmt(fip_p, ""), "curr": fmt(fip_c, ""),
             "curr_bar": int(fip_c_pct * 100),
             "curr_badge": badge_for(fip_c_pct),
             "proj_bar": int(fip_p_pct * 100),
             "proj_badge": badge_for(fip_p_pct),
             "delta": fmt((float(fip_c) - float(fip_p)) if (fip_c is not None and fip_p is not None) else None, ""),
             "delta_class": ("pos" if (fip_c is not None and fip_p is not None and float(fip_c)-float(fip_p) < 0) else ("neg" if (fip_c is not None and fip_p is not None and float(fip_c)-float(fip_p) > 0) else "neutral"))},
        ]
    else:
        woba_p = projections.get("wOBA")
        woba_c = current.get("wOBA")
        iso_p = projections.get("ISO")
        iso_c = current.get("ISO")
        wrc_p = projections.get("wRC+")
        wrc_c = current.get("wRC+")
        woba_c_pct = minmax_pct(series_for(hitters_df, playable, "curr_wOBA"), value_for(row, "curr_wOBA", woba_c), invert=False)
        woba_p_pct = minmax_pct(series_for(hitters_df, playable, "proj_wOBA"), value_for(row, "proj_wOBA", woba_p), invert=False)
        iso_c_pct = minmax_pct(series_for(hitters_df, playable, "curr_ISO"), value_for(row, "curr_ISO", iso_c), invert=False)
        iso_p_pct = minmax_pct(series_for(hitters_df, playable, "proj_ISO"), value_for(row, "proj_ISO", iso_p), invert=False)
        wrc_c_pct = minmax_pct(series_for(hitters_df, playable, "curr_wRC+"), value_for(row, "curr_wRC+", wrc_c), invert=False)
        wrc_p_pct = minmax_pct(series_for(hitters_df, playable, "proj_wRC+"), value_for(row, "proj_wRC+", wrc_p), invert=False)
        metrics += [
            {"label": "wOBA", "hint": "Weighted on-base average (higher is better)",
             "proj": fmt(woba_p, ""), "curr": fmt(woba_c, ""),
             "curr_bar": int(woba_c_pct * 100),
             "curr_badge": badge_for(woba_c_pct),
             "proj_bar": int(woba_p_pct * 100),
             "proj_badge": badge_for(woba_p_pct),
             "delta": fmt((float(woba_c) - float(woba_p)) if (woba_c is not None and woba_p is not None) else None, ""),
             "delta_class": ("pos" if (woba_c is not None and woba_p is not None and float(woba_c)-float(woba_p) > 0) else ("neg" if (woba_c is not None and woba_p is not None and float(woba_c)-float(woba_p) < 0) else "neutral"))},
            {"label": "ISO", "hint": "Isolated power (higher is better)",
             "proj": fmt(iso_p, ""), "curr": fmt(iso_c, ""),
             "curr_bar": int(iso_c_pct * 100),
             "curr_badge": badge_for(iso_c_pct),
             "proj_bar": int(iso_p_pct * 100),
             "proj_badge": badge_for(iso_p_pct),
             "delta": fmt((float(iso_c) - float(iso_p)) if (iso_c is not None and iso_p is not None) else None, ""),
             "delta_class": ("pos" if (iso_c is not None and iso_p is not None and float(iso_c)-float(iso_p) > 0) else ("neg" if (iso_c is not None and iso_p is not None and float(iso_c)-float(iso_p) < 0) else "neutral"))},
            {"label": "wRC+", "hint": "Run creation index (100 = avg)",
             "proj": fmt(wrc_p, "int"), "curr": fmt(wrc_c, "int"),
             "curr_bar": int(wrc_c_pct * 100),
             "curr_badge": badge_for(wrc_c_pct),
             "proj_bar": int(wrc_p_pct * 100),
             "proj_badge": badge_for(wrc_p_pct),
             "delta": fmt((float(wrc_c) - float(wrc_p)) if (wrc_c is not None and wrc_p is not None) else None, "int"),
             "delta_class": ("pos" if (wrc_c is not None and wrc_p is not None and float(wrc_c)-float(wrc_p) > 0) else ("neg" if (wrc_c is not None and wrc_p is not None and float(wrc_c)-float(wrc_p) < 0) else "neutral"))},
        ]

    # Build per-stat pct dictionaries for projections/current tables
    proj_pcts: dict[str, int] = {}
    curr_pcts: dict[str, int] = {}

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
        "metrics": metrics,
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
    roster = _team_roster(df, selected_team, hide_inj)
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
        },
    )



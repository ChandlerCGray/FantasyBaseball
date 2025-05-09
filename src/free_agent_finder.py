import os
import glob
import re
import pandas as pd

TEAM_FILTER = "Land of 10,000 Rakes"
ESPNS_POSITIONS = ["C", "1B", "2B", "3B", "SS", "OF", "DH", "P", "1B/3B", "2B/SS"]

PITCHER_STATS = ["IP", "FIP", "WHIP", "K-BB%", "SV"]
HITTER_STATS = ["AB", "wOBA", "ISO", "wRC+", "wBsR"]

def expand_positions(pos_str):
    if not isinstance(pos_str, str):
        return []
    pos_str = pos_str.upper().replace("\n", " ").replace("/", " ")
    raw_positions = re.split(r"[,\s]+", pos_str.strip())

    pitcher_roles = {"P", "SP", "RP", "CL"}
    hitter_roles = {"C", "1B", "2B", "3B", "SS", "OF", "DH"}

    normalized = set()
    for pos in raw_positions:
        if pos in pitcher_roles:
            normalized.add("P")
        elif pos in hitter_roles:
            normalized.add(pos)

    if "P" in normalized and any(pos in normalized for pos in hitter_roles):
        return []
    return list(normalized)

def match_espn_position(pos_list, target):
    if not isinstance(pos_list, list):
        return False
    if target == "1B/3B":
        return any(p in pos_list for p in ["1B", "3B"])
    if target == "2B/SS":
        return any(p in pos_list for p in ["2B", "SS"])
    return target in pos_list

def get_newest_csv(folder="../output", pattern="free_agents_ranked_*.csv"):
    files = glob.glob(os.path.join(folder, pattern))
    return max(files, key=os.path.getmtime) if files else None

def build_suggestion(pos, group, current_fa, current_roster=None):
    proj_score_fa = current_fa.get("proj_CompositeScore")
    curr_score_fa = current_fa.get("curr_CompositeScore")

    proj_score_roster = current_roster.get("proj_CompositeScore") if current_roster is not None else None
    curr_score_roster = current_roster.get("curr_CompositeScore") if current_roster is not None else None

    suggestion = {
        "Roster Player": current_roster["Name"] if current_roster is not None else None,
        "Position": pos,
        "Free Agent": current_fa["Name"],
        "FA Projected Score": proj_score_fa,
        "FA Current Score": curr_score_fa if pd.notna(curr_score_fa) else None
    }

    if current_roster is not None:
        proj_delta = proj_score_fa - proj_score_roster if pd.notna(proj_score_fa) and pd.notna(proj_score_roster) else None
        curr_delta = curr_score_fa - curr_score_roster if pd.notna(curr_score_fa) and pd.notna(curr_score_roster) else None
        reason_parts = []

        if pd.notna(proj_delta):
            if proj_delta > 2:
                reason_parts.append(f"Proj much better (+{proj_delta:.1f})")
            elif proj_delta > 0:
                reason_parts.append(f"Proj upgrade (+{proj_delta:.1f})")
            elif proj_delta < 0:
                reason_parts.append(f"Proj downgrade ({proj_delta:.1f})")

        if pd.notna(curr_delta):
            if curr_delta > 3:
                reason_parts.append(f"Curr breakout (+{curr_delta:.1f})")
            elif curr_delta > 1.5:
                reason_parts.append(f"Curr hot streak (+{curr_delta:.1f})")
            elif curr_delta < -1:
                reason_parts.append(f"Curr cold streak ({curr_delta:.1f})")

        suggestion.update({
            "Roster Projected Score": proj_score_roster,
            "Roster Current Score": curr_score_roster,
            "Score Delta (Projected)": proj_delta,
            "Score Delta (Current)": curr_delta,
            "Reason": ", ".join(reason_parts)
        })

    return suggestion

def suggest_free_agents():
    path = get_newest_csv()
    if not path:
        print("No ranked data found.")
        return pd.DataFrame()

    df = pd.read_csv(path, low_memory=False)
    df["fantasy_team"] = df["fantasy_team"].astype(str).str.lower()
    df["norm_positions"] = df["position"].apply(expand_positions)
    df = df[df["norm_positions"].apply(len) > 0]

    fa = df[df["fantasy_team"].isin(["free agent", "fa"])]
    roster = df[df["fantasy_team"] == TEAM_FILTER.lower()]

    suggestions = []

    for espn_pos in ESPNS_POSITIONS:
        group = "Pitcher" if espn_pos == "P" else "Hitter"
        fa_pos = fa[fa["norm_positions"].apply(lambda lst: match_espn_position(lst, espn_pos))].sort_values(by="proj_CompositeScore", ascending=False)
        roster_pos = roster[roster["norm_positions"].apply(lambda lst: match_espn_position(lst, espn_pos))].sort_values(by="proj_CompositeScore")

        if not roster_pos.empty:
            for i in range(min(5, len(fa_pos), len(roster_pos))):
                suggestion = build_suggestion(espn_pos, group, fa_pos.iloc[i], roster_pos.iloc[i])
                if suggestion.get("Reason"):
                    suggestions.append(suggestion)
        else:
            for i in range(min(5, len(fa_pos))):
                suggestions.append(build_suggestion(espn_pos, group, fa_pos.iloc[i]))

    return pd.DataFrame(suggestions)

def main():
    print("Analyzing latest file...")
    df = suggest_free_agents()
    if df.empty:
        print("No suggestions found.")
    else:
        print(df.to_string(index=False))

if __name__ == "__main__":
    main()

import os
import glob
import re
import pandas as pd
import streamlit as st
import plotly.express as px
import subprocess
import sys

# =============================================================================
# Constants & Configurations
# =============================================================================
ESPNS_POSITIONS = ["C", "1B", "2B", "3B", "SS", "OF", "DH", "P", "1B/3B", "2B/SS"]
MEASURED_STATS = [
    "AB", "wOBA", "wRC+", "ISO", "wBsR",       # hitter stats
    "IP", "FIP", "WHIP", "K-BB%", "SV"         # pitcher stats
]

# Score difference thresholds and weights for composite calculations.
SMALL_DIFF = 0.1
PROJ_WEIGHT = 0.8
CURR_WEIGHT = 0.2
STRONG_UPGRADE_THRESHOLD = 0.75
UPGRADE_THRESHOLD = 0.25
UNDERPERFORMANCE_THRESHOLD = -0.25

DEFAULT_TEAM = "land of 10,000 rakes"  # ensure it's lowercase

# =============================================================================
# Streamlit Setup & Theme-based Style Variables
# =============================================================================
st.set_page_config(page_title="Fantasy Baseball Tools", layout="wide")
st.title("⚾ Fantasy Baseball Analyzer")

# Compute theme-based variables once
is_dark = st.get_option("theme.base") == "dark"
card_bg = "#2f2f2f" if is_dark else "#f7f7f7"
card_text = "#f2f2f2" if is_dark else "#111111"
card_shadow = "0 2px 6px rgba(0,0,0,0.4)"

def run_scraper():
    if st.button("🔄 Run Scraper"):
        with st.spinner("Running main.py..."):
            try:
                result = subprocess.run(
                    [sys.executable, "./src/main.py"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                st.success("✅ Data updated successfully!")
                st.code(result.stdout or "No output.")
            except subprocess.CalledProcessError as e:
                st.error("❌ Update failed.")
                st.code(e.stderr or "No error output.")


# =============================================================================
# Helper Functions
# =============================================================================
def get_newest_csv(folder="./output", pattern="free_agents_ranked_*.csv"):
    files = glob.glob(os.path.join(folder, pattern))
    return max(files, key=os.path.getmtime) if files else None

def expand_positions(pos_str):
    if not isinstance(pos_str, str):
        return []
    pos_str = pos_str.upper().replace("\n", " ").replace("/", " ")
    raw_positions = re.split(r"[,\s]+", pos_str.strip())
    pitcher_roles = {"P", "SP", "RP", "CL", "PITCHER"}
    hitter_roles = {"C", "1B", "2B", "3B", "SS", "OF", "DH"}
    normalized = set()
    for pos in raw_positions:
        if pos in pitcher_roles:
            normalized.add("P")
        elif pos in hitter_roles:
            normalized.add(pos)
    return list(normalized)

def match_espn_position(pos_list, target):
    if not isinstance(pos_list, list):
        return False
    if target == "1B/3B":
        return any(p in pos_list for p in ["1B", "3B"])
    if target == "2B/SS":
        return any(p in pos_list for p in ["2B", "SS"])
    return target in pos_list

def measured_stat_columns(df, group):
    # Use display_name if available so that injured players are clearly marked.
    base_name = "display_name" if "display_name" in df.columns else "Name"
    base_cols = [base_name, "position", "proj_CompositeScore", "curr_CompositeScore", "ScoreDelta"]
    hitter_stats = [
        "proj_AB", "proj_wOBA", "proj_wRC+", "proj_ISO", "proj_wBsR",
        "curr_AB", "curr_wOBA", "curr_wRC+", "curr_ISO", "curr_wBsR"
    ]
    pitcher_stats = [
        "proj_IP", "proj_FIP", "proj_WHIP", "proj_K-BB%", "proj_SV",
        "curr_IP", "curr_FIP", "curr_WHIP", "curr_K-BB%", "curr_SV"
    ]
    stats = hitter_stats if group == "Hitter" else pitcher_stats
    return [col for col in base_cols + stats if col in df.columns]

def stat_table(df, group):
    subset = df[df["PlayerGroup"] == group].copy().head(5)
    # Rename the display name column to "Player" for presentation.
    return subset[measured_stat_columns(subset, group)].rename(columns={
        "display_name": "Player", "Name": "Player",
        "position": "Pos",
        "proj_CompositeScore": "Proj",
        "curr_CompositeScore": "Curr",
        "ScoreDelta": "Δ"
    })

def safe_delta(fa_score, roster_score):
    if pd.notna(fa_score) and pd.notna(roster_score):
        return fa_score - roster_score
    return None

def build_reason_message(diff, label, fa_name, roster_name):
    if diff is None:
        return f"⚠️ Comparison not possible between {fa_name} and {roster_name} (data missing)"
    if diff > SMALL_DIFF:
        return f"🌡️ {fa_name} outperforms {roster_name} by +{diff:.2f} {label}"
    elif diff < -SMALL_DIFF:
        return f"🧊 {fa_name} underperforms {roster_name} by {diff:.2f} {label}"
    else:
        return f"➖ {label.capitalize()} performance nearly identical for {fa_name} and {roster_name}"

def weighted_delta(proj_diff, curr_diff, proj_weight=PROJ_WEIGHT, curr_weight=CURR_WEIGHT):
    if proj_diff is None or curr_diff is None:
        return None
    return (proj_diff * proj_weight) + (curr_diff * curr_weight)

def determine_bucket_weighted(weighted_diff):
    if weighted_diff is None:
        return "⚠️ Inconclusive"
    if weighted_diff >= STRONG_UPGRADE_THRESHOLD:
        return "🚀 Strong upgrade"
    elif weighted_diff >= UPGRADE_THRESHOLD:
        return "✅ Upgrade"
    elif weighted_diff < UNDERPERFORMANCE_THRESHOLD:
        return "⚠️ Underperforming"
    else:
        return "➖ Marginal"

def build_suggestion(pos, group, current_fa, current_roster=None):
    def format_name(name):
        if not isinstance(name, str) or "." in name:
            return name
        parts = name.strip().split()
        return f"{parts[0][0]}. {' '.join(parts[1:])}" if len(parts) > 1 else name

    # Use display_name if available so that injured status is clear.
    fa_full_name = current_fa.get("display_name", current_fa.get("Name", ""))
    roster_full_name = current_roster.get("display_name", current_roster.get("Name", "")) if current_roster is not None else None

    fa_display_name = format_name(fa_full_name)
    roster_display_name = format_name(roster_full_name) if roster_full_name else None

    proj_score_fa = current_fa.get("proj_CompositeScore")
    curr_score_fa = current_fa.get("curr_CompositeScore")
    proj_score_roster = current_roster["proj_CompositeScore"] if current_roster is not None else None
    curr_score_roster = current_roster["curr_CompositeScore"] if current_roster is not None else None

    suggestion = {
        "Free Agent": current_fa.get("Name", ""),
        "FA Display Name": fa_display_name,
        "Roster Player": current_roster.get("Name", "") if current_roster is not None else None,
        "Roster Display Name": roster_display_name,
        "Position": pos,
        "FA Projected Score": proj_score_fa,
        "FA Current Score": curr_score_fa if pd.notna(curr_score_fa) else None
    }

    if current_roster is not None:
        proj_diff = safe_delta(proj_score_fa, proj_score_roster)
        curr_diff = safe_delta(curr_score_fa, curr_score_roster)
        reason_proj = build_reason_message(proj_diff, "projected", fa_display_name, roster_display_name)
        reason_curr = build_reason_message(curr_diff, "current", fa_display_name, roster_display_name)
        reason_message = "; ".join([reason_proj, reason_curr])
        overall_weighted_diff = weighted_delta(proj_diff, curr_diff)
        summary = determine_bucket_weighted(overall_weighted_diff)
        suggestion.update({
            "Roster Projected Score": proj_score_roster,
            "Roster Current Score": curr_score_roster,
            "Score Delta (Projected)": proj_diff,
            "Score Delta (Current)": curr_diff,
            "Weighted Delta": overall_weighted_diff,
            "Reason": reason_message,
            "Summary": summary,
        })
    return suggestion

def format_stat_section(df):
    base_name = "display_name" if "display_name" in df.columns else "Name"
    return df[measured_stat_columns(df, group="")].rename(columns={
        base_name: "Player",
        "position": "Pos",
        "proj_CompositeScore": "Proj",
        "curr_CompositeScore": "Curr",
        "ScoreDelta": "Δ"
    })

def classify_player(pos_list):
    if not isinstance(pos_list, list) or not pos_list:
        return "Unknown"
    if "P" in pos_list and any(pos in {"C", "1B", "2B", "3B", "SS", "OF", "DH"} for pos in pos_list):
        return "Two-Way"
    if "P" in pos_list:
        return "Pitcher"
    return "Hitter"

def abbreviate_name(name):
    parts = name.split()
    if len(parts) > 1:
        return f"{parts[0][0]}. {parts[-1]}"
    return name

def get_stat(df, player, prefix, stat_key):
    col_name = f"{prefix}_{stat_key}"
    val = df.loc[df["Name"] == player, col_name].values
    if len(val) > 0:
        try:
            return round(val[0], 3) if pd.notna(val[0]) else "—"
        except Exception:
            return "—"
    return "—"

def is_pitcher_player(df, player_name):
    row = df[df["Name"] == player_name]
    if row.empty:
        return False
    positions = row.iloc[0]["norm_positions"]
    return any(p in ["P", "SP", "RP"] for p in positions)

def display_suggestions(tier_df, fa_df, team_df):
    for i in range(0, len(tier_df), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j >= len(tier_df):
                break
            row_data = tier_df.iloc[i + j]
            name_fa = row_data["Free Agent"]
            name_roster = row_data["Roster Player"]
            pos = row_data["Position"]
            reason = row_data.get("Reason", "")
            proj_delta = row_data.get("Score Delta (Projected)")
            curr_delta = row_data.get("Score Delta (Current)")
            weighted_val = row_data.get("Weighted Delta")

            proj_delta_str = f"{proj_delta:.2f}" if pd.notna(proj_delta) else "N/A"
            curr_delta_str = f"{curr_delta:.2f}" if pd.notna(curr_delta) else "N/A"
            weighted_delta_str = f"{weighted_val:.2f}" if pd.notna(weighted_val) else "N/A"

            proj_color = "#2ecc71" if proj_delta and proj_delta > 0 else "#e74c3c"
            curr_color = "#2ecc71" if curr_delta and curr_delta > 0 else "#e74c3c"
            weighted_color = "#2ecc71" if weighted_val and weighted_val > 0 else "#e74c3c"

            fa_abbrev = abbreviate_name(row_data.get("FA Display Name", name_fa))
            roster_abbrev = abbreviate_name(row_data.get("Roster Display Name", name_roster)) if name_roster else "N/A"

            with col:
                with st.expander(f"📌 {pos} — {row_data.get('FA Display Name', name_fa)} over {row_data.get('Roster Display Name', name_roster) or 'N/A'}", expanded=False):
                    st.markdown(f"""
                        <div class="fa-tile" style="
                            border-radius: 1rem;
                            background-color: #1e1e1e;
                            padding: 1.2rem;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
                            color: #f5f5f5;
                            font-family: 'Segoe UI', sans-serif;
                            transition: all 0.2s ease-in-out;
                        ">
                            <div style="font-size: 1.1rem; font-weight: bold; margin-bottom: 0.3rem;">
                                {row_data.get('FA Display Name', name_fa)}
                            </div>
                            <div style="font-size: 0.9rem; color: #ccc; margin-bottom: 0.5rem;">
                                replacing <span style="color: #bbb;">{row_data.get('Roster Display Name', name_roster) or 'N/A'}</span>
                            </div>
                            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; font-size: 0.85rem; margin-bottom: 0.5rem;">
                                <div style="background-color: {proj_color}; color: white; padding: 0.3rem 0.6rem; border-radius: 1rem;">
                                    🧮 Proj Δ: {proj_delta_str}
                                </div>
                                <div style="background-color: {curr_color}; color: white; padding: 0.3rem 0.6rem; border-radius: 1rem;">
                                    🔥 Curr Δ: {curr_delta_str}
                                </div>
                                <div style="background-color: {weighted_color}; color: white; padding: 0.3rem 0.6rem; border-radius: 1rem;">
                                    🏆 Score: {weighted_delta_str}
                                </div>
                            </div>
                            <div style="font-size: 0.8rem; color: #aaa;">
                                💡 {reason}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    st.markdown("---")
                    st.markdown(f"#### 📊 {fa_abbrev} Stat Breakdown")

                    def format_stat(value):
                        return round(value, 3) if isinstance(value, (float, int)) and pd.notna(value) else "—"

                    hitter_stats = {
                        "AB": "At Bats",
                        "wOBA": "wOBA",
                        "wRC+": "wRC+",
                        "ISO": "ISO",
                        "wBsR": "wBsR"
                    }
                    pitcher_stats = {
                        "IP": "IP",
                        "FIP": "FIP",
                        "WHIP": "WHIP",
                        "K-BB%": "K-BB%",
                        "SV": "Saves"
                    }
                    stat_labels = pitcher_stats if is_pitcher_player(fa_df, name_fa) else hitter_stats
                    rows = []
                    for stat_key, label in stat_labels.items():
                        rows.append({
                            "Stat": label,
                            f"{fa_abbrev} (Proj)": get_stat(fa_df, name_fa, "proj", stat_key),
                            f"{roster_abbrev} (Proj)": get_stat(team_df, name_roster, "proj", stat_key),
                            f"{fa_abbrev} (Curr)": get_stat(fa_df, name_fa, "curr", stat_key),
                            f"{roster_abbrev} (Curr)": get_stat(team_df, name_roster, "curr", stat_key),
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True)

# use a fixed dark background color so that tiles don’t appear white:
card_bg = "#2f2f2f"  
card_text = "#f2f2f2"
card_shadow = "0 2px 6px rgba(0,0,0,0.4)"

def display_card(title, value, icon="", color=None, description=""):
    if color is None:
        color = card_text
    return f"""
    <div style="
        background-color: {card_bg};
        color: {card_text};
        padding: 1rem;
        border-radius: 0.75rem;
        box-shadow: {card_shadow};
        text-align: center;
    ">
        <div style="font-size: 0.9rem; opacity: 0.8;">{title}</div>
        <div style="font-size: 1.2rem; font-weight: bold; color: {color}; margin: 0.25rem 0;">
            {icon} {value}
        </div>
        <div style="font-size: 1rem; font-weight: 600;">{description}</div>
    </div>
    """

# =============================================================================
# Mode Rendering Functions
# =============================================================================
def render_team_dashboard(df, team_df, csv_path):
    st.caption(f"Using data from: `{os.path.basename(csv_path)}`")
    # Injury filter is applied globally via the hide_injured flag.
    view_mode = st.radio("View", ["All", "Hitter", "Pitcher"], horizontal=True)

    # Classify players based on normalized positions.
    team_df["PlayerGroup"] = team_df["norm_positions"].apply(classify_player)
    filtered_df = team_df.copy()
    if view_mode != "All":
        filtered_df = filtered_df[filtered_df["PlayerGroup"] == view_mode]

    if filtered_df.empty:
        st.warning(f"No {view_mode.lower()}s found on your team.")
        st.stop()

    filtered_df["ScoreDelta"] = filtered_df["curr_CompositeScore"] - filtered_df["proj_CompositeScore"]

    st.header("📊 Team Snapshot")
    over = filtered_df.sort_values("ScoreDelta", ascending=False).head(5)
    under = filtered_df.sort_values("ScoreDelta").head(5)
    volatile = filtered_df.assign(volatility=filtered_df["ScoreDelta"].abs()).sort_values("volatility", ascending=False).head(5)

    col1, col2, col3 = st.columns(3)
    with col1:
        avg_score = filtered_df["curr_CompositeScore"].mean()
        st.markdown(display_card("Team Avg (Curr)", f"{avg_score:.2f}"), unsafe_allow_html=True)
    with col2:
        if not over.empty:
            player = over.iloc[0]
            name = player["display_name"] if "display_name" in player else player["Name"]
            delta = player["ScoreDelta"]
            icon = "📈" if delta > 0 else "📉"
            delta_color = "#2ecc71" if delta > 0 else "#e74c3c"
            st.markdown(display_card("Best Performer", f"{name} {delta:.2f}", icon=icon, color=delta_color), unsafe_allow_html=True)
    with col3:
        if not volatile.empty:
            player = volatile.iloc[0]
            name = player["display_name"] if "display_name" in player else player["Name"]
            delta = player["ScoreDelta"]
            vol = player["volatility"]
            direction = "↑" if delta > 0 else "↓"
            color_value = "#2ecc71" if delta > 0 else "#e74c3c"
            icon = "🟢" if delta > 0 else "🔴"
            st.markdown(display_card("Most Volatile", f"{name} {direction} ±{vol:.2f}", icon=icon, color=color_value), unsafe_allow_html=True)

    st.markdown("---")
    st.header("📈 Visual Breakdown")
    left, right = st.columns(2)
    with left:
        st.subheader("🧱 Position Strength")
        position_records = []
        for pos in ESPNS_POSITIONS:
            matched = filtered_df[filtered_df["norm_positions"].apply(lambda lst: match_espn_position(lst, pos))]
            if matched.empty:
                continue
            curr_avg = matched["curr_CompositeScore"].mean()
            proj_avg = matched["proj_CompositeScore"].mean()
            position_records.append({"Position": pos, "Type": "Current", "Avg Score": curr_avg})
            position_records.append({"Position": pos, "Type": "Projected", "Avg Score": proj_avg})
        pos_summary = pd.DataFrame(position_records)
        fig_pos = px.bar(
            pos_summary,
            x="Position",
            y="Avg Score",
            color="Type",
            barmode="group",
            text_auto=".2f",
            title="Projected vs Current Avg Score by Position"
        )
        fig_pos.update_layout(showlegend=True)
        st.plotly_chart(fig_pos, use_container_width=True)
    with right:
        st.subheader("📉 Player Score Delta")
        fig_delta = px.bar(
            filtered_df.sort_values("ScoreDelta", ascending=False),
            x="display_name" if "display_name" in filtered_df.columns else "Name",
            y="ScoreDelta",
            color="ScoreDelta",
            color_continuous_scale=["red", "white", "green"],
            title="Current vs Projected"
        )
        fig_delta.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_delta, use_container_width=True)

    st.markdown("---")
    st.header("🔍 Performance Tables")
    top_col1, top_col2 = st.columns(2)
    show_hitters = view_mode in ["All", "Hitter"]
    show_pitchers = view_mode in ["All", "Pitcher"]

    if show_hitters:
        st.markdown("#### 🟢 Hitter Over/Underachievers")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("⬆️ Overachievers")
            st.dataframe(stat_table(over, "Hitter"), use_container_width=True)
        with col2:
            st.subheader("⬇️ Underachievers")
            st.dataframe(stat_table(under, "Hitter"), use_container_width=True)
    if show_pitchers:
        st.markdown("#### 🔵 Pitcher Over/Underachievers")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("⬆️ Overachievers")
            st.dataframe(stat_table(over, "Pitcher"), use_container_width=True)
        with col2:
            st.subheader("⬇️ Underachievers")
            st.dataframe(stat_table(under, "Pitcher"), use_container_width=True)

    st.markdown("---")
    st.header("📋 Roster Breakdown")
    for group in ["Hitter", "Pitcher"]:
        group_df = filtered_df[filtered_df["PlayerGroup"] == group].copy()
        if group_df.empty:
            st.warning(f"No {group}s found on your roster.")
            continue
        st.subheader(f"{group} Roster ({len(group_df)})")
        if group == "Hitter":
            base_stats = ["CompositeScore", "AB", "wOBA", "wRC+", "ISO", "wBsR"]
            stat_labels = {
                "CompositeScore": "Score",
                "AB": "At Bats",
                "wOBA": "wOBA",
                "wRC+": "wRC+",
                "ISO": "ISO",
                "wBsR": "wBsR"
            }
        else:
            base_stats = ["CompositeScore", "IP", "FIP", "WHIP", "K-BB%", "SV"]
            stat_labels = {
                "CompositeScore": "Score",
                "IP": "IP",
                "FIP": "FIP",
                "WHIP": "WHIP",
                "K-BB%": "K-BB%",
                "SV": "Saves"
            }
        prefixes = ["proj", "curr"]
        display_df = group_df[["display_name"]].copy()
        for prefix in prefixes:
            prefix_label = "Proj" if prefix == "proj" else "Curr"
            for stat in base_stats:
                col_name = f"{prefix}_{stat}"
                if col_name in group_df.columns:
                    display_df[f"{prefix_label} {stat_labels[stat]}"] = group_df[col_name]
        sort_col = "Curr Score"
        if sort_col in display_df.columns:
            display_df.sort_values(by=sort_col, ascending=False, inplace=True)
        st.dataframe(display_df.rename(columns={"display_name": "Player"}), use_container_width=True)

def render_free_agent_suggestions(team_df, fa_df, full_df):
    st.header("🧠 Free Agent Suggestions")
    selected_category = st.radio("Select Player Type", options=["All", "Hitters", "Pitchers"], horizontal=True)
    only_upgrades = st.checkbox("Only Show Projected Upgrades", value=True)
    is_dark = st.get_option("theme.base") == "dark"
    card_bg_local = "#1e1e1e"
    card_fg_local = "#f5f5f5"

    suggestions = []
    def is_relevant_position(pos):
        if selected_category == "All":
            return True
        elif selected_category == "Hitters":
            return pos not in {"P"}
        elif selected_category == "Pitchers":
            return pos == "P"
        return False

    for espn_pos in ESPNS_POSITIONS:
        if not is_relevant_position(espn_pos):
            continue
        group = "Pitcher" if espn_pos == "P" else "Hitter"
        fa_pos = fa_df[fa_df["norm_positions"].apply(lambda lst: match_espn_position(lst, espn_pos))].sort_values(by="proj_CompositeScore", ascending=False)
        roster_pos = team_df[team_df["norm_positions"].apply(lambda lst: match_espn_position(lst, espn_pos))].sort_values(by="proj_CompositeScore")
        if not roster_pos.empty:
            for i in range(min(5, len(fa_pos), len(roster_pos))):
                suggestion = build_suggestion(espn_pos, group, fa_pos.iloc[i], roster_pos.iloc[i])
                if suggestion.get("Reason"):
                    suggestions.append(suggestion)
        else:
            for i in range(min(5, len(fa_pos))):
                suggestions.append(build_suggestion(espn_pos, group, fa_pos.iloc[i]))

    if not suggestions:
        st.info("No meaningful free agent suggestions found.")
    else:
        df_suggestions = pd.DataFrame(suggestions)
        if only_upgrades:
            df_suggestions = df_suggestions[df_suggestions["Score Delta (Projected)"] > 0]
        bins = [-float("inf"), 0.05, 0.25, 0.50, float("inf")]
        labels = ["Negligible", "Small", "Medium", "Big"]
        df_suggestions["Upgrade Tier"] = pd.cut(df_suggestions["Score Delta (Projected)"], bins=bins, labels=labels, right=False)
        tier_order = ["Big", "Medium", "Small", "Negligible"]
        tier_icons = {"Big": "🚀", "Medium": "📈", "Small": "🔧", "Negligible": "⚪"}
        st.markdown("#### Free Agent Suggestions")
        for tier in tier_order:
            tier_df = df_suggestions[df_suggestions["Upgrade Tier"] == tier].sort_values(by="Weighted Delta", ascending=False)
            if tier_df.empty:
                continue
            header = f"## {tier_icons[tier]} {tier} Upgrades"
            if tier == "Negligible":
                show_negligible = st.checkbox("⚪ Show Negligible Upgrades", value=False)
                if show_negligible:
                    st.markdown(header)
                    display_suggestions(tier_df, fa_df, team_df)
            else:
                st.markdown(header)
                display_suggestions(tier_df, fa_df, team_df)

def render_league_dashboard(df):
    st.markdown("# League Dashboard")
    is_dark = st.get_option("theme.base") == "dark"
    card_bg_local = "#1e1e1e" if is_dark else "#e0e0e0"
    card_text_local = "#f0f0f0" if is_dark else "#111111"
    df["norm_positions"] = df["position"].apply(expand_positions)
    valid_data = df[df["norm_positions"].apply(lambda positions: len(positions) > 0)]
    league_teams = sorted({
        team.strip() for team in valid_data["fantasy_team"].dropna().unique()
        if team.strip().lower() not in {"free agent", "fa"}
    })

    summary_records = []
    for team in league_teams:
        team_data = valid_data[valid_data["fantasy_team"] == team]
        for pos in ESPNS_POSITIONS:
            matching_players = team_data[team_data["norm_positions"].apply(lambda p_list: match_espn_position(p_list, pos))]
            if not matching_players.empty:
                summary_records.append({
                    "Team": team.title(),
                    "Position": pos,
                    "Avg Score": matching_players["curr_CompositeScore"].mean(),
                    "Player Count": matching_players.shape[0]
                })
    league_summary = pd.DataFrame(summary_records)
    st.markdown("<h3 style='text-align:center; color:#bbb;'>Team Overviews</h3>", unsafe_allow_html=True)
    team_cards = []
    for team in league_teams:
        team_mask = league_summary["Team"] == team.title()
        team_data = league_summary[team_mask]
        if team_data.empty:
            continue
        best_row = team_data.loc[team_data["Avg Score"].idxmax()]
        worst_row = team_data.loc[team_data["Avg Score"].idxmin()]
        overall_avg = team_data["Avg Score"].mean()
        team_cards.append({
            "name": team.title(),
            "avg": overall_avg,
            "best": best_row["Position"],
            "worst": worst_row["Position"]
        })
    for i in range(0, len(team_cards), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(team_cards):
                card = team_cards[i + j]
                with col:
                    st.markdown(
                        f"""
                        <div style="
                            background: {card_bg_local};
                            color: {card_text_local};
                            border-radius: 8px;
                            padding: 1rem;
                            margin: 0.5rem;
                            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                        ">
                            <h4 style="margin-bottom:0.3rem;">{card['name']}</h4>
                            <p style="margin:0;">Average Score: <strong>{card['avg']:.2f}</strong></p>
                            <p style="margin:0;">Best: {card['best']}<br>Worst: {card['worst']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
    st.markdown("<h3 style='text-align:center; color:#bbb;'>Positional Breakdown</h3>", unsafe_allow_html=True)
    selected_pos = st.selectbox("Select Position", ESPNS_POSITIONS, index=0)
    pos_summary = league_summary[league_summary["Position"] == selected_pos]
    if not pos_summary.empty:
        fig = px.bar(
            pos_summary,
            x="Team",
            y="Avg Score",
            text_auto=".2f",
            color="Team",
            title=f"Dominance at Position {selected_pos}",
        )
        fig.update_layout(
            xaxis_title="Team",
            yaxis_title="Average Score",
            template="plotly_dark" if is_dark else "plotly_white",
            margin=dict(l=40, r=40, t=40, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected position.")
    st.markdown("<h3 style='text-align:center; color:#bbb;'>League Leaderboard</h3>", unsafe_allow_html=True)
    leaderboard = league_summary.groupby("Team")["Avg Score"].mean().reset_index()
    leaderboard.sort_values("Avg Score", ascending=False, inplace=True)
    leaderboard["Rank"] = range(1, len(leaderboard) + 1)
    leaderboard = leaderboard[["Rank", "Team", "Avg Score"]]
    st.dataframe(leaderboard.style.format({"Avg Score": "{:.2f}"}), use_container_width=True)

def render_mlb_overview(df):
    st.markdown("## 🌍 MLB Player Overview")
    if "norm_positions" not in df.columns:
        df["norm_positions"] = df["position"].apply(expand_positions)
    player_group = st.radio("Show players:", options=["All Players", "Free Agents", "Rostered Players"], horizontal=True)
    df_filtered = df.copy()
    if player_group == "Free Agents":
        df_filtered = df_filtered[df_filtered["fantasy_team"].str.lower().isin(["free agent", "fa"])]
    elif player_group == "Rostered Players":
        df_filtered = df_filtered[~df_filtered["fantasy_team"].str.lower().isin(["free agent", "fa"])]
    pos_filter = st.selectbox("Filter by Position", ["All"] + ESPNS_POSITIONS)
    all_players = df_filtered.copy()
    if pos_filter != "All":
        all_players = all_players[all_players["norm_positions"].apply(lambda lst: match_espn_position(lst, pos_filter))]
    st.subheader("🧾 All MLB Players")
    stat_cols = ["display_name", "Team", "fantasy_team", "position", "proj_CompositeScore", "curr_CompositeScore"]
    display_table = all_players[stat_cols].rename(columns={"display_name": "Player", "fantasy_team": "Fantasy Team"})
    st.caption(f"Showing {len(all_players)} players" + (f" at {pos_filter}" if pos_filter != "All" else ""))
    st.dataframe(display_table.sort_values("curr_CompositeScore", ascending=False), use_container_width=True)
    hitter_stats = [
        "proj_AB", "proj_wOBA", "proj_wRC+", "proj_ISO", "proj_wBsR",
        "curr_AB", "curr_wOBA", "curr_wRC+", "curr_ISO", "curr_wBsR"
    ]
    pitcher_stats = [
        "proj_IP", "proj_FIP", "proj_WHIP", "proj_K-BB%", "proj_SV",
        "curr_IP", "curr_FIP", "curr_WHIP", "curr_K-BB%", "curr_SV"
    ]
    st.subheader("🏆 Best Players by Position")
    for pos in ESPNS_POSITIONS:
        with st.expander(f"Best {pos} Players", expanded=False):
            pos_players = df_filtered[df_filtered["norm_positions"].apply(lambda lst: match_espn_position(lst, pos))]
            if not pos_players.empty:
                pos_players = pos_players.copy()
                sorted_players = pos_players.sort_values("proj_CompositeScore", ascending=False)
                extra_stats = pitcher_stats if pos == "P" else hitter_stats
                display_cols = ["display_name", "Team", "fantasy_team", "curr_CompositeScore", "proj_CompositeScore"] + extra_stats
                display_cols = [col for col in display_cols if col in sorted_players.columns]
                st.dataframe(sorted_players[display_cols].rename(columns={"display_name": "Player"}), use_container_width=True)
            else:
                st.info(f"No players available for {pos}.")
    st.subheader("⭐ Best Multi-Position Players")
    multi_pos_players = df_filtered[df_filtered["norm_positions"].apply(lambda lst: len(lst) > 1)]
    if not multi_pos_players.empty:
        mean_multi = multi_pos_players["curr_CompositeScore"].mean()
        std_multi = multi_pos_players["curr_CompositeScore"].std() or 1
        multi_pos_players = multi_pos_players.copy()
        multi_pos_players["Relative Score"] = (multi_pos_players["curr_CompositeScore"] - mean_multi) / std_multi
        top_multi = multi_pos_players.sort_values("curr_CompositeScore", ascending=False)
        all_extra_stats = hitter_stats + pitcher_stats
        display_cols = ["display_name", "Team", "fantasy_team", "curr_CompositeScore", "proj_CompositeScore", "Relative Score", "norm_positions"] + all_extra_stats
        display_cols = [col for col in dict.fromkeys(display_cols).keys() if col in top_multi.columns]
        st.dataframe(top_multi[display_cols].rename(columns={"display_name": "Player", "fantasy_team": "Fantasy Team"}), use_container_width=True)
    else:
        st.info("No multi-position players found.")

# =============================================================================
# Main Application Logic
# =============================================================================
def main():
    run_scraper()

    csv_path = get_newest_csv()
    if not csv_path:
        st.error("No ranked data CSV file found.")
        st.stop()

    df = pd.read_csv(csv_path, low_memory=False)
    df["fantasy_team"] = df["fantasy_team"].astype(str).str.lower()
    df["norm_positions"] = df["position"].apply(expand_positions)
    df = df[df["norm_positions"].apply(len) > 0]

    # Define a mapping for cleaned injury status text.
    injury_mapping = {
        "ACTIVE": "",
        "TEN_DAY_DL": "10IL",
        "FIFTEEN_DAY_DL": "15IL",
        "SIXTY_DAY_DL": "60IL",
        "DAY_TO_DAY": "DTD",
        "PATERNITY": "PAT",
        "OUT": "O",
        "SUSPENSION": "SUS"
    }

    # Compute a display_name column that shows the player's name and, if injured, an indicator.
    if "injury_status" in df.columns:
        df["display_name"] = df["Name"] + df["injury_status"].apply(lambda x: "" if x == "ACTIVE" else f" 🚑 [{injury_mapping.get(x, x)}]")
    else:
        df["display_name"] = df["Name"]

    # Global filter: allow players to be filtered out if injured.
    hide_injured = st.checkbox("Hide Injured Players", value=False)
    if hide_injured and "injury_status" in df.columns:
        df = df[df["injury_status"] == "ACTIVE"]

    valid_teams = df["fantasy_team"].dropna().unique()
    valid_teams = [team for team in valid_teams if team.lower() not in {"free agent", "fa"}]
    valid_teams = sorted(valid_teams)
    if DEFAULT_TEAM in valid_teams:
        valid_teams.remove(DEFAULT_TEAM)
        valid_teams.insert(0, DEFAULT_TEAM)
    selected_team = st.selectbox("Select Team", valid_teams, index=0)
    team_df = df[df["fantasy_team"] == selected_team].copy()
    fa_df = df[df["fantasy_team"].isin(["free agent", "fa"])].copy()

    mode = st.radio("Select Mode", ["Team Dashboard", "Free Agent Suggestions", "League Dashboard", "MLB Overview"])
    if mode == "Team Dashboard":
        render_team_dashboard(df, team_df, csv_path)
    elif mode == "Free Agent Suggestions":
        render_free_agent_suggestions(team_df, fa_df, df)
    elif mode == "League Dashboard":
        render_league_dashboard(df)
    elif mode == "MLB Overview":
        render_mlb_overview(df)

main()

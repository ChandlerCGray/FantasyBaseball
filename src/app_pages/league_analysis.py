"""
League Analysis - Compare all teams in the league
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config import COLORS, POSITIONS
from data_utils import can_play_position

def show_league_analysis(df, selected_team):
    """Show league-wide analysis and team comparisons"""
    st.markdown("## League Analysis")
    st.markdown("**Strategy Guide:** See how your team stacks up against the competition. Identify league-wide trends and competitive advantages.")
    
    # Get all teams (excluding free agents)
    teams = sorted([t for t in df["fantasy_team"].dropna().unique() 
                   if t.lower() not in ["free agent", "fa"]])
    
    if len(teams) < 2:
        st.info("Need at least 2 teams for league analysis.")
        return
    
    # Team strength overview
    st.markdown("### Team Strength Rankings")
    
    team_stats = []
    for team in teams:
        team_df = df[df["fantasy_team"] == team].copy()
        team_df = team_df[team_df["has_valid_position"]]
        
        if not team_df.empty:
            avg_proj = team_df["proj_CompositeScore"].mean()
            avg_curr = team_df["curr_CompositeScore"].mean()
            avg_delta = team_df["ScoreDelta"].mean()
            team_size = len(team_df)
            
            team_stats.append({
                "Team": team,
                "Avg_Projected": avg_proj,
                "Avg_Current": avg_curr,
                "Avg_Delta": avg_delta,
                "Team_Size": team_size,
                "Is_Your_Team": team == selected_team
            })
    
    if team_stats:
        team_df_stats = pd.DataFrame(team_stats)
        team_df_stats = team_df_stats.sort_values("Avg_Projected", ascending=False)
        
        # Team rankings
        st.markdown("#### Team Rankings by Projected Score")
        
        for i, (_, team_data) in enumerate(team_df_stats.iterrows()):
            from ui_components import get_rainbow_tile_class
            
            rank_emoji = ["🥇", "🥈", "🥉"] + [" "] * 10
            emoji = rank_emoji[min(i, len(rank_emoji)-1)]
            
            # Use rainbow tiles with special highlighting for user's team
            if team_data["Is_Your_Team"]:
                rainbow_class = "tile-rainbow-2"  # Green for user's team
                team_indicator = " (Your Team)"
                text_color = COLORS['dark']
            else:
                rainbow_class = get_rainbow_tile_class(i + 3)  # Offset to avoid green
                team_indicator = ""
                text_color = COLORS['dark']
            
            st.markdown(f"""
            <div class="{rainbow_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="font-size: 1.2rem; font-weight: 700; margin-bottom: 0.5rem; color: {text_color};">
                            {emoji} {i+1}. {team_data['Team']}{team_indicator}
                        </div>
                        <div style="display: flex; gap: 1rem; flex-wrap: wrap; font-size: 0.9rem; color: {COLORS['muted']};">
                            <span style="font-weight: 600;">Proj: {team_data['Avg_Projected']:.2f}</span>
                            <span style="font-weight: 600;">Curr: {team_data['Avg_Current']:.2f}</span>
                            <span style="font-weight: 600;">Δ: {team_data['Avg_Delta']:+.2f}</span>
                            <span style="font-weight: 600;">Players: {team_data['Team_Size']}</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Team comparison charts
        st.markdown("### ↗ Team Comparison Charts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Projected vs Current performance
            fig = px.scatter(
                team_df_stats,
                x="Avg_Projected",
                y="Avg_Current",
                size="Team_Size",
                color="Avg_Delta",
                hover_name="Team",
                title="Projected vs Current Performance",
                labels={
                    "Avg_Projected": "Average Projected Score",
                    "Avg_Current": "Average Current Score",
                    "Avg_Delta": "Performance Delta"
                },
                color_continuous_scale="RdYlGn"
            )
            
            # Add diagonal line for reference
            min_val = min(team_df_stats["Avg_Projected"].min(), team_df_stats["Avg_Current"].min())
            max_val = max(team_df_stats["Avg_Projected"].max(), team_df_stats["Avg_Current"].max())
            fig.add_shape(
                type="line",
                x0=min_val, y0=min_val,
                x1=max_val, y1=max_val,
                line=dict(dash="dash", color="gray"),
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Team performance bar chart
            fig = px.bar(
                team_df_stats,
                x="Team",
                y=["Avg_Projected", "Avg_Current"],
                title="Team Performance Comparison",
                labels={"value": "Average Score", "variable": "Score Type"},
                color_discrete_sequence=[COLORS["primary"], COLORS["secondary"]]
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
    
    # Position strength analysis across league
    st.markdown("###  Position Strength Across League")
    
    position_league_data = []
    for position in POSITIONS:
        for team in teams:
            team_df = df[df["fantasy_team"] == team].copy()
            team_df = team_df[team_df["has_valid_position"]]
            
            pos_players = team_df[team_df["norm_positions"].apply(
                lambda x: can_play_position(x, position)
            )]
            
            if not pos_players.empty:
                avg_score = pos_players["proj_CompositeScore"].mean()
                position_league_data.append({
                    "Team": team,
                    "Position": position,
                    "Avg_Score": avg_score,
                    "Player_Count": len(pos_players),
                    "Is_Your_Team": team == selected_team
                })
    
    if position_league_data:
        pos_league_df = pd.DataFrame(position_league_data)
        
        # Heatmap of team strengths by position
        pivot_df = pos_league_df.pivot(index="Team", columns="Position", values="Avg_Score")
        
        fig = px.imshow(
            pivot_df.values,
            x=pivot_df.columns,
            y=pivot_df.index,
            color_continuous_scale="RdYlGn",
            title="Team Strength Heatmap by Position",
            labels={"color": "Avg Score"}
        )
        
        # Highlight your team
        if selected_team in pivot_df.index:
            your_team_idx = list(pivot_df.index).index(selected_team)
            fig.add_shape(
                type="rect",
                x0=-0.5, y0=your_team_idx-0.5,
                x1=len(pivot_df.columns)-0.5, y1=your_team_idx+0.5,
                line=dict(color=COLORS["primary"], width=3),
                fillcolor="rgba(0,0,0,0)"
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Position rankings
        st.markdown("### 🏅 Position Rankings")
        
        selected_position = st.selectbox(
            "Select Position to Analyze",
            POSITIONS,
            help="See how teams rank at each position"
        )
        
        pos_data = pos_league_df[pos_league_df["Position"] == selected_position].copy()
        pos_data = pos_data.sort_values("Avg_Score", ascending=False)
        
        if not pos_data.empty:
            st.markdown(f"#### {selected_position} Rankings")
            
            cols = st.columns(min(4, len(pos_data)))
            for i, (_, team_data) in enumerate(pos_data.iterrows()):
                with cols[i % len(cols)]:
                    from ui_components import get_rainbow_tile_class
                    
                    rank_emoji = ["🥇", "🥈", "🥉"] + ["-"] * 10
                    emoji = rank_emoji[min(i, len(rank_emoji)-1)]
                    
                    # Use rainbow tiles with special highlighting for user's team
                    if team_data["Is_Your_Team"]:
                        rainbow_class = "tile-rainbow-2"  # Green for user's team
                    else:
                        rainbow_class = get_rainbow_tile_class(i + 3)  # Offset to avoid green
                    
                    st.markdown(f"""
                    <div class="{rainbow_class}" style="text-align: center;">
                        <div style="font-size: 1.5rem; margin-bottom: 0.75rem; color: {COLORS['dark']};">
                            {emoji}
                        </div>
                        <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem; color: {COLORS['dark']};">
                            {team_data['Team']}
                        </div>
                        <div style="font-size: 0.9rem; margin-bottom: 0.5rem; color: {COLORS['muted']}; font-weight: 600;">
                            Score: {team_data['Avg_Score']:.2f}
                        </div>
                        <div style="font-size: 0.8rem; color: {COLORS['muted']}; font-weight: 500;">
                            {team_data['Player_Count']} players
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # League trends
    st.markdown("### 📈 League Trends")
    
    # Overall league performance distribution
    league_players = df[df["fantasy_team"].isin(teams)].copy()
    league_players = league_players[league_players["has_valid_position"]]
    
    # Add diagnostic information
    if not league_players.empty:
        hitters = league_players[~league_players["norm_positions"].apply(lambda x: "P" in str(x) if x else False)]
        pitchers = league_players[league_players["norm_positions"].apply(lambda x: "P" in str(x) if x else False)]
        
        st.markdown("#### Distribution Analysis")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Players", len(league_players))
        with col2:
            st.metric("Hitters", len(hitters))
        with col3:
            st.metric("Pitchers", len(pitchers))
        with col4:
            avg_score = league_players["proj_CompositeScore"].mean()
            st.metric("Avg Score", f"{avg_score:.2f}")
        
        st.markdown("**Why the distribution looks wonky:** The bimodal (two-peak) pattern likely shows distinct player tiers - starters vs bench players, or different position groups with different scoring scales.")
        
        # Show separate distributions to diagnose the issue
        st.markdown("#### Detailed Distribution Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Combined distribution (what you saw before)
            fig = px.histogram(
                league_players,
                x="proj_CompositeScore",
                nbins=30,
                title="Combined League Score Distribution",
                labels={"proj_CompositeScore": "Projected Score", "count": "Number of Players"},
                color_discrete_sequence=[COLORS["primary"]]
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Performance vs projection
            fig = px.histogram(
                league_players,
                x="ScoreDelta",
                nbins=30,
                title="League Performance vs Projections",
                labels={"ScoreDelta": "Performance Delta", "count": "Number of Players"},
                color_discrete_sequence=[COLORS["secondary"]]
            )
            fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Expected")
            st.plotly_chart(fig, use_container_width=True)
        
        # Separate hitter vs pitcher distributions to explain the bimodal pattern
        if len(hitters) > 0 and len(pitchers) > 0:
            st.markdown("#### Hitters vs Pitchers Distribution")
            st.markdown("**This should explain the wonky distribution!** Hitters and pitchers often have different scoring scales.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.histogram(
                    hitters,
                    x="proj_CompositeScore",
                    nbins=20,
                    title="Hitters Only - Score Distribution",
                    labels={"proj_CompositeScore": "Projected Score", "count": "Number of Hitters"},
                    color_discrete_sequence=[COLORS["success"]]
                )
                hitter_avg = hitters["proj_CompositeScore"].mean()
                fig.add_vline(x=hitter_avg, line_dash="dash", line_color="green", 
                             annotation_text=f"Avg: {hitter_avg:.2f}")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.histogram(
                    pitchers,
                    x="proj_CompositeScore",
                    nbins=20,
                    title="Pitchers Only - Score Distribution",
                    labels={"proj_CompositeScore": "Projected Score", "count": "Number of Pitchers"},
                    color_discrete_sequence=[COLORS["warning"]]
                )
                pitcher_avg = pitchers["proj_CompositeScore"].mean()
                fig.add_vline(x=pitcher_avg, line_dash="dash", line_color="orange", 
                             annotation_text=f"Avg: {pitcher_avg:.2f}")
                st.plotly_chart(fig, use_container_width=True)
            
            # Summary explanation
            hitter_range = f"{hitters['proj_CompositeScore'].min():.2f} to {hitters['proj_CompositeScore'].max():.2f}"
            pitcher_range = f"{pitchers['proj_CompositeScore'].min():.2f} to {pitchers['proj_CompositeScore'].max():.2f}"
            
            st.markdown(f"""
            **Distribution Explanation:**
            - **Hitters**: Average {hitter_avg:.2f}, Range: {hitter_range}
            - **Pitchers**: Average {pitcher_avg:.2f}, Range: {pitcher_range}
            
            **🔍 Why it looks bimodal:** {'Hitters and pitchers have different scoring scales, creating two distinct peaks!' if abs(hitter_avg - pitcher_avg) > 0.5 else 'The scoring scales are similar, so the bimodal pattern might be due to starter vs bench player tiers.'}
            """)
        
        # Show score ranges by position to further diagnose
        st.markdown("#### Score Ranges by Position")
        position_stats = []
        for pos in POSITIONS:
            pos_players = league_players[league_players["norm_positions"].apply(
                lambda x: can_play_position(x, pos) if x else False
            )]
            if not pos_players.empty:
                position_stats.append({
                    "Position": pos,
                    "Count": len(pos_players),
                    "Avg_Score": pos_players["proj_CompositeScore"].mean(),
                    "Min_Score": pos_players["proj_CompositeScore"].min(),
                    "Max_Score": pos_players["proj_CompositeScore"].max()
                })
        
        if position_stats:
            pos_df = pd.DataFrame(position_stats)
            st.dataframe(pos_df.round(2), use_container_width=True, hide_index=True)
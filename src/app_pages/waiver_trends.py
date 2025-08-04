"""
Waiver Wire Trends - Track player performance trends
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

def show_waiver_trends(fa_df):
    """Show trending players and hot pickups"""
    st.markdown("## Waiver Wire Trends")
    st.markdown("*Identify hot pickups and trending players*")
    
    if fa_df.empty:
        st.info("No free agent data available.")
        return
    
    # Hot performers (positive score delta)
    st.markdown("### Hot Performers")
    st.markdown("*Players outperforming their projections*")
    
    hot_performers = fa_df[fa_df["ScoreDelta"] > 0].sort_values("ScoreDelta", ascending=False).head(10)
    
    if not hot_performers.empty:
        cols = st.columns(2)
        for i, (_, player) in enumerate(hot_performers.iterrows()):
            with cols[i % 2]:
                pos = player["norm_positions"][0] if player["norm_positions"] else "Unknown"
                delta = player["ScoreDelta"]
                
                st.markdown(f"""
                <div class="player-card" style="border-left-color: {COLORS['success']};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <div class="player-name" style="color: {COLORS['success']};">
                                {i+1}. {player['display_name']}
                            </div>
                            <div class="player-stats">
                                <span class="stat-badge pos-{pos}" style="color: white;">{pos}</span>
                                <span class="stat-badge" style="background: {COLORS['success']}; color: white;">
                                    +{delta:.2f}
                                </span>
                                <span class="stat-badge">Proj: {player['proj_CompositeScore']:.2f}</span>
                                <span class="stat-badge">Team: {player.get('Team', 'Unknown')}</span>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.5rem;">↗</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No players are currently outperforming their projections.")
    
    # Cold performers (negative score delta)
    st.markdown("### Cold Performers")
    st.markdown("*Players underperforming their projections*")
    
    cold_performers = fa_df[fa_df["ScoreDelta"] < 0].sort_values("ScoreDelta").head(8)
    
    if not cold_performers.empty:
        cols = st.columns(2)
        for i, (_, player) in enumerate(cold_performers.iterrows()):
            with cols[i % 2]:
                pos = player["norm_positions"][0] if player["norm_positions"] else "Unknown"
                delta = player["ScoreDelta"]
                
                st.markdown(f"""
                <div class="player-card" style="border-left-color: {COLORS['info']};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <div class="player-name" style="color: {COLORS['info']};">
                                {i+1}. {player['display_name']}
                            </div>
                            <div class="player-stats">
                                <span class="stat-badge pos-{pos}" style="color: white;">{pos}</span>
                                <span class="stat-badge" style="background: {COLORS['info']}; color: white;">
                                    {delta:.2f}
                                </span>
                                <span class="stat-badge">Proj: {player['proj_CompositeScore']:.2f}</span>
                                <span class="stat-badge">Team: {player.get('Team', 'Unknown')}</span>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.5rem;">↘</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No players are currently underperforming their projections.")
    
    # Performance distribution chart
    st.markdown("### Performance Distribution")
    
    # Create performance buckets
    fa_df_clean = fa_df.dropna(subset=["ScoreDelta"])
    
    if not fa_df_clean.empty:
        # Histogram of score deltas
        fig = px.histogram(
            fa_df_clean,
            x="ScoreDelta",
            nbins=30,
            title="Distribution of Player Performance vs Projections",
            labels={"ScoreDelta": "Performance Delta (Current - Projected)", "count": "Number of Players"},
            color_discrete_sequence=[COLORS["primary"]]
        )
        
        # Add vertical line at zero
        fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Expected Performance")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Position-based performance
        st.markdown("### Performance by Position")
        
        position_performance = []
        for position in POSITIONS:
            pos_players = fa_df_clean[fa_df_clean["norm_positions"].apply(
                lambda x: can_play_position(x, position)
            )]
            
            if not pos_players.empty:
                avg_delta = pos_players["ScoreDelta"].mean()
                count = len(pos_players)
                position_performance.append({
                    "Position": position,
                    "Avg_Delta": avg_delta,
                    "Count": count,
                    "Status": "Hot" if avg_delta > 0.1 else "Cold" if avg_delta < -0.1 else "Neutral"
                })
        
        if position_performance:
            pos_df = pd.DataFrame(position_performance)
            
            # Bar chart of position performance
            fig = px.bar(
                pos_df,
                x="Position",
                y="Avg_Delta",
                color="Status",
                title="Average Performance by Position",
                labels={"Avg_Delta": "Average Performance Delta"},
                color_discrete_map={
                    "Hot": COLORS["success"],
                    "Cold": COLORS["info"],
                    "Neutral": COLORS["muted"]
                }
            )
            
            fig.add_hline(y=0, line_dash="dash", line_color="black", annotation_text="Expected")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Position performance summary
            cols = st.columns(len(POSITIONS))
            for i, pos_data in enumerate(position_performance):
                with cols[i % len(cols)]:
                    pos = pos_data["Position"]
                    avg_delta = pos_data["Avg_Delta"]
                    status = pos_data["Status"]
                    
                    # Color based on performance
                    if status == "Hot":
                        tile_color = "background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);"
                        icon = "↗"
                    elif status == "Cold":
                        tile_color = "background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%);"
                        icon = "↘"
                    else:
                        tile_color = "background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);"
                        icon = "-"
                    
                    st.markdown(f"""
                    <div class="tile" style="{tile_color} text-align: center;">
                        <div style="margin-bottom: 0.5rem;">
                            <span class="stat-badge pos-{pos}" style="color: white; font-size: 1rem; padding: 0.5rem 1rem;">
                                {pos}
                            </span>
                        </div>
                        <div style="font-size: 1.5rem; margin-bottom: 0.25rem;">
                            {icon}
                        </div>
                        <div style="font-size: 1rem; font-weight: 600; margin-bottom: 0.25rem; color: {COLORS['dark']};">
                            {avg_delta:+.2f}
                        </div>
                        <div style="font-size: 0.8rem; opacity: 0.8;">
                            {pos_data['Count']} players
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
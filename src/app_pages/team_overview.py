"""
Team Overview page
"""

import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import POSITIONS, COLORS
from data_utils import can_play_position
from ui_components import create_position_strength_tile, create_rainbow_player_tile, get_rainbow_tile_class, create_expandable_player_tile

def show_team_overview(team_df, fa_df):
    """Show team overview and analysis"""
    st.markdown("## Team Analysis & Insights")
    st.markdown("**Strategy Guide:** Identify your team's strengths to leverage in trades, and weaknesses to address via waivers.")
    
    if team_df.empty:
        st.info("No team data available.")
        return
    
    # Team performance overview
    st.markdown("### Performance Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Best performers
        best_performers = team_df.sort_values("proj_CompositeScore", ascending=False).head(5)
        st.markdown("#### Top Performers")
        
        for i, (_, player) in enumerate(best_performers.iterrows()):
            # Use the rainbow_player_tile function which now uses expandable functionality
            create_rainbow_player_tile(player, i, show_rank=True)
    
    with col2:
        # Position distribution
        st.markdown("#### Position Distribution")
        
        position_counts = {}
        for _, player in team_df.iterrows():
            for pos in player['norm_positions']:
                position_counts[pos] = position_counts.get(pos, 0) + 1
        
        pos_index = 0
        for pos in POSITIONS:
            count = position_counts.get(pos, 0)
            if count > 0:
                rainbow_class = get_rainbow_tile_class(pos_index + 10)  # Offset for variety
                st.markdown(f"""
                <div class="{rainbow_class}" style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <span class="stat-badge pos-{pos}" style="color: white; font-weight: 700;">{pos}</span>
                        <span style="font-weight: 600; color: {COLORS['dark']};">Players</span>
                    </div>
                    <div style="font-weight: 800; font-size: 1.2rem; color: {COLORS['dark']};">{count}</div>
                </div>
                """, unsafe_allow_html=True)
                pos_index += 1
    
    # Team strength analysis
    st.markdown("### Position Strength Analysis")
    st.markdown("**Action Items:** Focus on 'Weak' positions for upgrades. Use 'Strong' positions as trade assets.")
    
    position_data = []
    for position in POSITIONS:
        pos_team = team_df[team_df["norm_positions"].apply(
            lambda x: can_play_position(x, position)
        )]
        pos_fa = fa_df[fa_df["norm_positions"].apply(
            lambda x: can_play_position(x, position)
        )]
        
        if not pos_team.empty:
            team_avg = pos_team["proj_CompositeScore"].mean()
            team_best = pos_team["proj_CompositeScore"].max()
            fa_best = pos_fa["proj_CompositeScore"].max() if not pos_fa.empty else 0
            upgrade_potential = fa_best - team_avg if not pos_fa.empty else 0
            
            position_data.append({
                "Position": position,
                "Team_Avg": team_avg,
                "Best_FA": fa_best,
                "Upgrade": upgrade_potential,
                "Strength": "Strong" if team_avg > 1.0 else "Average" if team_avg > 0 else "Weak"
            })
    
    if position_data:
        # Display position strengths in a grid
        cols = st.columns(4)
        for i, data in enumerate(position_data):
            with cols[i % 4]:
                pos = data["Position"]
                strength = data["Strength"]
                team_avg = data["Team_Avg"]
                upgrade_potential = data["Upgrade"]
                
                st.markdown(
                    create_position_strength_tile(pos, strength, team_avg, upgrade_potential),
                    unsafe_allow_html=True
                )
"""
Drop Candidates page
"""

import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import POSITIONS, COLORS
from data_utils import can_play_position
from ui_components import create_player_card, create_rainbow_player_tile, get_rainbow_tile_class, create_expandable_player_tile

def show_drop_candidates(team_df):
    """Show worst players on team (drop candidates)"""
    st.markdown("## Drop Candidates")
    st.markdown("**Action Required:** These are your weakest players. Consider dropping them for better free agents. Lower scores = higher drop priority.")
    
    if team_df.empty:
        st.info("No players found on your team.")
        return
    
    # Overall worst performers
    st.markdown("### Lowest Projected Scores")
    worst_overall = team_df.sort_values("proj_CompositeScore").head(8)
    
    # Display in beautiful rainbow tiles
    cols = st.columns(2)
    for i, (_, player) in enumerate(worst_overall.iterrows()):
        with cols[i % 2]:
            # Use the rainbow_player_tile function which now uses expandable functionality
            create_rainbow_player_tile(player, i, show_rank=True)
    
    # Biggest underperformers
    st.markdown("### Biggest Underperformers")
    st.markdown("*Players performing worse than projected*")
    
    underperformers = team_df.sort_values("ScoreDelta").head(6)
    
    for i, (_, player) in enumerate(underperformers.iterrows()):
        # Use the rainbow_player_tile function which now uses expandable functionality
        create_rainbow_player_tile(player, i + 8, show_rank=True)
    
    # Worst by position
    st.markdown("### Weakest at Each Position")
    
    position_data = []
    for position in POSITIONS:
        pos_players = team_df[team_df["norm_positions"].apply(
            lambda x: can_play_position(x, position)
        )].copy()
        
        if not pos_players.empty:
            worst_at_pos = pos_players.sort_values("proj_CompositeScore").iloc[0]
            score = worst_at_pos['proj_CompositeScore']
            
            position_data.append({
                'position': position,
                'player': worst_at_pos,
                'score': score
            })
    
    # Display position weaknesses in beautiful rainbow grid
    if position_data:
        cols = st.columns(4)
        for i, data in enumerate(position_data):
            with cols[i % 4]:
                rainbow_class = get_rainbow_tile_class(i + 16)  # Offset to get different colors
                pos = data['position']
                player = data['player']
                score = data['score']
                
                # Use the expandable player tile for position weaknesses
                create_expandable_player_tile(
                    player, 
                    i + 16, 
                    f"pos_weakness_{pos}", 
                    show_rank=False
                )
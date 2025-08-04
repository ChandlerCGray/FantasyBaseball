"""
Best Free Agents page
"""

import streamlit as st
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import POSITIONS, COLORS
from data_utils import can_play_position
from ui_components import create_top_player_tile, create_rainbow_player_tile, create_expandable_player_tile

def show_best_free_agents(fa_df):
    """Show best available free agents by position"""
    st.markdown("## Best Available Free Agents")
    st.markdown("**How to Use:** Find players to target for your waiver claims or trades. Higher projected scores = better fantasy value.")
    
    # Position selector with improved styling
    st.markdown("### Select Positions to View")
    selected_positions = st.multiselect(
        "Choose positions",
        POSITIONS,
        default=POSITIONS,
        help="Select which positions you want to see free agents for"
    )
    
    if not selected_positions:
        st.info("Please select at least one position to view free agents.")
        return
    
    for position in selected_positions:
        pos_fa = fa_df[fa_df["norm_positions"].apply(
            lambda x: can_play_position(x, position)
        )].copy()
        
        if pos_fa.empty:
            continue
        
        # Sort by projected composite score
        pos_fa = pos_fa.sort_values("proj_CompositeScore", ascending=False).head(10)
        
        # Position header with colored badge
        st.markdown(f"""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="display: inline-flex; align-items: center; gap: 0.5rem;">
                <span class="stat-badge pos-{position}" style="color: white; padding: 0.5rem 1rem; font-size: 1rem;">
                    {position}
                </span>
                Top Available Players
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Top 3 players in beautiful rainbow tiles
        if len(pos_fa) >= 3:
            col1, col2, col3 = st.columns(3)
            ranks = ["1st", "2nd", "3rd"]
            
            for i, (col, (_, player)) in enumerate(zip([col1, col2, col3], pos_fa.head(3).iterrows())):
                with col:
                    from ui_components import get_rainbow_tile_class
                    import pandas as pd
                    
                    rainbow_class = get_rainbow_tile_class(i)
                    delta_str = f"Δ {player['ScoreDelta']:.2f}" if pd.notna(player['ScoreDelta']) else "No Δ"
                    delta_icon = "↗" if pd.notna(player['ScoreDelta']) and player['ScoreDelta'] > 0 else "↘"
                    
                    st.markdown(f"""
                    <div class="{rainbow_class}">
                        <div style="text-align: center;">
                            <div style="font-size: 2rem; margin-bottom: 0.75rem; color: {COLORS['dark']};">{ranks[i]}</div>
                            <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem; color: {COLORS['dark']};">
                                {player['display_name']}
                            </div>
                            <div style="margin-bottom: 0.75rem;">
                                <span class="stat-badge pos-{position}" style="color: white; font-weight: 700;">
                                    {position}
                                </span>
                            </div>
                            <div style="font-size: 0.9rem; color: {COLORS['muted']}; margin-bottom: 0.75rem;">
                                {player.get('Team', 'Unknown')}
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="text-align: left;">
                                    <div style="font-size: 0.8rem; color: {COLORS['muted']}; font-weight: 600; text-transform: uppercase;">
                                        Proj Score
                                    </div>
                                    <div style="font-size: 1.3rem; font-weight: 800; color: {COLORS['dark']};">
                                        {player['proj_CompositeScore']:.2f}
                                    </div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 0.8rem; color: {COLORS['muted']}; font-weight: 600; text-transform: uppercase;">Performance</div>
                                    <div style="font-size: 1rem; font-weight: 700; color: {COLORS['dark']};">{delta_icon} {delta_str}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Remaining players in a clean list
        if len(pos_fa) > 3:
            st.markdown(f"""
            <div style="margin: 2rem 0 1rem 0;">
                <h4 style="color: #FFFFFF; font-weight: 600; font-size: 1.2rem;">Complete Rankings</h4>
            </div>
            """, unsafe_allow_html=True)
            
            for idx, (_, player) in enumerate(pos_fa.iloc[3:].iterrows(), 4):
                # Use expandable player tiles - numbering continues from 4+
                # The rainbow_player_tile function now uses expandable functionality
                create_rainbow_player_tile(player, idx - 4, show_rank=True, rank_number=idx)
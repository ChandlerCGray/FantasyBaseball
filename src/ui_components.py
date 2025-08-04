"""
Reusable UI components for the Fantasy Baseball App
"""

import streamlit as st
from config import COLORS

def format_stat_value(value):
    """Format a stat value for display"""
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)

def get_rainbow_tile_class(index):
    """Get a rainbow tile class based on index for beautiful muted colors"""
    rainbow_classes = [
        "tile-rainbow-1",  # Sky blue
        "tile-rainbow-2",  # Green
        "tile-rainbow-3",  # Yellow
        "tile-rainbow-4",  # Red
        "tile-rainbow-5",  # Purple
        "tile-rainbow-6",  # Orange
        "tile-rainbow-7",  # Emerald
        "tile-rainbow-8",  # Slate
    ]
    return rainbow_classes[index % len(rainbow_classes)]

def create_metric_tile(title, value, subtitle="", tile_class="metric-tile", color=None):
    """Create a beautiful metric tile with improved spacing and contrast"""
    if color is None:
        color = COLORS['primary']
    
    # Ensure values are properly formatted
    if isinstance(value, (int, float)):
        if isinstance(value, float):
            formatted_value = f"{value:.2f}" if value < 100 else f"{value:,.0f}"
        else:
            formatted_value = f"{value:,}"
    else:
        formatted_value = str(value)
    
    return f"""
    <div class="{tile_class}">
        <div style="text-align: center;">
            <div style="font-size: 2.5rem; font-weight: 700; color: {color}; line-height: 1; margin-bottom: 0.5rem;">
                {formatted_value}
            </div>
            <div style="font-size: 0.875rem; font-weight: 600; color: {COLORS['dark']}; text-transform: uppercase; letter-spacing: 0.5px;">
                {title}
            </div>
            {f'<div style="font-size: 0.75rem; color: {COLORS["muted"]}; margin-top: 0.25rem;">{subtitle}</div>' if subtitle else ''}
        </div>
    </div>
    """

def create_player_card(player, position="", border_color=None, show_warning=False):
    """Create a player card component with improved spacing and contrast"""
    if border_color is None:
        border_color = COLORS['primary']
    
    warning_icon = "!" if show_warning else "★"
    
    return f"""
    <div class="player-card" style="border-left-color: {border_color};">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="flex: 1;">
                <div style="font-size: 1.1rem; font-weight: 600; color: {COLORS['dark']}; margin-bottom: 0.5rem;">
                    {player.get('display_name', player.get('Name', 'Unknown'))}
                </div>
                <div style="display: flex; gap: 0.75rem; flex-wrap: wrap; font-size: 0.875rem;">
                    {f'<span style="background: linear-gradient(45deg, #1e3a8a, #3730a3); color: white; padding: 0.4rem 0.8rem; border-radius: 6px; font-weight: 600;">{position}</span>' if position else ''}
                    <span style="background: {COLORS['light']}; color: {COLORS['dark']}; padding: 0.4rem 0.8rem; border-radius: 6px; font-weight: 600;">
                        Proj: {player.get('proj_CompositeScore', 0):.2f}
                    </span>
                    <span style="background: {COLORS['light']}; color: {COLORS['muted']}; padding: 0.4rem 0.8rem; border-radius: 6px; font-weight: 500;">
                        {player.get('Team', 'Unknown')}
                    </span>
                </div>
            </div>
            <div style="text-align: right; margin-left: 1rem;">
                <div style="font-size: 1.5rem;">{warning_icon}</div>
            </div>
        </div>
    </div>
    """

def create_recommendation_tile(rec, priority_class="tile-high", priority_icon="↗"):
    """Create a recommendation tile with proper contrast"""
    return f"""
    <div class="{priority_class}" style="color: white !important;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div>
                <h4 style="margin: 0; color: white !important;">
                    <span style="background: rgba(255,255,255,0.2); color: white !important; padding: 0.25rem 0.5rem; border-radius: 6px; margin-right: 0.5rem; font-weight: 600;">{rec['Position']}</span>
                    Upgrade Available
                </h4>
                <p style="margin: 0.25rem 0 0 0; opacity: 0.9; color: white !important;">+{rec['Upgrade']:.2f} projected score improvement</p>
            </div>
            <div style="font-size: 1.5rem;">{priority_icon}</div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-top: 1rem;">
            <div style="text-align: center;">
                <div style="font-size: 0.9rem; opacity: 0.8; color: white !important;">ADD</div>
                <div style="font-size: 1.1rem; font-weight: 600; color: white !important;">{rec['Add']}</div>
                <div style="font-size: 0.8rem; opacity: 0.7; color: white !important;">{rec['Add_Team']} • {rec['Add_Score']:.2f}</div>
            </div>
            <div style="text-align: center; opacity: 0.6;">
                <div style="font-size: 1.5rem; color: white !important;">→</div>
                <div style="font-size: 0.8rem; color: white !important;">REPLACE</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 0.9rem; opacity: 0.8; color: white !important;">DROP</div>
                <div style="font-size: 1.1rem; font-weight: 600; color: white !important;">{rec['Drop']}</div>
                <div style="font-size: 0.8rem; opacity: 0.7; color: white !important;">Score: {rec['Drop_Score']:.2f}</div>
            </div>
        </div>
    </div>
    """

def create_position_strength_tile(position, strength, team_avg, upgrade_potential):
    """Create a position strength analysis tile"""
    # Color based on strength
    if strength == "Strong":
        tile_class = "tile-success"
        strength_color = COLORS['success']
    elif strength == "Average":
        tile_class = "tile-warning"
        strength_color = COLORS['warning']
    else:
        tile_class = "tile"
        strength_color = COLORS['danger']
    
    return f"""
    <div class="{tile_class}">
        <div style="text-align: center;">
            <div style="margin-bottom: 0.5rem;">
                <span class="stat-badge pos-{position}" style="color: white; font-size: 1rem; padding: 0.5rem 1rem;">
                    {position}
                </span>
            </div>
            <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem; color: {strength_color};">
                {strength}
            </div>
            <div style="font-size: 0.9rem; opacity: 0.8; margin-bottom: 0.5rem;">
                Avg: {team_avg:.2f}
            </div>
            <div style="font-size: 0.8rem; opacity: 0.7;">
                Upgrade: {upgrade_potential:+.2f}
            </div>
        </div>
    </div>
    """

def create_rainbow_player_tile(player, index, show_rank=True, rank_number=None):
    """
    Create a beautiful rainbow player tile with muted colors and 3D effects
    
    This function now uses the expandable player tile functionality
    """
    import uuid
    
    # Generate a unique key prefix for each player
    # Include position and player name to make it more unique
    pos = player.get('norm_positions', ['Unknown'])[0] if player.get('norm_positions') else 'Unknown'
    player_name = player.get('display_name', player.get('Name', 'Unknown')).replace(' ', '_').lower()
    
    # Add a unique identifier to ensure uniqueness
    unique_id = uuid.uuid4().hex[:8]
    
    key_prefix = f"rainbow_tile_{pos}_{player_name}_{unique_id}"
    
    # Use the new expandable player tile component
    return create_expandable_player_tile(player, index, key_prefix, show_rank, rank_number)

def create_top_player_tile(player, rank, colors, ranks):
    """Create a top player tile for free agents with high contrast"""
    import pandas as pd
    delta_str = f"Δ {player['ScoreDelta']:.2f}" if pd.notna(player['ScoreDelta']) else "No Δ"
    delta_color = "↗" if pd.notna(player['ScoreDelta']) and player['ScoreDelta'] > 0 else "↘"
    
    # Define high contrast backgrounds for each rank
    backgrounds = [
        "linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%)",  # Dark blue for 1st
        "linear-gradient(135deg, #be185d 0%, #9f1239 100%)",  # Dark red for 2nd  
        "linear-gradient(135deg, #0369a1 0%, #0284c7 100%)"   # Dark cyan for 3rd
    ]
    
    return f"""
    <div style="background: {backgrounds[rank]}; border-radius: 12px; padding: 1.5rem; margin: 1rem 0; 
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15); color: white !important;">
        <div style="text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem; color: white !important;">{ranks[rank]}</div>
            <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem; color: white !important; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">
                {player['display_name']}
            </div>
            <div style="font-size: 0.9rem; margin-bottom: 1rem; color: rgba(255,255,255,0.95) !important; font-weight: 500;">
                {player.get('Team', 'Unknown')}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="text-align: left;">
                    <div style="font-size: 0.8rem; color: rgba(255,255,255,0.8) !important; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">Proj Score</div>
                    <div style="font-size: 1.3rem; font-weight: 800; color: white !important; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">{player['proj_CompositeScore']:.2f}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 0.8rem; color: rgba(255,255,255,0.8) !important; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">Performance</div>
                    <div style="font-size: 1rem; font-weight: 700; color: white !important; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">{delta_color} {delta_str}</div>
                </div>
            </div>
        </div>
    </div>
    """

def create_expandable_player_tile(player, index, key_prefix, show_rank=True, rank_number=None):
    """
    Create an expandable player tile that shows condensed info by default
    and expands to show more details when clicked.
    """
    import pandas as pd
    import uuid
    
    # Generate a unique ID for this player to use in state management
    player_id = player.get('display_name', player.get('Name', 'Unknown')).replace(' ', '_').lower()
    
    # Include position, index, and a unique identifier to ensure uniqueness
    pos = player.get('norm_positions', ['Unknown'])[0] if player.get('norm_positions') else 'Unknown'
    
    # Add a unique identifier based on player's team and score to make the key truly unique
    team = player.get('Team', 'Unknown')
    score = player.get('proj_CompositeScore', 0)
    unique_id = f"{team}_{score:.2f}_{uuid.uuid4().hex[:8]}"
    
    state_key = f"{key_prefix}_{pos}_{index}_{unique_id}_{player_id}"
    
    # Initialize state if not exists
    if state_key not in st.session_state:
        st.session_state[state_key] = False
    
    # Get styling elements
    rainbow_class = get_rainbow_tile_class(index)
    delta_str = f"Δ {player['ScoreDelta']:.2f}" if pd.notna(player['ScoreDelta']) else "—"
    delta_color = COLORS['success'] if pd.notna(player['ScoreDelta']) and player['ScoreDelta'] > 0 else COLORS['danger']
    
    # Use custom rank number if provided, otherwise use index + 1
    if show_rank:
        rank_display = f"{rank_number}. " if rank_number is not None else f"{index + 1}. "
    else:
        rank_display = ""
    
    pos = player.get('norm_positions', ['Unknown'])[0] if player.get('norm_positions') else 'Unknown'
    
    # Create the container for the tile
    tile_container = st.container()
    
    with tile_container:
        # Create a clickable element that toggles the expanded state
        button_label = "▼ Details" if st.session_state[state_key] else "▶ Details"
        if st.button(button_label, key=f"toggle_{state_key}", help="Click to expand/collapse"):
            st.session_state[state_key] = not st.session_state[state_key]
            st.rerun()
        
        # Determine if we're showing expanded or collapsed view
        is_expanded = st.session_state[state_key]
        
        # Display the condensed view with improved hierarchy
        st.markdown(
            f"""
            <div class="{rainbow_class}">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="flex: 1;">
                        <div style="font-size: 1.3rem; font-weight: 800; color: {COLORS['dark']}; margin-bottom: 0.5rem; line-height: 1.2;">
                            {rank_display}{player.get('display_name', player.get('Name', 'Unknown'))}
                        </div>
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem;">
                            <div style="font-size: 1.8rem; font-weight: 800; color: #1e40af;">
                                {player.get('proj_CompositeScore', 0):.1f}
                            </div>
                            <div style="font-size: 0.9rem; color: {delta_color}; font-weight: 600;">
                                {delta_str}
                            </div>
                        </div>
                        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; font-size: 0.8rem;">
                            <span style="background: #f1f5f9; color: #475569; padding: 0.25rem 0.5rem; border-radius: 4px; font-weight: 600;">
                                {pos}
                            </span>
                            <span style="background: #f8fafc; color: #64748b; padding: 0.25rem 0.5rem; border-radius: 4px;">
                                {player.get('Team', 'Unknown')}
                            </span>
                        </div>
                    </div>
                    <div style="text-align: right; margin-left: 1rem; padding-top: 0.25rem;">
                        <div style="font-size: 1rem; color: #9ca3af;">{is_expanded and '▼' or '▶'}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Show expanded content if expanded
        if is_expanded:
            # Determine if player is a pitcher or hitter
            is_pitcher = "Pitcher" in player.get('position', '')
            
            # Create columns for stats
            cols = st.columns(5)
            
            # Select relevant stats based on player type
            if is_pitcher:
                stats = [
                    {"name": "K-BB%", "value": player.get('proj_K-BB%', 0), "color": "#3b82f6"},
                    {"name": "IP", "value": player.get('proj_IP', 0), "color": "#10b981"},
                    {"name": "WHIP", "value": player.get('proj_WHIP', 0), "color": "#f59e0b"},
                    {"name": "FIP", "value": player.get('proj_FIP', 0), "color": "#ef4444"},
                    {"name": "SV", "value": player.get('proj_SV', 0), "color": "#8b5cf6"}
                ]
            else:
                stats = [
                    {"name": "wOBA", "value": player.get('proj_wOBA', 0), "color": "#3b82f6"},
                    {"name": "ISO", "value": player.get('proj_ISO', 0), "color": "#10b981"},
                    {"name": "wBsR", "value": player.get('proj_wBsR', 0), "color": "#f59e0b"},
                    {"name": "AB", "value": player.get('proj_AB', 0), "color": "#ef4444"},
                    {"name": "wRC+", "value": player.get('proj_wRC+', 0), "color": "#8b5cf6"}
                ]
            
            # Display stats in columns
            for i, stat in enumerate(stats):
                with cols[i]:
                    st.markdown(
                        f"""
                        <div style="text-align: center; padding: 0.75rem; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                            <div style="font-size: 0.8rem; color: {COLORS['muted']}; margin-bottom: 0.25rem;">{stat['name']}</div>
                            <div style="font-size: 1.1rem; font-weight: 700; color: {stat['color']};">
                                {format_stat_value(stat['value'])}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            
            # Add position eligibility if available
            if player.get('norm_positions'):
                positions_list = ", ".join(player.get('norm_positions', []))
                st.markdown(f"**Eligible Positions:** {positions_list}")
            
            # Add performance trend if available
            if pd.notna(player.get('curr_CompositeScore')) and pd.notna(player.get('proj_CompositeScore')):
                trend_icon = "↗" if player['curr_CompositeScore'] > player['proj_CompositeScore'] else "↘"
                trend_color = "#10b981" if player['curr_CompositeScore'] > player['proj_CompositeScore'] else "#ef4444"
                st.markdown(f"**Current Performance:** <span style='color: {trend_color}; font-weight: 600;'>{trend_icon} {player.get('curr_CompositeScore', 0):.2f}</span>", unsafe_allow_html=True)
    
    return tile_container
"""
Player Comparison Tool - Compare two players side by side
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
from config import COLORS

def show_player_comparison(df):
    """Show a side-by-side comparison of two players"""
    st.markdown("## Player Comparison Tool")
    st.markdown("**Decision Helper:** Use this to validate add/drop moves, trade decisions, or lineup choices. Higher projected scores = better fantasy value.")
    
    # Get list of all players
    all_players = df.sort_values("proj_CompositeScore", ascending=False).copy()
    player_options = all_players["display_name"].tolist()
    
    # Player selection with pre-selection support from Quick Wins
    col1, col2 = st.columns(2)
    
    # Check for pre-selected players from Quick Wins
    player1_preselect = st.session_state.get('player1_preselect', None)
    player2_preselect = st.session_state.get('player2_preselect', None)
    
    # Determine default indices
    player1_idx = 0
    player2_idx = min(1, len(player_options)-1) if len(player_options) > 1 else 0
    
    if player1_preselect and player1_preselect in player_options:
        player1_idx = player_options.index(player1_preselect)
        # Clear the preselect after using it
        if 'player1_preselect' in st.session_state:
            del st.session_state.player1_preselect
    
    if player2_preselect and player2_preselect in player_options:
        player2_idx = player_options.index(player2_preselect)
        # Clear the preselect after using it
        if 'player2_preselect' in st.session_state:
            del st.session_state.player2_preselect
    
    with col1:
        player1_name = st.selectbox(
            "Select First Player",
            player_options,
            index=player1_idx if player_options else None,
            key="player1"
        )
    
    with col2:
        player2_name = st.selectbox(
            "Select Second Player",
            player_options,
            index=player2_idx if player_options else None,
            key="player2"
        )
    
    if not player1_name or not player2_name:
        st.warning("Please select two players to compare.")
        return
    
    # Get player data
    player1 = all_players[all_players["display_name"] == player1_name].iloc[0]
    player2 = all_players[all_players["display_name"] == player2_name].iloc[0]
    
    # Display comparison
    st.markdown("### Player Comparison")
    
    # Basic info comparison
    col1, col2 = st.columns(2)
    
    with col1:
        pos1 = player1["norm_positions"][0] if player1["norm_positions"] else "Unknown"
        st.markdown(f"""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #3b82f6; 
                    border-radius: 8px; padding: 1.25rem; text-align: center;">
            <div style="margin-bottom: 0.5rem;">
                <span style="background: #3b82f6; color: white; font-size: 0.9rem; padding: 0.4rem 0.8rem; 
                       border-radius: 6px; font-weight: 600;">
                    {pos1}
                </span>
            </div>
            <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.25rem; color: #1e293b;">
                {player1["display_name"]}
            </div>
            <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 0.5rem;">
                Team: {player1.get("Team", "Unknown")}
            </div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #1e293b;">
                Score: {player1["proj_CompositeScore"]:.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        pos2 = player2["norm_positions"][0] if player2["norm_positions"] else "Unknown"
        st.markdown(f"""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #f97316; 
                    border-radius: 8px; padding: 1.25rem; text-align: center;">
            <div style="margin-bottom: 0.5rem;">
                <span style="background: #f97316; color: white; font-size: 0.9rem; padding: 0.4rem 0.8rem; 
                       border-radius: 6px; font-weight: 600;">
                    {pos2}
                </span>
            </div>
            <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.25rem; color: #1e293b;">
                {player2["display_name"]}
            </div>
            <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 0.5rem;">
                Team: {player2.get("Team", "Unknown")}
            </div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #1e293b;">
                Score: {player2["proj_CompositeScore"]:.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Score difference
    score_diff = player1["proj_CompositeScore"] - player2["proj_CompositeScore"]
    better_player = player1["display_name"] if score_diff > 0 else player2["display_name"]
    
    # Decision recommendation based on score difference
    if abs(score_diff) > 1.0:
        decision_bg = "#dcfce7"  # Light green background
        decision_border = "#16a34a"  # Green border
        decision_title = "Clear Choice"
    elif abs(score_diff) > 0.3:
        decision_bg = "#fef3c7"  # Light yellow background
        decision_border = "#d97706"  # Amber border
        decision_title = "Moderate Edge"
    else:
        decision_bg = "#f1f5f9"  # Light gray background
        decision_border = "#64748b"  # Slate border
        decision_title = "Close Call"
    
    st.markdown(f"""
    <div style="background: {decision_bg}; border: 1px solid {decision_border}; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
        <div style="text-align: center;">
            <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem; color: #1e293b;">
                {decision_title}: Difference of {abs(score_diff):.2f} points
            </div>
            <div style="font-size: 0.95rem; color: #334155; font-weight: 500; margin-top: 0.5rem;">
                {better_player} has the higher projected score.
            </div>
            <div style="font-size: 0.9rem; color: #64748b; margin-top: 0.5rem;">
                {
                    "Make this move!" if abs(score_diff) > 1.0 else 
                    "Consider other factors like schedule and health." if abs(score_diff) > 0.3 else
                    "Look at recent trends, matchups, or personal preference."
                }
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Detailed stats comparison
    st.markdown("### Stats Comparison")
    
    # Determine if players are pitchers
    is_pitcher1 = "P" in player1["norm_positions"] if player1["norm_positions"] else False
    is_pitcher2 = "P" in player2["norm_positions"] if player2["norm_positions"] else False
    
    # Get relevant stats based on player type
    if is_pitcher1 and is_pitcher2:
        # Both are pitchers
        stats_to_compare = [
            ("proj_CompositeScore", "Projected Score"),
            ("curr_CompositeScore", "Current Score"),
            ("ScoreDelta", "Score Delta"),
            ("proj_IP", "Projected IP"),
            ("curr_IP", "Current IP"),
            ("proj_FIP", "Projected FIP"),
            ("curr_FIP", "Current FIP"),
            ("proj_WHIP", "Projected WHIP"),
            ("curr_WHIP", "Current WHIP"),
            ("proj_K-BB%", "Projected K-BB%"),
            ("curr_K-BB%", "Current K-BB%"),
            ("proj_SV", "Projected SV"),
            ("curr_SV", "Current SV")
        ]
    elif not is_pitcher1 and not is_pitcher2:
        # Both are hitters
        stats_to_compare = [
            ("proj_CompositeScore", "Projected Score"),
            ("curr_CompositeScore", "Current Score"),
            ("ScoreDelta", "Score Delta"),
            ("proj_AB", "Projected AB"),
            ("curr_AB", "Current AB"),
            ("proj_wOBA", "Projected wOBA"),
            ("curr_wOBA", "Current wOBA"),
            ("proj_wRC+", "Projected wRC+"),
            ("curr_wRC+", "Current wRC+"),
            ("proj_ISO", "Projected ISO"),
            ("curr_ISO", "Current ISO"),
            ("proj_wBsR", "Projected wBsR"),
            ("curr_wBsR", "Current wBsR")
        ]
    else:
        # Mixed - just show composite scores
        stats_to_compare = [
            ("proj_CompositeScore", "Projected Score"),
            ("curr_CompositeScore", "Current Score"),
            ("ScoreDelta", "Score Delta")
        ]
    
    # Create comparison data for chart
    chart_data = []
    for stat_key, stat_name in stats_to_compare:
        # Check if the stat exists in both players' data
        if stat_key in player1 and stat_key in player2:
            # Get values, handle NaN values
            val1 = float(player1[stat_key]) if pd.notna(player1[stat_key]) else 0.0
            val2 = float(player2[stat_key]) if pd.notna(player2[stat_key]) else 0.0
            
            # Calculate difference
            diff = val1 - val2
            
            # For some stats like FIP and WHIP, lower is better
            if stat_key in ["proj_FIP", "curr_FIP", "proj_WHIP", "curr_WHIP"]:
                better = "player1" if diff < 0 else "player2" if diff > 0 else "tie"
            else:
                better = "player1" if diff > 0 else "player2" if diff < 0 else "tie"
            
            # Add to chart data
            chart_data.append({
                "Stat": stat_name,
                player1["display_name"]: val1,
                player2["display_name"]: val2,
                "Difference": diff,
                "Better": better
            })
    
    if chart_data:
        # Convert to DataFrame
        chart_df = pd.DataFrame(chart_data)
        
        # Create grouped stat comparisons using site's tile theme
        st.subheader("Head-to-Head Comparison")
        
        # Group matching stats together (e.g., proj_wOBA and curr_wOBA)
        stat_groups = {}
        scoring_stats = []
        
        for row in chart_data:
            stat_name = row["Stat"]
            # Separate scoring stats for collapsible section
            if "Score" in stat_name:
                scoring_stats.append(row)
                continue
                
            # Extract the base stat name (remove "Projected " or "Current ")
            if stat_name.startswith("Projected "):
                base_stat = stat_name.replace("Projected ", "")
                if base_stat not in stat_groups:
                    stat_groups[base_stat] = {}
                stat_groups[base_stat]["projected"] = row
            elif stat_name.startswith("Current "):
                base_stat = stat_name.replace("Current ", "")
                if base_stat not in stat_groups:
                    stat_groups[base_stat] = {}
                stat_groups[base_stat]["current"] = row
            else:
                # Handle other stats (like Score Delta)
                if stat_name not in stat_groups:
                    stat_groups[stat_name] = {}
                stat_groups[stat_name]["other"] = row
        
        # Create a single collapsible section for all stats
        with st.expander("Detailed Stats Comparison", expanded=True):
            from ui_components import get_rainbow_tile_class
            
            # Combine scoring stats with other stats for a complete list
            all_stats_to_display = []
            
            # Add scoring stats first
            for score_data in scoring_stats:
                all_stats_to_display.append({
                    "name": score_data["Stat"],
                    "data": {"other": score_data}
                })
            
            # Add grouped stats
            for base_stat, group_data in stat_groups.items():
                all_stats_to_display.append({
                    "name": base_stat,
                    "data": group_data
                })
            
            # Display each stat in its own rainbow tile using a different approach
            for tile_index, stat_info in enumerate(all_stats_to_display):
                from ui_components import get_rainbow_tile_class
                tile_class = get_rainbow_tile_class(tile_index)
                stat_name = stat_info["name"]
                group_data = stat_info["data"]
                
                # Create a complete HTML tile with all content inside
                tile_html = f'<div class="{tile_class}">'
                tile_html += f'<h3 style="margin: 0 0 1rem 0; text-align: center; color: #1e293b;">{stat_name}</h3>'
                
                # Handle different types of stat data
                if "projected" in group_data and "current" in group_data:
                    # Both projected and current exist
                    proj_data = group_data["projected"]
                    curr_data = group_data["current"]
                    
                    # Get values and format them
                    p1_proj = proj_data[player1["display_name"]]
                    p2_proj = proj_data[player2["display_name"]]
                    proj_better = proj_data["Better"]
                    
                    p1_curr = curr_data[player1["display_name"]]
                    p2_curr = curr_data[player2["display_name"]]
                    curr_better = curr_data["Better"]
                    
                    # Format values
                    if "Score" in stat_name or "wOBA" in stat_name or "ISO" in stat_name or "WHIP" in stat_name:
                        p1_proj_fmt = f"{p1_proj:.3f}"
                        p2_proj_fmt = f"{p2_proj:.3f}"
                        p1_curr_fmt = f"{p1_curr:.3f}"
                        p2_curr_fmt = f"{p2_curr:.3f}"
                    elif "%" in stat_name:
                        p1_proj_fmt = f"{p1_proj:.1f}%"
                        p2_proj_fmt = f"{p2_proj:.1f}%"
                        p1_curr_fmt = f"{p1_curr:.1f}%"
                        p2_curr_fmt = f"{p2_curr:.1f}%"
                    else:
                        p1_proj_fmt = f"{p1_proj:.1f}"
                        p2_proj_fmt = f"{p2_proj:.1f}"
                        p1_curr_fmt = f"{p1_curr:.1f}"
                        p2_curr_fmt = f"{p2_curr:.1f}"
                    
                    # Add two-column layout
                    tile_html += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">'
                    
                    # Projected column
                    tile_html += '<div>'
                    tile_html += '<h4 style="margin: 0 0 0.75rem 0; text-align: center; color: #374151;">Projected</h4>'
                    tile_html += f'<div style="text-align: center; margin-bottom: 0.5rem; color: #1f2937;"><strong>{player1["display_name"]}</strong>: {p1_proj_fmt} {"✓" if proj_better == "player1" else ""}</div>'
                    tile_html += f'<div style="text-align: center; color: #1f2937;"><strong>{player2["display_name"]}</strong>: {p2_proj_fmt} {"✓" if proj_better == "player2" else ""}</div>'
                    tile_html += '</div>'
                    
                    # Current column
                    tile_html += '<div>'
                    tile_html += '<h4 style="margin: 0 0 0.75rem 0; text-align: center; color: #374151;">Current</h4>'
                    tile_html += f'<div style="text-align: center; margin-bottom: 0.5rem; color: #1f2937;"><strong>{player1["display_name"]}</strong>: {p1_curr_fmt} {"✓" if curr_better == "player1" else ""}</div>'
                    tile_html += f'<div style="text-align: center; color: #1f2937;"><strong>{player2["display_name"]}</strong>: {p2_curr_fmt} {"✓" if curr_better == "player2" else ""}</div>'
                    tile_html += '</div>'
                    
                    tile_html += '</div>'  # Close grid
                
                else:
                    # Handle single stats (scoring stats, etc.)
                    data = group_data.get("other") or group_data.get("projected") or group_data.get("current")
                    if data:
                        p1_val = data[player1["display_name"]]
                        p2_val = data[player2["display_name"]]
                        better = data["Better"]
                        
                        # Format values
                        if "Score" in stat_name or "wOBA" in stat_name or "ISO" in stat_name or "WHIP" in stat_name:
                            p1_fmt = f"{p1_val:.3f}"
                            p2_fmt = f"{p2_val:.3f}"
                        elif "%" in stat_name:
                            p1_fmt = f"{p1_val:.1f}%"
                            p2_fmt = f"{p2_val:.1f}%"
                        else:
                            p1_fmt = f"{p1_val:.1f}"
                            p2_fmt = f"{p2_val:.1f}"
                        
                        # Add head-to-head layout
                        tile_html += '<div style="display: grid; grid-template-columns: 2fr 1fr 2fr; gap: 1rem; align-items: center;">'
                        
                        # Player 1
                        tile_html += '<div style="text-align: center;">'
                        tile_html += f'<div style="margin-bottom: 0.5rem; color: #1f2937;"><strong>{player1["display_name"]}</strong></div>'
                        tile_html += f'<div style="font-size: 1.2rem; font-weight: 600; color: #1f2937;">{p1_fmt} {"✓" if better == "player1" else ""}</div>'
                        tile_html += '</div>'
                        
                        # VS
                        tile_html += '<div style="text-align: center; font-size: 1.2rem; color: #6b7280;">VS</div>'
                        
                        # Player 2
                        tile_html += '<div style="text-align: center;">'
                        tile_html += f'<div style="margin-bottom: 0.5rem; color: #1f2937;"><strong>{player2["display_name"]}</strong></div>'
                        tile_html += f'<div style="font-size: 1.2rem; font-weight: 600; color: #1f2937;">{p2_fmt} {"✓" if better == "player2" else ""}</div>'
                        tile_html += '</div>'
                        
                        tile_html += '</div>'  # Close grid
                
                # Close the tile
                tile_html += '</div>'
                
                # Display the complete tile
                st.markdown(tile_html, unsafe_allow_html=True)
        
        # Create tabs for different view options
        st.subheader("Detailed Comparison")
        tab1, tab2 = st.tabs(["Visual Comparison", "Detailed Breakdown"])
        
        with tab1:
            # Create a comprehensive table view with clear visual hierarchy
            st.markdown("""
            <div style="margin-bottom: 1rem; font-weight: 500;">
                Complete stats comparison table with visual indicators
            </div>
            """, unsafe_allow_html=True)
            
            # Build HTML table for better control over styling
            table_html = f"""
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 1.5rem;">
                    <thead>
                        <tr style="background-color: #f1f5f9; border-bottom: 2px solid #cbd5e1;">
                            <th style="padding: 0.75rem; text-align: left; font-weight: 600; color: #334155;">Stat</th>
                            <th style="padding: 0.75rem; text-align: center; font-weight: 600; color: #334155;">{player1["display_name"]}</th>
                            <th style="padding: 0.75rem; text-align: center; font-weight: 600; color: #334155;">Comparison</th>
                            <th style="padding: 0.75rem; text-align: center; font-weight: 600; color: #334155;">{player2["display_name"]}</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            # Group stats by category
            proj_stats = []
            curr_stats = []
            other_stats = []
            
            for row in chart_data:
                stat_name = row["Stat"]
                if stat_name.startswith("Projected"):
                    proj_stats.append(row)
                elif stat_name.startswith("Current"):
                    curr_stats.append(row)
                else:
                    other_stats.append(row)
            
            # Function to generate table rows for a group of stats
            def generate_rows(stats, header=None):
                rows = ""
                if header:
                    rows += f"""
                        <tr>
                            <td colspan="4" style="padding: 0.75rem; background-color: #e2e8f0; font-weight: 600; color: #334155;">{header}</td>
                        </tr>
                    """
                
                for row in stats:
                    stat_name = row["Stat"]
                    val1 = row[player1["display_name"]]
                    val2 = row[player2["display_name"]]
                    diff = row["Difference"]
                    better = row["Better"]
                    
                    # Format values based on stat type
                    if "Score" in stat_name or "wOBA" in stat_name or "ISO" in stat_name or "WHIP" in stat_name:
                        val1_fmt = f"{val1:.3f}"
                        val2_fmt = f"{val2:.3f}"
                        diff_fmt = f"{abs(diff):.3f}"
                    elif "%" in stat_name:
                        val1_fmt = f"{val1:.1f}%"
                        val2_fmt = f"{val2:.1f}%"
                        diff_fmt = f"{abs(diff):.1f}%"
                    else:
                        val1_fmt = f"{val1:.1f}"
                        val2_fmt = f"{val2:.1f}"
                        diff_fmt = f"{abs(diff):.1f}"
                    
                    # Determine colors and indicators based on who's better
                    if better == "player1":
                        val1_color = "#16a34a"  # Green
                        val2_color = "#64748b"  # Slate
                        arrow = "→"
                        diff_prefix = "+"
                    elif better == "player2":
                        val1_color = "#64748b"  # Slate
                        val2_color = "#16a34a"  # Green
                        arrow = "←"
                        diff_prefix = "-"
                    else:
                        val1_color = "#64748b"  # Slate
                        val2_color = "#64748b"  # Slate
                        arrow = "="
                        diff_prefix = ""
                    
                    rows += f"""
                        <tr style="border-bottom: 1px solid #e2e8f0;">
                            <td style="padding: 0.75rem; text-align: left; color: #334155;">{stat_name}</td>
                            <td style="padding: 0.75rem; text-align: center; font-weight: 600; color: {val1_color};">{val1_fmt}</td>
                            <td style="padding: 0.75rem; text-align: center; color: #64748b;">
                                <div style="display: flex; align-items: center; justify-content: center;">
                                    <span style="font-size: 1rem;">{arrow}</span>
                                    <span style="margin-left: 0.5rem; font-size: 0.85rem;">{diff_prefix}{diff_fmt}</span>
                                </div>
                            </td>
                            <td style="padding: 0.75rem; text-align: center; font-weight: 600; color: {val2_color};">{val2_fmt}</td>
                        </tr>
                    """
                return rows
            
            # Add rows for each category
            if proj_stats:
                table_html += generate_rows(proj_stats, "Projected Stats")
            if curr_stats:
                table_html += generate_rows(curr_stats, "Current Stats")
            if other_stats:
                table_html += generate_rows(other_stats, "Other Stats")
            
            # Close the table
            table_html += """
                    </tbody>
                </table>
            </div>
            """
            
            # Display the table
            st.markdown(table_html, unsafe_allow_html=True)
            
            # Add a legend
            st.markdown("""
            <div style="display: flex; gap: 1.5rem; margin-top: 1rem; margin-bottom: 2rem; font-size: 0.9rem;">
                <div style="display: flex; align-items: center;">
                    <span style="display: inline-block; width: 12px; height: 12px; background-color: #16a34a; border-radius: 50%; margin-right: 0.5rem;"></span>
                    <span style="color: #334155;">Better value</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <span style="display: inline-block; width: 12px; height: 12px; background-color: #64748b; border-radius: 50%; margin-right: 0.5rem;"></span>
                    <span style="color: #334155;">Lower value</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <span style="margin-right: 0.5rem;">→</span>
                    <span style="color: #334155;">Direction of advantage</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Fallback: Display a simple dataframe if the HTML table doesn't render properly
            with st.expander("Alternative View (click to expand)"):
                # Create a simplified dataframe for display
                display_df = pd.DataFrame({
                    "Stat": [row["Stat"] for row in chart_data],
                    f"{player1['display_name']}": [
                        f"{row[player1['display_name']]:.3f}" if "Score" in row["Stat"] or "wOBA" in row["Stat"] or "ISO" in row["Stat"] or "WHIP" in row["Stat"]
                        else f"{row[player1['display_name']]:.1f}%" if "%" in row["Stat"]
                        else f"{row[player1['display_name']]:.1f}"
                        for row in chart_data
                    ],
                    f"{player2['display_name']}": [
                        f"{row[player2['display_name']]:.3f}" if "Score" in row["Stat"] or "wOBA" in row["Stat"] or "ISO" in row["Stat"] or "WHIP" in row["Stat"]
                        else f"{row[player2['display_name']]:.1f}%" if "%" in row["Stat"]
                        else f"{row[player2['display_name']]:.1f}"
                        for row in chart_data
                    ],
                    "Difference": [
                        f"{row['Difference']:.3f}" if "Score" in row["Stat"] or "wOBA" in row["Stat"] or "ISO" in row["Stat"] or "WHIP" in row["Stat"]
                        else f"{row['Difference']:.1f}%" if "%" in row["Stat"]
                        else f"{row['Difference']:.1f}"
                        for row in chart_data
                    ]
                })
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        with tab2:
            # Create a mobile-friendly stats comparison view with expandable sections
            st.markdown("<div style='margin-bottom: 1rem;'>Tap on a stat to see the detailed comparison</div>", unsafe_allow_html=True)
            
            # Create expandable sections for each stat category
            for i, row in enumerate(chart_data):
                stat_name = row["Stat"]
                val1 = row[player1["display_name"]]
                val2 = row[player2["display_name"]]
                diff = row["Difference"]
                better = row["Better"]
                
                # Format values based on stat type
                if "Score" in stat_name or "wOBA" in stat_name or "ISO" in stat_name or "WHIP" in stat_name:
                    val1_fmt = f"{val1:.3f}"
                    val2_fmt = f"{val2:.3f}"
                    diff_fmt = f"{diff:.3f}"
                elif "%" in stat_name:
                    val1_fmt = f"{val1:.1f}%"
                    val2_fmt = f"{val2:.1f}%"
                    diff_fmt = f"{diff:.1f}%"
                else:
                    val1_fmt = f"{val1:.1f}"
                    val2_fmt = f"{val2:.1f}"
                    diff_fmt = f"{diff:.1f}"
                
                # Determine colors based on who's better
                if better == "player1":
                    val1_color = "#16a34a"  # Green
                    val2_color = "#64748b"  # Slate
                    arrow = "→"
                elif better == "player2":
                    val1_color = "#64748b"  # Slate
                    val2_color = "#16a34a"  # Green
                    arrow = "←"
                else:
                    val1_color = "#64748b"  # Slate
                    val2_color = "#64748b"  # Slate
                    arrow = "="
                
                with st.expander(f"{stat_name}"):
                    cols = st.columns([4, 1, 4])
                    
                    with cols[0]:
                        st.markdown(f"""
                        <div style="text-align: center;">
                            <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 0.25rem;">
                                {player1["display_name"]}
                            </div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: {val1_color};">
                                {val1_fmt}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with cols[1]:
                        st.markdown(f"""
                        <div style="text-align: center; padding-top: 1.5rem;">
                            <div style="font-size: 1.2rem; color: #64748b;">{arrow}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with cols[2]:
                        st.markdown(f"""
                        <div style="text-align: center;">
                            <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 0.25rem;">
                                {player2["display_name"]}
                            </div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: {val2_color};">
                                {val2_fmt}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Show difference
                    st.markdown(f"""
                    <div style="text-align: center; margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid #e2e8f0;">
                        <div style="font-size: 0.85rem; color: #64748b;">
                            Difference: {diff_fmt}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Create bar chart for visual comparison
        fig = px.bar(
            chart_df,
            x="Stat",
            y=[player1["display_name"], player2["display_name"]],
            barmode="group",
            title="Stats Comparison",
            color_discrete_sequence=[COLORS["primary"], COLORS["secondary"]]
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Radar chart for overall comparison
        categories = [stat[1] for stat in stats_to_compare if stat[0] in player1 and stat[0] in player2]
        
        if len(categories) >= 3:  # Need at least 3 categories for a radar chart
            import plotly.graph_objects as go
            
            fig = go.Figure()
            
            # Normalize values for radar chart
            values1 = []
            values2 = []
            
            for stat_key, _ in stats_to_compare:
                if stat_key in player1 and stat_key in player2:
                    val1 = player1[stat_key] if pd.notna(player1[stat_key]) else 0
                    val2 = player2[stat_key] if pd.notna(player2[stat_key]) else 0
                    
                    # Simple normalization to 0-1 range
                    max_val = max(abs(val1), abs(val2))
                    if max_val > 0:
                        values1.append(val1 / max_val)
                        values2.append(val2 / max_val)
                    else:
                        values1.append(0)
                        values2.append(0)
            
            fig.add_trace(go.Scatterpolar(
                r=values1,
                theta=categories,
                fill='toself',
                name=player1["display_name"],
                line_color=COLORS["primary"]
            ))
            
            fig.add_trace(go.Scatterpolar(
                r=values2,
                theta=categories,
                fill='toself',
                name=player2["display_name"],
                line_color=COLORS["secondary"]
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )
                ),
                title="Player Comparison Radar"
            )
            
            st.plotly_chart(fig, use_container_width=True)
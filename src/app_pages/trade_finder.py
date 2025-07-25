"""
Trade Finder - Find optimal trade opportunities across teams
"""

import streamlit as st
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import POSITIONS, COLORS
from data_utils import can_play_position
from ui_components import create_rainbow_player_tile, get_rainbow_tile_class

def show_trade_finder(df, selected_team):
    """Show trade opportunities between teams"""
    st.markdown("## 🤝 Trade Finder")
    st.markdown("**💡 Strategy Guide:** Find mutually beneficial trades. Look for players where you have surplus depth to trade for positions where you need help.")
    
    # Get all teams (excluding free agents and your team)
    all_teams = sorted([t for t in df["fantasy_team"].dropna().unique() 
                       if t.lower() not in ["free agent", "fa"] and t != selected_team])
    
    if len(all_teams) < 1:
        st.info("Need other teams in the league to find trade opportunities.")
        return
    
    # Trade partner selection
    st.markdown("### 🎯 Select Trade Partner")
    trade_partner = st.selectbox(
        "Choose team to explore trades with:",
        all_teams,
        help="Select another team to find mutually beneficial trade opportunities"
    )
    
    if not trade_partner:
        return
    
    # Get team data
    your_team_df = df[df["fantasy_team"] == selected_team].copy()
    partner_team_df = df[df["fantasy_team"] == trade_partner].copy()
    
    # Filter for valid positions
    your_team_df = your_team_df[your_team_df["has_valid_position"]]
    partner_team_df = partner_team_df[partner_team_df["has_valid_position"]]
    
    if your_team_df.empty or partner_team_df.empty:
        st.warning("One or both teams have no valid players for trading.")
        return
    
    # Show team comparison overview
    st.markdown("### 📊 Team Comparison Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        your_avg = your_team_df["proj_CompositeScore"].mean()
        your_size = len(your_team_df)
        
        st.markdown(f"""
        <div class="tile-rainbow-2">
            <div style="text-align: center;">
                <div style="font-size: 1.2rem; font-weight: 700; margin-bottom: 0.5rem; color: {COLORS['dark']};">
                    {selected_team} (Your Team)
                </div>
                <div style="font-size: 2rem; font-weight: 800; color: {COLORS['dark']}; margin-bottom: 0.5rem;">
                    {your_avg:.2f}
                </div>
                <div style="font-size: 0.9rem; color: {COLORS['muted']}; font-weight: 600;">
                    Average Value • {your_size} Players
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        partner_avg = partner_team_df["proj_CompositeScore"].mean()
        partner_size = len(partner_team_df)
        
        st.markdown(f"""
        <div class="tile-rainbow-4">
            <div style="text-align: center;">
                <div style="font-size: 1.2rem; font-weight: 700; margin-bottom: 0.5rem; color: {COLORS['dark']};">
                    {trade_partner}
                </div>
                <div style="font-size: 2rem; font-weight: 800; color: {COLORS['dark']}; margin-bottom: 0.5rem;">
                    {partner_avg:.2f}
                </div>
                <div style="font-size: 0.9rem; color: {COLORS['muted']}; font-weight: 600;">
                    Average Value • {partner_size} Players
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Find trade opportunities
    st.markdown("### 🔍 Trade Opportunities")
    
    trade_opportunities = []
    
    # For each position, find potential trades
    for position in POSITIONS:
        # Get players at this position from both teams
        your_pos_players = your_team_df[your_team_df["norm_positions"].apply(
            lambda x: can_play_position(x, position)
        )].copy()
        
        partner_pos_players = partner_team_df[partner_team_df["norm_positions"].apply(
            lambda x: can_play_position(x, position)
        )].copy()
        
        if your_pos_players.empty or partner_pos_players.empty:
            continue
        
        # Sort by projected composite score
        your_pos_players = your_pos_players.sort_values("proj_CompositeScore", ascending=False)
        partner_pos_players = partner_pos_players.sort_values("proj_CompositeScore", ascending=False)
        
        # Find upgrade opportunities for you
        for _, your_player in your_pos_players.iterrows():
            for _, partner_player in partner_pos_players.iterrows():
                your_value = your_player["proj_CompositeScore"]
                partner_value = partner_player["proj_CompositeScore"]
                
                # Look for meaningful upgrades (partner player significantly better)
                if partner_value > your_value + 0.3:
                    trade_opportunities.append({
                        "position": position,
                        "your_player": your_player,
                        "partner_player": partner_player,
                        "your_value": your_value,
                        "partner_value": partner_value,
                        "upgrade_for_you": partner_value - your_value,
                        "trade_type": "upgrade_for_you"
                    })
                
                # Look for opportunities where you can help them (you have better player)
                elif your_value > partner_value + 0.3:
                    trade_opportunities.append({
                        "position": position,
                        "your_player": your_player,
                        "partner_player": partner_player,
                        "your_value": your_value,
                        "partner_value": partner_value,
                        "upgrade_for_them": your_value - partner_value,
                        "trade_type": "upgrade_for_them"
                    })
    
    if not trade_opportunities:
        st.markdown("""
        <div class="tile-rainbow-8">
            <div style="text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 1rem;">🤔</div>
                <h3 style="margin: 0; color: #2C3E50;">No Clear Trade Opportunities</h3>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.8;">
                    Try selecting a different trade partner or adjust your value metric filter.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Group trade opportunities
    upgrades_for_you = [t for t in trade_opportunities if t["trade_type"] == "upgrade_for_you"]
    upgrades_for_them = [t for t in trade_opportunities if t["trade_type"] == "upgrade_for_them"]
    
    # Sort by upgrade potential
    upgrades_for_you.sort(key=lambda x: x["upgrade_for_you"], reverse=True)
    upgrades_for_them.sort(key=lambda x: x["upgrade_for_them"], reverse=True)
    
    # Display upgrade opportunities for you
    if upgrades_for_you:
        st.markdown("#### 📈 Potential Upgrades for Your Team")
        st.markdown(f"**🎯 Strategy:** These {trade_partner} players could improve your roster.")
        
        for i, trade in enumerate(upgrades_for_you[:5]):  # Show top 5
            col1, col2, col3 = st.columns([1, 0.2, 1])
            
            with col1:
                st.markdown(f"""
                <div class="tile-rainbow-4">
                    <div style="text-align: center;">
                        <div style="font-size: 0.8rem; color: #dc2626; font-weight: 700; text-transform: uppercase; margin-bottom: 0.5rem;">
                            📤 YOU TRADE AWAY
                        </div>
                        <div style="font-size: 1.2rem; font-weight: 800; color: {COLORS['dark']}; margin-bottom: 0.5rem;">
                            {trade['your_player']['display_name']}
                        </div>
                        <div style="margin-bottom: 0.75rem;">
                            <span class="stat-badge pos-{trade['position']}" style="color: white; font-weight: 700;">
                                {trade['position']}
                            </span>
                        </div>
                        <div style="font-size: 0.9rem; color: {COLORS['muted']}; margin-bottom: 0.5rem;">
                            {trade['your_player'].get('Team', 'Unknown')}
                        </div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #dc2626;">
                            Value: {trade['your_value']:.2f}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="text-align: center; padding: 2rem 0;">
                    <div style="font-size: 1.5rem; font-weight: 800; color: #16a34a; margin-bottom: 0.5rem;">
                        +{trade['upgrade_for_you']:.1f}
                    </div>
                    <div style="font-size: 2rem;">
                        ↔️
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="tile-rainbow-2">
                    <div style="text-align: center;">
                        <div style="font-size: 0.8rem; color: #16a34a; font-weight: 700; text-transform: uppercase; margin-bottom: 0.5rem;">
                            📥 YOU RECEIVE
                        </div>
                        <div style="font-size: 1.2rem; font-weight: 800; color: {COLORS['dark']}; margin-bottom: 0.5rem;">
                            {trade['partner_player']['display_name']}
                        </div>
                        <div style="margin-bottom: 0.75rem;">
                            <span class="stat-badge pos-{trade['position']}" style="color: white; font-weight: 700;">
                                {trade['position']}
                            </span>
                        </div>
                        <div style="font-size: 0.9rem; color: {COLORS['muted']}; margin-bottom: 0.5rem;">
                            {trade['partner_player'].get('Team', 'Unknown')}
                        </div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #16a34a;">
                            Value: {trade['partner_value']:.2f}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('<div style="margin: 1.5rem 0;"></div>', unsafe_allow_html=True)
    
    # Display opportunities where you can help them
    if upgrades_for_them:
        st.markdown("#### 🤝 Players They Might Want")
        st.markdown(f"**💡 Strategy:** Use these as trade assets. {trade_partner} might be interested in upgrading at these positions.")
        
        # Show in a more compact format
        for i, trade in enumerate(upgrades_for_them[:8]):  # Show top 8
            if i % 4 == 0:
                cols = st.columns(4)
            
            with cols[i % 4]:
                rainbow_class = get_rainbow_tile_class(i + 10)  # Offset for variety
                
                st.markdown(f"""
                <div class="{rainbow_class}" style="text-align: center;">
                    <div style="font-size: 0.8rem; color: {COLORS['muted']}; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">
                        TRADE ASSET
                    </div>
                    <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem; color: {COLORS['dark']};">
                        {trade['your_player']['display_name']}
                    </div>
                    <div style="margin-bottom: 0.75rem;">
                        <span class="stat-badge pos-{trade['position']}" style="color: white; font-weight: 700;">
                            {trade['position']}
                        </span>
                    </div>
                    <div style="font-size: 0.9rem; color: {COLORS['muted']}; margin-bottom: 0.5rem;">
                        Value: {trade['your_value']:.2f}
                    </div>
                    <div style="font-size: 0.8rem; color: #16a34a; font-weight: 600;">
                        +{trade['upgrade_for_them']:.1f} for them
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Multi-player trade suggestions
    st.markdown("### 🔄 Multi-Player Trade Ideas")
    st.markdown("**🧠 Advanced Strategy:** Package deals that could work for both teams.")
    
    # Find complementary trades (where you upgrade at one position, they upgrade at another)
    multi_trades = []
    
    for upgrade_for_you in upgrades_for_you[:3]:
        for upgrade_for_them in upgrades_for_them[:3]:
            if upgrade_for_you["position"] != upgrade_for_them["position"]:
                total_value_change_you = upgrade_for_you["upgrade_for_you"] - upgrade_for_them["upgrade_for_them"]
                total_value_change_them = upgrade_for_them["upgrade_for_them"] - upgrade_for_you["upgrade_for_you"]
                
                # Look for relatively balanced trades
                if abs(total_value_change_you) < 1.0:  # Reasonably balanced
                    multi_trades.append({
                        "you_get": upgrade_for_you["partner_player"],
                        "you_give": upgrade_for_them["your_player"],
                        "they_get": upgrade_for_them["your_player"],
                        "they_give": upgrade_for_you["partner_player"],
                        "your_net_gain": total_value_change_you,
                        "their_net_gain": total_value_change_them,
                        "balance_score": abs(total_value_change_you)
                    })
    
    # Sort by balance (most fair trades first)
    multi_trades.sort(key=lambda x: x["balance_score"])
    
    if multi_trades:
        for i, trade in enumerate(multi_trades[:3]):  # Show top 3 balanced trades
            balance_color = "tile-rainbow-2" if trade["balance_score"] < 0.3 else "tile-rainbow-3" if trade["balance_score"] < 0.6 else "tile-rainbow-4"
            
            st.markdown(f"""
            <div class="{balance_color}">
                <div style="text-align: center; margin-bottom: 1rem;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: {COLORS['dark']};">
                        💼 Package Deal #{i+1}
                    </div>
                    <div style="font-size: 0.9rem; color: {COLORS['muted']};">
                        Balance Score: {trade['balance_score']:.2f} (lower = more fair)
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr auto 1fr; gap: 1rem; align-items: center;">
                    <div style="text-align: center;">
                        <div style="font-size: 0.8rem; color: {COLORS['muted']}; font-weight: 600; margin-bottom: 0.5rem;">YOU GET</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: {COLORS['dark']};">
                            {trade['you_get']['display_name']}
                        </div>
                        <div style="font-size: 0.8rem; color: {COLORS['muted']}; margin-top: 0.25rem;">
                            Net: {trade['your_net_gain']:+.2f}
                        </div>
                    </div>
                    
                    <div style="text-align: center; font-size: 1.5rem;">
                        ↔️
                    </div>
                    
                    <div style="text-align: center;">
                        <div style="font-size: 0.8rem; color: {COLORS['muted']}; font-weight: 600; margin-bottom: 0.5rem;">YOU GIVE</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: {COLORS['dark']};">
                            {trade['you_give']['display_name']}
                        </div>
                        <div style="font-size: 0.8rem; color: {COLORS['muted']}; margin-top: 0.25rem;">
                            Their Net: {trade['their_net_gain']:+.2f}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Option B: correct str.format usage
        st.markdown("""
        <div style="color: {dark}; font-weight: 600;">
            No balanced multi-player trades found. Try the individual upgrade opportunities above.
        </div>
        """.format(dark=COLORS['dark']), unsafe_allow_html=True)

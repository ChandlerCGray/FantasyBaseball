"""
Main Fantasy Baseball App - Modular Version
"""

import os
import sys
import streamlit as st

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import PAGE_CONFIG, DEFAULT_TEAM, COLORS
    from styles import get_custom_css, get_hero_section
    from data_utils import load_data
    from ui_components import create_metric_tile
    from app_pages.add_drop_recommendations import show_add_drop_recommendations
    from app_pages.best_free_agents import show_best_free_agents
    from app_pages.drop_candidates import show_drop_candidates
    from app_pages.team_overview import show_team_overview
    from app_pages.player_comparison import show_player_comparison
    from app_pages.waiver_trends import show_waiver_trends
    from app_pages.league_analysis import show_league_analysis
    from app_pages.draft_strategy import show_draft_strategy
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Please make sure all required modules are available.")
    st.stop()

def main():
    """Main application function"""
    # Configure Streamlit
    st.set_page_config(**PAGE_CONFIG)
    
    # Production environment check
    if os.getenv('STREAMLIT_SERVER_PORT'):
        st.sidebar.info("Running in production mode")
    
    # Apply custom CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Initialize session state for navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Add/Drop Recommendations"
    
    # Simple header
    st.markdown("# Fantasy Baseball Dashboard")
    st.markdown("---")
    
    # Mobile controls - only show on mobile (when sidebar is hidden)
    st.markdown("""
    <style>
    @media (min-width: 769px) {
        .mobile-controls { display: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="mobile-controls">', unsafe_allow_html=True)
        
        # Mobile navigation
        st.markdown("### Mobile Navigation")
        pages = [
            ("Add/Drop Recommendations", "Add/Drop Recommendations"),
            ("Best Free Agents", "Best Free Agents"),
            ("Drop Candidates", "Drop Candidates"),
            ("Team Analysis", "Team Analysis"),
            ("Player Comparison", "Player Comparison"),
            ("Draft Strategy", "Draft Strategy"),
            ("Waiver Trends", "Waiver Trends"),
            ("League Analysis", "League Analysis")
        ]
        
        # Create mobile navigation buttons in 2 columns
        cols = st.columns(2)
        for i, (page_display, page_key) in enumerate(pages):
            col = cols[i % 2]
            if col.button(
                page_display,
                key=f"mobile_nav_{page_key}",
                use_container_width=True,
                type="primary" if st.session_state.current_page == page_key else "secondary"
            ):
                st.session_state.current_page = page_key
                st.rerun()
        
        # Mobile controls expander
        with st.expander("Mobile Controls", expanded=False):
            # Team selection
            df, csv_path = load_data()
            teams = sorted([t for t in df["fantasy_team"].dropna().unique() 
                           if t.lower() not in ["free agent", "fa"]])
            
            selected_team = st.selectbox(
                "Select Your Team",
                teams,
                index=teams.index(DEFAULT_TEAM) if DEFAULT_TEAM in teams else 0,
                key="mobile_team_select"
            )
            
            # Filters
            hide_injured = st.checkbox("Hide Injured Players", value=True, key="mobile_hide_injured")
            min_proj_score = st.slider("Min Projected Score", -3.0, 3.0, -1.0, 0.1, key="mobile_min_score")
            
            # Data update button
            if st.button("Update Data", use_container_width=True, key="mobile_update_data"):
                with st.spinner("Updating data..."):
                    try:
                        import subprocess
                        import sys
                        result = subprocess.run(
                            [sys.executable, "./src/main.py"],
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            cwd="."
                        )
                        st.success("Data updated successfully")
                        st.rerun()
                    except subprocess.CalledProcessError as e:
                        st.error("Update failed")
                        st.code(e.stderr or "No error output")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")
    

    
    # Sidebar controls
    with st.sidebar:
        st.markdown("### Controls")
        
        # Data update button
        if st.button("Update Data", help="Fetch latest data from ESPN and FanGraphs", use_container_width=True):
            with st.spinner("Updating data..."):
                try:
                    import subprocess
                    import sys
                    result = subprocess.run(
                        [sys.executable, "./src/main.py"],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd="."
                    )
                    st.success("Data updated successfully")
                    st.rerun()
                except subprocess.CalledProcessError as e:
                    st.error("Update failed")
                    st.code(e.stderr or "No error output")
        
        st.markdown("---")
        
        # Team selection
        df, csv_path = load_data()
        teams = sorted([t for t in df["fantasy_team"].dropna().unique() 
                       if t.lower() not in ["free agent", "fa"]])
        
        # Use mobile values if they exist, otherwise use defaults
        mobile_team = st.session_state.get("mobile_team_select", DEFAULT_TEAM)
        mobile_hide_injured = st.session_state.get("mobile_hide_injured", True)
        mobile_min_score = st.session_state.get("mobile_min_score", -1.0)
        
        selected_team = st.selectbox(
            "Select Your Team",
            teams,
            index=teams.index(mobile_team) if mobile_team in teams else 0
        )
        
        # Filters
        st.markdown("### Filters")
        hide_injured = st.checkbox("Hide Injured Players", value=mobile_hide_injured)
        min_proj_score = st.slider("Min Projected Score", -3.0, 3.0, mobile_min_score, 0.1)
        
        # Navigation menu
        st.markdown("### Navigation")
        
        pages = [
            ("Add/Drop Recommendations", "Add/Drop Recommendations"),
            ("Best Free Agents", "Best Free Agents"),
            ("Drop Candidates", "Drop Candidates"),
            ("Team Analysis", "Team Analysis"),
            ("Player Comparison", "Player Comparison"),
            ("Draft Strategy", "Draft Strategy"),
            ("Waiver Trends", "Waiver Trends"),
            ("League Analysis", "League Analysis")
        ]
        
        # Create navigation buttons
        for page_display, page_key in pages:
            if st.button(
                page_display,
                key=f"nav_{page_key}",
                use_container_width=True,
                type="primary" if st.session_state.current_page == page_key else "secondary"
            ):
                st.session_state.current_page = page_key
                st.rerun()
        
        # Data info tile
        st.markdown("### Data Info")
        st.markdown(f"""
        <div class="sidebar-nav">
            <div style="text-align: center;">
                <div class="medium-contrast" style="font-size: 0.9rem; margin-bottom: 0.5rem;">Data Source</div>
                <div class="high-contrast" style="font-size: 0.9rem; font-weight: 600;">
                    {os.path.basename(csv_path)}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Filter data
    if hide_injured:
        df = df[~df["display_name"].str.contains(r'\(', na=False)]
    
    # Split into team and free agents
    team_df = df[df["fantasy_team"] == selected_team].copy()
    fa_df = df[df["fantasy_team"].isin(["Free Agent", "FA"]) | df["fantasy_team"].isna()].copy()
    fa_df = fa_df[fa_df["proj_CompositeScore"] >= min_proj_score]
    
    if team_df.empty:
        st.error(f"No players found for team: {selected_team}")
        st.info("Available teams: " + ", ".join(teams))
        st.stop()
    
    # Show data quality info
    total_players = len(df)
    valid_pos_players = len(df[df["has_valid_position"]])
    
    # Quick stats overview
    team_size = len(team_df[team_df["has_valid_position"]])
    fa_size = len(fa_df[fa_df["has_valid_position"]])
    

    
    # Filter for valid positions for most operations
    team_df = team_df[team_df["has_valid_position"]]
    fa_df = fa_df[fa_df["has_valid_position"]]
    
    # Main content area - show page based on sidebar navigation
    st.markdown('<div class="content-section">', unsafe_allow_html=True)
    
    # Remove duplicate page titles - let each page handle its own title
    
    if st.session_state.current_page == "Add/Drop Recommendations":
        show_add_drop_recommendations(team_df, fa_df)
    elif st.session_state.current_page == "Best Free Agents":
        show_best_free_agents(fa_df)
    elif st.session_state.current_page == "Drop Candidates":
        show_drop_candidates(team_df)
    # Trade Finder tab has been removed
    elif st.session_state.current_page == "Team Analysis":
        show_team_overview(team_df, fa_df)
    elif st.session_state.current_page == "Player Comparison":
        show_player_comparison(df)
    elif st.session_state.current_page == "Draft Strategy":
        show_draft_strategy(df)
    elif st.session_state.current_page == "Waiver Trends":
        show_waiver_trends(fa_df)
    elif st.session_state.current_page == "League Analysis":
        show_league_analysis(df, selected_team)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
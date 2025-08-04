"""
Draft Strategy page for Fantasy Baseball App
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import tempfile
import glob
from draft_strategy_generator import analyze_and_adjust_rankings, CONFIG
from ui_components import get_rainbow_tile_class

def get_latest_draft_file():
    """Get the most recent draft strategy Excel file"""
    output_dir = "output"
    if not os.path.exists(output_dir):
        return None
    
    draft_files = [f for f in os.listdir(output_dir) if f.startswith("draft_strategy_") and f.endswith(".xlsx")]
    if not draft_files:
        return None
    
    latest_file = max(draft_files, key=lambda x: os.path.getctime(os.path.join(output_dir, x)))
    return os.path.join(output_dir, latest_file)

def load_existing_draft_data():
    """Load existing draft data from the most recent Excel file"""
    latest_file = get_latest_draft_file()
    if not latest_file:
        return None
    
    try:
        # Read the main sheet
        df = pd.read_excel(latest_file, sheet_name='All players')
        return df
    except Exception as e:
        st.error(f"Error loading existing draft data: {e}")
        return None

def save_draft_data_to_excel(draft_df, original_filepath=None):
    """Save updated draft data back to Excel file"""
    try:
        if original_filepath and os.path.exists(original_filepath):
            filepath = original_filepath
        else:
            # Create new file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join("output", f"draft_strategy_{timestamp}.xlsx")
        
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        
        # Read existing file to preserve other sheets
        if os.path.exists(filepath):
            with pd.ExcelWriter(filepath, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                draft_df.to_excel(writer, sheet_name='All players', index=False)
        else:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                draft_df.to_excel(writer, sheet_name='All players', index=False)
        
        return filepath
    except Exception as e:
        st.error(f"Error saving draft data: {e}")
        return None

def mark_player_drafted(draft_df, player_name, team_name=""):
    """Mark a player as drafted and return updated dataframe"""
    draft_df_copy = draft_df.copy()
    mask = draft_df_copy['Name'] == player_name
    if mask.any():
        draft_df_copy.loc[mask, 'Drafted'] = team_name if team_name else "Drafted"
    return draft_df_copy

def mark_player_undrafted(draft_df, player_name):
    """Mark a player as undrafted and return updated dataframe"""
    draft_df_copy = draft_df.copy()
    mask = draft_df_copy['Name'] == player_name
    if mask.any():
        draft_df_copy.loc[mask, 'Drafted'] = ""
    return draft_df_copy

def prepare_data_for_draft_analysis(df):
    """Convert the main app's dataframe format to match draft_strategy_generator expectations"""
    # Create a copy and rename columns to match expected format
    draft_df = df.copy()
    
    # Map columns to expected names
    column_mapping = {
        'display_name': 'Name',
        'proj_CompositeScore': 'CompositeScore',
        'Team': 'Team',
        'position': 'position',
        'fantasy_team': 'fantasy_team'
    }
    
    # Rename columns that exist
    for old_col, new_col in column_mapping.items():
        if old_col in draft_df.columns:
            draft_df[new_col] = draft_df[old_col]
    
    # Add required columns with defaults if they don't exist
    required_columns = {
        'AB': 'proj_AB',
        'ADP': 'ADP',
        'wOBA': 'proj_wOBA',
        'ISO': 'proj_ISO', 
        'wBsR': 'proj_wBsR',
        'wRC+': 'proj_wRC+',
        'IP': 'proj_IP',
        'FIP': 'proj_FIP',
        'WHIP': 'proj_WHIP',
        'K-BB%': 'proj_K-BB%',
        'SV': 'proj_SV'
    }
    
    for req_col, source_col in required_columns.items():
        if req_col not in draft_df.columns:
            if source_col in draft_df.columns:
                draft_df[req_col] = draft_df[source_col]
            else:
                # Set defaults based on column type
                if req_col == 'AB':
                    # Set a reasonable default AB for hitters, 0 for pitchers
                    draft_df[req_col] = draft_df.apply(
                        lambda row: 450 if 'P' not in str(row.get('position', '')) else 0, 
                        axis=1
                    )
                elif req_col == 'ADP':
                    draft_df[req_col] = range(1, len(draft_df) + 1)  # Sequential ADP
                else:
                    draft_df[req_col] = 0.0
    
    return draft_df

def show_draft_strategy(df):
    """Show draft strategy analysis and recommendations"""
    st.header("Draft Strategy")
    st.write("Smart draft recommendations based on position scarcity, player value, and tier analysis.")
    
    # Include all players for draft analysis (not just free agents)
    draft_eligible = df[df["has_valid_position"]].copy()
    
    if draft_eligible.empty:
        st.error("No players found for draft analysis.")
        return
    
    # Initialize session state for draft data
    if 'draft_data' not in st.session_state:
        # Try to load existing draft data first
        existing_data = load_existing_draft_data()
        if existing_data is not None:
            st.session_state.draft_data = {
                'draft_df': existing_data,
                'generated_at': datetime.now(),
                'filepath': get_latest_draft_file()
            }
    
    # Sidebar controls for draft strategy
    with st.sidebar:
        st.markdown("### Draft Settings")
        num_recommendations = st.slider("Number of Recommendations", 5, 25, 15)
        min_proj_score = st.slider("Minimum Projected Score", -2.0, 3.0, -0.5, 0.1)
        
        # Show current draft file info
        if 'draft_data' in st.session_state and 'filepath' in st.session_state.draft_data:
            filepath = st.session_state.draft_data['filepath']
            if filepath:
                filename = os.path.basename(filepath)
                st.info(f"Current: {filename}")
        
        # Filter by minimum score
        draft_eligible = draft_eligible[draft_eligible["proj_CompositeScore"] >= min_proj_score]
        
        # Generate draft strategy button
        if st.button("Generate New Draft Strategy", type="primary", use_container_width=True):
            with st.spinner("Generating draft strategy..."):
                try:
                    # Prepare data for analysis
                    prepared_df = prepare_data_for_draft_analysis(draft_eligible)
                    
                    # Create a temporary CSV file
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                        prepared_df.to_csv(tmp_file.name, index=False)
                        tmp_path = tmp_file.name
                    
                    # Run the analysis
                    analyzed_df = analyze_and_adjust_rankings(tmp_path)
                    
                    # Clean up temp file
                    os.unlink(tmp_path)
                    
                    # Save to Excel immediately
                    filepath = save_draft_data_to_excel(analyzed_df)
                    
                    # Store results
                    st.session_state.draft_data = {
                        'draft_df': analyzed_df,
                        'generated_at': datetime.now(),
                        'filepath': filepath
                    }
                    st.success("Draft strategy generated successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error generating draft strategy: {e}")
                    if 'tmp_path' in locals():
                        try:
                            os.unlink(tmp_path)
                        except:
                            pass
        
        # Load existing draft button
        if st.button("Reload Latest Draft", use_container_width=True):
            existing_data = load_existing_draft_data()
            if existing_data is not None:
                st.session_state.draft_data = {
                    'draft_df': existing_data,
                    'generated_at': datetime.now(),
                    'filepath': get_latest_draft_file()
                }
                st.success("Latest draft data loaded!")
                st.rerun()
            else:
                st.warning("No existing draft files found.")
    
    # Check if we have draft data
    if 'draft_data' not in st.session_state:
        st.info("Click 'Generate New Draft Strategy' in the sidebar to begin analysis, or load an existing draft.")
        return
    
    draft_df = st.session_state.draft_data['draft_df']
    
    # Create a GUI-style draft board interface
    st.markdown("### Draft Board")
    
    # Top controls row
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search Players", placeholder="Enter player name...")
    
    with col2:
        # Get available positions
        available_positions = set()
        if 'Eligible_Positions' in draft_df.columns:
            for positions in draft_df['Eligible_Positions']:
                if isinstance(positions, set):
                    available_positions.update(positions)
        
        position_filter = st.selectbox(
            "📍 Position Filter",
            options=['All'] + sorted(list(available_positions))
        )
    
    with col3:
        # Tier filter
        if 'Tier' in draft_df.columns:
            tier_options = ['All'] + sorted(draft_df['Tier'].unique())
            tier_filter = st.selectbox("Tier Filter", options=tier_options)
        else:
            tier_filter = 'All'
    
    with col4:
        # Draft status filter
        draft_status = st.selectbox("📋 Status", options=['All', 'Available', 'Drafted'])
    
    # Apply filters
    filtered_df = draft_df.copy()
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['Name'].str.contains(search_term, case=False, na=False)
        ]
    
    if position_filter != 'All':
        filtered_df = filtered_df[
            filtered_df['Eligible_Positions'].apply(
                lambda x: position_filter in x if isinstance(x, set) else False
            )
        ]
    
    if tier_filter != 'All':
        filtered_df = filtered_df[filtered_df['Tier'] == tier_filter]
    
    if draft_status == 'Available':
        filtered_df = filtered_df[filtered_df['Drafted'] == '']
    elif draft_status == 'Drafted':
        filtered_df = filtered_df[filtered_df['Drafted'] != '']
    
    # Summary stats row
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_players = len(filtered_df)
        st.metric("Total Players", total_players)
    
    with col2:
        if 'Drafted' in filtered_df.columns:
            drafted_count = len(filtered_df[filtered_df['Drafted'] != ''])
            st.metric("Drafted", drafted_count)
    
    with col3:
        if 'Drafted' in filtered_df.columns:
            available_count = len(filtered_df[filtered_df['Drafted'] == ''])
            st.metric("Available", available_count)
    
    with col4:
        if 'Tier' in filtered_df.columns and not filtered_df.empty:
            avg_tier = filtered_df['Tier'].mean()
            st.metric("Avg Tier", f"{avg_tier:.1f}")
    
    with col5:
        if 'Adjusted_CompositeScore' in filtered_df.columns and not filtered_df.empty:
            avg_score = filtered_df['Adjusted_CompositeScore'].mean()
            st.metric("Avg Score", f"{avg_score:.2f}")
    
    st.markdown("---")
    
    # Main draft board table
    if not filtered_df.empty:
        # Create the draft board display
        st.markdown("### Draft Board")
        
        # Prepare display dataframe with all relevant columns
        display_columns = [
            'Adjusted_Rank', 'Name', 'position', 'Team', 'Drafted',
            'CompositeScore', 'Adjusted_CompositeScore', 'Tier', 
            'Suggested_Draft_Round', 'VADP', 'ADP'
        ]
        
        available_columns = [col for col in display_columns if col in filtered_df.columns]
        display_df = filtered_df[available_columns].copy()
        
        # Add a "Draft" button column for interactive drafting
        if 'Drafted' in display_df.columns:
            display_df['Draft_Status'] = display_df['Drafted'].apply(
                lambda x: '✅ Drafted' if x != '' else '⭕ Available'
            )
        
        # Format the dataframe for better display
        if 'Adjusted_Rank' in display_df.columns:
            display_df['Rank'] = display_df['Adjusted_Rank'].astype(int)
        
        if 'CompositeScore' in display_df.columns:
            display_df['Base_Score'] = display_df['CompositeScore'].round(2)
        
        if 'Adjusted_CompositeScore' in display_df.columns:
            display_df['Adj_Score'] = display_df['Adjusted_CompositeScore'].round(2)
        
        if 'Suggested_Draft_Round' in display_df.columns:
            display_df['Round'] = display_df['Suggested_Draft_Round'].round(0).astype(int)
        
        if 'VADP' in display_df.columns:
            display_df['VADP'] = display_df['VADP'].round(0).astype(int)
        
        if 'ADP' in display_df.columns:
            display_df['ADP'] = display_df['ADP'].round(1)
        
        # Select final columns for display
        final_columns = ['Rank', 'Name', 'position', 'Team', 'Draft_Status', 'Tier', 'Round', 'Base_Score', 'Adj_Score', 'VADP', 'ADP']
        final_columns = [col for col in final_columns if col in display_df.columns]
        
        display_final = display_df[final_columns].copy()
        
        # Style the dataframe based on tier and draft status
        def style_row(row):
            styles = [''] * len(row)
            
            # Color by tier
            if 'Tier' in row:
                tier = row['Tier']
                if tier == 1:
                    styles = ['background-color: #dcfce7'] * len(row)  # Light green
                elif tier == 2:
                    styles = ['background-color: #fef3c7'] * len(row)  # Light yellow
                elif tier == 3:
                    styles = ['background-color: #fed7d7'] * len(row)  # Light red
                else:
                    styles = ['background-color: #f1f5f9'] * len(row)  # Light gray
            
            # Dim drafted players
            if 'Draft_Status' in row and '✅' in str(row['Draft_Status']):
                styles = ['background-color: #e5e7eb; opacity: 0.7'] * len(row)
            
            return styles
        
        # Interactive draft board with buttons
        st.markdown("**Click on a player to draft/undraft them:**")
        
        # Display players with interactive buttons
        for idx, (_, player) in enumerate(display_final.head(50).iterrows()):  # Limit to 50 for performance
            name = player.get('Name', 'Unknown')
            rank = player.get('Rank', 0)
            position = player.get('position', 'Unknown')
            team = player.get('Team', 'Unknown')
            tier = player.get('Tier', 1)
            round_num = player.get('Round', 1)
            base_score = player.get('Base_Score', 0)
            adj_score = player.get('Adj_Score', 0)
            draft_status = player.get('Draft_Status', '⭕ Available')
            
            # Create columns for player info and draft button
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 3, 1, 1, 1, 1, 1.5])
            
            with col1:
                st.write(f"**#{rank}**")
            
            with col2:
                # Color code by tier
                if tier == 1:
                    st.markdown(f"🟢 **{name}**")
                elif tier == 2:
                    st.markdown(f"🟡 **{name}**")
                elif tier == 3:
                    st.markdown(f"🟠 **{name}**")
                else:
                    st.markdown(f"⚪ **{name}**")
                st.caption(f"{position} • {team}")
            
            with col3:
                st.write(f"T{tier}")
            
            with col4:
                st.write(f"R{round_num}")
            
            with col5:
                st.write(f"{adj_score}")
            
            with col6:
                st.write(draft_status)
            
            with col7:
                # Draft/Undraft button
                is_drafted = '✅' in draft_status
                
                if is_drafted:
                    if st.button(f"Undraft", key=f"undraft_{idx}_{name}", help=f"Mark {name} as available"):
                        # Update the dataframe
                        updated_df = mark_player_undrafted(st.session_state.draft_data['draft_df'], name)
                        st.session_state.draft_data['draft_df'] = updated_df
                        
                        # Save to Excel
                        if 'filepath' in st.session_state.draft_data:
                            save_draft_data_to_excel(updated_df, st.session_state.draft_data['filepath'])
                        
                        st.success(f"{name} marked as available!")
                        st.rerun()
                else:
                    # Team input for drafting
                    team_input = st.text_input(
                        "Team", 
                        key=f"team_{idx}_{name}", 
                        placeholder="Team name",
                        label_visibility="collapsed"
                    )
                    
                    if st.button(f"✅ Draft", key=f"draft_{idx}_{name}", help=f"Mark {name} as drafted"):
                        # Update the dataframe
                        updated_df = mark_player_drafted(st.session_state.draft_data['draft_df'], name, team_input)
                        st.session_state.draft_data['draft_df'] = updated_df
                        
                        # Save to Excel
                        if 'filepath' in st.session_state.draft_data:
                            save_draft_data_to_excel(updated_df, st.session_state.draft_data['filepath'])
                        
                        team_text = f" to {team_input}" if team_input else ""
                        st.success(f"{name} drafted{team_text}!")
                        st.rerun()
            
            # Add separator line
            if idx < 49:  # Don't add separator after last item
                st.markdown("---")
        
        if len(filtered_df) > 100:
            st.info(f"Showing top 100 of {len(filtered_df)} results. Use filters to narrow down.")
        
        # Position-specific rankings
        st.markdown("---")
        st.markdown("### 📍 Position Rankings")
        
        # Create position tabs
        if 'Eligible_Positions' in filtered_df.columns:
            # Get top positions by player count
            position_counts = {}
            for positions in filtered_df['Eligible_Positions']:
                if isinstance(positions, set):
                    for pos in positions:
                        position_counts[pos] = position_counts.get(pos, 0) + 1
            
            # Sort positions by count and take top 8
            top_positions = sorted(position_counts.items(), key=lambda x: x[1], reverse=True)[:8]
            
            if top_positions:
                # Create columns for each position
                pos_cols = st.columns(min(4, len(top_positions)))
                
                for i, (pos, count) in enumerate(top_positions):
                    col_idx = i % len(pos_cols)
                    
                    with pos_cols[col_idx]:
                        st.markdown(f"**{pos}** ({count} players)")
                        
                        # Get top 5 players at this position
                        pos_players = filtered_df[
                            filtered_df['Eligible_Positions'].apply(
                                lambda x: pos in x if isinstance(x, set) else False
                            )
                        ].head(5)
                        
                        for j, (_, player) in enumerate(pos_players.iterrows()):
                            name = player.get('Name', 'Unknown')
                            rank = int(player.get('Adjusted_Rank', 0))
                            tier = int(player.get('Tier', 1))
                            drafted = player.get('Drafted', '')
                            
                            status_icon = '✅' if drafted != '' else '⭕'
                            st.write(f"{status_icon} {j+1}. {name} (#{rank}, T{tier})")
        
        # Tier breakdown
        st.markdown("---")
        st.markdown("### Tier Analysis")
        
        if 'Tier' in filtered_df.columns:
            tier_cols = st.columns(5)
            tier_counts = filtered_df['Tier'].value_counts().sort_index()
            
            for i, (tier, count) in enumerate(tier_counts.head(5).items()):
                with tier_cols[i]:
                    # Calculate availability
                    tier_players = filtered_df[filtered_df['Tier'] == tier]
                    if 'Drafted' in tier_players.columns:
                        available = len(tier_players[tier_players['Drafted'] == ''])
                        drafted = len(tier_players[tier_players['Drafted'] != ''])
                    else:
                        available = count
                        drafted = 0
                    
                    st.metric(
                        f"Tier {tier}",
                        f"{available}/{count}",
                        help=f"{available} available, {drafted} drafted"
                    )
    
    else:
        st.info("No players found matching your criteria.")
    
    # Quick actions section
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if st.button("Reset All Filters", use_container_width=True):
            st.rerun()
    
    with action_col2:
        if st.button("📈 Show Tier 1 Only", use_container_width=True):
            st.session_state.tier_filter = 1
            st.rerun()
    
    with action_col3:
        if st.button("⭕ Available Only", use_container_width=True):
            st.session_state.draft_status = 'Available'
            st.rerun()
    
    # Download section
    st.markdown("---")
    st.subheader("Export Draft Strategy")
    
    if st.button("Generate Excel Export", use_container_width=True):
        with st.spinner("Generating Excel file..."):
            try:
                # Create a temporary CSV and run the full analysis to generate Excel
                prepared_df = prepare_data_for_draft_analysis(draft_eligible)
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                    prepared_df.to_csv(tmp_file.name, index=False)
                    tmp_path = tmp_file.name
                
                # This will generate the Excel file in the output directory
                analyze_and_adjust_rankings(tmp_path)
                
                # Clean up temp file
                os.unlink(tmp_path)
                
                # Find the most recent draft strategy file
                output_dir = "output"
                if os.path.exists(output_dir):
                    draft_files = [f for f in os.listdir(output_dir) if f.startswith("draft_strategy_") and f.endswith(".xlsx")]
                    if draft_files:
                        latest_file = max(draft_files, key=lambda x: os.path.getctime(os.path.join(output_dir, x)))
                        filepath = os.path.join(output_dir, latest_file)
                        
                        with open(filepath, 'rb') as file:
                            st.download_button(
                                label="Download Draft Strategy (Excel)",
                                data=file.read(),
                                file_name=latest_file,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        st.success(f"Excel file generated: {latest_file}")
                    else:
                        st.error("No Excel file was generated.")
                else:
                    st.error("Output directory not found.")
                    
            except Exception as e:
                st.error(f"Error generating Excel file: {e}")
                if 'tmp_path' in locals():
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
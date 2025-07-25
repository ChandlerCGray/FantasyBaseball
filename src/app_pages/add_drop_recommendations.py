import streamlit as st
import pandas as pd
from config import POSITIONS
from data_utils import can_play_position
from ui_components import get_rainbow_tile_class


def show_add_drop_recommendations(team_df, fa_df):
    st.header("Quick Wins")
    st.write(
        "Below are your top upgrade opportunities. Use 'Compare' inside a tile to view detailed stats side by side."
    )

    # Top free agent candidates
    candidates = fa_df.sort_values("proj_CompositeScore", ascending=False).head(20)
    upgrades = []

    # Identify upgrades
    for _, fa in candidates.iterrows():
        for pos in fa.get("norm_positions", []):
            if pos not in POSITIONS:
                continue
            eligible = team_df[team_df["norm_positions"].apply(lambda x: can_play_position(x, pos))]
            drops = eligible[eligible["proj_CompositeScore"] < fa["proj_CompositeScore"]]
            if drops.empty:
                continue
            drop = drops.nsmallest(1, "proj_CompositeScore").iloc[0]
            gain = fa["proj_CompositeScore"] - drop["proj_CompositeScore"]
            if gain <= 0.15:
                continue

            # de-dupe per position+drop
            existing = next(
                (item for item in upgrades
                 if item["pos"] == pos and item["drop"]["display_name"] == drop["display_name"]),
                None
            )
            if existing:
                if existing["gain"] >= gain:
                    continue
                upgrades.remove(existing)

            upgrades.append({"pos": pos, "add": fa, "drop": drop, "gain": gain})

    if not upgrades:
        st.info("No clear upgrades. Adjust filters or check back later.")
        return

    # Sort by gain, limit top 5
    top_upgrades = sorted(upgrades, key=lambda x: x["gain"], reverse=True)[:5]

    # Render each suggestion using native Streamlit components
    for idx, rec in enumerate(top_upgrades):
        # Create a container for each recommendation
        with st.container():
            if idx > 0:
                st.markdown("---")
            
            # Use a card-like container with a border
            with st.container():
                # Header section
                st.subheader(f"{rec['pos']} Position Upgrade")
                st.caption(f"Recommendation #{idx + 1} • +{rec['gain']:.2f} points")
                
                # Player comparison section using columns
                cols = st.columns([5, 1, 5])
                
                # ADD player
                with cols[0]:
                    st.markdown("**ADD**")
                    st.info(
                        f"""
                        **{rec['add']['display_name']}**
                        
                        Team: {rec['add'].get('Team', 'Unknown')}
                        
                        Score: {rec['add']['proj_CompositeScore']:.2f}
                        """
                    )
                
                # Arrow
                with cols[1]:
                    st.write("")
                    st.write("")
                    st.markdown("<div style='text-align: center; font-size: 24px;'>→</div>", unsafe_allow_html=True)
                
                # DROP player
                with cols[2]:
                    st.markdown("**DROP**")
                    st.error(
                        f"""
                        **{rec['drop']['display_name']}**
                        
                        Current roster
                        
                        Score: {rec['drop']['proj_CompositeScore']:.2f}
                        """
                    )
            
            # Compare button with minimal styling and proper padding
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button(
                    "Compare", 
                    key=f"compare_{idx}", 
                    help="View detailed comparison",
                    use_container_width=True,
                    type="primary"
                ):
                    st.session_state.current_page = "Player Comparison"
                    st.session_state.player1_preselect = rec["add"]["display_name"]
                    st.session_state.player2_preselect = rec["drop"]["display_name"]
                    st.rerun()

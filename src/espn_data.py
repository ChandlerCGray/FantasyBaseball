from espn_api.baseball import League
import pandas as pd
import re


def remove_emojis(text):
    """Remove emojis from a string."""
    pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"  # misc symbols
        u"\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    return pattern.sub('', text).strip()


def determine_position(player):
    """Classify a player as 'Pitcher' or by their primary position."""
    if any(slot in player.eligibleSlots for slot in ("P", "SP", "RP")):
        return "Pitcher"
    return getattr(player, "position", "Unknown")


def extract_player_info(player, fantasy_team):
    """Convert a player object to a dictionary for DataFrame ingestion."""
    return {
        "name": player.name,
        "team": getattr(player, "proTeam", "FA"),
        "injury_status": player.injuryStatus,
        "eligible_positions": player.eligibleSlots,
        "fantasy_team": fantasy_team,
        "fantasy_points": player.total_points
    }


def get_all_players(league_id, season, espn_s2, swid):
    """
    Fetch all players in a fantasy baseball league.
    Includes both rostered players and free agents.
    """
    try:
        league = League(league_id=league_id, year=season, espn_s2=espn_s2, swid=swid)
        all_players = []
        rostered_names = set()

        for team in league.teams:
            team_name = remove_emojis(team.team_name)
            for player in team.roster:
                all_players.append(extract_player_info(player, team_name))
                rostered_names.add(player.name)

        for player in league.free_agents(size=5000):
            if player.name not in rostered_names:
                all_players.append(extract_player_info(player, "Free Agent"))

        df = pd.DataFrame(all_players)
        print(f"INFO: Retrieved {len(df)} players from ESPN.")
        # df.to_csv("espn_players.csv", index=False)

        return df

    except Exception as e:
        print(f"ERROR: Failed to fetch players: {e}")
        return pd.DataFrame()

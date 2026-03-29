from espn_api.baseball import League
from espn_api.baseball.constant import POSITION_MAP
import pandas as pd
import json
import re
import requests


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


def extract_player_info(player, fantasy_team, adp_map=None):
    """Convert a player object to a dictionary for DataFrame ingestion."""
    player_id = getattr(player, "playerId", None)
    espn_adp = None
    if adp_map and player_id is not None:
        try:
            espn_adp = adp_map.get(int(player_id))
        except Exception:
            espn_adp = None
    return {
        "player_id": player_id,
        "name": player.name,
        "team": getattr(player, "proTeam", "FA"),
        "injury_status": player.injuryStatus,
        "eligible_positions": player.eligibleSlots,
        "fantasy_team": fantasy_team,
        "fantasy_points": player.total_points,
        "espn_ADP": espn_adp,
    }


def fetch_espn_adp_map(league_id, season, espn_s2, swid, page_size=200, max_pages=40):
    """
    Fetch ESPN ADP values from raw league player pool endpoint.
    Returns: {player_id: averageDraftPosition}
    """
    url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/flb/seasons/{season}/segments/0/leagues/{league_id}"
    cookies = {"espn_s2": espn_s2, "SWID": swid}

    adp_map: dict[int, float] = {}
    offset = 0

    for _ in range(max_pages):
        player_filter = {
            "players": {
                "filterStatus": {"value": ["FREEAGENT", "WAIVERS", "ONTEAM"]},
                "filterSlotIds": {"value": list(range(0, 21))},
                "sortPercOwned": {"sortPriority": 1, "sortAsc": False},
                "limit": page_size,
                "offset": offset,
            }
        }
        headers = {"x-fantasy-filter": json.dumps(player_filter)}

        try:
            resp = requests.get(url, cookies=cookies, params={"view": "kona_player_info"}, headers=headers, timeout=30)
            if not resp.ok:
                print(f"WARNING: ESPN ADP endpoint returned {resp.status_code} at offset {offset}")
                break
            payload = resp.json()
        except Exception as e:
            print(f"WARNING: Failed to fetch ESPN ADP at offset {offset}: {e}")
            break

        players = payload.get("players", [])
        if not players:
            break

        for entry in players:
            player = entry.get("player", {}) if isinstance(entry, dict) else {}
            pid = player.get("id")
            if pid is None:
                continue

            ownership = player.get("ownership", {}) if isinstance(player.get("ownership"), dict) else {}
            adp = ownership.get("averageDraftPosition")

            # Fallback to standard draft rank if ADP is missing.
            if adp is None:
                ranks = player.get("draftRanksByRankType", {})
                if isinstance(ranks, dict):
                    standard_rank = ranks.get("STANDARD", {})
                    if isinstance(standard_rank, dict):
                        adp = standard_rank.get("rank")

            try:
                pid = int(pid)
                adp = float(adp)
            except Exception:
                continue

            if adp > 0:
                adp_map[pid] = adp

        if len(players) < page_size:
            break
        offset += page_size

    if adp_map:
        print(f"INFO: Retrieved ESPN ADP for {len(adp_map)} players.")
    else:
        print("WARNING: No ESPN ADP values retrieved.")
    return adp_map


def get_roster_settings(league_id, season, espn_s2, swid, output_dir="output"):
    """
    Fetch roster slot configuration from ESPN and save to JSON.
    Returns dict like {"C": 1, "1B": 1, "SP": 6, "RP": 3, ...}
    """
    try:
        league = League(league_id=league_id, year=season, espn_s2=espn_s2, swid=swid)
        # Access the raw league data for roster settings
        # The league object stores lineup slot counts from the settings
        # We can infer slots from any team's active roster structure
        slot_counts: dict[str, int] = {}

        # Count lineup slots from the first team's roster
        # Each player has a lineupSlot that shows where they're slotted
        if league.teams:
            team = league.teams[0]
            for player in team.roster:
                slot = getattr(player, "lineupSlot", "")
                if slot and slot not in ("BE", "IL", "IL+"):
                    slot_counts[slot] = slot_counts.get(slot, 0) + 1

        # If we got slots, also try to get from settings API
        # Fallback: use the raw ESPN endpoint
        if not slot_counts:
            # Try raw API
            import requests
            cookies = {"espn_s2": espn_s2, "SWID": swid}
            url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/flb/seasons/{season}/segments/0/leagues/{league_id}"
            resp = requests.get(url, cookies=cookies, params={"view": "mSettings"})
            if resp.ok:
                data = resp.json()
                lineup_slots = data.get("settings", {}).get("rosterSettings", {}).get("lineupSlotCounts", {})
                for slot_id_str, count in lineup_slots.items():
                    slot_id = int(slot_id_str)
                    if count > 0 and slot_id in POSITION_MAP:
                        pos = POSITION_MAP[slot_id]
                        if pos not in ("BE", "IL", "IL+"):
                            slot_counts[pos] = count

        if slot_counts:
            import os
            os.makedirs(output_dir, exist_ok=True)
            path = os.path.join(output_dir, "roster_settings.json")
            with open(path, "w") as f:
                json.dump(slot_counts, f, indent=2)
            print(f"INFO: Roster settings saved: {slot_counts}")

        return slot_counts

    except Exception as e:
        print(f"ERROR: Failed to fetch roster settings: {e}")
        return {}


def get_scoring_settings(league_id, season, espn_s2, swid, output_dir="output"):
    """
    Fetch league scoring rules from ESPN and save to JSON.
    Returns a dict mapping ESPN stat names to point values.
    """
    try:
        import requests, os
        cookies = {"espn_s2": espn_s2, "SWID": swid}
        url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/flb/seasons/{season}/segments/0/leagues/{league_id}"
        resp = requests.get(url, cookies=cookies, params={"view": "mSettings"})
        if not resp.ok:
            print(f"ERROR: ESPN scoring API returned {resp.status_code}")
            return {}
        data = resp.json()
        scoring_items = data.get("settings", {}).get("scoringSettings", {}).get("scoringItems", [])

        scoring = {}
        for item in scoring_items:
            sid = item["statId"]
            pts = item["points"]
            name = POSITION_MAP.get(sid)  # won't work, need STATS_MAP
            # Use espn_api's STATS_MAP for proper names
            from espn_api.baseball.constant import STATS_MAP
            stat_name = STATS_MAP.get(sid, f"UNK_{sid}")
            scoring[stat_name] = pts

        if scoring:
            os.makedirs(output_dir, exist_ok=True)
            path = os.path.join(output_dir, "scoring_settings.json")
            with open(path, "w") as f:
                json.dump(scoring, f, indent=2)
            print(f"INFO: Scoring settings saved: {scoring}")

        return scoring

    except Exception as e:
        print(f"ERROR: Failed to fetch scoring settings: {e}")
        return {}


def get_all_players(league_id, season, espn_s2, swid):
    """
    Fetch all players in a fantasy baseball league.
    Includes both rostered players and free agents.
    """
    try:
        league = League(league_id=league_id, year=season, espn_s2=espn_s2, swid=swid)
        adp_map = fetch_espn_adp_map(league_id, season, espn_s2, swid)
        all_players = []
        rostered_names = set()

        for team in league.teams:
            team_name = remove_emojis(team.team_name)
            for player in team.roster:
                all_players.append(extract_player_info(player, team_name, adp_map))
                rostered_names.add(player.name)

        for player in league.free_agents(size=5000):
            if player.name not in rostered_names:
                all_players.append(extract_player_info(player, "Free Agent", adp_map))

        df = pd.DataFrame(all_players)
        print(f"INFO: Retrieved {len(df)} players from ESPN.")
        # df.to_csv("espn_players.csv", index=False)

        return df

    except Exception as e:
        print(f"ERROR: Failed to fetch players: {e}")
        return pd.DataFrame()

import json
import requests
import pyodbc
from bs4 import BeautifulSoup

def get_fangraphs_data(api_url):
    """
    Fetches data from the Fangraphs API and returns the parsed JSON.
    """
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raises an exception for HTTP errors
        return response.json()
    except Exception as e:
        print(f"Error retrieving data from API: {e}")
        return None

def process_records(data, stat_mapping, insert_table, cursor, conn):
    """
    Processes a list of records using the provided stat_mapping and inserts into the given table.
    Looks up or inserts DimPlayer, DimTeam, and DimSeason.
    """
    table_columns = list(stat_mapping.keys())
    placeholders = ", ".join("?" for _ in table_columns)
    # Build the complete INSERT query.
    # Note: PlayerID, TeamID, and SeasonID come from the Dim* lookups.
    insert_query = (
        f"INSERT INTO {insert_table} (PlayerID, TeamID, SeasonID, " +
        ", ".join(table_columns) +
        ") VALUES (?, ?, ?, " + placeholders + ")"
    )
    
    for record in data.get("data", []):
        # Clean HTML for Name and Team fields.
        name_html = record.get("Name", "")
        team_html = record.get("Team", "")
        player_name = BeautifulSoup(name_html, "html.parser").get_text().strip()
        team_abb = BeautifulSoup(team_html, "html.parser").get_text().strip()
        season_year = record.get("Season")
        
        # DimPlayer: Check if the player exists using the API’s playerid.
        player_id_api = record.get("playerid")
        if not player_id_api:
            print("Warning: playerid is missing for record", record)
            continue
        
        cursor.execute(
            "SELECT playerid FROM DimPlayer WHERE Fangraphsplayerid = ?",
            player_id_api
        )
        row = cursor.fetchone()
        if row and row[0]:
            dim_player_id = row[0]
        else:
            cursor.execute(
                "INSERT INTO DimPlayer (Fangraphsplayerid, PlayerName, Bats) OUTPUT INSERTED.playerid VALUES (?, ?, ?)",
                player_id_api, player_name, record.get("Bats")
            )
            player_row = cursor.fetchone()
            if player_row and player_row[0]:
                dim_player_id = player_row[0]
            else:
                print(f"Error retrieving identity for player {player_name}. Skipping record.")
                conn.rollback()
                continue
            conn.commit()

        # DimTeam: Check if the team exists.
        cursor.execute(
            "SELECT TeamID FROM DimTeam WHERE TeamNameAbb = ?",
            team_abb
        )
        row = cursor.fetchone()
        if row and row[0]:
            team_id = row[0]
        else:
            cursor.execute(
                "INSERT INTO DimTeam (TeamName, TeamNameAbb) OUTPUT INSERTED.TeamID VALUES (?, ?)",
                team_abb, team_abb
            )
            team_row = cursor.fetchone()
            if team_row and team_row[0]:
                team_id = team_row[0]
            else:
                print(f"Error retrieving identity for team {team_abb}. Skipping record.")
                conn.rollback()
                continue
            conn.commit()

        # DimSeason: Check if the season exists.
        cursor.execute(
            "SELECT SeasonID FROM DimSeason WHERE SeasonYear = ?",
            season_year
        )
        row = cursor.fetchone()
        if row and row[0]:
            season_id = row[0]
        else:
            cursor.execute(
                "INSERT INTO DimSeason (SeasonYear) OUTPUT INSERTED.SeasonID VALUES (?)",
                season_year
            )
            season_row = cursor.fetchone()
            if season_row and season_row[0]:
                season_id = season_row[0]
            else:
                print(f"Error retrieving identity for season {season_year}. Skipping record.")
                conn.rollback()
                continue
            conn.commit()

        # Build the parameter tuple for the stat fields using the mapping.
        stat_values = tuple(record.get(api_key) for api_key in stat_mapping.values())
        params = (dim_player_id, team_id, season_id) + stat_values

        try:
            cursor.execute(insert_query, params)
            conn.commit()
        except pyodbc.IntegrityError as ie:
            print(f"Integrity error when inserting fact stats for player {player_name}: {ie}")
            conn.rollback()
            continue
        except Exception as e:
            print(f"Unexpected error when inserting fact stats for player {player_name}: {e}")
            conn.rollback()
            continue

def main():
    # Define your SQL Server connection string.
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=Baseball;"
        "UID=FangraphsApp;"
        "PWD=FangraphsApp;"
        "Trusted_Connection=yes;"
    )
    cursor = conn.cursor()
    
    # Optionally, set NOCOUNT ON for the session.
    cursor.execute("SET NOCOUNT ON;")
    
    # API URL for batting data.
    batting_api_url = (
        "https://www.fangraphs.com/api/leaders/major-league/data?age=&pos=all&stats=bat&lg=all&qual=0&season=2024&season1=2024&startdate=2024-03-01&enddate=2024-11-01&month=0&hand=&team=0&pageitems=2000000000&pagenum=1&ind=0&rost=0&players=&type=8&postseason=&sortdir=default&sortstat=WAR"
    )
    batting_data = get_fangraphs_data(batting_api_url)
    if batting_data is None or "data" not in batting_data:
        print("No batting data retrieved from the API. Exiting batting process.")
    else:
        # Mapping for batting – as in your original script.
        batting_stat_mapping = {
            "Age": "Age",
            "AgeRange": "AgeR",
            "SeasonMin": "SeasonMin",
            "SeasonMax": "SeasonMax",
            "Games": "G",
            "AtBats": "AB",
            "PlateAppearances": "PA",
            "Hits": "H",
            "Singles": "1B",
            "Doubles": "2B",
            "Triples": "3B",
            "HomeRuns": "HR",
            "Runs": "R",
            "RBI": "RBI",
            "BaseOnBalls": "BB",
            "IntentionalWalks": "IBB",
            "StrikeOuts": "SO",
            "HitByPitch": "HBP",
            "SacrificeFlies": "SF",
            "SacrificeHits": "SH",
            "GroundedIntoDoublePlay": "GDP",
            "StolenBases": "SB",
            "CaughtStealing": "CS",
            "BattingAverage": "AVG",
            "GroundBalls": "GB",
            "FlyBalls": "FB",
            "LineDrives": "LD",
            "InfieldFlyBalls": "IFFB",
            "Pitches": "Pitches",
            "Balls": "Balls",
            "Strikes": "Strikes",
            "IFH": "IFH",
            "BU": "BU",
            "BUH": "BUH",
            "BBPercent": "BB%",
            "KPercent": "K%",
            "BBPerK": "BB/K",
            "OnBasePercentage": "OBP",
            "SluggingPercentage": "SLG",
            "OPS": "OPS",
            "ISO": "ISO",
            "BABIP": "BABIP",
            "GB_FB_Ratio": "GB/FB",
            "LDPercent": "LD%",
            "GBPercent": "GB%",
            "FBPercent": "FB%",
            "IFFBPercent": "IFFB%",
            "HR_FB_Ratio": "HR/FB",
            "IFHPercent": "IFH%",
            "BUHPercent": "BUH%",
            "TTOPercent": "TTO%",
            "wOBA": "wOBA",
            "wRAA": "wRAA",
            "wRC": "wRC",
            "BattingValue": "Batting",
            "Fielding": "Fielding",
            "Replacement": "Replacement",
            "Positional": "Positional",
            "wLeague": "wLeague",
            "CFraming": "CFraming",
            "Defense": "Defense",
            "Offense": "Offense",
            "RAR": "RAR",
            "WAR": "WAR",
            "WAROld": "WAROld",
            "Dollars": "Dollars",
            "BaseRunning": "BaseRunning",
            "Spd": "Spd",
            "wRCPlus": "wRC+",
            "wBsR": "wBsR",
            "WPA": "WPA",
            "WPA_Negative": "-WPA",
            "WPA_Positive": "+WPA",
            "RE24": "RE24",
            "REW": "REW",
            "pLI": "pLI",
            "phLI": "phLI",
            "PH": "PH",
            "WPA_per_LI": "WPA/LI",
            "Clutch": "Clutch",
            "FBPercent1": "FB%1",
            "FBv": "FBv",
            "SLPercent": "SL%",
            "SLv": "SLv",
            "CTPercent": "CT%",
            "CTv": "CTv",
            "CBPercent": "CB%",
            "CBv": "CBv",
            "CHPercent": "CH%",
            "CHv": "CHv",
            "SFPercent": "SF%",
            "SFv": "SFv",
            "KNPercent": "KN%",
            "KNv": "KNv",
            "XXPercent": "XX%",
            "POPercent": "PO%",
            "wFB": "wFB",
            "wSL": "wSL",
            "wCT": "wCT",
            "wCB": "wCB",
            "wCH": "wCH",
            "wSF": "wSF",
            "wKN": "wKN",
            "wFB_PerC": "wFB/C",
            "wSL_PerC": "wSL/C",
            "wCT_PerC": "wCT/C",
            "wCB_PerC": "wCB/C",
            "wCH_PerC": "wCH/C",
            "wSF_PerC": "wSF/C",
            "wKN_PerC": "wKN/C",
            "OSwingPercent": "O-Swing%",
            "ZSwingPercent": "Z-Swing%",
            "SwingPercent": "Swing%",
            "OContactPercent": "O-Contact%",
            "ZContactPercent": "Z-Contact%",
            "ContactPercent": "Contact%",
            "ZonePercent": "Zone%",
            "FStrikePercent": "F-Strike%",
            "SwStrPercent": "SwStr%",
            "CStrPercent": "CStr%",
            "CPlusSwStrPercent": "C+SwStr%"
        }
        process_records(batting_data, batting_stat_mapping, "FactSeasonStatsBatting", cursor, conn)
    
    # API URL for pitching data.
    pitching_api_url = (
        "https://www.fangraphs.com/api/leaders/major-league/data?age=&pos=all&stats=pit&lg=all&qual=0&season=2024&season1=2024&startdate=2024-03-01&enddate=2024-11-01&month=0&hand=&team=0&pageitems=2000000000&pagenum=1&ind=0&rost=0&players=&type=8&postseason=&sortdir=default&sortstat=WAR"
    )
    pitching_data = get_fangraphs_data(pitching_api_url)
    if pitching_data is None or "data" not in pitching_data:
        print("No pitching data retrieved from the API. Exiting pitching process.")
    else:
        # Mapping for pitching (all metrics from your JSON sample).
        pitching_stat_mapping = {
            "Throws": "Throws",
            "xMLBAMID": "xMLBAMID",
            "Age": "Age",
            "AgeRange": "AgeR",
            "SeasonMin": "SeasonMin",
            "SeasonMax": "SeasonMax",
            "W": "W",
            "L": "L",
            "ERA": "ERA",
            "G": "G",
            "GS": "GS",
            "QS": "QS",
            "CG": "CG",
            "ShO": "ShO",
            "SV": "SV",
            "BS": "BS",
            "IP": "IP",
            "TBF": "TBF",
            "H": "H",
            "R": "R",
            "ER": "ER",
            "HR": "HR",
            "BB": "BB",
            "IBB": "IBB",
            "HBP": "HBP",
            "WP": "WP",
            "BK": "BK",
            "SO": "SO",
            "GB": "GB",
            "FB": "FB",
            "LD": "LD",
            "IFFB": "IFFB",
            "Pitches": "Pitches",
            "Balls": "Balls",
            "Strikes": "Strikes",
            "RS": "RS",
            "IFH": "IFH",
            "BU": "BU",
            "BUH": "BUH",
            "KPer9": "K/9",
            "BBPer9": "BB/9",
            "K_BB": "K/BB",
            "HPer9": "H/9",
            "HRPer9": "HR/9",
            "AVG": "AVG",
            "WHIP": "WHIP",
            "BABIP": "BABIP",
            "LOBPercent": "LOB%",
            "FIP": "FIP",
            "GB_FB": "GB/FB",
            "LDPercent": "LD%",
            "GBPercent": "GB%",
            "FBPercent": "FB%",
            "IFFBPercent": "IFFB%",
            "HR_FB": "HR/FB",
            "IFHPercent": "IFH%",
            "BUHPercent": "BUH%",
            "TTOPercent": "TTO%",
            "CFraming": "CFraming",
            "Starting": "Starting",
            "Start_IP": "Start-IP",
            "Relieving": "Relieving",
            "Relief_IP": "Relief-IP",
            "RAR": "RAR",
            "WAR": "WAR",
            "Dollars": "Dollars",
            "RA9_Wins": "RA9-Wins",
            "LOB_Wins": "LOB-Wins",
            "BIP_Wins": "BIP-Wins",
            "BS_Wins": "BS-Wins",
            "tERA": "tERA",
            "xFIP": "xFIP",
            "WPA": "WPA",
            "Negative_WPA": "-WPA",
            "Positive_WPA": "+WPA",
            "RE24": "RE24",
            "REW": "REW",
            "pLI": "pLI",
            "inLI": "inLI",
            "gmLI": "gmLI",
            "exLI": "exLI",
            "Pulls": "Pulls",
            "Games": "Games",
            "WPA_LI": "WPA/LI",
            "Clutch": "Clutch",
            "FBPercent1": "FB%1",
            "FBv": "FBv",
            "SLPercent": "SL%",
            "SLv": "SLv",
            "CTPercent": "CT%",
            "CTv": "CTv",
            "CBPercent": "CB%",
            "CBv": "CBv",
            "CHPercent": "CH%",
            "CHv": "CHv",
            "SFPercent": "SF%",
            "SFv": "SFv",
            "KNPercent": "KN%",
            "KNv": "KNv",
            "XXPercent": "XX%",
            "POPercent": "PO%",
            "wFB": "wFB",
            "wSL": "wSL",
            "wCT": "wCT",
            "wCB": "wCB",
            "wCH": "wCH",
            "wSF": "wSF",
            "wKN": "wKN",
            "wFB_PerC": "wFB/C",
            "wSL_PerC": "wSL/C",
            "wCT_PerC": "wCT/C",
            "wCB_PerC": "wCB/C",
            "wCH_PerC": "wCH/C",
            "wSF_PerC": "wSF/C",
            "wKN_PerC": "wKN/C",
            "O_SwingPercent": "O-Swing%",
            "Z_SwingPercent": "Z-Swing%",
            "SwingPercent": "Swing%",
            "O_ContactPercent": "O-Contact%",
            "Z_ContactPercent": "Z-Contact%",
            "ContactPercent": "Contact%",
            "ZonePercent": "Zone%",
            "F_StrikePercent": "F-Strike%",
            "SwStrPercent": "SwStr%",
            "CStrPercent": "CStr%",
            "CPlusSwStrPercent": "C+SwStr%",
            "Pull": "Pull",
            "Cent": "Cent",
            "Oppo": "Oppo",
            "Soft": "Soft",
            "Med": "Med",
            "Hard": "Hard",
            "bipCount": "bipCount",
            "PullPercent": "Pull%",
            "CentPercent": "Cent%",
            "OppoPercent": "Oppo%",
            "SoftPercent": "Soft%",
            "MedPercent": "Med%",
            "HardPercent": "Hard%",
            "KPer9_Plus": "K/9+",
            "BBPer9_Plus": "BB/9+",
            "K_BB_Plus": "K/BB+",
            "HPer9_Plus": "H/9+",
            "HRPer9_Plus": "HR/9+",
            "AVG_Plus": "AVG+",
            "WHIP_Plus": "WHIP+",
            "BABIP_Plus": "BABIP+",
            "LOBPercent_Plus": "LOB%+",
            "KPercent_Plus": "K%+",
            "BBPercent_Plus": "BB%+",
            "LDPercent_Plus": "LD+",
            "GBPercent_Plus": "GB+",
            "FBPercent_Plus": "FB+",
            "HRFBPercent_Plus": "HRFB+",
            "PullPercent_Plus": "Pull%+",
            "CentPercent_Plus": "Cent%+",
            "OppoPercent_Plus": "Oppo%+",
            "SoftPercent_Plus": "Soft%+",
            "MedPercent_Plus": "Med%+",
            "HardPercent_Plus": "Hard%+",
            "xwOBA": "xwOBA",
            "xAVG": "xAVG",
            "xSLG": "xSLG",
            "XBR": "XBR",
            "PPTV": "PPTV",
            "CPTV": "CPTV",
            "BPTV": "BPTV",
            "DSV": "DSV",
            "DGV": "DGV",
            "BTV": "BTV",
            "rPPTV": "rPPTV",
            "rCPTV": "rCPTV",
            "rBPTV": "rBPTV",
            "rDSV": "rDSV",
            "rDGV": "rDGV",
            "rBTV": "rBTV",
            "EBV": "EBV",
            "ESV": "ESV",
            "rFTeamV": "rFTeamV",
            "rBTeamV": "rBTeamV",
            "rTV": "rTV",
            "pfxFA_Percent": "pfxFA%",
            "pfxFT_Percent": "pfxFT%",
            "pfxFC_Percent": "pfxFC%",
            "pfxFS_Percent": "pfxFS%",
            "pfxFO_Percent": "pfxFO%",
            "pfxSI_Percent": "pfxSI%",
            "pfxSL_Percent": "pfxSL%",
            "pfxCU_Percent": "pfxCU%",
            "pfxKC_Percent": "pfxKC%",
            "pfxEP_Percent": "pfxEP%",
            "pfxCH_Percent": "pfxCH%",
            "pfxSC_Percent": "pfxSC%",
            "pfxKN_Percent": "pfxKN%",
            "pfxUN_Percent": "pfxUN%",
            "pfxvFA": "pfxvFA",
            "pfxvFT": "pfxvFT",
            "pfxvFC": "pfxvFC",
            "pfxvFS": "pfxvFS",
            "pfxvFO": "pfxvFO",
            "pfxvSI": "pfxvSI",
            "pfxvSL": "pfxvSL",
            "pfxvCU": "pfxvCU",
            "pfxvKC": "pfxvKC",
            "pfxvEP": "pfxvEP",
            "pfxvCH": "pfxvCH",
            "pfxvSC": "pfxvSC",
            "pfxvKN": "pfxvKN",
            "pfxFA_X": "pfxFA-X",
            "pfxFT_X": "pfxFT-X",
            "pfxFC_X": "pfxFC-X",
            "pfxFS_X": "pfxFS-X",
            "pfxFO_X": "pfxFO-X",
            "pfxSI_X": "pfxSI-X",
            "pfxSL_X": "pfxSL-X",
            "pfxCU_X": "pfxCU-X",
            "pfxKC_X": "pfxKC-X",
            "pfxEP_X": "pfxEP-X",
            "pfxCH_X": "pfxCH-X",
            "pfxSC_X": "pfxSC-X",
            "pfxKN_X": "pfxKN-X",
            "pfxFA_Z": "pfxFA-Z",
            "pfxFT_Z": "pfxFT-Z",
            "pfxFC_Z": "pfxFC-Z",
            "pfxFS_Z": "pfxFS-Z",
            "pfxFO_Z": "pfxFO-Z",
            "pfxSI_Z": "pfxSI-Z",
            "pfxSL_Z": "pfxSL-Z",
            "pfxCU_Z": "pfxCU-Z",
            "pfxKC_Z": "pfxKC-Z",
            "pfxEP_Z": "pfxEP-Z",
            "pfxCH_Z": "pfxCH-Z",
            "pfxSC_Z": "pfxSC-Z",
            "pfxKN_Z": "pfxKN-Z",
            "pfxwFA": "pfxwFA",
            "pfxwFT": "pfxwFT",
            "pfxwFC": "pfxwFC",
            "pfxwFS": "pfxwFS",
            "pfxwFO": "pfxwFO",
            "pfxwSI": "pfxwSI",
            "pfxwSL": "pfxwSL",
            "pfxwCU": "pfxwCU",
            "pfxwKC": "pfxwKC",
            "pfxwEP": "pfxwEP",
            "pfxwCH": "pfxwCH",
            "pfxwSC": "pfxwSC",
            "pfxwKN": "pfxwKN",
            "pfxwFA_PerC": "pfxwFA/C",
            "pfxwFT_PerC": "pfxwFT/C",
            "pfxwFC_PerC": "pfxwFC/C",
            "pfxwFS_PerC": "pfxwFS/C",
            "pfxwFO_PerC": "pfxwFO/C",
            "pfxwSI_PerC": "pfxwSI/C",
            "pfxwSL_PerC": "pfxwSL/C",
            "pfxwCU_PerC": "pfxwCU/C",
            "pfxwKC_PerC": "pfxwKC/C",
            "pfxwEP_PerC": "pfxwEP/C",
            "pfxwCH_PerC": "pfxwCH/C",
            "pfxwSC_PerC": "pfxwSC/C",
            "pfxwKN_PerC": "pfxwKN/C",
            "pfxO_Swing_Percent": "pfxO-Swing%",
            "pfxZ_Swing_Percent": "pfxZ-Swing%",
            "pfxSwing_Percent": "pfxSwing%",
            "pfxO_Contact_Percent": "pfxO-Contact%",
            "pfxZ_Contact_Percent": "pfxZ-Contact%",
            "pfxContact_Percent": "pfxContact%",
            "pfxZone_Percent": "pfxZone%",
            "pfxPace": "pfxPace",
            "piCH_Percent": "piCH%",
            "piCS_Percent": "piCS%",
            "piCU_Percent": "piCU%",
            "piFA_Percent": "piFA%",
            "piFC_Percent": "piFC%",
            "piFS_Percent": "piFS%",
            "piKN_Percent": "piKN%",
            "piSB_Percent": "piSB%",
            "piSI_Percent": "piSI%",
            "piSL_Percent": "piSL%",
            "piXX_Percent": "piXX%",
            "pivCH": "pivCH",
            "pivCS": "pivCS",
            "pivCU": "pivCU",
            "pivFA": "pivFA",
            "pivFC": "pivFC",
            "pivFS": "pivFS",
            "pivKN": "pivKN",
            "pivSB": "pivSB",
            "pivSI": "pivSI",
            "pivSL": "pivSL",
            "pivXX": "pivXX",
            "piCH_X": "piCH-X",
            "piCS_X": "piCS-X",
            "piCU_X": "piCU-X",
            "piFA_X": "piFA-X",
            "piFC_X": "piFC-X",
            "piFS_X": "piFS-X",
            "piKN_X": "piKN-X",
            "piSB_X": "piSB-X",
            "piSI_X": "piSI-X",
            "piSL_X": "piSL-X",
            "piXX_X": "piXX-X",
            "piCH_Z": "piCH-Z",
            "piCS_Z": "piCS-Z",
            "piCU_Z": "piCU-Z",
            "piFA_Z": "piFA-Z",
            "piFC_Z": "piFC-Z",
            "piFS_Z": "piFS-Z",
            "piKN_Z": "piKN-Z",
            "piSB_Z": "piSB-Z",
            "piSI_Z": "piSI-Z",
            "piSL_Z": "piSL-Z",
            "piXX_Z": "piXX-Z",
            "piwCH": "piwCH",
            "piwCS": "piwCS",
            "piwCU": "piwCU",
            "piwFA": "piwFA",
            "piwFC": "piwFC",
            "piwFS": "piwFS",
            "piwKN": "piwKN",
            "piwSB": "piwSB",
            "piwSI": "piwSI",
            "piwSL": "piwSL",
            "piwXX": "piwXX",
            "piwCH_PerC": "piwCH/C",
            "piwCS_PerC": "piwCS/C",
            "piwCU_PerC": "piwCU/C",
            "piwFA_PerC": "piwFA/C",
            "piwFC_PerC": "piwFC/C",
            "piwFS_PerC": "piwFS/C",
            "piwKN_PerC": "piwKN/C",
            "piwSB_PerC": "piwSB/C",
            "piwSI_PerC": "piwSI/C",
            "piwSL_PerC": "piwSL/C",
            "piwXX_PerC": "piwXX/C",
            "piO_Swing_Percent": "piO-Swing%",
            "piZ_Swing_Percent": "piZ-Swing%",
            "piSwing_Percent": "piSwing%",
            "piO_Contact_Percent": "piO-Contact%",
            "piZ_Contact_Percent": "piZ-Contact%",
            "piContact_Percent": "piContact%",
            "piZone_Percent": "piZone%",
            "piPace": "piPace",
            "Events": "Events",
            "EV": "EV",
            "LA": "LA",
            "Barrels": "Barrels",
            "BarrelPercent": "Barrel%",
            "maxEV": "maxEV",
            "HardHit": "HardHit",
            "HardHitPercent": "HardHit%",
            "Q": "Q",
            "TG": "TG",
            "TIP": "TIP",
            "PlayerNameRoute": "PlayerNameRoute",
            "PlayerName": "PlayerName",
            "position": "position",
            "TeamName": "TeamName",
            "TeamNameAbb": "TeamNameAbb",
            "teamid": "teamid",
            "playerid": "playerid",
            "position": "position"
        }
        process_records(pitching_data, pitching_stat_mapping, "FactSeasonStatsPitching", cursor, conn)
    
    cursor.close()
    conn.close()
    print("ETL process completed successfully.")

if __name__ == "__main__":
    main()

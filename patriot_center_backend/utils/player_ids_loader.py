import json
from datetime import datetime, timedelta
import os
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data

# Path to the player_ids.json file in the data directory
PLAYER_IDS_FILE = "patriot_center_backend/data/player_ids.json"

# Fields to keep
FIELDS_TO_KEEP = [
    "full_name", "age", "years_exp", "college", "team",
    "depth_chart_position", "fantasy_positions", "position", "number"
]

# Mapping of team IDs to their full names
TEAM_DEFENSE_NAMES = {
    "SEA": "Seattle Seahawks",
    "CHI": "Chicago Bears",
    "NE": "New England Patriots",
    "DAL": "Dallas Cowboys",
    "GB": "Green Bay Packers",
    "KC": "Kansas City Chiefs",
    "SF": "San Francisco 49ers",
    "PIT": "Pittsburgh Steelers",
    "PHI": "Philadelphia Eagles",
    "BUF": "Buffalo Bills",
    "NYG": "New York Giants",
    "NYJ": "New York Jets",
    "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings",
    "DEN": "Denver Broncos",
    "CLE": "Cleveland Browns",
    "CIN": "Cincinnati Bengals",
    "BAL": "Baltimore Ravens",
    "LAR": "Los Angeles Rams",
    "LAC": "Los Angeles Chargers",
    "ARI": "Arizona Cardinals",
    "ATL": "Atlanta Falcons",
    "CAR": "Carolina Panthers",
    "DET": "Detroit Lions",
    "HOU": "Houston Texans",
    "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars",
    "LV": "Las Vegas Raiders",
    "NO": "New Orleans Saints",
    "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans",
    "WAS": "Washington Commanders"
}

def load_player_ids():
    """
    Load player IDs from the JSON file. If the file is outdated (more than a week old),
    fetch updated data from the Sleeper API and update the file.
    Always ensure team defenses are included in the data.
    """
    # Check if the file exists
    if os.path.exists(PLAYER_IDS_FILE):
        with open(PLAYER_IDS_FILE, "r") as file:
            data = json.load(file)
        
        # Check if the file is outdated
        last_updated = datetime.strptime(data.get("Last_Updated", "1970-01-01"), "%Y-%m-%d")
        if datetime.now() - last_updated < timedelta(weeks=1):
            # Ensure team defenses are included in the data
            for player_id, player_info in data.items():
                # Check if the player ID corresponds to a team defense
                if player_id in TEAM_DEFENSE_NAMES:
                    data[player_id] = {
                        "full_name": TEAM_DEFENSE_NAMES[player_id],
                        "team": player_id,
                        "position": "DEF"  # Set position as "DEF" for team defenses
                    }
                    continue
            return data  # Return the updated data
    
    # If the file is outdated or doesn't exist, fetch new data
    new_data = fetch_updated_player_ids()
    new_data["Last_Updated"] = datetime.now().strftime("%Y-%m-%d")
    
    # Ensure team defenses are included in the new data
    for team_id, team_name in TEAM_DEFENSE_NAMES.items():
        if team_id not in new_data:
            new_data[team_id] = {
                "full_name": team_name,
                "team": team_id,
                "position": "DEF"
            }
    
    # Save the updated data to the file
    with open(PLAYER_IDS_FILE, "w") as file:
        json.dump(new_data, file, indent=4)
    
    return new_data

def fetch_updated_player_ids():
    """
    Fetch updated player IDs from the Sleeper API and filter to include only the desired fields.
    """
    response, status_code = fetch_sleeper_data("players/nfl")
    if status_code != 200:
        raise Exception("Failed to fetch player data from Sleeper API")
    
    # Filter the response to include only the desired fields
    filtered_data = {}
    for player_id, player_info in response.items():
        # Check if the player ID corresponds to a team defense
        if player_id in TEAM_DEFENSE_NAMES:
            filtered_data[player_id] = {
                "full_name": TEAM_DEFENSE_NAMES[player_id],
                "team": player_id,
                "position": "DEF"  # Set position as "DEF" for team defenses
            }
            continue
        
        # For regular players, keep only the desired fields
        filtered_data[player_id] = {key: player_info[key] for key in FIELDS_TO_KEEP if key in player_info}
    
    return filtered_data
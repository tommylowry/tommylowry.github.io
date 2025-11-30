"""
Player IDs loader and refresher for the Patriot Center backend.

Responsibilities:
- Read a cached player_ids.json file with selected player metadata fields.
- Refresh data from the Sleeper API if the cache is older than one week.
- Ensure all NFL team defenses are present as synthetic "players" with position DEF.
- Persist refreshed data back to disk in a stable, readable format.

Notes:
- This module performs file I/O and may perform network requests to Sleeper.
- The cache is timestamped with a Last_Updated YYYY-MM-DD string.
- Only a subset of fields specified in FIELDS_TO_KEEP is retained from the API.
- Returned structure includes a "Last_Updated" key plus player/team entries.
"""

import json
from datetime import datetime, timedelta
import os
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data

# Path to the player_ids.json file in the data directory (absolute path based on repository root)
_UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_UTILS_DIR)
_REPO_ROOT = os.path.dirname(_BACKEND_DIR)
PLAYER_IDS_FILE = os.path.join(_REPO_ROOT, "patriot_center_backend", "data", "player_ids.json")

# Fields to keep from Sleeper's player payload; reduces storage and surface area
FIELDS_TO_KEEP = [
    "full_name", "age", "years_exp", "college", "team",
    "depth_chart_position", "fantasy_positions", "position", "number"
]

# Mapping of team IDs to their full names
# Used to synthesize "DEF" entries for each NFL team defense
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
    "SD": "Los Angeles Chargers",
    "ARI": "Arizona Cardinals",
    "ATL": "Atlanta Falcons",
    "CAR": "Carolina Panthers",
    "DET": "Detroit Lions",
    "HOU": "Houston Texans",
    "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars",
    "LV": "Las Vegas Raiders",
    "OAK": "Las Vegas Raiders",
    "NO": "New Orleans Saints",
    "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans",
    "WAS": "Washington Commanders"
}

def load_player_ids():
    """
    Load player metadata (cached) or refresh if >7 days stale.

    Ensures:
        - Synthetic DEF entries present for all teams.
        - Only whitelisted fields retained.
    """
    # Fast path: existing cache present
    if os.path.exists(PLAYER_IDS_FILE):
        try:
            with open(PLAYER_IDS_FILE, "r") as file:
                data = json.load(file)

            try:
                # Parse timestamp (fallback to epoch for missing/malformed value)
                last_updated = datetime.strptime(data.get("Last_Updated", "1970-01-01"), "%Y-%m-%d")
                refresh = False
            except:
                refresh = True

            if not refresh:
            # Reuse cache if still fresh
                if datetime.now() - last_updated < timedelta(weeks=1):
                    # Ensure defense entries always present even on reuse
                    for team_code, team_name in TEAM_DEFENSE_NAMES.items():
                        if team_code not in data or data[team_code].get("position") != "DEF":
                            data[team_code] = {
                                "full_name": team_name,
                                "team": team_code,
                                "position": "DEF"
                            }
                    return data
            refresh = True
        except json.JSONDecodeError:
            # File exists but is empty or corrupted - trigger refresh
            refresh = True

    # Slow path: stale or missing -> rebuild
    new_data = fetch_updated_player_ids()
    new_data["Last_Updated"] = datetime.now().strftime("%Y-%m-%d")

    # Ensure all team defenses exist (avoid overwriting if already inserted)
    for team_id, team_name in TEAM_DEFENSE_NAMES.items():
        new_data.setdefault(team_id, {
            "full_name": team_name,
            "team": team_id,
            "position": "DEF"
        })

    with open(PLAYER_IDS_FILE, "w") as file:
        json.dump(new_data, file, indent=4)

    return new_data

def fetch_updated_player_ids():
    """
    Refresh player metadata from Sleeper players/nfl endpoint.

    Skips:
        - Defense payload originals (synthetic entries override).
    """
    response, status_code = fetch_sleeper_data("players/nfl")
    if status_code != 200:
        raise Exception("Failed to fetch player data from Sleeper API")

    filtered_data = {}
    for player_id, player_info in response.items():
        # Insert synthetic team defense entries early; skip original payload
        if player_id in TEAM_DEFENSE_NAMES:
            filtered_data[player_id] = {
                "full_name": TEAM_DEFENSE_NAMES[player_id],
                "team": player_id,
                "position": "DEF"
            }
            continue

        # Select only desired fields (presence-checked)
        filtered_data[player_id] = {
            key: player_info[key] for key in FIELDS_TO_KEEP if key in player_info
        }

    # (Defense entries already ensured above)
    return filtered_data
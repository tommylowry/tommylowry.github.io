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
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict
from datetime import datetime, timedelta

from patriot_center_backend.utils.sleeper_api_handler import fetch_json, SleeperAPIError
from patriot_center_backend.utils.config import PLAYER_IDS_FILE

logger = logging.getLogger(__name__)

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

def load_player_ids(force_refresh: bool = False, max_age_days: int = 7) -> Dict[str, Dict]:
    """
    Load player IDs from disk; refresh from Sleeper if missing or older than max_age_days.
    - Returns a flat mapping of player_id -> metadata (callers remain unchanged).
    - On refresh, writes a file wrapper with metadata:
      { "schema_version": 1, "Last_Updated": "YYYY-MM-DD", "players": { ... } }
    - Backward compatible with legacy flat JSON files (refreshed and rewritten on first run).
    """
    path = Path(PLAYER_IDS_FILE)

    def _return_players_from_raw(raw: dict) -> Dict[str, Dict]:
        # Support both wrapped and legacy flat formats
        if isinstance(raw, dict) and "players" in raw:
            return raw["players"]
        return raw if isinstance(raw, dict) else {}

    if path.exists() and not force_refresh:
        try:
            with path.open("r") as f:
                raw = json.load(f)
        except json.JSONDecodeError:
            raw = None

        if isinstance(raw, dict) and "players" in raw and "Last_Updated" in raw:
            # Wrapped format with metadata
            try:
                last = datetime.fromisoformat(str(raw["Last_Updated"]))
            except Exception:
                last = None
            if last and datetime.utcnow() - last < timedelta(days=max_age_days):
                return raw["players"]
            # stale -> refresh
        elif isinstance(raw, dict):
            # Legacy flat file without Last_Updated; treat as stale so we stamp it once
            logger.info("player_ids.json is legacy (no Last_Updated); refreshing to add metadata.")

    # Fetch fresh data
    try:
        data = fetch_updated_player_ids()
    except SleeperAPIError as e:
        logger.warning("Failed to refresh player IDs from Sleeper (%s). Falling back to existing cache if present.", e)
        if path.exists():
            try:
                with path.open("r") as f:
                    raw = json.load(f)
                return _return_players_from_raw(raw)
            except Exception:
                pass
        raise

    # Persist wrapped with metadata
    wrapped = {
        "schema_version": 1,
        "Last_Updated": datetime.utcnow().date().isoformat(),
        "players": data,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as file:
        json.dump(wrapped, file, indent=4)

    return data

def fetch_updated_player_ids() -> Dict[str, Dict]:
    """
    Fetch and filter player metadata from the Sleeper API.

    Behavior:
    - Calls Sleeper endpoint "players/nfl".
    - On success, returns a dict filtered to FIELDS_TO_KEEP for players.
    - Inserts synthetic DEF entries for every NFL team specified in TEAM_DEFENSE_NAMES.

    Returns:
    - dict: Mapping of player_id (or team code for defenses) to selected metadata fields.

    Raises:
    - SleeperAPIError: If the Sleeper API call fails.
    """
    response = fetch_json("players/nfl")

    filtered_data: Dict[str, Dict] = {}
    for player_id, player_info in response.items():
        # Add team defenses as synthetic players with position DEF
        if player_id in TEAM_DEFENSE_NAMES:
            filtered_data[player_id] = {
                "full_name": TEAM_DEFENSE_NAMES[player_id],
                "team": player_id,
                "position": "DEF",
            }
            continue

        # For regular players, keep only the desired fields to minimize storage
        filtered_data[player_id] = {key: player_info[key] for key in FIELDS_TO_KEEP if key in player_info}

    return filtered_data

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    from pprint import pprint
    ids = load_player_ids()
    print("Total player IDs:", len(ids))
    sample = list(ids.items())[:5]
    pprint(sample)
"""
Cache utilities for the Patriot Center backend.

Responsibilities:
- Load a JSON cache file (creating a structured default cache if missing).
- Save a JSON cache file with pretty formatting.
- Query Sleeper API to determine the current season and week.

Notes:
- When a cache file does not exist, an initial structure is created with
  Last_Updated_Season/Week markers and a per-season dictionary seeded from
  LEAGUE_IDS. For "replacement_score" caches, additional prior seasons are
  included to support multi-year averages.
- External network calls are performed in get_current_season_and_week via the Sleeper API.
"""

from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Any, Dict, Tuple

from patriot_center_backend.utils.sleeper_api_handler import fetch_json, SleeperAPIError
from patriot_center_backend.constants import LEAGUE_IDS


def load_cache(file_path):
    """
    Load data from a JSON cache file, or initialize a new cache structure.

    Behavior:
    - If file exists, returns its JSON content.
    - If missing, returns a dict pre-seeded with:
      - Last_Updated_Season: "0"
      - Last_Updated_Week: 0
      - One empty dict per season from LEAGUE_IDS.
      - Special case: if "replacement_score" appears in file_path, includes
        three additional seasons prior to the earliest LEAGUE_IDS year to
        support multi-year computations (e.g., 3-year rolling averages).

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        dict: The loaded data, or an initialized cache structure if the file doesn't exist.
    """
    if os.path.exists(file_path):
        # Load and return existing cache content
        with open(file_path, "r") as file:
            return json.load(file)
    else:
        # Initialize the cache with all years (plus historical years for replacement score caches)
        cache = {"Last_Updated_Season": "0", "Last_Updated_Week": 0}
        
        # Seed cache keys for all configured seasons
        years = list(LEAGUE_IDS.keys())
        
        # For replacement score caches, backfill extra seasons to compute multi-year averages
        if "replacement_score" in file_path:
            first_year = min(years)
            years.extend([first_year - 3, first_year - 2, first_year - 1])
            years = sorted(years)

        # Initialize an empty dict for each season
        for year in years:
            cache[str(year)] = {}
        return cache
    # Fallback (should be unreachable because function returns above)
    return {}


def save_cache(file_path, data):
    """
    Save data to a JSON cache file with indentation for readability.

    Args:
        file_path (str): Path to the JSON file.
        data (dict): The data to save.
    """
    # Persist cache atomically by writing the entire structure with 4-space indentation
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

def get_current_season_and_week() -> Tuple[int, int]:
    """Fetch the current season and week from Sleeper."""
    current_year = datetime.now().year
    league_id = LEAGUE_IDS.get(int(current_year))
    if not league_id:
        raise RuntimeError(f"No league ID found for the current year: {current_year}")
    league_info = fetch_json(f"league/{league_id}")
    current_season = int(league_info.get("season"))
    current_week = int(league_info.get("settings", {}).get("last_scored_leg", 0))
    return current_season, current_week

def get_max_weeks_for(kind: str, season: int, current_season: int, current_week: int) -> int:
    """
    Shared helper to cap the number of weeks processed per season.

    Rules:
    - starters, ffwar: cap regular season to 13 for 2019/2020, else 14.
    - replacement: cap to 17 for <=2020, else 18.
    - For the live season, clamp by current_week.
    """
    if kind in ("starters", "ffwar"):
        cap = 13 if season in (2019, 2020) else 14
        return min(current_week, cap) if season == current_season else cap
    if kind == "replacement":
        cap = 17 if season <= 2020 else 18
        return min(current_week, cap) if season == current_season else cap
    # Default conservative behavior
    return min(current_week, 14) if season == current_season else 14
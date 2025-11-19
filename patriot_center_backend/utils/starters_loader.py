"""Starters cache builder/updater for Patriot Center.

Responsibilities:
- Maintain per-week starters and points per manager from Sleeper.
- Incrementally update a JSON cache, resuming from Last_Updated_* markers.
- Normalize totals to 2 decimals and resolve manager display names.

Notes:
- Weeks are capped at 14 to exclude fantasy playoffs.
- Import-time execution at bottom warms the cache for downstream consumers.
"""
from __future__ import annotations

from decimal import Decimal
import logging
from typing import Dict, Optional

from patriot_center_backend.utils.sleeper_api_handler import fetch_json, SleeperAPIError
from patriot_center_backend.constants import LEAGUE_IDS, USERNAME_TO_REAL_NAME
from patriot_center_backend.utils.player_ids_loader import load_player_ids
from patriot_center_backend.utils.helpers import get_current_season_and_week, get_max_weeks_for
from patriot_center_backend.utils.cache_manager import CacheManager
from patriot_center_backend.constants import LEAGUE_IDS as _YEARS_SRC
from patriot_center_backend.utils.config import STARTERS_CACHE_FILE


# Constants
# Path to starters cache; PLAYER_IDS is used to map names/positions for lineup entries.
# PLAYER_IDS mapping is now injected; fallback loaded on demand.

logger = logging.getLogger(__name__)

def load_or_update_starters_cache(player_ids: Optional[Dict] = None) -> Dict:
    """
    Load starters data from the cache file. If the cache is outdated or doesn't exist,
    fetch only the missing data from the Sleeper API and update the cache.
    """
    player_ids = player_ids or load_player_ids()

    manager = CacheManager(STARTERS_CACHE_FILE, seed_years=list(_YEARS_SRC.keys()), schema="starters").load()
    cache = manager.data

    current_season, current_week = get_current_season_and_week()
    if current_week > 14:
        current_week = 14

    # Iterate seasons in ascending order so progress markers move forward predictably
    for year in sorted(LEAGUE_IDS.keys()):
        y = int(year)

        # Compute cap for this season; clamp current season to current_week
        max_weeks = get_max_weeks_for("starters", y, current_season, current_week)

        # Read and normalize progress markers
        lu_season, lu_week = manager.get_last_updated()
        try:
            lu_season_i = int(lu_season)
        except Exception:
            lu_season_i = 0
        try:
            lu_week_i = int(lu_week)
        except Exception:
            lu_week_i = 0

        # Skip fully-completed past seasons
        if lu_season_i and y < lu_season_i:
            continue

        # If we advance to a new season beyond the last updated season, reset week progress
        if lu_season_i < y:
            manager.reset_week_progress()
            lu_week_i = 0

        # Determine week range to process for this season
        start_week = lu_week_i + 1 if lu_season_i == y else 1
        if start_week > max_weeks:
            continue

        weeks_to_update = range(start_week, max_weeks + 1)
        logger.info("Updating starters cache season=%s weeks=%s", y, list(weeks_to_update))

        for wk in weeks_to_update:
            manager.ensure_year(y)
            week_payload = fetch_starters_for_week(y, wk, player_ids)
            manager.set_week_data(y, wk, week_payload)
            logger.debug("Starters cache updated season=%s week=%s", y, wk)

        # If we just finished the live season up to current_week, we can stop
        if y == current_season and max_weeks == current_week:
            break

    manager.save()
    return manager.strip_metadata_for_return()


def fetch_starters_for_week(season: int, week: int, player_ids: Dict) -> Dict:
    """
    Fetch starters data for a specific season and week.
    """
    league_id = LEAGUE_IDS[int(season)]
    try:
        managers = fetch_json(f"league/{league_id}/users")
    except SleeperAPIError:
        return {}

    # Fetch rosters once per season to map owner_id -> roster_id (avoid per-manager API calls)
    try:
        rosters = fetch_json(f"league/{league_id}/rosters")
    except SleeperAPIError:
        rosters = []

    owner_to_roster = {r.get("owner_id"): r.get("roster_id") for r in rosters if "owner_id" in r and "roster_id" in r}

    week_data: Dict[str, Dict] = {}
    
    try:
        matchups = fetch_json(f"league/{league_id}/matchups/{week}")
    except SleeperAPIError:
        return None
    
    for manager in managers:
        real_name = USERNAME_TO_REAL_NAME.get(manager.get("display_name"), "Unknown Manager")
        # 2019: Tommy started first 3 weeks before Cody took over
        if int(season) == 2019 and week < 4 and real_name == "Cody":
            real_name = "Tommy"

        roster_id = owner_to_roster.get(manager.get("user_id"))
        if roster_id is None and int(season) == 2024 and real_name == "Davey":
            roster_id = 4  # special case

        if not roster_id:
            continue
        
        starters_data = get_starters_data(league_id, int(roster_id), week, player_ids, matchups)
        if starters_data:
            week_data[real_name] = starters_data

    return week_data


def get_roster_id(year: int, user_id: str) -> Optional[int]:
    """
    Fetch the roster ID for a specific user in a given year.

    Behavior:
    - Queries Sleeper rosters for the league and finds the one owned by user_id.

    Args:
        year (int): The year to fetch the roster ID for.
        user_id (str): The user ID to fetch the roster ID for.

    Returns:
        str: The roster ID, or None if not found or API error occurs.
    """
    league_id = LEAGUE_IDS[int(year)]
    try:
        rosters = fetch_json(f"league/{league_id}/rosters")
    except SleeperAPIError:
        return None
    for roster in rosters:
        if roster['owner_id'] == user_id:
            return roster['roster_id']
    return None


def get_starters_data(league_id: str, roster_id: int, week: int, player_ids: Dict, matchups: Dict) -> Optional[Dict]:
    """
    Fetch starters data for a specific roster and week.

    Behavior:
    - Retrieves matchups, locates the record for roster_id, and builds:
      { player_name: {points, position}, "Total_Points": float }.
    - Filters out unknown players/positions to keep cache clean.
    - Rounds total points to two decimals via Decimal normalization.

    Args:
        league_id (str): The league ID.
        roster_id (str): The roster ID.
        week (int): The week to fetch data for.

    Returns:
        dict: The starters data for the given roster and week, or None on API error/absence.
    """
    for matchup in matchups:
        if matchup['roster_id'] == roster_id:
            manager_data = {"Total_Points": 0}
            for player_id in matchup['starters']:
                player_name = player_ids.get(player_id, {}).get('full_name', 'Unknown Player')
                if player_name == 'Unknown Player':
                    continue
                player_score = matchup['players_points'].get(player_id, 0)
                player_position = player_ids.get(player_id, {}).get('position', 'Unknown Position')
                if player_position == 'Unknown Position':
                    continue

                # Add player data
                manager_data[player_name] = {
                    "points": player_score,
                    "position": player_position
                }

                # Update total points
                manager_data["Total_Points"] += player_score

            # Normalize to 2 decimals; consistent presentation across weeks/managers
            manager_data["Total_Points"] = float(Decimal(manager_data["Total_Points"]).quantize(Decimal('0.01')).normalize())

            return manager_data

    return None

# Debug entrypoint
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    logger.info("Debug run: starters loader")
    data = load_or_update_starters_cache()
    seasons = [s for s in data.keys() if s.isdigit()]
    logger.info("Seasons loaded: %s", seasons)
    if seasons:
        latest = str(max(map(int, seasons)))
        weeks = sorted(data[latest].keys(), key=lambda x: int(x))
        logger.info("Latest season=%s weeks=%s", latest, weeks)
        if weeks:
            sample_week = weeks[-1]
            sample_mgrs = list(data[latest][sample_week].items())[:3]
            print(f"Sample managers season={latest} week={sample_week}:")
            for mgr, lineup in sample_mgrs:
                print(mgr, "Total_Points:", lineup.get("Total_Points"))
"""Starters cache builder/updater for Patriot Center.

Responsibilities:
- Maintain per-week starters and points per manager from Sleeper.
- Incrementally update a JSON cache, resuming from Last_Updated_* markers.
- Normalize totals to 2 decimals and resolve manager display names.

Performance:
- Minimizes API calls by:
  * Skipping already processed weeks (progress markers).
  * Only fetching week/user/roster/matchup data when needed.

Notes:
- Weeks are capped at 14 to exclude fantasy playoffs.
- Import-time execution at bottom warms the cache for downstream consumers.
"""
from decimal import Decimal
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data
from patriot_center_backend.constants import LEAGUE_IDS, USERNAME_TO_REAL_NAME
from patriot_center_backend.utils.player_ids_loader import load_player_ids
from patriot_center_backend.utils.cache_utils import load_cache, save_cache, get_current_season_and_week

# Path to starters cache; PLAYER_IDS maps IDs -> names/positions.
STARTERS_CACHE_FILE = "patriot_center_backend/data/starters_cache.json"
PLAYER_IDS = load_player_ids()

def load_or_update_starters_cache():
    """
    Incrementally load/update starters cache and persist changes.

    Logic:
    - Resume from Last_Updated_* markers (avoids redundant API calls).
    - Cap weeks at 14 (exclude playoffs).
    - Only fetch missing weeks per season; break early if fully current.
    - Strip metadata before returning to callers.

    Returns:
        dict: Nested {season: {week: {manager: {...}}}}
    """
    cache = load_cache(STARTERS_CACHE_FILE)

    current_season, current_week = get_current_season_and_week()
    if current_week > 14:
        current_week = 14  # Regular season cap

    for year in LEAGUE_IDS.keys():
        last_updated_season = int(cache.get("Last_Updated_Season", 0))
        last_updated_week = cache.get("Last_Updated_Week", 0)

        # Skip previously finished seasons; reset week marker when advancing season.
        if last_updated_season != 0:
            if year < last_updated_season:
                continue
            if last_updated_season < year:
                cache['Last_Updated_Week'] = 0  # Reset for new season

        # Early exit if fully up to date (prevents unnecessary API calls).
        if last_updated_season == int(current_season) and last_updated_week == current_week:
            break

        year = int(year)
        max_weeks = _get_max_weeks(year, current_season, current_week)

        if year == current_season or year == last_updated_season:
            last_updated_week = cache.get("Last_Updated_Week", 0)
            weeks_to_update = range(last_updated_week + 1, max_weeks + 1)
        else:
            weeks_to_update = range(1, max_weeks + 1)

        if not weeks_to_update:
            continue

        print(f"Updating starters cache for season {year}, weeks: {list(weeks_to_update)}")

        for week in weeks_to_update:
            cache.setdefault(str(year), {})
            cache[str(year)][str(week)] = fetch_starters_for_week(year, week)

            # Advance progress markers (enables resumable incremental updates).
            cache['Last_Updated_Season'] = str(year)
            cache['Last_Updated_Week'] = week
            print(f"  Starters cache updated internally for season {year}, week {week}")

    save_cache(STARTERS_CACHE_FILE, cache)
    cache.pop("Last_Updated_Season", None)
    cache.pop("Last_Updated_Week", None)
    return cache

def _get_max_weeks(season, current_season, current_week):
    """
    Determine maximum playable weeks for a season.

    Rules:
    - Live season -> current_week (capped above).
    - 2019/2020 -> 13 (legacy rule set).
    - Other seasons -> 14 (regular season boundary).

    Returns:
        int: Max week to process for season.
    """
    if season == current_season:
        return current_week
    elif season in [2019, 2020]:
        return 13
    return 14

def fetch_starters_for_week(season, week):
    """
    Build per-manager starter/points map for a given season/week.

    API calls:
        - users
        - rosters
        - matchups/{week}

    Returns:
        dict: real_manager_name -> {player_name: {points, position}, Total_Points}
              Empty dict on API failure.
    """
    league_id = LEAGUE_IDS[int(season)]
    sleeper_response_users = fetch_sleeper_data(f"league/{league_id}/users")
    if sleeper_response_users[1] != 200:
        return {}

    sleeper_response_rosters = fetch_sleeper_data(f"league/{league_id}/rosters")
    if sleeper_response_rosters[1] != 200:
        return {}

    sleeper_response_matchups = fetch_sleeper_data(f"league/{league_id}/matchups/{week}")
    if sleeper_response_matchups[1] != 200:
        return {}

    managers = sleeper_response_users[0]
    week_data = {}
    for manager in managers:
        real_name = USERNAME_TO_REAL_NAME.get(manager['display_name'], "Unknown Manager")

        # 2019 early-week reassignment (historical manual correction).
        if int(season) == 2019 and week < 4 and real_name == "Cody":
            real_name = "Tommy"

        roster_id = get_roster_id(sleeper_response_rosters, manager['user_id'])
        if roster_id is None:
            # Hard-coded correction for a known roster mismatch (2024 Davey).
            if int(season) == 2024 and real_name == "Davey":
                roster_id = 4

        if not roster_id:
            continue  # Skip unresolved roster

        starters_data = get_starters_data(sleeper_response_matchups, roster_id)
        if starters_data:
            week_data[real_name] = starters_data

    return week_data

def get_roster_id(sleeper_response_rosters, user_id):
    """
    Resolve a roster_id for the given user_id.

    Args:
        sleeper_response_rosters (tuple): (payload, status_code)
        user_id (str): Sleeper user identifier.

    Returns:
        int | None: roster_id if found, else None.
    """
    rosters = sleeper_response_rosters[0]
    for roster in rosters:
        if roster['owner_id'] == user_id:
            return roster['roster_id']
    return None

def get_starters_data(sleeper_response_matchups, roster_id):
    """
    Extract starters + total points for one roster/week.

    Filters:
        - Unknown players or positions skipped.
        - Total normalized to 2 decimals.

    Args:
        sleeper_response_matchups (tuple): (payload, status_code)
        roster_id (int): Target roster identifier.

    Returns:
        dict | None: {player_name: {points, position}, Total_Points} or None if not found.
    """
    matchups = sleeper_response_matchups[0]
    for matchup in matchups:
        if matchup['roster_id'] == roster_id:
            manager_data = {"Total_Points": 0.0}
            for player_id in matchup['starters']:
                player_meta = PLAYER_IDS.get(player_id, {})
                player_name = player_meta.get('full_name')
                if not player_name:
                    continue  # Skip unknown player
                player_position = player_meta.get('position')
                if not player_position:
                    continue  # Skip if no position resolved

                player_score = matchup['players_points'].get(player_id, 0)

                manager_data[player_name] = {
                    "points": player_score,
                    "position": player_position,
                    "player_id": player_id
                }
                manager_data["Total_Points"] += player_score

            manager_data["Total_Points"] = float(
                Decimal(manager_data["Total_Points"]).quantize(Decimal('0.01')).normalize()
            )
            return manager_data
    return None
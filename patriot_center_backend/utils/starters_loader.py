import json
import os
from datetime import datetime
from decimal import Decimal
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data
from  patriot_center_backend.constants import LEAGUE_IDS, USERNAME_TO_REAL_NAME
from patriot_center_backend.utils.player_ids_loader import load_player_ids

# Constants
STARTERS_CACHE_FILE = "patriot_center_backend/data/starters_cache.json"
PLAYER_IDS = load_player_ids()


def load_or_update_starters_cache():
    """
    Load starters data from the cache file. If the cache is outdated or doesn't exist,
    fetch only the missing data from the Sleeper API and update the cache.

    Returns:
        dict: The updated starters cache.
    """
    # Load existing cache or initialize a new one
    cache = _load_cache()

    # Dynamically determine the current season and week
    current_season, current_week = _get_current_season_and_week()

    # Get the last updated season and week from the cache
    last_updated_season = int(cache.get("Last_Updated_Season", 0))
    last_updated_week   = cache.get("Last_Updated_Week", 0)

    # Process all years in LEAGUE_IDS
    for year in LEAGUE_IDS.keys():
        if last_updated_season != 0:
            if year < last_updated_season:
                continue
            if last_updated_season < year:
                cache['Last_Updated_Week'] = 0
        
        if last_updated_season == int(current_season) and last_updated_week == current_week:
            break

        year = int(year)  # Ensure year is an integer
        max_weeks = _get_max_weeks(year, current_season, current_week)

        # Determine the range of weeks to update
        if year == current_season or year == last_updated_season:
            last_updated_week = cache.get("Last_Updated_Week", 0)
            weeks_to_update = range(last_updated_week + 1, max_weeks + 1)
        else:
            weeks_to_update = range(1, max_weeks + 1)

        if list(weeks_to_update) == []:
            continue
        
        print(f"Updating cache for season {year}, weeks: {list(weeks_to_update)}")

        # Fetch and update only the missing weeks for the year
        for week in weeks_to_update:
            if str(year) not in cache:
                cache[str(year)] = {}
            cache[str(year)][str(week)] = fetch_starters_for_week(year, week)

            cache['Last_Updated_Season'] = str(year)
            cache['Last_Updated_Week'] = week

            print("  Cache updated for season {}, week {}".format(year, week))

    # # Update the last updated season and week
    # cache["Last_Updated_Season"] = current_season
    # cache["Last_Updated_Week"] = current_week

    # Save the updated cache to the file
    _save_cache(cache)

    # Remove metadata before returning
    cache.pop("Last_Updated_Season", None)
    cache.pop("Last_Updated_Week", None)

    return cache


def _load_cache():
    """
    Load the starters cache from the file, or initialize a new one if the file doesn't exist.

    Returns:
        dict: The loaded or initialized cache.
    """
    if os.path.exists(STARTERS_CACHE_FILE):
        with open(STARTERS_CACHE_FILE, "r") as file:
            return json.load(file)
    else:
        # Initialize the cache with all years
        cache = {"Last_Updated_Season": "0", "Last_Updated_Week": 0}
        for year in LEAGUE_IDS.keys():
            cache[str(year)] = {}
        return cache


def _save_cache(cache):
    """
    Save the starters cache to the file.

    Args:
        cache (dict): The cache data to save.
    """
    with open(STARTERS_CACHE_FILE, "w") as file:
        json.dump(cache, file, indent=4)


def _get_current_season_and_week():
    """
    Fetch the current season and week from the Sleeper API.

    Returns:
        tuple: The current season (int) and the current week (int).
    """
    current_year = datetime.now().year
    league_id = LEAGUE_IDS.get(int(current_year))  # Get the league ID for the current year
    if not league_id:
        raise Exception(f"No league ID found for the current year: {current_year}")
    
    # OFFLINE DEBUGGING, comment out when online
    # return "2025", 10

    sleeper_response_league = fetch_sleeper_data(f"league/{league_id}")
    if sleeper_response_league[1] != 200:
        raise Exception("Failed to fetch league data from Sleeper API")

    league_info = sleeper_response_league[0]
    current_season = int(league_info.get("season"))  # Ensure current_season is an integer
    current_week = league_info.get("settings", {}).get("last_scored_leg", 0)
    if current_week > 14:
        current_week = 14  # Cap at 14 weeks

    return current_season, current_week


def _get_max_weeks(season, current_season, current_week):
    """
    Determine the maximum number of weeks for a given season.

    Args:
        season (int): The season to determine the max weeks for.
        current_season (int): The current season.
        current_week (int): The current week.

    Returns:
        int: The maximum number of weeks for the season.
    """
    if season == current_season:
        return current_week  # Use the current week for the current season
    elif season in [2019, 2020]:
        return 13  # Cap at 13 weeks for 2019 and 2020
    else:
        return 14  # Cap at 14 weeks for other seasons


def fetch_starters_for_week(season, week):
    """
    Fetch starters data for a specific season and week.

    Args:
        season (int): The season to fetch data for.
        week (int): The week to fetch data for.

    Returns:
        dict: The starters data for the given season and week.
    """
    league_id = LEAGUE_IDS[int(season)]
    sleeper_response_users = fetch_sleeper_data(f"league/{league_id}/users")
    if sleeper_response_users[1] != 200:
        return {}  # Return empty data if the API call fails

    managers = sleeper_response_users[0]
    week_data = {}
    for manager in managers:
        real_name = USERNAME_TO_REAL_NAME.get(manager['display_name'], "Unknown Manager")
        
        # Tommy started the 2019 season for 3 weeks before Cody took over
        if int(season) == 2019 and week < 4 and real_name == "Cody":
            real_name = "Tommy"
        
        roster_id = get_roster_id(season, manager['user_id'])
        if roster_id is None:
            # Handle special cases for known roster IDs
            if int(season) == 2024 and real_name == "Davey":
                roster_id = 4
        
        if not roster_id:
            continue

        # Fetch starters for the manager
        starters_data = get_starters_data(league_id, roster_id, week)
        if starters_data:
            week_data[real_name] = starters_data

    return week_data


def get_roster_id(year, user_id):
    """
    Fetch the roster ID for a specific user in a given year.

    Args:
        year (int): The year to fetch the roster ID for.
        user_id (str): The user ID to fetch the roster ID for.

    Returns:
        str: The roster ID, or None if not found.
    """
    league_id = LEAGUE_IDS[int(year)]
    sleeper_response_rosters = fetch_sleeper_data(f"league/{league_id}/rosters")
    if sleeper_response_rosters[1] != 200:
        return None

    rosters = sleeper_response_rosters[0]
    for roster in rosters:
        if roster['owner_id'] == user_id:
            return roster['roster_id']
    return None


def get_starters_data(league_id, roster_id, week):
    """
    Fetch starters data for a specific roster and week.

    Args:
        league_id (str): The league ID.
        roster_id (str): The roster ID.
        week (int): The week to fetch data for.

    Returns:
        dict: The starters data for the given roster and week.
    """
    sleeper_response_matchups = fetch_sleeper_data(f"league/{league_id}/matchups/{week}")
    if sleeper_response_matchups[1] != 200:
        return None

    matchups = sleeper_response_matchups[0]
    for matchup in matchups:
        if matchup['roster_id'] == roster_id:
            manager_data = {"Total_Points": 0}
            for player_id in matchup['starters']:
                player_name = PLAYER_IDS.get(player_id, {}).get('full_name', 'Unknown Player')
                if player_name == 'Unknown Player':
                    continue
                player_score = matchup['players_points'].get(player_id, 0)
                player_position = PLAYER_IDS.get(player_id, {}).get('position', 'Unknown Position')
                if player_position == 'Unknown Position':
                    continue

                # Add player data
                manager_data[player_name] = {
                    "points": player_score,
                    "position": player_position
                }

                # Update total points
                manager_data["Total_Points"] += player_score

            manager_data["Total_Points"] = float(Decimal(manager_data["Total_Points"]).quantize(Decimal('0.01')).normalize())

            return manager_data

    return None

load_or_update_starters_cache()
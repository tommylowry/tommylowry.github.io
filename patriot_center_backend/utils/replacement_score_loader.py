from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.utils.player_ids_loader import load_player_ids
from patriot_center_backend.utils.cache_utils import load_cache, save_cache, get_current_season_and_week

# Constants
REPLACEMENT_SCORE_FILE = "patriot_center_backend/data/replacement_score_cache.json"
PLAYER_IDS = load_player_ids()


def load_or_update_replacement_score_cache():
    """
    Load or update the replacement score cache.

    This function loads the existing replacement score cache from a JSON file.
    If the cache is outdated or missing data, it fetches the missing data from
    the Sleeper API and updates the cache. The cache is saved back to the file
    after updates.

    Returns:
        dict: The updated replacement score cache.
    """
    # Load existing cache or initialize a new one
    cache = load_cache(REPLACEMENT_SCORE_FILE)

    # Dynamically determine the current season and week
    current_season, current_week = get_current_season_and_week()
    if current_week > 18:
        current_week = 18  # Cap the current week at 18 (NFL's maximum regular season weeks)

    # Process all years in LEAGUE_IDS with extra years for replacement score
    years = list(LEAGUE_IDS.keys())
    first_year = min(years)
    # Add the three years prior to the first year in LEAGUE_IDS for historical averages
    years.extend([first_year - 3, first_year - 2, first_year - 1])
    years = sorted(years)

    for year in years:
        # Get the last updated season and week from the cache
        last_updated_season = int(cache.get("Last_Updated_Season", 0))
        last_updated_week = cache.get("Last_Updated_Week", 0)

        # Skip years that are already fully processed
        if last_updated_season != 0:
            if year < last_updated_season:
                continue
            if last_updated_season < year:
                cache["Last_Updated_Week"] = 0  # Reset the week if moving to a new year

        # If the cache is already up-to-date for the current season and week, stop processing
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

        print(f"Updating replacement score cache for season {year}, weeks: {list(weeks_to_update)}")

        # Fetch and update only the missing weeks for the year
        for week in weeks_to_update:
            if str(year) not in cache:
                cache[str(year)] = {}

            # Fetch replacement scores for the week
            cache[str(year)][str(week)] = _fetch_replacement_score_for_week(year, week)

            # Compute the 3-year average if data from three years ago exists
            if str(year - 3) in cache:
                cache[str(year)][str(week)] = _get_three_yr_avg(year, week, cache)

            # Update the metadata for the last updated season and week
            cache["Last_Updated_Season"] = str(year)
            cache["Last_Updated_Week"] = week

            print("  Replacement score cache updated internally for season {}, week {}".format(year, week))

    # Save the updated cache to the file
    save_cache(REPLACEMENT_SCORE_FILE, cache)

    # Remove metadata before returning
    # These fields are used internally for tracking updates but are not part of the final cache returned
    cache.pop("Last_Updated_Season", None)
    cache.pop("Last_Updated_Week", None)

    return cache


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
    elif season <= 2020:
        return 17  # Cap at 17 weeks for seasons 2020 and earlier
    else:
        return 18  # Cap at 18 weeks for other seasons


def _fetch_replacement_score_for_week(season, week):
    """
    Fetch replacement scores for a specific season and week.

    This function retrieves player data for a given season and week from the Sleeper API.
    It calculates replacement scores for each position (QB, RB, WR, TE) and the number of byes.

    Args:
        season (int): The season to fetch data for.
        week (int): The week to fetch data for.

    Returns:
        dict: The replacement scores for the given season and week.
    """
    # Fetch data from the Sleeper API for the given season and week
    sleeper_response_week_data = fetch_sleeper_data(f"stats/nfl/regular/{season}/{week}")
    if sleeper_response_week_data[1] != 200:
        # Raise an exception if the API call fails
        raise Exception(f"Failed to fetch week data from Sleeper API for season {season}, week {week}")
    
    # Initialize the number of byes to 32 (all teams initially assumed to be playing)
    byes = 32
    week_scores = {
        "QB": [],  # List of QB scores for the week
        "RB": [],  # List of RB scores for the week
        "WR": [],  # List of WR scores for the week
        "TE": []   # List of TE scores for the week
    }

    # Extract the data for the week
    week_data = sleeper_response_week_data[0]
    for player_id in week_data:
        # Skip team-level data (e.g., "TEAM_...")
        if "TEAM_" in player_id:
            byes -= 1  # Reduce the number of byes for each team found
            continue
        elif player_id not in PLAYER_IDS:
            # Skip players not found in the PLAYER_IDS mapping
            continue

        # Get player information from PLAYER_IDS
        player_info = PLAYER_IDS[player_id]
        if player_info["position"] in week_scores and "pts_half_ppr" in week_data[player_id]:
            # Add the player's half-PPR points to the appropriate position list
            week_scores[player_info["position"]].append(week_data[player_id]["pts_half_ppr"])

    # Sort scores for each position in descending order
    for position in week_scores:
        week_scores[position].sort(reverse=True)

    # Determine the replacement scores for each position
    # QB13 (13th best QB), RB31 (31st best RB), WR31 (31st best WR), TE13 (13th best TE)
    week_scores["QB"] = week_scores["QB"][12]  # 13th QB
    week_scores["RB"] = week_scores["RB"][30]  # 31st RB
    week_scores["WR"] = week_scores["WR"][30]  # 31st WR
    week_scores["TE"] = week_scores["TE"][12]  # 13th TE

    # Add the final number of byes to the scores
    week_scores["byes"] = byes

    return week_scores


def _get_three_yr_avg(season, week, cache):
    """
    Calculate the three-year average replacement scores for a given season and week.

    This function calculates the three-year average replacement scores for each position
    (QB, RB, WR, TE) based on historical data. It ensures monotonicity, where more byes
    should not lead to lower replacement scores.

    Args:
        season (int): The current season.
        week (int): The current week.
        cache (dict): The replacement score cache containing historical data.

    Returns:
        dict: The updated current week's scores with three-year averages added.
    """
    # Get the current week's scores and the number of byes
    current_week_scores = cache[str(season)][str(week)]
    byes = current_week_scores["byes"]

    # Initialize dictionaries to store scores and averages for each position
    three_yr_season_scores = {}
    three_yr_season_average = {}

    # Prepare structures for each position (QB, RB, WR, TE)
    for current_week_position in current_week_scores:
        if current_week_position == "byes":
            continue  # Skip the "byes" field
        three_yr_season_scores[current_week_position] = {}
        three_yr_season_average[current_week_position] = {}

    # Iterate through the past three years (and the current year)
    for past_year in [season, season - 1, season - 2, season - 3]:
        # Determine the weeks to consider for the past year
        weeks = range(1, 18 if past_year <= 2020 else 19)

        # For the current season, only consider up to the current week
        if past_year == season:
            weeks = range(1, week + 1)

        # For the season three years ago, only consider from the current week onward
        if past_year == season - 3:
            weeks = range(week, 18 if past_year <= 2020 else 19)

        # Process each week in the determined range
        for w in weeks:
            # Skip if the data for the past year or week is missing
            if str(past_year) not in cache or str(w) not in cache[str(past_year)]:
                continue

            # Get the number of byes for the past week
            past_byes = cache[str(past_year)][str(w)]["byes"]

            # Process scores for each position (QB, RB, WR, TE)
            for past_position in three_yr_season_scores:
                # Get the score for the position in the past week
                past_score = cache[str(past_year)][str(w)][past_position]

                # Initialize the list for the bye count if it doesn't exist
                if past_byes not in three_yr_season_scores[past_position]:
                    three_yr_season_scores[past_position][past_byes] = []

                # Append the score to the list for the corresponding bye count
                three_yr_season_scores[past_position][past_byes].append(past_score)

    # Compute the average replacement scores for each position and bye count
    for past_position in three_yr_season_scores:
        for past_byes in three_yr_season_scores[past_position]:
            # Calculate the average score for the position and bye count
            avg = sum(three_yr_season_scores[past_position][past_byes]) / len(
                three_yr_season_scores[past_position][past_byes]
            )
            three_yr_season_average[past_position][past_byes] = avg

    # Ensure monotonicity: more byes should not lead to lower replacement scores
    # This ensures that the replacement scores are non-decreasing as the number of byes increases
    list_of_byes = sorted(three_yr_season_average["QB"].keys())  # Use QB as a reference for bye counts
    for past_position in three_yr_season_average:
        for i in range(len(list_of_byes) - 1, 0, -1):
            # If the score for a higher bye count is greater than the score for a lower bye count,
            # adjust the lower bye count's score to ensure monotonicity
            if three_yr_season_average[past_position][list_of_byes[i]] > three_yr_season_average[past_position][
                list_of_byes[i - 1]
            ]:
                three_yr_season_average[past_position][list_of_byes[i - 1]] = three_yr_season_average[past_position][
                    list_of_byes[i]
                ]

    # Add the three-year averages to the current week's scores
    for past_position in three_yr_season_average:
        new_key = f"{past_position}_3yr_avg"  # Create a new key for the three-year average
        current_week_scores[new_key] = three_yr_season_average[past_position][byes]

    # Return the updated current week's scores with three-year averages added
    return current_week_scores

load_or_update_replacement_score_cache()
"""
Replacement-score cache builder for Patriot Center.

Responsibilities:
- Maintain a JSON cache of per-week replacement-level scores by position.
- Backfill historical seasons and compute 3-year rolling averages keyed by bye counts.
- Persist an incrementally updated cache to disk and expose it to callers.

Notes:
- Uses Sleeper API data (network I/O) via fetch_sleeper_data.
- Seed player metadata via load_player_ids to filter and position players.
- Current season/week is resolved at runtime and weeks are capped by era rules.
- Importing this module triggers a cache warm-up by calling load_or_update_replacement_score_cache().
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from patriot_center_backend.utils.sleeper_api_handler import fetch_json, SleeperAPIError
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.utils.player_ids_loader import load_player_ids
from patriot_center_backend.utils.helpers import get_current_season_and_week, get_max_weeks_for
from patriot_center_backend.utils.config import REPLACEMENT_SCORE_FILE

logger = logging.getLogger(__name__)

def load_or_update_replacement_score_cache(player_ids: Optional[Dict] = None) -> Dict:
    """
    Load or update the replacement score cache in an incremental, resumable fashion.

    Behavior:
    - Loads existing JSON cache (or initializes structure if file missing).
    - Determines current season/week; caps the week at 18 (post-2021 schedule).
    - Iterates seasons: all configured LEAGUE_IDS plus three prior seasons
      (to enable 3-year averages keyed by bye counts).
    - For each season, computes missing weeks only, honoring Last_Updated_* markers.
    - Computes and stores a 3-year average block when data from year-3 is present.
    - Persists the cache and removes internal metadata before returning.

    Side effects:
    - Reads/writes REPLACEMENT_SCORE_FILE.
    - Performs network I/O via Sleeper API (stats endpoint).

    Returns:
        dict: The updated replacement score cache with per-season/week entries.
    """
    # Ensure player metadata is available if not injected by caller
    player_ids = player_ids or load_player_ids()
    # Load cache via manager with schema metadata and atomic writes
    from patriot_center_backend.utils.cache_manager import CacheManager
    years_seed = sorted(list(LEAGUE_IDS.keys()))
    first_year = min(years_seed)
    years_seed.extend([first_year - 3, first_year - 2, first_year - 1])
    years_seed = sorted(years_seed)
    manager = CacheManager(REPLACEMENT_SCORE_FILE, seed_years=years_seed, schema="replacement").load()
    cache = manager.data

    # Dynamically determine the current season and week
    current_season, current_week = get_current_season_and_week()
    if current_week > 18:
        current_week = 18  # Cap the current week at 18 (NFL's maximum regular season weeks)

    # Process all years in LEAGUE_IDS with extra years for replacement score
    years = years_seed

    for year in years:
        # Get the last updated season and week from the cache
        last_updated_season, last_updated_week = manager.get_last_updated()

        # Skip years that are already fully processed
        if last_updated_season != 0:
            if year < last_updated_season:
                continue
            if last_updated_season < year:
                manager.reset_week_progress()  # Reset the week if moving to a new year

        # If the cache is already up-to-date for the current season and week, stop processing
        if last_updated_season == int(current_season) and last_updated_week == current_week:
            break

        year = int(year)  # Ensure year is an integer
        max_weeks = get_max_weeks_for("replacement", year, current_season, current_week)

        # Determine the range of weeks to update
        if year == current_season or year == last_updated_season:
            _, last_updated_week = manager.get_last_updated()
            weeks_to_update = range(last_updated_week + 1, max_weeks + 1)
        else:
            weeks_to_update = range(1, max_weeks + 1)

        if list(weeks_to_update) == []:
            continue

        logger.info("Updating replacement score cache season=%s weeks=%s", year, list(weeks_to_update))

        # Fetch and update only the missing weeks for the year
        for week in weeks_to_update:
            manager.ensure_year(year)
            # Fetch replacement scores for the week
            week_payload = _fetch_replacement_score_for_week(year, week, player_ids)
            # First, write the raw week scores so _get_three_yr_avg can read them from cache
            manager.set_week_data(year, week, week_payload)
            # Refresh local view of cache to reflect the write
            cache = manager.data
            # Compute the 3-year average if data from three years ago exists, then persist updated entry
            if str(year - 3) in cache:
                updated = _get_three_yr_avg(year, week, cache)
                manager.set_week_data(year, week, updated)
            logger.info("Replacement score cache updated season=%s week=%s", year, week)

    # Save the updated cache to the file
    manager.save()

    # Return the cache without metadata
    return manager.strip_metadata_for_return()


def _fetch_replacement_score_for_week(season: int, week: int, player_ids: Dict) -> Dict:
    """
    Fetch replacement scores for a specific season and week.

    This function retrieves player data for a given season and week from the Sleeper API.
    It calculates replacement scores for each position (QB, RB, WR, TE) and the number of byes.

    Algorithm:
    - Pull weekly stats (half-PPR) for all players from Sleeper.
    - Collect positional point lists for QB/RB/WR/TE, ignoring non-rostered players.
    - Determine replacement thresholds: QB13, RB31, WR31, TE13 (descending rank).
    - Count byes using TEAM_ records present in the payload.

    Args:
        season (int): The season to fetch data for.
        week (int): The week to fetch data for.

    Returns:
        dict: The replacement scores for the given season and week, plus 'byes'.

    Raises:
        SleeperAPIError: If the Sleeper API request fails.
    """
    # Will raise SleeperAPIError on failure
    week_data = fetch_json(f"stats/nfl/regular/{season}/{week}")
    
    # Initialize the number of byes to 32 (all teams initially assumed to be playing)
    byes = 32
    week_scores = {
        "QB": [],  # List of QB scores for the week
        "RB": [],  # List of RB scores for the week
        "WR": [],  # List of WR scores for the week
        "TE": []   # List of TE scores for the week
    }

    # Extract the data for the week
    for player_id in week_data:
        # Skip team-level data (e.g., "TEAM_...")
        if "TEAM_" in player_id:
            byes -= 1  # Reduce the number of byes for each team found
            continue
        elif player_id not in player_ids:
            # Skip players not found in the PLAYER_IDS mapping
            continue

        # Get player information from PLAYER_IDS
        player_info = player_ids[player_id]
        if player_info["position"] in week_scores and "pts_half_ppr" in week_data[player_id]:
            # Add the player's half-PPR points to the appropriate position list
            week_scores[player_info["position"]].append(week_data[player_id]["pts_half_ppr"])

    # Safe nth selector for descending-sorted lists
    def nth_desc(lst, idx, fallback=0.0):
        try:
            return lst[idx]
        except (IndexError, TypeError):
            return lst[-1] if lst else fallback

    for position in week_scores:
        week_scores[position].sort(reverse=True)

    # Use safe selector to avoid IndexError on short lists
    # 13th QB, 31st RB/WR, 13th TE by business rule
    week_scores["QB"] = nth_desc(week_scores["QB"], 12, 0.0)
    week_scores["RB"] = nth_desc(week_scores["RB"], 30, 0.0)
    week_scores["WR"] = nth_desc(week_scores["WR"], 30, 0.0)
    week_scores["TE"] = nth_desc(week_scores["TE"], 12, 0.0)

    # Add the final number of byes to the scores
    week_scores["byes"] = byes

    return week_scores


def _get_three_yr_avg(season, week, cache):
    """
    Calculate the three-year average replacement scores for a given season and week.

    This function calculates the three-year average replacement scores for each position
    (QB, RB, WR, TE) based on historical data. It ensures monotonicity, where more byes
    should not lead to lower replacement scores.

    Detailed behavior:
    - Aggregate historical replacement scores across [season, season-1, season-2, season-3].
    - Group scores by bye count to produce bye-aware averages.
    - For the current season, consider weeks up to the current week.
    - For season-3, consider weeks from the current week to the season end.
    - Enforce monotonicity across bye counts by backfilling non-decreasing values.
    - Write each position's "<POS>_3yr_avg" into the current week's record.

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

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    logger.info("Debug run: replacement score loader")
    # player_ids auto-loads when not provided
    data = load_or_update_replacement_score_cache()
    seasons = [s for s in data.keys() if s.isdigit()]
    logger.info("Seasons loaded: %s", seasons)
    if seasons:
        latest = str(max(map(int, seasons)))
        weeks = sorted(data[latest].keys(), key=lambda x: int(x))
        logger.info("Latest season=%s weeks=%s", latest, weeks)
        if weeks:
            w = weeks[-1]
            entry = data[latest][w]
            print(f"Season={latest} Week={w} sample keys:", list(entry.keys()))
            for k in ["QB", "RB", "WR", "TE", "byes"]:
                if k in entry:
                    print(k, "=>", entry[k])
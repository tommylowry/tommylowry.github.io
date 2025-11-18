from patriot_center_backend.utils.replacement_score_loader import load_or_update_replacement_score_cache
from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache
from patriot_center_backend.utils.cache_utils import load_cache, save_cache, get_current_season_and_week
from patriot_center_backend.constants import LEAGUE_IDS

# Constants
REPLACEMENT_SCORES   = load_or_update_replacement_score_cache()
PLAYER_DATA          = load_or_update_starters_cache()
FFWAR_CACHE_FILE     = "patriot_center_backend/data/ffWAR_cache.json"


def load_or_update_ffWAR_cache():
    """
    Load or update the ffWAR cache.

    This function loads the existing ffWAR cache from a JSON file.
    If the cache is outdated or missing data, it fetches the missing data from
    the Sleeper API and updates the cache. The cache is saved back to the file
    after updates.

    Returns:
        dict: The updated ffWAR cache.
    """
    # Load existing cache or initialize a new one
    cache = load_cache(FFWAR_CACHE_FILE)

    # Dynamically determine the current season and week
    current_season, current_week = get_current_season_and_week()
    if current_week > 14:
        current_week = 14  # Cap the current week at 14

    # Process all years in LEAGUE_IDS
    years = list(LEAGUE_IDS.keys())

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

            # Fetch ffWAR for the week
            cache[str(year)][str(week)] = _fetch_ffWAR(year, week)


            # Update the metadata for the last updated season and week
            cache["Last_Updated_Season"] = str(year)
            cache["Last_Updated_Week"] = week

            print("  ffWAR cache updated internally for season {}, week {}".format(year, week))

    # Save the updated cache to the file
    save_cache(FFWAR_CACHE_FILE, cache)

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
    elif season in [2019, 2020]:
        return 13  # Cap at 13 weeks for 2019 and 2020
    else:
        return 14  # Cap at 14 weeks for other seasons

def _fetch_ffWAR(season, week):

    weekly_data = PLAYER_DATA[str(season)][str(week)]

    players = {
        "QB":  {},
        "RB":  {},
        "WR":  {},
        "TE":  {},
        "K":   {},
        "DEF": {}
    }
    
    for manager in weekly_data:
        for position in players:
            
            old_players_position = players[position]
            old_players_position[manager] = {'total_points': weekly_data[manager]['Total_Points'], 'players': {}}
            players[position] = old_players_position
            
        for player in weekly_data[manager]:
            if player == 'Total_Points':
                continue

            position = weekly_data[manager][player]['position']
            players[position][manager]['players'][player] = weekly_data[manager][player]['points']
                

    ffWAR_results = {}
    for position in players:
        if position not in ['QB', 'RB', 'WR', 'TE']:
            continue
        calculated_ffWAR = _calculate_ffWAR_position(players[position], season, week, position)
        for player in calculated_ffWAR:
            ffWAR_results[player] = calculated_ffWAR[player]

    return ffWAR_results

def _calculate_ffWAR_position(scores, season, week, position):
    
    key = f"{position}_3yr_avg"
    replacement_average = REPLACEMENT_SCORES[str(season)][str(week)][key]
    
    
    # get score minus the average
    num_players = 0
    total_position_score = 0.0
    for manager in scores:
        num_players += len(scores[manager]['players'])
        for player in scores[manager]['players']:
            total_position_score += scores[manager]['players'][player]
    
    average_player_score_this_week = total_position_score / num_players


    for manager in scores:

        player_total_for_manager = 0.0
        for player in scores[manager]['players']:
            player_total_for_manager += scores[manager]['players'][player]
        
        if len(scores[manager]['players']) == 0:
            player_average_for_manager = 0
        else:
            player_average_for_manager = player_total_for_manager / len(scores[manager]['players'])

        # total_minus_position = total_points - player_average_for_manager
        scores[manager]['total_minus_position'] = scores[manager]["total_points"] - player_average_for_manager

        # weighted_total_score = total_points - manager_average + position average
        scores[manager]['weighted_total_score'] = scores[manager]["total_points"] - player_average_for_manager  + average_player_score_this_week

    ffWAR_position = {}
    for real_manager in scores:
        for player in scores[real_manager]['players']:
            num_simulated_games = 0
            num_wins   = 0
            player_score = scores[real_manager]['players'][player]

            for manager_playing in scores:
                for manager_opposing in scores:
                    if manager_playing == manager_opposing:
                        continue

                    # score of the opponent
                    simulated_opponent_score = scores[manager_opposing]['weighted_total_score']

                    # score if player was on manager_playing's lineup
                    simulated_player_score = scores[manager_playing]['total_minus_position'] + player_score

                    # score if replacement player was on manager_playing's lineup
                    simulated_replacement_score = scores[manager_playing]['total_minus_position'] + replacement_average
                    
                    # win if player wouldve won and replacement wouldve lost
                    if (simulated_player_score > simulated_opponent_score) and (simulated_replacement_score < simulated_opponent_score):
                        num_wins += 1
                    # loss if player wouldve lost and replacement wouldve won
                    if (simulated_player_score < simulated_opponent_score) and (simulated_replacement_score > simulated_opponent_score):
                        num_wins -= 1
                    
                    num_simulated_games += 1
            
            ffWAR_score = round(num_wins / num_simulated_games, 3)

            ffWAR_position[player] = {
                'ffWAR': ffWAR_score,
                'manager': real_manager,
                'position': position
            }
    
    return ffWAR_position


load_or_update_ffWAR_cache()
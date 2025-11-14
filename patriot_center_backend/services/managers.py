import patriot_center_backend.constants as consts
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data
from patriot_center_backend.utils.player_ids_loader import load_player_ids
import json
from decimal import Decimal

PLAYER_IDS = load_player_ids()


def get_user_id_from_manager(year, manager):
    league_id = consts.LEAGUE_IDS[year]
    sleeper_response_users = fetch_sleeper_data(f"league/{league_id}/users")
    if sleeper_response_users[1] != 200:
        return sleeper_response_users[0], sleeper_response_users[1]
    
    managers = sleeper_response_users[0]
    for mgr in managers:
        real_name = consts.USERNAME_TO_REAL_NAME[mgr['display_name']]
        if real_name == manager:
            return mgr['user_id'], 200
    
    return {"error": "Manager not found"}, 404


def get_roster_id_from_user(year, user_id):
    league_id = consts.LEAGUE_IDS[year]
    sleeper_response_rosters = fetch_sleeper_data(f"league/{league_id}/rosters")
    if sleeper_response_rosters[1] != 200:
        return sleeper_response_rosters[0], sleeper_response_rosters[1]
    
    rosters = sleeper_response_rosters[0]
    for roster in rosters:
        if roster['owner_id'] == user_id:
            return roster['roster_id'], 200
    
    return {"error": "Roster not found"}, 404


def get_yearly_starters(year, roster_id, league_id):
    league_id = consts.LEAGUE_IDS[year]

    # check if the year is currently in season
    sleeper_response_league = fetch_sleeper_data(f"league/{league_id}")
    if sleeper_response_league[1] != 200:
        return sleeper_response_league
    league_info = sleeper_response_league[0]

    # Fetch the starters for the manager and year for each week
    # 13 weeks for 2020 and earlier, 14 weeks for 2021 and later for the regular season
    num_weeks = 14 if  year > 2020 else 13
    if league_info.get('status', '') == 'in_season':
        num_weeks = league_info['settings'].get('last_scored_leg', 0)
    
    data = {}
    for week in range(1, num_weeks + 1):
        sleeper_response_matchups = fetch_sleeper_data(f"league/{league_id}/matchups/{week}")
        if sleeper_response_matchups[1] != 200:
            return sleeper_response_matchups
        
        matchups = sleeper_response_matchups[0]
        for matchup in matchups:
            if matchup['roster_id'] == roster_id:
                for i in range(1, len(matchup['starters'])):
                    player_id = matchup['starters'][i]

                    # Skip empty slots
                    if player_id == "0":
                        continue

                    # Get player details
                    player_name     = PLAYER_IDS.get(player_id, {}).get('full_name', 'Unknown Player')
                    player_score    = matchup['players_points'].get(player_id, 0)
                    player_position = PLAYER_IDS.get(player_id, {}).get('position', 'Unknown Position')
                    if player_name == "Taysom Hill":
                        player_position = "QB/TE"

                    if player_name in data:
                        data[player_name]['total_points'] += player_score
                        data[player_name]['weeks_started'] += 1
                    else:
                        data[player_name] = {
                            'total_points': player_score,
                            'weeks_started': 1, 
                            'position': player_position
                        }
    
    # Before returning, format all total_points to remove trailing zeros
    for player_name, player_data in data.items():
        player_data['total_points'] = float(Decimal(player_data['total_points']).quantize(Decimal('0.01')).normalize())

    return data, 200
                    



def get_starters(year=None, manager=None):

    # If year is None, fetch for all years
    if year is None:
        data = {}
        for yr in consts.LEAGUE_IDS.keys():
            per_year_result = get_starters(yr, manager)
            if per_year_result[1] != 200:
                return per_year_result
            data[yr] = per_year_result[0]
        return data
    


    # If manager is None, fetch for all managers for that year

    # Fetch league ID for the specified year
    league_id = consts.LEAGUE_IDS[year]
    if manager is None:
        
        # Fetch managers for the year specified
        sleeper_response_users = fetch_sleeper_data(f"league/{league_id}/users")
        if sleeper_response_users[1] != 200:
            return sleeper_response_users
        
        data = {}
        managers = sleeper_response_users[0]
        for manager in managers:
            real_name = consts.USERNAME_TO_REAL_NAME[manager['display_name']]
            per_manager_result = get_starters(year, real_name)
            if per_manager_result[1] != 200:
                return per_manager_result
            data[real_name] = per_manager_result[0]
        return data
    


    # If manager and year are specified, fetch starters for that manager and year

    # Get user ID from manager name
    user_id, status_code = get_user_id_from_manager(year, manager)
    if status_code != 200:
        return {"error": "Manager not found"}, status_code
    
    # Get roster ID for the user in the specified year
    roster_id, status_code = get_roster_id_from_user(year, user_id)
    if status_code != 200:
        return {"error": "Roster not found"}, status_code
    
    return get_yearly_starters(year, roster_id, league_id), 200

print(json.dumps(get_starters(2025, "Tommy"), indent = 4))
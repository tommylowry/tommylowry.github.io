import copy

from patriot_center_backend.constants import LEAGUE_IDS, NAME_TO_MANAGER_USERNAME
from patriot_center_backend.services.players import fetch_players, fetch_valid_options_cache

VALID_OPTIONS_CACHE = fetch_valid_options_cache()

def fetch_valid_options(arg1, arg2, arg3):
    
    default_response = {
        "years": list(LEAGUE_IDS.keys()),
        "weeks": list(range(1, 18)),
        "positions": list(["QB", "RB", "WR", "TE", "K", "DEF"]),
        "managers": list(NAME_TO_MANAGER_USERNAME.keys())
    }
    
    year, week, manager, player = _parse_args(arg1, arg2, arg3)

    # If all arguments are None, return all options
    if year == None and week == None and manager == None and player == None:
        return default_response
    
    if year == None and week != None:
        raise ValueError("Week specified without a year.")

    filtered_dict = _filter_year(year, default_response)
    filtered_dict = _filter_week(week, year, filtered_dict) # week needs year
    filtered_dict = _filter_manager(manager, year, week, filtered_dict)
    filtered_dict = _filter_player(player, year, manager, week, filtered_dict)

    return filtered_dict


def _filter_year(year, filtered_dict):
    if year == None:
        return filtered_dict
    
    yearly_lists = VALID_OPTIONS_CACHE.get(str(year), {})

    filtered_dict["weeks"] = _trim_list(filtered_dict["weeks"], list(map(int, yearly_lists.get("weeks", []))))
    filtered_dict["positions"] = _trim_list(filtered_dict["positions"], list(yearly_lists.get("positions", [])))
    filtered_dict["managers"] = _trim_list(filtered_dict["managers"], list(yearly_lists.get("managers", [])))

    return filtered_dict

def _filter_week(week, year, filtered_dict):
    if week == None:
        return filtered_dict
    
    weekly_lists = VALID_OPTIONS_CACHE.get(str(year), {}).get(str(week), {})

    filtered_dict["positions"] = _trim_list(filtered_dict["positions"], list(weekly_lists.get("positions", [])))
    filtered_dict["managers"] = _trim_list(filtered_dict["managers"], list(weekly_lists.get("managers", [])))

    return filtered_dict

def _filter_manager(manager, year, week, filtered_dict):
    if manager == None:
        return filtered_dict
    
    if year != None and week != None:
        filtered_dict["positions"] = _trim_list(filtered_dict["positions"], list(VALID_OPTIONS_CACHE.get(str(year), {}).get(str(week), {}).get(manager, []).get("positions", [])))

    reference_dict = copy.deepcopy(filtered_dict)

    for year_key in reference_dict["years"]:
        yearly_list = VALID_OPTIONS_CACHE.get(str(year_key), {})
        if manager not in yearly_list.get("managers", []):
            filtered_dict["years"].remove(year_key)
    
    # Only one year being evaluated, see what weeks they played that year
    if year != None or len(filtered_dict["years"]) == 1:
        if len(filtered_dict["years"]) == 1:
            year = filtered_dict["years"][0]
        for week_key in reference_dict["weeks"]:
            weekly_lists = VALID_OPTIONS_CACHE.get(str(year), {}).get(str(week_key), {})
            if manager not in weekly_lists.get("managers", []):
                filtered_dict["weeks"].remove(week_key)

    return filtered_dict

def _filter_player(player, year, manager, week, filtered_dict):
    if player == None:
        return filtered_dict
    
    PLAYERS_CACHE = fetch_players()

    position = PLAYERS_CACHE.get(player, {}).get("position", None)
    filtered_dict["positions"] = list([position])
    

    reference_dict = copy.deepcopy(filtered_dict)
    for year_key in reference_dict["years"]:
        yearly_list = VALID_OPTIONS_CACHE.get(str(year_key), {})
        if player not in yearly_list.get("players", []):
            filtered_dict["years"].remove(year_key)

    managers = list()
    years = list()
    weeks = list()
    reference_dict = copy.deepcopy(filtered_dict)

    # Year Specified
    if year != None:
        # Weeks
        for week_key in reference_dict["weeks"]:
            # if player did not play that week when only one year is being evaluated, remove the week
            if player not in VALID_OPTIONS_CACHE.get(str(year), {}).get(str(week_key), {}).get("players", []):
                filtered_dict["weeks"].remove(week_key)
            
            else:
                # Managers
                if manager != None:
                    if player in VALID_OPTIONS_CACHE.get(str(year), {}).get(str(week_key), {}).get(manager, {}).get("players", []):
                        if week_key not in weeks:
                            weeks.append(week_key)

                for manager_key in reference_dict["managers"]:
                    if player in VALID_OPTIONS_CACHE.get(str(year), {}).get(str(week_key), {}).get(manager_key, {}).get("players", []):
                        if week != None:
                            if week == week_key:
                                filtered_dict["managers"] = list([manager_key])
                        else:
                            if manager_key not in managers:
                                managers.append(manager_key)

    # Year Not Specified
    else:
        # Years
        for year_key in reference_dict["years"]:
            if player not in VALID_OPTIONS_CACHE.get(str(year_key), {}).get("players", []):
                filtered_dict["years"].remove(year_key)
                continue
            
            # Weeks
            for week_key in reference_dict["weeks"]:
                # if player did not play that week when only one year is being evaluated, remove the week
                if player not in VALID_OPTIONS_CACHE.get(str(year_key), {}).get(str(week_key), {}).get("players", []) and len(reference_dict.get("years")) == 1:
                    filtered_dict["weeks"].remove(week_key)
                    continue
                
                # Managers
                if manager != None:
                    if player in VALID_OPTIONS_CACHE.get(str(year_key), {}).get(str(week_key), {}).get(manager, {}).get("players", []):
                        if year_key not in years:
                            years.append(year_key)
                            
                
                for manager_key in reference_dict["managers"]:
                    if player in VALID_OPTIONS_CACHE.get(str(year_key), {}).get(str(week_key), {}).get(manager_key, {}).get("players", []):
                        if manager_key not in managers:
                            managers.append(manager_key)
        
        reference_dict = copy.deepcopy(filtered_dict)
        # If the player has only played one year, trim weeks to only those they played in
        if len(years) == 1:
            # Years
            year_key = years[0]

            for week_key in reference_dict["weeks"]:
                # if player did not play that week when only one year is being evaluated, remove the week
                if manager == None:
                    if player not in VALID_OPTIONS_CACHE.get(str(year_key), {}).get(str(week_key), {}).get("players", []):
                        filtered_dict["weeks"].remove(week_key)
                        continue
                else:
                    if player not in VALID_OPTIONS_CACHE.get(str(year_key), {}).get(str(week_key), {}).get(manager, {}).get("players", []):
                        filtered_dict["weeks"].remove(week_key)
                        continue
    
    filtered_dict["weeks"] = _trim_list(filtered_dict["weeks"], weeks)
    filtered_dict["years"] = _trim_list(filtered_dict["years"], years)
    filtered_dict["managers"] = _trim_list(filtered_dict["managers"], managers)
    
    return filtered_dict



def _trim_list(original_list, keep_list):
    if keep_list == []:
        return original_list
    
    reference_list = original_list.copy()
    for item in reference_list:
        if item not in keep_list:
            original_list.remove(item)
    return original_list

def _parse_args(arg1, arg2, arg3):
    """
    Parse and validate input arguments for fetching valid options.

    Args:
        arg1, arg2, arg3, arg4: Input arguments that may represent year, week, position, manager, or player.

    Returns:
        tuple: Parsed values for year, week, position, manager, player.
    """
    year     = None
    week     = None
    manager  = None
    player   = None

    players = fetch_players()

    args = [arg1, arg2, arg3]
    for arg in args:
        if arg == None:
            continue

        if isinstance(arg, int) or arg.isnumeric():
            arg = int(arg)
            # Check if arg is a valid year
            if arg in LEAGUE_IDS:
                if year != None:
                    raise ValueError("Multiple year arguments provided.")
                year = arg
            
            # Check if arg is a valid week
            elif 1 <= arg <= 17:
                if week != None:
                    raise ValueError("Multiple week arguments provided.")
                week = arg
            else:
                raise ValueError(f"Unrecognized integer argument: {arg}")
        
        else:
            # Check if arg is a manager
            if arg in NAME_TO_MANAGER_USERNAME:
                if manager != None:
                    raise ValueError("Multiple manager arguments provided.")
                manager = arg
            
            # Check if arg is a player
            elif arg.replace("_", " ").replace("%27", "'") in players:
                if player != None:
                    raise ValueError("Multiple player arguments provided.")
                player = arg.replace("_", " ").replace("%27", "'") # Normalize player name
            else:
                raise ValueError(f"Unrecognized argument: {arg}")

    return year, week, manager, player
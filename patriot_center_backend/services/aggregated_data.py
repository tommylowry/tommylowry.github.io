"""
Aggregation utilities over starters data.

Exposes helpers to:
- Aggregate totals across weeks/seasons for a manager by player.
- Aggregate totals across weeks/seasons for a player by manager.

Notes:
- Results are simple dicts suitable for JSON responses.
- Totals are rounded to two decimals via Decimal normalization.
"""
from patriot_center_backend.utils.ffWAR_loader import load_or_update_ffWAR_cache
from patriot_center_backend.services.managers import fetch_starters
from decimal import Decimal

ffWAR_cache = load_or_update_ffWAR_cache()


def fetch_aggregated_players(manager=None, season=None, week=None):
    """
    Fetch aggregated player data for a specific manager.

    Behavior:
    - Retrieves the slice of starters for the manager (optionally constrained).
    - Aggregates points and games started per player.
    - Preserves player position from the raw entries.

    Args:
        manager (str): The manager to fetch data for.
        season (int, optional): The season to filter by. Defaults to None.
        week (int, optional): The week to filter by. Defaults to None.

    Returns:
        dict: Aggregated player data with total points, games started, and position.
              Returns {} if no data is found for the filters.
    """
    raw_dict = fetch_starters(manager=manager, season=season, week=week)
    players_dict_to_return = {}

    # No matching data -> return empty aggregation
    if not raw_dict:
        return players_dict_to_return

    # Traverse season->week->manager->players to accumulate totals
    for year, weeks in raw_dict.items():
        for week, managers in weeks.items():
            for manager, manager_data in managers.items():
                for player, player_data in manager_data.items():
                    if player == "Total_Points":
                        continue

                    ffWAR_score = fetch_ffWAR_for_player(player, season=year, week=week)
                    player_data['ffWAR'] = ffWAR_score

                    if player in players_dict_to_return:
                        _update_player_data(players_dict_to_return, player, player_data)
                    else:
                        _initialize_player_data(players_dict_to_return, player, player_data)

    return players_dict_to_return


def fetch_aggregated_managers(player, season=None, week=None):
    """
    Fetch aggregated manager data for a specific player.

    Behavior:
    - Retrieves all starters (optionally constrained by season/week).
    - Aggregates points and games started per manager for the given player.

    Args:
        player (str): The player to fetch data for.
        season (int, optional): The season to filter by. Defaults to None.
        week (int, optional): The week to filter by. Defaults to None.

    Returns:
        dict: Aggregated manager data with total points, games started, and position.
              Returns {} if the player does not appear in the selection.
    """
    raw_dict = fetch_starters(season=season, week=week)
    managers_dict_to_return = {}

    for year, weeks in raw_dict.items():
        for week, managers in weeks.items():
            for manager, manager_data in managers.items():
                if player in manager_data:
                    raw_item = manager_data[player]

                    ffWAR_score = fetch_ffWAR_for_player(player, season=year, week=week)
                    raw_item['ffWAR'] = ffWAR_score

                    if manager in managers_dict_to_return:
                        _update_manager_data(managers_dict_to_return, manager, raw_item)
                    else:
                        _initialize_manager_data(managers_dict_to_return, manager, raw_item)

    return managers_dict_to_return

def fetch_ffWAR_for_player(player, season=None, week=None):
    """
    Fetch the ffWAR value for a specific player, season, and week.

    Args:
        player (str): The player to fetch ffWAR for.
        season (int, optional): The season to filter by. Defaults to None.
        week (int, optional): The week to filter by. Defaults to None.

    Returns:
        float: The ffWAR value for the player in the specified season and week.
               Returns 0.0 if no data is found.
    """
    if season is None or week is None:
        return 0.0

    season_str = str(season)
    week_str = str(week)

    if season_str in ffWAR_cache and week_str in ffWAR_cache[season_str]:
        week_data = ffWAR_cache[season_str][week_str]
        if player in week_data and "ffWAR" in week_data[player]:
            return week_data[player]["ffWAR"]

    return 0.0

def _update_player_data(players_dict, player, player_data):
    """
    Update the aggregated data for an existing player.

    Args:
        players_dict (dict): The dictionary containing aggregated player data.
        player (str): The player to update.
        player_data (dict): The raw data for the player.
    """
    player_dict_item = players_dict[player]
    player_dict_item['total_points'] += player_data['points']
    player_dict_item['ffWAR'] += player_data['ffWAR']
    player_dict_item['num_games_started'] += 1

    # Round the total points to two decimal places for consistent presentation
    player_dict_item["total_points"] = float(
        Decimal(player_dict_item["total_points"]).quantize(Decimal('0.01')).normalize()
    )

    player_dict_item["ffWAR"] = float(
        Decimal(player_dict_item["ffWAR"]).quantize(Decimal('0.001')).normalize()
    )

    players_dict[player] = player_dict_item


def _initialize_player_data(players_dict, player, player_data):
    """
    Initialize the aggregated data for a new player.

    Args:
        players_dict (dict): The dictionary containing aggregated player data.
        player (str): The player to initialize.
        player_data (dict): The raw data for the player.
    """
    # Capture initial totals and the stable position field
    players_dict[player] = {
        "total_points": player_data['points'],
        "num_games_started": 1,
        'ffWAR': player_data['ffWAR'],
        "position": player_data['position']
    }


def _update_manager_data(managers_dict, manager, raw_item):
    """
    Update the aggregated data for an existing manager.

    Args:
        managers_dict (dict): The dictionary containing aggregated manager data.
        manager (str): The manager to update.
        raw_item (dict): The raw data for the manager.
    """
    manager_dict_item = managers_dict[manager]
    manager_dict_item['total_points'] += raw_item['points']
    manager_dict_item['ffWAR'] += raw_item['ffWAR']
    manager_dict_item['num_games_started'] += 1

    # Round the total points to two decimal places for consistent presentation
    manager_dict_item["total_points"] = float(
        Decimal(manager_dict_item["total_points"]).quantize(Decimal('0.01')).normalize()
    )

    manager_dict_item["ffWAR"] = float(
        Decimal(manager_dict_item["ffWAR"]).quantize(Decimal('0.001')).normalize()
    )

    managers_dict[manager] = manager_dict_item


def _initialize_manager_data(managers_dict, manager, raw_item):
    """
    Initialize the aggregated data for a new manager.

    Args:
        managers_dict (dict): The dictionary containing aggregated manager data.
        manager (str): The manager to initialize.
        raw_item (dict): The raw data for the manager.
    """
    # Capture initial totals and the player's position for that manager
    managers_dict[manager] = {
        "total_points": raw_item['points'],
        "num_games_started": 1,
        'ffWAR': raw_item['ffWAR'],
        "position": raw_item['position']
    }

fetch_aggregated_players()
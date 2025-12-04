"""
Aggregation utilities over starters data.

Exposes helpers to:
- Aggregate totals across weeks/seasons for a manager by player.
- Aggregate totals across weeks/seasons for a player by manager.

Notes:
- Results are simple dicts suitable for JSON responses.
- Totals are rounded to two decimals via Decimal normalization (ffWAR to 3).
"""
from patriot_center_backend.utils.ffWAR_loader import load_or_update_ffWAR_cache
from patriot_center_backend.services.managers import fetch_starters
from decimal import Decimal

ffWAR_cache = load_or_update_ffWAR_cache()

def fetch_aggregated_players(manager=None, season=None, week=None):
    """
    Aggregate player metrics for a given manager.

    Traverses nested structure and collates:
    - total_points (rounded per update)
    - num_games_started
    - cumulative ffWAR (rounded per update)
    - position (taken from first occurrence)

    Args:
        manager (str | None): Target manager. Required for meaningful output.
        season (int | None): Optional season restriction.
        week (int | None): Optional week restriction.

    Returns:
        dict: {player: {total_points, num_games_started, ffWAR, position}}
    """
    raw_dict = fetch_starters(manager=manager, season=season, week=week)
    players_dict_to_return = {}

    if not raw_dict:
        return players_dict_to_return

    for year, weeks in raw_dict.items():
        for week, managers in weeks.items():
            for manager, manager_data in managers.items():
                for player, player_data in manager_data.items():
                    if player == "Total_Points":
                        # Skip aggregate row inside source structure
                        continue
                    ffWAR_score = fetch_ffWAR_for_player(player, season=year, week=week)
                    player_data['ffWAR'] = ffWAR_score

                    if player in players_dict_to_return:
                        _update_player_data(players_dict_to_return, player, player_data, manager, year)
                    else:
                        _initialize_player_data(players_dict_to_return, player, player_data, manager, year)

    return players_dict_to_return

def fetch_aggregated_managers(player, season=None, week=None):
    """
    Aggregate manager metrics for appearances of a given player.

    Args:
        player (str): Player name key.
        season (int | None): Optional season restriction.
        week (int | None): Optional week restriction.

    Returns:
        dict: {manager: {total_points, num_games_started, ffWAR, position}}
              Empty if player not present in filtered slice.
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
                        _update_manager_data(managers_dict_to_return, manager, raw_item, player, year)
                    else:
                        _initialize_manager_data(managers_dict_to_return, manager, raw_item, player, year)

    return managers_dict_to_return

def fetch_ffWAR_for_player(player, season=None, week=None):
    """
    Lookup ffWAR for a player at a specific season/week granularity.

    Returns zero if season/week not provided or absent from cache.

    Args:
        player (str): Player identifier.
        season (int | None): Season for lookup.
        week (int | None): Week for lookup.

    Returns:
        float: ffWAR value (0.0 if unavailable).
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

def _update_player_data(players_dict, player, player_data, manager, year):
    """
    Increment aggregation totals for an existing player entry.

    Rounds:
        total_points -> 2 decimals
        ffWAR -> 3 decimals
    """
    player_dict_item = players_dict[player]
    player_dict_item['total_points'] += player_data['points']
    player_dict_item['ffWAR'] += player_data['ffWAR']
    player_dict_item['num_games_started'] += 1

    player_dict_item["total_points"] = float(
        Decimal(player_dict_item["total_points"]).quantize(Decimal('0.01')).normalize()
    )
    player_dict_item["ffWAR"] = float(
        Decimal(player_dict_item["ffWAR"]).quantize(Decimal('0.001')).normalize()
    )
    players_dict[player] = player_dict_item

    # Handle playoff placement if present
    if "placement" in player_data:
        players_dict = _handle_playoff_placement(players_dict, player, manager, year, player_data["placement"])
    
    return players_dict

def _initialize_player_data(players_dict, player, player_data, manager, year):
    """
    Create initial aggregation record for a player.
    """

    if player_data['player_id'].isnumeric():
        player_image_endpoint = f"https://sleepercdn.com/content/nfl/players/{player_data['player_id']}.jpg"
    else:
        player_image_endpoint = f"https://sleepercdn.com/images/team_logos/nfl/{player_data['player_id'].lower()}.jpg"

    players_dict[player] = {
        "total_points": player_data['points'],
        "num_games_started": 1,
        'ffWAR': player_data['ffWAR'],
        "position": player_data['position'],
        "player_image_endpoint": player_image_endpoint
    }

    # Handle playoff placement if present
    if "placement" in player_data:
        players_dict = _handle_playoff_placement(players_dict, player, manager, year, player_data["placement"])
    
    return players_dict

def _update_manager_data(managers_dict, manager, raw_item, player, year):
    """
    Increment aggregation totals for an existing manager entry.

    Rounds:
        total_points -> 2 decimals
        ffWAR -> 3 decimals
    """
    manager_dict_item = managers_dict[manager]
    manager_dict_item['total_points'] += raw_item['points']
    manager_dict_item['ffWAR'] += raw_item['ffWAR']
    manager_dict_item['num_games_started'] += 1

    manager_dict_item["total_points"] = float(
        Decimal(manager_dict_item["total_points"]).quantize(Decimal('0.01')).normalize()
    )
    manager_dict_item["ffWAR"] = float(
        Decimal(manager_dict_item["ffWAR"]).quantize(Decimal('0.001')).normalize()
    )
    managers_dict[manager] = manager_dict_item

    # Handle playoff placement if present
    if "placement" in raw_item:
        managers_dict = _handle_playoff_placement(managers_dict, manager, player, year, raw_item["placement"])
    
    return managers_dict

def _initialize_manager_data(managers_dict, manager, raw_item, player, year):
    """
    Create initial aggregation record for a manager with a single player appearance.
    """
    
    if raw_item['player_id'].isnumeric():
        player_image_endpoint = f"https://sleepercdn.com/content/nfl/players/{raw_item['player_id']}.jpg"
    else:
        player_image_endpoint = f"https://sleepercdn.com/images/team_logos/nfl/{raw_item['player_id'].lower()}.png"

    managers_dict[manager] = {
        "total_points": raw_item['points'],
        "num_games_started": 1,
        'ffWAR': raw_item['ffWAR'],
        "position": raw_item['position'],
        "player_image_endpoint": player_image_endpoint
    }

    # Handle playoff placement if present
    if "placement" in raw_item:
        managers_dict = _handle_playoff_placement(managers_dict, manager, player, year, raw_item["placement"])
    
    return managers_dict

def _handle_playoff_placement(aggregation_dict, primary_item, secondary_item, year, placement):
    """
    Update playoff placement info in aggregation dict.
    """
    if "playoff_placement" not in aggregation_dict[primary_item]:
        aggregation_dict[primary_item]["playoff_placement"] = {
            secondary_item: {
                year: placement
            }
        }
    elif secondary_item not in aggregation_dict[primary_item]["playoff_placement"]:
        aggregation_dict[primary_item]["playoff_placement"][secondary_item] = {year: placement}
    elif year not in aggregation_dict[primary_item]["playoff_placement"][secondary_item]:
        aggregation_dict[primary_item]["playoff_placement"][secondary_item][year] = placement
    
    return aggregation_dict
from patriot_center_backend.services.managers import fetch_starters
from decimal import Decimal

def fetch_aggregated_players(manager, season=None, week=None):
    raw_dict = fetch_starters(manager, season = season, week = week)

    players_dict_to_return = {}

    if raw_dict == {}:
        return players_dict_to_return

    for year in raw_dict:
        for week in raw_dict[year]:
            for player in raw_dict[year][week][manager]:
                if player == "Total_Points":
                    continue
                
                raw_item = raw_dict[year][week][manager][player]
                if player in players_dict_to_return:
                    player_dict_item = players_dict_to_return[player]
                    player_dict_item['total_points']      += raw_item['points']
                    player_dict_item['num_games_started'] += 1
                    
                    # Round the decimal
                    player_dict_item["total_points"] = float(Decimal(player_dict_item["total_points"]).quantize(Decimal('0.01')).normalize())

                    players_dict_to_return[player] = player_dict_item
                    
                else:
                    players_dict_to_return[player] = {
                        "total_points":      raw_item['points'],
                        "num_games_started": 1,
                        "position":          raw_item['position']
                    }
    
    return players_dict_to_return

def fetch_aggregated_managers(player, season=None, week=None):
    raw_dict = fetch_starters(season=season, week=week)

    managers_dict_to_return = {}

    for year in raw_dict:
        for week in raw_dict[year]:
            for manager in raw_dict[year][week]:
                for eval_player in raw_dict[year][week][manager]:
                    if eval_player == player:

                        raw_item = raw_dict[year][week][manager][player]
                        if manager in managers_dict_to_return:
                            manager_dict_item = managers_dict_to_return[manager]
                            manager_dict_item['total_points']      += raw_item['points']
                            manager_dict_item['num_games_started'] += 1
                            
                            # Round the decimal
                            manager_dict_item["total_points"] = float(Decimal(manager_dict_item["total_points"]).quantize(Decimal('0.01')).normalize())

                            managers_dict_to_return[manager] = manager_dict_item

                        else:
                            managers_dict_to_return[manager] = {
                                "total_points":      raw_item['points'],
                                "num_games_started": 1,
                                "position":          raw_item['position']
                            }
    
    return managers_dict_to_return

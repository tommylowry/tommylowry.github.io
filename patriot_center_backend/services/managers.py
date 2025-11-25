"""
Service helpers for querying starters cache.

Provides filtered views over the starters cache by:
- season and/or week
- manager (optionally constrained by season/week)

Notes:
- STARTERS_CACHE is loaded at import time to serve requests quickly.
- Returns empty dicts on missing seasons/weeks/managers instead of raising.
"""
from utils.player_ids_loader import load_player_ids
from utils.starters_loader import load_or_update_starters_cache

PLAYER_IDS = load_player_ids()
STARTERS_CACHE = load_or_update_starters_cache()

def fetch_starters(manager=None, season=None, week=None):
    """
    Public entry point for retrieving starters slices.

    Dispatches to either season/week filtering or manager-centric filtering.

    Args:
        manager (str | None): Manager username (raw key in cache).
        season (int | None): Season identifier.
        week (int | None): Week number (1–17).

    Returns:
        dict: Nested dict shaped like STARTERS_CACHE subset.
    """
    if season is None and week is None and manager is None:
        # Full cache passthrough for unfiltered requests
        return STARTERS_CACHE

    if manager is None:
        return _filter_by_season_and_week(season, week)

    return _filter_by_manager(manager, season, week)

def _filter_by_season_and_week(season, week):
    """
    Slice cache down to season and optionally week.

    Args:
        season (int): Season identifier (must exist in cache).
        week (int | None): Week number to narrow further.

    Returns:
        dict: {season: {...}} or {season: {week: {...}}} or {} if not found.
    """
    season_str = str(season)
    if season_str not in STARTERS_CACHE:
        return {}

    if week is not None:
        week_str = str(week)
        if week_str not in STARTERS_CACHE[season_str]:
            return {}
        return {
            season_str: {
                week_str: STARTERS_CACHE[season_str][week_str]
            }
        }

    return {season_str: STARTERS_CACHE[season_str]}

def _filter_by_manager(manager, season, week):
    """
    Extract only data for one manager, optionally restricted by season/week.

    Iterates through cache (skipping metadata keys) and collects matches.

    Args:
        manager (str): Manager username.
        season (int | None): Season constraint.
        week (int | None): Week constraint.

    Returns:
        dict: Nested dict {season: {week: {manager: players}}}
    """
    filtered_data = {}

    for season_key, weeks in STARTERS_CACHE.items():
        # Skip metadata sentinel fields
        if season_key in ["Last_Updated_Season", "Last_Updated_Week"]:
            continue
        if season is not None and str(season) != season_key:
            continue

        for week_key, starters in weeks.items():
            if week is not None and str(week) != week_key:
                continue
            if manager in starters:
                # Initialize nested containers only when needed
                filtered_data.setdefault(season_key, {}).setdefault(week_key, {})
                filtered_data[season_key][week_key][manager] = starters[manager]

    return filtered_data
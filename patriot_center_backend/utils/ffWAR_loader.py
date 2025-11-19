"""Utilities to build and maintain the ffWAR cache for Patriot Center.

This module:
- Loads supporting caches at import time (replacement scores and starters).
- Determines the current fantasy season/week.
- Loads an ffWAR cache JSON file and incrementally updates it by year/week.
- Persists the updated cache back to disk.

Notes:
- Import-time cache loading is intentional for shared reuse and performance,
  but it has side effects (I/O and potential network calls).
- Weeks are capped at 14 to exclude playoff/post-season data from ffWAR.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Dict, Optional

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None

from patriot_center_backend.utils.replacement_score_loader import load_or_update_replacement_score_cache
from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache
from patriot_center_backend.utils.helpers import get_current_season_and_week, get_max_weeks_for
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.utils.config import FFWAR_CACHE_FILE

# Constants
# Load and memoize supporting datasets at import time so subsequent calls can reuse them.
# Be aware: these may perform network and disk I/O during import.
REPLACEMENT_SCORES   = load_or_update_replacement_score_cache()
PLAYER_DATA          = load_or_update_starters_cache()
# File path for persisted ffWAR cache across runs.

logger = logging.getLogger(__name__)

def load_or_update_ffWAR_cache(
    replacement_scores: Optional[Dict] = None,
    starters_cache: Optional[Dict] = None,
) -> Dict:
    """
    Load or update the ffWAR cache incrementally and persist it to disk.

    Behavior:
    - Loads the existing ffWAR cache JSON (or initializes an empty cache).
    - Determinescurrent season and wdwee | None at 14 toid playoffs.
   ds t | Nonerough a)ed league years and updates missing data
      based on the cache's Last_Updated_Season/Week markers.
    - Saves the cache back to FFWAR_CACHE_FILE after updates.

    Side effects:
    - Reads from and writes to FFWAR_CACHE_FILE.
    - May perform network calls to the Sleeper API via upstream utilities.

    Returns:
        dict: The in-memory ffWAR cache after applying any updates.
    """
    # Resolve dependencies (lazy getters) if not provided
    if replacement_scores is None or starters_cache is None:
        from patriot_center_backend.utils import get_replacement_score_cache, get_starters_cache
        replacement_scores = replacement_scores or get_replacement_score_cache()
        starters_cache = starters_cache or get_starters_cache()
    # Load cache via manager with schema metadata and atomic writes
    from patriot_center_backend.utils.cache_manager import CacheManager
    from patriot_center_backend.constants import LEAGUE_IDS as _YEARS_SRC
    manager = CacheManager(FFWAR_CACHE_FILE, seed_years=list(_YEARS_SRC.keys()), schema="ffwar").load()
    cache = manager.data

    current_season, current_week = get_current_season_and_week()
    if current_week > 14:
        current_week = 14

    years = list(LEAGUE_IDS.keys())
    for year in years:
        last_updated_season, last_updated_week = manager.get_last_updated()
        if last_updated_season != 0:
            if year < last_updated_season:
                continue
            if last_updated_season < year:
                manager.reset_week_progress()
        if last_updated_season == int(current_season) and last_updated_week == current_week:
            break
        year = int(year)
        max_weeks = get_max_weeks_for("ffwar", year, current_season, current_week)
        if year == current_season or year == last_updated_season:
            _, last_updated_week = manager.get_last_updated()
            weeks_to_update = range(last_updated_week + 1, max_weeks + 1)
        else:
            weeks_to_update = range(1, max_weeks + 1)
        if list(weeks_to_update) == []:
            continue
        logger.info("Updating ffWAR cache season=%s weeks=%s", year, list(weeks_to_update))
        for week in weeks_to_update:
            manager.ensure_year(year)
            # Fetch ffWAR for the week
            week_payload = _fetch_ffWAR(year, week, starters_cache, replacement_scores)
            # Set data and advance progress markers
            manager.set_week_data(year, week, week_payload)
            logger.info("ffWAR cache updated season=%s week=%s", year, week)
    manager.save()
    return manager.strip_metadata_for_return()

def _fetch_ffWAR(season: int, week: int, starters_cache: Dict, replacement_scores: Dict) -> Dict:
    """
    Build per-player ffWAR entries for a specific season/week across positions.
    """
    weekly_data = starters_cache[str(season)][str(week)]

    players = {
        "QB":  {},
        "RB":  {},
        "WR":  {},
        "TE":  {},
        "K":   {},
        "DEF": {}
    }

    # Initialize manager containers per position
    for manager in weekly_data:
        for pos in players:
            players[pos].setdefault(manager, {
                "players": {},
                # Store raw total points; original logic will derive weighted_total_score later
                "total_points": float(weekly_data[manager]["Total_Points"])
            })
        # Populate player entries
        for pname, pdata in weekly_data[manager].items():
            if pname == "Total_Points":
                continue
            pos = pdata["position"]
            players[pos][manager]["players"][pname] = float(pdata["points"])

    ffWAR_results: Dict[str, Dict] = {}
    for pos in ["QB", "RB", "WR", "TE"]:
        calculated = _calculate_ffWAR_position(players[pos], season, week, pos, replacement_scores)
        ffWAR_results.update(calculated)

    return ffWAR_results

def _calculate_ffWAR_position(
    scores: Dict,
    season: int,
    week: int,
    position: str,
    replacement_scores: Dict
) -> Dict:
    """
    Original ffWAR calculation logic (restored).
    - Adjusts each manager's total by replacing their position-specific player average with the global positional average.
    - Simulates every manager vs every opponent with player vs replacement baseline.
    """
    key = f"{position}_3yr_avg"
    replacement_average = replacement_scores[str(season)][str(week)][key]

    # Aggregate totals to compute global average player score for this position
    total_position_score = 0.0
    num_players = 0
    for mgr in scores:
        for player_name, player_score in scores[mgr]["players"].items():
            total_position_score += float(player_score)
            num_players += 1

    average_player_score_this_week = (total_position_score / num_players) if num_players else 0.0

    # Derive per-manager averages and adjusted totals
    for mgr in scores:
        player_total_for_manager = sum(float(v) for v in scores[mgr]["players"].values())
        count_players = len(scores[mgr]["players"])
        player_average_for_manager = player_total_for_manager / count_players if count_players else 0.0

        # total_minus_position = total_points - manager's position average
        scores[mgr]["total_minus_position"] = scores[mgr]["total_points"] - player_average_for_manager

        # weighted_total_score = total_points - manager_average + global position average
        scores[mgr]["weighted_total_score"] = (
            scores[mgr]["total_points"] - player_average_for_manager + average_player_score_this_week
        )

    ffWAR_position: Dict[str, Dict] = {}

    # Double loop simulation (original semantics)
    for real_manager in scores:
        for player_name, player_score in scores[real_manager]["players"].items():
            num_simulated_games = 0
            num_wins = 0
            player_score_f = float(player_score)

            for manager_playing in scores:
                for manager_opposing in scores:
                    if manager_playing == manager_opposing:
                        continue

                    simulated_opponent_score = scores[manager_opposing]["weighted_total_score"]

                    simulated_player_score = scores[manager_playing]["total_minus_position"] + player_score_f
                    simulated_replacement_score = scores[manager_playing]["total_minus_position"] + replacement_average

                    # Win if player beats opponent and replacement would lose
                    if (simulated_player_score > simulated_opponent_score) and (
                        simulated_replacement_score < simulated_opponent_score
                    ):
                        num_wins += 1
                    # Loss if player loses but replacement would win
                    if (simulated_player_score < simulated_opponent_score) and (
                        simulated_replacement_score > simulated_opponent_score
                    ):
                        num_wins -= 1

                    num_simulated_games += 1

            ffWAR_score = round(num_wins / num_simulated_games, 3) if num_simulated_games else 0.0
            ffWAR_position[player_name] = {
                "ffWAR": ffWAR_score,
                "manager": real_manager,
                "position": position,
            }

    return ffWAR_position

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    logger.info("Debug run: ffWAR loader")
    data = load_or_update_ffWAR_cache()
    seasons = [s for s in data.keys() if s.isdigit()]
    logger.info("Seasons loaded: %s", seasons)
    if seasons:
        latest = str(max(map(int, seasons)))
        weeks = sorted(data[latest].keys(), key=lambda x: int(x))
        logger.info("Latest season=%s weeks=%s", latest, weeks)
        if weeks:
            w = weeks[-1]
            players = list(data[latest][w].items())[:5]
            print(f"Season={latest} Week={w} sample ffWAR entries:")
            for name, entry in players:
                print(name, entry)
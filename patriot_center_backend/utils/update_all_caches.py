"""Batch updater for Patriot Center caches.

Responsibilities:
- Coordinate warming/updating of dependent caches with a single call.
- Delegate to per-cache loaders for incremental updates.

Side effects:
- Disk I/O and possible network requests via delegated utilities.
"""
import argparse
import logging
from patriot_center_backend.utils import (
    get_starters_cache,
    get_replacement_score_cache,
    get_ffwar_cache,
    warm_all_caches,
)
from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache
from patriot_center_backend.utils.replacement_score_loader import load_or_update_replacement_score_cache


def update_all_caches():
    """
    Update all caches (starters and replacement scores).

    Behavior:
    - Invokes the incremental updaters for starters and replacement scores.
    - Returns a dict containing both in-memory cache snapshots.

    Side effects:
    - May perform network I/O (Sleeper API) and disk I/O (cache files).

    Returns:
        dict: {
            "starters_cache": dict,
            "replacement_score_cache": dict
        }
    """
    # Warm/update starters cache; underlying function is incremental/resumable
    starters_cache = load_or_update_starters_cache()
    # Warm/update replacement score cache; also incremental/resumable
    replacement_score_cache = load_or_update_replacement_score_cache()
    return {
        "starters_cache": starters_cache,
        "replacement_score_cache": replacement_score_cache,
    }
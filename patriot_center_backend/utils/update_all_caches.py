"""Batch updater for Patriot Center caches.

Responsibilities:
- Coordinate warming/updating of dependent caches with a single call.
- Delegate to per-cache loaders for incremental updates.

Side effects:
- Disk I/O and possible network requests via delegated utilities.
"""
from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache
from patriot_center_backend.utils.replacement_score_loader import load_or_update_replacement_score_cache
from patriot_center_backend.utils.ffWAR_loader import load_or_update_ffWAR_cache


def update_all_caches():
    """
    Update all caches (starters and replacement scores).

    Behavior:
    - Invokes the incremental updaters for starters, replacement scores, and ffWAR.
    - Returns a dict containing both in-memory cache snapshots.

    Side effects:
    - May perform network I/O (Sleeper API) and disk I/O (cache files).

    Returns:
        dict: {
            "starters_cache": dict,
            "replacement_score_cache": dict
            "ffWAR_cache": dict
        }
    """
    # Warm/update starters cache; underlying function is incremental/resumable
    starters_cache = load_or_update_starters_cache()
    # Warm/update replacement score cache; also incremental/resumable
    replacement_score_cache = load_or_update_replacement_score_cache()
    # Warm/update ffWAR cache; also incremental/resumable
    ffWAR_cache = load_or_update_ffWAR_cache()
    
    return {
        "starters_cache": starters_cache,
        "replacement_score_cache": replacement_score_cache,
        "ffWAR_cache": ffWAR_cache
    }
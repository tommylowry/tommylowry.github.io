"""Batch updater for Patriot Center caches.

Responsibilities:
- Coordinate warming/updating of dependent caches with a single call.
- Delegates to per-cache loaders which are incremental/resumable.

Side effects:
- Disk I/O and network requests via delegated utilities.
"""
from utils.starters_loader import load_or_update_starters_cache
from utils.replacement_score_loader import load_or_update_replacement_score_cache
from utils.ffWAR_loader import load_or_update_ffWAR_cache


def update_all_caches():
    """
    Update all caches (starters, replacement scores, ffWAR) in one call.

    Returns:
        dict: Snapshot of the three updated in-memory caches.
    """
    # Warm/update starters cache (incremental)
    starters_cache = load_or_update_starters_cache()
    # Warm/update replacement score cache (includes 3yr averages)
    replacement_score_cache = load_or_update_replacement_score_cache()
    # Warm/update ffWAR cache (simulation-based)
    ffWAR_cache = load_or_update_ffWAR_cache()
    # Single consolidated return object for orchestration layers
    return {
        "starters_cache": starters_cache,
        "replacement_score_cache": replacement_score_cache,
        "ffWAR_cache": ffWAR_cache
    }
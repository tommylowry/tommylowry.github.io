"""
Utilities package initializer.

Goals:
- Avoid import-time side effects (no automatic cache updates on import).
- Expose lazy, memoized getters for heavy caches.
- Provide explicit bootstrap helpers to warm caches when desired.

Notes:
- Downstream modules that currently warm caches at import will still do so when imported.
  Subsequent refactors should remove those import-time calls to fully realize lazy behavior.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import threading
import importlib
# blank line between stdlib and local imports kept intentionally; __init__ should avoid heavy imports

# Thread-safe singletons for heavy caches
_starters_cache_lock = threading.Lock()
_replacement_cache_lock = threading.Lock()
_ffwar_cache_lock = threading.Lock()

_starters_cache: Optional[Dict[str, Any]] = None
_replacement_score_cache: Optional[Dict[str, Any]] = None
_ffwar_cache: Optional[Dict[str, Any]] = None


def get_starters_cache(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Lazily load and memoize the starters cache.

    Args:
        force_refresh: If True, re-fetch and overwrite the memoized cache.

    Returns:
        dict: Starters cache.
    """
    global _starters_cache
    if _starters_cache is None or force_refresh:
        with _starters_cache_lock:
            if _starters_cache is None or force_refresh:
                # Local import to defer any import-time side effects
                module = importlib.import_module("patriot_center_backend.utils.starters_loader")
                _starters_cache = module.load_or_update_starters_cache()
    return _starters_cache


def get_replacement_score_cache(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Lazily load and memoize the replacement score cache.

    Args:
        force_refresh: If True, re-fetch and overwrite the memoized cache.

    Returns:
        dict: Replacement score cache.
    """
    global _replacement_score_cache
    if _replacement_score_cache is None or force_refresh:
        with _replacement_cache_lock:
            if _replacement_score_cache is None or force_refresh:
                module = importlib.import_module("patriot_center_backend.utils.replacement_score_loader")
                _replacement_score_cache = module.load_or_update_replacement_score_cache()
    return _replacement_score_cache


def get_ffwar_cache(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Lazily load and memoize the ffWAR cache.

    Args:
        force_refresh: If True, re-fetch and overwrite the memoized cache.

    Returns:
        dict: ffWAR cache.
    """
    global _ffwar_cache
    if _ffwar_cache is None or force_refresh:
        with _ffwar_cache_lock:
            if _ffwar_cache is None or force_refresh:
                module = importlib.import_module("patriot_center_backend.utils.ffWAR_loader")
                _ffwar_cache = module.load_or_update_ffWAR_cache()
    return _ffwar_cache


def warm_all_caches(force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Explicitly warm all caches.

    Args:
        force_refresh: If True, forces refresh of all caches.

    Returns:
        dict: Snapshot of all warmed caches.
    """
    return {
        "starters_cache": get_starters_cache(force_refresh=force_refresh),
        "replacement_score_cache": get_replacement_score_cache(force_refresh=force_refresh),
        "ffwar_cache": get_ffwar_cache(force_refresh=force_refresh),
    }


def clear_caches() -> None:
    """
    Clear in-memory memoized caches. Does not touch on-disk cache files.
    """
    global _starters_cache, _replacement_score_cache, _ffwar_cache
    with _starters_cache_lock, _replacement_cache_lock, _ffwar_cache_lock:
        _starters_cache = None
        _replacement_score_cache = None
        _ffwar_cache = None

# Remove CLI from __init__ to avoid side effects and circular imports.

__all__ = [
    "get_starters_cache",
    "get_replacement_score_cache",
    "get_ffwar_cache",
    "warm_all_caches",
    "clear_caches",
]
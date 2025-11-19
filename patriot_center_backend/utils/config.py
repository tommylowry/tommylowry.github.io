from __future__ import annotations

# Back-compat shim so existing imports keep working.
from .config_paths import (  # noqa: F401
    BASE_DIR,
    DATA_DIR,
    PLAYER_IDS_FILE,
    STARTERS_CACHE_FILE,
    REPLACEMENT_SCORE_FILE,
    FFWAR_CACHE_FILE,
    API_RATE_LIMIT,
    MAX_PLAYER_IDS_AGE_DAYS,
)
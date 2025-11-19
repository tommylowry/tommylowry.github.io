from __future__ import annotations

import os
from pathlib import Path

# Optional app config loader (patriot_center_backend/config/config.json)
try:
    from patriot_center_backend.config import load_app_config
except Exception:
    def load_app_config() -> dict:
        return {}

# Base dir of the package
BASE_DIR = Path(__file__).resolve().parents[1]

# Load optional JSON config
_cfg = load_app_config() or {}

# Data dir: env override > config.json > package default "data"
_default_data = BASE_DIR / _cfg.get("data_dir", "data")
DATA_DIR = Path(os.environ.get("PATRIOT_CENTER_DATA_DIR", str(_default_data))).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Cache file paths
PLAYER_IDS_FILE = DATA_DIR / "player_ids.json"
STARTERS_CACHE_FILE = DATA_DIR / "starters_cache.json"
REPLACEMENT_SCORE_FILE = DATA_DIR / "replacement_score_cache.json"
FFWAR_CACHE_FILE = DATA_DIR / "ffWAR_cache.json"

# Tunables
API_RATE_LIMIT = float(os.environ.get("PATRIOT_CENTER_RATE_LIMIT", _cfg.get("api_rate_limit_req_per_sec", 5)))
MAX_PLAYER_IDS_AGE_DAYS = int(_cfg.get("max_player_ids_age_days", 7))
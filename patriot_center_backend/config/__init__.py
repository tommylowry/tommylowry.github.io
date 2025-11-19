from __future__ import annotations
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"

def load_app_config() -> dict:
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r") as f:
            return json.load(f)
    return {}
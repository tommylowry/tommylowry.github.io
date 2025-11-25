from pathlib import Path
from typing import Any, Dict
import yaml 


def _load_scoring_settings() -> Dict[str, Any]:
    """
    Load scoring_settings.yml into a plain dict.
    """
    scoring_path = Path.cwd() / "config" / "scoring_settings.yml"
    with scoring_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}

def _map_sleeper_keys(scoring_settings: Dict[str, Any]) -> Dict[str, str]:
    """
    Create a mapping from scoring settings keys to Sleeper API stat keys.

    Args:
        scoring_settings (dict): Scoring settings dictionary.

    Returns:
        dict: Mapping from scoring settings keys to Sleeper stat keys.
    """
    mapping = {}
    for position, stats in scoring_settings.get("positions", {}).items():
        for stat_key, stat_info in stats.items():
            sleeper_key = stat_info.get("sleeper_key")
            if sleeper_key:
                mapping[stat_key] = sleeper_key
    return mapping
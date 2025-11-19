# New file: schema types and validators for caches
from __future__ import annotations
from typing import Any, Dict
from numbers import Number

META_KEYS = {"Last_Updated_Season", "Last_Updated_Week", "schema_version", "created_at", "updated_at"}

def validate_starters_cache(data: Dict[str, Any]) -> None:
    for k, v in data.items():
        if k in META_KEYS:
            continue
        if not isinstance(v, dict):
            raise ValueError(f"Starters cache season {k} must be dict")
        for wk, wkval in v.items():
            if not isinstance(wkval, dict):
                raise ValueError(f"Starters cache week {k}/{wk} must be dict")
            if "Total_Points" not in wkval and len(wkval) > 0:
                # Some weeks may be empty; tolerate that
                pass
            for name, entry in wkval.items():
                if name == "Total_Points":
                    if not isinstance(entry, Number):
                        raise ValueError(f"Total_Points must be numeric at {k}/{wk}")
                    continue
                if not isinstance(entry, dict):
                    raise ValueError(f"Player entry must be dict at {k}/{wk}/{name}")
                if "points" in entry and not isinstance(entry["points"], Number):
                    raise ValueError(f"points must be numeric at {k}/{wk}/{name}")
                if "position" in entry and not isinstance(entry["position"], str):
                    raise ValueError(f"position must be str at {k}/{wk}/{name}")

def validate_replacement_cache(data: Dict[str, Any]) -> None:
    for k, v in data.items():
        if k in META_KEYS:
            continue
        if not isinstance(v, dict):
            raise ValueError(f"Replacement cache season {k} must be dict")
        for wk, wkval in v.items():
            if not isinstance(wkval, dict):
                raise ValueError(f"Replacement cache week {k}/{wk} must be dict")
            # Core keys expected
            for pos in ("QB", "RB", "WR", "TE"):
                if pos in wkval and not isinstance(wkval[pos], Number):
                    raise ValueError(f"{pos} must be numeric at {k}/{wk}")
            if "byes" in wkval and not isinstance(wkval["byes"], int):
                raise ValueError(f"byes must be int at {k}/{wk}")
            # Optional 3yr averages
            for pos in ("QB", "RB", "WR", "TE"):
                key = f"{pos}_3yr_avg"
                if key in wkval and not isinstance(wkval[key], Number):
                    raise ValueError(f"{key} must be numeric at {k}/{wk}")

def validate_ffwar_cache(data: Dict[str, Any]) -> None:
    for k, v in data.items():
        if k in META_KEYS:
            continue
        if not isinstance(v, dict):
            raise ValueError(f"ffWAR cache season {k} must be dict")
        for wk, wkval in v.items():
            if not isinstance(wkval, dict):
                raise ValueError(f"ffWAR cache week {k}/{wk} must be dict")
            for pid, entry in wkval.items():
                if not isinstance(entry, dict):
                    raise ValueError(f"Entry must be dict at {k}/{wk}/{pid}")
                if "ffwar" in entry and not isinstance(entry["ffwar"], Number):
                    raise ValueError(f"ffWAR must be numeric at {k}/{wk}/{pid}")
                if "manager" in entry and not isinstance(entry["manager"], str):
                    raise ValueError(f"manager must be str at {k}/{wk}/{pid}")
                if "position" in entry and not isinstance(entry["position"], str):
                    raise ValueError(f"position must be str at {k}/{wk}/{pid}")

__all__ = [
    "validate_starters_cache",
    "validate_replacement_cache",
    "validate_ffwar_cache",
]
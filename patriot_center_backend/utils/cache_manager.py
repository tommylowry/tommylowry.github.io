from __future__ import annotations

"""
Centralized cache manager for JSON caches with:
- schema_version, created_at, updated_at metadata
- progress markers (Last_Updated_Season/Week)
- atomic writes with backup and POSIX locks
- seeding of per-season containers
"""

import json
import os
import shutil
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    import fcntl  # POSIX file locks
except ImportError:  # pragma: no cover
    fcntl = None

from patriot_center_backend.utils.cache_schemas import (
    validate_ffwar_cache,
    validate_replacement_cache,
    validate_starters_cache,
)


@dataclass
class CacheManager:
    file_path: str
    seed_years: List[int] = field(default_factory=list)
    schema_version: int = 1
    schema: Optional[str] = None  # one of {"starters","replacement","ffwar"}

    def __post_init__(self):
        self._path = Path(self.file_path)
        self._data: Dict[str, Any] = {}
        self._lock_path = self._path.with_suffix(self._path.suffix + ".lock")
        self._dirty: bool = False

    @contextmanager
    def _file_lock(self, timeout: float = 10.0, poll: float = 0.05):
        """
        Cross-process exclusive file lock using a sidecar .lock file (POSIX).
        Falls back to a no-op if fcntl is unavailable.
        """
        if not fcntl:
            yield
            return
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._lock_path, "a+") as lf:
            start = time.monotonic()
            while True:
                try:
                    fcntl.flock(lf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() - start > timeout:
                        raise TimeoutError(f"Timed out acquiring lock for {self._path}")
                    time.sleep(poll)
            try:
                yield
            finally:
                try:
                    fcntl.flock(lf.fileno(), fcntl.LOCK_UN)
                except Exception:
                    pass

    def _validator(self) -> Optional[Callable[[Dict[str, Any]], None]]:
        if self.schema == "starters":
            return validate_starters_cache
        if self.schema == "replacement":
            return validate_replacement_cache
        if self.schema == "ffwar":
            return validate_ffwar_cache
        return None

    @property
    def data(self) -> Dict[str, Any]:
        return self._data

    def load(self) -> "CacheManager":
        if self._path.exists():
            with self._file_lock():
                try:
                    with open(self._path, "r") as f:
                        self._data = json.load(f)
                except json.JSONDecodeError:
                    # Fallback to .bak if current file is corrupted
                    bak = self._path.with_suffix(self._path.suffix + ".bak")
                    if bak.exists():
                        with open(bak, "r") as f:
                            self._data = json.load(f)
                    else:
                        raise
        else:
            self._data = {
                "schema_version": self.schema_version,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "Last_Updated_Season": "0",
                "Last_Updated_Week": 0,
            }

        # Backfill metadata if upgrading older files
        if "schema_version" not in self._data:
            self._data["schema_version"] = self.schema_version
        if "created_at" not in self._data:
            self._data["created_at"] = datetime.utcnow().isoformat()
        if "updated_at" not in self._data:
            self._data["updated_at"] = datetime.utcnow().isoformat()
        if "Last_Updated_Season" not in self._data:
            self._data["Last_Updated_Season"] = "0"
        if "Last_Updated_Week" not in self._data:
            self._data["Last_Updated_Week"] = 0

        # Ensure seed years exist
        for y in self.seed_years:
            self.ensure_year(y)
        # Validate after load/backfill
        v = self._validator()
        if v is not None:
            v(self._data)

        self._dirty = False  # freshly loaded state
        return self

    def ensure_year(self, year: int) -> None:
        key = str(int(year))
        if key not in self._data:
            self._data[key] = {}
            self._dirty = True

    def get_last_updated(self) -> tuple[int, int]:
        season = int(self._data.get("Last_Updated_Season", "0"))
        week = int(self._data.get("Last_Updated_Week", 0))
        return season, week

    def reset_week_progress(self) -> None:
        if self._data.get("Last_Updated_Week", 0) != 0:
            self._data["Last_Updated_Week"] = 0
            self._dirty = True

    def set_last_updated(self, season: int, week: int) -> None:
        if (
            self._data.get("Last_Updated_Season") != str(int(season))
            or self._data.get("Last_Updated_Week") != int(week)
        ):
            self._data["Last_Updated_Season"] = str(int(season))
            self._data["Last_Updated_Week"] = int(week)
            self._dirty = True

    def set_week_data(self, season: int, week: int, value: Any) -> None:
        self.ensure_year(season)
        s_key, w_key = str(int(season)), str(int(week))
        old = self._data.get(s_key, {}).get(w_key)
        if old != value:
            self._data[s_key][w_key] = value
            self._dirty = True
        self.set_last_updated(season, week)

    def save(self) -> None:
        # Skip write if nothing changed
        if not self._dirty and self._path.exists():
            return
        # Update timestamp and write atomically
        self._data["updated_at"] = datetime.utcnow().isoformat()
        # Validate before save
        v = self._validator()
        if v is not None:
            v(self._data)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        dirpath = str(self._path.parent)
        with self._file_lock():
            # Create backup before replace if file exists
            if self._path.exists():
                try:
                    shutil.copy2(self._path, self._path.with_suffix(self._path.suffix + ".bak"))
                except Exception:
                    pass
            with tempfile.NamedTemporaryFile("w", delete=False, dir=dirpath, prefix=".tmp_", suffix=".json") as tmp:
                json.dump(self._data, tmp, indent=4)
                tmp.flush()
                os.fsync(tmp.fileno())
                tmp_name = tmp.name
            os.replace(tmp_name, self._path)
        self._dirty = False

    def strip_metadata_for_return(self) -> Dict[str, Any]:
        # Return a copy without internal metadata fields
        result = {k: v for k, v in self._data.items() if k not in {
            "Last_Updated_Season", "Last_Updated_Week", "schema_version", "created_at", "updated_at"
        }}
        return result
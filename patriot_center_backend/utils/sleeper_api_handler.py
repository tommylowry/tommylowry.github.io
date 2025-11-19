from __future__ import annotations
"""Thin HTTP client for Sleeper API.

Provides a single helper to fetch JSON from Sleeper endpoints, normalizing
success/error responses for upstream utilities.
"""
import os, threading, time
from typing import Any, Dict, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import patriot_center_backend.constants as consts
from patriot_center_backend.utils.config_paths import API_RATE_LIMIT

class SleeperAPIError(Exception):
    """Typed error for Sleeper API failures."""
    def __init__(self, message: str, status_code: int = 0, url: str = ""):
        super().__init__(message); self.status_code = status_code; self.url = url

class _RateLimiter:
    """Very small rate limiter: enforce a minimum interval between requests."""
    def __init__(self, min_interval_sec: float = None):
        if min_interval_sec is not None:
            self._min = min_interval_sec
        else:
            self._min = 1.0 / API_RATE_LIMIT if API_RATE_LIMIT > 0 else 0.2
        self._lock = threading.Lock(); self._last = 0.0
    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            wait = self._min - (now - self._last)
            if wait > 0: time.sleep(wait)
            self._last = time.monotonic()

_limiter = _RateLimiter()
_session = requests.Session()
_session.headers.update({"Accept": "application/json"})
_retry = Retry(
    total=3,
    backoff_factor=0.3,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset(["GET"])
)
_adapter = HTTPAdapter(max_retries=_retry)
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)

def fetch_json(endpoint: str, timeout: float = 10.0) -> Union[Dict[str, Any], list]:
    """
    Fetch JSON from a Sleeper API endpoint with retry/backoff and rate limiting.

    Args:
        endpoint: Endpoint path appended to base URL (e.g., "league/{id}").
        timeout: Per-request timeout in seconds.

    Returns:
        Parsed JSON payload (dict or list).

    Raises:
        SleeperAPIError: On HTTP errors, timeouts, or JSON parsing failures.
    """
    url = f"{consts.SLEEPER_API_URL}/{endpoint}"
    _limiter.acquire()
    try:
        resp = _session.get(url, timeout=timeout)
    except requests.RequestException as e:
        raise SleeperAPIError(f"Request failed: {e}", url=url) from e
    if resp.status_code != 200:
        raise SleeperAPIError(
            f"Non-200 response {resp.status_code} for {url}",
            status_code=resp.status_code,
            url=url,
        )
    try:
        return resp.json()
    except ValueError as e:
        raise SleeperAPIError(f"Invalid JSON from {url}", status_code=resp.status_code, url=url) from e

def fetch_sleeper_data(endpoint: str):
    """
    Backwards-compatible wrapper around fetch_json for existing callers.
    Returns (payload, 200) on success; ({"error": str}, 500) on failure.
    """
    try:
        return fetch_json(endpoint), 200
    except SleeperAPIError as e:
        return {"error": str(e)}, 500
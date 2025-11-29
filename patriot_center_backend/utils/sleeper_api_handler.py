"""Thin HTTP client for Sleeper API.

Provides a single helper to fetch JSON from Sleeper endpoints, normalizing
success/error responses for upstream utilities.
"""
import requests
import patriot_center_backend.constants as consts

def fetch_sleeper_data(endpoint: str):
    """
    Perform GET request to Sleeper API and return parsed JSON.

    Args:
        endpoint (str): Relative endpoint appended to base URL.

    Returns:
        (payload, status_code):
            payload -> dict/list on success, {"error": str} on failure.
            status_code -> 200 on success else 500.

    Notes:
        - Caller handles non-200 cases (no exceptions raised here).
        - Timeout/backoff not implemented (simple thin client).
    """
    # Construct full URL from configured base and endpoint
    url = f"{consts.SLEEPER_API_URL}/{endpoint}"
    
    try:
        response = requests.get(url)
    except:
        # Standardized error wrapper for upstream consumers
        error_string = f"Failed to fetch data from Sleeper API with call to {url}"
        return {"error": error_string}, 500
    
    if response.status_code != 200:
        # Standardized error wrapper for upstream consumers
        error_string = f"Failed to fetch data from Sleeper API with call to {url}"
        return {"error": error_string}, 500

    # Return parsed JSON along with success status
    return response.json(), 200
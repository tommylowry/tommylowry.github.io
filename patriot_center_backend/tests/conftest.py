"""
Pytest fixtures for backend tests.

Provides reusable test data, mocks, and fixtures for all test modules.
"""
import json
import pytest
import tempfile
import os
from decimal import Decimal
from unittest.mock import Mock, patch


@pytest.fixture
def mock_player_ids():
    """Sample player IDs data for testing."""
    return {
        "7547": {
            "full_name": "Amon-Ra St. Brown",
            "age": 24,
            "years_exp": 3,
            "college": "USC",
            "team": "DET",
            "depth_chart_position": "1",
            "fantasy_positions": ["WR"],
            "position": "WR",
            "number": 14
        },
        "4866": {
            "full_name": "Travis Kelce",
            "age": 34,
            "years_exp": 11,
            "college": "Cincinnati",
            "team": "KC",
            "depth_chart_position": "1",
            "fantasy_positions": ["TE"],
            "position": "TE",
            "number": 87
        },
        "KC": {
            "full_name": "Kansas City Chiefs",
            "position": "DEF",
            "team": "KC",
            "fantasy_positions": ["DEF"]
        }
    }


@pytest.fixture
def mock_starters_cache():
    """Sample starters cache data."""
    return {
        "2024": {
            "1": {
                "Tommy": {
                    "Amon-Ra_St._Brown": {
                        "points": 18.5,
                        "position": "WR",
                        "player_id": "7547"
                    },
                    "Total_Points": 125.3
                },
                "Mike": {
                    "Travis_Kelce": {
                        "points": 12.3,
                        "position": "TE",
                        "player_id": "4866"
                    },
                    "Total_Points": 110.2
                }
            }
        },
        "Last_Updated_Season": "2024",
        "Last_Updated_Week": "1"
    }


@pytest.fixture
def mock_replacement_scores():
    """Sample replacement score data with correct structure."""
    return {
        "Last_Updated_Season": "2024",
        "Last_Updated_Week": 14,
        "2024": {
            "1": {
                "byes": 0,
                "2024_scoring": {
                    "QB": 15.2,
                    "RB": 8.5,
                    "WR": 7.3,
                    "TE": 5.1,
                    "K": 7.0,
                    "DEF": 5.5
                },
                "2025_scoring": {
                    "QB": 15.1,
                    "RB": 8.4,
                    "WR": 7.2,
                    "TE": 5.0,
                    "K": 6.9,
                    "DEF": 5.4
                }
            },
            "5": {
                "byes": 4,
                "2024_scoring": {
                    "QB": 14.8,
                    "RB": 8.0,
                    "WR": 6.8,
                    "TE": 4.7,
                    "K": 6.6,
                    "DEF": 5.1
                }
            }
        }
    }


@pytest.fixture
def mock_ffwar_cache():
    """Sample ffWAR cache data."""
    return {
        "2024": {
            "1": {
                "Amon-Ra_St._Brown": {
                    "ffWAR": 2.345,
                    "position": "WR"
                },
                "Travis_Kelce": {
                    "ffWAR": 1.234,
                    "position": "TE"
                }
            }
        },
        "Last_Updated_Season": "2024",
        "Last_Updated_Week": "1"
    }


@pytest.fixture
def mock_sleeper_api_responses():
    """Common Sleeper API response structures."""
    return {
        "league": {
            "league_id": "123456789",
            "name": "Test League",
            "season": "2024",
            "settings": {
                "playoff_week_start": 15
            }
        },
        "users": [
            {
                "user_id": "user1",
                "display_name": "Tommy",
                "metadata": {"team_name": "Team Tommy"}
            }
        ],
        "rosters": [
            {
                "roster_id": 1,
                "owner_id": "user1",
                "players": ["7547", "4866"]
            }
        ],
        "matchups": [
            {
                "roster_id": 1,
                "starters": ["7547"],
                "players_points": {"7547": 18.5}
            }
        ]
    }


@pytest.fixture
def temp_cache_file():
    """Create a temporary cache file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
        json.dump({}, f)

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def flask_app():
    """Create a Flask app instance for testing."""
    # Import here to avoid circular imports
    from patriot_center_backend.app import app

    app.config['TESTING'] = True
    app.config['DEBUG'] = False

    yield app


@pytest.fixture
def flask_client(flask_app):
    """Create a Flask test client."""
    return flask_app.test_client()


@pytest.fixture
def mock_fetch_sleeper_data():
    """Mock the fetch_sleeper_data function."""
    with patch('patriot_center_backend.utils.sleeper_api_handler.fetch_sleeper_data') as mock:
        mock.return_value = ({"test": "data"}, 200)
        yield mock


@pytest.fixture
def mock_load_cache():
    """Mock the load_cache function."""
    with patch('patriot_center_backend.utils.cache_utils.load_cache') as mock:
        mock.return_value = {}
        yield mock


@pytest.fixture
def mock_save_cache():
    """Mock the save_cache function."""
    with patch('patriot_center_backend.utils.cache_utils.save_cache') as mock:
        yield mock


@pytest.fixture
def mock_current_season_week():
    """Mock get_current_season_and_week to return fixed values."""
    with patch('patriot_center_backend.utils.cache_utils.get_current_season_and_week') as mock:
        mock.return_value = (2024, 14)
        yield mock


@pytest.fixture
def sample_aggregated_manager_data():
    """Sample aggregated manager data for testing."""
    return {
        "Tommy": {
            "total_points": 245.67,
            "num_games_started": 5,
            "ffWAR": 12.345,
            "position": "WR",
            "player_image_endpoint": "https://sleepercdn.com/content/nfl/players/7547.jpg"
        },
        "Mike": {
            "total_points": 123.45,
            "num_games_started": 3,
            "ffWAR": -2.145,
            "position": "WR",
            "player_image_endpoint": "https://sleepercdn.com/content/nfl/players/7547.jpg"
        }
    }


@pytest.fixture
def sample_aggregated_player_data():
    """Sample aggregated player data for testing."""
    return {
        "Amon-Ra_St._Brown": {
            "total_points": 245.67,
            "num_games_started": 12,
            "ffWAR": 24.567,
            "position": "WR",
            "player_image_endpoint": "https://sleepercdn.com/content/nfl/players/7547.jpg"
        },
        "Travis_Kelce": {
            "total_points": 189.34,
            "num_games_started": 10,
            "ffWAR": 15.234,
            "position": "TE",
            "player_image_endpoint": "https://sleepercdn.com/content/nfl/players/4866.jpg"
        }
    }

@ pytest.fixture
def sample_defenses_in_sleeper_data():
    """Sample Sleeper data including all team defenses."""
    return {
        "7547": {
            "full_name": "Amon-Ra St. Brown",
            "team": "DET",
            "position": "WR"
        },
        "4866": {
            "full_name": "Travis Kelce",
            "team": "KC",
            "position": "TE"
        },
        "ARI": {
            "full_name": "Arizona Cardinals",
            "team": "ARI",
            "position": "DEF"
        },
        "ATL": {
            "full_name": "Atlanta Falcons",
            "team": "ATL",
            "position": "DEF"
        },
        "BAL": {
            "full_name": "Baltimore Ravens",
            "team": "BAL",
            "position": "DEF"
        },
        "1667": {
            "full_name": "Some Other Player",
            "team": "XYZ",
            "position": "RB"
        }
    }
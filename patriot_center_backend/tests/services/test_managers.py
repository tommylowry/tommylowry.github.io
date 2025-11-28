"""
Unit tests for services/managers.py - Starters cache filtering.
"""
import pytest
from unittest.mock import patch


class TestFetchStarters:
    """Test fetch_starters main entry point."""

    @patch('services.managers.STARTERS_CACHE')
    def test_returns_full_cache_when_no_filters(self, mock_cache):
        """Test returns entire cache when all parameters are None."""
        from services.managers import fetch_starters

        mock_cache_data = {
            "2024": {
                "1": {"Tommy": {}, "Mike": {}}
            },
            "Last_Updated_Season": "2024",
            "Last_Updated_Week": "1"
        }

        with patch('services.managers.STARTERS_CACHE', mock_cache_data):
            result = fetch_starters(manager=None, season=None, week=None)

        # Should return the entire cache
        assert result == mock_cache_data

    @patch('services.managers._filter_by_season_and_week')
    def test_calls_filter_by_season_when_no_manager(self, mock_filter):
        """Test dispatches to season/week filter when manager is None."""
        from services.managers import fetch_starters

        mock_filter.return_value = {"2024": {"1": {}}}

        result = fetch_starters(manager=None, season=2024, week=1)

        # Should call _filter_by_season_and_week
        mock_filter.assert_called_once_with(2024, 1)
        assert result == {"2024": {"1": {}}}

    @patch('services.managers._filter_by_manager')
    def test_calls_filter_by_manager_when_manager_provided(self, mock_filter):
        """Test dispatches to manager filter when manager is provided."""
        from services.managers import fetch_starters

        mock_filter.return_value = {"2024": {"1": {"Tommy": {}}}}

        result = fetch_starters(manager="Tommy", season=2024, week=1)

        # Should call _filter_by_manager
        mock_filter.assert_called_once_with("Tommy", 2024, 1)
        assert result == {"2024": {"1": {"Tommy": {}}}}


class TestFilterBySeasonAndWeek:
    """Test _filter_by_season_and_week helper function."""

    @patch('services.managers.STARTERS_CACHE')
    def test_returns_empty_when_season_not_found(self, mock_cache):
        """Test returns {} when season doesn't exist in cache."""
        from services.managers import _filter_by_season_and_week

        mock_cache_data = {
            "2024": {"1": {"Tommy": {}}}
        }

        with patch('services.managers.STARTERS_CACHE', mock_cache_data):
            result = _filter_by_season_and_week(season=2099, week=None)

        assert result == {}

    @patch('services.managers.STARTERS_CACHE')
    def test_returns_empty_when_week_not_found(self, mock_cache):
        """Test returns {} when week doesn't exist for the season."""
        from services.managers import _filter_by_season_and_week

        mock_cache_data = {
            "2024": {
                "1": {"Tommy": {}},
                "2": {"Mike": {}}
            }
        }

        with patch('services.managers.STARTERS_CACHE', mock_cache_data):
            result = _filter_by_season_and_week(season=2024, week=99)

        assert result == {}

    @patch('services.managers.STARTERS_CACHE')
    def test_returns_single_week_when_week_provided(self, mock_cache):
        """Test returns only specified week when week parameter provided."""
        from services.managers import _filter_by_season_and_week

        mock_cache_data = {
            "2024": {
                "1": {"Tommy": {"Player1": {}}},
                "2": {"Tommy": {"Player2": {}}}
            }
        }

        with patch('services.managers.STARTERS_CACHE', mock_cache_data):
            result = _filter_by_season_and_week(season=2024, week=1)

        # Should only return week 1
        assert "2024" in result
        assert "1" in result["2024"]
        assert "2" not in result["2024"]
        assert result["2024"]["1"] == {"Tommy": {"Player1": {}}}

    @patch('services.managers.STARTERS_CACHE')
    def test_returns_all_weeks_when_no_week_provided(self, mock_cache):
        """Test returns all weeks for season when week is None."""
        from services.managers import _filter_by_season_and_week

        mock_cache_data = {
            "2024": {
                "1": {"Tommy": {}},
                "2": {"Mike": {}},
                "3": {"Cody": {}}
            }
        }

        with patch('services.managers.STARTERS_CACHE', mock_cache_data):
            result = _filter_by_season_and_week(season=2024, week=None)

        # Should return all weeks
        assert result == {"2024": mock_cache_data["2024"]}

    @patch('services.managers.STARTERS_CACHE')
    def test_converts_season_to_string_for_lookup(self, mock_cache):
        """Test properly converts season int to string for cache lookup."""
        from services.managers import _filter_by_season_and_week

        mock_cache_data = {
            "2024": {"1": {"Tommy": {}}}
        }

        with patch('services.managers.STARTERS_CACHE', mock_cache_data):
            # Pass int, should convert to string internally
            result = _filter_by_season_and_week(season=2024, week=None)

        assert "2024" in result


class TestFilterByManager:
    """Test _filter_by_manager helper function."""

    @patch('services.managers.STARTERS_CACHE')
    def test_returns_only_manager_data(self, mock_cache):
        """Test returns only the specified manager's data."""
        from services.managers import _filter_by_manager

        mock_cache_data = {
            "2024": {
                "1": {
                    "Tommy": {"Player1": {}},
                    "Mike": {"Player2": {}},
                    "Cody": {"Player3": {}}
                }
            }
        }

        with patch('services.managers.STARTERS_CACHE', mock_cache_data):
            result = _filter_by_manager(manager="Tommy", season=None, week=None)

        # Should only have Tommy's data
        assert "2024" in result
        assert "1" in result["2024"]
        assert "Tommy" in result["2024"]["1"]
        assert "Mike" not in result["2024"]["1"]
        assert "Cody" not in result["2024"]["1"]

    @patch('services.managers.STARTERS_CACHE')
    def test_skips_metadata_keys(self, mock_cache):
        """Test skips Last_Updated_Season and Last_Updated_Week keys."""
        from services.managers import _filter_by_manager

        mock_cache_data = {
            "2024": {"1": {"Tommy": {}}},
            "Last_Updated_Season": "2024",
            "Last_Updated_Week": "1"
        }

        with patch('services.managers.STARTERS_CACHE', mock_cache_data):
            result = _filter_by_manager(manager="Tommy", season=None, week=None)

        # Should not include metadata keys
        assert "Last_Updated_Season" not in result
        assert "Last_Updated_Week" not in result
        assert "2024" in result

    @patch('services.managers.STARTERS_CACHE')
    def test_filters_by_season_when_provided(self, mock_cache):
        """Test filters by season when season parameter provided."""
        from services.managers import _filter_by_manager

        mock_cache_data = {
            "2023": {"1": {"Tommy": {"Player1": {}}}},
            "2024": {"1": {"Tommy": {"Player2": {}}}}
        }

        with patch('services.managers.STARTERS_CACHE', mock_cache_data):
            result = _filter_by_manager(manager="Tommy", season=2024, week=None)

        # Should only have 2024 data
        assert "2024" in result
        assert "2023" not in result

    @patch('services.managers.STARTERS_CACHE')
    def test_filters_by_week_when_provided(self, mock_cache):
        """Test filters by week when week parameter provided."""
        from services.managers import _filter_by_manager

        mock_cache_data = {
            "2024": {
                "1": {"Tommy": {"Player1": {}}},
                "2": {"Tommy": {"Player2": {}}}
            }
        }

        with patch('services.managers.STARTERS_CACHE', mock_cache_data):
            result = _filter_by_manager(manager="Tommy", season=None, week=1)

        # Should only have week 1
        assert "2024" in result
        assert "1" in result["2024"]
        assert "2" not in result["2024"]

    @patch('services.managers.STARTERS_CACHE')
    def test_filters_by_season_and_week_together(self, mock_cache):
        """Test filters by both season and week when both provided."""
        from services.managers import _filter_by_manager

        mock_cache_data = {
            "2023": {"1": {"Tommy": {"Player1": {}}}},
            "2024": {
                "1": {"Tommy": {"Player2": {}}},
                "2": {"Tommy": {"Player3": {}}}
            }
        }

        with patch('services.managers.STARTERS_CACHE', mock_cache_data):
            result = _filter_by_manager(manager="Tommy", season=2024, week=1)

        # Should only have 2024 week 1
        assert result == {"2024": {"1": {"Tommy": {"Player2": {}}}}}

    @patch('services.managers.STARTERS_CACHE')
    def test_returns_empty_when_manager_not_found(self, mock_cache):
        """Test returns {} when manager doesn't exist in any week."""
        from services.managers import _filter_by_manager

        mock_cache_data = {
            "2024": {
                "1": {"Tommy": {}, "Mike": {}}
            }
        }

        with patch('services.managers.STARTERS_CACHE', mock_cache_data):
            result = _filter_by_manager(manager="NonExistent", season=None, week=None)

        assert result == {}

    @patch('services.managers.STARTERS_CACHE')
    def test_aggregates_manager_across_multiple_seasons_and_weeks(self, mock_cache):
        """Test aggregates all data for a manager across seasons and weeks."""
        from services.managers import _filter_by_manager

        mock_cache_data = {
            "2023": {
                "13": {"Tommy": {"Player1": {}}},
                "14": {"Tommy": {"Player2": {}}}
            },
            "2024": {
                "1": {"Tommy": {"Player3": {}}}
            }
        }

        with patch('services.managers.STARTERS_CACHE', mock_cache_data):
            result = _filter_by_manager(manager="Tommy", season=None, week=None)

        # Should have all Tommy's data across both seasons
        assert "2023" in result
        assert "13" in result["2023"]
        assert "14" in result["2023"]
        assert "2024" in result
        assert "1" in result["2024"]

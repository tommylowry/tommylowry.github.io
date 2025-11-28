"""
Unit tests for utils/cache_utils.py - Cache management utilities.
"""
import pytest
import json
import tempfile
import os
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime


class TestLoadCache:
    """Test load_cache function."""

    def test_loads_existing_cache_file(self):
        """Test loads and returns existing cache file content."""
        from utils.cache_utils import load_cache

        # Create a temporary cache file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {"Last_Updated_Season": "2024", "2024": {"1": {}}}
            json.dump(test_data, f)
            temp_path = f.name

        try:
            result = load_cache(temp_path)
            assert result == test_data
        finally:
            os.remove(temp_path)

    @patch('utils.cache_utils.LEAGUE_IDS', {2019: "id1", 2020: "id2", 2021: "id3"})
    def test_creates_new_cache_with_baseline_structure(self):
        """Test creates new cache with baseline structure when file doesn't exist."""
        from utils.cache_utils import load_cache

        # Use a path that doesn't exist
        non_existent_path = "/tmp/test_cache_nonexistent_12345.json"

        result = load_cache(non_existent_path)

        # Should have metadata fields
        assert "Last_Updated_Season" in result
        assert "Last_Updated_Week" in result
        assert result["Last_Updated_Season"] == "0"
        assert result["Last_Updated_Week"] == 0

        # Should have year keys from LEAGUE_IDS
        assert "2019" in result
        assert "2020" in result
        assert "2021" in result

    @patch('utils.cache_utils.LEAGUE_IDS', {2019: "id1", 2020: "id2"})
    def test_creates_replacement_score_cache_with_historical_years(self):
        """Test adds 3 historical years for replacement_score caches."""
        from utils.cache_utils import load_cache

        # File path containing "replacement_score"
        path = "/tmp/replacement_score_cache.json"

        result = load_cache(path)

        # Should have 3 extra years before 2019 (first year in LEAGUE_IDS)
        # 2019 - 3 = 2016, 2019 - 2 = 2017, 2019 - 1 = 2018
        assert "2016" in result
        assert "2017" in result
        assert "2018" in result
        assert "2019" in result
        assert "2020" in result

    @patch('utils.cache_utils.LEAGUE_IDS', {2019: "id1", 2020: "id2"})
    def test_non_replacement_cache_has_no_historical_years(self):
        """Test non-replacement caches don't get historical years."""
        from utils.cache_utils import load_cache

        # File path NOT containing "replacement_score"
        path = "/tmp/starters_cache.json"

        result = load_cache(path)

        # Should NOT have historical years
        assert "2016" not in result
        assert "2017" not in result
        assert "2018" not in result
        # Should only have configured years
        assert "2019" in result
        assert "2020" in result

    @patch('utils.cache_utils.LEAGUE_IDS', {2019: "id1", 2021: "id2", 2023: "id3"})
    def test_initializes_empty_dicts_for_each_year(self):
        """Test each year key is initialized with an empty dict."""
        from utils.cache_utils import load_cache

        path = "/tmp/test_cache.json"

        result = load_cache(path)

        # Each year should have an empty dict
        assert result["2019"] == {}
        assert result["2021"] == {}
        assert result["2023"] == {}


class TestSaveCache:
    """Test save_cache function."""

    def test_saves_cache_to_file_with_indentation(self):
        """Test saves cache data to file with proper JSON indentation."""
        from utils.cache_utils import save_cache

        test_data = {
            "Last_Updated_Season": "2024",
            "2024": {"1": {"Tommy": {"points": 100}}}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            save_cache(temp_path, test_data)

            # Read back and verify
            with open(temp_path, 'r') as f:
                content = f.read()
                saved_data = json.loads(content)

            assert saved_data == test_data
            # Verify it's indented (should have newlines and spaces)
            assert '\n' in content
            assert '    ' in content  # 4-space indentation
        finally:
            os.remove(temp_path)

    def test_overwrites_existing_file(self):
        """Test overwrites existing file content."""
        from utils.cache_utils import save_cache

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Write initial data
            json.dump({"old": "data"}, f)
            temp_path = f.name

        try:
            # Save new data
            new_data = {"new": "data"}
            save_cache(temp_path, new_data)

            # Read back and verify old data is replaced
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)

            assert saved_data == new_data
            assert "old" not in saved_data
        finally:
            os.remove(temp_path)


class TestGetCurrentSeasonAndWeek:
    """Test get_current_season_and_week function."""

    @patch('utils.cache_utils.datetime')
    @patch('utils.cache_utils.fetch_sleeper_data')
    @patch('utils.cache_utils.LEAGUE_IDS', {2024: "league_123"})
    def test_returns_current_season_and_week(self, mock_fetch, mock_datetime):
        """Test successfully retrieves current season and week from Sleeper API."""
        from utils.cache_utils import get_current_season_and_week

        # Mock current year
        mock_datetime.now.return_value = datetime(2024, 11, 15)

        # Mock Sleeper API response
        mock_fetch.return_value = (
            {
                "season": "2024",
                "settings": {"last_scored_leg": 10}
            },
            200
        )

        season, week = get_current_season_and_week()

        assert season == 2024
        assert week == 10
        mock_fetch.assert_called_once_with("league/league_123")

    @patch('utils.cache_utils.datetime')
    @patch('utils.cache_utils.LEAGUE_IDS', {})
    def test_raises_exception_when_league_id_not_found(self, mock_datetime):
        """Test raises Exception when current year not in LEAGUE_IDS."""
        from utils.cache_utils import get_current_season_and_week

        # Mock current year that's not in LEAGUE_IDS
        mock_datetime.now.return_value = datetime(2099, 1, 1)

        with pytest.raises(Exception, match="No league ID found for the current year: 2099"):
            get_current_season_and_week()

    @patch('utils.cache_utils.datetime')
    @patch('utils.cache_utils.fetch_sleeper_data')
    @patch('utils.cache_utils.LEAGUE_IDS', {2024: "league_123"})
    def test_raises_exception_when_api_fails(self, mock_fetch, mock_datetime):
        """Test raises Exception when Sleeper API returns non-200 status."""
        from utils.cache_utils import get_current_season_and_week

        mock_datetime.now.return_value = datetime(2024, 11, 15)

        # Mock failed API response
        mock_fetch.return_value = ({"error": "Not found"}, 404)

        with pytest.raises(Exception, match="Failed to fetch league data from Sleeper API"):
            get_current_season_and_week()

    @patch('utils.cache_utils.datetime')
    @patch('utils.cache_utils.fetch_sleeper_data')
    @patch('utils.cache_utils.LEAGUE_IDS', {2024: "league_123"})
    def test_handles_preseason_with_zero_week(self, mock_fetch, mock_datetime):
        """Test handles preseason where last_scored_leg is 0."""
        from utils.cache_utils import get_current_season_and_week

        mock_datetime.now.return_value = datetime(2024, 8, 1)

        # Mock preseason response (last_scored_leg = 0)
        mock_fetch.return_value = (
            {
                "season": "2024",
                "settings": {"last_scored_leg": 0}
            },
            200
        )

        season, week = get_current_season_and_week()

        assert season == 2024
        assert week == 0

    @patch('utils.cache_utils.datetime')
    @patch('utils.cache_utils.fetch_sleeper_data')
    @patch('utils.cache_utils.LEAGUE_IDS', {2024: "league_123"})
    def test_converts_season_to_int(self, mock_fetch, mock_datetime):
        """Test converts season string to int for downstream comparisons."""
        from utils.cache_utils import get_current_season_and_week

        mock_datetime.now.return_value = datetime(2024, 11, 15)

        # Sleeper returns season as string
        mock_fetch.return_value = (
            {
                "season": "2024",
                "settings": {"last_scored_leg": 10}
            },
            200
        )

        season, week = get_current_season_and_week()

        # Should be converted to int
        assert isinstance(season, int)
        assert season == 2024

    @patch('utils.cache_utils.datetime')
    @patch('utils.cache_utils.fetch_sleeper_data')
    @patch('utils.cache_utils.LEAGUE_IDS', {2024: "league_123"})
    def test_handles_missing_settings_gracefully(self, mock_fetch, mock_datetime):
        """Test handles missing settings dict with default week 0."""
        from utils.cache_utils import get_current_season_and_week

        mock_datetime.now.return_value = datetime(2024, 11, 15)

        # Response without settings
        mock_fetch.return_value = (
            {
                "season": "2024"
                # No "settings" key
            },
            200
        )

        season, week = get_current_season_and_week()

        assert season == 2024
        assert week == 0  # Default value when settings is missing

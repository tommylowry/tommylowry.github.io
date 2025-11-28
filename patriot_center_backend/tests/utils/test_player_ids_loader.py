"""
Unit tests for utils/player_ids_loader.py - Player metadata caching.
"""
import pytest
import json
import tempfile
import os
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime, timedelta


class TestLoadPlayerIds:
    """Test load_player_ids function."""

    @patch('utils.player_ids_loader.PLAYER_IDS_FILE')
    @patch('utils.player_ids_loader.datetime')
    def test_returns_fresh_cache_when_less_than_7_days_old(self, mock_datetime, mock_file_path):
        """Test returns cached data when cache is less than 7 days old."""
        from utils.player_ids_loader import load_player_ids

        # Mock current time
        mock_datetime.now.return_value = datetime(2024, 11, 20)
        mock_datetime.strptime = datetime.strptime

        # Create temp file with fresh cache (updated 3 days ago)
        cache_data = {
            "Last_Updated": "2024-11-17",  # 3 days ago
            "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"},
            "KC": {"full_name": "Kansas City Chiefs", "position": "DEF"}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(cache_data, f)
            temp_path = f.name

        try:
            with patch('utils.player_ids_loader.PLAYER_IDS_FILE', temp_path):
                result = load_player_ids()

            # Should return cached data without calling API
            assert result["7547"]["full_name"] == "Amon-Ra St. Brown"
            assert "KC" in result
        finally:
            os.remove(temp_path)

    @patch('utils.player_ids_loader.PLAYER_IDS_FILE')
    @patch('utils.player_ids_loader.datetime')
    def test_ensures_defenses_present_in_cached_data(self, mock_datetime, mock_file_path):
        """Test adds missing defense entries to cached data."""
        from utils.player_ids_loader import load_player_ids

        mock_datetime.now.return_value = datetime(2024, 11, 20)
        mock_datetime.strptime = datetime.strptime

        # Cache is fresh but missing some defenses
        cache_data = {
            "Last_Updated": "2024-11-19",  # 1 day ago
            "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
            # Missing defenses
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(cache_data, f)
            temp_path = f.name

        try:
            with patch('utils.player_ids_loader.PLAYER_IDS_FILE', temp_path):
                result = load_player_ids()

            # All defenses should be present
            assert "KC" in result
            assert result["KC"]["position"] == "DEF"
            assert result["KC"]["full_name"] == "Kansas City Chiefs"
            assert "NE" in result
            assert result["NE"]["full_name"] == "New England Patriots"
        finally:
            os.remove(temp_path)

    @patch('utils.player_ids_loader.fetch_updated_player_ids')
    @patch('utils.player_ids_loader.datetime')
    def test_refreshes_stale_cache(self, mock_datetime, mock_fetch):
        """Test refreshes cache when older than 7 days."""
        from utils.player_ids_loader import load_player_ids

        # Mock current time
        mock_datetime.now.return_value = datetime(2024, 11, 20)
        mock_datetime.strptime = datetime.strptime

        # Create temp file with stale cache (updated 10 days ago)
        cache_data = {
            "Last_Updated": "2024-11-10",  # 10 days ago - stale!
            "old_player": {"full_name": "Old Player"}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(cache_data, f)
            temp_path = f.name

        try:
            # Mock fetched data
            mock_fetch.return_value = {
                "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
            }

            with patch('utils.player_ids_loader.PLAYER_IDS_FILE', temp_path):
                result = load_player_ids()

            # Should have called fetch to refresh
            mock_fetch.assert_called_once()
            # Should have new data
            assert "7547" in result
        finally:
            os.remove(temp_path)

    @patch('utils.player_ids_loader.fetch_updated_player_ids')
    @patch('utils.player_ids_loader.datetime')
    def test_creates_cache_when_file_missing(self, mock_datetime, mock_fetch):
        """Test creates new cache when file doesn't exist."""
        from utils.player_ids_loader import load_player_ids

        mock_datetime.now.return_value = datetime(2024, 11, 20)

        # Use non-existent path
        non_existent_path = "/tmp/nonexistent_player_ids_12345.json"

        mock_fetch.return_value = {
            "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
        }

        try:
            with patch('utils.player_ids_loader.PLAYER_IDS_FILE', non_existent_path):
                result = load_player_ids()

            # Should have called fetch
            mock_fetch.assert_called_once()
            # Should have Last_Updated
            assert "Last_Updated" in result
        finally:
            if os.path.exists(non_existent_path):
                os.remove(non_existent_path)

    @patch('utils.player_ids_loader.datetime')
    def test_handles_malformed_timestamp(self, mock_datetime):
        """Test handles malformed Last_Updated timestamp gracefully."""
        from utils.player_ids_loader import load_player_ids

        mock_datetime.now.return_value = datetime(2024, 11, 20)
        mock_datetime.strptime = datetime.strptime

        # Cache with malformed timestamp
        cache_data = {
            "Last_Updated": "invalid-date",
            "7547": {"full_name": "Amon-Ra St. Brown"}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(cache_data, f)
            temp_path = f.name

        try:
            with patch('utils.player_ids_loader.PLAYER_IDS_FILE', temp_path):
                # Should handle gracefully by falling back to epoch (will trigger refresh)
                with patch('utils.player_ids_loader.fetch_updated_player_ids') as mock_fetch:
                    mock_fetch.return_value = {"new": "data"}
                    result = load_player_ids()

                    # Should have refreshed due to epoch fallback making cache ancient
                    mock_fetch.assert_called_once()
        finally:
            os.remove(temp_path)

    @patch('utils.player_ids_loader.fetch_updated_player_ids')
    @patch('utils.player_ids_loader.datetime')
    def test_saves_refreshed_cache_to_disk(self, mock_datetime, mock_fetch):
        """Test saves refreshed cache to disk with timestamp."""
        from utils.player_ids_loader import load_player_ids

        mock_datetime.now.return_value = datetime(2024, 11, 20)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            mock_fetch.return_value = {
                "7547": {"full_name": "Amon-Ra St. Brown"}
            }

            with patch('utils.player_ids_loader.PLAYER_IDS_FILE', temp_path):
                result = load_player_ids()

            # Should have saved to disk
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)

            assert "Last_Updated" in saved_data
            assert saved_data["Last_Updated"] == "2024-11-20"
        finally:
            os.remove(temp_path)


class TestFetchUpdatedPlayerIds:
    """Test fetch_updated_player_ids function."""

    @patch('utils.player_ids_loader.fetch_sleeper_data')
    def test_fetches_from_sleeper_api(self, mock_fetch):
        """Test fetches player data from Sleeper API."""
        from utils.player_ids_loader import fetch_updated_player_ids

        mock_fetch.return_value = (
            {
                "7547": {
                    "full_name": "Amon-Ra St. Brown",
                    "age": 24,
                    "position": "WR",
                    "team": "DET",
                    "extra_field": "should be filtered"
                }
            },
            200
        )

        result = fetch_updated_player_ids()

        mock_fetch.assert_called_once_with("players/nfl")
        assert "7547" in result

    @patch('utils.player_ids_loader.fetch_sleeper_data')
    def test_raises_exception_on_api_failure(self, mock_fetch):
        """Test raises Exception when Sleeper API fails."""
        from utils.player_ids_loader import fetch_updated_player_ids

        mock_fetch.return_value = ({"error": "Not found"}, 404)

        with pytest.raises(Exception, match="Failed to fetch player data from Sleeper API"):
            fetch_updated_player_ids()

    @patch('utils.player_ids_loader.fetch_sleeper_data')
    def test_filters_to_only_allowed_fields(self, mock_fetch):
        """Test only keeps fields in FIELDS_TO_KEEP."""
        from utils.player_ids_loader import fetch_updated_player_ids

        mock_fetch.return_value = (
            {
                "7547": {
                    "full_name": "Amon-Ra St. Brown",
                    "age": 24,
                    "position": "WR",
                    "team": "DET",
                    "extra_field_1": "should be filtered",
                    "extra_field_2": "should be filtered"
                }
            },
            200
        )

        result = fetch_updated_player_ids()

        player = result["7547"]
        # Should have allowed fields
        assert "full_name" in player
        assert "age" in player
        assert "position" in player
        assert "team" in player
        # Should NOT have extra fields
        assert "extra_field_1" not in player
        assert "extra_field_2" not in player

    @patch('utils.player_ids_loader.fetch_sleeper_data')
    def test_creates_synthetic_defense_entries(self, mock_fetch):
        """Test creates synthetic DEF entries for team defenses."""
        from utils.player_ids_loader import fetch_updated_player_ids

        mock_fetch.return_value = (
            {
                "KC": {
                    "full_name": "Some Other Value",  # Should be overridden
                    "position": "WRONG"
                },
                "7547": {
                    "full_name": "Amon-Ra St. Brown",
                    "position": "WR"
                }
            },
            200
        )

        result = fetch_updated_player_ids()

        # KC should be synthetic defense entry
        assert result["KC"]["full_name"] == "Kansas City Chiefs"
        assert result["KC"]["position"] == "DEF"
        assert result["KC"]["team"] == "KC"

        # Regular player should be unaffected
        assert result["7547"]["full_name"] == "Amon-Ra St. Brown"

    @patch('utils.player_ids_loader.fetch_sleeper_data')
    def test_handles_missing_fields_gracefully(self, mock_fetch):
        """Test handles players with missing optional fields."""
        from utils.player_ids_loader import fetch_updated_player_ids

        mock_fetch.return_value = (
            {
                "7547": {
                    "full_name": "Amon-Ra St. Brown",
                    "position": "WR"
                    # Missing: age, years_exp, college, team, etc.
                }
            },
            200
        )

        result = fetch_updated_player_ids()

        # Should only include fields that were present
        player = result["7547"]
        assert "full_name" in player
        assert "position" in player
        assert "age" not in player  # Was missing from source

    @patch('utils.player_ids_loader.fetch_sleeper_data')
    def test_includes_all_team_defenses(self, mock_fetch):
        """Test ensures all NFL team defenses are included."""
        from utils.player_ids_loader import fetch_updated_player_ids, TEAM_DEFENSE_NAMES

        mock_fetch.return_value = ({}, 200)  # Empty response

        result = fetch_updated_player_ids()

        # All team codes should be present as DEF
        for team_code in TEAM_DEFENSE_NAMES.keys():
            assert team_code in result
            assert result[team_code]["position"] == "DEF"
            assert result[team_code]["team"] == team_code

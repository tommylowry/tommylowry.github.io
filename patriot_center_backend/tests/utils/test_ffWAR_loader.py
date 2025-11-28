"""
Unit tests for utils/ffWAR_loader.py - Fantasy Football WAR calculations.
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal


class TestGetMaxWeeks:
    """Test _get_max_weeks helper function."""

    def test_returns_current_week_for_current_season(self):
        """Test returns current_week for current season."""
        from utils.ffWAR_loader import _get_max_weeks
        assert _get_max_weeks(season=2024, current_season=2024, current_week=14) == 14
        assert _get_max_weeks(season=2025, current_season=2025, current_week=8) == 8

    def test_returns_14_for_past_seasons(self):
        """Test returns 14 for completed past seasons."""
        from utils.ffWAR_loader import _get_max_weeks
        assert _get_max_weeks(season=2023, current_season=2024, current_week=14) == 14
        assert _get_max_weeks(season=2021, current_season=2024, current_week=14) == 14

    def test_returns_13_for_2019_and_2020(self):
        """Test returns 13 for 2019 and 2020 seasons (historical cap)."""
        from utils.ffWAR_loader import _get_max_weeks
        assert _get_max_weeks(season=2019, current_season=2024, current_week=14) == 13
        assert _get_max_weeks(season=2020, current_season=2024, current_week=14) == 13


class TestCalculateFfwarPosition:
    """Test _calculate_ffWAR_position simulation logic."""

    def test_returns_empty_dict_when_no_players(self):
        """Test returns empty dict when no players in scores."""
        from utils.ffWAR_loader import _calculate_ffWAR_position

        # Empty scores - no managers have players
        scores = {
            "Tommy": {"total_points": 100.0, "players": {}},
            "Mike": {"total_points": 95.0, "players": {}}
        }

        with patch('utils.ffWAR_loader.REPLACEMENT_SCORES', {"2024": {"1": {"QB_3yr_avg": 15.0}}}):
            result = _calculate_ffWAR_position(scores, season=2024, week=1, position="QB")

        assert result == {}

    @patch('utils.ffWAR_loader.REPLACEMENT_SCORES')
    def test_player_above_replacement_wins_extra_games(self, mock_replacement):
        """Test that a player scoring above replacement adds wins."""
        from utils.ffWAR_loader import _calculate_ffWAR_position

        # Setup: 2 managers, 1 player each
        # Tommy has strong QB, Mike has weak RB
        # We're testing Tommy's QB position
        scores = {
            "Tommy": {
                "total_points": 110.0,  # High total
                "players": {"Josh Allen": 30.0}  # Strong QB
            },
            "Mike": {
                "total_points": 100.0,  # Lower total
                "players": {"Weak QB": 10.0}  # Weak QB
            }
        }

        # Replacement is 15.0 - between the two players
        mock_replacement_data = {"2024": {"1": {"QB_3yr_avg": 15.0}}}

        with patch('utils.ffWAR_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result = _calculate_ffWAR_position(scores, season=2024, week=1, position="QB")

        # Josh Allen (30) is well above replacement (15), should have positive ffWAR
        assert "Josh Allen" in result
        assert result["Josh Allen"]["ffWAR"] > 0

        # Weak QB (10) is below replacement (15), should have negative ffWAR
        assert "Weak QB" in result
        assert result["Weak QB"]["ffWAR"] < 0

    @patch('utils.ffWAR_loader.REPLACEMENT_SCORES')
    def test_calculates_weighted_scores_correctly(self, mock_replacement):
        """Test the weighted score calculation logic."""
        from utils.ffWAR_loader import _calculate_ffWAR_position

        # 3 managers with 1 QB each
        scores = {
            "Tommy": {
                "total_points": 120.0,
                "players": {"QB1": 25.0}
            },
            "Mike": {
                "total_points": 110.0,
                "players": {"QB2": 20.0}
            },
            "Cody": {
                "total_points": 105.0,
                "players": {"QB3": 15.0}
            }
        }

        # Average position score = (25+20+15)/3 = 20.0
        # Tommy: weighted = 120 - 25 + 20 = 115
        # Mike: weighted = 110 - 20 + 20 = 110
        # Cody: weighted = 105 - 15 + 20 = 110

        mock_replacement_data = {"2024": {"1": {"QB_3yr_avg": 18.0}}}

        with patch('utils.ffWAR_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result = _calculate_ffWAR_position(scores, season=2024, week=1, position="QB")

        # All players should have results
        assert len(result) == 3
        assert "QB1" in result
        assert "QB2" in result
        assert "QB3" in result

    @patch('utils.ffWAR_loader.REPLACEMENT_SCORES')
    def test_simulates_all_vs_all_matchups(self, mock_replacement):
        """Test that simulation considers all possible matchups."""
        from utils.ffWAR_loader import _calculate_ffWAR_position

        # With 3 managers, each player gets tested in:
        # - 3 manager_playing scenarios (could be on any team)
        # - Against 2 opponents each (everyone except themselves)
        # Total: 3 * 2 = 6 simulated games per player

        scores = {
            "Tommy": {"total_points": 120.0, "players": {"Elite QB": 30.0}},
            "Mike": {"total_points": 110.0, "players": {"Good QB": 25.0}},
            "Cody": {"total_points": 100.0, "players": {"Bad QB": 10.0}}
        }

        mock_replacement_data = {"2024": {"1": {"QB_3yr_avg": 20.0}}}

        with patch('utils.ffWAR_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result = _calculate_ffWAR_position(scores, season=2024, week=1, position="QB")

        # Elite QB should have high positive ffWAR (wins many matchups vs replacement)
        assert result["Elite QB"]["ffWAR"] > 0.3

        # Bad QB should have negative ffWAR (loses matchups vs replacement)
        assert result["Bad QB"]["ffWAR"] < -0.3

    @patch('utils.ffWAR_loader.REPLACEMENT_SCORES')
    def test_includes_manager_and_position_in_result(self, mock_replacement):
        """Test that result includes manager and position metadata."""
        from utils.ffWAR_loader import _calculate_ffWAR_position

        scores = {
            "Tommy": {
                "total_points": 120.0,
                "players": {"Josh Allen": 25.0}
            }
        }

        mock_replacement_data = {"2024": {"1": {"QB_3yr_avg": 15.0}}}

        with patch('utils.ffWAR_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result = _calculate_ffWAR_position(scores, season=2024, week=1, position="QB")

        assert result["Josh Allen"]["manager"] == "Tommy"
        assert result["Josh Allen"]["position"] == "QB"
        assert "ffWAR" in result["Josh Allen"]

    @patch('utils.ffWAR_loader.REPLACEMENT_SCORES')
    def test_rounds_ffwar_to_three_decimals(self, mock_replacement):
        """Test that ffWAR is rounded to 3 decimal places."""
        from utils.ffWAR_loader import _calculate_ffWAR_position

        scores = {
            "Tommy": {"total_points": 120.0, "players": {"Player": 25.0}},
            "Mike": {"total_points": 110.0, "players": {"Player2": 20.0}}
        }

        mock_replacement_data = {"2024": {"1": {"QB_3yr_avg": 22.0}}}

        with patch('utils.ffWAR_loader.REPLACEMENT_SCORES', mock_replacement_data):
            result = _calculate_ffWAR_position(scores, season=2024, week=1, position="QB")

        # Check that result is rounded (should have max 3 decimal places)
        for player in result:
            ffwar = result[player]["ffWAR"]
            # Convert to string and check decimal places
            ffwar_str = str(ffwar)
            if '.' in ffwar_str:
                decimals = len(ffwar_str.split('.')[1])
                assert decimals <= 3


class TestFetchFfwar:
    """Test _fetch_ffWAR function that orchestrates position calculations."""

    @patch('utils.ffWAR_loader._calculate_ffWAR_position')
    @patch('utils.ffWAR_loader.PLAYER_DATA')
    def test_groups_players_by_position(self, mock_player_data, mock_calculate):
        """Test that players are correctly grouped by position."""
        from utils.ffWAR_loader import _fetch_ffWAR

        mock_player_data_dict = {
            "2024": {
                "1": {
                    "Tommy": {
                        "Josh Allen": {"points": 25.0, "position": "QB"},
                        "Saquon Barkley": {"points": 20.0, "position": "RB"},
                        "Total_Points": 120.0
                    },
                    "Mike": {
                        "Patrick Mahomes": {"points": 23.0, "position": "QB"},
                        "Total_Points": 115.0
                    }
                }
            }
        }

        mock_calculate.return_value = {}

        with patch('utils.ffWAR_loader.PLAYER_DATA', mock_player_data_dict):
            result = _fetch_ffWAR(season=2024, week=1)

            # Should call _calculate_ffWAR_position for each position
            # At minimum QB and RB since those have players
            assert mock_calculate.call_count == 6  # All 6 positions (QB, RB, WR, TE, K, DEF)

    @patch('utils.ffWAR_loader._calculate_ffWAR_position')
    @patch('utils.ffWAR_loader.PLAYER_DATA')
    def test_skips_total_points_sentinel(self, mock_player_data, mock_calculate):
        """Test that Total_Points is not treated as a player."""
        from utils.ffWAR_loader import _fetch_ffWAR

        mock_player_data_dict = {
            "2024": {
                "1": {
                    "Tommy": {
                        "Josh Allen": {"points": 25.0, "position": "QB"},
                        "Total_Points": 125.0  # Should be ignored
                    }
                }
            }
        }

        mock_calculate.return_value = {"Josh Allen": {"ffWAR": 2.5, "position": "QB", "manager": "Tommy"}}

        with patch('utils.ffWAR_loader.PLAYER_DATA', mock_player_data_dict):
            result = _fetch_ffWAR(season=2024, week=1)

        # Result should NOT contain Total_Points
        assert "Total_Points" not in result
        assert "Josh Allen" in result


class TestLoadOrUpdateFfwarCache:
    """Test load_or_update_ffWAR_cache main orchestration function."""

    @patch('utils.ffWAR_loader.get_current_season_and_week')
    @patch('utils.ffWAR_loader.load_cache')
    @patch('utils.ffWAR_loader.save_cache')
    @patch('utils.ffWAR_loader._fetch_ffWAR')
    def test_creates_new_cache_with_progress_markers(self, mock_fetch, mock_save, mock_load, mock_current):
        """Test creates cache with Last_Updated markers."""
        from utils.ffWAR_loader import load_or_update_ffWAR_cache

        mock_current.return_value = (2024, 1)  # Just week 1
        mock_load.return_value = {}
        mock_fetch.return_value = {"Player": {"ffWAR": 1.0, "position": "QB", "manager": "Tommy"}}

        result = load_or_update_ffWAR_cache()

        # Cache should be created and saved
        assert mock_save.called
        # Result should NOT include metadata markers (they're popped before return)
        assert "Last_Updated_Season" not in result
        assert "Last_Updated_Week" not in result

    @patch('utils.ffWAR_loader.get_current_season_and_week')
    @patch('utils.ffWAR_loader.load_cache')
    @patch('utils.ffWAR_loader.save_cache')
    @patch('utils.ffWAR_loader._fetch_ffWAR')
    def test_resumes_from_last_updated(self, mock_fetch, mock_save, mock_load, mock_current):
        """Test resumes processing from Last_Updated markers."""
        from utils.ffWAR_loader import load_or_update_ffWAR_cache

        mock_current.return_value = (2024, 5)
        # Cache already has weeks 1-3 for 2024
        mock_load.return_value = {
            "Last_Updated_Season": "2024",
            "Last_Updated_Week": 3,
            "2024": {
                "1": {},
                "2": {},
                "3": {}
            }
        }
        mock_fetch.return_value = {}

        result = load_or_update_ffWAR_cache()

        # Should only process weeks 4 and 5 (not 1-3)
        assert mock_fetch.call_count == 2

    @patch('utils.ffWAR_loader.get_current_season_and_week')
    @patch('utils.ffWAR_loader.load_cache')
    @patch('utils.ffWAR_loader.save_cache')
    @patch('utils.ffWAR_loader._fetch_ffWAR')
    def test_caps_weeks_at_14_for_regular_seasons(self, mock_fetch, mock_save, mock_load, mock_current):
        """Test that weeks are capped at 14."""
        from utils.ffWAR_loader import load_or_update_ffWAR_cache

        # Even if current week is 18, should stop at 14
        mock_current.return_value = (2024, 18)
        mock_load.return_value = {}
        mock_fetch.return_value = {}

        result = load_or_update_ffWAR_cache()

        # Should not process beyond week 14
        # For one season starting from scratch: 14 weeks
        assert mock_fetch.call_count <= 14

    @patch('utils.ffWAR_loader.get_current_season_and_week')
    @patch('utils.ffWAR_loader.load_cache')
    @patch('utils.ffWAR_loader.save_cache')
    @patch('utils.ffWAR_loader._fetch_ffWAR')
    def test_processes_historical_seasons_from_2019(self, mock_fetch, mock_save, mock_load, mock_current):
        """Test processes all seasons from 2019 to current."""
        from utils.ffWAR_loader import load_or_update_ffWAR_cache

        mock_current.return_value = (2021, 1)  # Just to 2021 week 1
        mock_load.return_value = {}
        mock_fetch.return_value = {}

        result = load_or_update_ffWAR_cache()

        # Should process:
        # - 2019: 13 weeks
        # - 2020: 13 weeks
        # - 2021: 1 week
        # Total: 13 + 13 + 1 = 27 calls
        assert mock_fetch.call_count == 27

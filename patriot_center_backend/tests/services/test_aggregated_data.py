"""
Unit tests for services/aggregated_data.py - Aggregation logic.
"""
import pytest
from unittest.mock import patch
from decimal import Decimal


class TestFetchAggregatedPlayers:
    """Test fetch_aggregated_players function."""

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_aggregates_single_player_single_week(self, mock_ffwar, mock_starters):
        """Test aggregating a single player over one week."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

        mock_starters.return_value = {
            "2024": {
                "1": {
                    "Tommy": {
                        "Amon-Ra St. Brown": {
                            "points": 18.5,
                            "position": "WR",
                            "player_id": "7547"
                        }
                    }
                }
            }
        }
        mock_ffwar.return_value = 2.5

        result = fetch_aggregated_players(manager="Tommy", season=2024, week=1)

        assert "Amon-Ra St. Brown" in result
        assert result["Amon-Ra St. Brown"]["total_points"] == 18.5
        assert result["Amon-Ra St. Brown"]["num_games_started"] == 1
        assert result["Amon-Ra St. Brown"]["ffWAR"] == 2.5
        assert result["Amon-Ra St. Brown"]["position"] == "WR"
        assert "player_image_endpoint" in result["Amon-Ra St. Brown"]

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_aggregates_player_across_multiple_weeks(self, mock_ffwar, mock_starters):
        """Test aggregating same player across multiple weeks."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

        mock_starters.return_value = {
            "2024": {
                "1": {
                    "Tommy": {
                        "Amon-Ra St. Brown": {
                            "points": 18.5,
                            "position": "WR",
                            "player_id": "7547"
                        }
                    }
                },
                "2": {
                    "Tommy": {
                        "Amon-Ra St. Brown": {
                            "points": 22.3,
                            "position": "WR",
                            "player_id": "7547"
                        }
                    }
                }
            }
        }
        mock_ffwar.side_effect = [2.5, 3.1]

        result = fetch_aggregated_players(manager="Tommy", season=2024)

        assert "Amon-Ra St. Brown" in result
        assert result["Amon-Ra St. Brown"]["total_points"] == 40.8
        assert result["Amon-Ra St. Brown"]["num_games_started"] == 2
        assert result["Amon-Ra St. Brown"]["ffWAR"] == 5.6

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_skips_total_points_sentinel(self, mock_ffwar, mock_starters):
        """Test that Total_Points sentinel is skipped."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

        mock_starters.return_value = {
            "2024": {
                "1": {
                    "Tommy": {
                        "Amon-Ra St. Brown": {
                            "points": 18.5,
                            "position": "WR",
                            "player_id": "7547"
                        },
                        "Total_Points": 125.3
                    }
                }
            }
        }
        mock_ffwar.return_value = 2.5

        result = fetch_aggregated_players(manager="Tommy")

        assert "Amon-Ra St. Brown" in result
        assert "Total_Points" not in result

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    def test_returns_empty_when_no_data_for_filters(self, mock_starters):
        """Test returns empty when the filters return no data."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

        mock_starters.return_value = {}
        result = fetch_aggregated_players(manager="Tommy", season=2019, week=99)
        assert result == {}

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_creates_correct_image_endpoint_for_player(self, mock_ffwar, mock_starters):
        """Test that player image endpoint is correctly constructed."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

        mock_starters.return_value = {
            "2024": {"1": {"Tommy": {"Amon-Ra St. Brown": {
                "points": 18.5, "position": "WR", "player_id": "7547"
            }}}}
        }
        mock_ffwar.return_value = 0.0

        result = fetch_aggregated_players(manager="Tommy")
        assert result["Amon-Ra St. Brown"]["player_image_endpoint"] == \
               "https://sleepercdn.com/content/nfl/players/7547.jpg"

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_creates_correct_image_endpoint_for_defense(self, mock_ffwar, mock_starters):
        """Test that DEF team image endpoint is correctly constructed."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

        mock_starters.return_value = {
            "2024": {"1": {"Tommy": {"Kansas City Chiefs": {
                "points": 12.0, "position": "DEF", "player_id": "KC"
            }}}}
        }
        mock_ffwar.return_value = 0.0

        result = fetch_aggregated_players(manager="Tommy")
        assert result["Kansas City Chiefs"]["player_image_endpoint"] == \
               "https://sleepercdn.com/images/team_logos/nfl/kc.jpg"


class TestFetchAggregatedManagers:
    """Test fetch_aggregated_managers function."""

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_aggregates_single_manager_single_week(self, mock_ffwar, mock_starters):
        """Test aggregating managers for a player in one week."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_managers

        mock_starters.return_value = {
            "2024": {"1": {"Tommy": {"Amon-Ra St. Brown": {
                "points": 18.5, "position": "WR", "player_id": "7547"
            }}}}
        }
        mock_ffwar.return_value = 2.5

        result = fetch_aggregated_managers("Amon-Ra St. Brown", season=2024, week=1)

        assert "Tommy" in result
        assert result["Tommy"]["total_points"] == 18.5
        assert result["Tommy"]["num_games_started"] == 1
        assert result["Tommy"]["ffWAR"] == 2.5

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_aggregates_multiple_managers(self, mock_ffwar, mock_starters):
        """Test aggregating multiple managers who started the same player."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_managers

        mock_starters.return_value = {
            "2024": {"1": {
                "Tommy": {"Amon-Ra St. Brown": {"points": 18.5, "position": "WR", "player_id": "7547"}},
                "Mike": {"Amon-Ra St. Brown": {"points": 18.5, "position": "WR", "player_id": "7547"}}
            }}
        }
        mock_ffwar.return_value = 2.5

        result = fetch_aggregated_managers("Amon-Ra St. Brown", season=2024, week=1)

        assert "Tommy" in result
        assert "Mike" in result

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    def test_returns_empty_when_player_not_started(self, mock_starters):
        """Test returns empty dict when player wasn't started by anyone."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_managers

        mock_starters.return_value = {
            "2024": {"1": {"Tommy": {"Different Player": {
                "points": 10.0, "position": "QB", "player_id": "1234"
            }}}}
        }

        result = fetch_aggregated_managers("Amon-Ra St. Brown", season=2024)
        assert result == {}

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_creates_correct_image_endpoint_for_defense_manager(self, mock_ffwar, mock_starters):
        """Test that DEF team image endpoint uses .png for manager aggregation."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_managers

        mock_starters.return_value = {
            "2024": {"1": {"Tommy": {"Kansas City Chiefs": {
                "points": 12.0, "position": "DEF", "player_id": "KC"
            }}}}
        }
        mock_ffwar.return_value = 0.0

        result = fetch_aggregated_managers("Kansas City Chiefs", season=2024)

        # Manager aggregation uses .png (line 185), different from player aggregation which uses .jpg
        assert result["Tommy"]["player_image_endpoint"] == \
               "https://sleepercdn.com/images/team_logos/nfl/kc.png"


class TestFetchFfwarForPlayer:
    """Test fetch_ffWAR_for_player function."""

    def test_returns_zero_when_no_season(self):
        from patriot_center_backend.services.aggregated_data import fetch_ffWAR_for_player
        assert fetch_ffWAR_for_player("Player", season=None, week=1) == 0.0

    def test_returns_zero_when_no_week(self):
        from patriot_center_backend.services.aggregated_data import fetch_ffWAR_for_player
        assert fetch_ffWAR_for_player("Player", season=2024, week=None) == 0.0

    @patch('patriot_center_backend.services.aggregated_data.ffWAR_cache', {"2024": {"1": {"Amon-Ra St. Brown": {"ffWAR": 2.345}}}})
    def test_returns_ffwar_from_cache(self):
        from patriot_center_backend.services.aggregated_data import fetch_ffWAR_for_player
        assert fetch_ffWAR_for_player("Amon-Ra St. Brown", season=2024, week=1) == 2.345

    @patch('patriot_center_backend.services.aggregated_data.ffWAR_cache', {"2024": {"1": {}}})
    def test_returns_zero_when_player_not_in_cache(self):
        from patriot_center_backend.services.aggregated_data import fetch_ffWAR_for_player
        assert fetch_ffWAR_for_player("Unknown Player", season=2024, week=1) == 0.0


class TestDecimalRounding:
    """Test that decimal rounding is correct."""

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_rounds_total_points_to_two_decimals(self, mock_ffwar, mock_starters):
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

        mock_starters.return_value = {
            "2024": {
                "1": {"Tommy": {"Test Player": {"points": 10.123456, "position": "WR", "player_id": "1234"}}},
                "2": {"Tommy": {"Test Player": {"points": 5.987654, "position": "WR", "player_id": "1234"}}}
            }
        }
        mock_ffwar.return_value = 0.0

        result = fetch_aggregated_players(manager="Tommy")
        assert result["Test Player"]["total_points"] == 16.11

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_rounds_ffwar_to_three_decimals(self, mock_ffwar, mock_starters):
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

        mock_starters.return_value = {
            "2024": {
                "1": {"Tommy": {"Test Player": {"points": 10.0, "position": "WR", "player_id": "1234"}}},
                "2": {"Tommy": {"Test Player": {"points": 10.0, "position": "WR", "player_id": "1234"}}}
            }
        }
        mock_ffwar.side_effect = [1.23456789, 2.34567891]

        result = fetch_aggregated_players(manager="Tommy")
        assert result["Test Player"]["ffWAR"] == 3.580

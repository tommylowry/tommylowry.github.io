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


class TestPlayoffPlacement:
    """Test playoff placement tracking functionality."""

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_tracks_single_playoff_placement_for_player(self, mock_ffwar, mock_starters):
        """Test that playoff placement is tracked for a single playoff week."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

        mock_starters.return_value = {
            "2024": {
                "15": {
                    "Tommy": {
                        "Amon-Ra St. Brown": {
                            "points": 25.0,
                            "position": "WR",
                            "player_id": "7547",
                            "placement": 1
                        }
                    }
                }
            }
        }
        mock_ffwar.return_value = 3.5

        result = fetch_aggregated_players(manager="Tommy")

        assert "Amon-Ra St. Brown" in result
        assert "playoff_placement" in result["Amon-Ra St. Brown"]
        assert "Tommy" in result["Amon-Ra St. Brown"]["playoff_placement"]
        assert "2024" in result["Amon-Ra St. Brown"]["playoff_placement"]["Tommy"]
        assert result["Amon-Ra St. Brown"]["playoff_placement"]["Tommy"]["2024"] == 1

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_tracks_multiple_playoff_placements_same_manager(self, mock_ffwar, mock_starters):
        """Test multiple playoff weeks with same manager keeps first placement seen."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

        mock_starters.return_value = {
            "2023": {
                "15": {"Tommy": {"Josh Allen": {"points": 30.0, "position": "QB", "player_id": "4881", "placement": 2}}},
                "16": {"Tommy": {"Josh Allen": {"points": 28.0, "position": "QB", "player_id": "4881", "placement": 1}}}
            }
        }
        mock_ffwar.return_value = 4.0

        result = fetch_aggregated_players(manager="Tommy")

        # First placement encountered is kept (week 15)
        assert result["Josh Allen"]["playoff_placement"]["Tommy"]["2023"] == 2

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_tracks_playoff_placements_across_multiple_years(self, mock_ffwar, mock_starters):
        """Test playoff placements tracked across different seasons."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

        mock_starters.return_value = {
            "2023": {
                "16": {"Tommy": {"Player": {"points": 20.0, "position": "RB", "player_id": "1234", "placement": 1}}}
            },
            "2024": {
                "16": {"Tommy": {"Player": {"points": 22.0, "position": "RB", "player_id": "1234", "placement": 3}}}
            }
        }
        mock_ffwar.return_value = 2.0

        result = fetch_aggregated_players(manager="Tommy")

        assert result["Player"]["playoff_placement"]["Tommy"]["2023"] == 1
        assert result["Player"]["playoff_placement"]["Tommy"]["2024"] == 3

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_tracks_playoff_placements_multiple_managers(self, mock_ffwar, mock_starters):
        """Test player started by different managers in different playoff years."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

        mock_starters.return_value = {
            "2023": {
                "16": {"Tommy": {"Player": {"points": 20.0, "position": "RB", "player_id": "1234", "placement": 1}}}
            },
            "2024": {
                "16": {"Mike": {"Player": {"points": 18.0, "position": "RB", "player_id": "1234", "placement": 2}}}
            }
        }
        mock_ffwar.return_value = 2.0

        result = fetch_aggregated_players()

        assert "playoff_placement" in result["Player"]
        assert "Tommy" in result["Player"]["playoff_placement"]
        assert "Mike" in result["Player"]["playoff_placement"]
        assert result["Player"]["playoff_placement"]["Tommy"]["2023"] == 1
        assert result["Player"]["playoff_placement"]["Mike"]["2024"] == 2

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_no_playoff_placement_for_regular_season(self, mock_ffwar, mock_starters):
        """Test that playoff_placement is not added for regular season games."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

        mock_starters.return_value = {
            "2024": {
                "1": {
                    "Tommy": {
                        "Player": {
                            "points": 15.0,
                            "position": "WR",
                            "player_id": "7547"
                        }
                    }
                }
            }
        }
        mock_ffwar.return_value = 1.5

        result = fetch_aggregated_players(manager="Tommy")

        assert "playoff_placement" not in result["Player"]

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_tracks_playoff_placement_for_managers(self, mock_ffwar, mock_starters):
        """Test playoff placement tracked in manager aggregation."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_managers

        mock_starters.return_value = {
            "2024": {
                "16": {
                    "Tommy": {
                        "Josh Allen": {
                            "points": 30.0,
                            "position": "QB",
                            "player_id": "4881",
                            "placement": 1
                        }
                    }
                }
            }
        }
        mock_ffwar.return_value = 4.0

        result = fetch_aggregated_managers("Josh Allen")

        assert "Tommy" in result
        assert "playoff_placement" in result["Tommy"]
        assert "Josh Allen" in result["Tommy"]["playoff_placement"]
        assert result["Tommy"]["playoff_placement"]["Josh Allen"]["2024"] == 1

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_manager_multiple_playoff_placements(self, mock_ffwar, mock_starters):
        """Test manager with same player across multiple playoff years."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_managers

        mock_starters.return_value = {
            "2023": {
                "16": {"Tommy": {"Player": {"points": 20.0, "position": "RB", "player_id": "1234", "placement": 3}}}
            },
            "2024": {
                "16": {"Tommy": {"Player": {"points": 25.0, "position": "RB", "player_id": "1234", "placement": 1}}}
            }
        }
        mock_ffwar.return_value = 2.5

        result = fetch_aggregated_managers("Player")

        assert result["Tommy"]["playoff_placement"]["Player"]["2023"] == 3
        assert result["Tommy"]["playoff_placement"]["Player"]["2024"] == 1

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_mixed_regular_and_playoff_weeks(self, mock_ffwar, mock_starters):
        """Test aggregation with both regular season and playoff weeks."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

        mock_starters.return_value = {
            "2024": {
                "1": {"Tommy": {"Player": {"points": 15.0, "position": "WR", "player_id": "7547"}}},
                "2": {"Tommy": {"Player": {"points": 18.0, "position": "WR", "player_id": "7547"}}},
                "16": {"Tommy": {"Player": {"points": 22.0, "position": "WR", "player_id": "7547", "placement": 1}}}
            }
        }
        mock_ffwar.return_value = 2.0

        result = fetch_aggregated_players(manager="Tommy")

        # Should aggregate all points
        assert result["Player"]["total_points"] == 55.0
        assert result["Player"]["num_games_started"] == 3
        # Should only track playoff placement for playoff week
        assert "playoff_placement" in result["Player"]
        assert result["Player"]["playoff_placement"]["Tommy"]["2024"] == 1

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_all_placement_values(self, mock_ffwar, mock_starters):
        """Test that placements 1, 2, and 3 are all tracked correctly."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

        mock_starters.return_value = {
            "2022": {
                "16": {"Tommy": {"P1": {"points": 20.0, "position": "QB", "player_id": "1", "placement": 1}}}
            },
            "2023": {
                "16": {"Mike": {"P2": {"points": 18.0, "position": "RB", "player_id": "2", "placement": 2}}}
            },
            "2024": {
                "16": {"Cody": {"P3": {"points": 15.0, "position": "WR", "player_id": "3", "placement": 3}}}
            }
        }
        mock_ffwar.return_value = 1.0

        result = fetch_aggregated_players()

        assert result["P1"]["playoff_placement"]["Tommy"]["2022"] == 1
        assert result["P2"]["playoff_placement"]["Mike"]["2023"] == 2
        assert result["P3"]["playoff_placement"]["Cody"]["2024"] == 3

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_same_player_different_managers_different_playoff_weeks(self, mock_ffwar, mock_starters):
        """Test same player with different managers in different playoff weeks with different placements."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

        # Christian McCaffrey started by Tommy in week 15 (semifinals, 2nd place)
        # Then traded/picked up and started by Mike in week 16 (championship, 1st place)
        mock_starters.return_value = {
            "2024": {
                "15": {
                    "Tommy": {
                        "Christian McCaffrey": {
                            "points": 28.5,
                            "position": "RB",
                            "player_id": "4034",
                            "placement": 2
                        }
                    }
                },
                "16": {
                    "Mike": {
                        "Christian McCaffrey": {
                            "points": 31.2,
                            "position": "RB",
                            "player_id": "4034",
                            "placement": 1
                        }
                    }
                }
            }
        }
        mock_ffwar.return_value = 3.0

        result = fetch_aggregated_players()

        # Player should be in results
        assert "Christian McCaffrey" in result

        # Should aggregate points across both weeks
        assert result["Christian McCaffrey"]["total_points"] == 59.7
        assert result["Christian McCaffrey"]["num_games_started"] == 2

        # Should track both managers' placements
        assert "playoff_placement" in result["Christian McCaffrey"]
        assert "Tommy" in result["Christian McCaffrey"]["playoff_placement"]
        assert "Mike" in result["Christian McCaffrey"]["playoff_placement"]

        # Each manager should have their own placement
        assert result["Christian McCaffrey"]["playoff_placement"]["Tommy"]["2024"] == 2
        assert result["Christian McCaffrey"]["playoff_placement"]["Mike"]["2024"] == 1

    @patch('patriot_center_backend.services.aggregated_data.fetch_starters')
    @patch('patriot_center_backend.services.aggregated_data.fetch_ffWAR_for_player')
    def test_same_player_different_managers_different_placements_manager_view(self, mock_ffwar, mock_starters):
        """Test manager aggregation when same player has different placements with different managers."""
        from patriot_center_backend.services.aggregated_data import fetch_aggregated_managers

        # Same scenario as above, but from manager perspective
        mock_starters.return_value = {
            "2024": {
                "15": {
                    "Tommy": {
                        "Christian McCaffrey": {
                            "points": 28.5,
                            "position": "RB",
                            "player_id": "4034",
                            "placement": 2
                        }
                    }
                },
                "16": {
                    "Mike": {
                        "Christian McCaffrey": {
                            "points": 31.2,
                            "position": "RB",
                            "player_id": "4034",
                            "placement": 1
                        }
                    }
                }
            }
        }
        mock_ffwar.return_value = 3.0

        result = fetch_aggregated_managers("Christian McCaffrey")

        # Both managers should be in results
        assert "Tommy" in result
        assert "Mike" in result

        # Each manager should have correct stats
        assert result["Tommy"]["total_points"] == 28.5
        assert result["Tommy"]["num_games_started"] == 1
        assert result["Mike"]["total_points"] == 31.2
        assert result["Mike"]["num_games_started"] == 1

        # Each manager should have playoff placement for this player
        assert result["Tommy"]["playoff_placement"]["Christian McCaffrey"]["2024"] == 2
        assert result["Mike"]["playoff_placement"]["Christian McCaffrey"]["2024"] == 1

"""
Unit tests for utils/starters_loader.py - Starters cache with incremental updates.
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal


class TestGetMaxWeeks:
    """Test _get_max_weeks helper function."""

    def test_returns_current_week_for_current_season(self):
        """Test returns current_week for current season."""
        from patriot_center_backend.utils.starters_loader import _get_max_weeks
        assert _get_max_weeks(season=2024, current_season=2024, current_week=10) == 10
        assert _get_max_weeks(season=2025, current_season=2025, current_week=5) == 5

    def test_returns_16_for_2019_and_2020(self):
        """Test returns 16 weeks for 2019 and 2020 seasons (includes playoffs)."""
        from patriot_center_backend.utils.starters_loader import _get_max_weeks
        assert _get_max_weeks(season=2019, current_season=2024, current_week=10) == 16
        assert _get_max_weeks(season=2020, current_season=2024, current_week=10) == 16

    def test_returns_17_for_other_past_seasons(self):
        """Test returns 17 weeks for completed seasons (not 2019/2020)."""
        from patriot_center_backend.utils.starters_loader import _get_max_weeks
        assert _get_max_weeks(season=2021, current_season=2024, current_week=10) == 17
        assert _get_max_weeks(season=2023, current_season=2024, current_week=10) == 17


class TestGetRelevantPlayoffRosterIds:
    """Test _get_relevant_playoff_roster_ids playoff logic."""

    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_returns_empty_dict_for_regular_season_2020_and_earlier(self, mock_fetch):
        """Test returns empty dict for weeks <= 13 in 2019/2020 seasons."""
        from patriot_center_backend.utils.starters_loader import _get_relevant_playoff_roster_ids

        result = _get_relevant_playoff_roster_ids(2019, 13, "league_123")
        assert result == {}
        assert not mock_fetch.called

        result = _get_relevant_playoff_roster_ids(2020, 10, "league_123")
        assert result == {}
        assert not mock_fetch.called

    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_returns_empty_dict_for_regular_season_2021_and_later(self, mock_fetch):
        """Test returns empty dict for weeks <= 14 in 2021+ seasons."""
        from patriot_center_backend.utils.starters_loader import _get_relevant_playoff_roster_ids

        result = _get_relevant_playoff_roster_ids(2021, 14, "league_123")
        assert result == {}
        assert not mock_fetch.called

        result = _get_relevant_playoff_roster_ids(2024, 10, "league_123")
        assert result == {}
        assert not mock_fetch.called

    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_fetches_playoff_bracket_for_playoff_weeks(self, mock_fetch):
        """Test fetches playoff bracket data for playoff weeks."""
        from patriot_center_backend.utils.starters_loader import _get_relevant_playoff_roster_ids

        playoff_bracket = [
            {"r": 1, "w": 1, "l": 2},
            {"r": 1, "w": 3, "l": 4},
            {"r": 2, "w": 1, "l": 3},
            {"r": 3, "w": 1, "l": 3, "p": 1},  # Championship
            {"r": 3, "w": 4, "l": 5, "p": 3}   # 3rd place
        ]
        mock_fetch.return_value = (playoff_bracket, 200)

        result = _get_relevant_playoff_roster_ids(2021, 15, "league_123")

        assert mock_fetch.called
        mock_fetch.assert_called_with("league/league_123/winners_bracket")
        assert set(result['round_roster_ids']) == {1, 2, 3, 4}

    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_extracts_round_1_rosters_for_week_14_in_2019_2020(self, mock_fetch):
        """Test extracts round 1 playoff rosters for week 14 in 2019/2020."""
        from patriot_center_backend.utils.starters_loader import _get_relevant_playoff_roster_ids

        playoff_bracket = [
            {"r": 1, "w": 1, "l": 2},
            {"r": 1, "w": 3, "l": 4},
            {"r": 2, "w": 1, "l": 3},
            {"r": 3, "w": 1, "l": 3, "p": 1},
            {"r": 3, "w": 4, "l": 5, "p": 3}
        ]
        mock_fetch.return_value = (playoff_bracket, 200)

        result = _get_relevant_playoff_roster_ids(2019, 14, "league_123")

        assert set(result['round_roster_ids']) == {1, 2, 3, 4}
        assert result['first_place_id'] == 1
        assert result['second_place_id'] == 3
        assert result['third_place_id'] == 4

    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_extracts_round_1_rosters_for_week_15_in_2021_plus(self, mock_fetch):
        """Test extracts round 1 playoff rosters for week 15 in 2021+."""
        from patriot_center_backend.utils.starters_loader import _get_relevant_playoff_roster_ids

        playoff_bracket = [
            {"r": 1, "w": 1, "l": 2},
            {"r": 1, "w": 3, "l": 4},
            {"r": 2, "w": 1, "l": 3},
            {"r": 3, "w": 1, "l": 3, "p": 1},
            {"r": 3, "w": 4, "l": 5, "p": 3}
        ]
        mock_fetch.return_value = (playoff_bracket, 200)

        result = _get_relevant_playoff_roster_ids(2021, 15, "league_123")

        assert set(result['round_roster_ids']) == {1, 2, 3, 4}

    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_skips_consolation_bracket_matchups(self, mock_fetch):
        """Test skips matchups with p=5 (consolation bracket)."""
        from patriot_center_backend.utils.starters_loader import _get_relevant_playoff_roster_ids

        playoff_bracket = [
            {"r": 1, "w": 1, "l": 2},
            {"r": 1, "w": 3, "l": 4},
            {"r": 1, "w": 7, "l": 8, "p": 5},  # Consolation - should skip
            {"r": 2, "w": 1, "l": 3},
            {"r": 3, "w": 1, "l": 3, "p": 1},
            {"r": 3, "w": 4, "l": 5, "p": 3}
        ]
        mock_fetch.return_value = (playoff_bracket, 200)

        result = _get_relevant_playoff_roster_ids(2021, 15, "league_123")

        # Should not include rosters 7 and 8 from consolation
        assert 7 not in result['round_roster_ids']
        assert 8 not in result['round_roster_ids']

    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_raises_error_for_week_17(self, mock_fetch):
        """Test raises ValueError for week 17 in 2019/2020 (round 4 is unsupported)."""
        from patriot_center_backend.utils.starters_loader import _get_relevant_playoff_roster_ids

        # Week 17 in 2019 maps to round 4 which explicitly raises error
        mock_fetch.return_value = ([], 200)

        with pytest.raises(ValueError, match="Cannot get playoff roster IDs for week 17"):
            _get_relevant_playoff_roster_ids(2019, 17, "league_123")

    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_raises_error_when_no_round_rosters_found(self, mock_fetch):
        """Test raises ValueError when no rosters found for the round."""
        from patriot_center_backend.utils.starters_loader import _get_relevant_playoff_roster_ids

        # Empty bracket
        mock_fetch.return_value = ([], 200)

        with pytest.raises(ValueError, match="Cannot get playoff roster IDs for the given week"):
            _get_relevant_playoff_roster_ids(2024, 15, "league_123")

    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_raises_error_when_placement_info_missing(self, mock_fetch):
        """Test raises ValueError when first/second/third place info missing."""
        from patriot_center_backend.utils.starters_loader import _get_relevant_playoff_roster_ids

        # Bracket without placement info (p field)
        playoff_bracket = [
            {"r": 1, "w": 1, "l": 2},
            {"r": 1, "w": 3, "l": 4}
        ]
        mock_fetch.return_value = (playoff_bracket, 200)

        with pytest.raises(ValueError, match="Cannot get first/second/third place roster IDs"):
            _get_relevant_playoff_roster_ids(2024, 15, "league_123")


class TestGetRosterId:
    """Test get_roster_id roster lookup."""

    def test_finds_roster_by_user_id(self):
        """Test finds correct roster_id for given user_id."""
        from patriot_center_backend.utils.starters_loader import get_roster_id

        rosters_response = (
            [
                {"owner_id": "user_123", "roster_id": 1},
                {"owner_id": "user_456", "roster_id": 2},
                {"owner_id": "user_789", "roster_id": 3}
            ],
            200
        )

        assert get_roster_id(rosters_response, "user_123") == 1
        assert get_roster_id(rosters_response, "user_456") == 2
        assert get_roster_id(rosters_response, "user_789") == 3

    def test_returns_none_when_user_not_found(self):
        """Test returns None when user_id doesn't match any roster."""
        from patriot_center_backend.utils.starters_loader import get_roster_id

        rosters_response = (
            [
                {"owner_id": "user_123", "roster_id": 1},
                {"owner_id": "user_456", "roster_id": 2}
            ],
            200
        )

        assert get_roster_id(rosters_response, "user_999") is None

    def test_returns_none_for_empty_rosters(self):
        """Test returns None when rosters list is empty."""
        from patriot_center_backend.utils.starters_loader import get_roster_id

        rosters_response = ([], 200)
        assert get_roster_id(rosters_response, "user_123") is None


class TestGetStartersData:
    """Test get_starters_data starter extraction."""

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"},
        "4034": {"full_name": "Christian McCaffrey", "position": "RB"},
        "NE": {"full_name": "New England Patriots", "position": "DEF"}
    })
    def test_extracts_starters_and_points(self):
        """Test extracts starter data with points and positions."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 1,
                    "starters": ["7547", "4034", "NE"],
                    "players_points": {
                        "7547": 15.6,
                        "4034": 28.3,
                        "NE": 12.0
                    }
                }
            ],
            200
        )

        result = get_starters_data(matchups_response, 1, {})

        # Should have all three players
        assert "Amon-Ra St. Brown" in result
        assert "Christian McCaffrey" in result
        assert "New England Patriots" in result

        # Verify points
        assert result["Amon-Ra St. Brown"]["points"] == 15.6
        assert result["Christian McCaffrey"]["points"] == 28.3
        assert result["New England Patriots"]["points"] == 12.0

        # Verify positions
        assert result["Amon-Ra St. Brown"]["position"] == "WR"
        assert result["Christian McCaffrey"]["position"] == "RB"
        assert result["New England Patriots"]["position"] == "DEF"

        # Verify player_ids
        assert result["Amon-Ra St. Brown"]["player_id"] == "7547"
        assert result["Christian McCaffrey"]["player_id"] == "4034"
        assert result["New England Patriots"]["player_id"] == "NE"

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"},
        "4034": {"full_name": "Christian McCaffrey", "position": "RB"}
    })
    def test_calculates_total_points_correctly(self):
        """Test sums all player points into Total_Points."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 1,
                    "starters": ["7547", "4034"],
                    "players_points": {
                        "7547": 15.6,
                        "4034": 28.3
                    }
                }
            ],
            200
        )

        result = get_starters_data(matchups_response, 1, {})

        # Total: 15.6 + 28.3 = 43.9
        assert result["Total_Points"] == 43.9

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
    })
    def test_rounds_total_points_to_2_decimals(self):
        """Test rounds Total_Points to 2 decimal places using Decimal."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 1,
                    "starters": ["7547"],
                    "players_points": {
                        "7547": 15.666666  # Should round to 15.67
                    }
                }
            ],
            200
        )

        result = get_starters_data(matchups_response, 1, {})

        # Decimal rounding should give us exactly 2 decimals
        # 15.666666 rounds to 15.67
        assert result["Total_Points"] == 15.67

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {})
    def test_skips_players_not_in_player_ids(self):
        """Test skips players without metadata (not in PLAYER_IDS)."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 1,
                    "starters": ["unknown_player"],
                    "players_points": {
                        "unknown_player": 20.0
                    }
                }
            ],
            200
        )

        result = get_starters_data(matchups_response, 1, {})

        # Should only have Total_Points (0.0 since no valid players)
        assert result["Total_Points"] == 0.0
        assert len(result) == 1  # Only Total_Points

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown"}  # Missing position
    })
    def test_skips_players_without_position(self):
        """Test skips players missing position field."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 1,
                    "starters": ["7547"],
                    "players_points": {
                        "7547": 20.0
                    }
                }
            ],
            200
        )

        result = get_starters_data(matchups_response, 1, {})

        # Should skip player without position
        assert "Amon-Ra St. Brown" not in result
        assert result["Total_Points"] == 0.0

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"position": "WR"}  # Missing full_name
    })
    def test_skips_players_without_full_name(self):
        """Test skips players missing full_name field."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 1,
                    "starters": ["7547"],
                    "players_points": {
                        "7547": 20.0
                    }
                }
            ],
            200
        )

        result = get_starters_data(matchups_response, 1, {})

        # Should skip player without full_name
        assert result["Total_Points"] == 0.0

    def test_returns_none_when_roster_not_found(self):
        """Test returns None when roster_id doesn't exist in matchups."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {"roster_id": 1, "starters": [], "players_points": {}},
                {"roster_id": 2, "starters": [], "players_points": {}}
            ],
            200
        )

        result = get_starters_data(matchups_response, 999, {})
        assert result is None

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
    })
    def test_handles_zero_points_correctly(self):
        """Test handles players with 0 points."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 1,
                    "starters": ["7547"],
                    "players_points": {
                        "7547": 0.0
                    }
                }
            ],
            200
        )

        result = get_starters_data(matchups_response, 1, {})

        assert result["Amon-Ra St. Brown"]["points"] == 0.0
        assert result["Total_Points"] == 0.0

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"},
        "4034": {"full_name": "Christian McCaffrey", "position": "RB"}
    })
    def test_adds_first_place_playoff_placement(self):
        """Test adds placement=1 for first place playoff roster."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 1,
                    "starters": ["7547", "4034"],
                    "players_points": {
                        "7547": 15.6,
                        "4034": 28.3
                    }
                }
            ],
            200
        )

        playoff_roster_ids = {
            "round_roster_ids": [1, 2, 3, 4],
            "first_place_id": 1,
            "second_place_id": 2,
            "third_place_id": 3
        }

        result = get_starters_data(matchups_response, 1, playoff_roster_ids)

        assert result["Amon-Ra St. Brown"]["placement"] == 1
        assert result["Christian McCaffrey"]["placement"] == 1

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
    })
    def test_adds_second_place_playoff_placement(self):
        """Test adds placement=2 for second place playoff roster."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 2,
                    "starters": ["7547"],
                    "players_points": {"7547": 15.6}
                }
            ],
            200
        )

        playoff_roster_ids = {
            "round_roster_ids": [1, 2, 3, 4],
            "first_place_id": 1,
            "second_place_id": 2,
            "third_place_id": 3
        }

        result = get_starters_data(matchups_response, 2, playoff_roster_ids)

        assert result["Amon-Ra St. Brown"]["placement"] == 2

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
    })
    def test_adds_third_place_playoff_placement(self):
        """Test adds placement=3 for third place playoff roster."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 3,
                    "starters": ["7547"],
                    "players_points": {"7547": 15.6}
                }
            ],
            200
        )

        playoff_roster_ids = {
            "round_roster_ids": [1, 2, 3, 4],
            "first_place_id": 1,
            "second_place_id": 2,
            "third_place_id": 3
        }

        result = get_starters_data(matchups_response, 3, playoff_roster_ids)

        assert result["Amon-Ra St. Brown"]["placement"] == 3

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
    })
    def test_no_placement_for_non_top_three_playoff_roster(self):
        """Test does not add placement for playoff rosters not in top 3."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 4,
                    "starters": ["7547"],
                    "players_points": {"7547": 15.6}
                }
            ],
            200
        )

        playoff_roster_ids = {
            "round_roster_ids": [1, 2, 3, 4],
            "first_place_id": 1,
            "second_place_id": 2,
            "third_place_id": 3
        }

        result = get_starters_data(matchups_response, 4, playoff_roster_ids)

        assert "placement" not in result["Amon-Ra St. Brown"]

    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
    })
    def test_no_placement_for_regular_season(self):
        """Test does not add placement when playoff_roster_ids is empty dict."""
        from patriot_center_backend.utils.starters_loader import get_starters_data

        matchups_response = (
            [
                {
                    "roster_id": 1,
                    "starters": ["7547"],
                    "players_points": {"7547": 15.6}
                }
            ],
            200
        )

        result = get_starters_data(matchups_response, 1, {})

        assert "placement" not in result["Amon-Ra St. Brown"]


class TestFetchStartersForWeek:
    """Test fetch_starters_for_week API integration and data mapping."""

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader.USERNAME_TO_REAL_NAME', {"sleeper_user": "Tommy"})
    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
    })
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_fetches_from_sleeper_api_successfully(self, mock_fetch, mock_playoff_ids):
        """Test fetches users, rosters, and matchups from Sleeper API."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}  # Regular season
        users = [{"user_id": "user_123", "display_name": "sleeper_user"}]
        rosters = [{"owner_id": "user_123", "roster_id": 1}]
        matchups = [
            {
                "roster_id": 1,
                "starters": ["7547"],
                "players_points": {"7547": 15.6}
            }
        ]

        def fetch_side_effect(endpoint):
            if "users" in endpoint:
                return (users, 200)
            elif "rosters" in endpoint:
                return (rosters, 200)
            elif "matchups" in endpoint:
                return (matchups, 200)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        result = fetch_starters_for_week(2024, 1)

        # Should have data for Tommy (mapped from sleeper_user)
        assert "Tommy" in result
        assert "Amon-Ra St. Brown" in result["Tommy"]
        assert result["Tommy"]["Amon-Ra St. Brown"]["points"] == 15.6

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_returns_empty_dict_on_users_api_failure(self, mock_fetch, mock_playoff_ids):
        """Test returns empty dict when users API fails."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}
        mock_fetch.return_value = ({"error": "Not found"}, 404)

        result = fetch_starters_for_week(2024, 1)
        assert result == {}

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_returns_empty_dict_on_rosters_api_failure(self, mock_fetch, mock_playoff_ids):
        """Test returns empty dict when rosters API fails."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}

        def fetch_side_effect(endpoint):
            if "users" in endpoint:
                return ([{"user_id": "user_123", "display_name": "Tommy"}], 200)
            elif "rosters" in endpoint:
                return ({"error": "Not found"}, 404)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        result = fetch_starters_for_week(2024, 1)
        assert result == {}

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_returns_empty_dict_on_matchups_api_failure(self, mock_fetch, mock_playoff_ids):
        """Test returns empty dict when matchups API fails."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}

        def fetch_side_effect(endpoint):
            if "users" in endpoint:
                return ([{"user_id": "user_123", "display_name": "Tommy"}], 200)
            elif "rosters" in endpoint:
                return ([{"owner_id": "user_123", "roster_id": 1}], 200)
            elif "matchups" in endpoint:
                return ({"error": "Not found"}, 404)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        result = fetch_starters_for_week(2024, 1)
        assert result == {}

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2019: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader.USERNAME_TO_REAL_NAME', {"sleeper_cody": "Cody"})
    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
    })
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_applies_2019_early_week_cody_to_tommy_correction(self, mock_fetch, mock_playoff_ids):
        """Test converts Cody to Tommy for 2019 weeks < 4."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}
        users = [{"user_id": "user_123", "display_name": "sleeper_cody"}]
        rosters = [{"owner_id": "user_123", "roster_id": 1}]
        matchups = [
            {
                "roster_id": 1,
                "starters": ["7547"],
                "players_points": {"7547": 15.6}
            }
        ]

        def fetch_side_effect(endpoint):
            if "users" in endpoint:
                return (users, 200)
            elif "rosters" in endpoint:
                return (rosters, 200)
            elif "matchups" in endpoint:
                return (matchups, 200)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        # Week 3 - should convert Cody to Tommy
        result = fetch_starters_for_week(2019, 3)
        assert "Tommy" in result
        assert "Cody" not in result

        # Week 4 - should NOT convert (week >= 4)
        result = fetch_starters_for_week(2019, 4)
        assert "Cody" in result
        assert "Tommy" not in result

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader.USERNAME_TO_REAL_NAME', {"sleeper_davey": "Davey"})
    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
    })
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_applies_2024_davey_roster_id_hardcode(self, mock_fetch, mock_playoff_ids):
        """Test hardcodes roster_id=4 for Davey in 2024 when roster lookup fails."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}
        users = [{"user_id": "user_davey", "display_name": "sleeper_davey"}]
        # Rosters doesn't have user_davey - triggers hardcode
        rosters = [{"owner_id": "other_user", "roster_id": 1}]
        matchups = [
            {
                "roster_id": 4,  # Hardcoded roster_id for Davey
                "starters": ["7547"],
                "players_points": {"7547": 15.6}
            }
        ]

        def fetch_side_effect(endpoint):
            if "users" in endpoint:
                return (users, 200)
            elif "rosters" in endpoint:
                return (rosters, 200)
            elif "matchups" in endpoint:
                return (matchups, 200)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        result = fetch_starters_for_week(2024, 1)

        # Should have data for Davey with hardcoded roster_id=4
        assert "Davey" in result
        assert "Amon-Ra St. Brown" in result["Davey"]

    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    @patch('patriot_center_backend.utils.starters_loader.USERNAME_TO_REAL_NAME', {})
    @patch('patriot_center_backend.utils.starters_loader.PLAYER_IDS', {
        "7547": {"full_name": "Amon-Ra St. Brown", "position": "WR"}
    })
    @patch('patriot_center_backend.utils.starters_loader._get_relevant_playoff_roster_ids')
    @patch('patriot_center_backend.utils.starters_loader.fetch_sleeper_data')
    def test_uses_unknown_manager_for_unmapped_display_names(self, mock_fetch, mock_playoff_ids):
        """Test uses 'Unknown Manager' for display names not in USERNAME_TO_REAL_NAME."""
        from patriot_center_backend.utils.starters_loader import fetch_starters_for_week

        mock_playoff_ids.return_value = {}
        users = [{"user_id": "user_123", "display_name": "unmapped_user"}]
        rosters = [{"owner_id": "user_123", "roster_id": 1}]
        matchups = [
            {
                "roster_id": 1,
                "starters": ["7547"],
                "players_points": {"7547": 15.6}
            }
        ]

        def fetch_side_effect(endpoint):
            if "users" in endpoint:
                return (users, 200)
            elif "rosters" in endpoint:
                return (rosters, 200)
            elif "matchups" in endpoint:
                return (matchups, 200)
            return ({}, 404)

        mock_fetch.side_effect = fetch_side_effect

        result = fetch_starters_for_week(2024, 1)

        # Should use "Unknown Manager" as fallback
        assert "Unknown Manager" in result


class TestLoadOrUpdateStartersCache:
    """Test load_or_update_starters_cache main orchestration."""

    @patch('patriot_center_backend.utils.starters_loader.get_current_season_and_week')
    @patch('patriot_center_backend.utils.starters_loader.load_cache')
    @patch('patriot_center_backend.utils.starters_loader.save_cache')
    @patch('patriot_center_backend.utils.starters_loader.fetch_starters_for_week')
    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    def test_creates_new_cache_with_baseline_structure(self, mock_fetch, mock_save, mock_load, mock_current):
        """Test initializes new cache with Last_Updated markers."""
        from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache

        mock_current.return_value = (2024, 1)
        mock_load.return_value = {}
        mock_fetch.return_value = {
            "Tommy": {
                "Total_Points": 100.0,
                "Josh Allen": {"points": 25.0, "position": "QB", "player_id": "4881"}
            }
        }

        result = load_or_update_starters_cache()

        # Should have called save
        assert mock_save.called
        # Result should NOT include metadata (popped before return)
        assert "Last_Updated_Season" not in result
        assert "Last_Updated_Week" not in result

    @patch('patriot_center_backend.utils.starters_loader.get_current_season_and_week')
    @patch('patriot_center_backend.utils.starters_loader.load_cache')
    @patch('patriot_center_backend.utils.starters_loader.save_cache')
    @patch('patriot_center_backend.utils.starters_loader.fetch_starters_for_week')
    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    def test_resumes_from_last_updated_markers(self, mock_fetch, mock_save, mock_load, mock_current):
        """Test resumes processing from Last_Updated_Season and Last_Updated_Week."""
        from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache

        mock_current.return_value = (2024, 5)
        # Cache already has weeks 1-3
        mock_load.return_value = {
            "Last_Updated_Season": "2024",
            "Last_Updated_Week": 3,
            "2024": {
                "1": {"Tommy": {"Total_Points": 100.0}},
                "2": {"Tommy": {"Total_Points": 105.0}},
                "3": {"Tommy": {"Total_Points": 110.0}}
            }
        }
        mock_fetch.return_value = {"Tommy": {"Total_Points": 115.0}}

        result = load_or_update_starters_cache()

        # Should only fetch weeks 4 and 5 (not 1-3)
        assert mock_fetch.call_count == 2

    @patch('patriot_center_backend.utils.starters_loader.get_current_season_and_week')
    @patch('patriot_center_backend.utils.starters_loader.load_cache')
    @patch('patriot_center_backend.utils.starters_loader.save_cache')
    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    def test_skips_when_fully_up_to_date(self, mock_save, mock_load, mock_current):
        """Test skips processing when cache is already current."""
        from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache

        mock_current.return_value = (2024, 5)
        # Cache is already at 2024 week 5
        mock_load.return_value = {
            "Last_Updated_Season": "2024",
            "Last_Updated_Week": 5,
            "2024": {str(w): {"Tommy": {"Total_Points": 100.0}} for w in range(1, 6)}
        }

        result = load_or_update_starters_cache()

        # Should still save but not fetch new data
        assert mock_save.called

    @patch('patriot_center_backend.utils.starters_loader.get_current_season_and_week')
    @patch('patriot_center_backend.utils.starters_loader.load_cache')
    @patch('patriot_center_backend.utils.starters_loader.save_cache')
    @patch('patriot_center_backend.utils.starters_loader.fetch_starters_for_week')
    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2024: "league_123"})
    def test_caps_current_week_at_14(self, mock_fetch, mock_save, mock_load, mock_current):
        """Test caps current_week at 14 (regular season) even if API returns higher."""
        from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache

        # API returns week 18 (playoffs)
        mock_current.return_value = (2024, 18)
        mock_load.return_value = {}
        mock_fetch.return_value = {"Tommy": {"Total_Points": 100.0}}

        result = load_or_update_starters_cache()

        # Should cap at 14, so max 14 calls
        assert mock_fetch.call_count <= 14

    @patch('patriot_center_backend.utils.starters_loader.get_current_season_and_week')
    @patch('patriot_center_backend.utils.starters_loader.load_cache')
    @patch('patriot_center_backend.utils.starters_loader.save_cache')
    @patch('patriot_center_backend.utils.starters_loader.fetch_starters_for_week')
    @patch('patriot_center_backend.utils.starters_loader.LEAGUE_IDS', {2019: "id1", 2020: "id2"})
    def test_processes_2019_and_2020_with_16_week_cap(self, mock_fetch, mock_save, mock_load, mock_current):
        """Test processes 2019 and 2020 with 16-week cap (includes playoffs)."""
        from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache

        # Current season is 2021 so 2019 and 2020 are past seasons
        mock_current.return_value = (2021, 10)
        mock_load.return_value = {}
        mock_fetch.return_value = {"Tommy": {"Total_Points": 100.0}}

        result = load_or_update_starters_cache()

        # Should process:
        # - 2019: 16 weeks (includes playoffs)
        # - 2020: 16 weeks (includes playoffs)
        # Total: 32 calls
        assert mock_fetch.call_count == 32

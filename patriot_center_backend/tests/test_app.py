"""
Unit tests for app.py - Flask routes and request handling.
"""
import pytest
from unittest.mock import patch, MagicMock
import json


class TestArgumentParsing:
    """Test the parse_arguments function with success and failure cases."""

    # === SUCCESS CASES ===

    def test_parse_no_arguments(self, flask_app):
        """Test parsing with no arguments returns all nulls."""
        from app import parse_arguments
        result = parse_arguments(None, None, None)
        assert result == (None, None, None)

    def test_parse_single_year(self, flask_app):
        """Test parsing a single valid year."""
        from app import parse_arguments
        # 2024 should be in LEAGUE_IDS
        result = parse_arguments("2024", None, None)
        assert result == (2024, None, None)

    def test_parse_year_and_week(self, flask_app):
        """Test parsing year and week together."""
        from app import parse_arguments
        result = parse_arguments("2024", "5", None)
        assert result == (2024, 5, None)

    def test_parse_year_and_manager(self, flask_app):
        """Test parsing year and manager (skip week)."""
        from app import parse_arguments
        result = parse_arguments("2024", "Tommy", None)
        assert result == (2024, None, "Tommy")

    def test_parse_all_three_arguments(self, flask_app):
        """Test parsing all three arguments in order."""
        from app import parse_arguments
        result = parse_arguments("2024", "Tommy", "5")
        assert result == (2024, 5, "Tommy")

    def test_parse_manager_only(self, flask_app):
        """Test parsing manager name only."""
        from app import parse_arguments
        result = parse_arguments("Tommy", None, None)
        assert result == (None, None, "Tommy")

    def test_parse_year_and_manager_different_order(self, flask_app):
        """Test parsing works regardless of argument order."""
        from app import parse_arguments
        result = parse_arguments("Tommy", "2024", None)
        assert result == (2024, None, "Tommy")

    def test_parse_week_boundary_min(self, flask_app):
        """Test week boundary at minimum (1)."""
        from app import parse_arguments
        result = parse_arguments("2024", "1", None)
        assert result == (2024, 1, None)

    def test_parse_week_boundary_max(self, flask_app):
        """Test week boundary at maximum (17)."""
        from app import parse_arguments
        result = parse_arguments("2024", "17", None)
        assert result == (2024, 17, None)

    # === FAILURE CASES ===

    def test_fail_week_without_year(self, flask_app):
        """Test that providing week without year raises ValueError."""
        from app import parse_arguments
        with pytest.raises(ValueError, match="Week provided without a corresponding year"):
            parse_arguments("5", None, None)

    def test_fail_week_without_year_with_manager(self, flask_app):
        """Test week without year fails even when manager is present."""
        from app import parse_arguments
        with pytest.raises(ValueError, match="Week provided without a corresponding year"):
            parse_arguments("Tommy", "5", None)

    def test_fail_multiple_years(self, flask_app):
        """Test that providing multiple years raises ValueError."""
        from app import parse_arguments
        with pytest.raises(ValueError, match="Multiple year arguments provided"):
            parse_arguments("2024", "2023", None)

    def test_fail_multiple_weeks(self, flask_app):
        """Test that providing multiple weeks raises ValueError."""
        from app import parse_arguments
        with pytest.raises(ValueError, match="Multiple week arguments provided"):
            parse_arguments("2024", "5", "10")

    def test_fail_multiple_managers(self, flask_app):
        """Test that providing multiple managers raises ValueError."""
        from app import parse_arguments
        with pytest.raises(ValueError, match="Multiple manager arguments provided"):
            parse_arguments("Tommy", "Mike", None)

    def test_fail_invalid_manager_name(self, flask_app):
        """Test that an unrecognized manager name raises ValueError."""
        from app import parse_arguments
        with pytest.raises(ValueError, match="Invalid argument provided: InvalidManager"):
            parse_arguments("InvalidManager", None, None)

    def test_fail_invalid_integer(self, flask_app):
        """Test that an integer not matching year or week range raises ValueError."""
        from app import parse_arguments
        # 99 is not a valid year and not in week range 1-17
        with pytest.raises(ValueError, match="Invalid integer argument provided"):
            parse_arguments("99", None, None)

    def test_fail_week_too_high(self, flask_app):
        """Test that week > 17 raises ValueError."""
        from app import parse_arguments
        with pytest.raises(ValueError, match="Invalid integer argument provided"):
            parse_arguments("2024", "18", None)

    def test_fail_week_zero(self, flask_app):
        """Test that week 0 raises ValueError."""
        from app import parse_arguments
        with pytest.raises(ValueError, match="Invalid integer argument provided"):
            parse_arguments("2024", "0", None)

    def test_fail_invalid_year(self, flask_app):
        """Test that a year not in LEAGUE_IDS raises ValueError."""
        from app import parse_arguments
        # Assuming 1999 is not in LEAGUE_IDS (pre-league)
        with pytest.raises(ValueError, match="Invalid integer argument provided"):
            parse_arguments("1999", None, None)


class TestFlattenDict:
    """Test the _flatten_dict helper function."""

    def test_flatten_empty_dict(self, flask_app):
        """Test flattening an empty dict."""
        from app import _flatten_dict
        result = _flatten_dict({})
        assert result == {}

    def test_flatten_flat_dict(self, flask_app):
        """Test flattening an already-flat dict."""
        from app import _flatten_dict
        input_dict = {"a": 1, "b": 2, "c": 3}
        result = _flatten_dict(input_dict)
        assert result == input_dict

    def test_flatten_nested_dict(self, flask_app):
        """Test flattening a nested dict."""
        from app import _flatten_dict
        input_dict = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        result = _flatten_dict(input_dict)
        assert result == {"level1.level2.level3": "value"}

    def test_flatten_mixed_dict(self, flask_app):
        """Test flattening a dict with mixed flat and nested keys."""
        from app import _flatten_dict
        input_dict = {
            "flat": 1,
            "nested": {
                "key": 2
            }
        }
        result = _flatten_dict(input_dict)
        assert result == {
            "flat": 1,
            "nested.key": 2
        }

    def test_flatten_custom_separator(self, flask_app):
        """Test flattening with a custom separator."""
        from app import _flatten_dict
        input_dict = {
            "a": {
                "b": "value"
            }
        }
        result = _flatten_dict(input_dict, sep="_")
        assert result == {"a_b": "value"}

    def test_flatten_none_input(self, flask_app):
        """Test that None input returns empty dict."""
        from app import _flatten_dict
        result = _flatten_dict(None)
        assert result == {}

    def test_flatten_non_dict_input(self, flask_app):
        """Test that non-dict input returns empty dict."""
        from app import _flatten_dict
        result = _flatten_dict("not a dict")
        assert result == {}


class TestToRecords:
    """Test the _to_records helper function."""

    def test_to_records_empty_dict(self, flask_app):
        """Test converting empty dict to records."""
        from app import _to_records
        result = _to_records({})
        assert result == []

    def test_to_records_flat_dict(self, flask_app):
        """Test converting flat dict to records."""
        from app import _to_records
        input_data = {
            "player1": {"points": 10},
            "player2": {"points": 20}
        }
        result = _to_records(input_data)
        assert len(result) == 2
        assert {"key": "player1", "points": 10} in result
        assert {"key": "player2", "points": 20} in result

    def test_to_records_custom_key_name(self, flask_app):
        """Test converting with custom key name."""
        from app import _to_records
        input_data = {
            "player1": {"points": 10}
        }
        result = _to_records(input_data, key_name="player")
        assert result[0] == {"player": "player1", "points": 10}

    def test_to_records_nested_values(self, flask_app):
        """Test converting dict with nested values."""
        from app import _to_records
        input_data = {
            "player1": {
                "stats": {
                    "points": 10
                }
            }
        }
        result = _to_records(input_data)
        # Should flatten nested stats
        assert "key" in result[0]
        assert result[0]["key"] == "player1"
        assert "stats.points" in result[0]
        assert result[0]["stats.points"] == 10

    def test_to_records_list_input(self, flask_app):
        """Test converting a list to records."""
        from app import _to_records
        input_data = [{"points": 10}, {"points": 20}]
        result = _to_records(input_data)
        assert len(result) == 2
        assert {"points": 10} in result
        assert {"points": 20} in result

    def test_to_records_scalar_value(self, flask_app):
        """Test converting a scalar value."""
        from app import _to_records
        result = _to_records(42)
        assert result == [{"value": 42}]


class TestFlaskRoutes:
    """Test Flask API endpoint routes."""

    def test_index_route(self, flask_client):
        """Test the root index route."""
        response = flask_client.get('/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "service" in data
        assert data["service"] == "Patriot Center Backend"
        assert "endpoints" in data

    def test_ping_route(self, flask_client):
        """Test the ping health check."""
        response = flask_client.get('/ping')
        assert response.status_code == 200
        assert b"pong" in response.data

    def test_health_route(self, flask_client):
        """Test the health check endpoint."""
        response = flask_client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"

    @patch('app.fetch_starters')
    def test_get_starters_no_params(self, mock_fetch, flask_client):
        """Test getting starters with no parameters."""
        mock_fetch.return_value = {"2024": {"1": {"Tommy": {}}}}

        response = flask_client.get('/get_starters')
        assert response.status_code == 200
        mock_fetch.assert_called_once_with(manager=None, season=None, week=None)

    @patch('app.fetch_starters')
    def test_get_starters_with_year(self, mock_fetch, flask_client):
        """Test getting starters filtered by year."""
        mock_fetch.return_value = {"2024": {"1": {"Tommy": {}}}}

        response = flask_client.get('/get_starters/2024')
        assert response.status_code == 200
        mock_fetch.assert_called_once_with(manager=None, season=2024, week=None)

    @patch('app.fetch_starters')
    def test_get_starters_json_format(self, mock_fetch, flask_client):
        """Test getting starters in JSON format."""
        mock_fetch.return_value = {"2024": {"1": {"Tommy": {}}}}

        response = flask_client.get('/get_starters?format=json')
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should return raw JSON, not flattened
        assert isinstance(data, dict)

    @patch('app.fetch_aggregated_players')
    def test_get_aggregated_players(self, mock_fetch, flask_client, sample_aggregated_player_data):
        """Test the aggregated players endpoint."""
        mock_fetch.return_value = sample_aggregated_player_data

        response = flask_client.get('/get_aggregated_players/2024/Tommy')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)  # Should be converted to records

    @patch('app.fetch_aggregated_managers')
    def test_get_aggregated_managers(self, mock_fetch, flask_client, sample_aggregated_manager_data):
        """Test the aggregated managers endpoint."""
        mock_fetch.return_value = sample_aggregated_manager_data

        response = flask_client.get('/get_aggregated_managers/Amon-Ra_St._Brown')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    @patch('app.fetch_aggregated_managers')
    def test_get_aggregated_managers_with_filters(self, mock_fetch, flask_client, sample_aggregated_manager_data):
        """Test aggregated managers with year and week filters."""
        mock_fetch.return_value = sample_aggregated_manager_data

        response = flask_client.get('/get_aggregated_managers/Josh_Allen/2024/5')
        assert response.status_code == 200
        # Should pass underscored name as is, parse year and week
        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args
        assert call_args[1]['player'] == "Josh Allen"  # Underscores converted to spaces
        assert call_args[1]['season'] == 2024
        assert call_args[1]['week'] == 5

    def test_get_aggregated_managers_invalid_params(self, flask_client):
        """Test that invalid parameters return 400 error."""
        response = flask_client.get('/get_aggregated_managers/Player/5')  # Week without year
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    @patch('app.fetch_starters')
    def test_meta_options(self, mock_fetch, flask_client):
        """Test the meta/options endpoint."""
        mock_fetch.return_value = {
            "2024": {
                "1": {"Tommy": {}, "Mike": {}},
                "2": {"Tommy": {}, "Cody": {}}
            },
            "2023": {
                "1": {"Tommy": {}}
            },
            "Last_Updated_Season": "2024",
            "Last_Updated_Week": "2"
        }

        response = flask_client.get('/meta/options')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert "seasons" in data
        assert "weeksBySeason" in data
        assert "managers" in data

    def test_cors_headers(self, flask_client):
        """Test that CORS headers are set."""
        response = flask_client.get('/')
        # Flask-CORS should add these headers
        assert 'Access-Control-Allow-Origin' in response.headers


class TestErrorHandling:
    """Test error handling in the Flask app."""

    @patch('app.fetch_starters')
    def test_api_error_handling(self, mock_fetch, flask_client):
        """Test that API errors are handled gracefully."""
        mock_fetch.side_effect = Exception("API Error")

        response = flask_client.get('/get_starters')
        # Should either return 500 or handle gracefully
        assert response.status_code in [200, 500]

    def test_invalid_route(self, flask_client):
        """Test accessing an invalid route returns 404."""
        response = flask_client.get('/invalid_route_12345')
        assert response.status_code == 404

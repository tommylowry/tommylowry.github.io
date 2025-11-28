"""
Unit tests for utils/sleeper_api_handler.py - Sleeper API HTTP client.
"""
import pytest
from unittest.mock import patch, Mock
import requests


class TestFetchSleeperData:
    """Test fetch_sleeper_data function."""

    @patch('utils.sleeper_api_handler.requests.get')
    def test_successful_api_call(self, mock_get):
        """Test successful API call returns data and 200."""
        from utils.sleeper_api_handler import fetch_sleeper_data

        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"test": "data", "id": 123}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        data, status = fetch_sleeper_data("/test/endpoint")

        assert status == 200
        assert data == {"test": "data", "id": 123}
        mock_get.assert_called_once()

    @patch('utils.sleeper_api_handler.requests.get')
    def test_constructs_correct_url(self, mock_get):
        """Test that URL is constructed correctly from endpoint."""
        from utils.sleeper_api_handler import fetch_sleeper_data
        from constants import SLEEPER_API_URL

        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        fetch_sleeper_data("/v1/league/123")

        # Should construct full URL
        expected_url = f"{SLEEPER_API_URL}/v1/league/123"
        mock_get.assert_called_once_with(expected_url)

    @patch('utils.sleeper_api_handler.requests.get')
    def test_handles_http_error(self, mock_get):
        """Test that HTTP errors are handled gracefully."""
        from utils.sleeper_api_handler import fetch_sleeper_data

        # Mock HTTP error
        mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")

        data, status = fetch_sleeper_data("/invalid/endpoint")

        assert status == 500
        assert "error" in data
        assert "404 Not Found" in data["error"]

    @patch('utils.sleeper_api_handler.requests.get')
    def test_handles_connection_error(self, mock_get):
        """Test that connection errors are handled."""
        from utils.sleeper_api_handler import fetch_sleeper_data

        mock_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")

        data, status = fetch_sleeper_data("/test/endpoint")

        assert status == 500
        assert "error" in data

    @patch('utils.sleeper_api_handler.requests.get')
    def test_handles_timeout(self, mock_get):
        """Test that timeouts are handled."""
        from utils.sleeper_api_handler import fetch_sleeper_data

        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        data, status = fetch_sleeper_data("/test/endpoint")

        assert status == 500
        assert "error" in data

    @patch('utils.sleeper_api_handler.requests.get')
    def test_handles_json_decode_error(self, mock_get):
        """Test that JSON decode errors are handled."""
        from utils.sleeper_api_handler import fetch_sleeper_data

        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        data, status = fetch_sleeper_data("/test/endpoint")

        assert status == 500
        assert "error" in data

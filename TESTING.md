# Testing Guide

This document explains how to run tests for the Patriot Center backend.

## Setup

1. **Install test dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running Tests

### Run all tests:
```bash
pytest
```

### Run with coverage report:
```bash
pytest --cov=. --cov-report=term-missing
```

### Run specific test file:
```bash
pytest patriot_center_backend/tests/test_app.py
```

### Run tests matching a pattern:
```bash
pytest -k "test_parse"
```

### Run with verbose output:
```bash
pytest -v
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_app.py              # Flask app and route tests
├── services/
│   └── test_aggregated_data.py  # Aggregation logic tests
└── utils/
    └── test_sleeper_api_handler.py  # API client tests
```

## Writing Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Example Test:
```python
def test_aggregates_player_data(mock_starters, mock_ffwar):
    """Test description."""
    from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

    # Setup
    mock_starters.return_value = {...}

    # Execute
    result = fetch_aggregated_players(manager="Tommy")

    # Assert
    assert result["Player"]["total_points"] == 18.5
```

## CI/CD

Tests run automatically on every pull request via GitHub Actions.
See [`.github/workflows/backend-tests.yml`](../.github/workflows/backend-tests.yml)

## Coverage

Current test coverage focuses on:
- ✅ Flask routes and argument parsing
- ✅ Aggregation logic (players and managers)
- ✅ API client error handling
- ⏳ Additional utils (can be expanded)

## Tips

- Use `-x` to stop on first failure: `pytest -x`
- Use `--lf` to run only last failed tests: `pytest --lf`
- Use `--pdb` to drop into debugger on failure: `pytest --pdb`

# Patriot Center

A comprehensive fantasy football analytics platform that calculates and displays advanced metrics for a private fantasy football league across multiple seasons (2019-2025).

## Overview

Patriot Center tracks 16 managers in a multi-year fantasy football league and provides detailed insights into player performance using **ffWAR (Fantasy Football Wins Above Replacement)** - a custom metric that measures how many wins a player adds compared to a "replacement level" player.

## Key Features

- **Advanced Metrics**: Calculate ffWAR by simulating hypothetical matchups with positional replacement averages
- **Multi-Season Analytics**: Historical tracking across 7+ seasons (2019-2025)
- **Flexible Filtering**: Filter by season, week, manager, or position
- **Player Detail Pages**: In-depth statistics and manager history for each player
- **Real-time Data**: Integration with Sleeper fantasy football API
- **Performance Optimized**: Local JSON caching to minimize API calls

## Technology Stack

### Frontend
- React 19.2.0 with React Router
- Deployed on Netlify
- Built with react-scripts

### Backend
- Python Flask with CORS support
- Gunicorn WSGI server
- Deployed on Fly.io

### Data Sources
- Sleeper API for real-time fantasy football data
- Local JSON caches for calculated metrics

## Project Structure

```
.
├── patriot_center_frontend/    # React frontend
│   ├── src/                    # React source code
│   │   ├── components/         # Reusable components
│   │   ├── pages/             # Page components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── services/          # API service layer
│   │   └── App.js             # Main application
│   ├── public/                # Static assets
│   ├── build/                 # Production build output
│   └── package.json           # Frontend dependencies
│
├── patriot_center_backend/    # Python Flask backend
│   ├── app.py                 # Main Flask application
│   ├── services/              # Business logic services
│   ├── utils/                 # Utility functions
│   ├── data/                  # JSON data caches
│   ├── tests/                 # Unit tests
│   └── constants.py           # Configuration constants
│
├── Dockerfile                 # Docker configuration
├── fly.toml                   # Fly.io deployment config
└── requirements.txt           # Backend dependencies
```

## API Endpoints

- `GET /get_starters` - Roster data by season/week/manager
- `GET /get_aggregated_players` - Player stats aggregated across weeks
- `GET /get_aggregated_managers/<player>` - Manager stats for specific player
- `GET /meta/options` - Available seasons, weeks, managers for UI filters
- `GET /health` - Health check endpoint
- `GET /ping` - Liveness check

## Development Setup

### Frontend

```bash
cd patriot_center_frontend

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

### Backend

```bash
# Create virtual environment (from project root)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server (from project root)
python -m patriot_center_backend.app
```

## Deployment

### Frontend (Netlify)
The frontend is automatically deployed to Netlify at [patriotcenter.netlify.app](https://patriotcenter.netlify.app)

Deployment is triggered automatically on push to `main` branch via Netlify's GitHub integration.

### Backend (Fly.io)
The backend API is deployed on Fly.io at `patriot-center-api.fly.dev`

Deployment is triggered automatically on push to `main` branch via GitHub Actions.

## Testing

```bash
# Run from project root
pytest
pytest --cov  # Run with coverage
```

## How ffWAR Works

ffWAR (Fantasy Football Wins Above Replacement) measures a player's value by:

1. Taking each game where a player was started
2. Simulating what would have happened if a "replacement level" player (positional average) was started instead
3. Calculating the net change in wins/losses
4. Aggregating across all weeks to determine total wins contributed

This provides a more nuanced view of player value than raw points alone.

## League Information

- **Number of Managers**: 16
- **Seasons Tracked**: 2019-2025
- **Regular Season Weeks**: 1-14 (excludes playoffs)
- **Positions**: QB, RB, WR, TE, K, DEF

## License

Private project for Patriot Center fantasy football league.

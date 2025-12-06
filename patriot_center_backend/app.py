from flask import Flask, jsonify, request
from flask_cors import CORS
from patriot_center_backend.constants import LEAGUE_IDS, NAME_TO_MANAGER_USERNAME

app = Flask(__name__)
CORS(app, resources={
    r"/get_aggregated_players*": {"origins": ["https://patriotcenter.netlify.app"]},
    r"/meta/options": {"origins": ["https://patriotcenter.netlify.app"]},
    r"/get_starters*": {"origins": ["https://patriotcenter.netlify.app"]},
    r"/get_aggregated_managers*": {"origins": ["https://patriotcenter.netlify.app"]},
    r"/players/list": {"origins": ["https://patriotcenter.netlify.app"]},
    r"/meta/valid_options*": {"origins": ["https://patriotcenter.netlify.app"]},
    r"/get_player_manager_aggregation*": {"origins": ["https://patriotcenter.netlify.app"]},
})
CORS(app)  # Enable CORS for all routes during development

@app.route('/')
def index():
    """Root endpoint with basic info."""
    return jsonify({
        "service": "Patriot Center Backend",
        "version": "1.0.0",
        "endpoints": [
            "/get_starters",
            "/get_aggregated_players",
            "/get_aggregated_managers/<player>",
            "/meta/options",
            "/ping",
            "/health"
        ]
    }), 200

@app.route('/ping')
def ping():
    """Liveness check endpoint."""
    return "pong", 200

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200

# Multiple route variants allow optional path parameters (year, manager, week)
@app.route('/get_starters', defaults={'arg1': None, 'arg2': None, 'arg3': None}, methods=['GET'])
@app.route('/get_starters/<string:arg1>', defaults={'arg2': None, 'arg3': None}, methods=['GET'])
@app.route('/get_starters/<string:arg1>/<string:arg2>', defaults={'arg3': None}, methods=['GET'])
@app.route('/get_starters/<string:arg1>/<string:arg2>/<string:arg3>', methods=['GET'])
def get_starters(arg1, arg2, arg3):
    """
    Fetch starters filtered by optional season (year), manager, and week.

    Path arguments are positional and inferred by type/value:
    - League IDs -> season
    - Week numbers 1-14 -> week
    - Known manager names -> manager

    Query param: format=json returns raw shape; otherwise flattened records.

    Returns:
        Flask Response: JSON payload (filtered starters or error).
    """
    from patriot_center_backend.services.managers import fetch_starters

    year, week, manager = parse_arguments(arg1, arg2, arg3)

    data = fetch_starters(season=year, manager=manager, week=week)
    if request.args.get("format") == "json":
        return jsonify(data), 200
    return jsonify(_to_records(data)), 200

@app.route('/get_aggregated_players', defaults={'arg1': None, 'arg2': None, 'arg3': None}, methods=['GET'])
@app.route('/get_aggregated_players/<string:arg1>', defaults={'arg2': None, 'arg3': None}, methods=['GET'])
@app.route('/get_aggregated_players/<string:arg1>/<string:arg2>', defaults={'arg3': None}, methods=['GET'])
@app.route('/get_aggregated_players/<string:arg1>/<string:arg2>/<string:arg3>', methods=['GET'])
def get_aggregated_players(arg1, arg2, arg3):
    """
    Aggregate player totals (points, games started, ffWAR) for a manager.

    Uses same positional inference rules as get_starters. Returns either raw
    aggregation or flattened record list.

    Returns:
        Flask Response: JSON payload (aggregated player stats or error).
    """
    from patriot_center_backend.services.aggregated_data import fetch_aggregated_players
    
    try:
        year, week, manager = parse_arguments(arg1, arg2, arg3)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    data = fetch_aggregated_players(season=year, manager=manager, week=week)
    if request.args.get("format") == "json":
        return jsonify(data), 200
    return jsonify(_to_records(data)), 200

@app.route('/get_aggregated_managers/<string:player>', defaults={'arg2': None, 'arg3': None}, methods=['GET'])
@app.route('/get_aggregated_managers/<string:player>/<string:arg2>', defaults={'arg3': None}, methods=['GET'])
@app.route('/get_aggregated_managers/<string:player>/<string:arg2>/<string:arg3>', methods=['GET'])
def get_aggregated_managers(player, arg2, arg3):
    """
    Aggregate manager totals (points, games started, ffWAR) for a given player.

    Player name comes first as a required path component. Remaining args are
    interpreted as season and/or week. Underscores are converted to spaces to
    allow URL-friendly player names.

    Returns:
        Flask Response: JSON payload (aggregated manager stats or error).
    """
    from patriot_center_backend.services.aggregated_data import fetch_aggregated_managers

    try:
        year, week, _ = parse_arguments(arg2, arg3, None)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    player = player.replace("_", " ").replace("%27", "'")

    data = fetch_aggregated_managers(player=player, season=year, week=week)
    if request.args.get("format") == "json":
        return jsonify(data), 200
    return jsonify(_to_records(data, key_name="player")), 200

@app.route('/get_player_manager_aggregation/<string:player>/<string:manager>', defaults={'year': None, 'week': None}, methods=['GET'])
@app.route('/get_player_manager_aggregation/<string:player>/<string:manager>/<string:year>', defaults={'week': None}, methods=['GET'])
@app.route('/get_player_manager_aggregation/<string:player>/<string:manager>/<string:year>/<string:week>', methods=['GET'])
def get_player_manager_aggregation(player, manager, year, week):
    """
    Aggregate totals for a specific player-manager pairing.

    Player and manager are required path components. Remaining args are
    interpreted as season and/or week. Underscores are converted to spaces
    to allow URL-friendly player names.

    Returns:
        Flask Response: JSON payload (aggregated stats or error).
    """
    from patriot_center_backend.services.aggregated_data import fetch_player_manager_aggregation

    player = player.replace("_", " ").replace("%27", "'")

    data = fetch_player_manager_aggregation(player=player, manager=manager, season=year, week=week)
    if request.args.get("format") == "json":
        return jsonify(data), 200
    return jsonify(_to_records(data, key_name="manager")), 200

@app.route('/players/list', methods=['GET'])
def list_players():
    """
    Endpoint to list all players in the system.
    """
    from patriot_center_backend.services.players import fetch_players
    players_data = fetch_players()
    if request.args.get("format") == "json":
        return jsonify(players_data), 200
    return jsonify(_to_records(players_data, key_name="name")), 200

@app.route('/meta/options', methods=['GET'])
def meta_options():
    """
    Expose selectable seasons, weeks, and managers for frontend filters.
    Omitting any in requests to /get_aggregated_players yields ALL for that category.
    """
    return jsonify({
        "seasons": list(LEAGUE_IDS),
        "weeks": list(range(1, 18)),
        "managers": list(NAME_TO_MANAGER_USERNAME.keys())
    }), 200

@app.route('/meta/valid_options', defaults={'arg1': None, 'arg2': None, 'arg3': None}, methods=['GET'])
@app.route('/meta/valid_options/<string:arg1>', defaults={'arg2': None, 'arg3': None}, methods=['GET'])
@app.route('/meta/valid_options/<string:arg1>/<string:arg2>', defaults={'arg3': None}, methods=['GET'])
@app.route('/meta/valid_options/<string:arg1>/<string:arg2>/<string:arg3>', methods=['GET'])
def valid_options(arg1, arg2, arg3):
    """
    Endpoint to validate provided season, week, manager, player, and position combinations.
    """
    from patriot_center_backend.services.valid_options import fetch_valid_options

    data = fetch_valid_options(arg1, arg2, arg3)
    # Sort each list in the response for consistent ordering
    for key in data:
        if isinstance(data[key], list):
            data[key].sort()
    return jsonify(data), 200

def parse_arguments(arg1, arg2, arg3):
    """
    Infer season (year), week, and manager from up to three positional args.

    Resolution order:
    - Integers matching LEAGUE_IDS -> season
    - Integers 1-14 -> week
    - Strings matching NAME_TO_MANAGER_USERNAME -> manager
    - Rejects duplicates or ambiguous assignments.

    Args:
        arg1, arg2, arg3 (str | None): Raw path segments.

    Returns:
        tuple: (season:int|None, week:int|None, manager:str|None)

    Raises:
        ValueError: On invalid values, duplicates, or week without season.
    """
    year = None
    manager = None
    week = None

    for arg in (arg1, arg2, arg3):
        if arg is None:
            continue
        
        if arg.isnumeric() == True:
            arg_int = int(arg)
            if arg_int in LEAGUE_IDS:
                if year is not None:
                    raise ValueError("Multiple year arguments provided.")
                year = arg_int
            elif 1 <= arg_int <= 17:
                if week is not None:
                    raise ValueError("Multiple week arguments provided.")
                week = arg_int
            else:
                raise ValueError("Invalid integer argument provided.")
        else:
            # Non-integer -> attempt manager match
            if arg in NAME_TO_MANAGER_USERNAME:
                if manager is not None:
                    raise ValueError("Multiple manager arguments provided.")
                manager = arg
                continue
            else:
                raise ValueError(f"Invalid argument provided: {arg}")

    if week is not None and year is None:
        # Week without season is not meaningful
        raise ValueError("Week provided without a corresponding year.")

    return year, week, manager

def _flatten_dict(d, parent_key="", sep="."):
    """
    Recursively flatten a nested dict into a single-level dict.

    Keys are concatenated with the provided separator. Non-dict values are
    copied directly. Non-dict inputs yield an empty dict.

    Args:
        d (dict | any): Potentially nested dictionary to flatten.
        parent_key (str): Prefix carried through recursive calls.
        sep (str): Separator for concatenated keys.

    Returns:
        dict: Flattened dictionary.
    """
    out = {}
    for k, v in (d or {}).items() if isinstance(d, dict) else []:
        nk = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            # Recurse into nested dicts
            out.update(_flatten_dict(v, nk, sep))
        else:
            out[nk] = v
    return out

def _to_records(data, key_name="key"):
    """
    Normalize mixed dict/list structures into a list of record dicts.

    - Lists of dicts -> flattened dict per item.
    - Dicts -> each key becomes a record; nested dict/list values are expanded.
    - Scalars -> wrapped into a single record.

    Args:
        data (dict | list | any): Input structure.
        key_name (str): Field name to assign original dict keys.

    Returns:
        list[dict]: List of normalized record dictionaries.
    """
    if isinstance(data, list):
        return [(_flatten_dict(x) if isinstance(x, dict) else {"value": x}) for x in data]
    if isinstance(data, dict):
        rows = []
        for k, v in data.items():
            if isinstance(v, list):
                # Expand list items under the same key
                for item in v:
                    row = {key_name: k}
                    row.update(_flatten_dict(item) if isinstance(item, dict) else {"value": item})
                    rows.append(row)
            elif isinstance(v, dict):
                row = {key_name: k}
                row.update(_flatten_dict(v))
                rows.append(row)
            else:
                rows.append({key_name: k, "value": v})

        # sort the records by key_name if possible
        rows.sort(key=lambda x: x.get(key_name, ""), reverse=False)

        return rows

    # Fallback for scalar values
    return [{"value": data}]

if __name__ == '__main__':
    from os import getenv
    app.run(host="0.0.0.0", port=int(getenv("PORT", "8080")))
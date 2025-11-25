from flask import Flask, jsonify, request
from constants import LEAGUE_IDS, NAME_TO_MANAGER_USERNAME
from services.managers import fetch_starters
from services.aggregated_data import fetch_aggregated_players, fetch_aggregated_managers

app = Flask(__name__)

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
        return rows
    # Fallback for scalar values
    return [{"value": data}]

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
    try:
        year, week, manager = parse_arguments(arg1, arg2, arg3)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

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
    try:
        year, week, _ = parse_arguments(arg2, arg3, None)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    player = player.replace("_", " ")

    data = fetch_aggregated_managers(player=player, season=year, week=week)
    if request.args.get("format") == "json":
        return jsonify(data), 200
    return jsonify(_to_records(data, key_name="player")), 200

@app.route('/meta/options', methods=['GET'])
def meta_options():
    """
    Expose selectable seasons, weeks, and managers for frontend filters.
    Omitting any in requests to /get_aggregated_players yields ALL for that category.
    """
    return jsonify({
        "seasons": list(LEAGUE_IDS),
        "weeks": list(range(1, 15)),
        "managers": list(NAME_TO_MANAGER_USERNAME.keys())
    }), 200

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
        try:
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
        except ValueError:
            # Non-integer -> attempt manager match
            if arg in NAME_TO_MANAGER_USERNAME:
                if manager is not None:
                    raise ValueError("Multiple manager arguments provided.")
                manager = arg
            else:
                raise ValueError(f"Invalid argument provided: {arg}")

    if week is not None and year is None:
        # Week without season is not meaningful
        raise ValueError("Week provided without a corresponding year.")

    return year, week, manager

if __name__ == '__main__':
    import os
    port = int(os.getenv("PORT", 5050))
    # Bind to localhost for development; configurable port via env
    app.run(debug=True, host="127.0.0.1", port=port)
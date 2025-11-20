from flask import Flask, jsonify
from constants import LEAGUE_IDS, NAME_TO_MANAGER_USERNAME
from patriot_center_backend.services.managers import fetch_starters
from patriot_center_backend.services.aggregated_data import fetch_aggregated_players

app = Flask(__name__)

@app.route('/api/arg2s/get_starters', defaults={'arg1': None, 'arg2': None, 'arg3': None}, methods=['GET'])
@app.route('/api/arg2s/get_starters/<string:arg1>', defaults={'arg2': None, 'arg3': None}, methods=['GET'])
@app.route('/api/arg2s/get_starters/<string:arg1>/<string:arg2>', defaults={'arg3': None}, methods=['GET'])
@app.route('/api/arg2s/get_starters/<string:arg1>/<string:arg2>/<string:arg3>', methods=['GET'])
def get_starters(arg1, arg2, arg3):
    """
    API endpoint to fetch starters based on year, manager, and/or week.

    Args:
        arg1, arg2, arg3: Optional arguments that can represent year, manager, or week.

    Returns:
        JSON response with the requested data or an error message.
    """
    try:
        # Parse and validate the arguments
        year, manager, week = parse_arguments(arg1, arg2, arg3)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Fetch the starters data
    data = fetch_starters(season=year, manager=manager, week=week)
    return jsonify(data), 200

@app.route('/api/arg2s/get_starters', defaults={'arg1': None, 'arg2': None, 'arg3': None}, methods=['GET'])
@app.route('/api/arg2s/get_starters/<string:arg1>', defaults={'arg2': None, 'arg3': None}, methods=['GET'])
@app.route('/api/arg2s/get_starters/<string:arg1>/<string:arg2>', defaults={'arg3': None}, methods=['GET'])
@app.route('/api/arg2s/get_starters/<string:arg1>/<string:arg2>/<string:arg3>', methods=['GET'])
def get_aggregated_players(arg1, arg2, arg3):
    """
    API endpoint to fetch starters in an aggregated json based on year, manager, and/or week.

    Args:
        arg1, arg2, arg3: Optional arguments that can represent year, manager, or week.

    Returns:
        JSON response with the requested data or an error message.
    """
    try:
        # Parse and validate the arguments
        year, manager, week = parse_arguments(arg1, arg2, arg3)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Fetch the starters data
    data = fetch_aggregated_players(season=year, manager=manager, week=week)
    return jsonify(data), 200

@app.route('/api/arg2s/get_starters/<string:player>', defaults={'arg2': None, 'arg3': None}, methods=['GET'])
@app.route('/api/arg2s/get_starters/<string:player>/<string:arg2>', defaults={'arg3': None}, methods=['GET'])
@app.route('/api/arg2s/get_starters/<string:player>/<string:arg2>/<string:arg3>', methods=['GET'])
def get_aggregated_managers(arg1, arg2, arg3):
    """
    API endpoint to fetch starters in an aggregated json based on year, manager, and/or week.

    Args:
        arg1, arg2, arg3: Optional arguments that can represent year, manager, or week.

    Returns:
        JSON response with the requested data or an error message.
    """
    try:
        # Parse and validate the arguments
        year, manager, week = parse_arguments(arg1, arg2, arg3)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Fetch the starters data
    data = fetch_aggregated_players(season=year, manager=manager, week=week)
    return jsonify(data), 200

def parse_arguments(arg1, arg2, arg3):
    """
    Parse and validate the input arguments.

    Args:
        arg1, arg2, arg3: Optional arguments that can represent year, manager, or week.

    Returns:
        tuple: (year, manager, week)

    Raises:
        ValueError: If the arguments are invalid or conflicting.
    """
    year = None
    manager = None
    week = None

    args = [arg1, arg2, arg3]
    for arg in args:
        if arg is None:
            continue

        # Check if the argument is an integer
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
            # Argument is not an integer, check if it's a manager name
            if arg in NAME_TO_MANAGER_USERNAME:
                if manager is not None:
                    raise ValueError("Multiple manager arguments provided.")
                manager = arg
            else:
                raise ValueError(f"Invalid argument provided: {arg}")
            
    if week is not None and year is None:
        raise ValueError("Week provided without a corresponding year.")

    return year, manager, week

if __name__ == '__main__':
    app.run(debug=True)
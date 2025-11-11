import requests
from flask import Flask, jsonify
from constants import LEAGUE_IDS, MANAGER_MAP, SEASONS

app = Flask(__name__)

@app.route('/api/league_reference')
def league_reference():
    data = {
        "league_ids": LEAGUE_IDS,
        "seasons": SEASONS,
        "managers": MANAGER_MAP
    }
    return jsonify(data)

@app.route('/api/test_league_members/<int:year>')
def test_league_members(year):
    league_id = LEAGUE_IDS.get(year)
    url = f"https://api.sleeper.app/v1/league/{league_id}/users"
    resp = requests.get(url)
    users = resp.json()
    # Map usernames to display names
    member_display = [
        {
            "username": user['display_name'],
            "real_name": MANAGER_MAP.get(user['display_name'], "Unknown")
        }
        for user in users
    ]
    return jsonify(member_display)

if __name__ == '__main__':
    app.run(debug=True)
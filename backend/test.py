import requests
from flask import Flask, jsonify
from constants import LEAGUE_IDS, MANAGER_MAP

app = Flask(__name__)


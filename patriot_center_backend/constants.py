# patriot_center_backend/constants.py

# Map year to the league ids
LEAGUE_IDS = {
    2019: "399260536505671680",
    2020: "567745628522500096",
    2021: "650026670341861376",
    2022: "784823696450772992",
    2023: "979405891168493568",
    2024: "1113631749025796096",
    2025: "1256401636973101056",
}

# Map usernames to real name for display
USERNAME_TO_REAL_NAME = {
    "aalvaa":          "Anthony",
    "bbennick":        "Benz",
    "BilliamBlowland": "Billiam",
    "senorpapi":       "Christian",
    "codestoppable":   "Cody",
    "dpereira7":       "Davey",
    "BrownBoyLove":    "Dheeraj",
    "jkjackson16":     "Jack",
    "Jrazzam":         "Jay",
    "lukehellyer":     "Luke",
    "mitchwest":       "Mitch",
    "owen0010":        "Owen",
    "parkdaddy":       "Parker",
    "Siemonster":      "Sach",
    "samprice18":      "Sam",
    "charris34":       "Soup",
    "tommylowry":      "Tommy",
    "bispity":         "Ty"
}

# Invert the MANAGER_USERNAME_TO_REAL_NAME mapping
NAME_TO_MANAGER_USERNAME = {v: k for k, v in USERNAME_TO_REAL_NAME.items()}

# Sleeper API base URL
SLEEPER_API_URL = "https://api.sleeper.app/v1"

# Map scoring_settings.yml to sleeper api stat keys

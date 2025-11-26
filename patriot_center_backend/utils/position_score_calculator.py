from pathlib import Path
from typing import Dict
import yaml 

def _load_scoring_settings() -> Dict[str, float]:
    scoring_path = Path.cwd() / "config" / "scoring_settings.yml"
    with scoring_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    sleeper_api_value = {
        # Passing
        "pass_yd":   data.get("passing_yards", 0),
        "pass_td":   data.get("passing_td", 0),
        "pass_2pt":  data.get("passing_2pt_conversion", 0),
        "pass_int":  data.get("pass_intercepted", 0),


        # Rushing
        "rush_yd":  data.get("rushing_yards", 0),
        "rush_td":  data.get("rushing_td", 0),
        "rush_2pt": data.get("rushing_2pt_conversion", 0),


        # Receiving
        "rec":     data.get("reception", 0),
        "rec_yd":  data.get("receiving_yards", 0),
        "rec_td":  data.get("receiving_td", 0),
        "rec_2pt": data.get("receiving_2pt_conversion", 0),


        # Kicking
        "fgm_0_19":    data.get("fg_made_0-19", 0),
        "fgm_20_29":   data.get("fg_made_20-29", 0),
        "fgm_30_39":   data.get("fg_made_30-39", 0),
        "fgm_40_49":   data.get("fg_made_40-49", 0),
        "fgm_50p":     data.get("fg_made_50+", 0),
        "xpm":         data.get("pat_made", 0),

        "fgmiss_0_19":  data.get("fg_missed_0-19", 0),
        "fgmiss_20_29": data.get("fg_missed_20-29", 0),
        "fgmiss_30_39": data.get("fg_missed_30-39", 0),
        "fgmiss_40_49": data.get("fg_missed_40-49", 0),
        "fgmiss_50p":   data.get("fg_missed_50+", 0),
        "xpmiss":       data.get("pat_missed", 0),


        # Team Defense
        "def_td":         data.get("defensive_td", 0),
        "sack":           data.get("sacks", 0),
        "int":            data.get("interceptions", 0),
        "fum_rec":        data.get("fumble_recovery", 0),
        "safe":           data.get("safety", 0),
        "ff":             data.get("fumble_forced", 0),
        "blk_kick":       data.get("blocked_kick", 0),

        "pts_allow_0":   data.get("points_allowed_0", 0),
        "pts_allow_1_6": data.get("points_allowed_1-6", 0),
        "pts_allow_7_13": data.get("points_allowed_7-13", 0),
        "pts_allow_14_20": data.get("points_allowed_14-20", 0),
        "pts_allow_21_27": data.get("points_allowed_21-27", 0),
        "pts_allow_28_34": data.get("points_allowed_28-34", 0),
        "pts_allow_35p":   data.get("points_allowed_35+", 0),

        "yds_allow_0_100":  data.get("less_than_100_yards_allowed", 0),
        "yds_allow_100_199": data.get("100-199_yards_allowed", 0),
        "yds_allow_200_299": data.get("200-299_yards_allowed", 0),
        "yds_allow_300_349": data.get("300-349_yards_allowed", 0),
        "yds_allow_350_399": data.get("350-399_yards_allowed", 0),
        "yds_allow_400_449": data.get("400-449_yards_allowed", 0),
        "yds_allow_450_499": data.get("450-499_yards_allowed", 0),
        "yds_allow_500_549": data.get("500-549_yards_allowed", 0),
        "yds_allow_550p":    data.get("550+_yards_allowed", 0),

        "def_st_td":      data.get("special_teams_td", 0),
        "def_st_ff":      data.get("special_teams_forced_fumble", 0),
        "def_st_fum_rec": data.get("special_teams_fumble_recovery", 0),


        # Special Teams Player
        "st_td":      data.get("special_teams_player_td", 0),
        "st_ff":      data.get("special_teams_player_forced_fumble", 0),
        "st_fum_rec": data.get("special_teams_player_fumble_recovery", 0),


        # Misc
        "fum":        data.get("fumble", 0),
        "fum_lost":   data.get("fumble_lost", 0),
        "fum_rec_td": data.get("fumble_recovery_td", 0)
    }
    return sleeper_api_value

def calculate_player_score(player_data: Dict[str, float]) -> float:
    
    scoring_settings = _load_scoring_settings()

    total_score = 0.0
    for stat_key, stat_value in player_data.items():

        if stat_key.startswith("pts_allow_") or stat_key.startswith("yds_allow_"):
            if stat_key not in scoring_settings and stat_key[-1].isnumeric():
                print("Warning: Missing scoring setting for", stat_key)


        if stat_key in scoring_settings:
            points_per_unit = scoring_settings[stat_key]
            total_score += stat_value * points_per_unit
    return total_score
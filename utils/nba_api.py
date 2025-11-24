import requests
from datetime import date

API_BASE = "https://api.balldontlie.io/v1/games"


API_KEY = "d6d8cded-3a7a-4aae-8675-b8ad9f873320"

def get_today_games():
    """Holt die heutigen NBA-Spiele von der balldontlie v2 API."""
    today = date.today().isoformat()

    headers = {
        "Authorization": API_KEY
    }

    params = {
        "start_date": today,
        "end_date": today,
        "per_page": 100
    }

    try:
        response = requests.get(API_BASE, params=params, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print("Fehler beim Laden der Spiele:", e)
        return []

    data = response.json().get("data", [])

    games = []
    for g in data:
        games.append(
            {
                "home": g["home_team"]["full_name"],
                "visitor": g["visitor_team"]["full_name"],
            }
        )

    return games

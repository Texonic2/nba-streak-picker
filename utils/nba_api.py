import requests
from datetime import date
import os
import json

# Basis-URL der balldontlie-API (v2)
API_BASE = "https://api.balldontlie.io/v1/games"

# 🔥 HIER deinen API-Key eintragen (NICHT im Chat posten!)
API_KEY = "d6d8cded-3a7a-4aae-8675-b8ad9f873320"

# Lokaler Cache für Spiele pro Datum, um API-Calls zu sparen
GAMES_CACHE_FILE = os.path.join("data", "games_cache.json")
_games_cache = {}  # key: "YYYY-MM-DD", value: Liste von Spielen


def _ensure_cache_loaded():
    """Lädt den Cache einmalig aus der Datei."""
    global _games_cache

    # data-Ordner sicherstellen
    os.makedirs(os.path.dirname(GAMES_CACHE_FILE), exist_ok=True)

    if _games_cache:
        return

    if not os.path.exists(GAMES_CACHE_FILE):
        _games_cache = {}
        return

    try:
        with open(GAMES_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                _games_cache = data
            else:
                _games_cache = {}
    except (json.JSONDecodeError, FileNotFoundError):
        _games_cache = {}


def _save_cache():
    """Speichert den Cache in die Datei."""
    with open(GAMES_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(_games_cache, f, ensure_ascii=False, indent=2)


def get_games_for_date(day: date):
    """
    Holt alle Spiele für ein bestimmtes Datum.
    - Wenn im Cache vorhanden → von dort lesen (kein API-Call).
    - Sonst einmal von der API holen, in Cache speichern.
    Rückgabe: Liste von Dicts mit 'home' und 'visitor'.
    """
    _ensure_cache_loaded()

    day_str = day.isoformat()

    # 1) Wenn im Cache → direkt zurückgeben
    if day_str in _games_cache:
        return _games_cache[day_str]

    # 2) Sonst von der API holen
    headers = {
        "Authorization": API_KEY  # laut Doku: Authorization: <key>
    }
    params = {
        "start_date": day_str,
        "end_date": day_str,
        "per_page": 100
    }

    try:
        response = requests.get(API_BASE, params=params, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print("Fehler beim Laden der Spiele:", e)
        # Falls irgendwann später schon mal gecached wurde:
        return _games_cache.get(day_str, [])

    data = response.json().get("data", [])

    games = []
    for g in data:
        games.append(
            {
                "home": g["home_team"]["full_name"],
                "visitor": g["visitor_team"]["full_name"],
            }
        )

    # 3) Im Cache speichern
    _games_cache[day_str] = games
    _save_cache()

    return games


def get_today_games():
    """
    Komfortfunktion: Spiele für heute.
    """
    return get_games_for_date(date.today())

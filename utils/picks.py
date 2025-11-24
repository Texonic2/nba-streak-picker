# utils/picks.py
import json
import os

PICKS_FILE = os.path.join("data", "picks.json")

# Liste von Dicts: {"date": "YYYY-MM-DD", "team": "Los Angeles Lakers"}
picks = []


def _ensure_file():
    """Stellt sicher, dass data-Ordner und JSON-Datei existieren."""
    os.makedirs(os.path.dirname(PICKS_FILE), exist_ok=True)

    if not os.path.exists(PICKS_FILE):
        with open(PICKS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def load_picks(show: bool = False):
    """Picks aus Datei laden; optional anzeigen."""
    global picks
    _ensure_file()

    try:
        with open(PICKS_FILE, "r", encoding="utf-8") as f:
            picks = json.load(f)
            if not isinstance(picks, list):
                picks = []
    except (json.JSONDecodeError, FileNotFoundError):
        picks = []

    if show:
        print("=== Deine bisherigen Picks ===")
        if not picks:
            print("Noch keine Picks vorhanden.")
        else:
            for i, p in enumerate(picks, start=1):
                print(f"{i}. {p['date']} – {p['team']}")


def save_pick(team: str, pick_date: str):
    """Neuen Pick (Datum + Team) speichern."""
    global picks
    team = team.strip()
    if not team:
        return

    picks.append({"date": pick_date, "team": team})

    with open(PICKS_FILE, "w", encoding="utf-8") as f:
        json.dump(picks, f, ensure_ascii=False, indent=2)


def already_picked(team: str) -> bool:
    """True, wenn Team irgendwann schon getippt wurde (case-insensitive)."""
    tl = team.lower().strip()
    return any(p["team"].lower() == tl for p in picks)

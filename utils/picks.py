import json
import os
from typing import List, Dict, Any

# Datei, in der alle Picks gespeichert werden
PICKS_FILE = os.path.join("data", "picks.json")

# Globale Liste von Picks:
# [{"date": "YYYY-MM-DD", "team": "Miami Heat", "run": 1}, ...]
picks: List[Dict[str, Any]] = []


def _ensure_file():
    """
    Stellt sicher, dass data-Ordner und picks.json existieren.
    """
    os.makedirs(os.path.dirname(PICKS_FILE), exist_ok=True)

    if not os.path.exists(PICKS_FILE):
        with open(PICKS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def _save():
    """
    Schreibt den aktuellen Inhalt von 'picks' in die Datei.
    """
    with open(PICKS_FILE, "w", encoding="utf-8") as f:
        json.dump(picks, f, ensure_ascii=False, indent=2)


def load_picks(show: bool = False):
    """
    Lädt Picks aus der JSON-Datei in die globale Variable 'picks'.
    Normalisiert auch ältere Formate (nur Team oder ohne run).
    """
    global picks
    _ensure_file()

    try:
        with open(PICKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = []

    normalized: List[Dict[str, Any]] = []

    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict):
                team = entry.get("team")
                if not team:
                    continue
                date_val = entry.get("date", "unknown")
                run_val = int(entry.get("run", 1))
                normalized.append({"date": date_val, "team": team, "run": run_val})
            elif isinstance(entry, str):
                # ganz alte Struktur: nur Teamname
                normalized.append({"date": "unknown", "team": entry, "run": 1})

    picks = normalized

    if show:
        print("=== Deine bisherigen Picks (alle Läufe) ===")
        if not picks:
            print("Noch keine Picks vorhanden.")
        else:
            for i, p in enumerate(picks, start=1):
                print(f"{i}. Lauf {p['run']} – {p['date']} – {p['team']}")


def get_runs() -> List[int]:
    """
    Gibt alle vorhandenen Lauf-Nummern sortiert zurück.
    Wenn noch nichts da ist → [1].
    """
    if not picks:
        return [1]
    runs = sorted({int(p.get("run", 1)) for p in picks})
    return runs or [1]


def get_picks_for_run(run: int) -> List[Dict[str, Any]]:
    """
    Gibt alle Picks für einen bestimmten Lauf zurück.
    Jeder Eintrag enthält zusätzlich den globalen Index.
    """
    result: List[Dict[str, Any]] = []
    for i, p in enumerate(picks):
        r = int(p.get("run", 1))
        if r == run:
            result.append(
                {
                    "index": i,  # globaler Index in der Liste 'picks'
                    "date": p.get("date", "unknown"),
                    "team": p.get("team", ""),
                    "run": r,
                }
            )
    return result


def save_pick(team: str, pick_date: str, run: int):
    """
    Speichert einen neuen Pick (Datum + Team + Lauf).
    """
    global picks

    team = team.strip()
    if not team:
        return

    picks.append(
        {
            "date": pick_date,
            "team": team,
            "run": int(run),
        }
    )

    _save()


def already_picked(team: str, run: int) -> bool:
    """
    Prüft, ob dieses Team im selben Lauf schon getippt wurde (case-insensitive).
    """
    tl = team.lower().strip()
    for p in picks:
        if int(p.get("run", 1)) == int(run) and p.get("team", "").lower() == tl:
            return True
    return False


def has_pick_on_date(date_str: str, run: int) -> bool:
    """
    Prüft, ob in diesem Lauf an diesem Datum schon ein Pick existiert.
    """
    for p in picks:
        if int(p.get("run", 1)) == int(run) and p.get("date") == date_str:
            return True
    return False


def get_all_picks() -> List[Dict[str, Any]]:
    """
    Gibt alle Picks zurück (falls du irgendwann Statistiken willst).
    """
    return picks


def delete_pick(index: int):
    """
    Löscht einen Pick anhand seines globalen Index.
    """
    global picks
    if 0 <= index < len(picks):
        picks.pop(index)
        _save()


def swap_picks(index_a: int, index_b: int):
    """
    Tauscht zwei Picks anhand ihrer globalen Indizes.
    """
    global picks
    if (
        0 <= index_a < len(picks)
        and 0 <= index_b < len(picks)
        and index_a != index_b
    ):
        picks[index_a], picks[index_b] = picks[index_b], picks[index_a]
        _save()

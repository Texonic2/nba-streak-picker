import os
import sys
from datetime import date

# Projektordner auf den Python-Pfad setzen
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from utils.picks import load_picks, save_pick, already_picked, has_pick_on_date
from utils.nba_api import get_today_games


def show_menu():
    print("\n=== NBA Streak Picker ===")
    print("1. Heutige Spiele anzeigen")
    print("2. Team für heute auswählen")
    print("3. Meine Picks anzeigen")
    print("4. Beenden")


def show_today_games():
    games = get_today_games()

    print("=== Heutige Spiele ===")
    if not games:
        print("Keine Spiele heute (oder API-Problem).")
        return

    for i, g in enumerate(games, start=1):
        print(f"{i}. {g['visitor']} @ {g['home']}")


def pick_team_for_today():
    """Einen Pick für den heutigen Tag machen."""
    # Picks laden (falls sich extern was geändert hat)
    load_picks()

    today_str = date.today().isoformat()

    if has_pick_on_date(today_str):
        print(f"✖ Du hast für heute ({today_str}) bereits ein Team getippt.")
        return

    games = get_today_games()
    if not games:
        print("Heute gibt es keine Spiele (oder API-Problem).")
        return

    # Alle Teams, die heute spielen
    teams_today = sorted({g["home"] for g in games} | {g["visitor"] for g in games})

    print("=== Teams, die heute spielen ===")
    for i, t in enumerate(teams_today, start=1):
        print(f"{i}. {t}")

    auswahl = input("Nummer oder Teamname eingeben: ").strip()

    team = None

    # Nutzer gibt eine Zahl ein
    if auswahl.isdigit():
        idx = int(auswahl)
        if 1 <= idx <= len(teams_today):
            team = teams_today[idx - 1]
        else:
            print("✖ Ungültige Nummer.")
            return
    else:
        # Nutzer gibt einen Teamnamen ein
        matches = [t for t in teams_today if t.lower() == auswahl.lower()]
        if not matches:
            print(f"✖ '{auswahl}' spielt heute nicht.")
            return
        team = matches[0]

    if already_picked(team):
        print(f"✖ Team '{team}' wurde bereits an einem anderen Tag getippt!")
        return

    save_pick(team, today_str)
    print(f"✔ Pick gespeichert: {today_str} – {team}")


def main():
    # Bestehende Picks einmal initial laden
    load_picks()

    while True:
        show_menu()
        choice = input("Auswahl: ").strip()

        if choice == "1":
            show_today_games()

        elif choice == "2":
            pick_team_for_today()

        elif choice == "3":
            load_picks(show=True)

        elif choice == "4":
            print("Bye! 🏀")
            break

        else:
            print("Ungültige Auswahl!")


if __name__ == "__main__":
    main()

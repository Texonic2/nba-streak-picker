# main.py
import os
import sys
from datetime import date

# Sicherstellen, dass der Projektordner auf dem Python-Pfad ist
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from utils.picks import load_picks, save_pick, already_picked
from utils.nba_api import get_today_games


def show_menu():
    print("\n=== NBA Streak Picker ===")
    print("1. Heutige Spiele anzeigen")
    print("2. Team für heute auswählen")
    print("3. Meine Picks anzeigen")
    print("4. Beenden")


def show_today_games(games):
    print("=== Heutige Spiele ===")
    if not games:
        print("Keine Spiele heute (oder API-Problem).")
        return

    for i, g in enumerate(games, start=1):
        print(f"{i}. {g['visitor']} @ {g['home']}")


def main():
    # vorhandene Picks laden
    load_picks()

    while True:
        show_menu()
        choice = input("Auswahl: ").strip()

        if choice == "1":
            games = get_today_games()
            # Feldnamen anpassen für die Ausgabe
            games_pretty = [
                {"home": g["home"], "visitor": g["visitor"]} for g in games
            ]
            show_today_games(
                [{"home": g["home"], "visitor": g["visitor"]} for g in games]
            )

        elif choice == "2":
            games = get_today_games()

            if not games:
                print("Heute gibt es keine Spiele (oder API-Problem).")
                continue

            # Alle Teams, die heute spielen
            teams_today = set()
            for g in games:
                teams_today.add(g["home"])
                teams_today.add(g["visitor"])

            print("Teams, die heute spielen:")
            for t in sorted(teams_today):
                print(" -", t)

            team = input("Welches Team tippst du heute? ").strip()

            if team not in teams_today:
                print(f"✖ '{team}' spielt heute nicht.")
                continue

            if already_picked(team):
                print(f"✖ Team '{team}' wurde bereits an einem anderen Tag getippt!")
                continue

            today_str = date.today().isoformat()
            save_pick(team, today_str)
            print(f"✔ Pick gespeichert: {today_str} – {team}")

        elif choice == "3":
            load_picks(show=True)

        elif choice == "4":
            print("Bye!")
            break

        else:
            print("Ungültige Auswahl!")


if __name__ == "__main__":
    main()

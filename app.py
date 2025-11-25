from datetime import date, timedelta
import os
import sys
import calendar

from flask import Flask, render_template, request, redirect, url_for

# Projektordner auf Python-Pfad setzen (falls nötig)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from utils.picks import (
    load_picks,
    save_pick,
    already_picked,
    has_pick_on_date,
    get_runs,
    get_picks_for_run,
    delete_pick,
    swap_picks,
)
from utils.nba_api import get_games_for_date

app = Flask(__name__)
app.secret_key = "d6d8cded-3a7a-4aae-8675-b8ad9f873320"

# Logo-Mapping für Teams
TEAM_LOGOS = {
    "Atlanta Hawks": "https://cdn.nba.com/logos/nba/1610612737/global/L/logo.svg",
    "Boston Celtics": "https://cdn.nba.com/logos/nba/1610612738/global/L/logo.svg",
    "Brooklyn Nets": "https://cdn.nba.com/logos/nba/1610612751/global/L/logo.svg",
    "Charlotte Hornets": "https://cdn.nba.com/logos/nba/1610612766/global/L/logo.svg",
    "Chicago Bulls": "https://cdn.nba.com/logos/nba/1610612741/global/L/logo.svg",
    "Cleveland Cavaliers": "https://cdn.nba.com/logos/nba/1610612739/global/L/logo.svg",
    "Dallas Mavericks": "https://cdn.nba.com/logos/nba/1610612742/global/L/logo.svg",
    "Denver Nuggets": "https://cdn.nba.com/logos/nba/1610612743/global/L/logo.svg",
    "Detroit Pistons": "https://cdn.nba.com/logos/nba/1610612765/global/L/logo.svg",
    "Golden State Warriors": "https://cdn.nba.com/logos/nba/1610612744/global/L/logo.svg",
    "Houston Rockets": "https://cdn.nba.com/logos/nba/1610612745/global/L/logo.svg",
    "Indiana Pacers": "https://cdn.nba.com/logos/nba/1610612754/global/L/logo.svg",
    "Los Angeles Clippers": "https://cdn.nba.com/logos/nba/1610612746/global/L/logo.svg",
    "Los Angeles Lakers": "https://cdn.nba.com/logos/nba/1610612747/global/L/logo.svg",
    "Memphis Grizzlies": "https://cdn.nba.com/logos/nba/1610612763/global/L/logo.svg",
    "Miami Heat": "https://cdn.nba.com/logos/nba/1610612748/global/L/logo.svg",
    "Milwaukee Bucks": "https://cdn.nba.com/logos/nba/1610612749/global/L/logo.svg",
    "Minnesota Timberwolves": "https://cdn.nba.com/logos/nba/1610612750/global/L/logo.svg",
    "New Orleans Pelicans": "https://cdn.nba.com/logos/nba/1610612740/global/L/logo.svg",
    "New York Knicks": "https://cdn.nba.com/logos/nba/1610612752/global/L/logo.svg",
    "Oklahoma City Thunder": "https://cdn.nba.com/logos/nba/1610612760/global/L/logo.svg",
    "Orlando Magic": "https://cdn.nba.com/logos/nba/1610612753/global/L/logo.svg",
    "Philadelphia 76ers": "https://cdn.nba.com/logos/nba/1610612755/global/L/logo.svg",
    "Phoenix Suns": "https://cdn.nba.com/logos/nba/1610612756/global/L/logo.svg",
    "Portland Trail Blazers": "https://cdn.nba.com/logos/nba/1610612757/global/L/logo.svg",
    "Sacramento Kings": "https://cdn.nba.com/logos/nba/1610612758/global/L/logo.svg",
    "San Antonio Spurs": "https://cdn.nba.com/logos/nba/1610612759/global/L/logo.svg",
    "Toronto Raptors": "https://cdn.nba.com/logos/nba/1610612761/global/L/logo.svg",
    "Utah Jazz": "https://cdn.nba.com/logos/nba/1610612762/global/L/logo.svg",
    "Washington Wizards": "https://cdn.nba.com/logos/nba/1610612764/global/L/logo.svg",
}


def _get_current_run_from_request(runs):
    run_param = request.args.get("run", type=int)
    if run_param is not None:
        return run_param
    return max(runs) if runs else 1


def _get_current_day_from_request():
    day_param = request.args.get("day")
    if day_param:
        try:
            return date.fromisoformat(day_param)
        except ValueError:
            pass
    return date.today()


@app.route("/", methods=["GET", "POST"])
def index():
    load_picks()
    runs = get_runs()
    current_run = _get_current_run_from_request(runs)

    if current_run not in runs:
        runs.append(current_run)
        runs = sorted(set(runs))

    current_day = _get_current_day_from_request()
    current_day_str = current_day.isoformat()
    today = date.today()

    message = None
    error = None

    # === POST: Team aus Matchup picken ===
    if request.method == "POST":
        team = request.form.get("team", "").strip()
        form_run = request.form.get("run", type=int)
        form_day = request.form.get("day")

        if form_run is not None:
            current_run = form_run
        if form_day:
            try:
                current_day = date.fromisoformat(form_day)
                current_day_str = current_day.isoformat()
            except ValueError:
                pass

        # Spiele für das Formular-Datum holen
        games_for_form = get_games_for_date(current_day)
        if games_for_form:
            teams_today = sorted(
                {g["home"] for g in games_for_form} | {g["visitor"] for g in games_for_form}
            )
        else:
            teams_today = []

        if not team:
            error = "Bitte ein Team auswählen."
        elif team not in teams_today:
            error = f"'{team}' spielt an diesem Spieltag nicht."
        elif has_pick_on_date(current_day_str, current_run):
            error = (
                f"Du hast für den Spieltag {current_day_str} "
                f"in Lauf {current_run} bereits ein Team getippt."
            )
        elif already_picked(team, current_run):
            error = (
                f"Team '{team}' wurde in Lauf {current_run} "
                f"bereits an einem anderen Spieltag getippt."
            )
        else:
            save_pick(team, current_day_str, current_run)
            next_day_redirect = current_day + timedelta(days=1)
            return redirect(
                url_for(
                    "index",
                    run=current_run,
                    day=next_day_redirect.isoformat(),
                )
            )

    # === Spiele & Matchup-Karten für aktuellen Tag ===
    games = get_games_for_date(current_day)

    if games:
        teams_today = sorted(
            {g["home"] for g in games} | {g["visitor"] for g in games}
        )
    else:
        teams_today = []

    game_cards = []
    for g in games:
        visitor_name = g["visitor"]
        home_name = g["home"]

        game_cards.append(
            {
                "visitor": {
                    "name": visitor_name,
                    "logo": TEAM_LOGOS.get(visitor_name),
                    "picked": already_picked(visitor_name, current_run),
                },
                "home": {
                    "name": home_name,
                    "logo": TEAM_LOGOS.get(home_name),
                    "picked": already_picked(home_name, current_run),
                },
            }
        )

    # Tages-Navigation (+/- 1 Tag)
    prev_day = current_day - timedelta(days=1)
    next_day = current_day + timedelta(days=1)
    prev_day_str = prev_day.isoformat()
    next_day_str = next_day.isoformat()

    # === Picks laden (für Liste & Kalender) ===
    picks_for_run = get_picks_for_run(current_run)

    # Set von Pick-Daten im aktuellen Lauf
    pick_dates = set()
    for p in picks_for_run:
        try:
            d = date.fromisoformat(p["date"])
            pick_dates.add(d)
        except ValueError:
            continue

    # Back-to-back: Datum, an dem auch der Vortag ein Pick war
    b2b_dates = set()
    for d in pick_dates:
        if d - timedelta(days=1) in pick_dates:
            b2b_dates.add(d)

    # === Monatskalender vorbereiten ===
    cal = calendar.Calendar(firstweekday=0)  # 0 = Montag
    month_weeks = []
    for week in cal.monthdatescalendar(current_day.year, current_day.month):
        week_cells = []
        for d in week:
            in_month = (d.month == current_day.month)
            if not in_month:
                css_class = "day-other"
            else:
                if d in b2b_dates:
                    css_class = "day-b2b"      # Rot
                elif d in pick_dates:
                    css_class = "day-picked"   # Grün
                elif d >= today:
                    css_class = "day-future"   # Gelb
                else:
                    css_class = "day-empty"    # Grau

            week_cells.append(
                {
                    "date": d.isoformat(),
                    "day": d.day,
                    "in_month": in_month,
                    "css_class": css_class,
                }
            )
        month_weeks.append(week_cells)

    # Monatslabel & Navigation
    month_label = current_day.strftime("%B %Y")  # z.B. "November 2025"

    if current_day.month == 1:
        prev_month_day = date(current_day.year - 1, 12, 1)
    else:
        prev_month_day = date(current_day.year, current_day.month - 1, 1)

    if current_day.month == 12:
        next_month_day = date(current_day.year + 1, 1, 1)
    else:
        next_month_day = date(current_day.year, current_day.month + 1, 1)

    prev_month_str = prev_month_day.isoformat()
    next_month_str = next_month_day.isoformat()

    return render_template(
        "index.html",
        current_day=current_day_str,
        game_cards=game_cards,
        picks=picks_for_run,
        runs=runs,
        current_run=current_run,
        message=message,
        error=error,
        prev_day=prev_day_str,
        next_day=next_day_str,
        TEAM_LOGOS=TEAM_LOGOS,
        month_weeks=month_weeks,
        month_label=month_label,
        prev_month_day=prev_month_str,
        next_month_day=next_month_str,
    )


@app.route("/new_run")
def new_run():
    load_picks()
    runs = get_runs()
    new_run_id = max(runs) + 1 if runs else 1
    day_param = request.args.get("day")
    if not day_param:
        day_param = date.today().isoformat()
    return redirect(url_for("index", run=new_run_id, day=day_param))


@app.route("/delete_pick", methods=["POST"])
def delete_pick_route():
    index = request.form.get("index", type=int)
    run = request.form.get("run", type=int)
    day = request.form.get("day")

    if index is not None:
        load_picks()
        delete_pick(index)

    return redirect(
        url_for(
            "index",
            run=run or 1,
            day=day or date.today().isoformat(),
        )
    )


@app.route("/swap_picks", methods=["POST"])
def swap_picks_route():
    index_a = request.form.get("index_a", type=int)
    index_b = request.form.get("index_b", type=int)
    run = request.form.get("run", type=int)
    day = request.form.get("day")

    if index_a is not None and index_b is not None:
        load_picks()
        swap_picks(index_a, index_b)

    return redirect(
        url_for(
            "index",
            run=run or 1,
            day=day or date.today().isoformat(),
        )
    )


if __name__ == "__main__":
    app.run(debug=True)

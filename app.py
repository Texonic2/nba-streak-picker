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

# Grobe Stärke-Skala (0–100) pro Team – für Smart Picks.
TEAM_STRENGTH = {
    "Boston Celtics": 96,
    "Denver Nuggets": 93,
    "Oklahoma City Thunder": 92,
    "Minnesota Timberwolves": 91,
    "Milwaukee Bucks": 90,
    "New York Knicks": 89,
    "Los Angeles Clippers": 88,
    "Dallas Mavericks": 88,
    "Phoenix Suns": 87,
    "Cleveland Cavaliers": 87,
    "Philadelphia 76ers": 86,
    "Indiana Pacers": 85,
    "New Orleans Pelicans": 84,
    "Sacramento Kings": 84,
    "Los Angeles Lakers": 83,
    "Miami Heat": 82,
    "Orlando Magic": 82,
    "Golden State Warriors": 81,
    "Houston Rockets": 80,
    "Toronto Raptors": 79,
    "Atlanta Hawks": 78,
    "Chicago Bulls": 77,
    "Memphis Grizzlies": 76,
    "Brooklyn Nets": 76,
    "San Antonio Spurs": 75,
    "Utah Jazz": 75,
    "Portland Trail Blazers": 74,
    "Charlotte Hornets": 73,
    "Detroit Pistons": 72,
    "Washington Wizards": 72,
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


def build_smart_picks(games, used_teams, current_run, current_day_str):
    """
    Smart-Pick-Engine:
    - berücksichtigt nur Teams, die in diesem Lauf noch nicht benutzt sind
    - bevorzugt Heimteams
    - bevorzugt Teams, die stärker als der Gegner eingeschätzt werden
    - gibt sortierte Liste von Vorschlägen zurück (beste zuerst)
    """
    suggestions = []

    # Wenn für den Tag schon ein Pick existiert, keine Vorschläge
    if has_pick_on_date(current_day_str, current_run):
        return []

    for g in games:
        visitor = g["visitor"]
        home = g["home"]

        for side, team in (("visitor", visitor), ("home", home)):
            if team in used_teams:
                # Schon benutzt in diesem Lauf → nicht verfügbar
                continue

            opponent = home if side == "visitor" else visitor
            is_home = (side == "home")

            team_strength = TEAM_STRENGTH.get(team, 80)
            opp_strength = TEAM_STRENGTH.get(opponent, 80)

            score = team_strength  # Basis: Stärke
            reasons = [f"Team-Stärke {team_strength} vs. {opp_strength}"]

            # Heimvorteil
            if is_home:
                score += 5
                reasons.append("Heimspiel")

            diff = team_strength - opp_strength
            if diff >= 8:
                score += 4
                reasons.append("klar stärker als der Gegner")
            elif diff >= 3:
                score += 2
                reasons.append("leicht stärker als der Gegner")
            elif diff <= -5:
                reasons.append("eigentlich Underdog")

            suggestions.append(
                {
                    "team": team,
                    "opponent": opponent,
                    "home": is_home,
                    "score": score,
                    "reasons": reasons,
                    "logo": TEAM_LOGOS.get(team),
                }
            )

    # Nach Score sortieren, beste zuerst
    suggestions.sort(key=lambda s: s["score"], reverse=True)

    # Top 3 reichen
    return suggestions[:3]


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

    game_cards = []
    if games:
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

    # Picks laden (für Statistik, Kalender, Smart Picks)
    picks_for_run = get_picks_for_run(current_run)

    # verwendete Teams im aktuellen Lauf
    used_teams = sorted({p["team"] for p in picks_for_run})
    used_set = set(used_teams)

    # Smart-Pick-Vorschläge
    smart_picks = build_smart_picks(games or [], used_set, current_run, current_day_str)

    # Tages-Navigation (+/- 1 Tag)
    prev_day = current_day - timedelta(days=1)
    next_day = current_day + timedelta(days=1)
    prev_day_str = prev_day.isoformat()
    next_day_str = next_day.isoformat()

    # === Kalender & B2B ===
    pick_dates = set()
    for p in picks_for_run:
        try:
            d = date.fromisoformat(p["date"])
            pick_dates.add(d)
        except ValueError:
            continue

    b2b_dates = set()
    for d in pick_dates:
        if d - timedelta(days=1) in pick_dates:
            b2b_dates.add(d)

    cal = calendar.Calendar(firstweekday=0)
    month_weeks = []
    for week in cal.monthdatescalendar(current_day.year, current_day.month):
        week_cells = []
        for d in week:
            in_month = d.month == current_day.month
            if not in_month:
                css_class = "day-other"
            else:
                if d in b2b_dates:
                    css_class = "day-b2b"
                elif d in pick_dates:
                    css_class = "day-picked"
                elif d >= today:
                    css_class = "day-future"
                else:
                    css_class = "day-empty"

            week_cells.append(
                {
                    "date": d.isoformat(),
                    "day": d.day,
                    "in_month": in_month,
                    "css_class": css_class,
                }
            )
        month_weeks.append(week_cells)

    month_label = current_day.strftime("%B %Y")

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

    # === Streak-Statistik ===
    total_picks = len(picks_for_run)
    total_teams = len(TEAM_LOGOS)

    stats = {
        "total_picks": total_picks,
        "used_teams_count": len(used_teams),
        "total_teams": total_teams,
    }

    # Status aller Teams
    team_status = []
    all_teams_sorted = sorted(TEAM_LOGOS.keys())
    for t in all_teams_sorted:
        team_status.append(
            {
                "name": t,
                "logo": TEAM_LOGOS.get(t),
                "used": t in used_set,
            }
        )

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
        next_month_day=next_month_day.isoformat(),
        stats=stats,
        team_status=team_status,
        smart_picks=smart_picks,
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

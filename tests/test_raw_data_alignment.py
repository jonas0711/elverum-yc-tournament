import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def connect(db_name: str) -> sqlite3.Connection:
    path = ROOT / "data" / "build" / db_name
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def minutes_since_midnight(time_str: str) -> int:
    hours, minutes = map(int, time_str.split(":"))
    return hours * 60 + minutes


def test_bus_route_headways_match_reference():
    """Ensure headways per route align with the published PDF schedule."""
    expected_minutes = {1: 50, 2: 30, 3: 40}
    with connect("bus_routes.db") as conn:
        for route_id, headway in expected_minutes.items():
            first_stop_times = conn.execute(
                """
                SELECT service_day, departure_time
                FROM route_stop_times
                WHERE route_id = ? AND stop_order = 1
                ORDER BY service_day, departure_time
                """,
                (route_id,),
            ).fetchall()
            assert first_stop_times, f"route {route_id} missing first-stop times"
            by_day = {}
            for row in first_stop_times:
                by_day.setdefault(row["service_day"], []).append(row["departure_time"])
            for service_day, times in by_day.items():
                intervals = [
                    minutes_since_midnight(b) - minutes_since_midnight(a)
                    for a, b in zip(times, times[1:])
                ]
                if not intervals:
                    continue
                # All intervals should match the PDF cadence for that route.
                assert all(i == headway for i in intervals), (
                    f"route {route_id} {service_day} intervals {intervals} "
                    f"do not all equal {headway}"
                )


def test_bus_route_thon_central_only_serviced_on_saturday():
    """Verify Thon Central departures only exist on Saturday as in the PDF."""
    with connect("bus_routes.db") as conn:
        stop_id = conn.execute(
            "SELECT stop_id FROM stops WHERE stop_name = 'Thon Central (lørdag)'"
        ).fetchone()["stop_id"]
        rows = conn.execute(
            """
            SELECT DISTINCT route_id, service_day
            FROM route_stop_times
            WHERE stop_id = ?
            """,
            (stop_id,),
        ).fetchall()
        assert {row["service_day"] for row in rows} == {"sat"}


def test_lodging_roros_teams_match_overview():
    """Røros squads should mirror the overnatningsoversigt excerpt."""
    with connect("lodging.db") as conn:
        club_id = conn.execute(
            "SELECT club_id FROM clubs WHERE name = 'Røros'"
        ).fetchone()["club_id"]
        squads = conn.execute(
            """
            SELECT raw_label, headcount, room_text
            FROM teams
            WHERE club_id = ?
            ORDER BY raw_label
            """,
            (club_id,),
        ).fetchall()
        expected = {
            "G2014,2 lag": ("A002", 18),
            "J2011": ("A004", 14),
            "J2013": ("A101", 21),
            "J2015": ("A103", 20),
            "G2015": ("A104", 11),
        }
        assert len(squads) == len(expected)
        for squad in squads:
            room, headcount = expected[squad["raw_label"]]
            assert squad["room_text"] == room
            assert squad["headcount"] == headcount


def test_lodging_school_one_total_headcount():
    """ELVERUM UNGDOMSSKOLE sum matches 414 as in the Word document."""
    with connect("lodging.db") as conn:
        total = conn.execute(
            """
            SELECT SUM(headcount)
            FROM teams
            WHERE club_id IN (
                SELECT club_id FROM clubs WHERE school_id = (
                    SELECT school_id FROM schools WHERE name = 'ELVERUM UNGDOMSSKOLE'
                )
            )
            """
        ).fetchone()[0]
        assert total == 414


def test_tournament_first_elverumshallen_block():
    """First match block at Elverumshallen Friday matches the Excel capture."""
    with connect("tournament.db") as conn:
        rows = conn.execute(
            """
            SELECT g.start_time, t.name AS tournament_name,
                   home.name AS home_team, away.name AS away_team
            FROM games g
            JOIN tournaments t ON g.tournament_id = t.tournament_id
            JOIN halls h ON g.hall_id = h.hall_id
            JOIN teams home ON home.team_id = g.home_team_id
            JOIN teams away ON away.team_id = g.away_team_id
            JOIN event_days d ON d.day_id = g.day_id
            WHERE h.name = 'Elverumshallen'
              AND d.date = '2025-04-25'
            ORDER BY g.start_time
            LIMIT 5
            """
        ).fetchall()
        expected = [
            ("18:00", "Elverum Yngres Cup - Jenter 12 år - 02", "Elverum", "Lensbygda"),
            ("18:19", "Elverum Yngres Cup - Jenter 12 år - 02", "Gjøvik HK 2", "Storhamar 2"),
            ("18:38", "Elverum Yngres Cup - Jenter 12 år - 01", "Koppang Håndballklubb 2", "Ring IL"),
            ("18:57", "Elverum Yngres Cup - Jenter 12 år - 01", "Gjøvik HK", "Varde 2"),
            ("19:16", "Elverum Yngres Cup - Jenter 12 år - 03", "Ottestad", "Storhamar"),
        ]
        assert [(row["start_time"], row["tournament_name"], row["home_team"], row["away_team"]) for row in rows] == expected

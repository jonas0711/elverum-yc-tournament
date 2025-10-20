#!/usr/bin/env python3
"""
Ad-hoc integrity checks for the consolidated event planner database.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "build" / "event_planner.db"


def fetch_one(conn: sqlite3.Connection, query: str):
    cur = conn.execute(query)
    return cur.fetchone()


def fetch_all(conn: sqlite3.Connection, query: str):
    cur = conn.execute(query)
    return cur.fetchall()


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing database: {DB_PATH}. Run build_event_db.py first.")
    conn = sqlite3.connect(DB_PATH)

    print("=== Tournament schedule ===")
    total_games = fetch_one(conn, "SELECT COUNT(*) FROM schedule_games")[0]
    print(f"Total games: {total_games}")

    distinct_days = fetch_all(
        conn, "SELECT date, label FROM schedule_event_days ORDER BY date"
    )
    print("Event days:")
    for date, label in distinct_days:
        print(f"  {date} ({label})")

    print("\n=== Lodging ===")
    orphan_teams = fetch_one(
        conn,
        """
        SELECT COUNT(*) FROM lodging_teams
        WHERE team_id NOT IN (SELECT team_id FROM lodging_team_rooms)
        """,
    )[0]
    print(f"Lodging teams without room assignment: {orphan_teams}")

    division_counts = fetch_all(
        conn,
        """
        SELECT division_key, COUNT(*)
        FROM lodging_teams
        WHERE division_key IS NOT NULL
        GROUP BY division_key
        ORDER BY division_key
        """,
    )
    print("Division keys loaded:")
    for division_key, count in division_counts:
        print(f"  {division_key}: {count} teams")

    multi_team_examples = fetch_all(
        conn,
        """
        SELECT lc.name, lt.raw_label, lt.num_teams
        FROM lodging_teams lt
        JOIN lodging_clubs lc ON lt.club_id = lc.club_id
        WHERE lt.num_teams > 1
        ORDER BY lc.name, lt.raw_label
        LIMIT 5
        """,
    )
    if multi_team_examples:
        print("Examples of clubs with multiple squads in one age group:")
        for club, label, num in multi_team_examples:
            print(f"  {club}: {label} ({num} squads)")

    squad_total = fetch_one(conn, "SELECT COUNT(*) FROM lodging_team_squads")[0]
    print(f"Total lodging team squads tracked: {squad_total}")

    print("\n=== Transport ===")
    route_days = fetch_all(
        conn,
        """
        SELECT route_id, service_day, COUNT(*) AS departures
        FROM transport_route_stop_times
        GROUP BY route_id, service_day
        ORDER BY route_id, service_day
        """,
    )
    for route_id, service_day, count in route_days:
        print(f"Route {route_id} - {service_day}: {count} departures")

    latest_sat = fetch_one(
        conn,
        """
        SELECT MAX(departure_time)
        FROM transport_route_stop_times
        WHERE route_id = 2 AND service_day = 'sat'
        """,
    )[0]
    print(f"Route 2 latest Saturday departure: {latest_sat}")

    print("\n=== Stop linkage summary ===")
    links = fetch_all(
        conn,
        """
        SELECT ts.stop_name, tsl.lodging_school_id, tsl.schedule_hall_id
        FROM transport_stop_links tsl
        JOIN transport_stops ts USING(stop_id)
        ORDER BY ts.stop_id
        """
    )
    for name, school_id, hall_id in links:
        print(f"{name}: school={school_id}, hall={hall_id}")

    print("\n=== Team alias coverage ===")
    alias_counts = fetch_all(
        conn,
        """
        SELECT
            SUM(CASE WHEN schedule_team_id IS NOT NULL THEN 1 ELSE 0 END) AS matched,
            SUM(CASE WHEN schedule_team_id IS NULL THEN 1 ELSE 0 END) AS unmatched
        FROM team_aliases
        """,
    )
    matched_aliases, unmatched_aliases = alias_counts[0]
    total_aliases = (matched_aliases or 0) + (unmatched_aliases or 0)
    print(f"Aliases matched: {matched_aliases or 0}")
    print(f"Aliases unmatched: {unmatched_aliases or 0}")
    print(f"Total aliases tracked: {total_aliases}")

    unresolved = fetch_all(
        conn,
        """
        SELECT lt.team_id, lc.name, lt.raw_label, ta.note
        FROM team_aliases ta
        JOIN lodging_teams lt ON ta.lodging_team_id = lt.team_id
        JOIN lodging_clubs lc ON lt.club_id = lc.club_id
        WHERE ta.schedule_team_id IS NULL
        ORDER BY lc.name, lt.raw_label
        LIMIT 5
        """,
    )
    if unresolved:
        print("Sample unresolved mappings:")
        for team_id, club_name, raw_label, note in unresolved:
            print(f"  {club_name} - {raw_label}: {note}")

    conn.close()


if __name__ == "__main__":
    main()

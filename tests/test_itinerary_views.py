#!/usr/bin/env python3
"""Checks for itinerary-supporting views."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path("data/build/event_planner.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def test_team_itinerary_segments_populated():
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM team_itinerary_segments").fetchone()[0]
        assert count > 0, "Itinerary staging table should contain generated segments"


def test_game_sequence_differences():
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT game_sequence, minutes_since_prev_game
            FROM vw_team_game_sequence
            WHERE minutes_since_prev_game IS NOT NULL
            ORDER BY date, start_time
            LIMIT 1
            """
        ).fetchone()
        assert row is not None, "Expected at least one sequence with previous game gap"
        assert row["game_sequence"] > 1, "Sequence index should increment past first game"
        assert row["minutes_since_prev_game"] >= 0, "Gap between games must be non-negative"


def test_daily_summary_matches_games():
    with get_connection() as conn:
        daily = conn.execute(
            """
            SELECT alias_id, date, games_count
            FROM vw_team_daily_summary
            LIMIT 5
            """
        ).fetchall()
        assert daily, "Expected rows in daily summary view"
        for row in daily:
            raw_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM vw_team_games
                WHERE alias_id = ? AND date = ?
                """,
                (row["alias_id"], row["date"]),
            ).fetchone()[0]
            assert raw_count == row["games_count"]


def test_logistics_events_view():
    with get_connection() as conn:
        events = conn.execute(
            """
            SELECT event_type, stop_name
            FROM vw_logistics_events
            ORDER BY event_type
            """
        ).fetchall()
        assert events, "Expected seeded logistics events"
        types = {row["event_type"]: row["stop_name"] for row in events}
        assert "lunch" in types and "Thon Central" in types["lunch"]
        assert "concert" in types and "Terningen" in types["concert"]


def test_bus_load_summary_present():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT route_id, trip_index, estimated_headcount
            FROM vw_bus_load_summary
            ORDER BY service_day, route_id, departure_time
            LIMIT 5
            """
        ).fetchall()
        assert rows, "Expected bus load summary rows after itinerary generation"
        for row in rows:
            assert row["estimated_headcount"] >= 0


def test_bus_capacity_alerts_threshold():
    with get_connection() as conn:
        alerts = conn.execute(
            "SELECT MAX(estimated_headcount) FROM vw_bus_capacity_alerts"
        ).fetchone()[0]
        summary_max = conn.execute(
            "SELECT MAX(estimated_headcount) FROM vw_bus_load_summary"
        ).fetchone()[0]
        if alerts is not None:
            assert alerts <= summary_max


def test_concert_segments_exist():
    with get_connection() as conn:
        count = conn.execute(
            """
            SELECT COUNT(*)
            FROM team_itinerary_segments
            WHERE segment_type = 'concert'
            """
        ).fetchone()[0]
        assert count > 0, "Concert segments should be generated for squads"


def test_no_placeholder_segments():
    with get_connection() as conn:
        count = conn.execute(
            """
            SELECT COUNT(*)
            FROM team_itinerary_segments
            WHERE segment_type = 'placeholder'
            """
        ).fetchone()[0]
        assert count == 0, "Placeholder segments should be eliminated"


def test_manual_transport_view_matches_notes():
    with get_connection() as conn:
        view_count = conn.execute("SELECT COUNT(*) FROM vw_manual_transport_needs").fetchone()[0]
        raw_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM team_itinerary_segments
            WHERE segment_type = 'note' OR (segment_type = 'bus' AND route_id IS NULL)
            """
        ).fetchone()[0]
        assert view_count == raw_count


if __name__ == "__main__":
    test_team_itinerary_segments_populated()
    test_game_sequence_differences()
    test_daily_summary_matches_games()
    test_logistics_events_view()
    test_bus_load_summary_present()
    test_concert_segments_exist()
    test_no_placeholder_segments()
    test_manual_transport_view_matches_notes()

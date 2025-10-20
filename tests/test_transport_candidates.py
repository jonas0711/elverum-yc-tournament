#!/usr/bin/env python3
"""Sanity checks for transport candidate preparation."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path("data/build/event_planner.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def test_transport_candidate_buffer():
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT buffer_minutes, travel_minutes, departure_stop_name, arrival_stop_name
            FROM vw_game_transport_candidates
            WHERE lodging_club = 'Aurskog Finstadbru'
            ORDER BY date, start_time
            LIMIT 1
            """
        ).fetchone()
        assert row is not None, "Expected at least one bus candidate for Aurskog Finstadbru"
        assert row["buffer_minutes"] >= 40, "Buffer should satisfy 40 minute rule"
        assert row["travel_minutes"] >= 0, "Travel time must be non-negative"
        assert row["departure_stop_name"], "Departure stop should be named"
        assert row["arrival_stop_name"], "Arrival stop should be named"


def test_logistics_events_seeded():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT event_type, start_time, end_time, service_day
            FROM logistics_events
            ORDER BY event_type
            """
        ).fetchall()
        assert rows, "Expected seeded logistics events"
        types = {row["event_type"]: row for row in rows}
        lunch = types.get("lunch")
        concert = types.get("concert")
        assert lunch is not None, "Lunch event missing"
        assert lunch["service_day"] == "sat" and lunch["start_time"] == "13:00" and lunch["end_time"] == "17:30"
        assert concert is not None, "Concert event missing"
        assert concert["service_day"] == "sat" and concert["start_time"] == "19:30" and concert["end_time"] == "21:00"


if __name__ == "__main__":
    test_transport_candidate_buffer()
    test_logistics_events_seeded()

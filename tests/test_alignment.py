#!/usr/bin/env python3
"""Cross-domain checks linking lodging squads to tournament schedule."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path("data/build/event_planner.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def test_alignment_rooms_and_schedule_team():
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT schedule_team_name, room_codes
            FROM vw_team_alignment
            WHERE lodging_club = 'Røros' AND raw_label = 'J2011'
            """
        ).fetchone()
        assert row is not None
        assert row["schedule_team_name"] == "Røros"
        assert row["room_codes"] == "A004"


def test_alignment_example_game():
    with get_connection() as conn:
        schedule_team_id = conn.execute(
            """
            SELECT schedule_team_id
            FROM vw_team_alignment
            WHERE lodging_club = 'Gjøvik HK' AND raw_label = 'J2013'
            """
        ).fetchone()[0]
        rows = conn.execute(
            """
            SELECT day_label, start_time, opponent_name
            FROM vw_team_games
            WHERE schedule_team_id = ?
            ORDER BY date, start_time
            LIMIT 1
            """,
            (schedule_team_id,),
        ).fetchall()
        assert rows, "Expected at least one scheduled game for Gjøvik HK J2013"
        sample = rows[0]
        assert sample["day_label"].startswith("Fredag") or sample["day_label"].startswith("Lørdag")
        assert sample["opponent_name"], "Opponent name should be present"


if __name__ == "__main__":
    test_alignment_rooms_and_schedule_team()
    test_alignment_example_game()

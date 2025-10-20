#!/usr/bin/env python3
"""Validate tournament schedule entries against reference screenshots."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path("data/build/tournament.db")


def fetch_game(day_id: int, time: str, hall: str, tournament: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT t.name AS tournament,
                   h.name AS hall,
                   home.name AS home_team,
                   away.name AS away_team
            FROM games g
            JOIN tournaments t ON g.tournament_id = t.tournament_id
            JOIN halls h ON g.hall_id = h.hall_id
            JOIN teams home ON g.home_team_id = home.team_id
            JOIN teams away ON g.away_team_id = away.team_id
            WHERE g.day_id = ? AND g.start_time = ? AND h.name = ? AND t.name = ?
            """,
            (day_id, time, hall, tournament),
        ).fetchall()
    if not rows:
        raise AssertionError(
            f"No game found for day={day_id}, time={time}, hall={hall}, tournament={tournament}"
        )
    return rows


def assert_game(day_id: int, time: str, hall: str, tournament: str, home: str, away: str):
    rows = fetch_game(day_id, time, hall, tournament)
    assert any(row["home_team"] == home and row["away_team"] == away for row in rows), (
        f"Expected {home} vs {away} at {hall} {time} in {tournament}, "
        f"but found {[ (row['home_team'], row['away_team']) for row in rows ]}"
    )


def run_checks():
    # Screenshot 190008: Friday opening matches
    assert_game(
        day_id=1,
        time="18:00",
        hall="Elverumshallen",
        tournament="Elverum Yngres Cup - Jenter 12 år - 02",
        home="Elverum",
        away="Lensbygda",
    )
    assert_game(
        day_id=1,
        time="18:19",
        hall="Elverumshallen",
        tournament="Elverum Yngres Cup - Jenter 12 år - 02",
        home="Gjøvik HK 2",
        away="Storhamar 2",
    )

    # Screenshot 190032: Saturday 08:57 block
    assert_game(
        day_id=2,
        time="08:57",
        hall="Elverumshallen - Kortbane",
        tournament="Elverum Yngres Cup - Jenter 10 år - 02",
        home="Flisa 2",
        away="Lisleby Blå",
    )
    assert_game(
        day_id=2,
        time="08:57",
        hall="Elverumshallen - Mini 1",
        tournament="Elverum Yngres Cup - Jenter 8 år - 01",
        home="Elverum 2",
        away="Gjøvik HK",
    )

    # Screenshot 190043: Saturday afternoon 15:36 / 15:55 etc.
    assert_game(
        day_id=2,
        time="15:55",
        hall="Elverumshallen - Kortbane",
        tournament="Elverum Yngres Cup - Gutter 10 år - 02",
        home="Hasle-Løren Gul",
        away="Furnes 2",
    )


if __name__ == "__main__":
    run_checks()

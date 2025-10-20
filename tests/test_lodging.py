#!/usr/bin/env python3
"""Validate lodging data against reference overnatningsoversigt screenshots."""

from __future__ import annotations

import sqlite3
from pathlib import Path

LODGE_DB = Path("data/build/lodging.db")


def fetch_team(club: str, label: str) -> tuple[int, str, int, list[str]]:
    with sqlite3.connect(LODGE_DB) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT t.team_id, t.raw_label, t.headcount
            FROM teams t
            JOIN clubs c ON t.club_id = c.club_id
            WHERE c.name = ? AND t.raw_label = ?
            """,
            (club, label),
        ).fetchone()
        if row is None:
            raise AssertionError(f"Team {club} / {label} not found")
        rooms = [r[0] for r in conn.execute(
            """
            SELECT room_code
            FROM team_rooms tr
            JOIN rooms r ON tr.room_id = r.room_id
            WHERE tr.team_id = ?
            ORDER BY room_code
            """,
            (row["team_id"],),
        ).fetchall()]
        return row["team_id"], row["raw_label"], row["headcount"], rooms


def assert_team(club: str, label: str, expected_headcount: int, expected_rooms: list[str]):
    team_id, stored_label, headcount, rooms = fetch_team(club, label)
    assert stored_label == label
    assert headcount == expected_headcount, f"{club} {label}: expected {expected_headcount}, got {headcount}"
    assert rooms == expected_rooms, f"{club} {label}: expected rooms {expected_rooms}, got {rooms}"


def run_checks():
    # Elverum ungdomsskole
    assert_team("Røros", "G2014,2 lag", 18, ["A002"])
    assert_team("Røros", "J2011", 14, ["A004"])
    assert_team("Hasle/Løren", "J2014", 21, ["B201"])
    assert_team("Storhamar", "J2012,2 lag", 22, ["B301"])
    assert_team("Ring IL", "J2012+J2011", 15, ["B304"])
    assert_team("Skarnes", "J2015,2 lag", 23, ["B309"])

    # Frydenlund skole
    assert_team("Borgen IL", "J2011", 12, ["D123"])
    assert_team("Tydal", "J2013,2 lag", 17, ["D124"])
    assert_team("Drøbak/Frogn", "G2013", 18, ["C123"])
    assert_team("Gjøvik HK", "J2013", 31, ["B120", "B121"])

    # Ydalir skole
    assert_team("Lensbygda", "J2012", 11, ["2.062"])
    assert_team("Ottestad", "G2012,2 lag", 17, ["2.060"])
    assert_team("Jardar IL", "J2008", 17, ["1.065"])
    assert_team("Trysil", "J2011", 10, ["2.049"])
    assert_team("Kolbu IL", "G2012", 17, ["2.039"])

    # ELVIS
    assert_team("Årdalstangen", "J2011", 20, ["B120"])
    assert_team("Jotun", "J2012 ,2 lag", 18, ["B137"])
    assert_team("Heradsbygda HK", "J2012,3 lag", 27, ["C226", "C227"])
    assert_team("HK Vestre Toten", "J2014,2 lag", 11, ["C111"])
    assert_team("Utleira", "J2011,2 lag", 21, ["E162"])
    assert_team("Sverresborg", "J2013,2 lag", 16, ["C127"])
    assert_team("Sverresborg", "G2014", 16, ["C119"])

    print("All lodging checks passed.")


if __name__ == "__main__":
    run_checks()

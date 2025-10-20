#!/usr/bin/env python3
"""
Sanity checks for the parsed bus schedules based on the reference route tables.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path("data/build/bus_routes.db")


def fetch_times(route_number: int, stop_name: str, service_day: str = "sat", stop_order: int | None = None) -> list[str]:
    query = """
        SELECT stop_order, departure_time
        FROM route_stop_times rst
        JOIN routes r USING(route_id)
        JOIN stops s USING(stop_id)
        WHERE r.route_number = ?
          AND s.stop_name = ?
          AND rst.service_day = ?
    """
    params = [route_number, stop_name, service_day]
    if stop_order is not None:
        query += " AND rst.stop_order = ?"
        params.append(stop_order)
    query += " ORDER BY rst.stop_order, rst.departure_time"

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(query, params).fetchall()
    return [row[1] for row in rows]


def test_route1_ydalir_primary():
    expected = ["07:00", "07:50", "08:40", "09:30", "10:20", "11:10", "12:00", "12:50", "13:40", "14:30", "15:20", "16:10", "17:00", "17:50", "18:40"]
    assert fetch_times(1, "Ydalir", stop_order=1) == expected


def test_route1_ydalir_return_loop():
    expected = [
        "08:20", "09:10", "10:00", "10:50", "11:40",
        "12:30", "13:20", "14:10", "15:00", "15:50",
        "16:40", "17:30", "18:20", "19:10", "20:00",
    ]
    assert fetch_times(1, "Ydalir", stop_order=12) == expected


def test_route1_thon_central():
    expected = ["13:25", "14:15", "15:05", "15:55", "16:45", "17:35", "13:05", "13:55", "14:45", "15:35", "16:25", "17:15", "18:05"]
    assert fetch_times(1, "Thon Central (lørdag)") == expected


def test_route2_eus_half_hour():
    expected = [
        "07:00", "07:30", "08:00", "08:30", "09:00", "09:30",
        "10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
        "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
        "16:00", "16:30", "17:00", "17:30", "18:00", "18:30", "19:00",
    ]
    assert fetch_times(2, "Elverum ungdomsskole (EUS)") == expected


def test_route2_terningen_arena_offsets():
    expected = [
        "07:25", "07:55", "08:25", "08:55", "09:25", "09:55",
        "10:25", "10:55", "11:25", "11:55", "12:25", "12:55",
        "13:25", "13:55", "14:25", "14:55", "15:25", "15:55",
        "16:25", "16:55", "17:25", "17:55", "18:25", "18:55", "19:25",
    ]
    assert fetch_times(2, "Terningen Arena") == expected


def test_route3_eus_full_span():
    expected = [
        "07:35", "08:15", "08:55", "09:35", "10:15", "10:55",
        "11:35", "12:15", "12:55", "13:35", "14:15", "14:55",
        "15:35", "16:15", "16:55", "17:35", "18:15", "18:55",
    ]
    assert fetch_times(3, "Elverum ungdomsskole (EUS)") == expected


def test_route3_thon_central_loop():
    expected = [
        "13:05", "13:45", "14:25", "15:05", "15:45", "16:25",
        "17:05", "17:45",
    ]
    assert fetch_times(3, "Thon Central (lørdag)") == expected


def run_all():
    test_route1_ydalir_primary()
    test_route1_ydalir_return_loop()
    test_route1_thon_central()
    test_route2_eus_half_hour()
    test_route2_terningen_arena_offsets()
    test_route3_eus_full_span()
    test_route3_thon_central_loop()
    print("All bus schedule checks passed.")


if __name__ == "__main__":
    run_all()

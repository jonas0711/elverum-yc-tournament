#!/usr/bin/env python3
"""Export a single squad itinerary as JSON (baseline for PDF generation)."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "build" / "event_planner.db"

SERVICE_DAY_ORDER = {"fri": 0, "sat": 1, "sun": 2}


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing database: {DB_PATH}. Run build_event_db.py first.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_alias_id(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    if args.alias_id is not None:
        return args.alias_id
    if args.team_name:
        row = conn.execute(
            """
            SELECT DISTINCT alias_id
            FROM vw_team_alignment
            WHERE schedule_team_name = ?
            ORDER BY alias_id
            """,
            (args.team_name,),
        ).fetchone()
        if row:
            return row["alias_id"]
        raise ValueError(f"No alias found for schedule_team_name='{args.team_name}'")
    raise ValueError("Provide either --alias-id or --team-name")


def fetch_itinerary(conn: sqlite3.Connection, alias_id: int) -> Dict:
    header = conn.execute(
        """
        SELECT DISTINCT
            alias_id,
            lodging_club,
            raw_label,
            schedule_team_name,
            school_name,
            headcount,
            room_codes
        FROM vw_team_alignment
        WHERE alias_id = ?
        """,
        (alias_id,),
    ).fetchone()
    if header is None:
        raise ValueError(f"Alias {alias_id} not found in vw_team_alignment")

    rows = conn.execute(
        """
        SELECT
            alias_id,
            sequence_no,
            segment_type,
            service_day,
            event_date,
            start_time,
            end_time,
            origin_stop_name,
            origin_stop_display,
            destination_stop_name,
            destination_stop_display,
            route_id,
            route_number,
            trip_index,
            travel_minutes,
            buffer_minutes,
            notes
        FROM vw_team_itinerary_flat
        WHERE alias_id = ?
        ORDER BY
            CASE service_day WHEN 'fri' THEN 0 WHEN 'sat' THEN 1 WHEN 'sun' THEN 2 ELSE 3 END,
            sequence_no
        """,
        (alias_id,),
    ).fetchall()

    days: Dict[str, List[Dict]] = {}
    for row in rows:
        day_key = row["event_date"] or f"service:{row['service_day']}"
        days.setdefault(day_key, []).append(
            {
                "sequence_no": row["sequence_no"],
                "segment_type": row["segment_type"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "origin_stop": row["origin_stop_display"] or row["origin_stop_name"],
                "destination_stop": row["destination_stop_display"] or row["destination_stop_name"],
                "route_number": row["route_number"],
                "trip_index": row["trip_index"],
                "travel_minutes": row["travel_minutes"],
                "buffer_minutes": row["buffer_minutes"],
                "notes": row["notes"],
            }
        )

    manual_segments = conn.execute(
        """
        SELECT service_day, event_date, start_time, end_time, notes
        FROM vw_manual_transport_needs
        WHERE alias_id = ?
        ORDER BY
            CASE service_day WHEN 'fri' THEN 0 WHEN 'sat' THEN 1 WHEN 'sun' THEN 2 ELSE 3 END,
            start_time
        """,
        (alias_id,),
    ).fetchall()

    return {
        "alias_id": header["alias_id"],
        "lodging_club": header["lodging_club"],
        "lodging_label": header["raw_label"],
        "schedule_team_name": header["schedule_team_name"],
        "school_name": header["school_name"],
        "headcount": header["headcount"],
        "room_codes": header["room_codes"],
        "days": [
            {"event_date": key, "segments": segments}
            for key, segments in sorted(
                days.items(),
                key=lambda kv: (SERVICE_DAY_ORDER.get(kv[0][:3], 99), kv[0]),
            )
        ],
        "manual_transport": [dict(row) for row in manual_segments],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export itinerary for a single alias as JSON.")
    parser.add_argument("--alias-id", type=int, help="Alias ID from vw_team_alignment")
    parser.add_argument("--team-name", help="Schedule team name (vw_team_alignment.schedule_team_name)")
    args = parser.parse_args()

    with get_connection() as conn:
        alias_id = fetch_alias_id(conn, args)
        itinerary = fetch_itinerary(conn, alias_id)
        print(json.dumps(itinerary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

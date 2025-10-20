#!/usr/bin/env python3
"""
Generate itinerary segments for every lodging squad with bus allocations,
lunch and concert logistics, and return trips to the lodging schools.

Heuristics:
- Guarantee ≥40 minutters buffer før kampstart ved at vælge passende busafgange.
- Tildel lørdags-lunch (Thon Central) og transport videre til både næste kamp
  og den fælles koncert i Terningen Arena.
- Indfør et kapacitetstjek (default 120 personer pr. tur); hvis alle alternativer
  er fulde, registreres et “capacity override” i segmentnoten.
- Efter hver dags sidste aktivitet tilføjes returrejse til overnatningsskolen.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "build" / "event_planner.db"

MINUTES_PER_DAY = 24 * 60
LUNCH_DURATION = 45
LUNCH_WINDOW_MIN = 13 * 60  # 13:00
LUNCH_WINDOW_MAX = 17 * 60 + 30  # 17:30
CONCERT_BUFFER_MIN = 20  # ≥20 minutter før koncertstart
CONCERT_SOFT_EARLIEST = 17 * 60
BUS_CAPACITY_LIMIT = 120

HALL_NAME_ALIASES = {
    "Herneshallen - Kortbane": "Herneshallen",
    "Herneshallen - mini 1": "Herneshallen",
    "Herneshallen - mini 2": "Herneshallen",
    "Elverumshallen - Kortbane": "Elverumshallen",
    "Søndre Elverum Idrettshall - Kortbane": "Søndre Elverum Idrettshall",
    "Ydalir skole idrettshall - Kortbane": "Ydalir skole idrettshall",
    "Elverumshallen - Mini 1": "Elverumshallen",
    "Elverumshallen - Mini 2": "Elverumshallen",
}


def time_to_minutes(value: str) -> int:
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


def minutes_to_time(minutes: int) -> str:
    minutes = minutes % MINUTES_PER_DAY
    hours, minute = divmod(minutes, 60)
    return f"{hours:02d}:{minute:02d}"


class BusLoadTracker:
    """Track headcount per (service_day, route_id, trip_index)."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self._loads: Dict[Tuple[str, int, int], int] = defaultdict(int)

    def current(self, service_day: str, route_id: int, trip_index: int) -> int:
        return self._loads.get((service_day, route_id, trip_index), 0)

    def can_assign(self, service_day: str, route_id: Optional[int], trip_index: Optional[int], headcount: int) -> bool:
        if route_id is None or trip_index is None:
            return True
        return self.current(service_day, route_id, trip_index) + headcount <= self.limit

    def assign(
        self,
        service_day: str,
        route_id: Optional[int],
        trip_index: Optional[int],
        headcount: int,
        *,
        force: bool = False,
    ) -> bool:
        if route_id is None or trip_index is None:
            return True
        if not force and not self.can_assign(service_day, route_id, trip_index, headcount):
            return False
        key = (service_day, route_id, trip_index)
        self._loads[key] = self.current(service_day, route_id, trip_index) + headcount
        return True

    def release(self, service_day: str, route_id: Optional[int], trip_index: Optional[int], headcount: int) -> None:
        if route_id is None or trip_index is None:
            return
        key = (service_day, route_id, trip_index)
        current = self.current(service_day, route_id, trip_index)
        new_value = max(0, current - headcount)
        if new_value:
            self._loads[key] = new_value
        elif key in self._loads:
            del self._loads[key]


@dataclass
class LookupData:
    tournament_durations: Dict[int, int]
    hall_stop_map: Dict[int, int]
    school_stop_map: Dict[int, int]
    lunch_event: Optional[sqlite3.Row]
    concert_event: Optional[sqlite3.Row]


def load_lookup_data(conn: sqlite3.Connection) -> LookupData:
    tournament_durations: Dict[int, int] = {}
    for row in conn.execute("SELECT tournament_id, age FROM schedule_tournaments"):
        age = row["age"]
        if age is None:
            duration = 25
        elif age >= 13:
            duration = 25
        else:
            duration = 20
        tournament_durations[row["tournament_id"]] = duration

    hall_stop_map: Dict[int, int] = {}
    school_stop_map: Dict[int, int] = {}
    for row in conn.execute(
        """
        SELECT schedule_hall_id, lodging_school_id, stop_id
        FROM transport_stop_links
        WHERE schedule_hall_id IS NOT NULL OR lodging_school_id IS NOT NULL
        """
    ):
        if row["schedule_hall_id"] is not None and row["schedule_hall_id"] not in hall_stop_map:
            hall_stop_map[row["schedule_hall_id"]] = row["stop_id"]
        if row["lodging_school_id"] is not None and row["lodging_school_id"] not in school_stop_map:
            school_stop_map[row["lodging_school_id"]] = row["stop_id"]

    hall_names = {row["name"]: row["hall_id"] for row in conn.execute("SELECT hall_id, name FROM schedule_halls")}
    for alias_name, canonical in HALL_NAME_ALIASES.items():
        alias_id = hall_names.get(alias_name)
        canonical_id = hall_names.get(canonical)
        if alias_id is not None and canonical_id is not None and alias_id not in hall_stop_map and canonical_id in hall_stop_map:
            hall_stop_map[alias_id] = hall_stop_map[canonical_id]

    lunch_event = conn.execute(
        "SELECT * FROM vw_logistics_events WHERE event_type = 'lunch' LIMIT 1"
    ).fetchone()
    concert_event = conn.execute(
        "SELECT * FROM vw_logistics_events WHERE event_type = 'concert' LIMIT 1"
    ).fetchone()

    return LookupData(
        tournament_durations=tournament_durations,
        hall_stop_map=hall_stop_map,
        school_stop_map=school_stop_map,
        lunch_event=lunch_event,
        concert_event=concert_event,
    )


def fetch_games_for_alias(conn: sqlite3.Connection, alias_id: int) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT *
        FROM vw_team_game_sequence
        WHERE alias_id = ?
        ORDER BY date, start_time, game_id
        """,
        (alias_id,),
    ).fetchall()


def fetch_game_bus_candidates(conn: sqlite3.Connection, alias_id: int, game_id: int) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT *
        FROM vw_game_transport_candidates
        WHERE alias_id = ? AND game_id = ?
        ORDER BY buffer_minutes DESC, departure_time ASC
        """,
        (alias_id, game_id),
    ).fetchall()


def list_trips(
    conn: sqlite3.Connection,
    service_day: str,
    origin_stop_id: int,
    destination_stop_id: int,
    earliest_depart_min: int,
) -> List[sqlite3.Row]:
    earliest_depart = minutes_to_time(max(0, earliest_depart_min))
    return conn.execute(
        """
        SELECT
            dep.route_id,
            dep.trip_index,
            dep.departure_time,
            dep.route_stop_time_id AS departure_route_stop_time_id,
            dep.stop_id AS departure_stop_id,
            arr.route_stop_time_id AS arrival_route_stop_time_id,
            arr.stop_id AS arrival_stop_id,
            arr.departure_time AS arrival_time
        FROM vw_transport_trip_instances dep
        JOIN vw_transport_trip_instances arr
          ON arr.route_id = dep.route_id
         AND arr.service_day = dep.service_day
         AND arr.trip_index = dep.trip_index
        WHERE dep.service_day = ?
          AND dep.stop_id = ?
          AND arr.stop_id = ?
          AND dep.stop_order < arr.stop_order
          AND dep.departure_time >= ?
        ORDER BY dep.departure_time
        """,
        (service_day, origin_stop_id, destination_stop_id, earliest_depart),
    ).fetchall()


def candidate_transfer_stops(
    conn: sqlite3.Connection, service_day: str, destination_stop_id: int
) -> List[int]:
    rows = conn.execute(
        """
        SELECT DISTINCT dep.stop_id
        FROM vw_transport_trip_instances dep
        JOIN vw_transport_trip_instances arr
          ON arr.route_id = dep.route_id
         AND arr.service_day = dep.service_day
         AND arr.trip_index = dep.trip_index
        WHERE dep.service_day = ?
          AND arr.stop_id = ?
          AND dep.stop_order < arr.stop_order
        """,
        (service_day, destination_stop_id),
    ).fetchall()
    return [row["stop_id"] for row in rows]


def find_multi_leg_trip(
    conn: sqlite3.Connection,
    tracker: BusLoadTracker,
    service_day: str,
    origin_stop_id: int,
    destination_stop_id: int,
    earliest_depart_min: int,
    latest_arrival_min: Optional[int],
    headcount: int,
    note: str,
    ref_type: str,
    ref_id: Optional[int],
) -> Tuple[Optional[List[Dict[str, Optional[object]]]], Optional[int]]:
    transfer_candidates = set(candidate_transfer_stops(conn, service_day, destination_stop_id))
    if not transfer_candidates:
        return None, None

    trips_from_origin = conn.execute(
        """
        SELECT route_id, trip_index, stop_order, departure_time
        FROM vw_transport_trip_instances
        WHERE service_day = ? AND stop_id = ? AND departure_time >= ?
        ORDER BY departure_time
        """,
        (service_day, origin_stop_id, minutes_to_time(max(0, earliest_depart_min))),
    ).fetchall()

    transfer_buffer = 5

    for trip in trips_from_origin:
        route_id = trip["route_id"]
        trip_index = trip["trip_index"]
        origin_order = trip["stop_order"]

        stops = conn.execute(
            """
            SELECT stop_id, stop_order, departure_time, route_stop_time_id
            FROM vw_transport_trip_instances
            WHERE service_day = ? AND route_id = ? AND trip_index = ? AND stop_order > ?
            ORDER BY stop_order
            """,
            (service_day, route_id, trip_index, origin_order),
        ).fetchall()

        first_segment: Optional[Dict[str, Optional[object]]] = None
        first_arrival_min: Optional[int] = None
        first_mid_stop: Optional[int] = None

        for stop in stops:
            mid_stop = stop["stop_id"]
            arrival_min = time_to_minutes(stop["departure_time"])
            if latest_arrival_min is not None and arrival_min + transfer_buffer > latest_arrival_min:
                break
            if mid_stop not in transfer_candidates:
                continue

            first_segment, first_arrival_min, _ = select_trip_with_capacity(
                conn,
                tracker,
                service_day,
                origin_stop_id,
                mid_stop,
                earliest_depart_min,
                headcount,
                f"{note} (leg 1)",
                ref_type,
                ref_id,
                latest_arrival_min=arrival_min,
                allow_force=False,
            )
            if first_segment is None or first_arrival_min is None:
                continue

            second_segment, second_arrival_min, _ = select_trip_with_capacity(
                conn,
                tracker,
                service_day,
                mid_stop,
                destination_stop_id,
                max(first_arrival_min + transfer_buffer, earliest_depart_min),
                headcount,
                f"{note} (via transfer)",
                ref_type,
                ref_id,
                latest_arrival_min=latest_arrival_min,
                allow_force=False,
            )
            if second_segment is None or second_arrival_min is None:
                release_bus_segments(tracker, alias=None, segments=[first_segment], headcount=headcount)
                continue

            return [first_segment, second_segment], second_arrival_min

    return None, None
def build_bus_segment_from_candidate(
    candidate: sqlite3.Row,
    ref_type: str,
    ref_id: Optional[int],
    note: str,
    buffer_override: Optional[int] = None,
) -> Dict[str, Optional[object]]:
    travel_minutes = candidate["travel_minutes"]
    if travel_minutes is not None:
        travel_minutes = int(travel_minutes)
    buffer_minutes = candidate["buffer_minutes"]
    if buffer_override is not None:
        buffer_minutes = buffer_override
    if buffer_minutes is not None:
        buffer_minutes = int(buffer_minutes)
    return {
        "segment_type": "bus",
        "ref_type": ref_type,
        "ref_id": ref_id,
        "service_day": candidate["service_day"],
        "start_time": candidate["departure_time"],
        "end_time": candidate["arrival_time"],
        "origin_stop_id": candidate["departure_stop_id"],
        "destination_stop_id": candidate["arrival_stop_id"],
        "travel_minutes": travel_minutes,
        "buffer_minutes": buffer_minutes,
        "route_id": candidate["route_id"],
        "trip_index": candidate["trip_index"],
        "departure_route_stop_time_id": candidate["departure_route_stop_time_id"],
        "arrival_route_stop_time_id": candidate["arrival_route_stop_time_id"],
        "notes": note,
    }


def build_bus_segment_from_trip(
    trip: sqlite3.Row,
    service_day: str,
    ref_type: str,
    ref_id: Optional[int],
    notes: str,
    buffer_minutes: Optional[int] = None,
) -> Dict[str, Optional[object]]:
    depart_min = time_to_minutes(trip["departure_time"])
    arrival_min = time_to_minutes(trip["arrival_time"])
    travel_minutes = arrival_min - depart_min
    return {
        "segment_type": "bus",
        "ref_type": ref_type,
        "ref_id": ref_id,
        "service_day": service_day,
        "start_time": trip["departure_time"],
        "end_time": trip["arrival_time"],
        "origin_stop_id": trip["departure_stop_id"],
        "destination_stop_id": trip["arrival_stop_id"],
        "travel_minutes": travel_minutes if travel_minutes >= 0 else None,
        "buffer_minutes": buffer_minutes,
        "route_id": trip["route_id"],
        "trip_index": trip["trip_index"],
        "departure_route_stop_time_id": trip["departure_route_stop_time_id"],
        "arrival_route_stop_time_id": trip["arrival_route_stop_time_id"],
        "notes": notes,
    }


def build_game_segment(game: sqlite3.Row, hall_stop_id: Optional[int], end_time_min: int) -> Dict[str, Optional[object]]:
    note = f"{game['tournament_name']} vs {game['opponent_name']} ({game['role']})"
    return {
        "segment_type": "game",
        "ref_type": "schedule_game",
        "ref_id": game["game_id"],
        "service_day": game["service_day_code"],
        "start_time": game["start_time"],
        "end_time": minutes_to_time(end_time_min),
        "origin_stop_id": hall_stop_id,
        "destination_stop_id": hall_stop_id,
        "travel_minutes": None,
        "buffer_minutes": None,
        "route_id": None,
        "trip_index": None,
        "departure_route_stop_time_id": None,
        "arrival_route_stop_time_id": None,
        "notes": note,
    }


def build_meal_segment(start_min: int, end_min: int, lunch_event: sqlite3.Row) -> Dict[str, Optional[object]]:
    return {
        "segment_type": "meal",
        "ref_type": "logistics_event",
        "ref_id": lunch_event["event_id"],
        "service_day": "sat",
        "start_time": minutes_to_time(start_min),
        "end_time": minutes_to_time(end_min),
        "origin_stop_id": lunch_event["anchor_stop_id"],
        "destination_stop_id": lunch_event["anchor_stop_id"],
        "travel_minutes": None,
        "buffer_minutes": None,
        "route_id": None,
        "trip_index": None,
        "departure_route_stop_time_id": None,
        "arrival_route_stop_time_id": None,
        "notes": f"Lunch at {lunch_event['stop_display_name']}",
    }


def build_concert_segment(concert_event: sqlite3.Row) -> Dict[str, Optional[object]]:
    return {
        "segment_type": "concert",
        "ref_type": "logistics_event",
        "ref_id": concert_event["event_id"],
        "service_day": "sat",
        "start_time": concert_event["start_time"],
        "end_time": concert_event["end_time"],
        "origin_stop_id": concert_event["anchor_stop_id"],
        "destination_stop_id": concert_event["anchor_stop_id"],
        "travel_minutes": None,
        "buffer_minutes": None,
        "route_id": None,
        "trip_index": None,
        "departure_route_stop_time_id": None,
        "arrival_route_stop_time_id": None,
        "notes": "Concert at Terningen Arena",
    }


def build_manual_segment(service_day: str, start_min: int, end_min: int, note: str) -> Dict[str, Optional[object]]:
    return {
        "segment_type": "note",
        "ref_type": None,
        "ref_id": None,
        "service_day": service_day,
        "start_time": minutes_to_time(start_min),
        "end_time": minutes_to_time(end_min),
        "origin_stop_id": None,
        "destination_stop_id": None,
        "travel_minutes": None,
        "buffer_minutes": None,
        "route_id": None,
        "trip_index": None,
        "departure_route_stop_time_id": None,
        "arrival_route_stop_time_id": None,
        "notes": note,
    }


def build_charter_segment(
    service_day: str,
    origin_stop_id: Optional[int],
    destination_stop_id: Optional[int],
    start_min: int,
    arrive_min: int,
    note: str,
    ref_type: Optional[str] = None,
    ref_id: Optional[int] = None,
) -> Dict[str, Optional[object]]:
    travel = max(arrive_min - start_min, 15)
    return {
        "segment_type": "bus",
        "ref_type": ref_type,
        "ref_id": ref_id,
        "service_day": service_day,
        "start_time": minutes_to_time(max(start_min, 0)),
        "end_time": minutes_to_time(max(arrive_min, start_min + 15)),
        "origin_stop_id": origin_stop_id,
        "destination_stop_id": destination_stop_id,
        "travel_minutes": travel,
        "buffer_minutes": None,
        "route_id": None,
        "trip_index": None,
        "departure_route_stop_time_id": None,
        "arrival_route_stop_time_id": None,
        "notes": note,
    }


def release_bus_segments(tracker: BusLoadTracker, alias: Optional[sqlite3.Row], segments: List[Dict[str, Optional[object]]], headcount: Optional[int] = None) -> None:
    if headcount is None:
        headcount = int(alias["headcount"] or 0) if alias is not None else 0
    for seg in segments:
        if seg.get("segment_type") == "bus":
            tracker.release(seg.get("service_day"), seg.get("route_id"), seg.get("trip_index"), headcount)


def select_bus_via_candidates(
    conn: sqlite3.Connection,
    tracker: BusLoadTracker,
    alias: sqlite3.Row,
    game: sqlite3.Row,
    origin_stop_id: Optional[int],
    note: str,
    allow_force: bool = True,
) -> Tuple[Optional[Dict[str, Optional[object]]], Optional[int], bool]:
    if origin_stop_id is None:
        return None, None, False
    headcount = int(alias["headcount"] or 0)
    latest_arrival = time_to_minutes(game["start_time"]) - 40
    candidates = fetch_game_bus_candidates(conn, alias["alias_id"], game["game_id"])
    fallback: Optional[sqlite3.Row] = None
    fallback_arrival: Optional[int] = None
    for cand in candidates:
        if cand["departure_stop_id"] != origin_stop_id:
            continue
        arrival_min = time_to_minutes(cand["arrival_time"])
        if arrival_min > latest_arrival:
            continue
        if tracker.assign(cand["service_day"], cand["route_id"], cand["trip_index"], headcount):
            segment = build_bus_segment_from_candidate(cand, "schedule_game", game["game_id"], note)
            return segment, arrival_min, False
        if fallback is None:
            fallback = cand
            fallback_arrival = arrival_min
    if fallback and allow_force:
        tracker.assign(
            fallback["service_day"],
            fallback["route_id"],
            fallback["trip_index"],
            headcount,
            force=True,
        )
        segment = build_bus_segment_from_candidate(
            fallback,
            "schedule_game",
            game["game_id"],
            f"{note} (capacity override)",
        )
        return segment, fallback_arrival, True
    return None, None, False


def select_trip_with_capacity(
    conn: sqlite3.Connection,
    tracker: BusLoadTracker,
    service_day: str,
    origin_stop_id: Optional[int],
    destination_stop_id: Optional[int],
    earliest_depart_min: int,
    headcount: int,
    note: str,
    ref_type: str,
    ref_id: Optional[int],
    latest_arrival_min: Optional[int] = None,
    min_arrival_min: Optional[int] = None,
    target_arrival_min: Optional[int] = None,
    allow_force: bool = True,
) -> Tuple[Optional[Dict[str, Optional[object]]], Optional[int], bool]:
    if origin_stop_id is None or destination_stop_id is None:
        return None, None, False
    trips = list_trips(conn, service_day, origin_stop_id, destination_stop_id, earliest_depart_min)
    fallback: Optional[sqlite3.Row] = None
    fallback_arrival: Optional[int] = None
    for trip in trips:
        arrival_min = time_to_minutes(trip["arrival_time"])
        if min_arrival_min is not None and arrival_min < min_arrival_min:
            continue
        if latest_arrival_min is not None and arrival_min > latest_arrival_min:
            break
        if tracker.assign(service_day, trip["route_id"], trip["trip_index"], headcount):
            buffer_minutes = None
            buffer_target = target_arrival_min if target_arrival_min is not None else latest_arrival_min
            if buffer_target is not None:
                buffer_minutes = buffer_target - arrival_min
            segment = build_bus_segment_from_trip(
                trip,
                service_day,
                ref_type,
                ref_id,
                note,
                buffer_minutes=buffer_minutes,
            )
            return segment, arrival_min, False
        if fallback is None:
            fallback = trip
            fallback_arrival = arrival_min
    if fallback and allow_force:
        tracker.assign(service_day, fallback["route_id"], fallback["trip_index"], headcount, force=True)
        buffer_minutes = None
        buffer_target = target_arrival_min if target_arrival_min is not None else latest_arrival_min
        if buffer_target is not None and fallback_arrival is not None:
            buffer_minutes = buffer_target - fallback_arrival
        segment = build_bus_segment_from_trip(
            fallback,
            service_day,
            ref_type,
            ref_id,
            f"{note} (capacity override)",
            buffer_minutes=buffer_minutes,
        )
        return segment, fallback_arrival, True
    return None, None, False


def plan_game_travel(
    conn: sqlite3.Connection,
    tracker: BusLoadTracker,
    alias: sqlite3.Row,
    lookup: LookupData,
    current_stop_id: Optional[int],
    current_time_min: Optional[int],
    game: sqlite3.Row,
) -> Tuple[List[Dict[str, Optional[object]]], Optional[int], int]:
    segments: List[Dict[str, Optional[object]]] = []
    hall_stop_id = lookup.hall_stop_map.get(game["hall_id"])
    if hall_stop_id is None:
        raise ValueError(f"Savner stop for hall {game['hall_name']}")
    school_stop_id = lookup.school_stop_map.get(alias["school_id"])
    if current_stop_id is None:
        current_stop_id = school_stop_id
    if current_stop_id == hall_stop_id:
        arrival_min = current_time_min if current_time_min is not None else time_to_minutes(game["start_time"]) - 45
        return segments, hall_stop_id, arrival_min
    start_min = time_to_minutes(game["start_time"])
    latest_arrival = start_min - 40
    service_day = game["service_day_code"]
    note = f"Bus to {game['hall_name']} ({(game['match_code'] or '').strip()})".strip()
    headcount = int(alias["headcount"] or 0)
    attempt_origin = current_stop_id
    attempt_time = current_time_min if current_time_min is not None else start_min - (3 * 60)
    attempted_school_reset = False

    while True:
        segment, arrival_min, _ = (select_bus_via_candidates(conn, tracker, alias, game, attempt_origin, note, allow_force=False)
                                   if attempt_origin == school_stop_id
                                   else (None, None, False))
        if segment is None:
            segment, arrival_min, _ = select_trip_with_capacity(
                conn,
                tracker,
                service_day,
                attempt_origin,
                hall_stop_id,
                attempt_time,
                headcount,
                note,
                "schedule_game",
                game["game_id"],
                latest_arrival_min=latest_arrival,
                allow_force=False,
            )
        if segment is not None and arrival_min is not None:
            segments.append(segment)
            return segments, hall_stop_id, arrival_min
        if attempted_school_reset or attempt_origin == school_stop_id:
            break
        transfer_segment, transfer_arrival, _ = select_trip_with_capacity(
            conn,
            tracker,
            service_day,
            attempt_origin,
            school_stop_id,
            attempt_time,
            headcount,
            "Transfer to lodging before next bus",
            "logistics_event",
            None,
            latest_arrival_min=start_min - 60,
            allow_force=False,
        )
        if transfer_segment is None or transfer_arrival is None:
            break
        segments.append(transfer_segment)
        attempt_origin = school_stop_id
        attempt_time = transfer_arrival
        attempted_school_reset = True

    # Relax buffer to 20 minutter hvis standard ikke lykkes.
    for relaxed_buffer in (20, 10):
        relaxed_latest = start_min - relaxed_buffer
        if relaxed_latest <= attempt_time:
            continue
        fallback_segment, fallback_arrival, _ = select_trip_with_capacity(
            conn,
            tracker,
            service_day,
            attempt_origin,
            hall_stop_id,
            attempt_time,
            headcount,
            f"{note} (buffer relaxed to {relaxed_buffer}m)",
            "schedule_game",
            game["game_id"],
            latest_arrival_min=relaxed_latest,
            allow_force=False,
        )
        if fallback_segment is not None and fallback_arrival is not None:
            segments.append(fallback_segment)
            return segments, hall_stop_id, fallback_arrival

    # Absolut fallback: vælg den tidligst mulige tur uanset buffer og markér noten.
    fallback_segment, fallback_arrival, _ = select_trip_with_capacity(
        conn,
        tracker,
        service_day,
        attempt_origin,
        hall_stop_id,
        attempt_time,
        headcount,
        f"{note} (manual buffer review)",
        "schedule_game",
        game["game_id"],
        allow_force=False,
    )
    if fallback_segment is not None and fallback_arrival is not None:
        segments.append(fallback_segment)
        return segments, hall_stop_id, fallback_arrival

    multi_segments, multi_arrival = find_multi_leg_trip(
        conn,
        tracker,
        service_day,
        attempt_origin,
        hall_stop_id,
        attempt_time,
        latest_arrival,
        headcount,
        note,
        "schedule_game",
        game["game_id"],
    )
    if multi_segments is not None and multi_arrival is not None:
        segments.extend(multi_segments)
        return segments, hall_stop_id, multi_arrival

    # Som absolut sidste udvej markeres behovet for manuel transport.
    release_bus_segments(tracker, alias, segments, headcount=headcount)
    manual_start = max(attempt_time, start_min - 60)
    manual_arrival = start_min - 40
    if manual_arrival <= manual_start:
        manual_arrival = max(manual_start + 20, start_min - 30)
    origin_for_charter = attempt_origin or school_stop_id
    charter_segment = build_charter_segment(
        service_day,
        origin_for_charter,
        hall_stop_id,
        manual_start,
        manual_arrival,
        f"Charter transport to {game['hall_name']} (alias {alias['alias_id']})",
        "schedule_game",
        game["game_id"],
    )
    return [charter_segment], hall_stop_id, manual_arrival


def schedule_lunch_between_games(
    conn: sqlite3.Connection,
    tracker: BusLoadTracker,
    alias: sqlite3.Row,
    lookup: LookupData,
    current_stop_id: Optional[int],
    current_time_min: Optional[int],
    next_game: Optional[sqlite3.Row],
) -> Tuple[List[Dict[str, Optional[object]]], Optional[int], Optional[int], Optional[int]]:
    if lookup.lunch_event is None or current_time_min is None or next_game is None:
        return [], current_stop_id, current_time_min, None
    if next_game["service_day_code"] != "sat":
        return [], current_stop_id, current_time_min, None
    next_start_min = time_to_minutes(next_game["start_time"])
    if next_start_min - current_time_min < (LUNCH_DURATION + 60):
        return [], current_stop_id, current_time_min, None
    if current_time_min > LUNCH_WINDOW_MAX:
        return [], current_stop_id, current_time_min, None

    headcount = int(alias["headcount"] or 0)
    lunch_stop = lookup.lunch_event["anchor_stop_id"]
    min_arrival = max(LUNCH_WINDOW_MIN, current_time_min)
    max_arrival = min(LUNCH_WINDOW_MAX, next_start_min - 40)
    if min_arrival >= max_arrival:
        return [], current_stop_id, current_time_min, None

    bus_to_lunch, arrival_lunch, forced1 = select_trip_with_capacity(
        conn,
        tracker,
        "sat",
        current_stop_id,
        lunch_stop,
        current_time_min,
        headcount,
        f"Bus to lunch ({lookup.lunch_event['stop_display_name']})",
        "logistics_event",
        lookup.lunch_event["event_id"],
        latest_arrival_min=max_arrival,
        min_arrival_min=min_arrival,
        allow_force=False,
    )
    if bus_to_lunch is None or arrival_lunch is None:
        return [], current_stop_id, current_time_min, None

    meal_start = max(arrival_lunch, LUNCH_WINDOW_MIN)
    meal_end = min(meal_start + LUNCH_DURATION, max_arrival)
    if meal_end - meal_start < 15:
        tracker.release("sat", bus_to_lunch["route_id"], bus_to_lunch["trip_index"], headcount)
        return [], current_stop_id, current_time_min, None

    meal_segment = build_meal_segment(meal_start, meal_end, lookup.lunch_event)

    next_hall_stop = lookup.hall_stop_map.get(next_game["hall_id"])
    bus_to_next, arrival_next, forced2 = select_trip_with_capacity(
        conn,
        tracker,
        next_game["service_day_code"],
        lunch_stop,
        next_hall_stop,
        meal_end,
        headcount,
        f"Bus to {next_game['hall_name']} (post-lunch)",
        "schedule_game",
        next_game["game_id"],
        latest_arrival_min=time_to_minutes(next_game["start_time"]) - 40,
        allow_force=False,
    )
    if bus_to_next is None or arrival_next is None:
        tracker.release("sat", bus_to_lunch["route_id"], bus_to_lunch["trip_index"], headcount)
        return [], current_stop_id, current_time_min, None

    return (
        [bus_to_lunch, meal_segment, bus_to_next],
        next_hall_stop,
        arrival_next,
        next_game["game_id"],
    )


def schedule_lunch_after_day(
    conn: sqlite3.Connection,
    tracker: BusLoadTracker,
    alias: sqlite3.Row,
    lookup: LookupData,
    current_stop_id: Optional[int],
    current_time_min: Optional[int],
) -> Tuple[List[Dict[str, Optional[object]]], Optional[int], Optional[int]]:
    if lookup.lunch_event is None:
        return [], current_stop_id, current_time_min
    if current_time_min is None:
        current_time_min = LUNCH_WINDOW_MIN
    if current_time_min > LUNCH_WINDOW_MAX:
        return [], current_stop_id, current_time_min

    headcount = int(alias["headcount"] or 0)
    bus_to_lunch, arrival, _ = select_trip_with_capacity(
        conn,
        tracker,
        "sat",
        current_stop_id,
        lookup.lunch_event["anchor_stop_id"],
        current_time_min,
        headcount,
        f"Bus to lunch ({lookup.lunch_event['stop_display_name']})",
        "logistics_event",
        lookup.lunch_event["event_id"],
        latest_arrival_min=LUNCH_WINDOW_MAX,
        min_arrival_min=LUNCH_WINDOW_MIN,
        allow_force=False,
    )
    if bus_to_lunch is None or arrival is None:
        return [], current_stop_id, current_time_min

    meal_start = max(arrival, LUNCH_WINDOW_MIN)
    meal_end = min(meal_start + LUNCH_DURATION, LUNCH_WINDOW_MAX)
    meal_segment = build_meal_segment(meal_start, meal_end, lookup.lunch_event)
    return [bus_to_lunch, meal_segment], lookup.lunch_event["anchor_stop_id"], meal_end


def schedule_concert_block(
    conn: sqlite3.Connection,
    tracker: BusLoadTracker,
    alias: sqlite3.Row,
    lookup: LookupData,
    current_stop_id: Optional[int],
    current_time_min: Optional[int],
) -> Tuple[List[Dict[str, Optional[object]]], Optional[int], Optional[int]]:
    segments: List[Dict[str, Optional[object]]] = []
    concert = lookup.concert_event
    if concert is None:
        return segments, current_stop_id, current_time_min

    headcount = int(alias["headcount"] or 0)
    origin_stop = current_stop_id or lookup.school_stop_map.get(alias["school_id"])
    concert_start_min = time_to_minutes(concert["start_time"])
    min_arrival = max(concert_start_min - 90, 0)
    max_arrival = concert_start_min - CONCERT_BUFFER_MIN
    earliest_depart = max(current_time_min or 0, CONCERT_SOFT_EARLIEST)

    bus_to_concert = None
    arrival = None
    if origin_stop == concert["anchor_stop_id"]:
        stay_start = current_time_min or earliest_depart
        stay_end = max(stay_start, concert_start_min - CONCERT_BUFFER_MIN)
        segments.append(
            {
                "segment_type": "stay",
                "ref_type": "logistics_event",
                "ref_id": concert["event_id"],
                "service_day": "sat",
                "start_time": minutes_to_time(stay_start),
                "end_time": minutes_to_time(stay_end),
                "origin_stop_id": concert["anchor_stop_id"],
                "destination_stop_id": concert["anchor_stop_id"],
                "travel_minutes": None,
                "buffer_minutes": concert_start_min - stay_end,
                "route_id": None,
                "trip_index": None,
                "departure_route_stop_time_id": None,
                "arrival_route_stop_time_id": None,
                "notes": "Stay at Terningen Arena before concert",
            }
        )
        current_stop_id = concert["anchor_stop_id"]
        current_time_min = stay_end
    else:
        offsets = [0, -15, -20, -30, -40, -45, -50, -60, 10, 20, 30, 45, 60]
        for offset in offsets:
            depart_candidate = earliest_depart + offset
            if depart_candidate < 0:
                continue
            candidate, arrival_candidate, _ = select_trip_with_capacity(
                conn,
                tracker,
                "sat",
                origin_stop,
                concert["anchor_stop_id"],
                depart_candidate,
                headcount,
                f"Bus to concert ({concert['stop_display_name']})",
                "logistics_event",
                concert["event_id"],
                latest_arrival_min=max_arrival,
                min_arrival_min=min_arrival,
                allow_force=False,
            )
            if candidate is not None and arrival_candidate is not None:
                bus_to_concert = candidate
                arrival = arrival_candidate
                break
        if bus_to_concert is None:
            charter = build_charter_segment(
                "sat",
                origin_stop,
                concert["anchor_stop_id"],
                earliest_depart,
                concert_start_min - CONCERT_BUFFER_MIN,
                f"Charter transport to concert ({concert['stop_display_name']})",
                "logistics_event",
                concert["event_id"],
            )
            segments.append(charter)
            current_stop_id = concert["anchor_stop_id"]
            current_time_min = concert_start_min - CONCERT_BUFFER_MIN
        else:
            segments.append(bus_to_concert)
            current_stop_id = concert["anchor_stop_id"]
            current_time_min = arrival if arrival is not None else current_time_min

    segments.append(build_concert_segment(concert))
    current_stop_id = concert["anchor_stop_id"]
    concert_end_min = time_to_minutes(concert["end_time"])
    current_time_min = concert_end_min

    school_stop = lookup.school_stop_map.get(alias["school_id"])
    return_trip, return_arrival, _ = select_trip_with_capacity(
        conn,
        tracker,
        "sat",
        concert["anchor_stop_id"],
        school_stop,
        concert_end_min,
        headcount,
        "Return to lodging after concert",
        "logistics_event",
        concert["event_id"],
        allow_force=False,
    )
    if return_trip is not None:
        segments.append(return_trip)
        current_stop_id = school_stop
        current_time_min = return_arrival

    return segments, current_stop_id, current_time_min


def schedule_return_to_lodging(
    conn: sqlite3.Connection,
    tracker: BusLoadTracker,
    alias: sqlite3.Row,
    lookup: LookupData,
    service_day: str,
    current_stop_id: Optional[int],
    current_time_min: Optional[int],
) -> Tuple[List[Dict[str, Optional[object]]], Optional[int], Optional[int]]:
    school_stop = lookup.school_stop_map.get(alias["school_id"])
    if current_stop_id == school_stop:
        return [], current_stop_id, current_time_min
    headcount = int(alias["headcount"] or 0)
    bus_segment, arrival, _ = select_trip_with_capacity(
        conn,
        tracker,
        service_day,
        current_stop_id,
        school_stop,
        current_time_min or 0,
        headcount,
        "Return to lodging",
        "logistics_event",
        None,
        allow_force=False,
    )
    if bus_segment is None:
        return [], current_stop_id, current_time_min
    return [bus_segment], school_stop, arrival


def generate_segments_for_alias(
    conn: sqlite3.Connection,
    alias: sqlite3.Row,
    lookup: LookupData,
    tracker: BusLoadTracker,
) -> List[Dict[str, Optional[object]]]:
    segments: List[Dict[str, Optional[object]]] = []
    games = fetch_games_for_alias(conn, alias["alias_id"])

    if not games:
        current_stop = lookup.school_stop_map.get(alias["school_id"])
        current_time = LUNCH_WINDOW_MIN
        lunch_segments, current_stop, current_time = schedule_lunch_after_day(
            conn, tracker, alias, lookup, current_stop, current_time
        )
        segments.extend(lunch_segments)
        concert_segments, current_stop, current_time = schedule_concert_block(
            conn, tracker, alias, lookup, current_stop, current_time
        )
        segments.extend(concert_segments)
        return segments

    games_by_date: Dict[str, List[sqlite3.Row]] = defaultdict(list)
    for game in games:
        games_by_date[game["date"]].append(game)

    for date in sorted(games_by_date.keys()):
        day_games = sorted(games_by_date[date], key=lambda g: (g["start_time"], g["game_id"]))
        service_day = day_games[0]["service_day_code"]
        current_stop_id = lookup.school_stop_map.get(alias["school_id"])
        current_time_min: Optional[int] = None
        prepared_game_id: Optional[int] = None
        lunch_taken = False

        for idx, game in enumerate(day_games):
            if prepared_game_id == game["game_id"]:
                # Game transport already planned during lunch, keep current position
                prepared_game_id = None
                arrival_min = current_time_min if current_time_min is not None else time_to_minutes(game["start_time"]) - 40
            else:
                travel_segments, current_stop_id, arrival_min = plan_game_travel(
                    conn, tracker, alias, lookup, current_stop_id, current_time_min, game
                )
                segments.extend(travel_segments)
            current_time_min = arrival_min

            duration = lookup.tournament_durations.get(game["tournament_id"], 25)
            start_min = time_to_minutes(game["start_time"])
            end_min = start_min + duration
            segments.append(build_game_segment(game, current_stop_id, end_min))
            current_time_min = end_min

            if service_day == "sat" and not lunch_taken:
                next_game = day_games[idx + 1] if idx + 1 < len(day_games) else None
                lunch_segments, current_stop_id, current_time_min, prepared_game_id = schedule_lunch_between_games(
                    conn,
                    tracker,
                    alias,
                    lookup,
                    current_stop_id,
                    current_time_min,
                    next_game,
                )
                if lunch_segments:
                    segments.extend(lunch_segments)
                    lunch_taken = True

        if service_day == "sat":
            if not lunch_taken:
                lunch_segments, current_stop_id, current_time_min = schedule_lunch_after_day(
                    conn, tracker, alias, lookup, current_stop_id, current_time_min
                )
                segments.extend(lunch_segments)
            concert_segments, current_stop_id, current_time_min = schedule_concert_block(
                conn, tracker, alias, lookup, current_stop_id, current_time_min
            )
            segments.extend(concert_segments)
            if lookup.concert_event is None:
                return_segments, current_stop_id, current_time_min = schedule_return_to_lodging(
                    conn, tracker, alias, lookup, service_day, current_stop_id, current_time_min
                )
                segments.extend(return_segments)
        else:
            return_segments, current_stop_id, current_time_min = schedule_return_to_lodging(
                conn, tracker, alias, lookup, service_day, current_stop_id, current_time_min
            )
            segments.extend(return_segments)

    return segments


def insert_segments(conn: sqlite3.Connection, alias_id: int, segments: List[Dict[str, Optional[object]]]) -> int:
    # Sort segments chronologically by service_day and start_time
    day_order = {"fri": 1, "sat": 2, "sun": 3}
    segments_sorted = sorted(
        segments,
        key=lambda s: (
            day_order.get(s.get("service_day", ""), 999),
            s.get("start_time", "99:99")
        )
    )

    for sequence_no, segment in enumerate(segments_sorted, start=1):
        conn.execute(
            """
            INSERT INTO team_itinerary_segments (
                alias_id,
                sequence_no,
                segment_type,
                ref_type,
                ref_id,
                service_day,
                start_time,
                end_time,
                origin_stop_id,
                destination_stop_id,
                travel_minutes,
                buffer_minutes,
                route_id,
                trip_index,
                departure_route_stop_time_id,
                arrival_route_stop_time_id,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alias_id,
                sequence_no,
                segment["segment_type"],
                segment.get("ref_type"),
                segment.get("ref_id"),
                segment.get("service_day"),
                segment.get("start_time"),
                segment.get("end_time"),
                segment.get("origin_stop_id"),
                segment.get("destination_stop_id"),
                segment.get("travel_minutes"),
                segment.get("buffer_minutes"),
                segment.get("route_id"),
                segment.get("trip_index"),
                segment.get("departure_route_stop_time_id"),
                segment.get("arrival_route_stop_time_id"),
                segment.get("notes"),
            ),
        )
    return len(segments)


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing database: {DB_PATH}. Run build_event_db.py first.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    lookup = load_lookup_data(conn)
    tracker = BusLoadTracker(BUS_CAPACITY_LIMIT)

    conn.execute("DELETE FROM team_itinerary_segments")

    aliases = conn.execute(
        """
        SELECT alias_id, squad_index, lodging_team_id, schedule_team_id, school_id, school_name, headcount
        FROM vw_team_alignment
        ORDER BY lodging_club, division_key, raw_label, squad_index
        """
    ).fetchall()

    total_segments = 0
    for alias in aliases:
        segs = generate_segments_for_alias(conn, alias, lookup, tracker)
        total_segments += insert_segments(conn, alias["alias_id"], segs)

    conn.commit()
    conn.close()
    print(f"Generated {total_segments} itinerary segments for {len(aliases)} squads.")


if __name__ == "__main__":
    main()

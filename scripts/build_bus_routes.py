#!/usr/bin/env python3
"""
ETL pipeline for the Elverum shuttle bus schedules.

The script parses the plain-text extraction of `bussruter-eyc (1).pdf`,
reconstructs the tables for each route, normalises stop names, and emits a
relational SQLite database at `data/build/bus_routes.db`.

Assumptions (documented for traceability):
- Route 1 and Route 3 operate on Saturday only (`kun lør` headers).
- Route 2 runs every 30 minutes across all three days; last departures are
  17:00 (Fri/Sun) and 19:00 (Sat) as indicated by `siste avg søn` / `siste avg lør`.
- Rows containing `:mm` without an hour represent shorthand for the 30-minute
  cadence; we regenerate the full timetable programmatically.
- `Thon Central (lørdag)` on Route 2 is informational (no explicit departures in
  the table) but is still created as a stop so it can be linked in later logic.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

ROOT = Path(__file__).resolve().parent.parent
TEXT_FILE = ROOT / "data" / "raw" / "bus_routes_text.txt"
DB_FILE = ROOT / "data" / "build" / "bus_routes.db"
SQL_DUMP_FILE = ROOT / "data" / "build" / "bus_routes.sql"

# --------------------------------------------------------------------------- #
# Helper dataclasses


@dataclass
class RouteStop:
    raw_name: str
    canonical_name: str
    display_name: str
    stop_order: int
    default_offset_min: Optional[int] = None
    times: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))


@dataclass
class RouteData:
    route_number: int
    title: str
    frequency_note: str
    extra_notes: List[str]
    stops: List[RouteStop]


# --------------------------------------------------------------------------- #
def parse_stop_descriptions() -> Dict[str, str]:
    """Extract stop descriptions from the narrative section."""
    if not TEXT_FILE.exists():
        raise FileNotFoundError(
            f"Plain text dump missing: {TEXT_FILE}. "
            "Ensure the PDF extraction helper was executed."
        )
    lines = TEXT_FILE.read_text(encoding="utf-8").splitlines()
    descriptions: Dict[str, str] = {}
    idx = 0
    while idx < len(lines):
        if lines[idx].strip().lower().startswith("busstopp"):
            idx += 1
            current_name: Optional[str] = None
            buffer: List[str] = []
            while idx < len(lines):
                raw = lines[idx].rstrip()
                stripped = raw.strip()
                if not stripped:
                    idx += 1
                    continue
                if stripped.startswith("Rute "):
                    if current_name and buffer:
                        descriptions[current_name] = " ".join(buffer).strip()
                    return descriptions
                if stripped.endswith(":"):
                    if current_name and buffer:
                        text = " ".join(buffer).strip()
                        descriptions[current_name] = text
                        canonical, _ = canonicalise_stop(current_name)
                        descriptions.setdefault(canonical, text)
                    current_name = stripped[:-1].strip()
                    buffer = []
                else:
                    buffer.append(stripped)
                idx += 1
            if current_name and buffer:
                text = " ".join(buffer).strip()
                descriptions[current_name] = text
                canonical, _ = canonicalise_stop(current_name)
                descriptions.setdefault(canonical, text)
            break
        idx += 1
    return descriptions


CANONICAL_STOP_NAMES: Dict[str, str] = {
    "Ydalir ": "Ydalir",
    "Ydalir": "Ydalir",
    "EUS": "Elverum ungdomsskole (EUS)",
    "EUS*": "Elverum ungdomsskole (EUS)",
    "ELVIS": "Elverum videregående skole (ELVIS)",
    "Terningen A.": "Terningen Arena",
    "Terningen Arena": "Terningen Arena",
    "Søndre Elv.": "Søndre Elverum",
    "Søndre Elverum": "Søndre Elverum",
    "Thon Central (lørdag)": "Thon Central (lørdag)",
    "Thon Central": "Thon Central (lørdag)",
}


def canonicalise_stop(raw_name: str) -> Tuple[str, str]:
    """Return canonical name plus clean display label."""
    cleaned = raw_name.strip()
    canonical = CANONICAL_STOP_NAMES.get(cleaned, cleaned)
    return canonical, canonical  # use canonical as default display


TIME_TOKEN = "%H:%M"


def parse_time(token: str) -> datetime:
    return datetime.strptime(token, TIME_TOKEN)


def minutes_between(later: str, earlier: str) -> int:
    return int((parse_time(later) - parse_time(earlier)).total_seconds() // 60)


# --------------------------------------------------------------------------- #
# Route parsing


def is_time_token(value: str) -> bool:
    value = value.strip()
    if value.startswith(":"):
        return False
    if value.count(":") == 1:
        hh, mm = value.split(":")
        return hh.isdigit() and len(mm) == 2 and mm.isdigit()
    return False


def parse_bus_data(text_file: Path, stop_descriptions: Dict[str, str]) -> Tuple[Dict[int, RouteData], List[str]]:
    if not text_file.exists():
        raise FileNotFoundError(f"Plain text dump missing: {text_file}")

    lines = text_file.read_text(encoding="utf-8").splitlines()

    known_stops: Set[str] = set(stop_descriptions.keys())
    known_stops.update(CANONICAL_STOP_NAMES.keys())
    known_stops.update(CANONICAL_STOP_NAMES.values())

    # Normalise variants without trailing colon for quick lookup.
    normalised_stop_lookup: Dict[str, str] = {}
    for name in known_stops:
        normalised_stop_lookup[name] = name
        normalised_stop_lookup[name.rstrip(":")] = name

    routes: Dict[int, RouteData] = {}
    current_route: Optional[RouteData] = None
    current_stop: Optional[RouteStop] = None
    seen_sequences = 0
    skip_busstop = False

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.lower().startswith("busstopp"):
            skip_busstop = True
            continue
        if skip_busstop and not stripped.startswith("Rute "):
            continue
        if skip_busstop and stripped.startswith("Rute "):
            skip_busstop = False
        if stripped.startswith("Rute "):
            try:
                route_number = int(stripped.split()[1])
            except (IndexError, ValueError):
                continue
            current_route = RouteData(
                route_number=route_number,
                title=f"Rute {route_number}",
                frequency_note="",
                extra_notes=[],
                stops=[],
            )
            routes[route_number] = current_route
            current_stop = None
            seen_sequences = 0
            continue

        if current_route is None:
            continue

        lower = stripped.lower()
        if lower.startswith("hvert") or lower.startswith("hver"):
            current_route.frequency_note = stripped
            continue
        if lower.startswith("kun ") or lower.startswith("siste avg"):
            current_route.extra_notes.append(stripped)
            continue

        normalised = stripped.rstrip(":")
        if normalised in normalised_stop_lookup:
            canonical, display = canonicalise_stop(normalised)
            seen_sequences += 1
            current_stop = RouteStop(
                raw_name=normalised,
                canonical_name=canonical,
                display_name=display,
                stop_order=seen_sequences,
                times={"raw": []},
            )
            current_route.stops.append(current_stop)
            continue

        if is_time_token(stripped):
            if current_stop is not None:
                current_stop.times.setdefault("raw", []).append(stripped)
            continue

        # Ignore other informational lines
        continue

    all_stops = sorted({stop.canonical_name for route in routes.values() for stop in route.stops})
    return routes, all_stops


def expand_route_times(route: RouteData) -> None:
    """Normalise raw timetable tokens into per-day departure lists."""
    if route.route_number in (1, 3):
        # Saturday-only service; raw tokens already contain HH:MM.
        for stop in route.stops:
            raw_times = stop.times.pop("raw", [])
            if not raw_times:
                continue
            stop.times["sat"] = raw_times
    elif route.route_number == 2:
        # Extract last departures for each day (explicit values from the PDF).
        last_departures: Dict[str, str] = {"sat": "19:00", "sun": "17:00", "fri": "17:00"}
        # Identify explicit times tied to the header row (y == 511.44)
        header_times = [stop for stop in route.stops if stop.raw_name == "EUS"]
        if not header_times:
            raise ValueError("Route 2 expected to contain an EUS row for base departures.")
        base_stop = header_times[0]
        raw_times = base_stop.times.get("raw", [])
        explicit = [token for token in raw_times if token.count(":") == 1 and not token.startswith(":")]
        if len(explicit) < 2:
            raise ValueError("Route 2 requires at least two explicit departure times to determine cadence.")
        start_time = explicit[0]
        interval_minutes = minutes_between(explicit[1], explicit[0])
        if interval_minutes <= 0:
            raise ValueError("Invalid interval computed for Route 2 timetable.")

        # Compute offsets per stop (difference from base departure).
        for stop in route.stops:
            tokens = stop.times.get("raw", [])
            first_explicit = next(
                (t for t in tokens if t.count(":") == 1 and not t.startswith(":")), None
            )
            if not first_explicit:
                stop.default_offset_min = None
                continue
            stop.default_offset_min = minutes_between(first_explicit, start_time)

        # Generate departures per service day.
        for stop in route.stops:
            tokens = stop.times.get("raw", [])
            stop.times.clear()
            if stop.default_offset_min is None:
                continue
            for day, last_time in last_departures.items():
                effective_last = last_departures.get("sun") if day == "fri" else last_time
                effective_last = effective_last or last_departures["sun"]
                current = parse_time(start_time)
                final = parse_time(effective_last)
                times_for_day: List[str] = []
                while current <= final:
                    departure = current + timedelta(minutes=stop.default_offset_min)
                    times_for_day.append(departure.strftime(TIME_TOKEN))
                    current += timedelta(minutes=interval_minutes)
                stop.times[day] = times_for_day
    else:
        raise NotImplementedError(f"Unexpected route number: {route.route_number}")

    # Sort times for each stop/day to ensure deterministic output.
    for stop in route.stops:
        for day, tokens in stop.times.items():
            stop.times[day] = sorted(tokens)


# --------------------------------------------------------------------------- #
# Database output


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS routes (
    route_id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_number INTEGER NOT NULL UNIQUE,
    title TEXT NOT NULL,
    frequency_note TEXT,
    extra_notes TEXT
);

CREATE TABLE IF NOT EXISTS stops (
    stop_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stop_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS route_stops (
    route_stop_id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL,
    stop_id INTEGER NOT NULL,
    stop_order INTEGER NOT NULL,
    default_offset_min INTEGER,
    UNIQUE(route_id, stop_order),
    FOREIGN KEY (route_id) REFERENCES routes(route_id),
    FOREIGN KEY (stop_id) REFERENCES stops(stop_id)
);

CREATE TABLE IF NOT EXISTS route_stop_times (
    route_stop_time_id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL,
    stop_id INTEGER NOT NULL,
    stop_order INTEGER NOT NULL,
    service_day TEXT NOT NULL,
    departure_time TEXT NOT NULL,
    condition_note TEXT,
    FOREIGN KEY (route_id) REFERENCES routes(route_id),
    FOREIGN KEY (stop_id) REFERENCES stops(stop_id)
);

CREATE INDEX IF NOT EXISTS idx_route_stop_times_lookup
    ON route_stop_times(route_id, service_day, departure_time);
"""


def build_database(routes: List[RouteData], stop_descriptions: Dict[str, str]) -> None:
    if DB_FILE.exists():
        DB_FILE.unlink()
    conn = sqlite3.connect(DB_FILE)
    conn.executescript(SCHEMA_SQL)

    # Insert stops first to obtain consistent IDs.
    stop_catalog: Dict[str, int] = {}
    for route in routes:
        for stop in route.stops:
            canonical = stop.canonical_name
            if canonical in stop_catalog:
                continue
            description = stop_descriptions.get(stop.raw_name.strip())
            if description is None:
                description = stop_descriptions.get(canonical)
            conn.execute(
                "INSERT INTO stops (stop_name, display_name, description) VALUES (?, ?, ?)",
                (canonical, stop.display_name, description),
            )
            stop_catalog[canonical] = conn.execute(
                "SELECT stop_id FROM stops WHERE stop_name = ?", (canonical,)
            ).fetchone()[0]

    # Insert routes and associated schedules.
    for route in routes:
        extra_notes = "; ".join(route.extra_notes) if route.extra_notes else None
        conn.execute(
            "INSERT INTO routes (route_number, title, frequency_note, extra_notes) VALUES (?, ?, ?, ?)",
            (route.route_number, route.title, route.frequency_note, extra_notes),
        )
        route_id = conn.execute(
            "SELECT route_id FROM routes WHERE route_number = ?", (route.route_number,)
        ).fetchone()[0]

        for stop in route.stops:
            stop_id = stop_catalog[stop.canonical_name]
            conn.execute(
                """
                INSERT INTO route_stops (route_id, stop_id, stop_order, default_offset_min)
                VALUES (?, ?, ?, ?)
                """,
                (route_id, stop_id, stop.stop_order, stop.default_offset_min),
            )
            for day, departures in stop.times.items():
                for dep in departures:
                    conn.execute(
                        """
                        INSERT INTO route_stop_times (route_id, stop_id, stop_order, service_day, departure_time, condition_note)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (route_id, stop_id, stop.stop_order, day, dep, None),
                    )

    conn.commit()

    # Emit SQL dump for transparency.
    with SQL_DUMP_FILE.open("w", encoding="utf-8") as dump:
        for line in conn.iterdump():
            dump.write(f"{line}\n")

    conn.close()


# --------------------------------------------------------------------------- #
# Main orchestration


def main() -> None:
    stop_descriptions = parse_stop_descriptions()
    routes_map, _ = parse_bus_data(TEXT_FILE, stop_descriptions)

    routes: List[RouteData] = []
    for route_number in sorted(routes_map.keys()):
        route = routes_map[route_number]
        expand_route_times(route)
        routes.append(route)

    build_database(routes, stop_descriptions)
    print(f"Created {DB_FILE} with {len(routes)} routes.")


if __name__ == "__main__":
    main()

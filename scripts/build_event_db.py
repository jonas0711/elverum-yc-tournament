#!/usr/bin/env python3
"""
Combine transport, lodging, and tournament datasets into a single
event_planner SQLite database.

Source databases (must exist beforehand):
    data/build/bus_routes.db
    data/build/lodging.db
    data/build/tournament.db

Output:
    data/build/event_planner.db
    data/build/event_planner.sql
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
BUS_DB = ROOT / "data" / "build" / "bus_routes.db"
LODGING_DB = ROOT / "data" / "build" / "lodging.db"
TOURNAMENT_DB = ROOT / "data" / "build" / "tournament.db"
TARGET_DB = ROOT / "data" / "build" / "event_planner.db"
TARGET_SQL = ROOT / "data" / "build" / "event_planner.sql"


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

-- Transport domain ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS transport_routes (
    route_id INTEGER PRIMARY KEY,
    route_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    frequency_note TEXT,
    extra_notes TEXT
);

CREATE TABLE IF NOT EXISTS transport_stops (
    stop_id INTEGER PRIMARY KEY,
    stop_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS transport_route_stops (
    route_stop_id INTEGER PRIMARY KEY,
    route_id INTEGER NOT NULL,
    stop_id INTEGER NOT NULL,
    stop_order INTEGER NOT NULL,
    default_offset_min INTEGER,
    UNIQUE(route_id, stop_order),
    FOREIGN KEY (route_id) REFERENCES transport_routes(route_id),
    FOREIGN KEY (stop_id) REFERENCES transport_stops(stop_id)
);

CREATE TABLE IF NOT EXISTS transport_route_stop_times (
    route_stop_time_id INTEGER PRIMARY KEY,
    route_id INTEGER NOT NULL,
    stop_id INTEGER NOT NULL,
    stop_order INTEGER NOT NULL,
    service_day TEXT NOT NULL,
    departure_time TEXT NOT NULL,
    condition_note TEXT,
    FOREIGN KEY (route_id) REFERENCES transport_routes(route_id),
    FOREIGN KEY (stop_id) REFERENCES transport_stops(stop_id)
);

CREATE TABLE IF NOT EXISTS transport_stop_links (
    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    stop_id INTEGER NOT NULL,
    lodging_school_id INTEGER,
    schedule_hall_id INTEGER,
    FOREIGN KEY (stop_id) REFERENCES transport_stops(stop_id),
    FOREIGN KEY (lodging_school_id) REFERENCES lodging_schools(school_id),
    FOREIGN KEY (schedule_hall_id) REFERENCES schedule_halls(hall_id)
);

-- Lodging domain -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS lodging_schools (
    school_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS lodging_clubs (
    club_id INTEGER PRIMARY KEY,
    school_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    UNIQUE (school_id, name),
    FOREIGN KEY (school_id) REFERENCES lodging_schools(school_id)
);

CREATE TABLE IF NOT EXISTS lodging_teams (
    team_id INTEGER PRIMARY KEY,
    club_id INTEGER NOT NULL,
    raw_label TEXT NOT NULL,
    gender TEXT,
    year INTEGER,
    num_teams INTEGER,
    headcount INTEGER,
    room_text TEXT,
    division_key TEXT,
    FOREIGN KEY (club_id) REFERENCES lodging_clubs(club_id)
);

CREATE TABLE IF NOT EXISTS lodging_rooms (
    room_id INTEGER PRIMARY KEY,
    school_id INTEGER NOT NULL,
    room_code TEXT NOT NULL,
    UNIQUE (school_id, room_code),
    FOREIGN KEY (school_id) REFERENCES lodging_schools(school_id)
);

CREATE TABLE IF NOT EXISTS lodging_team_rooms (
    team_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    PRIMARY KEY (team_id, room_id),
    FOREIGN KEY (team_id) REFERENCES lodging_teams(team_id),
    FOREIGN KEY (room_id) REFERENCES lodging_rooms(room_id)
);

CREATE TABLE IF NOT EXISTS lodging_team_squads (
    squad_id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    squad_index INTEGER NOT NULL,
    UNIQUE (team_id, squad_index),
    FOREIGN KEY (team_id) REFERENCES lodging_teams(team_id)
);

-- Tournament domain --------------------------------------------------------
CREATE TABLE IF NOT EXISTS schedule_halls (
    hall_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS schedule_event_days (
    day_id INTEGER PRIMARY KEY,
    date TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schedule_tournaments (
    tournament_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    gender TEXT,
    age INTEGER,
    birth_year INTEGER,
    pool_code TEXT
);

CREATE TABLE IF NOT EXISTS schedule_teams (
    team_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS schedule_games (
    game_id INTEGER PRIMARY KEY,
    tournament_id INTEGER NOT NULL,
    hall_id INTEGER NOT NULL,
    day_id INTEGER NOT NULL,
    match_code TEXT,
    start_time TEXT NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    FOREIGN KEY (tournament_id) REFERENCES schedule_tournaments(tournament_id),
    FOREIGN KEY (hall_id) REFERENCES schedule_halls(hall_id),
    FOREIGN KEY (day_id) REFERENCES schedule_event_days(day_id),
    FOREIGN KEY (home_team_id) REFERENCES schedule_teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES schedule_teams(team_id)
);

-- Cross-domain team alignment placeholder ----------------------------------
CREATE TABLE IF NOT EXISTS team_aliases (
    alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lodging_team_id INTEGER,
    schedule_team_id INTEGER,
    squad_index INTEGER,
    note TEXT,
    FOREIGN KEY (lodging_team_id) REFERENCES lodging_teams(team_id),
    FOREIGN KEY (schedule_team_id) REFERENCES schedule_teams(team_id)
);

-- Event logistics ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS logistics_events (
    event_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    service_day TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    anchor_stop_id INTEGER NOT NULL,
    notes TEXT,
    CHECK (event_type IN ('lunch', 'concert')),
    FOREIGN KEY (anchor_stop_id) REFERENCES transport_stops(stop_id)
);

CREATE TABLE IF NOT EXISTS team_itinerary_segments (
    segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    alias_id INTEGER NOT NULL,
    sequence_no INTEGER NOT NULL,
    segment_type TEXT NOT NULL,
    ref_type TEXT,
    ref_id INTEGER,
    service_day TEXT,
    start_time TEXT,
    end_time TEXT,
    origin_stop_id INTEGER,
    destination_stop_id INTEGER,
    travel_minutes INTEGER,
    buffer_minutes INTEGER,
    route_id INTEGER,
    trip_index INTEGER,
    departure_route_stop_time_id INTEGER,
    arrival_route_stop_time_id INTEGER,
    notes TEXT,
    UNIQUE (alias_id, sequence_no),
    CHECK (segment_type IN ('game', 'bus', 'meal', 'concert', 'stay', 'note', 'placeholder')),
    FOREIGN KEY (alias_id) REFERENCES team_aliases(alias_id),
    FOREIGN KEY (origin_stop_id) REFERENCES transport_stops(stop_id),
    FOREIGN KEY (destination_stop_id) REFERENCES transport_stops(stop_id),
    FOREIGN KEY (route_id) REFERENCES transport_routes(route_id)
);
"""


def fetch_all(conn: sqlite3.Connection, query: str) -> Iterable[Tuple]:
    return conn.execute(query).fetchall()


def copy_domain_data() -> None:
    if not (BUS_DB.exists() and LODGING_DB.exists() and TOURNAMENT_DB.exists()):
        raise FileNotFoundError("Source databases not found. Run domain ETL scripts first.")

    if TARGET_DB.exists():
        TARGET_DB.unlink()

    master = sqlite3.connect(TARGET_DB)
    master.executescript(SCHEMA_SQL)

    # ------------------------- Transport data ------------------------------
    bus = sqlite3.connect(BUS_DB)
    master.executemany(
        "INSERT INTO transport_routes (route_id, route_number, title, frequency_note, extra_notes) VALUES (?, ?, ?, ?, ?)",
        fetch_all(bus, "SELECT route_id, route_number, title, frequency_note, extra_notes FROM routes"),
    )
    master.executemany(
        "INSERT INTO transport_stops (stop_id, stop_name, display_name, description) VALUES (?, ?, ?, ?)",
        fetch_all(bus, "SELECT stop_id, stop_name, display_name, description FROM stops"),
    )
    master.executemany(
        """
        INSERT INTO transport_route_stops (route_stop_id, route_id, stop_id, stop_order, default_offset_min)
        VALUES (?, ?, ?, ?, ?)
        """,
        fetch_all(
            bus,
            "SELECT route_stop_id, route_id, stop_id, stop_order, default_offset_min FROM route_stops",
        ),
    )
    master.executemany(
        """
        INSERT INTO transport_route_stop_times (route_stop_time_id, route_id, stop_id, stop_order, service_day, departure_time, condition_note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        fetch_all(
            bus,
            """
            SELECT route_stop_time_id, route_id, stop_id, stop_order, service_day, departure_time, condition_note
            FROM route_stop_times
            """,
        ),
    )
    bus.close()

    # ------------------------- Lodging data --------------------------------
    lodging = sqlite3.connect(LODGING_DB)
    master.executemany(
        "INSERT INTO lodging_schools (school_id, name) VALUES (?, ?)",
        fetch_all(lodging, "SELECT school_id, name FROM schools"),
    )
    master.executemany(
        "INSERT INTO lodging_clubs (club_id, school_id, name) VALUES (?, ?, ?)",
        fetch_all(lodging, "SELECT club_id, school_id, name FROM clubs"),
    )
    master.executemany(
        """
        INSERT INTO lodging_teams (team_id, club_id, raw_label, gender, year, num_teams, headcount, room_text, division_key)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        fetch_all(
            lodging,
            "SELECT team_id, club_id, raw_label, gender, year, num_teams, headcount, room_text, division_key FROM teams",
        ),
    )
    master.executemany(
        "INSERT INTO lodging_rooms (room_id, school_id, room_code) VALUES (?, ?, ?)",
        fetch_all(lodging, "SELECT room_id, school_id, room_code FROM rooms"),
    )
    master.executemany(
        "INSERT INTO lodging_team_rooms (team_id, room_id) VALUES (?, ?)",
        fetch_all(lodging, "SELECT team_id, room_id FROM team_rooms"),
    )
    master.executemany(
        "INSERT INTO lodging_team_squads (squad_id, team_id, squad_index) VALUES (?, ?, ?)",
        fetch_all(lodging, "SELECT squad_id, team_id, squad_index FROM team_squads"),
    )
    lodging.close()

    # ------------------------- Tournament data -----------------------------
    tournament = sqlite3.connect(TOURNAMENT_DB)
    master.executemany(
        "INSERT INTO schedule_halls (hall_id, name) VALUES (?, ?)",
        fetch_all(tournament, "SELECT hall_id, name FROM halls"),
    )
    master.executemany(
        "INSERT INTO schedule_event_days (day_id, date, label) VALUES (?, ?, ?)",
        fetch_all(tournament, "SELECT day_id, date, label FROM event_days"),
    )
    master.executemany(
        "INSERT INTO schedule_tournaments (tournament_id, name, gender, age, birth_year, pool_code) VALUES (?, ?, ?, ?, ?, ?)",
        fetch_all(tournament, "SELECT tournament_id, name, gender, age, birth_year, pool_code FROM tournaments"),
    )
    master.executemany(
        "INSERT INTO schedule_teams (team_id, name) VALUES (?, ?)",
        fetch_all(tournament, "SELECT team_id, name FROM teams"),
    )
    master.executemany(
        """
        INSERT INTO schedule_games (game_id, tournament_id, hall_id, day_id, match_code, start_time, home_team_id, away_team_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        fetch_all(
            tournament,
            "SELECT game_id, tournament_id, hall_id, day_id, match_code, start_time, home_team_id, away_team_id FROM games",
        ),
    )
    tournament.close()

    # ------------------------- Stop cross-links ----------------------------
    school_name_to_id = {
        name: school_id
        for school_id, name in master.execute("SELECT school_id, name FROM lodging_schools")
    }
    hall_name_to_id = {
        name: hall_id
        for hall_id, name in master.execute("SELECT hall_id, name FROM schedule_halls")
    }

    stop_links: Dict[int, Tuple[Optional[int], Optional[int]]] = {}
    school_map = {
        "Elverum ungdomsskole (EUS)": "ELVERUM UNGDOMSSKOLE",
        "Elverum videregående skole (ELVIS)": "ELVIS",
        "Frydenlund": "FRYDENLUND",
        "Ydalir": "YDALIR",
    }
    # Map stop names to hall names (including sub-halls)
    hall_map = {
        "Elverum ungdomsskole (EUS)": ["Elverumshallen", "Elverumshallen - Kortbane", "Elverumshallen - Mini 1", "Elverumshallen - Mini 2"],
        "Elverum videregående skole (ELVIS)": ["Elvishallen"],
        "Terningen Arena": ["Terningen Arena"],
        "Herneshallen": ["Herneshallen", "Herneshallen - Kortbane", "Herneshallen - mini 1", "Herneshallen - mini 2"],
        "Søndre Elverum": ["Søndre Elverum Idrettshall", "Søndre Elverum Idrettshall - Kortbane"],
        "Ydalir": ["Ydalir skole idrettshall", "Ydalir skole idrettshall - Kortbane"],
    }

    for stop_id, stop_name in master.execute("SELECT stop_id, stop_name FROM transport_stops"):
        school_id = None
        school_key = school_map.get(stop_name)
        if school_key:
            school_id = school_name_to_id.get(school_key)

        # Get all hall names for this stop (can be multiple)
        hall_names = hall_map.get(stop_name, [])
        if not hall_names:
            # Insert one row with NULL hall_id for school-only stops
            master.execute(
                "INSERT INTO transport_stop_links (stop_id, lodging_school_id, schedule_hall_id) VALUES (?, ?, ?)",
                (stop_id, school_id, None),
            )
        else:
            # Insert one row per hall linked to this stop
            for hall_name in hall_names:
                hall_id = hall_name_to_id.get(hall_name)
                if hall_id is not None:
                    master.execute(
                        "INSERT INTO transport_stop_links (stop_id, lodging_school_id, schedule_hall_id) VALUES (?, ?, ?)",
                        (stop_id, school_id, hall_id),
                    )

    stop_lookup = {
        name: stop_id for stop_id, name in master.execute("SELECT stop_id, stop_name FROM transport_stops")
    }

    def require_stop_id(stop_name: str) -> int:
        try:
            return stop_lookup[stop_name]
        except KeyError as exc:
            raise KeyError(f"Missing stop '{stop_name}' required for logistics events") from exc

    logistics_events = [
        (
            None,
            "Lørdagslunch Thon Central",
            "lunch",
            "sat",
            "13:00",
            "17:30",
            require_stop_id("Thon Central (lørdag)"),
            "Lunch window Saturday 13:00–17:30 at Thon Central",
        ),
        (
            None,
            "Konsert Terningen Arena",
            "concert",
            "sat",
            "19:30",
            "21:00",
            require_stop_id("Terningen Arena"),
            "Concert Saturday 19:30–21:00 at Terningen Arena",
        ),
    ]

    master.executemany(
        """
        INSERT INTO logistics_events (event_id, name, event_type, service_day, start_time, end_time, anchor_stop_id, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        logistics_events,
    )


    master.commit()

    master.executescript(
        """
        DROP VIEW IF EXISTS vw_manual_transport_needs;
        DROP VIEW IF EXISTS vw_team_itinerary_flat;
        DROP VIEW IF EXISTS vw_bus_load_summary;
        DROP VIEW IF EXISTS vw_game_transport_candidates;
        DROP VIEW IF EXISTS vw_transport_trip_instances;
        DROP VIEW IF EXISTS vw_team_game_sequence;
        DROP VIEW IF EXISTS vw_team_daily_summary;
        DROP VIEW IF EXISTS vw_team_games;
        DROP VIEW IF EXISTS vw_logistics_events;
        DROP VIEW IF EXISTS vw_team_alignment;

        CREATE VIEW vw_team_alignment AS
        SELECT
            ta.alias_id,
            ta.squad_index,
            lt.team_id AS lodging_team_id,
            lc.name AS lodging_club,
            lt.raw_label,
            lt.division_key,
            lt.headcount,
            ls.school_id,
            ls.name AS school_name,
            GROUP_CONCAT(DISTINCT lr.room_code ORDER BY lr.room_code) AS room_codes,
            st.team_id AS schedule_team_id,
            st.name AS schedule_team_name
        FROM team_aliases ta
        JOIN lodging_teams lt ON lt.team_id = ta.lodging_team_id
        JOIN lodging_clubs lc ON lc.club_id = lt.club_id
        JOIN lodging_schools ls ON ls.school_id = lc.school_id
        LEFT JOIN lodging_team_rooms ltr ON ltr.team_id = lt.team_id
        LEFT JOIN lodging_rooms lr ON lr.room_id = ltr.room_id
        LEFT JOIN schedule_teams st ON st.team_id = ta.schedule_team_id
        GROUP BY ta.alias_id;

        CREATE VIEW vw_team_games AS
        SELECT
            ta.alias_id,
            ta.squad_index,
            lt.team_id AS lodging_team_id,
            st.team_id AS schedule_team_id,
            g.game_id,
            d.date,
            d.label AS day_label,
            g.start_time,
            h.name AS hall_name,
            t.name AS tournament_name,
            CASE WHEN g.home_team_id = st.team_id THEN 'home' ELSE 'away' END AS role,
            opp.name AS opponent_name,
            g.match_code,
            h.hall_id,
            d.day_id,
            t.tournament_id,
            CASE CAST(strftime('%w', d.date) AS INTEGER)
                WHEN 5 THEN 'fri'
                WHEN 6 THEN 'sat'
                WHEN 0 THEN 'sun'
                ELSE NULL
            END AS service_day_code
        FROM team_aliases ta
        JOIN lodging_teams lt ON lt.team_id = ta.lodging_team_id
        JOIN schedule_teams st ON st.team_id = ta.schedule_team_id
        JOIN schedule_games g ON g.home_team_id = st.team_id OR g.away_team_id = st.team_id
        JOIN schedule_event_days d ON d.day_id = g.day_id
        JOIN schedule_halls h ON h.hall_id = g.hall_id
        JOIN schedule_tournaments t ON t.tournament_id = g.tournament_id
        JOIN schedule_teams opp ON opp.team_id = CASE WHEN g.home_team_id = st.team_id THEN g.away_team_id ELSE g.home_team_id END;

        CREATE VIEW vw_team_game_sequence AS
        WITH ordered AS (
            SELECT
                g.*,
                ROW_NUMBER() OVER (
                    PARTITION BY g.alias_id
                    ORDER BY g.date, g.start_time, g.game_id
                ) AS game_sequence,
                LAG(g.start_time) OVER (
                    PARTITION BY g.alias_id
                    ORDER BY g.date, g.start_time, g.game_id
                ) AS prev_start_time,
                LAG(g.date) OVER (
                    PARTITION BY g.alias_id
                    ORDER BY g.date, g.start_time, g.game_id
                ) AS prev_date,
                LEAD(g.start_time) OVER (
                    PARTITION BY g.alias_id
                    ORDER BY g.date, g.start_time, g.game_id
                ) AS next_start_time,
                LEAD(g.date) OVER (
                    PARTITION BY g.alias_id
                    ORDER BY g.date, g.start_time, g.game_id
                ) AS next_date
            FROM vw_team_games g
        )
        SELECT
            ordered.alias_id,
            ordered.squad_index,
            ordered.lodging_team_id,
            ordered.schedule_team_id,
            ordered.game_id,
            ordered.date,
            ordered.day_label,
            ordered.start_time,
            ordered.hall_name,
            ordered.tournament_name,
            ordered.role,
            ordered.opponent_name,
            ordered.match_code,
            ordered.hall_id,
            ordered.day_id,
            ordered.tournament_id,
            ordered.service_day_code,
            ordered.game_sequence,
            ordered.prev_date,
            ordered.prev_start_time,
            ordered.next_date,
            ordered.next_start_time,
            CASE
                WHEN prev_date = date THEN
                    ((CAST(substr(start_time, 1, 2) AS INTEGER) * 60 + CAST(substr(start_time, 4, 2) AS INTEGER))
                    - (CAST(substr(prev_start_time, 1, 2) AS INTEGER) * 60 + CAST(substr(prev_start_time, 4, 2) AS INTEGER)))
                ELSE NULL
            END AS minutes_since_prev_game,
            CASE
                WHEN next_date = date THEN
                    ((CAST(substr(next_start_time, 1, 2) AS INTEGER) * 60 + CAST(substr(next_start_time, 4, 2) AS INTEGER))
                    - (CAST(substr(start_time, 1, 2) AS INTEGER) * 60 + CAST(substr(start_time, 4, 2) AS INTEGER)))
                ELSE NULL
            END AS minutes_until_next_game
        FROM ordered;

        CREATE VIEW vw_team_daily_summary AS
        SELECT
            alias_id,
            date,
            MIN(start_time) AS first_game_time,
            MAX(start_time) AS last_game_time,
            COUNT(*) AS games_count
        FROM vw_team_games
        GROUP BY alias_id, date;

        CREATE VIEW vw_logistics_events AS
        SELECT
            e.event_id,
            e.name,
            e.event_type,
            e.service_day,
            e.start_time,
            e.end_time,
            e.anchor_stop_id,
            ts.stop_name,
            ts.display_name AS stop_display_name,
            e.notes
        FROM logistics_events e
        JOIN transport_stops ts ON ts.stop_id = e.anchor_stop_id;

        CREATE VIEW vw_transport_trip_instances AS
        WITH ordered AS (
            SELECT
                route_stop_time_id,
                route_id,
                service_day,
                stop_id,
                stop_order,
                departure_time,
                condition_note,
                SUM(CASE WHEN stop_order = 1 THEN 1 ELSE 0 END) OVER (
                    PARTITION BY route_id, service_day
                    ORDER BY departure_time, stop_order, route_stop_time_id
                ) AS trip_index
            FROM transport_route_stop_times
        )
        SELECT
            route_stop_time_id,
            route_id,
            service_day,
            stop_id,
            stop_order,
            departure_time,
            condition_note,
            trip_index
        FROM ordered;

        CREATE VIEW vw_game_transport_candidates AS
        WITH game_context AS (
            SELECT
                g.alias_id,
                g.squad_index,
                g.lodging_team_id,
                g.schedule_team_id,
                g.game_id,
                g.date,
                g.day_label,
                g.start_time,
                g.service_day_code,
                g.hall_id,
                g.hall_name,
                g.tournament_name,
                g.match_code,
                ta.lodging_club,
                ta.school_id,
                ta.school_name,
                ta.room_codes,
                ta.headcount
            FROM vw_team_games g
            JOIN vw_team_alignment ta ON ta.alias_id = g.alias_id
            WHERE g.service_day_code IS NOT NULL
        ),
        candidate AS (
            SELECT
                ctx.alias_id,
                ctx.squad_index,
                ctx.lodging_team_id,
                ctx.schedule_team_id,
                ctx.game_id,
                ctx.date,
                ctx.day_label,
                ctx.start_time,
                ctx.service_day_code AS service_day,
                ctx.hall_id,
                ctx.hall_name,
                ctx.tournament_name,
                ctx.match_code,
                ctx.lodging_club,
                ctx.school_id,
                ctx.school_name,
                ctx.room_codes,
                ctx.headcount,
                dep.route_id,
                tr.route_number,
                tr.title AS route_title,
                dep.trip_index,
                dep.route_stop_time_id AS departure_route_stop_time_id,
                dep.stop_id AS departure_stop_id,
                dep_stops.stop_name AS departure_stop_name,
                dep_stops.display_name AS departure_stop_display,
                dep.departure_time AS departure_time,
                dep.condition_note AS departure_condition,
                arr.route_stop_time_id AS arrival_route_stop_time_id,
                arr.stop_id AS arrival_stop_id,
                arr_stops.stop_name AS arrival_stop_name,
                arr_stops.display_name AS arrival_stop_display,
                arr.departure_time AS arrival_time,
                arr.condition_note AS arrival_condition,
                ((CAST(substr(arr.departure_time, 1, 2) AS INTEGER) * 60 + CAST(substr(arr.departure_time, 4, 2) AS INTEGER))
                  - (CAST(substr(dep.departure_time, 1, 2) AS INTEGER) * 60 + CAST(substr(dep.departure_time, 4, 2) AS INTEGER))) AS travel_minutes,
                ((CAST(substr(ctx.start_time, 1, 2) AS INTEGER) * 60 + CAST(substr(ctx.start_time, 4, 2) AS INTEGER))
                  - (CAST(substr(arr.departure_time, 1, 2) AS INTEGER) * 60 + CAST(substr(arr.departure_time, 4, 2) AS INTEGER))) AS buffer_minutes
            FROM game_context ctx
            JOIN transport_stop_links lodging_link ON lodging_link.lodging_school_id = ctx.school_id
            JOIN transport_stop_links hall_link ON hall_link.schedule_hall_id = ctx.hall_id
            JOIN vw_transport_trip_instances dep
                ON dep.stop_id = lodging_link.stop_id
               AND dep.service_day = ctx.service_day_code
            JOIN vw_transport_trip_instances arr
                ON arr.route_id = dep.route_id
               AND arr.service_day = dep.service_day
               AND arr.trip_index = dep.trip_index
               AND arr.stop_id = hall_link.stop_id
            JOIN transport_routes tr ON tr.route_id = dep.route_id
            JOIN transport_stops dep_stops ON dep_stops.stop_id = dep.stop_id
            JOIN transport_stops arr_stops ON arr_stops.stop_id = arr.stop_id
            WHERE dep.stop_order < arr.stop_order
        )
        SELECT *
        FROM candidate
        WHERE buffer_minutes >= 40
          AND travel_minutes >= 0;

        CREATE VIEW vw_team_itinerary_flat AS
        WITH day_lookup AS (
            SELECT 'fri' AS service_day, date FROM schedule_event_days WHERE label LIKE 'Fredag %'
            UNION ALL
            SELECT 'sat', date FROM schedule_event_days WHERE label LIKE 'Lørdag %'
            UNION ALL
            SELECT 'sun', date FROM schedule_event_days WHERE label LIKE 'Søndag %'
        )
        SELECT
            seg.alias_id,
            ta.lodging_club,
            ta.raw_label,
            ta.schedule_team_name,
            seg.sequence_no,
            seg.segment_type,
            seg.service_day,
            dl.date AS event_date,
            seg.start_time,
            seg.end_time,
            origin.stop_name AS origin_stop_name,
            origin.display_name AS origin_stop_display,
            dest.stop_name AS destination_stop_name,
            dest.display_name AS destination_stop_display,
            seg.route_id,
            tr.route_number,
            seg.trip_index,
            seg.travel_minutes,
            seg.buffer_minutes,
            seg.notes
        FROM team_itinerary_segments seg
        JOIN vw_team_alignment ta ON ta.alias_id = seg.alias_id
        LEFT JOIN day_lookup dl ON dl.service_day = seg.service_day
        LEFT JOIN transport_stops origin ON origin.stop_id = seg.origin_stop_id
        LEFT JOIN transport_stops dest ON dest.stop_id = seg.destination_stop_id
        LEFT JOIN transport_routes tr ON tr.route_id = seg.route_id;

        CREATE VIEW vw_manual_transport_needs AS
        WITH day_lookup AS (
            SELECT 'fri' AS service_day, date FROM schedule_event_days WHERE label LIKE 'Fredag %'
            UNION ALL
            SELECT 'sat', date FROM schedule_event_days WHERE label LIKE 'Lørdag %'
            UNION ALL
            SELECT 'sun', date FROM schedule_event_days WHERE label LIKE 'Søndag %'
        )
        SELECT
            seg.alias_id,
            ta.lodging_club,
            ta.raw_label,
            ta.schedule_team_name,
            seg.service_day,
            dl.date AS event_date,
            seg.start_time,
            seg.end_time,
            origin.stop_name AS origin_stop_name,
            dest.stop_name AS destination_stop_name,
            seg.notes
        FROM team_itinerary_segments seg
        JOIN vw_team_alignment ta ON ta.alias_id = seg.alias_id
        LEFT JOIN day_lookup dl ON dl.service_day = seg.service_day
        LEFT JOIN transport_stops origin ON origin.stop_id = seg.origin_stop_id
        LEFT JOIN transport_stops dest ON dest.stop_id = seg.destination_stop_id
        WHERE seg.segment_type = 'note'
           OR (seg.segment_type = 'bus' AND seg.route_id IS NULL);

        CREATE VIEW vw_bus_load_summary AS
        SELECT
            seg.route_id,
            seg.trip_index,
            seg.service_day,
            seg.start_time AS departure_time,
            tr.route_number,
            COUNT(seg.segment_id) AS segment_count,
            COALESCE(SUM(al.headcount), 0) AS estimated_headcount
        FROM team_itinerary_segments seg
        JOIN transport_routes tr ON tr.route_id = seg.route_id
        JOIN vw_team_alignment al ON al.alias_id = seg.alias_id
        WHERE seg.segment_type = 'bus'
          AND seg.route_id IS NOT NULL
        GROUP BY seg.route_id, seg.trip_index, seg.service_day, seg.start_time, tr.route_number
        ORDER BY seg.service_day, seg.route_id, seg.start_time;

        CREATE VIEW vw_bus_capacity_alerts AS
        SELECT *
        FROM vw_bus_load_summary
        WHERE estimated_headcount > 100
        ORDER BY estimated_headcount DESC;
        """
    )

    with TARGET_SQL.open("w", encoding="utf-8") as dump:
        for line in master.iterdump():
            dump.write(f"{line}\n")

    master.close()


def main() -> None:
    copy_domain_data()
    print(f"Created {TARGET_DB}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
ETL pipeline for the tournament schedule in
`Kampoppsett EYC 25 - 27 april 2025 (1).xlsx`.

Outputs:
    data/build/tournament.db
    data/build/tournament.sql
"""

from __future__ import annotations

import re
import sqlite3
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent
XLSX_PATH = ROOT / "Kampoppsett EYC 25 - 27 april 2025 (1).xlsx"
DB_PATH = ROOT / "data" / "build" / "tournament.db"
SQL_DUMP_PATH = ROOT / "data" / "build" / "tournament.sql"

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

BIRTH_YEAR_BASE = 2024


def read_sheet() -> List[List[str]]:
    if not XLSX_PATH.exists():
        raise FileNotFoundError(f"Missing source spreadsheet: {XLSX_PATH}")

    with ZipFile(XLSX_PATH) as zf:
        shared_strings: List[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            shared_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in shared_root.findall(".//a:si", NS):
                text = "".join(t.text or "" for t in si.findall(".//a:t", NS))
                shared_strings.append(text)

        sheet_root = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))

    rows: List[List[str]] = []
    for row in sheet_root.findall(".//a:row", NS):
        row_cells: Dict[str, str] = {}
        for cell in row.findall("a:c", NS):
            ref = cell.attrib.get("r", "")
            match = re.match(r"([A-Z]+)(\d+)", ref)
            if not match:
                continue
            col = match.group(1)
            cell_type = cell.attrib.get("t")
            text = ""
            value = cell.find("a:v", NS)
            if value is not None:
                if cell_type == "s":
                    idx = int(value.text)
                    text = shared_strings[idx] if idx < len(shared_strings) else ""
                else:
                    text = value.text or ""
            else:
                inline = cell.find("a:is", NS)
                if inline is not None:
                    text = "".join(t.text or "" for t in inline.findall(".//a:t", NS))
            row_cells[col] = text

        # Determine number of columns (A-F expected).
        max_col = 6
        current_row: List[str] = []
        for offset in range(max_col):
            col_letter = chr(ord("A") + offset)
            current_row.append(row_cells.get(col_letter, ""))  # default empty string
        rows.append([cell.strip() for cell in current_row])

    return rows


DAY_NAMES = {
    "mandag": 0,
    "tirsdag": 1,
    "onsdag": 2,
    "torsdag": 3,
    "fredag": 4,
    "lørdag": 5,
    "søndag": 6,
}


def parse_event_day(label: str) -> Tuple[str, str]:
    """Return ISO date and canonical label from strings like 'Fredag 25.04.25'."""
    parts = label.strip().split()
    if len(parts) < 2:
        raise ValueError(f"Unable to parse event day from '{label}'")
    day_label = parts[0]
    date_part = parts[1]
    date = datetime.strptime(date_part, "%d.%m.%y").date()
    return date.isoformat(), f"{day_label} {date_part}"


def convert_time(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Empty time value")
    try:
        # Excel stores times as fractions of a day.
        number = float(value.replace(",", "."))
        minutes = int(round(number * 24 * 60))
        minutes %= 24 * 60
        hours, minute = divmod(minutes, 60)
        return f"{hours:02d}:{minute:02d}"
    except ValueError:
        if ":" in value:
            hours, minute = value.split(":", 1)
            return f"{int(hours):02d}:{int(minute):02d}"
        raise


def parse_schedule(rows: List[List[str]]) -> List[Dict[str, str]]:
    games: List[Dict[str, str]] = []
    current_hall: Optional[str] = None
    current_day_label: Optional[str] = None
    current_day_iso: Optional[str] = None

    for row in rows:
        if not any(row):
            continue
        first_cell = row[0].strip()
        if first_cell.lower() == "tid":
            continue

        lower = first_cell.lower()
        if lower.startswith(("fredag", "lørdag", "søndag")):
            current_day_iso, current_day_label = parse_event_day(first_cell)
            continue

        if first_cell and not any(cell.strip() for cell in row[1:]):
            # Hall heading
            current_hall = first_cell
            continue

        if not current_day_iso or not current_hall:
            continue  # Insufficient context

        time_val = first_cell
        tournament = row[1].strip()
        match_code = row[2].strip()
        hall_name = row[3].strip() or current_hall
        home_team = row[4].strip()
        away_team = row[5].strip()

        if not tournament or not home_team or not away_team:
            continue

        try:
            time_str = convert_time(time_val)
        except ValueError:
            continue

        games.append(
            {
                "day_iso": current_day_iso,
                "day_label": current_day_label or "",
                "hall": hall_name,
                "tournament": tournament,
                "match_code": match_code,
                "time": time_str,
                "home": home_team,
                "away": away_team,
            }
        )

    return games


def parse_tournament_metadata(name: str) -> Tuple[Optional[str], Optional[int], Optional[int], Optional[str]]:
    gender: Optional[str] = None
    age: Optional[int] = None
    birth_year: Optional[int] = None
    pool: Optional[str] = None

    # Pattern: "- Jenter 12 år - 02" or "- Gutter 11 år"
    match = re.search(r"-(?:\s*)(Jenter|Gutter)\s+(\d+)\s+år(?:\s*-\s*(\w+))?", name, re.IGNORECASE)
    if match:
        gender = "J" if match.group(1).lower().startswith("j") else "G"
        age = int(match.group(2))
        if match.group(3):
            pool = match.group(3)
    else:
        # Sluttspill names like "Elverum Yngres Cup J13 A-sluttspill"
        match = re.search(r"(J|G)(\d{2})", name)
        if match:
            gender = "J" if match.group(1).lower() == "j" else "G"
            age = int(match.group(2))
        # Generic "Jenter 13" without hyphen
        if age is None:
            match = re.search(r"(Jenter|Gutter)\s+(\d+)\s*år", name, re.IGNORECASE)
            if match:
                gender = "J" if match.group(1).lower().startswith("j") else "G"
                age = int(match.group(2))

    if "sluttspill" in name.lower() and pool is None:
        pool_match = re.search(r"(\b[A-Z])[- ]sluttspill", name, re.IGNORECASE)
        if pool_match:
            pool = pool_match.group(1).upper()
        else:
            pool = "sluttspill"

    if age is not None:
        birth_year = BIRTH_YEAR_BASE - age

    return gender, age, birth_year, pool


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS halls (
    hall_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS event_days (
    day_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tournaments (
    tournament_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    gender TEXT,
    age INTEGER,
    birth_year INTEGER,
    pool_code TEXT
);

CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS games (
    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL,
    hall_id INTEGER NOT NULL,
    day_id INTEGER NOT NULL,
    match_code TEXT,
    start_time TEXT NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    FOREIGN KEY (tournament_id) REFERENCES tournaments(tournament_id),
    FOREIGN KEY (hall_id) REFERENCES halls(hall_id),
    FOREIGN KEY (day_id) REFERENCES event_days(day_id),
    FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES teams(team_id)
);

CREATE INDEX IF NOT EXISTS idx_games_lookup
    ON games(day_id, hall_id, start_time);
"""


def build_database(games: List[Dict[str, str]]) -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL)

    hall_ids: Dict[str, int] = {}
    day_ids: Dict[str, int] = {}
    tournament_ids: Dict[str, int] = {}
    team_ids: Dict[str, int] = {}

    for game in games:
        hall = game["hall"]
        if hall not in hall_ids:
            conn.execute("INSERT INTO halls (name) VALUES (?)", (hall,))
            hall_ids[hall] = conn.execute(
                "SELECT hall_id FROM halls WHERE name = ?", (hall,)
            ).fetchone()[0]

        day_iso = game["day_iso"]
        if day_iso not in day_ids:
            conn.execute(
                "INSERT INTO event_days (date, label) VALUES (?, ?)",
                (day_iso, game["day_label"]),
            )
            day_ids[day_iso] = conn.execute(
                "SELECT day_id FROM event_days WHERE date = ?", (day_iso,)
            ).fetchone()[0]

        tournament = game["tournament"]
        if tournament not in tournament_ids:
            gender, age, birth_year, pool = parse_tournament_metadata(tournament)
            conn.execute(
                "INSERT INTO tournaments (name, gender, age, birth_year, pool_code) VALUES (?, ?, ?, ?, ?)",
                (tournament, gender, age, birth_year, pool),
            )
            tournament_ids[tournament] = conn.execute(
                "SELECT tournament_id FROM tournaments WHERE name = ?",
                (tournament,),
            ).fetchone()[0]

        for key in ("home", "away"):
            team_name = game[key]
            if team_name not in team_ids:
                conn.execute("INSERT INTO teams (name) VALUES (?)", (team_name,))
                team_ids[team_name] = conn.execute(
                    "SELECT team_id FROM teams WHERE name = ?", (team_name,)
                ).fetchone()[0]

        conn.execute(
            """
            INSERT INTO games (
                tournament_id, hall_id, day_id, match_code,
                start_time, home_team_id, away_team_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tournament_ids[tournament],
                hall_ids[hall],
                day_ids[day_iso],
                game["match_code"] or None,
                game["time"],
                team_ids[game["home"]],
                team_ids[game["away"]],
            ),
        )

    conn.commit()

    with SQL_DUMP_PATH.open("w", encoding="utf-8") as dump:
        for line in conn.iterdump():
            dump.write(f"{line}\n")

    conn.close()


def main() -> None:
    rows = read_sheet()
    games = parse_schedule(rows)
    build_database(games)
    print(f"Created {DB_PATH} with {len(games)} games.")


if __name__ == "__main__":
    main()

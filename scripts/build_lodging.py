#!/usr/bin/env python3
"""
ETL pipeline for lodging allocations extracted from `Overnatningsoversigt (1).docx`.

Outputs:
    data/build/lodging.db  – normalized SQLite database
    data/build/lodging.sql – SQL dump for auditability

Schema:
    schools(school_id, name)
    clubs(club_id, school_id, name)
    teams(team_id, club_id, raw_label, gender, year, num_teams, headcount, room_text)
    rooms(room_id, school_id, room_code)
    team_rooms(team_id, room_id)
"""

from __future__ import annotations

import re
import sqlite3
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent
DOCX_PATH = ROOT / "Overnatningsoversigt (1).docx"
DB_PATH = ROOT / "data" / "build" / "lodging.db"
SQL_DUMP_PATH = ROOT / "data" / "build" / "lodging.sql"

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def normalise_text(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value.strip())
    return value


def iter_body_blocks(root: ET.Element):
    body = root.find("w:body", NS)
    if body is None:
        return
    for child in body:
        yield child


def paragraph_text(para: ET.Element) -> str:
    return normalise_text("".join(t.text or "" for t in para.findall(".//w:t", NS)))


def table_rows(table: ET.Element) -> List[List[str]]:
    rows: List[List[str]] = []
    for row in table.findall("w:tr", NS):
        cells = []
        for cell in row.findall("w:tc", NS):
            text = normalise_text("".join(t.text or "" for t in cell.findall(".//w:t", NS)))
            cells.append(text)
        rows.append(cells)
    return rows


def parse_school_tables() -> Dict[str, List[List[List[str]]]]:
    if not DOCX_PATH.exists():
        raise FileNotFoundError(f"Missing source document: {DOCX_PATH}")
    with ZipFile(DOCX_PATH) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)

    school_tables: Dict[str, List[List[List[str]]]] = defaultdict(list)
    current_school: Optional[str] = None

    for block in iter_body_blocks(root):
        if block.tag.endswith("}p"):
            text = paragraph_text(block)
            if not text:
                continue
            if text.lower().startswith("hvem bor"):
                continue
            current_school = text.rstrip(":")
        elif block.tag.endswith("}tbl"):
            if not current_school:
                continue
            if current_school.lower().startswith("skolefordeling"):
                continue
            rows = table_rows(block)
            school_tables[current_school].append(rows)
    return school_tables


TEAM_LABEL_SPLIT = re.compile(r"(\d[\d\s]*)")
NUM_TEAMS_PATTERN = re.compile(r"(\d+)\s*lag", re.IGNORECASE)
GENDER_YEAR_PATTERN = re.compile(r"([JG])(\d{4})")


def parse_team_rows(rows: List[List[str]]) -> List[Dict[str, Optional[str]]]:
    teams: List[Dict[str, Optional[str]]] = []
    current_club: Optional[str] = None
    last_team: Optional[Dict[str, Optional[str]]] = None

    for row in rows[1:]:  # skip header
        if not row:
            continue
        # Ensure row has at least four columns for consistent indexing.
        while len(row) < 4:
            row.append("")

        name = normalise_text(row[0])
        rest = " ".join(normalise_text(c) for c in row[1:] if normalise_text(c))

        if not name and rest and last_team:
            # Continuation of room text on a blank row.
            combined = f"{last_team['room_raw']} {rest}".strip()
            last_team["room_raw"] = combined
            continue

        if not name:
            continue

        lower = name.lower()
        if lower.startswith(("sum", "disp")):
            break
        if lower == "klubb/lag":
            continue
        if "grupperom" in lower:
            continue

        if not rest:
            current_club = name
            continue

        count = None
        room_text = normalise_text(row[-1]) if row else rest

        count_cell = normalise_text(row[2]) if len(row) > 2 else ""
        if count_cell:
            digits = re.sub(r"\s+", "", count_cell)
            if digits.isdigit():
                count = int(digits)

        # Fallback: attempt to parse count embedded in name.
        if count is None:
            match = TEAM_LABEL_SPLIT.search(name)
            if match:
                numeric = re.sub(r"\s+", "", match.group(1))
                if numeric.isdigit():
                    count = int(numeric)
                    name = (name[: match.start()] + name[match.end() :]).strip(", ")

        if count is None:
            # Skip malformed rows that do not contain counts.
            continue

        clean_label = re.sub(r"\s+", " ", name).strip()
        clean_label = re.sub(r"(?<=\D)\s+(?=\d)", "", clean_label)
        clean_label = re.sub(r"(?<=\d)\s+(?=\d)", "", clean_label)
        team_record = {
            "club": current_club,
            "team_label": clean_label,
            "headcount": count,
            "room_raw": room_text or "",
        }
        teams.append(team_record)
        last_team = team_record

    return teams


def parse_all_allocations() -> Dict[str, List[Dict[str, Optional[str]]]]:
    school_tables = parse_school_tables()
    allocations: Dict[str, List[Dict[str, Optional[str]]]] = defaultdict(list)
    for school, tables in school_tables.items():
        for table in tables:
            team_rows = parse_team_rows(table)
            if team_rows:
                allocations[school].extend(team_rows)
    return allocations


def parse_gender_year(label: str) -> Tuple[Optional[str], Optional[int]]:
    cleaned = label.replace(" ", "")
    match = GENDER_YEAR_PATTERN.search(cleaned)
    if match:
        gender = match.group(1)
        year = int(match.group(2))
        return gender, year
    return None, None


def parse_num_teams(label: str) -> int:
    cleaned = label.replace(",", " ")
    matches = re.findall(r"(?:(?<=\s)|^)(\d+)\s*lag", cleaned)
    if matches:
        try:
            return int(matches[-1])
        except ValueError:
            return 1
    return 1


ROOM_SPLIT = re.compile(r"[,+]")


def normalise_room_code(code: str) -> str:
    code = normalise_text(code)
    if not code:
        return ""
    if re.search(r"[0-9]", code):
        code = code.replace(" ", "")
    return code


def expand_room_codes(raw: str) -> List[str]:
    if not raw:
        return []
    tokens = []
    for part in ROOM_SPLIT.split(raw):
        token = normalise_room_code(part)
        if token:
            tokens.append(token)
    return tokens or []


def build_division_key(gender: Optional[str], year: Optional[int]) -> Optional[str]:
    if gender and year:
        return f"{gender.upper()}{year}"
    return None


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schools (
    school_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS clubs (
    club_id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    UNIQUE (school_id, name),
    FOREIGN KEY (school_id) REFERENCES schools(school_id)
);

CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL,
    raw_label TEXT NOT NULL,
    gender TEXT,
    year INTEGER,
    num_teams INTEGER,
    headcount INTEGER,
    room_text TEXT,
    division_key TEXT,
    FOREIGN KEY (club_id) REFERENCES clubs(club_id)
);

CREATE TABLE IF NOT EXISTS rooms (
    room_id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER NOT NULL,
    room_code TEXT NOT NULL,
    UNIQUE (school_id, room_code),
    FOREIGN KEY (school_id) REFERENCES schools(school_id)
);

CREATE TABLE IF NOT EXISTS team_rooms (
    team_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    PRIMARY KEY (team_id, room_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);

CREATE TABLE IF NOT EXISTS team_squads (
    squad_id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    squad_index INTEGER NOT NULL,
    UNIQUE (team_id, squad_index),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);
"""


def build_database(allocations: Dict[str, List[Dict[str, Optional[str]]]]) -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL)

    school_ids: Dict[str, int] = {}
    club_ids: Dict[Tuple[int, str], int] = {}
    room_ids: Dict[Tuple[int, str], int] = {}

    for school_name in sorted(allocations.keys()):
        conn.execute("INSERT INTO schools (name) VALUES (?)", (school_name,))
        school_ids[school_name] = conn.execute(
            "SELECT school_id FROM schools WHERE name = ?", (school_name,)
        ).fetchone()[0]

    for school_name, entries in allocations.items():
        school_id = school_ids[school_name]
        for entry in entries:
            club_name = entry["club"] or "Ukjent klubb"
            key = (school_id, club_name)
            if key not in club_ids:
                conn.execute(
                    "INSERT INTO clubs (school_id, name) VALUES (?, ?)",
                    (school_id, club_name),
                )
                club_ids[key] = conn.execute(
                    "SELECT club_id FROM clubs WHERE school_id = ? AND name = ?",
                    (school_id, club_name),
                ).fetchone()[0]
            club_id = club_ids[key]

            raw_label = entry["team_label"] or "Ukjent lag"
            gender, year = parse_gender_year(raw_label)
            num_teams = parse_num_teams(raw_label)
            headcount = entry["headcount"]
            room_text = entry["room_raw"]
            division_key = build_division_key(gender, year)

            conn.execute(
                """
                INSERT INTO teams (club_id, raw_label, gender, year, num_teams, headcount, room_text, division_key)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (club_id, raw_label, gender, year, num_teams, headcount, room_text, division_key),
            )
            team_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            for room_code in expand_room_codes(room_text):
                key = (school_id, room_code)
                if key not in room_ids:
                    conn.execute(
                        "INSERT INTO rooms (school_id, room_code) VALUES (?, ?)",
                        (school_id, room_code),
                    )
                    room_ids[key] = conn.execute(
                        "SELECT room_id FROM rooms WHERE school_id = ? AND room_code = ?",
                        (school_id, room_code),
                    ).fetchone()[0]
                conn.execute(
                    "INSERT OR IGNORE INTO team_rooms (team_id, room_id) VALUES (?, ?)",
                    (team_id, room_ids[key]),
                )

            squad_total = max(1, num_teams or 1)
            for index in range(1, squad_total + 1):
                conn.execute(
                    "INSERT INTO team_squads (team_id, squad_index) VALUES (?, ?)",
                    (team_id, index),
                )

    conn.commit()

    with SQL_DUMP_PATH.open("w", encoding="utf-8") as dump:
        for line in conn.iterdump():
            dump.write(f"{line}\n")

    conn.close()


def main() -> None:
    allocations = parse_all_allocations()
    build_database(allocations)
    print(f"Created {DB_PATH} with {sum(len(v) for v in allocations.values())} team rows.")


if __name__ == "__main__":
    main()

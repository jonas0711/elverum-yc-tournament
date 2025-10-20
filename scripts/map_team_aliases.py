#!/usr/bin/env python3
"""
Populate the team_aliases table by matching lodging squads to tournament teams.

Heuristics:
- Match on division key (gender + birth year) derived from tournament metadata.
- Require the lodging club slug to be present in the schedule team name variants.
- Allocate multiple squads per club (team_squads) to distinct schedule teams when available.
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "build" / "event_planner.db"

GENERIC_WORDS = {
    "il",
    "hk",
    "if",
    "fk",
    "sk",
    "hl",
    "klubb",
    "handballklubb",
    "håndballklubb",
    "handball",
    "haandballklubb",
}

CUSTOM_SLUGS = {
    "Aurskog Finstadbru": {"afsk"},
}


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", normalized.lower())


def schedule_variants(name: str) -> Set[str]:
    variants: Set[str] = set()
    variants.add(slugify(name))
    name_no_digits = re.sub(r"\b\d+\b", "", name)
    variants.add(slugify(name_no_digits))
    for part in re.split(r"[/-]", name):
        variants.add(slugify(part))
    for token in name.split():
        variants.add(slugify(token))
    return {v for v in variants if v}


def club_slugs(name: str) -> Set[str]:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    words = [w for w in re.split(r"[^a-z0-9]+", ascii_name) if w]
    slugs: Set[str] = set()
    if words:
        slugs.add(slugify("".join(words)))
        filtered = [w for w in words if w not in GENERIC_WORDS]
        if filtered:
            slugs.add(slugify("".join(filtered)))
        for word in filtered:
            slugs.add(slugify(word))
    slugs.update(CUSTOM_SLUGS.get(name, set()))
    return {slug for slug in slugs if slug}


@dataclass
class ScheduleTeam:
    team_id: int
    name: str
    division_keys: Set[str]
    slug_variants: Set[str]


@dataclass
class LodgingTeam:
    team_id: int
    club_name: str
    raw_label: str
    division_key: Optional[str]
    squad_count: int


def load_schedule_teams(conn: sqlite3.Connection) -> Dict[int, ScheduleTeam]:
    query = """
    WITH team_games AS (
        SELECT tournament_id, home_team_id AS team_id FROM schedule_games
        UNION ALL
        SELECT tournament_id, away_team_id AS team_id FROM schedule_games
    )
    SELECT st.team_id,
           st.name,
           GROUP_CONCAT(DISTINCT CASE
               WHEN t.gender IS NOT NULL AND t.birth_year IS NOT NULL
               THEN t.gender || printf('%04d', t.birth_year)
           END) AS division_keys
    FROM schedule_teams st
    LEFT JOIN team_games tg ON tg.team_id = st.team_id
    LEFT JOIN schedule_tournaments t ON tg.tournament_id = t.tournament_id
    GROUP BY st.team_id, st.name
    """
    schedule: Dict[int, ScheduleTeam] = {}
    for team_id, name, division_str in conn.execute(query):
        keys: Set[str] = set()
        if division_str:
            for key in division_str.split(","):
                key = (key or "").strip()
                if key:
                    keys.add(key)
        schedule[team_id] = ScheduleTeam(
            team_id=team_id,
            name=name,
            division_keys=keys,
            slug_variants=schedule_variants(name),
        )
    return schedule


def load_lodging_teams(conn: sqlite3.Connection) -> List[LodgingTeam]:
    query = """
    SELECT lt.team_id,
           lc.name AS club_name,
           lt.raw_label,
           lt.division_key,
           COALESCE(MAX(ls.squad_index), CASE
               WHEN lt.num_teams IS NOT NULL AND lt.num_teams > 0 THEN lt.num_teams
               ELSE 1 END, 1) AS squad_count
    FROM lodging_teams lt
    JOIN lodging_clubs lc ON lt.club_id = lc.club_id
    LEFT JOIN lodging_team_squads ls ON lt.team_id = ls.team_id
    GROUP BY lt.team_id, lc.name, lt.raw_label, lt.division_key, lt.num_teams
    ORDER BY lc.name, lt.division_key, lt.raw_label
    """
    teams: List[LodgingTeam] = []
    for team_id, club_name, raw_label, division_key, squad_count in conn.execute(query):
        teams.append(
            LodgingTeam(
                team_id=team_id,
                club_name=club_name,
                raw_label=raw_label,
                division_key=division_key,
                squad_count=int(squad_count or 1),
            )
        )
    return teams


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing database: {DB_PATH}. Run build_event_db.py first.")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    schedule = load_schedule_teams(conn)
    lodging = load_lodging_teams(conn)

    conn.execute("DELETE FROM team_aliases")

    assigned_by_division: Dict[Tuple[int, str], int] = {}
    matched_count = 0
    unmatched_count = 0

    for team in lodging:
        club_slugs_set = club_slugs(team.club_name)
        primary_slug = slugify(team.club_name)
        division_key = team.division_key

        if not division_key:
            note = "unmatched: missing division key"
            for squad_index in range(1, team.squad_count + 1):
                conn.execute(
                    "INSERT INTO team_aliases (lodging_team_id, schedule_team_id, squad_index, note) VALUES (?, ?, ?, ?)",
                    (team.team_id, None, squad_index, note),
                )
                unmatched_count += 1
            continue

        candidates: List[ScheduleTeam] = []
        for sched in schedule.values():
            if division_key not in sched.division_keys:
                continue
            if any(
                any(slug in variant for slug in club_slugs_set)
                for variant in sched.slug_variants
            ):
                candidates.append(sched)

        # Remove already assigned schedule teams.
        for squad_index in range(1, team.squad_count + 1):
            scored_candidates = []
            for sched in candidates:
                assign_key = (sched.team_id, division_key)
                usage = assigned_by_division.get(assign_key, 0)
                base_score = 100 - usage * 10
                if slugify(sched.name) == primary_slug:
                    base_score += 20
                if str(squad_index) in sched.name or f"{squad_index}" in sched.slug_variants:
                    base_score += 15
                if re.search(r"lag", team.raw_label) and re.search(rf"{squad_index}\\b", sched.name):
                    base_score += 5
                scored_candidates.append((base_score, usage, sched))
            scored_candidates.sort(key=lambda item: (-item[0], item[1], item[2].name))

            if scored_candidates and scored_candidates[0][0] > 0:
                _, usage, sched = scored_candidates[0]
                assign_key = (sched.team_id, division_key)
                assigned_by_division[assign_key] = usage + 1
                note = f"auto-match division {division_key}"
                conn.execute(
                    "INSERT INTO team_aliases (lodging_team_id, schedule_team_id, squad_index, note) VALUES (?, ?, ?, ?)",
                    (team.team_id, sched.team_id, squad_index, note),
                )
                matched_count += 1
            else:
                note = f"unmatched: no schedule team for division {division_key}"
                conn.execute(
                    "INSERT INTO team_aliases (lodging_team_id, schedule_team_id, squad_index, note) VALUES (?, ?, ?, ?)",
                    (team.team_id, None, squad_index, note),
                )
                unmatched_count += 1

    conn.commit()
    conn.close()

    total = matched_count + unmatched_count
    print(f"Alias mapping complete: {matched_count} matched, {unmatched_count} unmatched (total {total}).")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Render a hyper-personalised PDF plan for a single squad alias.

Usage:
    python3 scripts/render_pdf.py --alias-id 1 --output output/itineraries

Requires `fpdf` (install via `pip install fpdf2`) for PDF rendering.
Falls back to plain text if the library is unavailable.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

try:
    from fpdf import FPDF  # type: ignore

    HAS_FPDF = True
except ImportError:  # pragma: no cover - optional dependency
    HAS_FPDF = False

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "build" / "event_planner.db"

SERVICE_DAY_LABEL = {"fri": "Fredag", "sat": "Lørdag", "sun": "Søndag"}


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Missing database: {DB_PATH}. Run build scripts first.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_alias_header(conn: sqlite3.Connection, alias_id: int) -> Dict:
    row = conn.execute(
        """
        SELECT alias_id, lodging_club, raw_label, schedule_team_name,
               school_name, room_codes, headcount
        FROM vw_team_alignment
        WHERE alias_id = ?
        """,
        (alias_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Alias {alias_id} not found")
    return dict(row)


def fetch_itinerary(conn: sqlite3.Connection, alias_id: int) -> List[Dict]:
    rows = conn.execute(
        """
        SELECT *
        FROM vw_team_itinerary_flat
        WHERE alias_id = ?
        ORDER BY service_day, sequence_no
        """,
        (alias_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_manual_segments(conn: sqlite3.Connection, alias_id: int) -> List[Dict]:
    rows = conn.execute(
        """
        SELECT *
        FROM vw_manual_transport_needs
        WHERE alias_id = ?
        ORDER BY service_day, start_time
        """,
        (alias_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_games(conn: sqlite3.Connection, alias_id: int) -> List[Dict]:
    rows = conn.execute(
        """
        SELECT date, day_label, start_time, hall_name, tournament_name,
               opponent_name, role
        FROM vw_team_games
        WHERE alias_id = ?
        ORDER BY date, start_time
        """,
        (alias_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def render_pdf(header: Dict, itinerary: List[Dict], manual: List[Dict], games: List[Dict], output_path: Path) -> None:
    if not HAS_FPDF:
        raise RuntimeError("fpdf2 is required to render PDFs. Install with `pip install fpdf2`.")

    pdf = FPDF()
    pdf.add_font("DejaVu", "", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    pdf.add_font("DejaVu", "B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    # Set margins to ensure text doesn't overflow
    pdf.set_margins(left=15, top=15, right=15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, "Elverum Yngres Cup - Holdplan")
    pdf.ln(10)

    pdf.set_font("DejaVu", "", 12)
    pdf.cell(0, 8, f"Hold: {header['schedule_team_name']} ({header['lodging_club']} - {header['raw_label']})")
    pdf.ln(8)
    pdf.cell(0, 8, f"Overnatning: {header['school_name']}  Rum: {header['room_codes']}  Deltagere: {header['headcount']}")
    pdf.ln(12)

    current_service_day: Optional[str] = None
    pdf.set_font("DejaVu", "B", 13)
    pdf.cell(0, 8, "Tidslinje")
    pdf.ln(8)
    pdf.set_font("DejaVu", "", 11)

    for item in itinerary:
        service_day = item["service_day"]
        if service_day != current_service_day:
            current_service_day = service_day
            label = SERVICE_DAY_LABEL.get(service_day, service_day.upper())
            pdf.ln(2)
            pdf.set_font("DejaVu", "B", 12)
            pdf.cell(0, 7, f"{label} ({item.get('event_date','')})")
            pdf.ln(7)
            pdf.set_font("DejaVu", "", 11)

        segment_type = item["segment_type"]
        start = item["start_time"] or "-"
        end = item["end_time"] or "-"
        origin = item.get("origin_stop_display") or item.get("origin_stop_name") or ""
        destination = item.get("destination_stop_display") or item.get("destination_stop_name") or ""
        notes = item.get("notes") or ""
        route = f" Rute {item['route_number']}" if item.get("route_number") else ""

        # Format segment nicely - use truncation to prevent overflow
        if segment_type == "bus":
            # Truncate long names
            origin_short = origin[:25] + "..." if len(origin) > 25 else origin
            dest_short = destination[:25] + "..." if len(destination) > 25 else destination
            pdf.set_font("DejaVu", "B", 10)
            pdf.cell(0, 5, f"{start}-{end}: BUS{route}")
            pdf.ln(5)
            pdf.set_font("DejaVu", "", 9)
            pdf.cell(5, 4, "")
            pdf.multi_cell(0, 4, f"Fra: {origin_short} -> Til: {dest_short}")
        elif segment_type == "game":
            pdf.set_font("DejaVu", "B", 10)
            pdf.cell(0, 5, f"{start}: KAMP")
            pdf.ln(5)
            pdf.set_font("DejaVu", "", 9)
            if notes:
                pdf.cell(5, 4, "")
                # Truncate tournament name if too long
                notes_short = notes[:70] + "..." if len(notes) > 70 else notes
                pdf.multi_cell(0, 4, notes_short)
        elif segment_type == "concert":
            pdf.set_font("DejaVu", "B", 10)
            pdf.cell(0, 5, f"{start}: KONCERT - Terningen Arena")
            pdf.ln(5)
        elif segment_type == "meal":
            pdf.set_font("DejaVu", "B", 10)
            pdf.cell(0, 5, f"{start}: LUNCH - Thon Central")
            pdf.ln(5)
        else:
            pdf.set_font("DejaVu", "", 10)
            pdf.cell(0, 5, f"{start}: {segment_type.upper()}")
            pdf.ln(5)

    if manual:
        pdf.ln(4)
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 6, "Charter / Manuelle transporter")
        pdf.ln(6)
        pdf.set_font("DejaVu", "", 9)
        for entry in manual:
            label = SERVICE_DAY_LABEL.get(entry["service_day"], entry["service_day"])
            start = entry["start_time"]
            note = entry["notes"] or ""
            origin = (entry["origin_stop_name"] or "-")[:20]
            dest = (entry["destination_stop_name"] or "-")[:20]
            pdf.cell(0, 4, f"{label} {start}: {origin} -> {dest}")
            pdf.ln(4)

    if games:
        pdf.add_page()
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 6, "Kampoversigt")
        pdf.ln(6)
        pdf.set_font("DejaVu", "", 9)
        for g in games:
            opponent = g['opponent_name'][:20]
            hall = g['hall_name'][:30] + "..." if len(g['hall_name']) > 30 else g['hall_name']
            pdf.cell(0, 4, f"{g['date']} {g['start_time']}: vs {opponent} ({g['role']})")
            pdf.ln(4)
            pdf.cell(5, 3, "")
            pdf.cell(0, 3, f"{hall}")
            pdf.ln(4)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(output_path)


def render_text(header: Dict, itinerary: List[Dict], manual: List[Dict], games: List[Dict], output_path: Path) -> None:
    lines = [
        "Elverum Yngres Cup – Holdplan",
        f"Hold: {header['schedule_team_name']} ({header['lodging_club']} – {header['raw_label']})",
        f"Overnatning: {header['school_name']}  Rum: {header['room_codes']}  Deltagere: {header['headcount']}",
        "",
        "Tidslinje:",
    ]
    current_service_day: Optional[str] = None
    for item in itinerary:
        service_day = item["service_day"]
        if service_day != current_service_day:
            current_service_day = service_day
            label = SERVICE_DAY_LABEL.get(service_day, service_day.upper())
            lines.append(f"  {label} ({item.get('event_date','')})")
        segment_type = item["segment_type"]
        start = item["start_time"] or "-"
        end = item["end_time"] or "-"
        origin = item.get("origin_stop_display") or item.get("origin_stop_name") or ""
        destination = item.get("destination_stop_display") or item.get("destination_stop_name") or ""
        notes = item.get("notes") or ""
        route = f" Rute {item['route_number']}#" if item.get("route_number") else ""
        lines.append(f"    {start}–{end} | {segment_type.upper():6} | {origin} → {destination}{route} {notes}")

    if manual:
        lines.append("")
        lines.append("Charter / manuelle transporter:")
        for entry in manual:
            label = SERVICE_DAY_LABEL.get(entry["service_day"], entry["service_day"])
            start = entry["start_time"]
            note = entry["notes"]
            origin = entry["origin_stop_name"] or "-"
            dest = entry["destination_stop_name"] or "-"
            lines.append(f"  {label} {start} | {origin} → {dest} | {note}")

    if games:
        lines.append("")
        lines.append("Kampe:")
        for g in games:
            lines.append(
                f"  {g['date']} {g['start_time']} | {g['hall_name']} | {g['tournament_name']} vs {g['opponent_name']} ({g['role']})"
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render hyperpersonalised PDF/text plan for a squad alias.")
    parser.add_argument("--alias-id", type=int, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "output" / "itineraries")
    parser.add_argument("--format", choices=["pdf", "txt"], default="pdf")
    args = parser.parse_args()

    with get_connection() as conn:
        header = fetch_alias_header(conn, args.alias_id)
        itinerary = fetch_itinerary(conn, args.alias_id)
        manual = fetch_manual_segments(conn, args.alias_id)
        games = fetch_games(conn, args.alias_id)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Sanitize team name for filename (replace / and spaces)
    safe_team_name = header['schedule_team_name'].replace('/', '-').replace(' ', '_')
    filename = f"{args.alias_id}_{safe_team_name}_{timestamp}.{args.format}"
    output_path = args.output / filename

    if args.format == "pdf":
        render_pdf(header, itinerary, manual, games, output_path)
    else:
        render_text(header, itinerary, manual, games, output_path)

    print(f"Wrote itinerary to {output_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate PDF itineraries for all 80 team aliases.

Usage:
    python3 scripts/generate_all_pdfs.py
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "build" / "event_planner.db"
OUTPUT_DIR = ROOT / "output" / "itineraries"


def main() -> None:
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        print("Run the build scripts first:")
        print("  python3 scripts/build_bus_routes.py")
        print("  python3 scripts/build_lodging.py")
        print("  python3 scripts/build_tournament.py")
        print("  python3 scripts/build_event_db.py")
        print("  python3 scripts/map_team_aliases.py")
        print("  python3 scripts/generate_itineraries.py")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("""
        SELECT alias_id, lodging_club, raw_label, schedule_team_name
        FROM vw_team_alignment
        ORDER BY alias_id
    """)
    aliases = cur.fetchall()
    conn.close()

    if not aliases:
        print("Error: No team aliases found in database")
        sys.exit(1)

    print(f"Generating PDFs for {len(aliases)} teams...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    fail_count = 0
    failed_aliases = []

    for alias_id, club, label, schedule_name in aliases:
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/render_pdf.py",
                    "--alias-id",
                    str(alias_id),
                    "--output",
                    str(OUTPUT_DIR),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                success_count += 1
                print(f"  ✓ {alias_id:3}: {schedule_name:30} ({club} - {label})")
            else:
                fail_count += 1
                failed_aliases.append((alias_id, schedule_name, result.stderr))
                print(f"  ✗ {alias_id:3}: {schedule_name:30} FAILED")
        except Exception as e:
            fail_count += 1
            failed_aliases.append((alias_id, schedule_name, str(e)))
            print(f"  ✗ {alias_id:3}: {schedule_name:30} ERROR: {e}")

    print(f"\nGeneration complete:")
    print(f"  Success: {success_count}/{len(aliases)}")
    print(f"  Failed:  {fail_count}/{len(aliases)}")

    if failed_aliases:
        print("\nFailed teams:")
        for alias_id, name, error in failed_aliases:
            print(f"  {alias_id}: {name}")
            print(f"     {error[:200]}")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

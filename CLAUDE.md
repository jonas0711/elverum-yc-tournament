# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an event logistics system that generates personalized PDF itineraries for handball teams attending the Elverum Youth Championship (EYC) tournament on April 25-27, 2025. The system fuses three data sources—bus schedules, lodging assignments, and tournament games—into a SQLite database and outputs per-team PDF plans showing transport, games, lunch slots, and the Saturday evening concert.

**Core requirement**: Teams must arrive at halls **≥40 minutes before game start**. Transport must only use the official bus plan; never invent routes or extra departures.

## Build Pipeline (Run in Order)

All commands run from repository root. Each script is idempotent and overwrites its target database.

```bash
python3 scripts/build_bus_routes.py      # Parses bussruter-eyc PDF → bus_routes.db
python3 scripts/build_lodging.py         # Parses Overnatningsoversigt docx → lodging.db
python3 scripts/build_tournament.py      # Parses Kampoppsett xlsx → tournament.db
python3 scripts/build_event_db.py        # Consolidates into event_planner.db + views
python3 scripts/map_team_aliases.py      # Links lodging squads to tournament teams
python3 scripts/generate_itineraries.py  # Materializes team_itinerary_segments
```

Output artifacts land in [data/build/](data/build/).

## Test & Validation

Run tests after regenerating databases:

```bash
python3 tests/test_bus_routes.py
python3 tests/test_lodging.py
python3 tests/test_tournament.py
python3 tests/test_alignment.py
python3 tests/test_transport_candidates.py
python3 tests/test_itinerary_views.py
python3 tests/integrity_checks.py        # Summarizes data quality checks
```

Tests use direct script execution (not pytest framework). Each test prints assertions and exits non-zero on failure.

## Database Inspection

```bash
sqlite3 data/build/event_planner.db ".tables"
sqlite3 data/build/event_planner.db "SELECT COUNT(*) FROM schedule_games;"
sqlite3 data/build/event_planner.db "SELECT * FROM vw_team_alignment LIMIT 5;"
```

## Generate PDF Itineraries

```bash
python3 scripts/render_pdf.py --alias-id 1 --output output/itineraries
```

Requires `fpdf2` (install via `pip install fpdf2`). Falls back to plain text if unavailable.

Export JSON for a team:
```bash
python3 scripts/export_itinerary.py --team-name "Bjørkelangen/Høland"
```

## Architecture

### Data Flow

```
Raw sources (PDF, DOCX, XLSX)
  ↓
Domain ETL scripts (build_bus_routes, build_lodging, build_tournament)
  ↓
Domain databases (bus_routes.db, lodging.db, tournament.db)
  ↓
build_event_db.py consolidation
  ↓
event_planner.db (transport_*, lodging_*, schedule_*, team_aliases)
  ↓
map_team_aliases.py (lodging squads → tournament teams)
  ↓
generate_itineraries.py (materializes team_itinerary_segments)
  ↓
render_pdf.py (per-squad PDF plans)
```

### Key Tables in event_planner.db

- **transport_\***: Routes, stops, per-day departures ([transport_route_stop_times](data/build/event_planner.db)), and links to schools/halls ([transport_stop_links](data/build/event_planner.db)).
- **lodging_\***: Schools, clubs, teams, rooms, and team-room relationships. [lodging_team_squads](data/build/event_planner.db) splits multi-squad clubs (e.g., "Hold 1" and "Hold 2").
- **schedule_\***: Tournament halls, days, tournaments, teams, and [schedule_games](data/build/event_planner.db).
- **team_aliases**: Joins lodging squads to tournament teams via club slug matching and division keys (gender + birth year). Populated by [map_team_aliases.py](scripts/map_team_aliases.py).
- **logistics_events**: Fixed events (Thon Central lunch 13:00-17:30, Terningen Arena concert 19:30-21:00).
- **team_itinerary_segments**: Staging table populated by [generate_itineraries.py](scripts/generate_itineraries.py). Stores bus, game, lunch, concert, and `note` segments (note = manual transport needed).

### Key Views

- **vw_team_alignment**: Master team view showing lodging club, schedule team name, school, rooms, headcount.
- **vw_team_games**: Per-team game schedule with hall and time info.
- **vw_transport_trip_instances**: Denormalizes route/stop/time tuples for each service day (fri/sat/sun).
- **vw_game_transport_candidates**: Matches bus departures to games, filtering for ≥40 min buffer.
- **vw_team_itinerary_flat**: Flattens [team_itinerary_segments](data/build/event_planner.db) for PDF rendering.
- **vw_manual_transport_needs**: Lists segments with `segment_type='note'` where no viable bus was found.
- **vw_bus_load_summary**: Aggregates headcount per bus trip for capacity checking (default limit 120 passengers).

See [docs/schema_overview.md](docs/schema_overview.md) for full table definitions.

### Module Organization

- **scripts/**: ETL builders, itinerary generator, PDF renderer, export tools.
- **tests/**: Validation scripts; execute directly (not via pytest).
- **data/raw/**: Plain-text snapshots of source files (auto-regenerated when needed).
- **data/build/**: Generated SQLite databases and SQL dumps.
- **docs/**: Schema diagrams, ETL overview, progress notes, test documentation.
- **images/**: Screenshots and reference diagrams.

## Code Style

- Python 3.11+ with 4-space indentation and snake_case naming.
- Module-level constants for shared config (e.g., `BUS_CAPACITY_LIMIT`, `LUNCH_WINDOW_MIN`).
- SQL: uppercase keywords, singular table names, explicit `FOREIGN KEY` clauses.
- Preserve existing filenames when adding raw sources to maintain provenance.

## Domain-Specific Rules

### Transport Planning
- Every bus segment must reference an existing [transport_route_stop_times](data/build/event_planner.db) row; do not invent routes or times.
- For games, select bus departures ensuring arrival ≥40 minutes before `start_time`.
- After each day's last activity, add a return trip to the lodging school.
- Track bus capacity using [BusLoadTracker](scripts/generate_itineraries.py:57) (default 120 passengers). If all candidates are full, log "capacity override" in segment notes.

### Lunch Scheduling (Saturday only)
- Window: 13:00–17:30 at Thon Central (stop: "Thon Central").
- Departure must be from the team's last hall (if they played a game) or lodging school (if idle).
- Account for game duration when scheduling lunch slots:
  - Ages 13-16: 25 minutes per game.
  - Ages 6-12: 20 minutes per game.
- Default lunch duration: 45 minutes.

### Concert Logistics (Saturday evening)
- Terningen Arena, 19:30–21:00.
- Transport must start from the team's last Saturday activity (game or lunch) with ≥20 minute buffer before 19:30.
- Use stop "Terningen Arena" for concert venue.

### Team Aliases
- Lodging clubs may field multiple squads (e.g., "Bjørkelangen/Høland J2011 (2)" means two squads).
- [map_team_aliases.py](scripts/map_team_aliases.py) matches lodging teams to tournament teams using club slug and division key.
- When a club has multiple squads, the script allocates them to distinct schedule teams with matching division keys.
- Elverum home teams do not need lodging or itineraries.

## Common Pitfalls

- **Missing 40-minute buffer**: Always verify game transport using [vw_game_transport_candidates](data/build/event_planner.db).
- **Invented bus routes**: Only use times from [transport_route_stop_times](data/build/event_planner.db). If no viable bus exists, log it as `segment_type='note'` with explanation.
- **Lunch conflicts**: Check that lunch slots don't overlap with games. Use [vw_team_game_sequence](data/build/event_planner.db) to see ordered game timings.
- **Capacity overruns**: Run [vw_bus_load_summary](data/build/event_planner.db) after generating itineraries to detect overbooked trips.
- **Hall name normalization**: [generate_itineraries.py](scripts/generate_itineraries.py:34) defines `HALL_NAME_ALIASES` mapping sub-halls (e.g., "Herneshallen - mini 1") to parent halls. Apply these when linking stops to halls.

## Documentation References

- **Project scope**: [projekt.md](projekt.md) (requirements in Danish), [mail.md](mail.md) (original client email).
- **ETL overview**: [docs/etl_overview.md](docs/etl_overview.md).
- **Schema design**: [docs/relational_schema_plan.md](docs/relational_schema_plan.md).
- **Test guide**: [docs/tests.md](docs/tests.md).
- **Progress log**: [docs/status.md](docs/status.md), [docs/todo.md](docs/todo.md).
- **Developer quickstart**: [docs/developer_launch.md](docs/developer_launch.md).

## Extensions & Future Work

See [docs/todo.md](docs/todo.md) for pending tasks. Key areas:
- Refine lunch assignment heuristics for teams with multiple Saturday games.
- Add alarm for overbooked buses (integrate [vw_bus_load_summary](data/build/event_planner.db) into validation).
- Enhance PDF layout (see [docs/pdf_blueprint.md](docs/pdf_blueprint.md)).
- Support manual transport override UI for `note` segments flagged in [vw_manual_transport_needs](data/build/event_planner.db).

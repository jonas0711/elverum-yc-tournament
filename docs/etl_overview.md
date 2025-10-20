# ETL Overview

## Data Sources
- `bussruter-eyc (1).pdf` → raw shuttle schedule.
- `Overnatningsoversigt (1).docx` → lodging assignments.
- `Kampoppsett EYC 25 - 27 april 2025 (1).xlsx` → tournament game schedule.

Plain-text snapshots live under `data/raw/` and are regenerated automatically by the ETL scripts when required.

## Build Scripts
Run the scripts from the repository root in the listed order:

1. `python3 scripts/build_bus_routes.py`  
   Produces `data/build/bus_routes.db` and `data/build/bus_routes.sql`.

2. `python3 scripts/build_lodging.py`  
   Produces `data/build/lodging.db` and `data/build/lodging.sql`.

3. `python3 scripts/build_tournament.py`  
   Produces `data/build/tournament.db` and `data/build/tournament.sql`.

4. `python3 scripts/build_event_db.py`  
   Consolidates the three domain databases into `data/build/event_planner.db`, seeds `logistics_events` (lørdags-lunch & koncert) og bygger views (`vw_team_alignment`, `vw_team_games`, `vw_transport_trip_instances`, `vw_game_transport_candidates`). En SQL dump gemmes i `data/build/event_planner.sql`.

5. `python3 scripts/map_team_aliases.py`  
   Populates `team_aliases` inside `event_planner.db` by matching lodging squads to tournament teams using club slugs and division keys.

6. `python3 scripts/generate_itineraries.py`  
   Materialises baseline `team_itinerary_segments` (bus, game, lunch, koncert) leveraging the prepared views og markerer manglende forbindelser som `segment_type='note'`.

Each script is idempotent: it rewrites the target database/dump on every run.

## Integrity Checks
After building the consolidated database, run:

```
python3 tests/integrity_checks.py
```

This prints a summary of:
- Tournament game count and dates loaded.
- Lodging teams without a room assignment (should be zero).
- Bus departure counts per route/service day and the latest Saturday departure for route 2.
- Stop-to-school/hall linkage coverage.

## Key Tables in `event_planner.db`
- `transport_*`: shuttle routes, stops, per-day departures, and links to schools/halls.
- `lodging_*`: schools, clubs, teams, rooms, and team-room relationships.
- `schedule_*`: tournament halls, days, tournaments, teams, and games.
- `team_aliases`: matcher lodging squads til turneringshold (opdateres af `map_team_aliases.py`).
- `team_itinerary_segments`: tom stagingtabel hvor kommende algoritme kan gemme planlagte segmenter.
- `logistics_events`: faste arrangementer (Thon Central lunch, Terningen Arena koncert) for itinerary-planlægning.
- Views: `vw_team_alignment`, `vw_team_games`, `vw_transport_trip_instances`, `vw_team_game_sequence`, `vw_team_daily_summary`, `vw_logistics_events`, `vw_game_transport_candidates`, `vw_bus_load_summary`, `vw_team_itinerary_flat`, `vw_manual_transport_needs`.

Refer to `docs/relational_schema_plan.md` for the conceptual ER diagram and planned extensions (e.g., itineraries, lunch assignments).

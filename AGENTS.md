# Repository Guidelines

## Project Goal & Deliverables
Maintain a pipeline that fuses bus, lodging, and match schedules into SQLite and emits per-team PDF itineraries. Each plan must span Fri–Sun, list transport legs arriving ≥40 minutes before matches, and distinguish clubs with multiple squads. Include the Saturday lunch window (13:00–17:30 at Thon Central, departing from the last arena or lodging if idle) and the Saturday concert at Terningen Arena (26 April, 19:30–21:00). Include bus-stop details for each hop plus passenger counts. Bus-load and lunch summaries are lower priority; log any deferrals in the plan files.
- Only schedule transport using the official bus plan; never invent routes or extra departures.

## Project Structure & Module Organization
`create_bus_database.py` in the repo root parses `extracted_text.txt` (from `bussruter-eyc (1).pdf`) into `data/build/bus_routes.*`. Lodging schemas live in `full_database.sql`, with historic imports in `data/build/tournament.db`. Raw captures remain under `data/raw/`; generated artifacts land in `data/build/`. Requirement notes sit in `projekt.md`, `mail.md`, and the `*_plan_creation.md` files—append dated updates only. Promote durable utilities to `scripts/` and regression checks to `tests/`.

## Build, Test, and Development Commands
- `python create_bus_database.py` regenerates bus SQL/DB and surfaces parsing warnings inline.
- `sqlite3 data/build/bus_routes.db ".tables"` confirms `Routes`, `Stops`, and `RouteStops` exist post-regeneration.
- `sqlite3 data/build/tournament.db "SELECT COUNT(*) FROM Teams;"` validates lodging imports before new joins.
- `sqlite3 < full_database.sql` reapplies the lodging schema; execute against a disposable DB during iteration.

## Coding Style & Naming Conventions
Use Python 3.11, 4-space indentation, descriptive snake_case, and module-level constants for shared stop lists. SQL scripts should uppercase keywords, keep singular table names, and declare explicit `FOREIGN KEY` clauses. Mirror existing filenames when adding raw sources to preserve provenance.

## Testing Guidelines
After bus regeneration, sample three itineraries with `sqlite3 data/build/bus_routes.db "SELECT route_number, stop_name, departure_time FROM RouteStops LIMIT 20;"`, verifying the 40-minute buffer. When adjusting lodging or transport joins, reconcile team counts against `Overnatningsoversigt (1).docx` and note manual tweaks in the relevant plan file. Capture any bus-load calculations and lunch slot heuristics in `docs/tests.md` once stabilised.

## Commit & Pull Request Guidelines
Adopt Conventional Commits (e.g., `feat: add bus occupancy summary`, `fix: adjust lunch window logic`). Reference the motivating plan document in every PR, list regenerated artifacts, and include before/after command snippets for schema-impacting changes. Attach updated source PDFs or spreadsheets only when the upstream data changes materially.

## Data & Security Notes
Artifacts include identifiable participants. Keep raw exports out of version control, treat the provided PDF, Word, and Excel files as authoritative, and redact club names when sharing logs externally.

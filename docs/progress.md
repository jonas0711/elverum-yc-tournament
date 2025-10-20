# Development Log

## 2025-04-07

### Repository Understanding
- **Requirements**: Per `mail.md` and `projekt.md`, every non-Elverum team needs a personalised itinerary linking games, transport, lodging, lunch window (Saturday 13:00–17:30 at Thon Central), and the Saturday concert (19:30–21:00 Terningen Arena) while guaranteeing bus arrivals ≥40 min before games.
- **Raw data**:
  - `bussruter-eyc (1).pdf` contains three shuttle routes with stop descriptions and conditional service notes.
  - `Overnatningsoversigt (1).docx` lists lodging assignments by school → club → team/room.
  - `Kampoppsett EYC 25 - 27 april 2025 (1).xlsx` holds the complete tournament schedule (hall, day, tournament, match code, teams, time).

### ETL Pipelines
- **Bus routes** (`scripts/build_bus_routes.py`):
  - Parses the PDF text extraction, normalises stops, preserves Saturday-only flags for routes 1 & 3 and expands the 30-minute cadence for route 2 across Fri/Sat/Sun.
  - Generates `data/build/bus_routes.db` with tables `routes`, `stops`, `route_stops`, `route_stop_times`.
  - Stop descriptions stored using the narrative “Busstopp” section.
- **Lodging** (`scripts/build_lodging.py`):
  - Reads DOCX tables, associates each club heading with its teams, extracts headcount from the “Antall” column, and splits room assignments.
  - Outputs `data/build/lodging.db` with `schools`, `clubs`, `teams`, `rooms`, `team_rooms`.
  - Filters out “grupperom” aggregate notes. Recognised 62 team rows spanning 4 schools and 29 clubs.
- **Tournament schedule** (`scripts/build_tournament.py`):
  - Pulls the Excel sheet, converts fractional start times to `HH:MM`, and respects hall/day headings.
  - Loads into `data/build/tournament.db` across `halls`, `event_days`, `tournaments`, `teams`, `games` (368 games, 33 tournaments, 87 team labels).

### Consolidated Database
- **Integration** (`scripts/build_event_db.py`):
  - Copies all domain tables into `data/build/event_planner.db` (`transport_*`, `lodging_*`, `schedule_*`).
  - Adds `transport_stop_links` linking shuttle stops to lodging schools and halls (e.g., EUS ↔ Elverumshallen, ELVIS ↔ Elvishallen).
  - Provides `team_aliases` placeholder for future reconciliation between lodging team labels and tournament team names.

### Metadata Enhancements
- Lodging ETL now records `division_key` (`gender+birth year`) and expands multi-team entries into `team_squads` so downstream logic can target each squad individually.
- Tournament ETL parses gender/age/pool metadata from tournament names and stores derived `birth_year` (assuming 2024 season) for cross-referencing with lodging divisions.
- Consolidated database mirrors these fields and the integrity check reports division coverage plus sample multi-squad clubs.

### Alias Mapping
- `scripts/map_team_aliases.py` matcher nu alle 80 lodging-squads til turneringshold via division keys, klub-slugs og supplerende aliaser (fx AFSK for Aurskog Finstadbru). Integritetstesten bekræfter 100 % dækning.

### Bus Schedule Corrections (images/busplan)
- Rebuilt `scripts/build_bus_routes.py` to parse the PDF text directly, fixing missing/incorrect times for Rute 1 and Rute 3 (including Thon Central (lørdag) departures and all “kun lør” columns).
- Added regression tests in `tests/test_bus_routes.py` that compare the database output with the reference tables from the images (Ydalir, Thon Central, EUS etc.).

### Test Coverage
- `tests/test_bus_routes.py` verificerer begge retninger af ruterne (Ydalir loops, Thon Central og Terningen Arena offsets) mod busplan-billederne.
- `tests/test_lodging.py` tager repræsentative klubber fra hver skole (Elverum, Frydenlund, Ydalir, ELVIS) og matcher headcount samt normaliserede rumkoder mod overnatningsoversigten.
- `tests/test_tournament.py` sammenligner kampinfo fra fredagens åbningskampe, lørdagens 08:57-blok og eftermiddagskampene med Excel-screenshots.
- `tests/test_alignment.py` bekræfter at `team_aliases` knytter overnatning til turneringshold (eks. Røros J2011 → rum A004) og at de samme squads findes i kampprogrammet.
- `tests/integrity_checks.py` rapporterer tværgående totals (spil, divisioner, busafgange) samt alias-status (alle 80 squads mappet).

### Integrity Checks
- `tests/integrity_checks.py` confirms:
  - 368 games across Fri/Sat/Sun present.
  - No lodging team lacks a room assignment.
  - Bus route frequencies and latest departures (Route 2 late Saturday bus 19:50).
  - Stop linkage coverage for school/hall combinations.

### Open Considerations
- Clubs can field multiple squads within the same age group; lodging records (`raw_label`) need to be reconciled with tournament team names to ensure itinerary joins per squad.
- Future itinerary engine must derive age/gender from both lodging and schedule datasets and guarantee each team references its specific room/school.
- `docs/todo.md` tracks ongoing schema/to-do actions regarding age-group mapping and lodging relationships.

## 2025-04-08

### Logistics Prep
- Udvidede `scripts/build_event_db.py` med tabellen `logistics_events` og automatiske indlæsninger for lørdags-lunch (Thon Central) samt koncerten i Terningen Arena.
- Tilføjede viewet `vw_transport_trip_instances`, der leverer et stabilt trip-index per rute/service-dag/stop til videre rejseplanlægning.
- Byggede `vw_game_transport_candidates`, som matcher hvert alias/game til busafgange fra overnatningsskole til kamp-hal, og beregner rejsetid samt buffer ≥40 min før kampstart.
- Forstærkede `vw_team_games` med matchkode, hal-id og service-dagskode (fri/lør/søn), så den kommende itinerary-algoritme kan arbejde direkte på viewet uden ekstra dataset-forberedelse.
- Etablerede `team_itinerary_segments` som tom materialiseringstavle til fremtidige rejseplaner samt hjælpeviews `vw_team_game_sequence`, `vw_team_daily_summary` og `vw_logistics_events` til brug i algoritmens planlægningslogik.

-### Itinerary Generation
- Implementerede `scripts/generate_itineraries.py`, der udfylder `team_itinerary_segments` med bus- og kampsegmenter, lørdags-lunch samt koncerttransport baseret på de nye views.
- Udvidede `scripts/build_event_db.py` med `vw_bus_load_summary`, `vw_team_itinerary_flat` og `vw_manual_transport_needs`, så planlagte busafgange kan summeres pr. trip, eksporteres til PDF-input og manuale transporter (nu chartere) kan overvåges.
- Tilføjede tests (`tests/test_itinerary_views.py`, `tests/test_transport_candidates.py`) som nu verificerer logistikhændelser, segment-tabellen, busbelastninger, koncertsegmenter, og at manuelle transporter i view’et matcher de charter-markerede segmenter.
- Generatoren håndterer kapacitets-tracking, hall-aliaser, direkte/multi-leg routing; fallback resulterer i eksplicitte charter-bussegmenter (`route_id` NULL). Efter tilbagevenden til de officielle ruter resterer 357 chartere (112 på koncertlørdag). Højeste planlagte load er 112 passagerer (monitoreret via `vw_bus_capacity_alerts`).
- Charteropsamling dokumenteret i `docs/manual_transport_needs.md` (356 segmenter fordelt på koncert + søndagslogistik) som udgangspunkt for shuttle/charterplanlægning.
- Blueprint for hyperpersonaliseret PDF plan lagt i `docs/pdf_blueprint.md` (sektioner, datafelter, render-flow); understøttes af JSON-export via `scripts/export_itinerary.py`.
- Prototype-PDF generator tilføjet (`scripts/render_pdf.py`), som anvender data fra `vw_team_itinerary_flat` / `vw_manual_transport_needs` og outputter filer i `output/itineraries/` (kræver `fpdf2`).

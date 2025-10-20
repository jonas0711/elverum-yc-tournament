# Relational Schema Plan

## Guiding Requirements
- Every non-Elverum team needs a personalised itinerary that links games, lodging, bus transport, lunch, and the Saturday concert (`mail.md`, `projekt.md`).
- Buses must deliver teams to halls at least 40 minutes before each scheduled game.
- Lunch takes place at Thon Central between 13:00–17:30 on Saturday; routing must account for the preceding location (current hall if they played, otherwise lodging).
- Concert runs Saturday 19:30–21:00 at Terningen Arena and requires transport integration.

## Core Domains
1. **Tournament Schedule**
   - Halls (`halls`): id, name, notes.
   - Calendar days (`event_days`): id, date, display_label.
   - Competitions (`tournaments`): id, name, gender, age_group, birth_year, pool_code.
   - Teams (`teams`): id, club_name, squad_label, gender, year, is_elverum.
   - Games (`games`): id, tournament_id, hall_id, day_id, start_time, end_time, home_team_id, away_team_id, match_code.

2. **Lodging**
   - Schools (`schools`): id, name, address_note.
   - Rooms (`rooms`): id, school_id, room_code, capacity_hint.
   - Lodging assignments (`team_lodgings`): team_id, room_id, party_size, division_key, notes.
   - Squad expansion (`team_squads`): derived rows per team_id with squad_index for clubs fielding multiple squads in the same age group.

3. **Transport**
   - Routes (`routes`): id, public_number, description, operating_frequency.
   - Stops (`stops`): id, name, location_hint, hall_id, school_id.
   - Trips (`route_trips`): id, route_id, service_day (fri|sat|sun), sequence_no.
   - Stop times (`trip_stop_times`): trip_id, stop_id, stop_sequence, departure_time, condition_note (e.g., “kun lør”).

4. **Event Logistics**
   - Logistics events (`logistics_events`): id, name, event_type (`lunch`/`concert`), service_day, start_time, end_time, anchor_stop_id, notes.
   - Team itineraries (`team_itinerary_segments`): alias_id, sequence_no, segment_type (game|bus|stay|meal|concert|note|placeholder), ref_type, ref_id, timings, stop-reference, travel/buffer metrics.

## Relationships & Keys
- `teams` is the shared dimension across tournament, lodging, and itineraries.
- `team_lodgings.team_id` references `teams.id`; `team_lodgings.room_id` references `rooms.id`; `rooms.school_id` references `schools.id`.
- `games.*_team_id` references `teams.id`; enforce `home_team_id <> away_team_id`.
- `games.day_id` references `event_days.id`; `games.hall_id` references `halls.id`.
- `route_trips.route_id` references `routes.id`; `trip_stop_times.trip_id` references `route_trips.id`.
- `trip_stop_times.stop_id` references `stops.id`. Stops can optionally link to a hall (`stops.hall_id`) or school (`stops.school_id`) to support itinerary joins.
- `logistics_events` anvender transport-stop som ankerpunkt (fx Thon Central, Terningen Arena) og knyttes til service-dag for let filtrering.
- `team_itinerary_segments` (materialiseres af itinerary-generatoren) bliver outputtabellen; `segment_type` + `ref_type/ref_id` definerer referenceobjektet. `travel_minutes`/`buffer_minutes` kan anvendes til validering.

## Derived Views & Checks
- `vw_game_transport_candidates`: allerede implementeret view der leverer busafgange (≥40 min buffer) fra skole-stop til hal-stop pr. kamp.
- `vw_game_arrivals`: joins itineraries to ensure arrival segments reach hall stops ≥40 minutes before the associated game.
- `vw_bus_load_summary`: summerer bussegmenter pr. route/trip og estimerer headcount til kapacitetskontrol.
- `vw_team_daily_plan`: flatten per-team sequences for PDF generation.

## Data Quality Rules
- No duplicate team names per tournament bracket after normalisation.
- Every non-Elverum team must appear in `team_lodgings` and `games`.
- Every game must have at least one viable bus arrival candidate (matching day/stop).
- Lunch window assignments must fall within 13:00–17:30 and be reachable by bus from preceding location.
- Concert transport must start from each team’s last Saturday activity (game or lunch) with a valid bus route to Terningen Arena.

## Implementation Notes
- Store raw extracts under `data/raw/` (already created) to keep ETL reproducible.
- Build ETL scripts under `scripts/` with modular functions per domain and a master loader that populates a single SQLite database (`data/build/event_planner.db`).
- Apply migrations using explicit `CREATE TABLE` statements with foreign keys and indexes on join columns (`team_id`, `route_id`, `game_id`).
- Include lightweight pytest-style checks or SQL-based assertions to validate counts, orphan records, and 40-minute buffers after each load.

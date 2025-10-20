# Developer Launch Checklist

## 1. Data Build
From repository root:

```bash
python3 scripts/build_bus_routes.py
python3 scripts/build_lodging.py
python3 scripts/build_tournament.py
python3 scripts/build_event_db.py
python3 scripts/map_team_aliases.py
python3 scripts/generate_itineraries.py
```

Output artefakter:
- `data/build/bus_routes.db`
- `data/build/lodging.db`
- `data/build/tournament.db`
- `data/build/event_planner.db` (med views `vw_team_alignment`, `vw_team_games`, `vw_game_transport_candidates`, `vw_team_game_sequence`, `vw_bus_load_summary`)
- `team_itinerary_segments` indeholder både bus-/kampsegmenter og evt. `note`-segmenter hvor transport skal afklares manuelt; brug `vw_manual_transport_needs` som overblik.
- `scripts/render_pdf.py --alias-id <ID>` genererer en PDF (kræver `fpdf2`) eller tekstversion af holdplanen under `output/itineraries/`.

## 2. Tests (manuelle scripts)

```bash
python3 tests/test_bus_routes.py
python3 tests/test_lodging.py
python3 tests/test_tournament.py
python3 tests/test_alignment.py
python3 tests/test_transport_candidates.py
python3 tests/test_itinerary_views.py
python3 tests/integrity_checks.py
```

## 3. Eksport / Integration

- `python3 scripts/export_itinerary.py --team-name "Bjørkelangen/Høland"` udskriver et JSON-udtræk baseret på `vw_team_itinerary_flat`, klar til videre generering af PDF.

## 3. Forstå relationerne
- `docs/tests.md`: beskriver hvert testscript og referencebilleder.
- `docs/status.md`: projektstatus, dataflow, TODO.
- `docs/schema_overview.md`: tabel- og foreign-key-dokumentation.
- `docs/team_alignment.json` + `docs/club_school_summary.csv`: klub → overnatning → turneringshold (inkl. kampantal).
- `docs/game_alignment.csv`: sample kampe med begge holdenes skoler/rum.

## 4. Næste skridt (jf. projekt.md)
1. Validér og forbedr de genererede `team_itinerary_segments` (f.eks. håndtering af flere lørdagskampe, returtransport til overnatning, justering af lunch-slot).
2. Udled kapacitetsregler og alarmer via `vw_bus_load_summary`, så overbookede busser kan opdages og omplanlægges.
3. Generér PDF-er for hvert squad (brug `scripts/render_pdf.py` + layout blueprint) og indarbejd buffer-/bemærkningsfelter i layoutet.

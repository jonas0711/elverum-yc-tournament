# Status – Elverum Data Platform (2025-04-08)

## Inputgrundlag
- **Busplan**: `bussruter-eyc (1).pdf` → `data/build/bus_routes.db`.
- **Overnatning**: `Overnatningsoversigt (1).docx` → `data/build/lodging.db`.
- **Kampoppsett**: `Kampoppsett EYC 25 - 27 april 2025 (1).xlsx` → `data/build/tournament.db`.

Screenshots i `images/` er brugt som reference til tests.

## ETL & Konsolidering
- `scripts/build_bus_routes.py` → normaliserede ruter, stop, afgangstider.
- `scripts/build_lodging.py` → klub/hold pr. skole med `division_key`, rum og squads.
- `scripts/build_tournament.py` → normaliserede turneringer, haller, kampe, hold­metadata.
- `scripts/build_event_db.py` → samler alt i `data/build/event_planner.db`, seed'er logistikhændelser (lørdags-lunch, koncert), opretter hjælpetabellen `team_itinerary_segments` og views:
  - `vw_team_alignment`: kobler lodging-team (klub, rum, headcount) til matchende turneringshold.
  - `vw_team_games`: viser kampprogram pr. squad (dato, tid, hal, modstander, service-dagskode).
  - `vw_team_game_sequence`: rækkefølge per squad inkl. tidsafstand til forrige/næste kamp.
  - `vw_team_daily_summary`: bundter dagens kampe per squad (første/sidste start).
  - `vw_transport_trip_instances`: trip-index pr. rute/service-dag/stop til koordination af rejser.
  - `vw_game_transport_candidates`: viable busafgange (≥40 min buffer) fra skole-stop til hal-stop pr. kamp.
  - `vw_logistics_events`: faste arrangementer med tilknyttet busstop.
  - `vw_bus_load_summary`: estimat af passagerer pr. rute/trip baseret på planlagte bussegmenter.
  - `vw_bus_capacity_alerts`: filtrerer afgange med >100 estimerede passagerer for hurtig opfølgning.
- `scripts/map_team_aliases.py` → matcher 100 % (80/80) lodging-squads til turneringshold.
- `scripts/generate_itineraries.py` → materialiserer `team_itinerary_segments` (bus til kamp, kampsegmenter, lørdags-lunch og koncerttransport). Manglende offentlige forbindelser planlægges nu som charter-bussegmenter (`route_id` NULL), og `vw_manual_transport_needs` lister i alt 356 charterbehov (primært søndagsrejser + enkelte koncertafgange).
- Views til downstream forbrug: `vw_team_itinerary_flat` (flad tidslinje med stopnavne/route info) og `vw_manual_transport_needs` (liste over manuelle transporter der skal afdækkes).

## Testoversigt
- `tests/test_bus_routes.py`: Verificerer alle ruter (Ydalir loops, Thon Central, Terningen Arena osv.) mod busplan-billederne.
- `tests/test_lodging.py`: Samples fra alle skoler (Elverum, Frydenlund, Ydalir, ELVIS) mod overnatningsoversigten.
- `tests/test_tournament.py`: Åbningskampe fredag, lørdag 08:57-blok og lørdag eftermiddag 15:55 mod Excel-screenshots.
- `tests/test_alignment.py`: Sikrer at `team_aliases` binder overnatningshold til turneringshold og at de optræder i kampprogrammet.
- `tests/test_transport_candidates.py`: Sanity-check for logistikhændelser og buskandidater (buffer ≥40, seedede events).
- `tests/test_itinerary_views.py`: Validerer at itinerary-segmenter er genereret, busbelastninger opsummeres, koncertsegmenter findes, og staging-tabellen ikke er tom.
- `tests/integrity_checks.py`: Opsummerer tværgående stats (kampe, busafgange, divisioner, aliasdækning).

Alle tests er grønne efter seneste kørsel.

## Datauddrag
- `docs/team_alignment.json` og `docs/club_school_summary.csv` viser pr. klub og squad: alder (division), school/rum, matchet turneringshold og antal kampe (udledt via `vw_team_games`).
- `docs/game_alignment.csv` giver eksempler på kampe, inklusive hvilke skoler/rum de to involverede squads bor på.
- `docs/manual_transport_needs.md` + `vw_manual_transport_needs` i databasen fremhæver 357 charterkrav (112 lørdag – primært koncertafgange, 228 søndag), som skal adresseres i shuttleplanen før endelig algoritme/planlægning.
- `docs/pdf_blueprint.md` beskriver layout og datapipeline til de hyperpersonaliserede PDF’er baseret på `vw_team_itinerary_flat`; `scripts/render_pdf.py` genererer en prototype-PDF pr. alias (kræver `fpdf2`).

## Næste skridt (jf. `projekt.md`)
1. Nedbringe `segment_type='note'` (manuelle transporter) via multi-trins busrouting og udvidet stopmapping for hall-varianter; prioriter søndagsmorgen-case (Frydenlund ↔ ELVIS/Søndre) og holdlogik uden kollektivdækning.
2. Forfine kapacitetslogikken yderligere ved at planlægge eksplicitte alternative afgange (eller dedikerede busser) når `vw_bus_load_summary` nærmer sig 120 personer.
3. Udvikle PDF-generatoren, der læser `vw_team_itinerary_flat` og præsenterer hyperpersonaliserede dagsplaner (inkl. buffere, bemærkninger og markering af manuelle transporter).

Status: Alle rå data er integreret i én relationel DB med dokumenterede tests og views, klar til at bygge itineraries og rapportering på toppen.

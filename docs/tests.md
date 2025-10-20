# Test Overview

## `tests/test_bus_routes.py`
- **Purpose**: Verifies that the shuttle timetables parsed from `bussruter-eyc (1).pdf` match the reference schedules (see `images/busplan/*.png`).
- **Key Assertions**:
  - `test_route1_ydalir_primary` / `test_route1_ydalir_return_loop`: confirm both legs of Rute 1 (yellow board) list all departure times for Ydalir, including the “kun lør” afternoon column.
  - `test_route1_thon_central`: ensures both Thon Central (lørdag) blocks are present (13:25–17:35 and 13:05–18:05).
  - `test_route2_eus_half_hour` / `test_route2_terningen_arena_offsets`: check Rute 2’s 30‑min cadence and that the offsets place Terningen Arena 25 minutes past each hour.
  - `test_route3_eus_full_span` / `test_route3_thon_central_loop`: validate the full 40‑min sequence for Rute 3, including the limited Thon Central column.

## `tests/test_lodging.py`
- **Purpose**: Confirms lodging assignments (schools, headcounts, rooms) parsed from `Overnatningsoversigt (1).docx` match the Word screenshots (`images/overnatning/*.png`).
- **Sampling**:
  - Elverum ungdomsskole: Røros, Hasle/Løren, Storhamar, Ring IL, Skarnes.
  - Frydenlund: Borgen IL, Tydal, Drøbak/Frogn, Gjøvik HK.
  - Ydalir: Lensbygda, Ottestad, Jardar IL, Trysil, Kolbu IL.
  - ELVIS: Årdalstangen, Jotun, Heradsbygda HK, HK Vestre Toten, Utleira, plus Sverresborg squads.
- Each assertion checks both headcount and normalized room codes so data is ready for itinerary logic.

## `tests/test_tournament.py`
- **Purpose**: Validates the tournament schedule extracted from `Kampoppsett EYC 25 - 27 april 2025 (1).xlsx` against screenshots (`images/kampopsett/*.png`).
- **Sampling**:
  - Opening matches Friday 18:00/18:19 (Elverumshallen).
  - Saturday morning block at 08:57 (different halls and age groups).
  - Saturday afternoon example 15:55 (Hasle-Løren Gul vs Furnes 2).
- Confirms correct mapping of day, time, hall, tournament label, and home/away teams.

## `tests/test_alignment.py`
- **Purpose**: Ensures the cross-domain link between overnatning og turneringshold fungerer via `vw_team_alignment` og `vw_team_games` i `event_planner.db`.
- **Checks**:
  - Lodging-squad `Røros / J2011` er matchet til schedule holdet “Røros” og har rumkoden `A004` som i overnatningsoversigten.
  - Eksempel fra `Gjøvik HK / J2013` har mindst én kamp i scedulen med korrekt dag og modstander.

## `tests/test_transport_candidates.py`
- **Purpose**: Verifies logistics scaffolding efter konsolidering.
- **Checks**:
  - `vw_game_transport_candidates` returnerer mindst én kandidat med buffer ≥40 minutter og gyldige afgang-/ankomststop.
  - `logistics_events` tabellen er seeded med lørdags-lunch (13:00–17:30) og koncerten (19:30–21:00).

## `tests/test_itinerary_views.py`
- **Purpose**: Sikrer at itinerary-infrastrukturen er aktiv efter `generate_itineraries.py`.
- **Checks**:
  - `team_itinerary_segments` indeholder data, og koncertsegmenter er genereret for squads.
  - `vw_team_game_sequence` rapporterer positive tidsgab mellem kampe, og `vw_team_daily_summary` stemmer med rå game-counts.
- `vw_bus_load_summary` leverer aggregeret kapacitet per rute/trip (forberedelse til kapacitetsvalidering).
- Ingen `segment_type='placeholder'` forekommer i den materialiserede tabel.
- `vw_manual_transport_needs` har én række pr. `note`-segment, så manuelle transporter kan planlægges særskilt.

## `tests/integrity_checks.py`
- **Purpose**: Cross-domain sanity report for the consolidated `event_planner.db`.
- **Output**:
  - Counts for games, event days, and lodging teams without rooms.
  - Division key summary (gender + birth year) to ensure metadata is populated.
  - Bus departures per route/service day (sanity check for frequency).
  - Stop linkage table (maps bus stops to schools/halls).
  - `team_aliases` coverage (all 80 lodging squads currently matched).

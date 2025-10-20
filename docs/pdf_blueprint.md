# PDF Blueprint – Hyperpersonalized Team Plan

## Input Data
- **Source view:** `vw_team_itinerary_flat` (ordered by service_day, sequence_no)
- **Supplemental:** `vw_manual_transport_needs`, `vw_bus_load_summary`, team metadata from `vw_team_alignment`/`vw_team_games`.
- **Exporter:** `python3 scripts/export_itinerary.py --alias-id <ID>` (JSON payload til render-service).

## Layout Sections (per hold)
1. **Header**
   - Holdnavn (`schedule_team_name`), klub (`lodging_club`), årgang (`lodging_label`).
   - Overnatningsskole + rum (`school_name`, `room_codes`), headcount.
   - Kontaktinformation (skal tilføjes manuelt hvis tilgængeligt).
2. **Dag-til-dag tidslinje**
   - For hver `event_date`/`service_day`:
     - Segment type og tidsrum (`start_time`–`end_time`).
     - Ikoner pr. segment (`bus`, `game`, `meal`, `stay`, `concert`, `note`).
     - Afgang/ankomststop (`origin_stop_display`, `destination_stop_display`).
     - Busnr./rute (`route_number`, `trip_index`), travel- og buffer-minutter hvor tilgængelig.
     - Notefelt – især for chartere eller manuelt planlagte transporter.
3. **Transportopsummering**
   - Liste over alle busafgange med estimeret passagertal fra `vw_bus_load_summary` (cross-join på alias, route_id & trip_index).
   - Chartersektion (fra `vw_manual_transport_needs`) med markering: “Charter” eller “Manuelt arrangér”.
4. **Kampdetaljer**
   - Tabel over kampe (fra `vw_team_games`): dato, tidspunkt, hal, turnering, modstander, rolle (home/away).
   - Indsæt `vw_team_daily_summary` for quick stats pr. dag.
5. **Særlige aktiviteter**
   - Lunch-slot (13:00–17:30) med “Frivillig / planlagt” status.
   - Koncertdetaljer (19:30–21:00 Terningen Arena) + charter/bus info.
6. **Bemærkninger**
   - Advarsel for segmenter med `notes` der indeholder “manual” eller “charter”.
   - Kapacitetsnote hvis `estimated_headcount` > 100 på nogen af holdets afgange.

## Output Format
- Primær: PDF (A4, stående). Designet til udlevering til holdansvarlige.
- Sekundær: JSON (fra `scripts/export_itinerary.py`) til frontend/preview.

## Render Flow (foreslået)
1. Kør `build_*` scripts + `generate_itineraries.py`.
2. For hvert alias:
   - `python3 scripts/export_itinerary.py --alias-id <ID>` → JSON.
   - Render-service (f.eks. Node/Python) lægger data i templating engine (HTML→PDF eller direkte PDF bibliotek).
3. Arkiver PDF i `output/itineraries/<alias_id>.pdf` og optional ZIP per klub.

## Åbne Punkter
- Indsamle kontaktinfo og buskapacitet (reelle sæder) for endelig charterplan.
- Støtte til flere sprog (DK/NO/EN) – besluttelse af labels i layout.
- Automatiseret distribution (mail / portal) efter generering.

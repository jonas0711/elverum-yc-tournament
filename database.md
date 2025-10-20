# Databaseoversigt

Dette dokument opsummerer hele datalagret i Elverum-projektet efter seneste
regenerering (2025-10-20). Alle tal og eksempler stammer fra de faktiske SQLite
filer under `data/build/`.

## 1. `data/build/bus_routes.db`

| Tabel | Rækker | Formål |
|-------|--------|--------|
| `routes` | 3 | Rutenavne, officielle rutenumre og tekstnoter fra buspdf'en. |
| `stops` | 8 | Standardiserede stoppesteder med beskrivelser fra busmaterialet. |
| `route_stops` | 30 | Sekvenserer stoppene pr. rute og angiver evt. default-offset. |
| `route_stop_times` | 799 | Fuld tidstabel pr. rute/dag/trip; genereret til faste intervaller. |

**Eksempel:** `route_stop_times` rækker 1–3 repræsenterer lørdagsafgange fra
Ydalir på Rute 1 (`07:00`, `07:50`, `08:40`). Hvert stop-knudepunkt kan kobles
til skoler/haller via `transport_stop_links` i hoveddatabasen.

## 2. `data/build/lodging.db`

| Tabel | Rækker | Formål |
|-------|--------|--------|
| `schools` | 4 | Overnatningssteder (EUS, ELVIS, Frydenlund, Ydalir). |
| `clubs` | 29 | Klub pr. skole. |
| `teams` | 62 | Overnatningshold; indeholder køn, årgang, antal hold og headcount. |
| `team_squads` | 80 | Materialiserer de 80 squads (f.eks. “Furnes – G2014,2 lag” → 2 poster). |
| `rooms` | 68 | Rumkoder pr. skole. |
| `team_rooms` | 70 | Kobling mellem hold og rum. |

**Eksempel:** Klubben Røros (`clubs.club_id = 1`) har et hold “G2014,2 lag”
med `headcount = 18` og rum “A002”. To squads (`squad_index = 1 og 2`) oprettes
derfor i `team_squads`.

## 3. `data/build/tournament.db`

| Tabel | Rækker | Formål |
|-------|--------|--------|
| `schedule_event_days` | 3 | Fredag–Søndag med labels. |
| `schedule_halls` | 12 | Alle haller/baner inkl. kortbaner. |
| `schedule_tournaments` | 19 | Turneringer (alder/klasse). |
| `schedule_teams` | 80 | Kampnavne fra Excel-arket. |
| `schedule_games` | 368 | Kompleks kampprogram med starttider, hal og hold. |

**Eksempel:** Kamp `30441202004` ligger i `schedule_games` med start kl. 18:00
fredag i Elverumshallen og matcher turneringen “Elverum Yngres Cup - Jenter 12 år - 02”.

## 4. `data/build/event_planner.db`

Den konsoliderede database består af tabeller fra transport, overnatning og
turnering samt hjælpetabeller, logs og views. Nedenfor er strukturen grupperet
efter domæne.

### 4.1 Transporttabeller

| Tabel | Rækker | Noter |
|-------|--------|-------|
| `transport_routes` | 3 | Samme data som `routes`, men tilgængelig for krydsslag. |
| `transport_stops` | 8 | Kan linkes til skoler (`lodging_school_id`) og haller (`schedule_hall_id`). |
| `transport_route_stops` | 30 | Stopsekvenser pr. rute. |
| `transport_route_stop_times` | 799 | Afledt fra busrutetabellen inkl. `trip_index`. |
| `transport_stop_links` | 13 | Manuelle koblinger: fx EUS ↔ Elverumshallen, ELVIS ↔ Elvishallen. |

**Eksempel:** `transport_stop_links` kobler `stop_id = 2` (“Elverum ungdomsskole
(EUS)”) til både overnatningsskolen EUS (`lodging_school_id = 1`) og hallen
Elverumshallen (`schedule_hall_id = 1`).

### 4.2 Overnatningstabeller

| Tabel | Rækker | Noter |
|-------|--------|-------|
| `lodging_schools` | 4 | Identisk med `schools` fra den oprindelige DB. |
| `lodging_clubs` | 29 | Klubnavne per skole. |
| `lodging_teams` | 62 | Kopieret fra `teams` og brugt til alias-matching. |
| `lodging_rooms` | 68 | Rumkoder. |
| `lodging_team_rooms` | 70 | Relation hold↔rum. |
| `lodging_team_squads` | 80 | Squads med `squad_index`. |

### 4.3 Turneringstabeller

| Tabel | Rækker | Noter |
|-------|--------|-------|
| `schedule_event_days` | 3 | Datoer med service-dagskode (`fri/sat/sun`). |
| `schedule_halls` | 12 | Alle spillehaller. |
| `schedule_tournaments` | 19 | Alder/klasse inkl. køn. |
| `schedule_teams` | 80 | Kampnavne (fx “AFSK”). |
| `schedule_games` | 368 | Kampprogrammet inkl. `home_team_id` og `away_team_id`. |

### 4.4 Alias og logistiktabeller

| Tabel | Rækker | Noter |
|-------|--------|-------|
| `team_aliases` | 80 | Matcher 1:1 mellem `lodging_team_squads` og `schedule_teams`. |
| `logistics_events` | 2 | De faste begivenheder: lørdagsfrokost og koncert. |
| `team_itinerary_segments` | 1 977 | Udvidet tidslinje per alias (bus, kamp, frokost, koncert, charter). |

**Eksempel:** Alias 5 (“Furnes – G2014,2 lag”) har 25 segmenter, inkl. tre
charterbusser på søndag (`route_id` NULL, note “Charter transport…”).

### 4.5 Centrale views

| View | Rækker | Funktion |
|------|--------|----------|
| `vw_team_alignment` | 80 | Samler klubbens overnatningsdata med kampnavne og rum. |
| `vw_team_games` | 955 | Kampliste pr. alias/squad inkl. dag, modstander og rolle. |
| `vw_team_itinerary_flat` | 1 977 | Flad tidslinje til PDF-udtræk (rute, stop, buffer, noter). |
| `vw_team_game_sequence` | 955 | Kampe med afstanden til forrige/næste kamp (minutter). |
| `vw_bus_load_summary` | 328 | Headcount per busafgang (samlet fra `team_itinerary_segments`). |
| `vw_manual_transport_needs` | 378 | Segmenter der kræver charter/manuel håndtering. |
| `vw_logistics_events` | 2 | Convenience-view for lunch/koncert parametre. |
| `vw_transport_trip_instances` | 799 | Alle ture med `trip_index` til routingalgoritmen. |

**Eksempel på view-data:** Første række i `vw_team_itinerary_flat` er alias 1
(AFSK) med en lørdagsbus fra EUS til Søndre Elverum kl. 08:00 (planlagt ankomst
07:50, buffer 131 minutter).

### 4.6 Sammenfatning og relationer

1. **Transport → Overnatning/Haller:** `transport_stop_links` binder stoppesteder
   til skoler og haller, hvilket gør det muligt at udlede start- og slutstop for
   alle rejser.
2. **Lodging → Tournament:** `team_aliases` binder squads til turneringshold,
   hvilket er fundamentet for kampplan og transportberegninger.
3. **Itineraries:** `generate_itineraries.py` sletter/indsætter i
   `team_itinerary_segments` og danner bus-, kamp-, frokost- og koncertsegmenter.
   Resultatet bruges direkte i views til PDF-generatoren.
4. **Kapacitet:** `vw_bus_load_summary` summerer headcount pr. `service_day`
   + `route_id` + `trip_index` for at opdage belastning pr. tur (ingen kører
   over 120 personer i den nuværende datafil).

### 4.7 Nøglestatistikker

- 80 alias-id’er (alle squads matcher et turneringshold).
- 368 kampe fordelt på tre eventdage.
- 1 977 segmenter i tidslinjen, heraf 378 charter-noter og 21 frokostsegmenter.
- 799 unikke busafgangsregistreringer, fordelt på tre ruter.

## 5. Praktiske forespørgsler

- **Liste over kommende kampe for alias 3 (Borgen):**
  ```sql
  SELECT date, start_time, hall_name, opponent_name
  FROM vw_team_games
  WHERE alias_id = 3
  ORDER BY date, start_time;
  ```
- **Busbelastning på lørdag for Rute 1:**
  ```sql
  SELECT trip_index, estimated_headcount
  FROM vw_bus_load_summary
  WHERE service_day = 'sat' AND route_number = 1
  ORDER BY trip_index;
  ```
- **Segmenttidslinje til PDF for alias 5:**
  ```sql
  SELECT sequence_no, segment_type, start_time, end_time, notes
  FROM vw_team_itinerary_flat
  WHERE alias_id = 5
  ORDER BY sequence_no;
  ```

Disse forespørgsler er verificeret mod de aktuelle data og returnerer de
eksempler, der er gengivet ovenfor.


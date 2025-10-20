# Database Schema Overview

## lodging_clubs

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| club_id | INTEGER | False |  | True |
| school_id | INTEGER | True |  | False |
| name | TEXT | True |  | False |

**Foreign Keys**

| Column | References |
|--------|-----------|
| school_id | lodging_schools.school_id |

## lodging_rooms

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| room_id | INTEGER | False |  | True |
| school_id | INTEGER | True |  | False |
| room_code | TEXT | True |  | False |

**Foreign Keys**

| Column | References |
|--------|-----------|
| school_id | lodging_schools.school_id |

## lodging_schools

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| school_id | INTEGER | False |  | True |
| name | TEXT | True |  | False |

## lodging_team_rooms

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| team_id | INTEGER | True |  | True |
| room_id | INTEGER | True |  | True |

**Foreign Keys**

| Column | References |
|--------|-----------|
| room_id | lodging_rooms.room_id |
| team_id | lodging_teams.team_id |

## lodging_team_squads

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| squad_id | INTEGER | False |  | True |
| team_id | INTEGER | True |  | False |
| squad_index | INTEGER | True |  | False |

**Foreign Keys**

| Column | References |
|--------|-----------|
| team_id | lodging_teams.team_id |

## lodging_teams

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| team_id | INTEGER | False |  | True |
| club_id | INTEGER | True |  | False |
| raw_label | TEXT | True |  | False |
| gender | TEXT | False |  | False |
| year | INTEGER | False |  | False |
| num_teams | INTEGER | False |  | False |
| headcount | INTEGER | False |  | False |
| room_text | TEXT | False |  | False |
| division_key | TEXT | False |  | False |

**Foreign Keys**

| Column | References |
|--------|-----------|
| club_id | lodging_clubs.club_id |

## schedule_event_days

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| day_id | INTEGER | False |  | True |
| date | TEXT | True |  | False |
| label | TEXT | True |  | False |

## schedule_games

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| game_id | INTEGER | False |  | True |
| tournament_id | INTEGER | True |  | False |
| hall_id | INTEGER | True |  | False |
| day_id | INTEGER | True |  | False |
| match_code | TEXT | False |  | False |
| start_time | TEXT | True |  | False |
| home_team_id | INTEGER | True |  | False |
| away_team_id | INTEGER | True |  | False |

**Foreign Keys**

| Column | References |
|--------|-----------|
| away_team_id | schedule_teams.team_id |
| home_team_id | schedule_teams.team_id |
| day_id | schedule_event_days.day_id |
| hall_id | schedule_halls.hall_id |
| tournament_id | schedule_tournaments.tournament_id |

## schedule_halls

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| hall_id | INTEGER | False |  | True |
| name | TEXT | True |  | False |

## schedule_teams

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| team_id | INTEGER | False |  | True |
| name | TEXT | True |  | False |

## schedule_tournaments

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| tournament_id | INTEGER | False |  | True |
| name | TEXT | True |  | False |
| gender | TEXT | False |  | False |
| age | INTEGER | False |  | False |
| birth_year | INTEGER | False |  | False |
| pool_code | TEXT | False |  | False |

## sqlite_sequence

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| name |  | False |  | False |
| seq |  | False |  | False |

## team_aliases

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| alias_id | INTEGER | False |  | True |
| lodging_team_id | INTEGER | False |  | False |
| schedule_team_id | INTEGER | False |  | False |
| squad_index | INTEGER | False |  | False |
| note | TEXT | False |  | False |

**Foreign Keys**

| Column | References |
|--------|-----------|
| schedule_team_id | schedule_teams.team_id |
| lodging_team_id | lodging_teams.team_id |

## logistics_events

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| event_id | INTEGER | False |  | True |
| name | TEXT | True |  | False |
| event_type | TEXT | True |  | False |
| service_day | TEXT | True |  | False |
| start_time | TEXT | True |  | False |
| end_time | TEXT | True |  | False |
| anchor_stop_id | INTEGER | True |  | False |
| notes | TEXT | False |  | False |

**Foreign Keys**

| Column | References |
|--------|-----------|
| anchor_stop_id | transport_stops.stop_id |

## team_itinerary_segments

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| segment_id | INTEGER | False |  | True |
| alias_id | INTEGER | True |  | False |
| sequence_no | INTEGER | True |  | False |
| segment_type | TEXT | True |  | False |
| ref_type | TEXT | False |  | False |
| ref_id | INTEGER | False |  | False |
| service_day | TEXT | False |  | False |
| start_time | TEXT | False |  | False |
| end_time | TEXT | False |  | False |
| origin_stop_id | INTEGER | False |  | False |
| destination_stop_id | INTEGER | False |  | False |
| travel_minutes | INTEGER | False |  | False |
| buffer_minutes | INTEGER | False |  | False |
| route_id | INTEGER | False |  | False |
| trip_index | INTEGER | False |  | False |
| departure_route_stop_time_id | INTEGER | False |  | False |
| arrival_route_stop_time_id | INTEGER | False |  | False |
| notes | TEXT | False |  | False |

**Foreign Keys**

| Column | References |
|--------|-----------|
| alias_id | team_aliases.alias_id |
| origin_stop_id | transport_stops.stop_id |
| destination_stop_id | transport_stops.stop_id |
| route_id | transport_routes.route_id |

## transport_route_stop_times

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| route_stop_time_id | INTEGER | False |  | True |
| route_id | INTEGER | True |  | False |
| stop_id | INTEGER | True |  | False |
| stop_order | INTEGER | True |  | False |
| service_day | TEXT | True |  | False |
| departure_time | TEXT | True |  | False |
| condition_note | TEXT | False |  | False |

**Foreign Keys**

| Column | References |
|--------|-----------|
| stop_id | transport_stops.stop_id |
| route_id | transport_routes.route_id |

## transport_route_stops

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| route_stop_id | INTEGER | False |  | True |
| route_id | INTEGER | True |  | False |
| stop_id | INTEGER | True |  | False |
| stop_order | INTEGER | True |  | False |
| default_offset_min | INTEGER | False |  | False |

**Foreign Keys**

| Column | References |
|--------|-----------|
| stop_id | transport_stops.stop_id |
| route_id | transport_routes.route_id |

## transport_routes

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| route_id | INTEGER | False |  | True |
| route_number | INTEGER | True |  | False |
| title | TEXT | True |  | False |
| frequency_note | TEXT | False |  | False |
| extra_notes | TEXT | False |  | False |

## transport_stop_links

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| stop_id | INTEGER | False |  | True |
| lodging_school_id | INTEGER | False |  | False |
| schedule_hall_id | INTEGER | False |  | False |

**Foreign Keys**

| Column | References |
|--------|-----------|
| schedule_hall_id | schedule_halls.hall_id |
| lodging_school_id | lodging_schools.school_id |
| stop_id | transport_stops.stop_id |

## transport_stops

| Column | Type | Not Null | Default | PK |
|--------|------|----------|---------|----|
| stop_id | INTEGER | False |  | True |
| stop_name | TEXT | True |  | False |
| display_name | TEXT | True |  | False |
| description | TEXT | False |  | False |

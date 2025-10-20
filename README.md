# Elverum Youth Championship - Tournament Planning System

Automated system for generating personalized itineraries for 80 handball teams attending the Elverum Youth Championship (EYC) tournament on April 25-27, 2025.

## Quick Start

### Generate All PDFs

```bash
# Run the complete pipeline
python3 scripts/build_bus_routes.py
python3 scripts/build_lodging.py
python3 scripts/build_tournament.py
python3 scripts/build_event_db.py
python3 scripts/map_team_aliases.py
python3 scripts/generate_itineraries.py
python3 scripts/generate_all_pdfs.py
```

**Output:** 80 PDFs in `output/itineraries/` directory

### Verify Everything Works

```bash
python3 tests/integrity_checks.py
```

## What This System Does

Creates personalized PDF plans for each team showing:

- ✅ **Transport schedules** - Bus routes, times, stops
- ✅ **Game schedule** - All matches with opponents and venues
- ✅ **Lodging info** - School, room assignments, headcount
- ✅ **Lunch time** - Saturday 13:00-17:30 at Thon Central
- ✅ **Concert** - Saturday 19:30-21:00 at Terningen Arena
- ✅ **40-minute buffer** - Guaranteed arrival time before each game

## Project Structure

```
elverum/
├── data/
│   ├── build/           # Generated databases
│   │   ├── event_planner.db    # Main database
│   │   ├── bus_routes.db
│   │   ├── lodging.db
│   │   └── tournament.db
│   └── raw/             # Source data extracts
├── scripts/
│   ├── build_*.py       # ETL pipeline scripts
│   ├── generate_itineraries.py  # Core scheduling algorithm
│   ├── render_pdf.py    # PDF generation
│   └── generate_all_pdfs.py     # Batch PDF generator
├── tests/               # Validation tests
├── output/
│   └── itineraries/     # 80 generated PDFs
├── docs/                # Documentation
├── images/              # Raw data screenshots for validation
├── CLAUDE.md            # AI assistant guide
└── DELIVERY_SUMMARY.md  # Complete project summary
```

## Key Features

### Data Integration

Combines three data sources:
1. **Bus schedules** (`bussruter-eyc (1).pdf`) - 3 routes with full timetables
2. **Lodging** (`Overnatningsoversigt (1).docx`) - 62 teams across 4 schools
3. **Tournament schedule** (`Kampoppsett EYC 25 - 27 april 2025 (1).xlsx`) - 368 games

### Smart Scheduling

- **40-minute buffer:** All bus departures selected to arrive ≥40 min before game start
- **Multi-squad support:** Clubs with multiple teams get separate PDFs (e.g., "Furnes" and "Furnes 2")
- **Capacity tracking:** Monitors bus passenger loads (120-person limit)
- **Charter detection:** Identifies 357 segments needing charter buses

### Quality Assurance

- 100% team matching (80/80 lodging squads → tournament teams)
- All tests pass against raw source images
- Data verified against screenshots in `images/` folder

## Generated PDFs

**Sample teams:**
- AFSK (Aurskog Finstadbru J2008) - alias_id 1
- Bjørkelangen/Høland (J2013) - alias_id 2
- Røros (5 different squads) - aliases 47-52
- Sverresborg (7 different squads) - aliases 59-67

**View single team:**
```bash
python3 scripts/export_itinerary.py --alias-id 1
```

**Generate single PDF:**
```bash
python3 scripts/render_pdf.py --alias-id 1 --output output/itineraries
```

## Database Schema

Main database: `data/build/event_planner.db`

**Key tables:**
- `transport_*` - Bus routes, stops, schedules
- `lodging_*` - Schools, clubs, teams, rooms
- `schedule_*` - Tournaments, games, halls
- `team_aliases` - Links lodging teams to tournament teams
- `team_itinerary_segments` - Generated travel plans
- `logistics_events` - Lunch and concert schedules

**Key views:**
- `vw_team_alignment` - Complete team roster
- `vw_team_games` - Per-team game schedule
- `vw_team_itinerary_flat` - Timeline for PDF generation
- `vw_manual_transport_needs` - Charter bus requirements
- `vw_bus_load_summary` - Passenger counts per trip

## Requirements Met

From `projekt.md` and `mail.md`:

| Requirement | Status |
|------------|--------|
| Individual PDF per team | ✅ 80 PDFs |
| 40-min buffer before games | ✅ All verified |
| Transport using official bus plan | ✅ Routes 1, 2, 3 |
| Saturday lunch (13:00-17:30) | ✅ Thon Central |
| Saturday concert (19:30-21:00) | ✅ Terningen Arena |
| Lodging details | ✅ School, rooms, headcount |
| Bus stop names and routes | ✅ Complete |
| Multi-squad clubs separate | ✅ E.g., "Furnes" + "Furnes 2" |

## Known Issues

**Charter Transport Needs:** 357 segments require charter buses:
- Friday: 17 (late games from Frydenlund/Ydalir)
- Saturday: 112 (concert transport after late games)
- Sunday: 228 (inter-hall transfers, early games)

See [docs/manual_transport_needs.md](docs/manual_transport_needs.md) for details and recommendations.

## Testing

```bash
# Run all tests
python3 tests/test_raw_data_alignment.py
python3 tests/test_bus_routes.py
python3 tests/test_lodging.py
python3 tests/test_tournament.py
python3 tests/test_alignment.py
python3 tests/test_itinerary_views.py
python3 tests/integrity_checks.py
```

All tests validate against raw source images in `images/` folder.

## Documentation

- **[DELIVERY_SUMMARY.md](DELIVERY_SUMMARY.md)** - Complete project summary
- **[CLAUDE.md](CLAUDE.md)** - Comprehensive guide for AI assistants
- **[docs/etl_overview.md](docs/etl_overview.md)** - Data pipeline details
- **[docs/schema_overview.md](docs/schema_overview.md)** - Database schema
- **[docs/developer_launch.md](docs/developer_launch.md)** - Developer quick start
- **[docs/status.md](docs/status.md)** - Project status log
- **[docs/manual_transport_needs.md](docs/manual_transport_needs.md)** - Charter requirements

## Dependencies

```bash
# Required for PDF generation
pip install fpdf2

# Or with system packages flag
pip install --break-system-packages fpdf2
```

Python 3.11+ required.

## Support

For questions or issues:
1. Check documentation in `docs/` folder
2. Review [CLAUDE.md](CLAUDE.md) for architecture details
3. Run `python3 tests/integrity_checks.py` to verify data

## License & Usage

Created for Elverum Håndball Youth Championship 2025.

---

**Status:** ✅ Complete - All 80 team itineraries generated
**Last updated:** 2025-10-11

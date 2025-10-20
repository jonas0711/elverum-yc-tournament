# TO DO

- Model club → team relationships with explicit age-group and squad identifiers so each club can host multiple teams across different brackets (including multiple squads in the same age group). Extract age metadata consistently from both lodging data (`raw_label`) and tournament team names to support aliasing.
- Capture lodging assignments per individual team, ensuring every itinerary generated later references the correct school/room for that specific squad.
- Maintain `team_aliases` coverage; after the latest heuristik står alle 80 squads matchet, så nye klubnavne/ændringer skal blot tilføjes i alias-mappingen.
- Iteration on `scripts/generate_itineraries.py`: håndter multi-leg chartererstatning (koncertshuttle, søndagsmorgen loops) så posterne i `vw_manual_transport_needs` kan reduceres/elimineres.
- Indbyg kapacitetsregler baseret på `vw_bus_load_summary` (sæt max pr. busafgang, fordel squads på alternative ruter/afgange hvor nødvendigt).
- Design PDF-generator og layout der præsenterer `team_itinerary_segments` med tydelig tidslinje, businformation, buffere og noter til holdene.

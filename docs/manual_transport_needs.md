# Manual Transport Needs (Generated 2025-04-08)

## Summary
- **Total charter/special segments:** 357  
- **Breakdown:** 17 (fredag), 112 (lørdag), 228 (søndag)
- Disse segmenter svarer til `route_id IS NULL` i `team_itinerary_segments` og eksponeres via `vw_manual_transport_needs`.

## Fredag (17 segmenter)
- Små grupper: Frydenlund/Ydalir → Elverumshallen (kampstart sent fredag aften).  
  *Løsning*: planlæg shuttle eller koordinér med klubberne om mindre minibusser.

## Lørdag (112 segmenter)
- **Koncerttransport (rest):**  
  - 7 × Søndre Elverum → Terningen Arena (efter sen eftermiddagskamp).  
  - 4 × Herneshallen/Ydalir → Terningen Arena.  
  *Anbefaling*: Koordiner dedikerede charterafgange omkring 17:30–18:15 for de sidste hold (ingen nye offentlige ruter må oprettes).
- **Mellemhals-flows:** Få resterende ture Ydalir → Elvishallen (alias 59/61/62/63/64/66) – typisk direkte efter kamp før koncert.  
  *Løsning*: Planlæg kortvarig charter/minibus mellem Ydalir og Elvishallen for disse specifikke hold.

## Søndag (228 segmenter)
- Mellem Ydalir/Søndre ↔ EUS/ELVIS/Herneshallen – hovedsageligt midt på dagen.  
  *Anbefaling*: Planlæg dedikerede charterafgange (fx kl. 15:00 og 16:00) mellem Ydalir/Søndre og EUS/ELVIS for at dække disse overgange.  
- Få chartere Terningen → EUS efter slutspel; koordiner dedikeret retur eller opjustér rute 96.

## Tiltag & Næste skridt
1. **Koncertshuttle** – vurder ekstra afgange (eller større bus) for Søndre/Hernes/Ydalir kl. 17:30–18:10.  
2. **Søndagsloop** – analyser `vw_manual_transport_needs` dagligen og planlæg flere direkte ture (Ydalir/Frydenlund → EUS/Hernes) hvis kampstart <09:00.  
3. **Kommunikation** – informér berørte klubber om planlagte charters og saml feedback på kapacitet/ankomsttider.  
4. **Automatisering** – når shuttleplan er bekræftet, indlæs tiderne i `build_event_db.py` så generatoren erstatter de resterende charters med regulære afgange.

> Brug `python3 scripts/export_itinerary.py --alias-id <ID>` for at se den fulde plan inkl. chartersegmenter pr. hold.

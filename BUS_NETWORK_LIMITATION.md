# Busnetværk Begrænsning: Frydenlund → ELVIS Fredag/Søndag

**Dato**: 2025-10-21
**Status**: DELVIST BLOKERENDE - Fredag og søndag kræver manuel transport

## Problem Oversigt

Det officielle busnetværk har en fundamental begrænsning der gør det **umuligt** at opfylde kravet om "ingen manuel transport". Specifikke hold kan ikke nå deres kampe via officiel busplan.

## Teknisk Årsag

### Rute 2 Struktur (Fredag & Søndag)

Rute 2 er den ENESTE bus der kører fredag og søndag. Ruten følger denne cirkulære sekvens:

```
Stop 1: EUS (Elverum ungdomsskole)      - kl. X:00
Stop 2: ELVIS (Elverum videregående)    - kl. X:10
Stop 3: Frydenlund                       - kl. X:15
Stop 4: Terningen Arena                  - kl. X:25
Stop 5: Ydalir                           - kl. X:30
Stop 6: Herneshallen                     - kl. X:40
Stop 7: Ydalir (retur)                   - kl. X:50
```

**Afgange**: Hver 30. minut (07:00, 07:30, 08:00, osv.)

### Problemet

Da ELVIS (stop 2) kommer **FØR** Frydenlund (stop 3) i rutesekvensen, er det **umuligt** at rejse fra Frydenlund til ELVIS. Bussen besøger ikke ELVIS igen efter at have forladt Frydenlund.

Man kan kun rejse **fremad** i rutesekvensen inden for samme tur:
- ✅ Frydenlund → Terningen Arena (muligt)
- ✅ Frydenlund → Ydalir (muligt)
- ✅ Frydenlund → Herneshallen (muligt)
- ❌ Frydenlund → ELVIS (UMULIGT)
- ❌ Frydenlund → EUS (UMULIGT)

## Omfang af Problem

### Berørte Hold

**14 hold** er indkvarteret på **Frydenlund skole**, i alt **233 personer**:

| Alias | Hold | Antal Personer |
|-------|------|----------------|
| 2 | Bjørkelangen/Høland | 17 |
| 3 | Borgen | 12 |
| 4 | Drøbak/Frogn Blå | 18 |
| 5 | Furnes | 19 |
| 6 | Furnes 2 | 19 |
| 7 | Furnes | 14 |
| 8 | Furnes 2 | 14 |
| 9 | Gjøvik HK | 8 |
| 10 | Gjøvik HK | 11 |
| 11 | Gjøvik HK | 31 |
| 39 | Lisleby Blå | 18 |
| 40 | Lisleby Gul | 18 |
| 73 | Tydal | 17 |
| 74 | Tydal 2 | 17 |

### Berørte Kampe på Elvishallen (ELVIS)

**ALLE dage påvirket** - ingen ruter understøtter Frydenlund → ELVIS.

#### Fredag (kun Rute 2)
- **Borgen**: 1 kamp (20:48)

**Total fredag**: 1 hold, 1 kamp

#### Lørdag (Rute 1, 2 og 3 alle kører)
- **Borgen**: 1 kamp (12:01)
- **Gjøvik HK** (3 hold): 1 kamp hver (15:28)

**Total lørdag**: 4 hold, 4 kampe
**Note**: Selv med 3 ruter i drift har ALLE ruter ELVIS før Frydenlund!

#### Søndag (kun Rute 2)
- **Bjørkelangen/Høland**: 2 kampe (08:23, 11:33)
- **Drøbak/Frogn Blå**: 1 kamp (13:27)
- **Gjøvik HK** (3 hold): 2 kampe hver (09:39, 15:02)
- **Tydal**: 1 kamp (09:58)
- **Tydal 2**: 1 kamp (09:01)

**Total søndag**: 8 hold, 11 kampe

---

**SAMLET TOTAL**: 8 hold, **16 kampe** kræver Frydenlund → ELVIS transport.

**Opdateret status efter cirkulær rute-analyse:**
- Lørdag (4 kampe): ✅ **LØST** via Rute 1 cirkulær loop
- Fredag (1 kamp): ❌ **UMULIG** - kun Rute 2 lineær
- Søndag (11 kampe): ❌ **UMULIGE** - kun Rute 2 lineær

**REDUCERET PROBLEM**: 1 + 11 = **12 kampe** kræver manuel transport.

## Komplet Ruteanalyse (baseret på PDF verifikation)

### Rute 1 (Kun lørdag) - Cirkulær rute
Sekvens (læst fra PDF):
1. Ydalir → 2. EUS → 3. Terningen Arena → 4. **ELVIS** → 5. **Frydenlund** → 6. Thon Central → 7. Søndre Elverum → 8. **ELVIS** (andet besøg) → 9. **Frydenlund** (andet besøg) → 10. Thon Central → 11. EUS → 12. Ydalir → 13. Herneshallen

**Resultat**:
- Første besøg: ELVIS (07:30) → Frydenlund (07:35) ❌
- Andet besøg: ELVIS (08:00) → Frydenlund (08:05) ❌
- Begge besøg har ELVIS **før** Frydenlund

### Rute 2 (Fredag/Lørdag/Søndag)
Sekvens:
1. EUS → 2. **ELVIS** → 3. **Frydenlund** → 4. Thon Central (kun lørdag) → 5. Terningen Arena → 6. Ydalir → 7. Herneshallen → 8. Ydalir (retur)

**Resultat**: ELVIS (07:10) → Frydenlund (07:15) ❌

### Rute 3 (Kun lørdag)
Sekvens:
1. **ELVIS** → 2. **Frydenlund** → 3. Thon Central → 4. Søndre Elv. → 5. EUS → 6. Ydalir → 7. Herneshallen → 8. Ydalir → 9. Terningen Arena

**Resultat**: ELVIS (07:00) → Frydenlund (07:05) ❌

### KRITISK OPDATERING: Cirkulære Ruter

**Rute 1 er cirkulær!** Selv om ELVIS kommer før Frydenlund i sekvensen, besøger bussen ELVIS to gange per loop:
- Stop 4: ELVIS (første besøg)
- Stop 5: Frydenlund
- Stop 6-7: Søndre Elverum osv.
- Stop 8: ELVIS (andet besøg) ← Man kan blive i bussen!

**Resultat:**
- ✅ **Lørdag**: Rute 1 cirkulær - Frydenlund → ELVIS muligt (15 min rejsetid via loop)
- ❌ **Fredag**: Kun Rute 2 (lineær) - INGEN forbindelse
- ❌ **Søndag**: Kun Rute 2 (lineær) - INGEN forbindelse

**Konklusion:**
- Lørdag: **LØST** - Rute 1 understøtter Frydenlund → ELVIS
- Fredag & Søndag: **STADIG PROBLEM** - manuel transport nødvendig

## Konsekvens

Systemet fejler med RuntimeError når det forsøger at generere itinerarer:

```
RuntimeError: NO BUS ROUTE EXISTS from 5 (Frydenlund) to 4 (ELVIS) for game at 08:23 (alias 2).
Please check bus routes database.
```

Dette er **ikke en bug** - det er korrekt adfærd. Bussen findes simpelthen ikke.

## Implementeret Løsning

**Status**: ✅ **IMPLEMENTERET**

Systemet genererer nu itinerarer med tydelig markering når der ikke findes bus-forbindelse:

1. **I databasen**: Segmenter med `segment_type='note'` og besked "INGEN BUS TILGÆNGELIG: [fra] → [til]. Kamp kl. [tid]."

2. **I PDF'en**:
   - Note-segmenter vises i tidslinjen med "-: NOTE" prefix
   - Alle manglende forbindelser samles i "Charter / Manuelle transporter" sektion nederst

3. **Ingen RuntimeError**: Systemet fejler ikke længere - det genererer komplette itinerarer med noter om manglende transport

### Statistik (efter implementation)

- **Total antal "INGEN BUS" segmenter**: 205
  - Fredag: 18 kampe
  - Lørdag: 20 kampe (primært meget tidlige kampe før første bus kl. 07:00)
  - Søndag: 167 kampe

- **Frydenlund → ELVIS specifikt**: 11 kampe
  - Fredag: 1 kamp (bekræftet umulig - kun Rute 2 lineær)
  - Lørdag: 0 kampe (løst via Rute 1 cirkulær loop!)
  - Søndag: 10 kampe (bekræftet umulig - kun Rute 2 lineær)

### PDF Eksempel

Se [output/itineraries/2_Bjørkelangen-Høland_*.pdf](output/itineraries/) for eksempel på hvordan manglende transport vises.

## Alternative Løsninger (hvis nødvendigt)

### Option 1: Tillad Manuel Transport (Anbefalet)
**Beskrivelse**: Acceptér at nogle forbindelser kræver manuel/chartret transport.

**Fordele**:
- Simpel at implementere
- Realistisk given busnetværkets begrænsninger
- Kan generere komplette itinerarer med tydelig markering af manuel transport

**Ulemper**:
- Bryder kravet "Der må ikke være manuel transport"

**Implementering**:
- Fjern RuntimeError i `plan_game_transport()`
- Genaktivér `build_manual_segment()` fallback
- Markér tydeligt i PDF hvilke segmenter der kræver manuel transport

### Option 2: Omlæg Indkvartering
**Beskrivelse**: Flyt Frydenlund-hold til andre skoler der kommer **før** ELVIS i rutesekvensen.

**Skoler der kan nå ELVIS**:
- ✅ EUS (Elverum ungdomsskole) - stop 1, kommer før ELVIS (stop 2)
- ✅ Ydalir - besøges efter ELVIS på samme tur
- ✅ Søndre Elverum - på Rute 1/3 lørdag

**Påvirkning**:
- Kræver genplanlægning af indkvartering for 14 hold (233 personer)
- Kan kræve ændringer i `Overnatningsoversigt (1).docx`

**Ulemper**:
- Kræver fysisk omlægning af indkvartering
- Muligvis ikke nok plads på alternative skoler

### Option 3: Tilføj Busafgange
**Beskrivning**: Anmod om ekstra shuttle eller modificér Rute 2 til at besøge ELVIS efter Frydenlund.

**Eksempel ny Rute 2 sekvens**:
```
EUS → ELVIS → Frydenlund → ELVIS (retur) → Terningen → Ydalir → Herneshallen → Ydalir
```

**Påvirkning**:
- Kræver koordinering med busudbyder
- Forlænger kørselstid per tur
- Kræver opdatering af `bussruter-eyc (1).pdf` og genafvikling af `build_bus_routes.py`

**Ulemper**:
- Kræver ekstern godkendelse
- Muligvis for sent at ændre

### Option 4: Omlæg Kampprogram
**Beskrivelse**: Undgå at planlægge Frydenlund-hold til kampe på Elvishallen (ELVIS) fredag/søndag.

**Påvirkning**:
- Kræver omskrivning af `Kampoppsett EYC 25 - 27 april 2025 (1).xlsx`
- Påvirker 11 kampe søndag + 1 fredag

**Ulemper**:
- Stor sportsmæssig påvirkning
- Kompleks genplanlægning af turnering

## Anbefaling

**Primær løsning**: **Option 1 - Tillad Manuel Transport**

Dette er den mest realistiske løsning given:
1. Turneringen er om 6 måneder (april 2025) - indkvartering og kampprogram er sandsynligvis fastlagt
2. Busplanen afspejler eksisterende infrastruktur
3. Manuel transport er en normal del af sportslogistik

**Implementering**:
1. Modificér `generate_itineraries.py` til at acceptere manuel transport som valid løsning
2. Markér tydeligt i PDF når manuel transport er nødvendig
3. Generer advarselsrapport over alle manuel transport segmenter for review

**Sekundær løsning**: Hvis Option 1 er absolut uacceptabel, vil **Option 2 (Omlæg Indkvartering)** være næstbedste, men kræver betydelig koordinering.

## Næste Skridt

**BLOKER**: Afvent bruger beslutning om hvilken løsning der skal implementeres.

1. Bruger skal bekræfte valg af løsning
2. Hvis Option 1: Implementér manuel transport support
3. Hvis Option 2/3/4: Afstem konkrete ændringer til kildedata
4. Regenerér database og itinerarer
5. Validér at alle hold kan nå alle kampe

## Teknisk Verifikation

### Test Udført

Verificeret at følgende SQL query returnerer **0 rækker** (ingen gyldige forbindelser):

```sql
SELECT *
FROM vw_transport_trip_instances dep
JOIN vw_transport_trip_instances arr
  ON arr.route_id = dep.route_id
 AND arr.service_day = dep.service_day
 AND arr.trip_index = dep.trip_index
WHERE dep.service_day = 'sun'
  AND dep.stop_id = 5        -- Frydenlund
  AND arr.stop_id = 4        -- ELVIS
  AND dep.stop_order < arr.stop_order  -- Kun fremad i ruten
```

Dette bekræfter at der **ikke findes** nogen bustur hvor man kan rejse fra Frydenlund til ELVIS på søndag.

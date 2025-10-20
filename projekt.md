Grundlag: Læs altid @mail.md for at forstå grundlaget

Data:
Alle filer skal konverteres til SQL db. Som algoritmen trækker fra. Det skal ende med en hyper personaliserede plan på pdf til hvert hold. Dvs. også hvis der er et hold 1 og hold 2 for samme hold. Så skal hvert hold have en pdf, da de skal noget forskelligt.

Requirements:
- Kampe kobles til busplan (Minimum 40 min før kampsstart ift. ankomst)
- Lunch skal beregnes på bedst muligt tidspunkt for det individuelle hold indenfor tidsrum
    - Obs. kørsel til Lunch skal være fra den hal man lige har spillet kamp i, medmindre man ikke har spillet kamp. Så skal det være fra overnatngingssted.
- Koncert og transport til den skal med i planen
- Overnatningssted skal med
- Transport mellem haller skal med hvis man skifter hal at spille i
- Alle hold skal have deres egen.
- PDF, skal være let overskuelig og tilpasset det enkelte hold
- Busrute og busstopsteder skal med
- Alt rådata, skal laves til en stor db med sammenhænge man kan hente fra
    - Rådata: @bussruter-eyc (1).pdf , @Overnatningsoversigt (1).docx , @Kampoppsett EYC 25 - 27 april 2025 (1).xlsx
- Færdiggør og tilpas alle planer som har været igang: @overnatningssted_plan_creation.md , @tournament_plan_creation.md , @bus_plan_creation.md
    - Sammenlig db så det bliver en stor relationel db

Eksempel på output (kort version)

Hold: EH Aalborg U15 Piger
Overnatning: Skole 3
Fredag

Kamp 1: 10:40 – Elverum Hall 2
→ Afgang 09:25 med Bus 4 fra Skole 3
→ Ankomst 10:00

Kamp 2: 15:20 – Elverum Hall 1
→ Afgang 14:05 med Bus 4
→ Ankomst 14:40
Lørdag

Lunch: 14:20 Thon Central

Koncert: 19:30–21:00 Terningen Arena


End goal er:
PDF:
Jeg vil meget gerne gøre sådan at hvert hold har deres egen plan for turneringen, det vil sige at de har en lille oversigt over hvornår de skal med bussen for at være der min. 40 min før kampstart. Jeg har vedlagt en busplan, overnatningsoversigt og kampplan. Ydermere er der nogle ekstra ting man skal være opmærksom på i forhold til bespisning og koncert som holdene også skal transportere sig til.

PDF:
Derudover vil jeg gerne have en oversigt over hvor mange personer der er på enkelte busser i forhold til den oversigt der bliver lavet.


PDF:
Derudover må der også gerne genereres en plan over hvornår de forskellige hold spiser hvis det er muligt udfra hvornår de ankommer med bussen.

## 2025-10-11
- PDF skal vise en dagsopdelt oversigt over alle kampene for hvert hold, og transportbenene skal sikre ankomst minimum 40 minutter før kampstart (tidligere vejledende krav, nu eksplicit kontrolkrav).
- Al transport skal planlægges ud fra den officielle busplan; der må ikke opfindes ekstra ruter eller afgange.
- Lørdagsfrokosten skal placeres mellem 13:00 og 17:30 på Thon Central, med rejser fra seneste hal (eller overnatning hvis holdet er inaktivt), samt retur videre til næste aktivitet.
- Matchvarighed skal indregnes i frokostplanlægningen, så holdene realistisk kan nå både kampene og frokosten.
- Transport til og fra koncerten i Terningen Arena (26. april, 19:30–21:00) skal indgå i planerne.
- Overnatningsstedet styrer første morgentransport hver dag, så den første kamp nås tidsnok.

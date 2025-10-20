Brug gh cli

Du skal nu file et Github Issue. Følg best practises for github Issues:
Vigtigste elementer i en GitHub Issue
En god GitHub Issue skal være klar, konkret og handlingsorienteret. Her er de vigtigste elementer, du skal inkludere:​

Titel og beskrivelse
En beskrivende titel skal opsummere problemet kort og præcist, for eksempel "Bug: App crasher ved login-klik" eller "Feature: Tilføj søgefunktion til brugerside". Beskrivelsen skal give detaljeret kontekst, herunder hvad du forventede ville ske, og hvad der faktisk skete.​

Gentagelsessteps og tekniske detaljer
For bug-rapporter er det essentielt at inkludere trin-for-trin instruktioner til at genskabe problemet. Tilføj miljødetaljer som operativsystem, browser eller softwareversion. For eksempel:​

Åbn appen

Naviger til login-skærm

Klik login uden at indtaste legitimationsoplysninger​

Visuelle hjælpemidler
Screenshots, logs eller videoer kan hjælpe andre med hurtigt at forstå problemet. Disse visuelle elementer gør det lettere for andre udviklere at reproducere og løse issuen.​

Labels og struktur
Brug labels som "bug", "enhancement" eller "question" til at kategorisere issuen korrekt. For større opgaver kan du bruge markdown checklists til at opdele issuen i mindre tasks. Dette gør det lettere at tracke fremskridt og teste for succes.​

Foreslået løsning
Hvis du har en idé til, hvordan problemet kan løses, skal du inkludere den i issuen. Dette hjælper maintainers med at forstå dine tanker og kan fremskynde løsningen.​

Issue Templates
Brug issue templates for at sikre konsistens. Du kan oprette templates i .github/ISSUE_TEMPLATE mappen i dit repository med forskellige typer som bug report, feature request og documentation. Templates sikrer, at alle nødvendige informationer inkluderes hver gang.​

Søg før oprettelse
Før du opretter en ny issue, skal du søge efter eksisterende issues for at undgå dubletter. GitHub foreslår ikke automatisk dubletter, så manuel søgning er vigtig. Dette holder issue trackeren organiseret og fokuseret.​

Lukning og opfølgning
Når en issue er løst, skal du poste en final summary kommentar og derefter lukke den. Du kan bruge syntaksen Closes #issue_number i pull requests eller commits til automatisk at lukke relaterede issues.


Research også kodebasen for at finde alle relevant filer og mapper der kan hjælpe med at finde og løse fejlen. Dette er vores issue: 
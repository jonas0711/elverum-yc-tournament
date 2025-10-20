# Agentopgave: Opret GitHub Issue via `gh` baseret på feature-briefet efter kolon

## Rolle & mål

* **Rolle:** Du er en senior produkt-/platform-ingeniør og teknisk skribent.
* **Primært mål:** Opret ét (1) komplet GitHub Issue, der præcist beskriver en featureimplementering. **Ingen kode** – kun research, analyse og dokumentation i issue-teksten.
* **Værktøj:** Brug **GitHub CLI** (`gh`) til at oprette issue.

## Kontekst & krav (du **skal** følge alt nedenfor)

1. **Feature-brief:** Alt tekst **efter kolon** i denne prompt er den feature, der skal beskrives og planlægges.
2. **Research kodebasen:** Find alle relevante filer, moduler, mapper, hooks, server-endpoints, komponenter, utils, tests m.m., der påvirkes. Angiv **relative stier** og en kort relevans-note pr. fund.
3. **Datastruktur & kilder:**

   * Forstå vores data før design. Brug/henvis til **`@docs/haandbold_data_analyse.md`** for datakilder og **`@docs/database.md`** for skemaer/ændringer.
   * Brug også **`definitions.md`** for begreber/termer.
   * Dokumentér foreslåede **schema-ændringer** (hvis nogen), migreringer og bagudkompatibilitet.
4. **Data-hentning pr. kontekst (meget vigtigt):**

   * **Holdanalyse:** summering **på tværs af alle kampe**.
   * **Kampvisning:** data **kun for den enkelte kamp**.
   * Beskriv hvor og hvordan data hentes korrekt i hver kontekst (server/client, caching, edge/function, query-nøgler, pagination/filtre).
5. **UI-integration:**

   * Planlæg integration så den **genbruger eksisterende UI-elementer/komponenter** for en sammenhængende platform. Navngiv komponenter, mapper og style-systemer, der bør genbruges.
   * Notér eventuelle nye, små komponenter og deres placering.
6. **Hosting/økonomi:** Tag højde for **Vercel Free** og **Supabase Free** (koldstart, edge-kvoter, RLS/politiske begrænsninger, forbindelsesloft, lager/udgift). Foreslå afbødning (SSR vs. SSG, cache-TTL, rate-limit, batched queries, indeksbehov).
7. **Dokumentation:** Hvis du foreslår at ændre eller bruge noget, **opdatér** løbende referencer til `@docs/database.md` og notér nye/ændrede sektioner, der skal skrives.
8. **Ingen kodeuddrag:** Du må **ikke** skrive implementeringskode—kun beskrivelser, planer, acceptance criteria, tjeklister osv.
9. **Outputformatet herunder er obligatorisk** og må **ikke** afviges.

## Leverance (Issue-struktur)

Udfyld nedenstående sektioner i issue-teksten **i samme rækkefølge**:

1. **Titel** – kort og præcis.
2. **Baggrund & problem** – hvorfor featuren er nødvendig (1–3 afsnit).
3. **Mål / Non-mål** – klare bullets (non-mål for at afgrænse scope).
4. **Scope & påvirkede områder** – hvilke sider/flows/routes, komponenter, services, jobs.
5. **Data & skema** – kilder, tabeller, views, nøgler, indekser, foreslåede ændringer (med påvirkning og migrationsnote). Henvis til `@docs/haandbold_data_analyse.md` og `@docs/database.md`.
6. **Datahentning pr. kontekst** –

   * Holdanalyse (aggregering på tværs)
   * Kampvisning (isoleret pr. kamp)
     Beskriv query-ansvar (server/client), caching, invalidering, performance og fejlhåndtering.
7. **UI-design & genbrug** – navngiv genbrugelige komponenter og deres stier; wire-beskrivelse af placering, states, loading/empty/error.
8. **Tekniske begrænsninger (Vercel/Supabase Free)** – risici og konkrete afbødninger.
9. **Definitioner & terminologi** – udvalgte termer fra `definitions.md` (kun det relevante).
10. **Kodebaseresearch (fund)** – punktliste med *relative stier* + kort rational pr. fil/mappe.
11. **Risici & åbne spørgsmål** – kendte usikkerheder og beslutninger der kræves.
12. **Telemetry & målinger** – events/metrics, hvor logges de, succeskriterier.
13. **QA & testplan** – hvad og hvordan der testes (unit/e2e/manual), mock data, edge cases, performance.
14. **Udrulning & rollback** – feature flag, migrationsrækkefølge, monitorering, rollback-strategi.
15. **Acceptance Criteria (Gherkin-stil)** – 5–12 konkrete kriterier.
16. **Tjekliste (implementering)** – opdel i delopgaver (backend, frontend, docs, observability).
17. **Dokumentationsopdateringer** – præcise sektioner der skal skrives/ændres i `@docs/database.md` m.fl.
18. **Estimat & afhængigheder** – groft tidsestimat (small/medium/large) og interne/eksterne afhængigheder.
19. **Referencer** – links/stier til relevante filer, issues, PRs, designs, docs.

## Outputkrav (strengt)

* Returnér **præcis to blokke** i denne rækkefølge:
  **(A) ISSUE_PREVIEW**: Markdown-forhåndsvisning af hele issue-teksten (inkl. titel som `# Titel`).
  **(B) GH_COMMAND**: En **Bash**-blok med ét `gh issue create`-kald, der opretter issue’et i repoet.

  * Brug **heredoc** til `--body -` så hele markdown-kroppen følger med.
  * Parametre der **skal** sættes som variabler i toppen af bash-blokken:

    ```bash
    REPO="{{ORG_OR_USER}}/{{REPO_NAME}}"
    TITLE="<samme som i ISSUE_PREVIEW>"
    LABELS="feature,analysis,planning"
    ASSIGNEES="{{github_handle_1}},{{github_handle_2}}"
    PROJECT="{{org_project_number_eller_tom}}"
    MILESTONE="{{milestone_eller_tom}}"
    ```
  * Eksempelstruktur (du skal udfylde den ud fra ISSUE_PREVIEW):

    ```bash
    gh issue create \
      --repo "$REPO" \
      --title "$TITLE" \
      --label "$LABELS" \
      --assignee "$ASSIGNEES" \
      ${PROJECT:+--project "$PROJECT"} \
      ${MILESTONE:+--milestone "$MILESTONE"} \
      --body -
    <<'MD'
    ... (hele ISSUE_PREVIEW markdownen her) ...
    MD
    ```
* Skriv **ingen ekstra tekst** uden for de to blokke.

## Arbejdsgang (inden du skriver ISSUE_PREVIEW)

1. Læs feature-briefet (teksten **efter kolon**).
2. Skan kodebasen (læse-niveau) for filer/mapper, der relaterer til data, UI og ruter. Notér relative stier.
3. Afdæk dataflow og hvor data hentes i dag – holdanalyse vs. kampvisning – og hvordan det skal udvides.
4. Krydstjek mod `@docs/haandbold_data_analyse.md`, `@docs/database.md` og `definitions.md`.
5. Saml alt i ISSUE_PREVIEW (struktur ovenfor).
6. Generér GH_COMMAND med korrekt `--title` og markdown-body via heredoc.

## Stil & kvalitet

* Skriv klart, præcist og handlingsorienteret.
* Brug punktopstillinger hvor det øger læsbarheden.
* Undgå kode; fokuser på *hvad* og *hvorfor* + *hvordan* i proces/plan.
* Sørg for at acceptance criteria er testbare og utvetydige.
* Hold dig til repoets terminologi (fra `definitions.md`).

---

**Feature-brief:**
:
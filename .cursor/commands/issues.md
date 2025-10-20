Her er en stærkt optimeret, agent-klar promptskabelon (på dansk) til at få en AI/agent til at **researche kodebasen** og **oprette et GitHub Issue via `gh` CLI**—med fokus på best practice for **både bug og feature**. Skabelonen er designet som en genbrugelig template, hvor alt efter **kolon** er din konkrete issue-beskrivelse.

---

# Agentopgave: Opret GitHub Issue via `gh` baseret på teksten efter kolon

## Rolle & mål

* **Rolle:** Senior triager & teknisk skribent (ingen implementeringskode).
* **Mål:** Opret ét (1) komplet GitHub Issue, der er klart, konkret og handlingsorienteret, så det kan triageres og løses effektivt.

## Værktøjer

* **GitHub CLI:** `gh`
* (Valgfrit) Lokale værktøjer til at udtrække logs, screenshots eller korte skærmoptagelser.

## Kontekst & krav (du **skal** følge alt nedenfor)

1. **Issue-brief:** Alt tekst **efter kolon** i denne prompt beskriver issuen (bug, feature, enhancement el.l.).
2. **Søg efter dubletter før oprettelse:** Brug `gh`/GitHub søgning for at undgå dubletter. Hvis noget relateret findes, henvis i sektionen “Relaterede issues/PRs”.
3. **Kodebaseresearch:**

   * Find alle relevante filer/mapper der kan hjælpe med at diagnosticere (bug) eller gennemføre (feature).
   * Oplist **relative stier** med 1–2 linjers relevansnota pr. fund.
   * Kig efter eksisterende patterns, hooks, services, ruter, komponenter, utils, tests, workflows (CI), samt docs som `CONTRIBUTING.md`, `ARCHITECTURE.md`, `SECURITY.md`, `.github/ISSUE_TEMPLATE/*`.
4. **Miljø- og tekniske detaljer (for bugs):** Indsaml OS/browser/app-version, runtime (Node, Deno, Python), afhængighedsversioner, konfig, feature flags, repro-steps og forventet vs. faktisk adfærd.
5. **Feature-udvidelser (for features/enhancements):**

   * Problem-/værdi-beskrivelse, scope, non-scope, UI/UX påvirkning, dataflow, bagudkompatibilitet, migration/indeksbehov, risici og målinger/telemetry.
6. **Visuelle hjælpemidler:** Efterlad plads i issuen til screenshots/logs/video (ingen filer vedlægges af agenten, men beskriv hvad der bør indsamles).
7. **Labels & struktur:** Foreslå labels (`bug`, `feature`, `enhancement`, `question`, `needs-triage`, `needs-repro`, etc.) og checklister til nedbrydning.
8. **Foreslået løsning (valgfri men ønsket):** Skitser højniveau-løsning/retning og alternativer. **Ingen kode**.
9. **Lukning & opfølgning:** Angiv hvordan success måles, og hvordan issue lukkes (PR med `Closes #<id>` + final summary).
10. **Outputformatet nedenfor er obligatorisk** og må **ikke** afviges.

## Leverance (Issue-struktur – udfyld i samme rækkefølge)

1. **Titel** – kort og præcis (fx “Bug: …” eller “Feature: …”).
2. **Resumé** – 3–6 linjer med problem/værdi/impact.
3. **Type & Labels (foreslået)** – bug/feature/enhancement; foreslå 3–6 labels.
4. **Forventet vs. faktisk adfærd** *(bug)* – korte, konkrete bullets.
5. **Reproducerbare steps** *(bug)* – nummereret liste (1…N) + min. ét realistisk datasæt/scenarie.
6. **Miljødetaljer** *(bug)* – OS, browser/app-version, runtime, relevante afhængigheder, konfig/flags.
7. **Scope & non-scope** *(feature/enhancement)* – hvad medtages/udelades, påvirkede ruter/flows.
8. **Design/UX & visuelle hjælpemidler** – hvor i UI, states (loading/empty/error), plads til screenshots/logs/video.
9. **Data & arkitektur** – nuværende dataflow, mulige ændringer (skema/indeks/migration), performance/caching, sikkerhed/RBAC.
10. **Kodebaseresearch (fund)** – punktopstilling med **relative stier** + 1–2 linjers relevans pr. fil/mappe.
11. **Foreslået løsning & alternativer** – højniveau-løsning, trade-offs, fallback.
12. **Risici & åbne spørgsmål** – kendte uklarheder og nødvendige beslutninger.
13. **Telemetry & succeskriterier** – events, metrics, hvor logges de, hvordan vurderes success.
14. **QA & testplan** – unit/e2e/manual, edge cases, repro-matrix (miljøer/versioner).
15. **Tjekliste** – markdown-checklist nedbrudt i delopgaver (triage, research, design, implementeringsplan, test, docs, release).
16. **Relaterede issues/PRs** – links/refs til lignende/forudgående arbejde og dubletnoter.
17. **Lukning & opfølgning** – plan for lukning, release-notes, kommunikation.

## Outputkrav (strengt)

Returnér **præcis to blokke** i denne rækkefølge:
**(A) ISSUE_PREVIEW**: Markdown-forhåndsvisning af hele issue-teksten (inkl. titel som `# Titel`).
**(B) GH_COMMAND**: En **Bash**-blok med ét `gh issue create`-kald, der opretter issuen i repoet.

* Brug **heredoc** til `--body -` så hele markdown-kroppen følger med.
* Sæt følgende variabler i toppen af bash-blokken (udfyld `TITLE` så den matcher ISSUE_PREVIEW):

```bash
REPO="{{ORG_OR_USER}}/{{REPO_NAME}}"
TITLE="<samme som i ISSUE_PREVIEW>"
LABELS="triage,needs-review"
ASSIGNEES="{{github_handle_1}},{{github_handle_2}}"
PROJECT="{{org_project_number_eller_tom}}"
MILESTONE="{{milestone_eller_tom}}"
```

* Eksempelstruktur (du skal udfylde felter ud fra ISSUE_PREVIEW):

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

## Arbejdsgang (inden du skriver ISSUE_PREVIEW)

1. Læs issue-briefet (teksten **efter kolon**).
2. Søg efter dubletter/relaterede issues og noter dem.
3. Reproducer (hvis bug) / afgræns scope (hvis feature).
4. Research kodebasen (læse-niveau), noter relative stier og relevans.
5. Udfyld alle sektioner i ISSUE_PREVIEW.
6. Generér GH_COMMAND med korrekt `--title` og heredoc-body.

## Stil & kvalitet

* Skriv kort, præcist, handlingsorienteret.
* Brug bullets og nummererede lister for klarhed.
* **Ingen implementeringskode**.
* Acceptance-kriterier kan medtages i tjeklisten for features, og repro-steps for bugs skal være utvetydige.

---

**Issue-brief:**
:
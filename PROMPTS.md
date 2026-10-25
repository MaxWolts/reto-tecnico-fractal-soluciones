# AI Prompts

**Tool:** Claude Code. One orchestrator model planned the work and handed each task to a smaller or larger model depending on difficulty.

**My role:** I set the goals, chose the stack and the workflow, answered the options the AI gave me, and reviewed the results. The AI wrote most of the code and docs.

Contents: **Decisions** · **My prompts** · **Review** · **Appendix** (full subagent prompts, collapsed).

---

## 1. Decisions

| # | Topic | Options I had | My choice |
|---|-------|---------------|-----------|
| 1 | Backend + frontend | AI suggested .NET 8 + Dapper + React | **Python (FastAPI) + React** |
| 2 | Cloud | Railway, AWS or Azure (from the challenge) | **Railway** |
| 3 | Database for development | MySQL on Railway · install MySQL locally · use an existing one | **Install MySQL 8 locally** |
| 4 | Repo and deploy | AI creates them with CLIs · I create them myself | **I push and deploy myself; AI works only locally** |
| 5 | Commit style | — | **Small commits per stage, gitmoji, short plain English** |
| 6 | Scope | — | **Deliver in one day; quality over quantity; check consistency between artifacts** |
| 7 | AI workflow | — | **Short answers; pick a model per task** |
| 8 | Two extra safety checks (DB rules vs code test, lock history edits in DB) | Fix now · leave for later | **Leave for later, go to deploy** (listed as next steps) |

---

## 2. My prompts

Originals were written in Spanish; spelling is cleaned up, meaning unchanged.

**1 · Understand the challenge**
> "Es una prueba técnica que debo realizar y esa es la imagen de referencia del punto 3. ¿Qué sugerencias das para hacerla lo mejor posible?"

*This is a technical test and this is the reference image for point 3. What do you suggest to do it as well as possible?* (challenge PDF + mockup attached)

**2 · What the committee expects**
> "Teniendo en cuenta que se permite el uso de IA, ¿qué suelen esperar?"

*Since AI is allowed, what do they usually expect?*

**3 · How to build it**
> "Teniendo eso en cuenta, ¿cómo realizarías el proyecto?"

*With that in mind, how would you build the project?*
→ The AI proposed .NET + Dapper. I changed it in the next prompt.

**4 · Start the project**
> "Realiza el proyecto con Python y React; usaremos Railway. Prepara los prompts para colocarlos en PROMPTS.md. Se entregará todo en un día. Mantengamos el criterio por encima de la cantidad, con verificación de inconsistencias y un historial de commits progresivo. Respuestas siempre breves, y usa el modelo adecuado según la complejidad de cada tarea: uno ligero para tareas mecánicas, uno intermedio para código típico y el más potente para diseño complejo y revisión."

*Build it with Python and React on Railway. Prepare the prompts for PROMPTS.md. Delivery in one day. Quality over quantity, check inconsistencies, progressive commit history. Always keep answers short, and use the right model for each task: a light one for mechanical work, a mid one for typical code, the strongest for complex design and review.*

My answers to the options:
- Database: install MySQL locally.
- Commits: "Commits simples por etapas, con gitmoji, sin comentarios extensos, que parezcan de una persona con un inglés simple. Trabaja de manera local."

**5–6 · Local database ready**
> "Listo, la instalación." · "backend/.env creado con DATABASE_URL y TEST_DATABASE_URL. Continúa."

*MySQL installed. `.env` created. Continue.*
→ First real run of the stored procedures. 88 tests pass and the full flow works in the browser.

---

## Review

Each task went to the right model (light for setup, mid for code, strongest for SQL and review). A final review checked docs, SQL, API and UI against each other. Bugs it caught and fixed:
- A stale version returned 422 instead of 409.
- Closed tickets could still be reassigned.
- Integration tests could wipe the production database.

---

## Appendix — Full subagent prompts

Kept as sent. Only local file paths are shortened.

Every report was required in terse form: answer first, one line per finding, negations kept exact.

### 6. Init repo — Haiku
- **Purpose:** Repo skeleton with no secrets.

<details><summary>Prompt</summary>

> Task: initialize repo for a technical challenge "Maintenance Tickets" (FastAPI backend in backend/, React+Vite+TS frontend in frontend/, MySQL SQL scripts in database/, docs in docs/). All content in English. Do exactly: 1. `git init -b main`. 2. Create `.gitignore` covering Python, Node, env files (.env, .env.*, but NOT .env.example), IDE (.vs/, .vscode/, .idea/), OS, logs. 3. Create `.env.example` with placeholders: DATABASE_URL, CORS_ORIGINS, LOG_LEVEL, VITE_API_URL. 4. Create README stub. 5. Create PROMPTS.md skeleton. 6. Commit `🎉 init project` (no body, no trailers).
</details>

### 7. Design docs — Sonnet
- **Purpose:** ERD, state machine, sequence and architecture diagrams before any code.
- **Checked:** The agent reported 6 spec gaps. Resolved in the spec:
  - The service loads the ticket before a transition.
  - A CHECK violation returns 400.
  - Line endings are normalized with `.gitattributes`.
  - The frontend refreshes after every mutation.

<details><summary>Prompt</summary>

> Read the spec first (single source of truth). Task: write design docs in English, Mermaid diagrams. Keep each doc focused and short; do not invent entities/endpoints/codes absent from the spec. 1. docs/erd.md: erDiagram with operator, ticket, ticket_history, allowed_transition (all columns, PK/FK); ticket 1-N history; explain why allowed_transition has no FK; integrity rules (FK RESTRICT, append-only history, CHECK constraints, optimistic concurrency via version). 2. docs/state-machine.md: stateDiagram-v2 with guard labels, transitions table, where it is enforced (frontend, service, stored procedure — defense in depth). 3. docs/sequence.md: create ticket (alt 400) and change status (service validation alt 422; SP: START TRANSACTION, SELECT … FOR UPDATE, version check, allowed_transition check, UPDATE, INSERT history, COMMIT; alt SIGNAL → ROLLBACK → 404/409/422 ProblemDetails). 4. docs/architecture.md: Browser → React (Railway static) → FastAPI → MySQL; layers routes → services → domain / repositories → SPs; RFC 7807 mapping table. Commit `📝 add design docs (erd, states, sequence, architecture)`. Report spec gaps.
</details>

### 8. Schema and seed — Opus
- **Purpose:** Tables with named constraints. Seed reproduces the reference mockup with coherent histories.
- **Checked:** Each seeded history walks only allowed transitions, and versions equal 1 + changes. The `erd.md` mismatch on `updated_at` was flagged and fixed in step 16.

<details><summary>Prompt</summary>

> Read spec first. Also read docs/erd.md; if it differs from spec, follow spec and report. Touch ONLY database/ and .gitattributes. 1. .gitattributes `* text=auto eol=lf`. 2. database/01_schema.sql: idempotent, FK-safe drops with a "dev reset" comment, CREATE TABLE operator, ticket (AUTO_INCREMENT=1001), ticket_history, allowed_transition per spec with named constraints, InnoDB utf8mb4; insert the 5 allowed_transition rows (reference data). No stored procedures here. 3. database/03_seed.sql: 3 operators; demo tickets matching the mockup (#1042, #1045, #1039, #1031, #1028) with explicit ids, coherent history walking only allowed transitions, version = 1 + status changes + assignments; comment why seed inserts directly. Self-check against spec column by column. Commit `🗃️ add db schema and seed data`.
</details>

### 9. Stored procedures + DB init script — Opus
- **Purpose:** All writes go through SPs. Each SP runs in a transaction with ROLLBACK + RESIGNAL, row locks, and rules read from `allowed_transition` (no hardcoded transitions).
- **Checked:** The agent flagged that the integration tests reset the DB at `DATABASE_URL`, which could wipe production. Fixed in step 12.

<details><summary>Prompt</summary>

> Read spec, schema, seed and state_machine.py. Touch ONLY database/ and backend/scripts/. MySQL is NOT installed; write carefully and self-review. 1. database/02_stored_procedures.sql: sp_create_ticket, sp_change_ticket_status, sp_add_comment, sp_assign_ticket exactly per spec; DELIMITER blocks; no DEFINER; EXIT HANDLER ROLLBACK + RESIGNAL; START TRANSACTION … COMMIT; result SELECT after COMMIT; not-found via NULL-initialized variable (not ROW_COUNT); rules looked up in allowed_transition; NULLIF(TRIM(x),''). 2. Seed DELETEs must work under --safe-updates. 3. backend/scripts/init_db.py: stdlib + PyMySQL, handles DELIMITER, quotes and comments; `--no-seed`. 4. Integration tests (marker integration, skip when DB unavailable): invalid transition leaves no history row (rollback proof), DIAGNOSIS_REQUIRED, CONCURRENCY_CONFLICT, TICKET_NOT_FOUND, COMMENT_EMPTY, OPERATOR_NOT_FOUND, FK delete fails (1451). Commit `🗃️ add stored procedures and db init script`.
</details>

### 10. Domain layer, test-first — Sonnet
- **Purpose:** Pure state machine mirroring `allowed_transition`, with no DB and no framework.
- **Checked:** Tests cover all 16 (from, to) pairs. A drift test fails if the code table differs from the 5 DB rows.

<details><summary>Prompt</summary>

> Read spec and docs/state-machine.md. Touch ONLY backend/. Backend skeleton + pure domain layer + tests (TDD: tests first). 1. Pinned requirements, requirements-dev, pyproject (pytest markers, ruff). 2. venv. 3. domain/status.py (StrEnums), exceptions.py (DomainError with code; one subclass per spec code; CODE_TO_ERROR), state_machine.py (TransitionRule, TRANSITIONS mirroring allowed_transition, allowed_from, validate_transition). 4. Table-driven tests over all 16 pairs; whitespace diagnosis → DiagnosisRequired; final states have no transitions; PENDING→RESOLVED explicit; drift guard. 5. pytest + ruff green. Commit `✨ add ticket state machine with tests`.
</details>

### 11. Repository, service, routes, errors — Sonnet
- **Purpose:** Layered API. SQL only in the repository; business rules only in the service; thin routes; RFC 7807 errors; no generic 500.
- **Checked:** Smoke test with no DB: `/health` reports `database: down` and `/api/tickets` returns 503 problem JSON. The agent reported that 500 responses lacked CORS headers. Fixed in step 12.

<details><summary>Prompt</summary>

> Read spec and the existing domain code. Touch ONLY backend/. config.py (pydantic-settings), db.py (parse DATABASE_URL incl. Railway form, DictCursor, autocommit off), repositories/ticket_repository.py (callproc SPs; errno 1644 message → domain exception; parameterized reads with filters), services/ticket_service.py (state machine before repo; builds allowedTransitions; no SQL, no FastAPI), schemas (camelCase, validation rules), routes (thin), errors.py (DomainError → status; validation → 400 with errors[]; DB down → 503; catch-all → 500 generic, logged). Tests with an in-memory fake repository: 201, 400 shape, 404, 409, 422 PENDING→RESOLVED, 422 missing diagnosis, happy path with history count 3. Keep it lean: no generic base repository, no DI framework. Two commits: `✨ add repository and service layers`, `✨ add api routes and error handling`.
</details>

### 12. Robustness fixes — Sonnet
- **Purpose:** Fix the issues reported in steps 9 and 11.

<details><summary>Prompt</summary>

> Fix, each with a test: 1. Integration tests read ONLY TEST_DATABASE_URL, never fall back to DATABASE_URL, refuse to run if both are equal. 2. 500 responses lack CORS headers (ServerErrorMiddleware is outermost): add a catch-all middleware inside CORS returning RFC 7807 500. 3. init_db sets time_zone '+00:00' (same as app connections). 4. Query validation returned 503 when DB down: make the connection lazy so 400 comes first. Commit `🐛 fix cors on errors, lazy db conn, safe test db`.
</details>

### 13. Frontend board and create form — Sonnet
- **Purpose:** Layout of the reference mockup, with no UI kit and no extra deps.

<details><summary>Prompt</summary>

> Read spec and the reference mockup image. Touch ONLY frontend/. Vite react-ts; types mirroring the spec; fetch client throwing ApiError with ProblemDetails; CSS tokens (brand colors, Inter, responsive). Components: Header (role toggle Reporter/Operator), CreateTicketForm (inline validation mirroring backend, backend field errors, spinner), Board (3 columns, counters, empty states, skeleton, error banner with retry), TicketCard (code, title, asset chip, priority, assignee initials, relative time, keyboard accessible), Toasts, useTickets. build + lint clean. Commit `✨ add frontend board and create form`.
</details>

### 14. Drawer, transitions, history, bonus — Sonnet
- **Purpose:** Make traceability visible, and add the bonus: assignment, filters, simulated notifications.
- **Checked:** The agent flagged that assignment on closed tickets was undefined. I decided to reject it (`TICKET_CLOSED`) in all layers, in step 16.

<details><summary>Prompt</summary>

> Touch ONLY frontend/. Stage 8: TicketDrawer (aria-modal, Esc, details, one action button per allowedTransitions, Operator only), TransitionDialog (diagnosis/comment required per rule), 409 → toast + reload, 422 → inline error, HistoryTimeline, comment box, editable user name (history actor). Commit `✨ add ticket drawer with status actions and history`. Stage 9: assignee select (PUT with version), FiltersBar (status incl. Cancelled, priority, operator, date range, debounced search, state kept in URL), NotificationBell (poll 15 s, paused when tab hidden, unseen badge, click opens ticket, last-seen in localStorage; comment that notifications are simulated from history). Commit `✨ add assignment, filters and notifications`.
</details>

### 15. Railway config — Haiku
- **Purpose:** Config-as-code and a deploy guide.
- **Rule:** `init_db` drops tables, so it never runs as a pre-deploy step.
- **Checked:** All pinned dependencies have Python 3.12 Linux wheels.

<details><summary>Prompt</summary>

> backend/railway.json (RAILPACK, uvicorn on $PORT, healthcheck /health, NO preDeployCommand because init_db drops tables), backend/.python-version 3.12 (check wheels exist for 3.12), frontend/railway.json, frontend/.env.example, docs/deploy-railway.md (dashboard steps: MySQL service, backend with DATABASE_URL=${{MySQL.MYSQL_URL}}, one-time init from local with warning, frontend with build-time VITE_API_URL, CORS, smoke test, troubleshooting). Commit `🔧 add railway config and deploy guide`.
</details>

### 16. Cross-artifact consistency review — Opus (read-only) + Sonnet (fixes)
- **Purpose:** Make sure docs, SQL, backend and frontend tell the same story.
- **Result:** 0 high, 6 medium and 12 low findings. One medium (Railway files not committed) was already fixed when the review ended. All others were fixed in `🐛 fix review findings in api and db` and `📝 sync docs with code`. Main ones:
  - A stale version returned 422 instead of 409. The service now checks the version first, in the same order as the SP.
  - Closed tickets could be reassigned. Now rejected with `TICKET_CLOSED` in the SP, the service and the UI.
  - Searching `#1042` found nothing.
  - The repository `callproc` path had no integration test.
  - Function names in the diagrams did not match the code.

<details><summary>Review prompt</summary>

> READ-ONLY review. Cross-artifact consistency + correctness: erd.md vs 01_schema.sql (every column/type/null/default/FK/index/check); state-machine.md vs allowed_transition vs state_machine.py vs frontend labels; sequence.md vs real call chain and status codes; architecture.md error table vs errors.py vs frontend handling; SP MySQL 8 syntax, transaction/rollback, result columns vs repository vs schemas, callproc result-set handling; seed histories; API shapes vs frontend types and query params; secrets/hygiene; English only. One line per finding with severity and fix.
</details>

### 17. README — Sonnet
- **Purpose:** Run instructions and stack justification, checked against real files.

<details><summary>Prompt</summary>

> Write the final README in English. Read docs, backend, frontend, database first; every command must match real files; do not invent features. Sections: summary + live URLs, features, lifecycle table + 3-layer enforcement, architecture links + tree, stack justification with trade-offs, run locally (Windows first), tests (integration needs TEST_DATABASE_URL on a throwaway DB), API overview + RFC 7807 example, deployment link, AI usage link. Commit `📝 write readme`.
</details>

### 18. First run against real MySQL — Opus
- **Purpose:** Prove the SQL path. Until this step, every SP had only been reviewed by reading it.
- **Result:**
  - No SQL or repository bugs.
  - The test harness needed 2 fixes: load `backend/.env`, and create the test DB before connecting.
  - 88 tests pass, including 12 integration tests.
  - API smoke checks: 201 create; 422 `INVALID_TRANSITION`; 422 `DIAGNOSIS_REQUIRED`; 409 stale version; history holds 3 events.
- **Then:** End-to-end in the browser: create, start work, resolve blocked without diagnosis, resolve with diagnosis. Screenshots taken for the README.

<details><summary>Prompt</summary>

> MySQL 8.0 now running locally; backend/.env has DATABASE_URL and TEST_DATABASE_URL. SECURITY: never print the password or full URLs. First time any SQL runs. 1. Run init_db; fix errors at the root cause. 2. Integration tests must pass, not skip; fix real bugs, do not weaken assertions. 3. Full suite + ruff green. 4. Re-seed and check versions 6,4,3,1,1. 5. Live smoke with curl: health, list, create, PENDING→RESOLVED 422, start 200, resolve without diagnosis 422, with diagnosis 200, stale version 409, history 3 events, notifications.
</details>

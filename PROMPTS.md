# AI Prompts

**Language / Idioma:** [English](#english) · [Español](#español)

<a id="english"></a>

**Tool:** Claude Code. One orchestrator model planned the work and gave each task to a light, mid or strong model depending on difficulty.

**My role:** I set the goals, chose the stack, picked between the options the AI proposed, ran the checks that needed my accounts (database, GitHub, hosting) and reviewed the results. The AI wrote most of the code and docs.

Contents: **Decisions** · **My prompts** · **Review** · **Appendix** (full subagent prompts, collapsed).

---

## 1. Decisions

| # | Topic | Options I had | My choice |
|---|-------|---------------|-----------|
| 1 | Backend + frontend | AI suggested .NET 8 + Dapper + React | **Python (FastAPI) + React** |
| 2 | Database for development | MySQL on Railway · install locally · existing server | **MySQL 8 installed locally** |
| 3 | Workflow | — | **One day; quality over quantity; consistency checks; small commits per stage** |
| 4 | AI usage | — | **Short answers; the right model for each task** |
| 5 | Railway setup | Dashboard · CLI · single combined service | **Dashboard with GitHub integration** |
| 6 | Railway unavailable (new signups paused after its Oct 21 incident; Azure not possible for me) | Wait · AWS · free external services | **Free external services, justified in the README** |
| 7 | Hosting | Aiven + Render + Netlify · Aiven + Vercel | **Aiven (MySQL) + Vercel (frontend and API)**: no cold start during the demo |
| 8 | Two extra safety checks (DB rules vs code test, DB-level history lock) | Fix now · later | **Later** (listed as next steps) |

---

## 2. My prompts

Written in Spanish; edited for spelling and clarity, meaning unchanged.

### Planning

**1 · Understand the challenge**
> "Este es el enunciado de una prueba técnica y la imagen de referencia del punto 3. ¿Qué sugerencias das para hacerla lo mejor posible?"

*Here is the challenge and the reference mockup. What do you suggest to do it as well as possible?*

**2 · What the committee expects**
> "Si se permite usar IA, ¿qué suele esperar el comité?"

*If AI is allowed, what does the committee usually expect?*

**3 · Approach**
> "Con eso en cuenta, ¿cómo realizarías el proyecto?"

*With that in mind, how would you build it?*
→ The AI proposed .NET + Dapper. I chose Python in the next prompt.

### Build

**4 · Start**
> "Realiza el proyecto con Python y React; desplegaremos en Railway. Se entrega en un día. Prioriza la calidad sobre la cantidad, verifica inconsistencias entre los artefactos y mantén un historial de commits progresivo. Prepara los prompts para PROMPTS.md. Respuestas breves, y usa el modelo adecuado según la complejidad de cada tarea: uno ligero para tareas mecánicas, uno intermedio para código típico y el más potente para diseño complejo y revisión."

*Build it with Python and React, deploy on Railway, deliver in one day. Quality over quantity, check consistency between artifacts, progressive commits. Prepare PROMPTS.md. Short answers; the right model per task.*

My answers to its options:
- Database: install MySQL locally.
- Commits: "Commits pequeños por etapa, con gitmoji y mensajes cortos en inglés sencillo. Trabaja solo en local."

**5 · Run against the real database**
> "MySQL instalado y backend/.env creado con DATABASE_URL y TEST_DATABASE_URL. Continúa."

*MySQL is installed and `.env` is ready. Continue.*
→ First real run of the stored procedures: 88 tests pass and the full flow works in the browser.

### Deploy

**6 · Choose how to deploy**
> "Repo creado en GitHub. Haz el push y dame las opciones para desplegar en Railway con pros y contras; yo elijo."

*Push the repo and give me the Railway deploy options with pros and cons; I'll choose.*
→ Dashboard, CLI or a single combined service. I chose the dashboard: no code changes and auto-deploy on push.

**7 · Platform outage**
> "Railway está caído. ¿Qué alternativas gratuitas hay dentro de lo permitido?" · "Revisa status.railway.com para estimar cuánto puede demorar."

*Railway is down. What free options are allowed? Check the status page to estimate how long it may take.*
→ New signups were paused after a security incident, with no date. AWS and Azure need a card and verification.

**8 · Free external services**
> "No puedo usar Railway ni Azure. ¿Qué servicios gratuitos puedo usar para publicar la demo? Lo justificaré luego."

*I can't use Railway or Azure. Which free services can host the demo? I'll justify it later.*
→ Options per layer. I discarded TiDB because it has no stored procedures and chose Aiven for MySQL.

**9 · Simplify hosting**
> "¿Vercel no evitaría tener que usar Render y Netlify?"

*Wouldn't Vercel replace both Render and Netlify?*
→ Yes: one platform for frontend and API, and no 50 s cold start. I chose Aiven + Vercel.

**10 · Debug the deployed API**
> "El backend responde FUNCTION_INVOCATION_FAILED. Estos son los logs: ModuleNotFoundError: No module named 'fastapi'."

*The API fails with these logs.*
→ Root cause: Vercel reads dependencies from `pyproject.toml`, not `requirements.txt`. Fixed, plus a test that keeps both lists in sync.

---

## Review

Each task went to the right model: light for setup, mid for code, strongest for SQL and review. A final review checked docs, SQL, API and UI against each other. Bugs caught and fixed:
- A stale version returned 422 instead of 409.
- Closed tickets could still be reassigned.
- Integration tests could wipe the production database.
- The deployed API could not find its dependencies (found from the logs).

---

---

<a id="español"></a>

# Prompts de IA — Español

**Herramienta:** Claude Code. Un modelo orquestador planificó el trabajo y asignó cada tarea a un modelo ligero, intermedio o potente según la dificultad.

**Mi rol:** Definí los objetivos, elegí el stack, escogí entre las opciones que propuso la IA, ejecuté las verificaciones que requerían mis cuentas (base de datos, GitHub, hosting) y revisé los resultados. La IA escribió la mayor parte del código y de la documentación.

Contenido: **Decisiones** · **Mis prompts** · **Revisión** · **Anexo** (prompts completos de los subagentes, en inglés).

---

## 1. Decisiones

| # | Tema | Opciones que tenía | Mi elección |
|---|------|--------------------|-------------|
| 1 | Backend + frontend | La IA sugirió .NET 8 + Dapper + React | **Python (FastAPI) + React** |
| 2 | Base de datos para desarrollo | MySQL en Railway · instalar local · servidor existente | **MySQL 8 instalado localmente** |
| 3 | Flujo de trabajo | — | **Un día; calidad sobre cantidad; verificaciones de consistencia; commits pequeños por etapa** |
| 4 | Uso de IA | — | **Respuestas breves; el modelo adecuado para cada tarea** |
| 5 | Configuración de Railway | Dashboard · CLI · un único servicio combinado | **Dashboard con integración de GitHub** |
| 6 | Railway no disponible (registros nuevos pausados tras su incidente del 21 de oct; Azure no es posible para mí) | Esperar · AWS · servicios externos gratuitos | **Servicios externos gratuitos, justificados en el README** |
| 7 | Hosting | Aiven + Render + Netlify · Aiven + Vercel | **Aiven (MySQL) + Vercel (frontend y API)**: sin arranque en frío durante la demo |
| 8 | Dos verificaciones de seguridad extra (reglas de la BD vs prueba de código, bloqueo del historial a nivel de BD) | Corregir ahora · después | **Después** (listadas como próximos pasos) |

---

## 2. Mis prompts

Escritos en español; editados por ortografía y claridad, sin cambiar el sentido.

### Planificación

**1 · Entender el reto**
> "Este es el enunciado de una prueba técnica y la imagen de referencia del punto 3. ¿Qué sugerencias das para hacerla lo mejor posible?"

**2 · Qué espera el comité**
> "Si se permite usar IA, ¿qué suele esperar el comité?"

**3 · Enfoque**
> "Con eso en cuenta, ¿cómo realizarías el proyecto?"

→ La IA propuso .NET + Dapper. Elegí Python en el siguiente prompt.

### Construcción

**4 · Inicio**
> "Realiza el proyecto con Python y React; desplegaremos en Railway. Se entrega en un día. Prioriza la calidad sobre la cantidad, verifica inconsistencias entre los artefactos y mantén un historial de commits progresivo. Prepara los prompts para PROMPTS.md. Respuestas breves, y usa el modelo adecuado según la complejidad de cada tarea: uno ligero para tareas mecánicas, uno intermedio para código típico y el más potente para diseño complejo y revisión."

Mis respuestas a sus opciones:
- Base de datos: instalar MySQL localmente.
- Commits: "Commits pequeños por etapa, con gitmoji y mensajes cortos en inglés sencillo. Trabaja solo en local."

**5 · Ejecutar contra la base de datos real**
> "MySQL instalado y backend/.env creado con DATABASE_URL y TEST_DATABASE_URL. Continúa."

→ Primera ejecución real de los procedimientos almacenados: 88 pruebas pasan y el flujo completo funciona en el navegador.

### Despliegue

**6 · Elegir cómo desplegar**
> "Repo creado en GitHub. Haz el push y dame las opciones para desplegar en Railway con pros y contras; yo elijo."

→ Dashboard, CLI o un único servicio combinado. Elegí el dashboard: sin cambios de código y despliegue automático con cada push.

**7 · Caída de la plataforma**
> "Railway está caído. ¿Qué alternativas gratuitas hay dentro de lo permitido?" · "Revisa status.railway.com para estimar cuánto puede demorar."

→ Los registros nuevos se pausaron tras un incidente de seguridad, sin fecha. AWS y Azure requieren tarjeta y verificación.

**8 · Servicios externos gratuitos**
> "No puedo usar Railway ni Azure. ¿Qué servicios gratuitos puedo usar para publicar la demo? Lo justificaré luego."

→ Opciones por capa. Descarté TiDB porque no tiene procedimientos almacenados y elegí Aiven for MySQL.

**9 · Simplificar el hosting**
> "¿Vercel no evitaría tener que usar Render y Netlify?"

→ Sí: una sola plataforma para frontend y API, y sin arranque en frío de 50 s. Elegí Aiven + Vercel.

**10 · Depurar la API desplegada**
> "El backend responde FUNCTION_INVOCATION_FAILED. Estos son los logs: ModuleNotFoundError: No module named 'fastapi'."

→ Causa raíz: Vercel lee las dependencias de `pyproject.toml`, no de `requirements.txt`. Corregido, más una prueba que mantiene ambas listas sincronizadas.

---

## Revisión

Cada tarea fue al modelo adecuado: ligero para la configuración, intermedio para el código, el más potente para SQL y revisión. Una revisión final contrastó documentación, SQL, API y UI entre sí. Errores detectados y corregidos:
- Una versión obsoleta devolvía 422 en lugar de 409.
- Los tickets cerrados aún podían reasignarse.
- Las pruebas de integración podían borrar la base de datos de producción.
- La API desplegada no encontraba sus dependencias (detectado en los logs).

---

Los prompts completos enviados a los subagentes están al final, en inglés: [Appendix](#appendix--full-subagent-prompts).

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

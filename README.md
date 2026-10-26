# Maintenance Tickets

Maintenance ticket workflow with an enforced state machine, a full per-ticket event history (Ticket 1-N History) and MySQL stored procedures that own every write. FastAPI backend with a strict routes / services / domain / repositories split, React + Vite + TypeScript frontend, deployed on Vercel (frontend and backend) and Aiven MySQL (free tiers).

- Live demo: <frontend URL - TBD>
- API docs: <backend URL>/docs - TBD

## Screens

Built from the reference mockup, with UX additions: filters, ticket drawer with history timeline, guarded status actions and a notification bell.

![Board](docs/screens/board.png)

![Ticket drawer with diagnosis and history](docs/screens/ticket-drawer.jpg)

## Features

Core:
- Create tickets (title, description, asset code, priority, reporter); ids start at 1001.
- Status changes validated by a state machine, with diagnosis or comment required where the rules say so.
- Append-only history per ticket: `CREATED`, `STATUS_CHANGED`, `COMMENT`, `ASSIGNED` events with actor and timestamp.
- Optimistic concurrency (`version` column) plus row locking in the stored procedures; stale writes get HTTP 409.
- RFC 7807 error responses with stable machine-readable codes.

Bonus:
- Operator assignment and unassignment (blocked on final states).
- Filters: status, priority, operator, date range, free-text search.
- Simulated notifications: there is no push channel. The UI polls `GET /api/notifications` (every 15 s), which reads `STATUS_CHANGED` / `ASSIGNED` history events.

## Ticket lifecycle

Statuses: `PENDING`, `IN_PROGRESS`, `RESOLVED`, `CANCELLED`. `RESOLVED` and `CANCELLED` are final. Diagram and guards: [docs/state-machine.md](docs/state-machine.md).

| From        | To          | Requires diagnosis | Requires comment |
|-------------|-------------|--------------------|------------------|
| PENDING     | IN_PROGRESS | no                 | no               |
| PENDING     | CANCELLED   | no                 | yes              |
| IN_PROGRESS | RESOLVED    | yes                | no               |
| IN_PROGRESS | PENDING     | no                 | yes              |
| IN_PROGRESS | CANCELLED   | no                 | yes              |

Any other pair (same status, `PENDING -> RESOLVED`, anything leaving a final state) is rejected. Enforced in three layers:

- **Frontend**: shows only the actions in the ticket's `allowedTransitions` and asks for diagnosis or comment. UX only, never trusted.
- **Service**: `backend/app/domain/state_machine.py` (pure Python) validates before any SQL; failures are HTTP 422.
- **Database**: `sp_change_ticket_status` checks the `allowed_transition` table inside the transaction, with `FOR UPDATE` and the `version` check, so a client that bypasses the API still cannot break the rules.

## Architecture

Request path: `routes` (HTTP and Pydantic only) -> `services` (use cases) -> `domain` (state machine, exceptions, no I/O) and `repositories` (the only SQL; calls stored procedures, maps MySQL signals to domain errors) -> MySQL 8.

- [docs/architecture.md](docs/architecture.md): layers, configuration, error mapping
- [docs/sequence.md](docs/sequence.md): sequence diagrams of the main flows
- [docs/erd.md](docs/erd.md): entity-relationship diagram (`operator`, `ticket`, `ticket_history`, `allowed_transition`)

```
.
├── backend/
│   ├── app/            api/, domain/, services/, repositories/, schemas/, config.py, db.py, main.py
│   ├── scripts/        init_db.py
│   ├── tests/          unit tests + integration/
│   ├── pyproject.toml  pytest + ruff config + Vercel entrypoint (tool.vercel)
│   ├── requirements.txt, requirements-dev.txt
│   └── railway.json
├── frontend/
│   ├── src/            api/, components/, hooks/, context/, styles/, App.tsx
│   ├── package.json
│   └── railway.json
├── database/           01_schema.sql, 02_stored_procedures.sql, 03_seed.sql
├── docs/               architecture, state-machine, sequence, erd, deploy-free-tier, deploy-railway
├── .env.example        backend and frontend variables
└── PROMPTS.md
```

## Tech stack

- **FastAPI + Pydantic v2**: typed request/response models and OpenAPI docs at `/docs`. Endpoints are synchronous: fine for this load, not tuned for high concurrency.
- **PyMySQL + stored procedures, no ORM**: transitions, locking and history writes live in SQL, so the rules hold for any client. Trade-off: logic is split between SQL and Python, and the transition table is mirrored in `state_machine.py`.
- **MySQL 8**: transactions, `FOR UPDATE`, CHECK constraints, managed free offering on Aiven (TLS).
- **React 19 + Vite + TypeScript, no UI kit**: small bundle and full control of the board/drawer UI. Trade-off: hand-written components and CSS.
- **Vercel + Aiven**: static frontend and serverless FastAPI backend on Vercel, MySQL on Aiven, all free tiers. The backend entrypoint is set by `tool.vercel` in `backend/pyproject.toml`. Trade-off: serverless cold starts and a new DB connection per request. Railway configs are kept as an alternative.

## Run locally

Prerequisites: Python 3.12+, Node 20+, MySQL 8.

1. Create the database (`init_db.py` also creates it if the user has rights):

   ```sql
   CREATE DATABASE tickets CHARACTER SET utf8mb4;
   ```

2. Backend (PowerShell, from the repo root):

   ```powershell
   cd backend
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   Copy-Item ..\.env.example .env
   ```

   Bash: `source .venv/bin/activate` and `cp ../.env.example .env`.

   The only env example is the root `.env.example`. In `backend/.env` set `DATABASE_URL` to your MySQL credentials; `CORS_ORIGINS` and `LOG_LEVEL` can stay. The `VITE_API_URL` line is for the frontend and the backend ignores it.

3. Create tables, procedures and demo data:

   ```powershell
   python scripts/init_db.py
   ```

   WARNING: this DROPS AND RECREATES ALL TABLES in the target database. Add `--no-seed` to skip the demo rows (schema and procedures only).

4. Start the API:

   ```powershell
   uvicorn app.main:app --reload
   ```

5. Frontend (new terminal, from the repo root):

   ```powershell
   cd frontend
   npm install
   Copy-Item .env.example .env
   npm run dev
   ```

   Bash: `cp .env.example .env`.

URLs: API http://localhost:8000 (docs at `/docs`, health at `/health`); frontend http://localhost:5173.

## Tests and linting

From `backend/` with the venv active:

```powershell
pytest -q
ruff check .
```

`pytest -q` runs the unit tests (state machine, service, API with a fake repository, integration guard). Integration tests hit a real MySQL (stored procedures and repository), DROP and recreate tables, and are selected by marker. `TEST_DATABASE_URL` must point to a throwaway database, never the same value as `DATABASE_URL` (the guard refuses to run otherwise):

```powershell
$env:TEST_DATABASE_URL="mysql://user:password@localhost:3306/tickets_test"
pytest -m integration
```

Bash: `TEST_DATABASE_URL=mysql://user:password@localhost:3306/tickets_test pytest -m integration`.

From `frontend/`:

```powershell
npm run lint
npm run build
```

## API overview

Interactive docs: `/docs`. JSON fields are camelCase.

| Method | Path | Purpose |
|--------|------|---------|
| GET  | `/health` | Liveness and database status |
| GET  | `/api/transitions` | Allowed transition table |
| GET  | `/api/operators` | List operators |
| POST | `/api/tickets` | Create ticket |
| GET  | `/api/tickets` | List; filters `status`, `priority`, `operatorId`, `from`, `to`, `q` |
| GET  | `/api/tickets/{id}` | Ticket detail, incl. `allowedTransitions` |
| GET  | `/api/tickets/{id}/history` | Ticket event history |
| POST | `/api/tickets/{id}/transitions` | Change status (`toStatus`, `diagnosis`, `comment`, `actor`, `version`) |
| POST | `/api/tickets/{id}/comments` | Add comment |
| PUT  | `/api/tickets/{id}/assignee` | Assign or unassign operator |
| GET  | `/api/notifications` | Recent status/assignment events (`since`, `limit`) |

Errors are `application/problem+json` (RFC 7807) with a stable `code`:

```json
{
  "type": "about:blank",
  "title": "Unprocessable Entity",
  "status": 422,
  "detail": "Cannot move from PENDING to RESOLVED",
  "code": "INVALID_TRANSITION"
}
```

Codes: 404 `TICKET_NOT_FOUND`, `OPERATOR_NOT_FOUND`; 409 `CONCURRENCY_CONFLICT`; 422 `INVALID_TRANSITION`, `DIAGNOSIS_REQUIRED`, `COMMENT_REQUIRED`, `COMMENT_EMPTY`, `TICKET_CLOSED`; 400 `VALIDATION_ERROR` (with `errors[{field,message}]`); 503 `DATABASE_UNAVAILABLE`; 500 `INTERNAL_ERROR`. Full table: [docs/architecture.md](docs/architecture.md#error-handling).

## Deployment

Full guide: [docs/deploy-free-tier.md](docs/deploy-free-tier.md).

- Vercel: two projects from this repo, backend (Root Directory `backend`, serverless FastAPI) and frontend (Root Directory `frontend`, static Vite). Aiven for MySQL (free plan, TLS).
- Backend: `DATABASE_URL` with `?ssl-mode=REQUIRED`, `DB_SSL_CA` (PEM text) and `CORS_ORIGINS` = frontend origin. Frontend: build-time `VITE_API_URL` = backend URL.
- Run `init_db.py` once, by hand, against the Aiven URI. It is deliberately not in any deploy command because it drops tables.
- Why not Railway: new signups are paused after its Oct 21 2026 security incident. The Railway guide stays as an alternative: [docs/deploy-railway.md](docs/deploy-railway.md).

## AI usage

AI assistance and the prompts used are documented in [PROMPTS.md](PROMPTS.md).

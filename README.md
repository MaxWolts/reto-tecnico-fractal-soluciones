# Maintenance Tickets

**Language / Idioma:** [English](#english) · [Español](#español)

<a id="english"></a>

Maintenance ticket workflow with an enforced state machine, a full per-ticket event history (Ticket 1-N History) and MySQL stored procedures that own every write. FastAPI backend with a strict routes / services / domain / repositories split, React + Vite + TypeScript frontend, deployed on Vercel (frontend and backend) and Aiven MySQL (free tiers).

- Live demo: https://reto-tecnico-fractal-soluciones.vercel.app
- API docs: https://reto-tecnico-fractal-soluciones-38r.vercel.app/docs

## Screens

Built from the reference mockup, with UX additions: filters, ticket drawer with history timeline, guarded status actions and a notification bell.

![Board](docs/screens/board.png)

![Ticket drawer with diagnosis and history](docs/screens/ticket-drawer.jpg)

![Board in dark mode](docs/screens/board-dark.png)

The UI follows Apple's Human Interface Guidelines: 44 px hit targets, WCAG AA contrast, rem type scale, light and dark mode, motion that respects reduced-motion, and a content-first mobile layout.

**UX next steps:** pressed (`:active`) states on all controls, distinct disabled vs. busy styles, column headers larger than card titles, a darker "High" priority dot, optimistic updates, and remaining hard-coded spacing moved to tokens.

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

---

<a id="español"></a>

# Maintenance Tickets — Español

Flujo de tickets de mantenimiento con una máquina de estados obligatoria, un historial completo de eventos por ticket (Ticket 1-N History) y procedimientos almacenados de MySQL que se encargan de toda escritura. Backend FastAPI con una separación estricta en routes / services / domain / repositories, frontend React + Vite + TypeScript, desplegado en Vercel (frontend y backend) y Aiven MySQL (planes gratuitos).

La documentación técnica en docs/ está en inglés.

- Demo en vivo: https://reto-tecnico-fractal-soluciones.vercel.app
- Documentación de la API: https://reto-tecnico-fractal-soluciones-38r.vercel.app/docs

## Pantallas

Construidas a partir del mockup de referencia, con mejoras de UX: filtros, panel lateral del ticket con línea de tiempo del historial, acciones de estado protegidas y una campana de notificaciones.

![Board](docs/screens/board.png)

![Ticket drawer with diagnosis and history](docs/screens/ticket-drawer.jpg)

![Tablero en modo oscuro](docs/screens/board-dark.png)

La interfaz sigue las Human Interface Guidelines de Apple: áreas táctiles de 44 px, contraste WCAG AA, escala tipográfica en rem, modo claro y oscuro, animaciones que respetan reduced-motion y un diseño móvil que prioriza el contenido.

**Próximos pasos de UX:** estados presionados (`:active`) en todos los controles, estilos distintos para deshabilitado y procesando, títulos de columna más grandes que los de las tarjetas, un punto de prioridad "High" más oscuro, actualizaciones optimistas y llevar a tokens el espaciado que aún está fijo.

## Funcionalidades

Base:
- Crear tickets (título, descripción, código de activo, prioridad, reportante); los ids empiezan en 1001.
- Los cambios de estado los valida una máquina de estados, con diagnóstico o comentario obligatorio donde las reglas lo indican.
- Historial de solo anexado por ticket: eventos `CREATED`, `STATUS_CHANGED`, `COMMENT`, `ASSIGNED` con actor y marca de tiempo.
- Concurrencia optimista (columna `version`) más bloqueo de filas en los procedimientos almacenados; las escrituras obsoletas reciben HTTP 409.
- Respuestas de error RFC 7807 con códigos estables legibles por máquina.

Extras:
- Asignación y desasignación de operador (bloqueada en estados finales).
- Filtros: estado, prioridad, operador, rango de fechas, búsqueda de texto libre.
- Notificaciones simuladas: no hay canal push. La UI consulta `GET /api/notifications` (cada 15 s), que lee los eventos de historial `STATUS_CHANGED` / `ASSIGNED`.

## Ciclo de vida del ticket

Estados: `PENDING`, `IN_PROGRESS`, `RESOLVED`, `CANCELLED`. `RESOLVED` y `CANCELLED` son finales. Diagrama y reglas: [docs/state-machine.md](docs/state-machine.md).

| From        | To          | Requires diagnosis | Requires comment |
|-------------|-------------|--------------------|------------------|
| PENDING     | IN_PROGRESS | no                 | no               |
| PENDING     | CANCELLED   | no                 | yes              |
| IN_PROGRESS | RESOLVED    | yes                | no               |
| IN_PROGRESS | PENDING     | no                 | yes              |
| IN_PROGRESS | CANCELLED   | no                 | yes              |

Cualquier otro par (mismo estado, `PENDING -> RESOLVED`, cualquier salida de un estado final) se rechaza. Se aplica en tres capas:

- **Frontend**: muestra solo las acciones de `allowedTransitions` del ticket y pide diagnóstico o comentario. Solo UX, nunca se confía en él.
- **Servicio**: `backend/app/domain/state_machine.py` (Python puro) valida antes de cualquier SQL; los fallos son HTTP 422.
- **Base de datos**: `sp_change_ticket_status` revisa la tabla `allowed_transition` dentro de la transacción, con `FOR UPDATE` y la verificación de `version`, de modo que un cliente que se salte la API tampoco pueda romper las reglas.

## Arquitectura

Ruta de una petición: `routes` (solo HTTP y Pydantic) -> `services` (casos de uso) -> `domain` (máquina de estados, excepciones, sin I/O) y `repositories` (el único SQL; llama a procedimientos almacenados, convierte las señales de MySQL en errores de dominio) -> MySQL 8.

- [docs/architecture.md](docs/architecture.md): capas, configuración, mapeo de errores
- [docs/sequence.md](docs/sequence.md): diagramas de secuencia de los flujos principales
- [docs/erd.md](docs/erd.md): diagrama entidad-relación (`operator`, `ticket`, `ticket_history`, `allowed_transition`)

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

## Stack tecnológico

- **FastAPI + Pydantic v2**: modelos tipados de petición/respuesta y documentación OpenAPI en `/docs`. Los endpoints son síncronos: suficiente para esta carga, sin ajustes para alta concurrencia.
- **PyMySQL + procedimientos almacenados, sin ORM**: las transiciones, el bloqueo y la escritura del historial viven en SQL, así que las reglas valen para cualquier cliente. Compromiso: la lógica queda repartida entre SQL y Python, y la tabla de transiciones se replica en `state_machine.py`.
- **MySQL 8**: transacciones, `FOR UPDATE`, restricciones CHECK, oferta gratuita administrada en Aiven (TLS).
- **React 19 + Vite + TypeScript, sin kit de UI**: bundle pequeño y control total de la UI del tablero y del panel lateral. Compromiso: componentes y CSS escritos a mano.
- **Vercel + Aiven**: frontend estático y backend FastAPI serverless en Vercel, MySQL en Aiven, todo en planes gratuitos. El punto de entrada del backend lo define `tool.vercel` en `backend/pyproject.toml`. Compromiso: arranques en frío serverless y una conexión nueva a la base de datos por petición. Las configuraciones de Railway se conservan como alternativa.

## Ejecución local

Requisitos previos: Python 3.12+, Node 20+, MySQL 8.

1. Crea la base de datos (`init_db.py` también la crea si el usuario tiene permisos):

   ```sql
   CREATE DATABASE tickets CHARACTER SET utf8mb4;
   ```

2. Backend (PowerShell, desde la raíz del repositorio):

   ```powershell
   cd backend
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   Copy-Item ..\.env.example .env
   ```

   Bash: `source .venv/bin/activate` y `cp ../.env.example .env`.

   El único ejemplo de variables de entorno es el `.env.example` de la raíz. En `backend/.env` define `DATABASE_URL` con tus credenciales de MySQL; `CORS_ORIGINS` y `LOG_LEVEL` pueden quedar igual. La línea `VITE_API_URL` es para el frontend y el backend la ignora.

3. Crea tablas, procedimientos y datos de demostración:

   ```powershell
   python scripts/init_db.py
   ```

   ADVERTENCIA: esto ELIMINA Y VUELVE A CREAR TODAS LAS TABLAS de la base de datos de destino. Agrega `--no-seed` para omitir las filas de demostración (solo esquema y procedimientos).

4. Inicia la API:

   ```powershell
   uvicorn app.main:app --reload
   ```

5. Frontend (terminal nueva, desde la raíz del repositorio):

   ```powershell
   cd frontend
   npm install
   Copy-Item .env.example .env
   npm run dev
   ```

   Bash: `cp .env.example .env`.

URLs: API http://localhost:8000 (documentación en `/docs`, health en `/health`); frontend http://localhost:5173.

## Pruebas y linting

Desde `backend/` con el venv activo:

```powershell
pytest -q
ruff check .
```

`pytest -q` ejecuta las pruebas unitarias (máquina de estados, servicio, API con un repositorio falso, guarda de integración). Las pruebas de integración usan un MySQL real (procedimientos almacenados y repositorio), ELIMINAN y recrean las tablas, y se seleccionan por marcador. `TEST_DATABASE_URL` debe apuntar a una base de datos desechable, nunca al mismo valor que `DATABASE_URL` (la guarda se niega a ejecutar en ese caso):

```powershell
$env:TEST_DATABASE_URL="mysql://user:password@localhost:3306/tickets_test"
pytest -m integration
```

Bash: `TEST_DATABASE_URL=mysql://user:password@localhost:3306/tickets_test pytest -m integration`.

Desde `frontend/`:

```powershell
npm run lint
npm run build
```

## Resumen de la API

Documentación interactiva: `/docs`. Los campos JSON van en camelCase.

| Method | Path | Purpose |
|--------|------|---------|
| GET  | `/health` | Estado de disponibilidad y de la base de datos |
| GET  | `/api/transitions` | Tabla de transiciones permitidas |
| GET  | `/api/operators` | Lista de operadores |
| POST | `/api/tickets` | Crear ticket |
| GET  | `/api/tickets` | Listar; filtros `status`, `priority`, `operatorId`, `from`, `to`, `q` |
| GET  | `/api/tickets/{id}` | Detalle del ticket, incl. `allowedTransitions` |
| GET  | `/api/tickets/{id}/history` | Historial de eventos del ticket |
| POST | `/api/tickets/{id}/transitions` | Cambiar estado (`toStatus`, `diagnosis`, `comment`, `actor`, `version`) |
| POST | `/api/tickets/{id}/comments` | Agregar comentario |
| PUT  | `/api/tickets/{id}/assignee` | Asignar o desasignar operador |
| GET  | `/api/notifications` | Eventos recientes de estado/asignación (`since`, `limit`) |

Los errores son `application/problem+json` (RFC 7807) con un `code` estable:

```json
{
  "type": "about:blank",
  "title": "Unprocessable Entity",
  "status": 422,
  "detail": "Cannot move from PENDING to RESOLVED",
  "code": "INVALID_TRANSITION"
}
```

Códigos: 404 `TICKET_NOT_FOUND`, `OPERATOR_NOT_FOUND`; 409 `CONCURRENCY_CONFLICT`; 422 `INVALID_TRANSITION`, `DIAGNOSIS_REQUIRED`, `COMMENT_REQUIRED`, `COMMENT_EMPTY`, `TICKET_CLOSED`; 400 `VALIDATION_ERROR` (con `errors[{field,message}]`); 503 `DATABASE_UNAVAILABLE`; 500 `INTERNAL_ERROR`. Tabla completa: [docs/architecture.md](docs/architecture.md#error-handling).

## Despliegue

Guía completa: [docs/deploy-free-tier.md](docs/deploy-free-tier.md).

- Vercel: dos proyectos desde este repositorio, backend (Root Directory `backend`, FastAPI serverless) y frontend (Root Directory `frontend`, Vite estático). Aiven for MySQL (plan gratuito, TLS).
- Backend: `DATABASE_URL` con `?ssl-mode=REQUIRED`, `DB_SSL_CA` (texto PEM) y `CORS_ORIGINS` = origen del frontend. Frontend: `VITE_API_URL` en tiempo de build = URL del backend.
- Ejecuta `init_db.py` una sola vez, a mano, contra la URI de Aiven. A propósito no está en ningún comando de despliegue porque elimina tablas.
- Por qué no Railway: los registros nuevos están pausados tras su incidente de seguridad del 21 de octubre de 2026. La guía de Railway se conserva como alternativa: [docs/deploy-railway.md](docs/deploy-railway.md).

## Uso de IA

La asistencia de IA y los prompts utilizados están documentados en [PROMPTS.md](PROMPTS.md#español).

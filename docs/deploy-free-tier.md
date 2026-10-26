# Deploy on a free tier (Aiven + Vercel)

Railway paused new signups after its security incident (see status.railway.com, Oct 21 2026), and Azure is not available to me. So the primary deploy uses free services: Aiven for MySQL and two Vercel projects from the same repo, one for the FastAPI backend (serverless Python) and one for the React frontend (static Vite). The Railway guide ([deploy-railway.md](deploy-railway.md)) is kept as an alternative.

How it is wired:

- `backend/pyproject.toml` has `[tool.vercel] entrypoint = "app.main:app"`, so Vercel finds the FastAPI app with Root Directory `backend`. Dependencies come from `backend/requirements.txt`, Python 3.12 from `backend/.python-version`.
- The frontend needs no config file: Vercel detects Vite with Root Directory `frontend`.
- `backend/app/db.py` and `backend/scripts/init_db.py`: TLS support through `?ssl-mode=` in `DATABASE_URL`. `DB_SSL_CA` (PEM text) is written to a temp file, which works on Vercel (`/tmp` is writable).

## Warning: the init script drops all tables

`backend/scripts/init_db.py` runs `database/01_schema.sql`, which drops and recreates all tables. Every row is lost each time it runs. Run it once, by hand, in step B. Never put it in a build or start command.

## A. Aiven: MySQL

1. Sign up at aiven.io.
2. Create a service: MySQL, plan Free, the region nearest to you.
3. Wait until the service is Running.
4. Copy the Service URI. It looks like `mysql://avnadmin:PASSWORD@HOST:PORT/defaultdb?ssl-mode=REQUIRED`.
5. Download the CA certificate (`ca.pem`) from the service overview. Keep it outside the repo.
6. Change the path of the URI from `/defaultdb` to `/tickets`: `mysql://avnadmin:PASSWORD@HOST:PORT/tickets?ssl-mode=REQUIRED`. `init_db.py` creates that database.

## B. Initialize the database once

From PowerShell, in `backend/`:

```powershell
$env:DATABASE_URL = "mysql://avnadmin:PASSWORD@HOST:PORT/tickets?ssl-mode=REQUIRED"
$env:DB_SSL_CA_PATH = "C:\path\to\ca.pem"
.venv\Scripts\python scripts\init_db.py
Remove-Item Env:DATABASE_URL, Env:DB_SSL_CA_PATH
```

This drops and recreates the tables, then loads demo data. Run it only on a fresh database.

## C. Vercel: backend project

1. In Vercel: Add New > Project, import the GitHub repo.
2. Set Root Directory to `backend`. Framework preset: FastAPI (or auto-detected).
3. Add environment variables:
   - `DATABASE_URL`: the same URI as step B, with `/tickets`.
   - `DB_SSL_CA`: the full content of `ca.pem`, including the BEGIN and END lines.
   - `CORS_ORIGINS`: `http://localhost:5173` for now.
   - `LOG_LEVEL`: `INFO`.
4. Deploy. Note the domain, for example `https://<backend>.vercel.app`.
5. Open `https://<backend>.vercel.app/health`. It must report the database as ok. Open `/docs` to see the API docs.

## D. Vercel: frontend project

1. Add New > Project, import the same repo again.
2. Set Root Directory to `frontend`. Vite is detected.
3. Before the first deploy, add the environment variable `VITE_API_URL=https://<backend>.vercel.app` (no trailing slash).
4. Deploy. Note the domain, for example `https://<frontend>.vercel.app`.

## E. Allow the frontend origin

In the backend project, set `CORS_ORIGINS=https://<frontend>.vercel.app` (no trailing slash). Then Deployments > Redeploy, because env var changes apply only to new deployments.

## F. Smoke test and troubleshooting

Smoke test: open the frontend site, check the ticket list loads, open a ticket, make a valid state change, and try an invalid one to see the error message.

- CORS error in the browser console: `CORS_ORIGINS` must equal the frontend origin exactly (scheme and host, no trailing slash, no path). Redeploy the backend after changing it.
- Frontend calls `localhost:8000`: `VITE_API_URL` is baked in at build time. Set it, then Redeploy the frontend project.
- `/health` reports the database down or logs an SSL error: check that the URI has `?ssl-mode=REQUIRED` and that `DB_SSL_CA` holds the whole PEM. Without `DB_SSL_CA`, the connection is encrypted but the server is not verified, and a warning is logged.
- Where are the logs: backend project > Logs (Runtime Logs) in the Vercel dashboard.
- Function time limit (10 s on the free plan) does not matter here: each request is a few quick queries.
- First request after idle can be slower (serverless cold start). Retry.

## Lessons from the first deploy

- Vercel installs Python dependencies from `backend/pyproject.toml` when it exists, not from `requirements.txt`. Both lists are kept identical; `tests/test_dependencies.py` fails if they drift. Symptom when missing: `ModuleNotFoundError: No module named 'fastapi'` and `FUNCTION_INVOCATION_FAILED`.
- Use the production domain (no hash, e.g. `reto-tecnico-fractal-soluciones.vercel.app`). Per-deployment URLs with a hash are behind Vercel Authentication and return 302.
- Add env vars for the **Production** environment, then Redeploy. `VITE_API_URL` is baked in at build time; a missing value makes the frontend call `http://localhost:8000`.

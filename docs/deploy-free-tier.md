# Deploy on a free tier (Aiven + Render + Netlify)

Railway paused new signups after its security incident (see status.railway.com, Oct 21 2026), and Azure is not available to me. So the primary deploy uses three free services: Aiven for MySQL, Render for the FastAPI backend, and Netlify for the React frontend. The Railway guide ([deploy-railway.md](deploy-railway.md)) is kept as an alternative.

Config files already in the repo:

- `render.yaml`: Render Blueprint for the `tickets-api` web service (root `backend/`, `/health` check).
- `netlify.toml`: build in `frontend/` with Node 22, publish `dist`, SPA fallback to `/index.html`.
- `backend/app/db.py` and `backend/scripts/init_db.py`: TLS support through `?ssl-mode=` in `DATABASE_URL`.

## Warning: the init script drops all tables

`backend/scripts/init_db.py` runs `database/01_schema.sql`, which drops and recreates all tables. Every row is lost each time it runs. Run it once, by hand, in step B. Never put it in a build or start command.

## A. Aiven: MySQL

1. Sign up at aiven.io.
2. Create a service: MySQL, plan Free, the region nearest to you.
3. Wait until the service is Running.
4. Copy the Service URI. It looks like `mysql://avnadmin:PASSWORD@HOST:PORT/defaultdb?ssl-mode=REQUIRED`.
5. Download the CA certificate (`ca.pem`) from the service overview.
6. The default database is `defaultdb`. Change the path of the URI to `/tickets`: `mysql://avnadmin:PASSWORD@HOST:PORT/tickets?ssl-mode=REQUIRED`. `init_db.py` creates that database.

## B. Initialize the database once

From PowerShell, in `backend/`:

```powershell
$env:DATABASE_URL = "mysql://avnadmin:PASSWORD@HOST:PORT/tickets?ssl-mode=REQUIRED"
$env:DB_SSL_CA_PATH = "C:\path\to\ca.pem"
.venv\Scripts\python scripts\init_db.py
Remove-Item Env:DATABASE_URL, Env:DB_SSL_CA_PATH
```

This drops and recreates the tables, then loads demo data. Run it only on a fresh database.

## C. Render: backend

1. In Render: New > Blueprint (or New > Web Service) and pick the GitHub repo. The Blueprint reads `render.yaml`.
2. Set the environment variables that are marked as not synced:
   - `DATABASE_URL`: the same URI as step B, with `/tickets`.
   - `DB_SSL_CA`: paste the full content of `ca.pem`, including the BEGIN and END lines.
   - `CORS_ORIGINS`: `http://localhost:5173` for now.
3. Deploy.
4. Open `https://<render-domain>/health`. It must report the database as ok.

The free plan sleeps after 15 minutes without traffic. The first request after that takes about 50 seconds.

## D. Netlify: frontend

1. Netlify: Add new site > Import an existing project > GitHub, pick the repo. `netlify.toml` is picked up automatically.
2. Before the first deploy, add the environment variable `VITE_API_URL=https://<render-domain>` (no trailing slash).
3. Deploy. Note the Netlify domain.

## E. Render: allow the frontend origin

In Render, set `CORS_ORIGINS=https://<netlify-domain>` (no trailing slash) and redeploy.

## F. Smoke test and troubleshooting

Smoke test: open the Netlify site, check the ticket list loads, open a ticket, make a valid state change, and try an invalid one to see the error message.

- CORS error in the browser console: `CORS_ORIGINS` must equal the Netlify origin exactly (scheme and host, no trailing slash, no path). Redeploy Render after changing it.
- First request is slow or times out: Render free plan cold start (about 50 s). Retry.
- `/health` reports the database down or logs an SSL error: check that the URI has `?ssl-mode=REQUIRED` and that `DB_SSL_CA` holds the whole PEM. Without `DB_SSL_CA`, the connection is encrypted but the server is not verified, and a warning is logged.
- Frontend calls `localhost:8000`: `VITE_API_URL` is baked in at build time. Set it, then trigger a new Netlify deploy (clear cache and deploy).

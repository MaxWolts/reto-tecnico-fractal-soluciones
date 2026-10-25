# Deploy to Railway (dashboard, no CLI)

This guide deploys three things to one Railway project:

- a MySQL database service,
- the FastAPI backend (`backend/`),
- the React + Vite frontend (`frontend/`).

Config files already in the repo:

- `backend/railway.json`: Railpack build, start command, `/health` healthcheck, restart on failure. It has no pre-deploy command on purpose.
- `backend/.python-version`: Python `3.12`.
- `frontend/railway.json`: Railpack build. Railpack serves the Vite `dist` folder as a static site.
- `frontend/.env.example`: documents `VITE_API_URL`.

## Warning: the init script drops all tables

`backend/scripts/init_db.py` runs `database/01_schema.sql`, which **DROPS AND RECREATES ALL TABLES**. Every row is lost each time it runs. Run it **once**, by hand, in step d. Never add it to a deploy command, a pre-deploy command, or a startup hook. Do not run it again on a database that holds data you want to keep.

## a. Push the repo to public GitHub

Push the whole repository (`backend/`, `frontend/`, `database/`, `docs/`) to a public GitHub repository.

## b. Create the project and add a MySQL service

1. In Railway, click **New Project**, then **Empty Project**.
2. Click **+ New** > **Database** > **Add MySQL**.
3. Keep the service name `MySQL`. The variable references below depend on that exact name.
4. Open the MySQL service, then **Variables** (or **Connect**). Confirm these exist:
   - `MYSQL_URL`: used by the backend over the private network.
   - `MYSQL_PUBLIC_URL`: used from your own machine in step d. If it is missing, enable public networking / TCP proxy for the MySQL service first.

## c. Add the backend service

1. Click **+ New** > **GitHub Repo**, then pick the repository.
2. Open the new service, then **Settings**:
   - **Root Directory**: `backend`
   - **Config-as-code / Config File Path**: `backend/railway.json`. If the dashboard rejects this path, use `/backend/railway.json`. The path is always from the repo root.
3. Open **Variables** and add:
   - `DATABASE_URL` = `${{MySQL.MYSQL_URL}}`
   - `CORS_ORIGINS` = `http://localhost:5173` (placeholder for now; the real frontend URL is set in step e)
   - `LOG_LEVEL` = `INFO`
4. Open **Settings** > **Networking** > **Generate Domain**. Copy the URL, for example `https://backend-production-xxxx.up.railway.app`.
5. Wait for the deploy to finish. `/health` should return OK. The database is still empty at this point; that is expected.

## d. Initialize the database once, from your machine

Run this from your local `backend/` folder, in PowerShell. Use the **public** MySQL URL (`MYSQL_PUBLIC_URL`) from step b.

```powershell
cd D:\little-proyects\prueba-tec\backend
$env:DATABASE_URL="<MYSQL_PUBLIC_URL>"; .venv\Scripts\python scripts\init_db.py
```

- This **drops all tables** on the Railway database, then recreates the schema, the stored procedures, and the demo data.
- To create only the schema and procedures with no demo rows, add `--no-seed`:

  ```powershell
  $env:DATABASE_URL="<MYSQL_PUBLIC_URL>"; .venv\Scripts\python scripts\init_db.py --no-seed
  ```

- The script creates the database if it does not exist.
- Clear the variable afterwards so later local runs do not hit Railway by mistake: `Remove-Item Env:DATABASE_URL`.

## e. Add the frontend service

1. Click **+ New** > **GitHub Repo**, pick the same repository.
2. Open the new service, then **Settings**:
   - **Root Directory**: `frontend`
   - **Config File Path**: `frontend/railway.json`
3. Open **Variables** and add `VITE_API_URL` = `https://backend-production-xxxx.up.railway.app` (the backend URL from step c, no trailing slash).
   - `VITE_API_URL` is a **build-time** value. Vite bakes it into the JavaScript during the build. Set it **before** the build runs. If you change it later, trigger a new deploy so the build runs again.
4. **Settings** > **Networking** > **Generate Domain**. Copy the URL, for example `https://frontend-production-yyyy.up.railway.app`.
5. Go back to the **backend** service, **Variables**, and set `CORS_ORIGINS` = `https://frontend-production-yyyy.up.railway.app`. Use the exact origin: scheme and host, **no trailing slash**. Then **Redeploy** the backend.

## f. Smoke test

1. Open `https://<backend-domain>/health`. It should return a healthy response.
2. Open `https://<backend-domain>/docs`. The FastAPI Swagger page should load.
3. Open the frontend URL. The ticket list should load with the demo data (or empty, if you used `--no-seed`).
4. Create a new ticket.
5. Move the ticket to another status using the ticket drawer's status actions.
6. Open the ticket's history and confirm the status change is listed.

If step 3 shows errors, check the troubleshooting section below first.

## g. Troubleshooting

- **Browser console shows a CORS error** (`blocked by CORS policy`): `CORS_ORIGINS` on the backend must match the frontend origin exactly, including `https://`, and must have **no trailing slash**. After changing it, redeploy the backend.
- **503 from the backend, or the database is unreachable**: check that `DATABASE_URL` is the reference `${{MySQL.MYSQL_URL}}` exactly. The service name in the reference must be `MySQL`. Check that the MySQL service is running. Check the backend's deploy logs.
- **Frontend calls `http://localhost:8000`**: `VITE_API_URL` was not set when the frontend was built. Set `VITE_API_URL` in the frontend service variables, then trigger a new deploy so the build runs again. Changing the variable alone does not change a build that already happened.
- **Tables are empty after a deploy**: this is expected. Redeploys do not touch the database. Only step d (`init_db.py`) drops and recreates tables, so do not rerun it unless you want to wipe the data.

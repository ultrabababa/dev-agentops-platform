# Public Showcase Deployment

This document describes the public read-only deployment of the DevAgentOps Evaluation Explorer.

The deployment intentionally separates the frontend and API:

```text
Render Static Site
  React / Vite
  VITE_API_BASE_URL=https://<api-host>/api
        |
        v
Render Web Service
  FastAPI / Uvicorn
  read-only showcase catalog + frozen SQLite snapshots
```

The frontend stays available as a static site even when the free API instance is sleeping. The API contains no public write endpoints and reads the frozen sanitized showcase data bundled with the repository.

## 1. Preflight

From the repository root:

```bash
pytest -q -p no:cacheprovider

cd frontend
npm ci
npm test
npm run build
cd ..

git diff --check
```

## 2. Deploy the FastAPI service first

The repository root contains `render.yaml` for the API service.

In Render:

1. Sign in and connect the GitHub repository `ultrabababa/dev-agentops-platform`.
2. Create a new Blueprint and select this repository.
3. Use `render.yaml` from the repository root.
4. Create the `devagentops-showcase-api` service.
5. Wait for the first deployment to finish.

The Blueprint configures:

```text
Runtime: Python
Plan: Free
Region: Singapore
Build: pip install -e .
Start: uvicorn devagentops.api:app --host 0.0.0.0 --port $PORT
Health check: /health
DEVAGENTOPS_SHOWCASE_CATALOG_PATH=showcase-data/catalog.json
```

After deployment, record the public API origin, for example:

```text
https://devagentops-showcase-api.onrender.com
```

Verify it before creating the frontend:

```bash
curl -fsS https://<api-host>/health
curl -fsS https://<api-host>/api/overview
```

Expected health response:

```json
{"status":"ok"}
```

`/api/overview` must return the real public Evaluation Explorer overview, not a 404.

## 3. Create the static frontend

Create a **Static Site** in Render from the same GitHub repository.

Use these settings:

```text
Branch: main
Root Directory: frontend
Build Command: npm ci && npm run build
Publish Directory: dist
```

Add this build-time environment variable:

```text
VITE_API_BASE_URL=https://<api-host>/api
```

Do not add a trailing slash after `/api`.

Because the Explorer uses client-side routing, add this rewrite:

```text
Source: /*
Destination: /index.html
Action: Rewrite
```

Deploy the static site and record its public origin, for example:

```text
https://devagentops-showcase.onrender.com
```

## 4. Allow the frontend origin in FastAPI CORS

Open the Render API service and add this environment variable:

```text
DEVAGENTOPS_CORS_ORIGINS=https://<frontend-host>
```

Use the frontend **origin only**:

```text
https://devagentops-showcase.onrender.com
```

Do not include a path and do not use `*`.

Multiple explicit origins can be supplied as a comma-separated list if a second trusted frontend is intentionally deployed:

```text
https://example-a.com,https://example-b.com
```

After changing the environment variable, redeploy/restart the API service.

Verify the CORS response:

```bash
curl -sS -D - -o /dev/null \
  -H 'Origin: https://<frontend-host>' \
  https://<api-host>/api/overview
```

The response headers should contain:

```text
access-control-allow-origin: https://<frontend-host>
```

## 5. Public smoke test

Open the deployed frontend and verify at least:

```text
/
/conditions
/conditions/l4
/runs
/compare
/cases
```

Then open one real Run and one Sample drill-down page and verify:

- Structured Report renders;
- Evidence renders;
- Trajectory is either real data or an honest unavailable state;
- Trace is separate from Trajectory;
- no provider reasoning/thinking is exposed;
- direct browser refresh on a nested route does not 404;
- the browser console has no CORS errors;
- `/compare` keeps the fresh-generation causal boundary and fixed-output replay distinction.

## 6. Free-tier behavior

The static frontend is independent of the FastAPI process. On Render's free web-service plan, the API can sleep after inactivity and the first API request after a cold period can take longer while the service wakes up.

Do not treat the first cold request latency as a DevAgentOps Runtime benchmark result; it is hosting behavior only.

## 7. Environment variables

### Backend

| Variable | Purpose |
| --- | --- |
| `DEVAGENTOPS_SHOWCASE_CATALOG_PATH` | Path to the read-only public showcase catalog. Render uses `showcase-data/catalog.json`. |
| `DEVAGENTOPS_CORS_ORIGINS` | Comma-separated explicit browser origins allowed to call the API. |

### Frontend

| Variable | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Build-time base URL for the public API, including `/api`. |

Vite environment variables are compiled into the static bundle at build time. Changing `VITE_API_BASE_URL` requires a frontend rebuild/redeploy.

## 8. Deployment boundary

The public deployment must remain read-only:

- no evaluation execution endpoint;
- no database writes;
- no authentication/user state;
- no raw `.devagentops/` databases;
- no hidden evaluator answer bodies;
- no provider reasoning/thinking.

The deployed Explorer is a presentation and evidence-inspection surface for already-frozen formal experiment data.

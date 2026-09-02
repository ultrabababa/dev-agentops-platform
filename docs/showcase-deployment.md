# Public Showcase Deployment

This document describes the production public deployment of the DevAgentOps Evaluation Explorer.

## Production endpoints

```text
Frontend
https://devagentops.onrender.com

Backend API origin
https://devagentops-showcase-api.onrender.com

Explorer API base
https://devagentops-showcase-api.onrender.com/api

Architecture Explorer
https://devagentops.onrender.com/architecture
```

The deployment intentionally separates the static frontend and read-only API:

```text
https://devagentops.onrender.com
  Render Static Site
  React / Vite
  VITE_API_BASE_URL=https://devagentops-showcase-api.onrender.com/api
        |
        v
https://devagentops-showcase-api.onrender.com
  Render Web Service
  FastAPI / Uvicorn
  read-only showcase catalog + frozen sanitized SQLite snapshots
```

The frontend stays available as a static site even when the free API instance is sleeping. The API contains no public write endpoints and reads frozen sanitized showcase data bundled with the repository.

The Architecture Explorer is also static-only. Its Archify HTML/SVG assets are built from the versioned files under `docs/architecture/` and do not depend on the FastAPI process.

## Backend deployment

The repository root contains `render.yaml` for the API service.

Current production service:

```text
Name: devagentops-showcase-api
Runtime: Python
Plan: Free
Region: Singapore
Build: pip install -e .
Start: uvicorn devagentops.api:app --host 0.0.0.0 --port $PORT
Health check: /health
DEVAGENTOPS_SHOWCASE_CATALOG_PATH=showcase-data/catalog.json
```

Production health checks:

```bash
curl -fsS https://devagentops-showcase-api.onrender.com/health
curl -fsS https://devagentops-showcase-api.onrender.com/api/overview
```

Expected health response:

```json
{"status":"ok"}
```

`/api/overview` must return the public Evaluation Explorer overview rather than a 404.

## Frontend deployment

The frontend is a separate Render **Static Site** built from the same repository.

Production settings:

```text
Name: devagentops
Branch: main
Root Directory: frontend
Build Command: npm ci && npm run build
Publish Directory: dist
```

Build-time environment variable:

```text
VITE_API_BASE_URL=https://devagentops-showcase-api.onrender.com/api
```

Before both `npm run dev` and `npm run build`, npm lifecycle hooks execute:

```text
npm run sync:architecture
```

`frontend/scripts/sync-architecture.mjs` copies the frozen Archify HTML/SVG outputs from:

```text
docs/architecture/
```

into the generated Vite public-assets directory:

```text
frontend/public/architecture-assets/
```

That destination is gitignored. `docs/architecture/` remains the only version-controlled source of the rendered architecture artifacts; do not maintain a second committed copy under `frontend/`.

Because the Explorer uses client-side routing, the Static Site must keep this rewrite:

```text
Source: /*
Destination: /index.html
Action: Rewrite
```

Without that rewrite, direct browser refreshes on nested routes such as `/compare`, `/runs/...`, `/conditions/l4` or `/architecture` can return a hosting-layer 404.

Static files under `/architecture-assets/` must continue to be served as files rather than routed through the SPA rewrite.

## CORS

The FastAPI service uses an explicit allowlist rather than wildcard CORS.

Production backend environment variable:

```text
DEVAGENTOPS_CORS_ORIGINS=https://devagentops.onrender.com
```

Do not add a trailing slash and do not use `*`.

Multiple trusted origins may be supplied only when intentionally needed:

```text
https://example-a.com,https://example-b.com
```

Verify production CORS:

```bash
curl -sS -D - -o /dev/null \
  -H 'Origin: https://devagentops.onrender.com' \
  https://devagentops-showcase-api.onrender.com/api/overview
```

The response should contain:

```text
access-control-allow-origin: https://devagentops.onrender.com
```

## Public smoke test

The production frontend should be checked at least at:

```text
https://devagentops.onrender.com/
https://devagentops.onrender.com/conditions
https://devagentops.onrender.com/conditions/l4
https://devagentops.onrender.com/runs
https://devagentops.onrender.com/compare
https://devagentops.onrender.com/cases
https://devagentops.onrender.com/architecture
```

Architecture assets should also be checked directly:

```text
https://devagentops.onrender.com/architecture-assets/system.html
https://devagentops.onrender.com/architecture-assets/evaluation-workflow.html
https://devagentops.onrender.com/architecture-assets/l4-runtime.html
```

Verify that the `/architecture` page can switch among all three views, render the embedded diagrams, and open each full interactive Archify document in a new tab.

Then open one real Run and one Sample drill-down and verify:

- Structured Report renders;
- Evidence renders;
- Trajectory is real model-visible interaction data or an honest unavailable state;
- Trace remains separate from Trajectory;
- provider reasoning/thinking is not exposed;
- direct browser refresh on a nested route does not 404;
- browser console has no CORS error;
- `/compare` keeps fresh-generation causal boundaries and the fixed-output replay distinction.

## Free-tier behavior

The static frontend is independent of the FastAPI process. On Render's free web-service plan, the API can sleep after inactivity and the first API request after a cold period can take longer while the service wakes up.

Do not interpret the first cold request latency as a DevAgentOps Runtime benchmark result. It is hosting behavior only.

The `/architecture` route and `/architecture-assets/*` remain available while the API is sleeping because they are part of the static frontend deployment.

## Environment variables

### Backend

| Variable | Production value | Purpose |
| --- | --- | --- |
| `DEVAGENTOPS_SHOWCASE_CATALOG_PATH` | `showcase-data/catalog.json` | Read-only public showcase catalog. |
| `DEVAGENTOPS_CORS_ORIGINS` | `https://devagentops.onrender.com` | Explicit browser origin allowed to call the API. |

### Frontend

| Variable | Production value | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `https://devagentops-showcase-api.onrender.com/api` | Build-time public API base URL. |

Vite environment variables are compiled into the static bundle at build time. Changing `VITE_API_BASE_URL` requires a frontend rebuild/redeploy.

## Deployment boundary

The public deployment must remain read-only:

- no evaluation execution endpoint;
- no database writes;
- no authentication/user state;
- no raw `.devagentops/` databases;
- no hidden evaluator answer bodies;
- no provider reasoning/thinking;
- no unsanitized raw message/manifest dump.

The deployed Explorer is a presentation, evidence-inspection and experiment-attribution surface for already-frozen formal experiment data. Architecture HTML/SVG is static documentation and does not widen the API or execution boundary.

## Local preflight before deployment changes

From the repository root:

```bash
pytest -q -p no:cacheprovider

cd frontend
npm ci
npm run sync:architecture
npm test
npm run build
cd ..

git diff --check
```

Deployment changes should not alter frozen evaluation results or Runtime Treatment identities unless a separate experiment explicitly requires that change.

---
phase: 05-deployment-documentation
plan: 01
subsystem: infra
tags: [railway, docker, caddy, reflex, deployment, scipy]

# Dependency graph
requires:
  - phase: 04-portfolio-optimization
    provides: portfolio_optimization.py using scipy.optimize.minimize
provides:
  - Dockerfile with Caddy reverse proxy for Railway single-container deployment
  - railway.toml with DOCKERFILE builder, /ping health check, 180s timeout
  - rxconfig.py reads API_URL from environment (localhost fallback for dev)
  - 7 demo company financial JSONs committed to git (DEPLOY-02)
  - 7 demo company price JSONs committed to git (DEPLOY-02)
  - requirements.txt with scipy, without dev-only matplotlib/seaborn/jupyter/nbconvert
  - .gitignore with explicit exceptions for all 14 demo data files
affects: [05-02-readme, 05-03-inline-comments]

# Tech tracking
tech-stack:
  added: [caddy, docker, railway.toml, Node.js 20 (build-time only)]
  patterns: [single-container reverse proxy pattern — Caddy fronts static + proxies backend; embedded Caddyfile via RUN printf avoids formatting warnings]

key-files:
  created:
    - Dockerfile
    - railway.toml
  modified:
    - requirements.txt
    - .gitignore
    - rxconfig.py

key-decisions:
  - "Dockerfile + embedded Caddyfile over nixpacks — avoids 15-min WebSocket disconnection issue with external Caddy"
  - "PORT:-8080 default in Caddyfile; Railway injects PORT at runtime"
  - "API_URL read from os.environ with localhost:8000 fallback — backward compatible for local dev"
  - "reflex export --frontend-only --no-zip at build time; reflex run --backend-only at runtime"
  - "Demo data (14 files) committed to git so Railway deployment works on first visit without manual setup"
  - "Премиум financial JSON has embedded double-quotes in filename; gitignore pattern !data/\"_Премиум_Нэксус_\"_ХК_2025.json handles it"
  - "Premim price JSON: Премиум Нэксус  ХК.json (double-space variant) is the correct file per D-06"

patterns-established:
  - "Single-container Railway deployment: python:3.12-slim + Caddy + Node.js 20 for Reflex apps"
  - "Embedded Caddyfile via RUN printf to avoid format validation errors on build"
  - "ENV-driven api_url in rxconfig.py pattern for Railway/Render deployments"

requirements-completed: [DEPLOY-01, DEPLOY-02]

# Metrics
duration: 20min
completed: 2026-04-01
---

# Phase 5 Plan 01: Railway Deployment Infrastructure Summary

**Dockerfile with Caddy reverse proxy, railway.toml, updated rxconfig.py, and 14 demo data files committed — Railway deployment ready**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-04-01T03:29:44Z
- **Completed:** 2026-04-01T03:49:44Z
- **Tasks:** 3 + 1 bonus (demo data commit)
- **Files modified:** 5 config files + 14 data files

## Accomplishments

- Created Dockerfile: python:3.12-slim + Caddy + Node.js 20; builds static frontend via `reflex export`, serves via Caddy with backend proxy
- Created railway.toml: DOCKERFILE builder, /ping health check, 180s timeout, ON_FAILURE restart policy
- Updated rxconfig.py: `api_url=os.environ.get("API_URL", "http://localhost:8000")` — frontend WebSocket connects to Railway HTTPS URL when deployed
- Fixed requirements.txt: added scipy>=1.11.0, removed matplotlib/seaborn/jupyter/nbconvert (dev deps causing build timeouts)
- Updated .gitignore: added exceptions for all 7 demo financial JSONs and 7 demo price JSONs
- Committed all 14 demo data files so app works on first Railway visit (DEPLOY-02)

## Task Commits

1. **Task 1: Fix requirements.txt and .gitignore** - `29aa259` (chore)
2. **Task 2: Write Dockerfile and railway.toml** - `4ecf3fb` (feat)
3. **Task 3: Update rxconfig.py with API_URL env var** - `0e1c720` (feat)
4. **Bonus: Commit demo data files for DEPLOY-02** - `060d2c9` (chore)

## Files Created/Modified

- `Dockerfile` - Single-container Railway build: python:3.12-slim + Caddy + Node.js 20; embedded Caddyfile; `reflex export` build + `reflex run --backend-only` runtime
- `railway.toml` - Railway build config: DOCKERFILE builder, /ping healthcheck, 180s timeout, ON_FAILURE restart
- `rxconfig.py` - Added `import os` and `api_url=os.environ.get("API_URL", "http://localhost:8000")`
- `requirements.txt` - scipy added; matplotlib/seaborn/jupyter/nbconvert removed
- `.gitignore` - Added exceptions for 7 financial JSONs + 7 price JSONs in data/ and data/prices/
- `data/АПУ_2025.json` etc. (7 files) - Demo company financial data committed
- `data/prices/АПУ.json` etc. (7 files) - Demo company price history committed

## Decisions Made

- Used embedded Caddyfile pattern (`RUN printf ...`) instead of a separate `Caddyfile` file — avoids Caddy's format-check warnings on startup that can cause WebSocket disconnects
- `PORT:-8080` default in Caddyfile — Railway injects `$PORT` at runtime; 8080 works for local Docker testing
- `reflex export --frontend-only --no-zip` at image build time; static files moved to `/srv`; Caddy serves from `/srv`
- Backend runs on port 8000 always; Caddy proxies `/_event/*`, `/ping`, `/_upload/*` to it
- Committed demo data files as a bonus task because `must_haves.truths` explicitly requires "All 7 demo companies' financial and price JSONs are tracked in git and committed"

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Committed demo data files**
- **Found during:** Post-task verification
- **Issue:** Plan must_haves stated "All 7 demo companies' financial and price JSONs are tracked in git and committed" — simply updating .gitignore is insufficient without an actual commit of the data files
- **Fix:** Staged and committed all 14 demo data files (7 financial + 7 price JSONs) as a separate atomic commit
- **Files modified:** 14 data files in data/ and data/prices/
- **Verification:** `git log --oneline` shows commit 060d2c9 with 14 files
- **Committed in:** `060d2c9`

---

**Total deviations:** 1 auto-fixed (Rule 2 — missing critical)
**Impact on plan:** Required for DEPLOY-02 correctness. No scope creep.

## Issues Encountered

- Премиум financial JSON filename contains embedded double-quote characters (`"_Премиум_Нэксус_"_ХК_2025.json`). The .gitignore exception required writing the exact filename with quotes as `!data/"_Премиум_Нэксус_"_ХК_2025.json` — Python write was used to ensure exact bytes were written correctly.
- `git check-ignore -v` with negation rules always exits 0 and prints the matching negation line — this is normal behavior; actual un-ignore status confirmed via `git status` showing files as untracked.

## User Setup Required

After Railway deployment, the user must set one environment variable:

```
API_URL=https://{your-app}.up.railway.app
```

Then redeploy. Without this, the frontend WebSocket connects to `localhost:8000` and all state events fail in production.

## Next Phase Readiness

- Deployment infrastructure complete — ready for Railway deploy
- README rewrite (05-02) and inline comments (05-03) can proceed independently
- Post-first-deploy: set API_URL env var in Railway dashboard, then redeploy

---
*Phase: 05-deployment-documentation*
*Completed: 2026-04-01*

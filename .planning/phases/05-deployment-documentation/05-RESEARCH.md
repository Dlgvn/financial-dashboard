# Phase 5: Deployment & Documentation — Research

**Researched:** 2026-03-30
**Domain:** Railway deployment (Reflex 0.8.26), gitignore management, README authoring, inline comments
**Confidence:** MEDIUM — Railway/Reflex deployment has known complexity; findings are cross-referenced from official docs, Railway help station, and community reports

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Deploy to Railway (not Render). Railway's Nixpacks auto-detects Python; better Reflex community reports; simpler configuration via `railway.toml`.
- **D-02:** No environment variables needed in the deployed app — the app uses flat JSON files only. Strip `ALPHA_VANTAGE_API_KEY` and `DATABASE_URL` from any deployment config (these are leftover dev artifacts in `.env`, not used by the app).
- **D-03:** Deployment config: `railway.toml` at project root. Start command: `reflex run --env prod` (or equivalent for production mode). Build command handles `pip install -r requirements.txt`.
- **D-04:** `requirements.txt` must be audited before deploy — `scipy` is missing (needed by Phase 4 optimizer). Add it before creating the Railway config.
- **D-05:** Un-gitignore the 7 demo companies' files by adding explicit `!` exceptions to `.gitignore`. Ship both financial JSONs and price JSONs.
- **D-06:** Files to un-gitignore (financial): `АПУ_2025.json`, `Хаан_банк_2025.json`, `Мандал_даатгал_2025.json`, `Сүү_2025.json`, `Моносхүнс_2025.json`, `Дархан_нэхий_ХК_2025.json`, `_Премиум_Нэксус_ХК_2025.json`, `index.json`. Prices: `АПУ.json`, `Хаан банк.json`, `Мандал даатгал.json`, `Сүү.json`, `Моносхүнс.json`, `Дархан нэхий ХК.json`, `Премиум Нэксус  ХК.json`.
- **D-07:** All other `data/*.json` and `data/prices/*.json` remain gitignored. Only demo file exceptions added.
- **D-08:** README tone: both capstone evaluator and GitHub portfolio audience.
- **D-09:** README includes detailed methodology section: Piotroski F-Score (9 criteria, F7 N/A), Beneish M-Score (8 indices, threshold −1.78, DEPI N/A), Altman Z-Score (Safe > 2.99, Grey 1.23–2.99, Distress < 1.23), Composite Health Score formula (weights: profitability 25%, liquidity 20%, solvency 20%, activity 15%, Altman 10%, Piotroski 10%; −10 Beneish penalty), mean-variance optimization (max-Sharpe SLSQP, efficient frontier sampling).
- **D-10:** README section order: project description + live demo URL → features → methodology → tech stack → data sources → local setup → known issues/limitations → future improvements → author.
- **D-11:** No screenshots for this phase — deferred.
- **D-12:** Known issues to document: F7 always N/A, DEPI always N/A, P/E and P/BV require manual shares-outstanding input.
- **D-13:** Inline comments in: `portfolio_optimization.py`, `excel_parser.py` (header_mappings.py), `ratios.py`.
- **D-14:** Comments explain why (formula source, threshold meaning, limitation), not just what.
- **D-15:** `.env` already in `.gitignore` — confirmed.
- **D-16:** Audit all Python files for hardcoded credentials before deploy commit.
- **D-17:** Railway deployment requires zero secrets configured.

### Claude's Discretion

- Exact `railway.toml` and `nixpacks.toml` configuration details — research Reflex 0.8.26 Railway deploy requirements.
- Order and exact wording of README sections — follow D-10 structure.
- Which specific code lines need comments vs which are self-explanatory — follow D-13 file list.

### Deferred Ideas (OUT OF SCOPE)

- Screenshots — deferred. When ready: Screener, Upload flow, Portfolio page, Company detail page. Place in `assets/screenshots/`.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEPLOY-01 | App deployed to Railway with stable public HTTPS URL accessible without login | Railway deployment architecture, railway.toml config, Reflex prod command |
| DEPLOY-02 | Demo data (7 companies' financial JSONs + price JSONs) bundled into deployment so app works on first visit | gitignore exception pattern, data file inventory, Премиум naming anomaly |
| DOCS-01 | README contains: project description, live demo URL, feature list, tech stack, data sources, setup, known issues, future improvements, author | README section map, existing v1 content to preserve/expand |
| DOCS-02 | Code has inline comments for non-obvious logic (portfolio_optimization.py, ratios.py, excel_parser.py/header_mappings.py) | Source code audit — key formulas identified in each file |
| DOCS-03 | No API keys or secrets committed; .env confirmed in .gitignore | .env contents verified, .gitignore verified, no hardcoded secrets found in Python files |
</phase_requirements>

---

## Summary

Phase 5 has five distinct work areas: (1) fix requirements.txt, (2) un-gitignore demo data, (3) write Railway config, (4) rewrite README, and (5) add inline comments. All five are independent and can be parallelized within the plan.

The most technically risky area is the Railway deployment. Reflex 0.8.26 runs a frontend (Next.js, port 3000) and a backend (FastAPI/uvicorn, port 8000) as separate processes. Railway expects a single port. The recommended working approach is a Dockerfile with Caddy as a reverse proxy to unify both services on a single `$PORT`. An alternative — nixpacks with `reflex run --env prod` as the start command and a single-port trick — exists but has a documented 15-minute WebSocket disconnection issue when Caddy runs externally. The Dockerfile + embedded Caddyfile approach avoids this.

The data bundling is straightforward: `.gitignore` uses `!data/filename.json` exceptions, but there is a naming anomaly to resolve first: the financial JSON for Премиум is stored as `"_Премиум_Нэксус_"_ХК_2025.json` (with embedded quotes in the name) and there are two price files (`Премиум Нэксус  ХК.json` with double space and `Премиум Нэксус ХК.json` with single space). The correct file for deployment must be identified and the gitignore exception written to match exactly.

**Primary recommendation:** Use a Dockerfile with an embedded Caddyfile for Railway deployment. Set `api_url` in rxconfig.py to the Railway-assigned HTTPS URL. Add scipy to requirements.txt immediately. Un-gitignore demo files with exact filename matches.

---

## Standard Stack

### Core (already in project)
| Library | Version in requirements.txt | Purpose | Notes |
|---------|----------------------------|---------|-------|
| reflex | 0.8.26 | Web framework | Pinned — do not change |
| scipy | MISSING — must add | Portfolio optimization (SLSQP) | Add `scipy>=1.11.0`; 1.17.0 confirmed in venv |
| numpy | >=2.0 (transitive via reflex) | Array math | Already installed |
| openpyxl | >=3.1.0 | Excel parsing | Already present |
| xlrd | >=2.0.0 | Legacy .xls parsing | Already present |
| pandas | >=2.0.0 | Data utilities | Already present |
| requests | >=2.32.0 | HTTP scraper | Already present |
| beautifulsoup4 | >=4.12.0 | HTML scraper | Already present |

### Deployment-specific (new)
| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| Caddy | 2.x (via apt) | Reverse proxy unifying frontend + backend on single port | Embedded in Dockerfile |
| Docker | — | Container build for Railway | Write Dockerfile at project root |

### Not needed
- nixpacks.toml — optional and frequently ignored on Railway; Dockerfile approach is more reliable for Reflex
- Procfile — Railway ignores this in favor of railway.toml startCommand or Dockerfile CMD

**Requirements.txt fix:**
```
# Add to requirements.txt
scipy>=1.11.0
```

Remove `matplotlib>=3.7.0`, `seaborn>=0.12.0`, `jupyter>=1.0.0`, `nbconvert>=7.0.0` — these are dev/notebook dependencies that are not used by the Reflex app at runtime and will slow down Railway builds.

---

## Architecture Patterns

### Reflex Production Deployment Architecture

Reflex in production runs two processes:
- **Frontend:** Next.js static files or dev server on port 3000
- **Backend:** FastAPI + uvicorn on port 8000 (WebSocket at `/_event/`)

Railway expects a single public port (injected as `$PORT` env var). The bridge is Caddy.

**Single-container approach (recommended):**

```
Railway container (single service)
├── Caddy (:$PORT)
│   ├── /_event/* → localhost:8000  (WebSocket, backend)
│   ├── /ping     → localhost:8000  (health check)
│   ├── /_upload/ → localhost:8000  (file upload)
│   └── /*        → /srv/           (static frontend files)
├── reflex run --env prod --backend-only  (port 8000)
└── /srv/   ← reflex export --frontend-only writes here
```

### Dockerfile Pattern for Reflex + Railway

```dockerfile
# Source: official Reflex docker-example + Railway single-port adaptation
FROM python:3.12-slim

# Install Caddy and Node.js (required by Reflex for frontend build)
RUN apt-get update && apt-get install -y curl gnupg2 debian-keyring debian-archive-keyring \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' > /etc/apt/sources.list.d/caddy-stable.list \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get update && apt-get install -y caddy nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build frontend static files
RUN reflex export --frontend-only --no-zip \
    && mv .web/_static /srv

# Embed Caddyfile to avoid the "caddy fmt" formatting warning that causes disconnects
RUN printf ':%s {\n  encode gzip\n  @backend path /_event/* /ping /_upload/*\n  reverse_proxy @backend localhost:8000\n  root * /srv\n  file_server\n  try_files {path} /404.html\n}\n' "${PORT:-8080}" > /Caddyfile

EXPOSE 8080
# Start backend and Caddy; PORT is set by Railway at runtime
CMD ["sh", "-c", "reflex run --env prod --backend-only --backend-port 8000 & caddy run --config /Caddyfile --adapter caddyfile"]
```

**Critical: api_url must be set.** Railway assigns a unique HTTPS URL. This must be passed into rxconfig.py so the browser knows where to connect WebSocket. Options:

Option A — hardcode after Railway assigns URL (simplest):
```python
# rxconfig.py
import reflex as rx
import os

config = rx.Config(
    app_name="financial_dashboard",
    api_url=os.environ.get("API_URL", "http://localhost:8000"),
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)
```

Then set `API_URL=https://your-app.up.railway.app` as a Railway environment variable (not a secret — it's the public URL).

Option B — set `REFLEX_API_URL` in Railway dashboard (as of Reflex 0.7.13+, all env vars must be `REFLEX_`-prefixed).

### gitignore Exception Pattern

Current `.gitignore` state:
```
data/*.json
!data/company_registry.json
```

Extended pattern for demo files:
```gitignore
data/*.json
!data/company_registry.json
!data/index.json
!data/АПУ_2025.json
!data/Хаан_банк_2025.json
!data/Мандал_даатгал_2025.json
!data/Сүү_2025.json
!data/Моносхүнс_2025.json
!data/Дархан_нэхий_ХК_2025.json
# NOTE: actual filename has embedded quotes — verify exact name before committing
!data/"_Премиум_Нэксус_"_ХК_2025.json

data/prices/*.json
!data/prices/АПУ.json
!data/prices/Хаан банк.json
!data/prices/Мандал даатгал.json
!data/prices/Сүү.json
!data/prices/Моносхүнс.json
!data/prices/Дархан нэхий ХК.json
# NOTE: Two price files exist for Премиум — double space version is the correct one per D-06
!data/prices/Премиум Нэксус  ХК.json
```

**gitignore limitation:** Git's `!` exception pattern for files with special characters (quotes, spaces) must use the exact filename as it appears on disk. Filenames with embedded double-quote characters (`"`) in gitignore patterns may not work correctly on all systems — the planner should note this risk and verify after committing.

### Anti-Patterns to Avoid

- **Running `reflex run` without `--env prod`:** Development mode rebuilds on every change, runs a hot-reload server, and is significantly slower. Railway will deploy in dev mode and waste memory.
- **External Caddyfile with caddy fmt warning:** The Caddyfile formatting warning at startup can cause early WebSocket disconnects. Embed the Caddyfile inline in the Dockerfile via `RUN printf ...` to sidestep the issue.
- **Setting `data/*.json` exclusion without `data/prices/*.json` exclusion:** The current `.gitignore` only has `data/*.json` — there is no rule for `data/prices/*.json`. The price files are currently tracked (modified in git status). Adding `data/prices/*.json` with `!` exceptions is needed to prevent all 155 non-demo price files from being committed.
- **Not setting `api_url`:** If `api_url` is not set, the frontend's WebSocket connects to `localhost:8000` — which works locally but fails in production because the browser cannot reach the container's localhost.
- **Including jupyter/matplotlib in requirements.txt for Railway:** These pull in large transitive dependencies (scipy is already ~40MB; adding jupyter doubles the image size) and cause build timeouts.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Single-port serving (frontend + backend) | Custom Python HTTP proxy | Caddy with embedded Caddyfile | Caddy handles WebSocket proxying, gzip, static files, path routing in ~10 lines |
| WebSocket proxying | Manual upgrade handling | Caddy `reverse_proxy` | WebSocket upgrades are handled transparently |
| Frontend build | Custom Node.js build pipeline | `reflex export --frontend-only` | Official Reflex command; produces static files in `.web/_static` |
| Secrets detection | Manual grep | Git audit (no new tool needed) | .env already gitignored; audit is a one-time `grep -r` check |

---

## Runtime State Inventory

This phase is a deployment and documentation phase. There is no rename/refactor. However, because deployment introduces a new runtime environment, key state items are noted.

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | `data/*.json` flat files — 7 demo files must be committed to git | gitignore exceptions per D-06 |
| Live service config | None — app has no external service integrations in deployment | None |
| OS-registered state | None — no scheduled tasks or registered processes | None |
| Secrets/env vars | `.env` contains `ALPHA_VANTAGE_API_KEY` and `DATABASE_URL` — these are NOT used by the Reflex app. Confirmed `.env` is in `.gitignore`. | No action on secrets; set `API_URL` as Railway env var (non-secret, public URL) after first deploy |
| Build artifacts | `venv/`, `.web/`, `__pycache__/` — all gitignored | None |

**Naming anomaly — must resolve before gitignore work:**
- Financial JSON: actual filename on disk is `"_Премиум_Нэксус_"_ХК_2025.json` (with literal double-quote characters). The CONTEXT.md D-06 lists it without quotes as `_Премиум_Нэксус_ХК_2025.json`. These do not match. The planner must use the exact on-disk name.
- Price files: two files exist — `Премиум Нэксус  ХК.json` (double space) and `Премиум Нэксус ХК.json` (single space). D-06 says `Премиум Нэксус  ХК.json` (double space). Verify the correct one is used by the application before committing only that one.

---

## Common Pitfalls

### Pitfall 1: api_url Not Set — WebSocket Connects to localhost
**What goes wrong:** Browser opens the Railway HTTPS URL, gets the frontend, then the frontend tries to open a WebSocket to `localhost:8000`. This fails silently — the UI loads but all state events fail.
**Why it happens:** Reflex embeds the `api_url` into the compiled frontend at build time. If not set, it defaults to `localhost`.
**How to avoid:** Set `API_URL` environment variable in Railway before deploying, OR hardcode in rxconfig.py after Railway assigns the URL. The env var approach is cleaner.
**Warning signs:** App loads visually but doesn't respond to interactions; browser console shows WebSocket `ERR_CONNECTION_REFUSED`.

### Pitfall 2: Health Check Fails on Railway
**What goes wrong:** Railway marks the deploy as unhealthy and rolls back.
**Why it happens:** Railway's default health check hits `/` on the assigned port. Caddy may not be ready fast enough, or Reflex backend takes >30s to start.
**How to avoid:** Set `healthcheckPath = "/ping"` and `healthcheckTimeout = 180` in railway.toml (Reflex's `/ping` endpoint returns 200 once backend is ready).
**Warning signs:** Deployment shows "Health check failed" in Railway logs.

### Pitfall 3: Frontend Build Fails Due to Missing Node.js
**What goes wrong:** `reflex export --frontend-only` fails inside the Dockerfile during build.
**Why it happens:** The Python base image doesn't include Node.js; Reflex requires it to build the Next.js frontend.
**How to avoid:** Install Node.js 20.x in the Dockerfile before running `reflex export`.
**Warning signs:** Docker build fails with `node: not found` or npm errors.

### Pitfall 4: gitignore Exceptions Don't Work for Files with Spaces or Quotes
**What goes wrong:** `git add data/prices/Хаан банк.json` works, but `!data/prices/Хаан банк.json` in `.gitignore` may not un-ignore it on some systems.
**Why it happens:** Spaces in filenames are valid in gitignore patterns but some tooling has edge cases. Embedded double-quotes (`"`) in filenames are unusual and may need escaping.
**How to avoid:** After updating `.gitignore`, run `git status` to verify the target files appear as untracked (not ignored). Use `git check-ignore -v data/prices/file.json` to debug.
**Warning signs:** After adding `!` exceptions, `git status` still doesn't show the file as untracked.

### Pitfall 5: scipy Not in requirements.txt
**What goes wrong:** Railway build installs requirements.txt, then the app imports `from scipy.optimize import minimize` and crashes at startup.
**Why it happens:** scipy was added to the venv locally but never added to requirements.txt.
**How to avoid:** Add `scipy>=1.11.0` to requirements.txt BEFORE creating the Dockerfile or railway.toml. This is decision D-04.
**Warning signs:** Railway deploy log shows `ModuleNotFoundError: No module named 'scipy'`.

### Pitfall 6: Jupyter/matplotlib in requirements.txt Causes Build Timeout
**What goes wrong:** Railway build times out or produces a very large image.
**Why it happens:** `jupyter>=1.0.0` pulls in ~200MB of dependencies; `matplotlib` and `seaborn` add another ~100MB. These are not used by the Reflex app in production.
**How to avoid:** Remove dev-only dependencies from requirements.txt before deploying. Keep only what the app imports at runtime.
**Warning signs:** Build takes >10 minutes; image exceeds 1GB.

### Pitfall 7: Caddy Formatting Warning Causes WebSocket Disconnects
**What goes wrong:** App works for ~15 minutes then WebSocket disconnects.
**Why it happens:** If Caddyfile is passed as a separate file rather than embedded in the Dockerfile, Caddy prints a "not formatted" warning at startup. In some versions this causes intermittent behavior.
**How to avoid:** Embed the Caddyfile content directly in the Dockerfile using `RUN printf '...' > /Caddyfile`. This way Caddy starts with pre-formatted config.
**Warning signs:** Caddy startup log contains "Caddyfile input is not formatted".

---

## Code Examples

### railway.toml (minimal, using Dockerfile)
```toml
# Source: Railway Config as Code docs + Reflex Railway Help Station
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = ""
healthcheckPath = "/ping"
healthcheckTimeout = 180
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### rxconfig.py with api_url from env var
```python
# Source: Reflex self-hosting docs + REFLEX_ prefix convention (>=0.7.13)
import os
import reflex as rx

config = rx.Config(
    app_name="financial_dashboard",
    api_url=os.environ.get("API_URL", "http://localhost:8000"),
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)
```

### Verifying gitignore exceptions work
```bash
# After editing .gitignore:
git check-ignore -v "data/АПУ_2025.json"        # should print nothing if unignored
git check-ignore -v "data/prices/Хаан банк.json" # should print nothing if unignored
git status                                         # file should appear as untracked
```

### Inline comment style guide (per D-14)
Comments should explain **why** — formula source, threshold meaning, or constraint:
```python
# Good: explains why this threshold matters
# M-Score > -1.78 indicates possible manipulation (Beneish 1999, misstatement threshold)
if m_score > -1.78:

# Bad: just restates the code
# Check if m_score is greater than -1.78
if m_score > -1.78:
```

---

## Inline Comment Targets — Code Audit

Research identified the specific lines in each file that need explanatory comments per D-13/D-14.

### portfolio_optimization.py — Key comment targets

| Line range | What needs a comment | Why |
|------------|---------------------|-----|
| ~77–79 | `log_returns = np.log(closes[1:] / closes[:-1])` | Why log returns instead of simple returns (log-normality assumption, additivity across time) |
| ~170–173 | `ann_return = mean_return * 252` and `ann_downside_std = downside_std * math.sqrt(252)` | Annualization convention: 252 trading days; sqrt rule for volatility scaling |
| ~186–191 | CVaR calculation | CVaR = Expected Shortfall = mean of returns below 5th percentile (tail loss measure more robust than VaR) |
| ~221–233 | `neg_sharpe` function and SLSQP call | Maximize Sharpe = minimize negative Sharpe; SLSQP is gradient-based constrained optimizer; weights sum to 1, bounds [0,1] enforce long-only |
| ~283–300 | `sample_frontier` | Random Dirichlet-style sampling (raw/sum normalization) to approximate efficient frontier — Monte Carlo, not a true Markowitz sweep |
| ~279 | `seed=42` | Fixed seed ensures frontier scatter is deterministic across page loads |

### ratios.py — Key comment targets

| Function | Lines | What needs a comment |
|----------|-------|---------------------|
| `compute_piotroski` | F4 (~334) | Accruals: OCF/TA > ROA tests whether cash earnings exceed accrual earnings — a quality signal (Sloan 1996) |
| `compute_piotroski` | F7 (~346) | Always None — MSE Excel files do not contain shares outstanding; documented limitation |
| `compute_beneish` | DSRI (~460) | Days Sales Receivables Index — rising AR relative to revenue suggests premature revenue recognition |
| `compute_beneish` | GMI (~466–468) | Gross Margin Index — declining margin creates incentive to manipulate |
| `compute_beneish` | AQI (~474–486) | Asset Quality Index — growth in non-current, non-PPE assets (off-balance-sheet risk proxy) |
| `compute_beneish` | DEPI (~495–497) | Always None — MSE filings do not disclose depreciation separately |
| `compute_beneish` | M-Score coefficients (~536–545) | Source: Beneish (1999) probit regression; intercept -4.84; each coefficient is the log-odds contribution |
| `compute_beneish` | threshold -1.78 (~556–557) | -1.78 is Beneish's original misstatement cutoff; -2.22 is the more conservative "likely clean" threshold |
| `compute_composite_score` | `_interp` function (~598–605) | Linear interpolation maps raw ratio values to 0–100 subscores; ranges are calibrated to typical MSE company values |
| `compute_composite_score` | weights dict (~671–678) | Weights: profitability 25%, liquidity 20%, solvency 20%, activity 15%, Altman 10%, Piotroski 10% — total 100%; Beneish penalty applied post-aggregation |
| `compute_composite_score` | re-normalise (~693–695) | Available-data normalization: if a component has no data, its weight is redistributed proportionally to present components |
| `compute_composite_score` | Beneish penalty (~698–699) | −10 penalty applied only when M-Score is both reliable (≥5 indices) and above -1.78 manipulation threshold |

### header_mappings.py — Key comment targets

| Location | What needs a comment |
|----------|---------------------|
| Module docstring / `match_header` | Why 7 separate dictionaries instead of one: each statement type (balance sheet, income statement, cash flow, bank BS, bank IS, insurance BS, insurance IS) has entirely different Mongolian terminology; merging them would cause false matches |
| `normalize_header` | Explanation of why normalization is needed: MSE files have inconsistent spacing, capitalization, and trailing whitespace in cell values |
| `match_header` — sort by length descending | Why longer patterns checked first: "урт хугацаат зээл" (long-term loans) must match before "зээл" (generic loans) to avoid false positives |
| `BALANCE_SHEET_HEADERS` — duplicate cash keys | Three near-identical keys for cash_and_equivalents: comma-space variants and "ба" variant — real MSE files use all three spellings inconsistently |
| `SHEET_TYPE_PATTERNS` | Why abbreviations "сбд", "одт", "мгт": MSE uses these Mongolian acronyms as shorthand sheet names in some company files |

---

## README Structure Map

Per D-10, the planner should implement exactly this section order:

1. **Header + tagline** — "MSE Analytica — Fundamental analysis platform for the Mongolian Stock Exchange"
2. **Live demo URL** — placeholder until Railway assigns URL; add after first deploy
3. **What it does (2–3 sentences)** — upload MSE Excel → instant fundamental analysis
4. **Features** — bulleted list (26 ratios, Piotroski, Beneish, Altman, composite score, portfolio optimization, efficient frontier, price charts, valuation metrics)
5. **Methodology** — per D-09: Piotroski (9 criteria, F7 N/A), Beneish (8 indices, threshold, DEPI N/A), Altman Z (3 zones), Composite Score (weight table), Mean-Variance (SLSQP + frontier sampling)
6. **Tech stack** — Reflex 0.8.26, Python 3.12, scipy, numpy, pandas, openpyxl, xlrd, requests, BeautifulSoup4, Tailwind v4
7. **Data sources** — mse.mn (financial statements), old.mse.mn (historical prices), with links
8. **Local setup** — step-by-step: clone, venv, pip install, reflex run
9. **Known issues/limitations** — per D-12: F7 N/A, DEPI N/A, P/E requires manual shares input; also note EBITDA uses EBIT as proxy (no depreciation line in MSE data)
10. **Future improvements** — sector routing (Phase 2 pending), full company detail tabs, screener filters, PDF export
11. **Author** — name, institution, capstone context

**Existing README.md status:** File exists at repo root (v1.0). It has useful content (scoring models, data format, companies table) but is missing: live demo URL, methodology detail, data sources links, portfolio optimization section, valuation metrics. The rewrite preserves the factual content and expands it significantly.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | App runtime | Yes (global) | 3.12.5 | — |
| reflex | App framework | Yes (in venv) | 0.8.26 | — |
| scipy | Portfolio optimizer | Yes (in venv, NOT in requirements.txt) | 1.17.0 in venv | None — must add to requirements.txt |
| numpy | Math operations | Yes (transitive) | 2.3.4 | — |
| Docker | Dockerfile build for Railway | Not checked — Railway builds in cloud | — | Railway builds image remotely; local Docker not required for deployment |
| Railway CLI | Railway deploy | Not checked | — | Can deploy via Railway dashboard + GitHub integration (no CLI needed) |
| Node.js | Reflex frontend build (inside Docker) | Yes (local venv has it via reflex) | 20.x (managed by reflex) | Must be installed in Dockerfile explicitly |

**Missing dependencies with no fallback:**
- `scipy` in requirements.txt — must be added before Railway build

**Missing dependencies with fallback:**
- Local Docker — not required; Railway builds the Dockerfile remotely via GitHub push or `railway up`

---

## Validation Architecture

> `workflow.nyquist_validation` is not explicitly set to false in `.planning/config.json` (key is absent). Section is included.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (if installed in venv) — check with `python -m pytest --version` |
| Config file | None detected — no pytest.ini or pyproject.toml test config |
| Quick run | `python -m pytest tests/ -x -q 2>/dev/null` |
| Full suite | `python -m pytest tests/ -v 2>/dev/null` |

Note: A `tests/` directory exists in the project root. Its contents were not audited but it exists. Phase 5 tasks are primarily deployment and docs — not new logic — so test coverage requirements are lighter.

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEPLOY-01 | App accessible at Railway URL | smoke (manual) | `curl -s https://<railway-url>/ping` | ❌ run after deploy |
| DEPLOY-02 | Demo data loads on first visit | smoke (manual) | `curl -s https://<railway-url>/` returns 200 | ❌ run after deploy |
| DOCS-01 | README contains required sections | manual review | — | N/A |
| DOCS-02 | Inline comments present in target files | manual review | — | N/A |
| DOCS-03 | No secrets in committed files | automated | `git log --all -p \| grep -E "API_KEY\|PASSWORD\|SECRET"` | ✅ run before push |

### Sampling Rate
- **Per task commit:** `git check-ignore -v data/АПУ_2025.json` (gitignore verification)
- **Per wave merge:** `python -m pytest tests/ -x -q` (if tests exist)
- **Phase gate:** Successful Railway deployment + `/ping` returns 200 before marking DEPLOY-01 complete

### Wave 0 Gaps
- No new test files needed — Phase 5 adds no new logic
- Secrets audit command is a one-liner, not a test file
- Post-deploy smoke tests are manual (no automated e2e test infra)

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `API_URL` env var | `REFLEX_API_URL` env var | Reflex 0.7.13 | Old env var name no longer works |
| Nixpacks auto-detect for Reflex | Dockerfile recommended | ~2024 | Nixpacks works but has edge cases; Dockerfile is more predictable |
| `reflex run` (dev) | `reflex run --env prod` (prod) | Always | Dev mode has hot-reload overhead unsuitable for production |
| Separate Caddyfile | Embedded Caddyfile in Dockerfile | Community fix 2024 | Prevents 15-min WebSocket disconnect |

---

## Open Questions

1. **Exact Railway-assigned HTTPS URL**
   - What we know: Railway assigns a URL like `https://financial-dashboard-production.up.railway.app` after first deploy
   - What's unclear: The exact URL is not known until after first deploy
   - Recommendation: Use env var `API_URL` in rxconfig.py; set its value in Railway dashboard after first deploy, then redeploy

2. **Премиум financial JSON filename with embedded quotes**
   - What we know: File on disk is `"_Премиум_Нэксус_"_ХК_2025.json` with literal double-quote characters; D-06 in CONTEXT.md omits the quotes
   - What's unclear: Whether the gitignore `!` exception will work correctly with embedded quotes on all systems
   - Recommendation: Planner should add a verification step: after updating .gitignore, run `git check-ignore -v` to confirm the file is no longer ignored; if the pattern fails, consider renaming the file to remove the quotes (which would also require updating index.json and any code that references it)

3. **Whether to remove jupyter/matplotlib from requirements.txt**
   - What we know: These are not imported by the Reflex app; they are dev/notebook dependencies
   - What's unclear: Whether removing them would break anything in the codebase (e.g., scripts/ or tests/)
   - Recommendation: Scan `scripts/` and `tests/` for imports before removing; if only used in notebooks, move to a separate `requirements-dev.txt` and keep main `requirements.txt` production-only

4. **Double-space vs single-space Премиум price file**
   - What we know: Two files exist — `Премиум Нэксус  ХК.json` (double space) and `Премиум Нэксус ХК.json` (single space); D-06 specifies the double-space version
   - What's unclear: Which file the application actually loads (depends on name normalization in the scraper/loader)
   - Recommendation: Check `json_store.py` or state.py to see which filename pattern is used when loading price data for this company; commit only the correct one

---

## Sources

### Primary (HIGH confidence)
- Reflex official self-hosting docs: https://reflex.dev/docs/hosting/self-hosting/ — api_url config, production run command, port architecture
- Railway Config as Code docs: https://docs.railway.com/reference/config-as-code — railway.toml format, startCommand, healthcheckPath
- Reflex GitHub issue #4236: https://github.com/reflex-dev/reflex/issues/4236 — single-port Dockerfile + Caddyfile pattern, 15-min disconnect fix

### Secondary (MEDIUM confidence)
- Railway Help Station — Reflex deployment thread: https://station.railway.com/questions/python-reflex-deployment-df87ca6e — health check config, Dockerfile approach recommendation
- GeniePy production guide: https://geniepy.com/blog/how-to-run-reflex-apps-in-production/ — port 3000/8000 architecture, backend-only flag
- Reflex CLI docs: https://reflex.dev/docs/api-reference/cli/ — `--env prod`, `--backend-only`, `--frontend-only` flags

### Tertiary (LOW confidence)
- supmo668/reflex-railway-deploy GitHub template — configuration structure; content not fully verified
- WebSearch aggregated findings on REFLEX_ env var prefix change in 0.7.13 — single source, not verified against changelog

---

## Metadata

**Confidence breakdown:**
- Railway deployment config: MEDIUM — multiple community sources align; exact Dockerfile content needs local testing after first deploy
- gitignore exceptions: HIGH — standard git behavior, well-documented; Премиум filename anomaly is a LOW-confidence risk item
- requirements.txt fix (scipy): HIGH — confirmed missing from file, confirmed present in venv at 1.17.0
- Inline comment targets: HIGH — sourced directly from reading the actual source files
- README structure: HIGH — derived from locked decisions D-08 through D-12 and existing README content

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (Railway/Reflex deployment patterns are stable; Reflex 0.8.x API unlikely to change in 30 days)

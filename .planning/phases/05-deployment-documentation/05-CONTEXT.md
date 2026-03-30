# Phase 5: Deployment & Documentation - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Deploy MSE Analytica to Railway with demo data pre-loaded, and ship comprehensive documentation — a README that serves both capstone evaluators and GitHub visitors, plus inline comments for non-obvious logic.

**In scope:** DEPLOY-01, DEPLOY-02, DOCS-01, DOCS-02, DOCS-03
- Railway deployment with stable public HTTPS URL
- Demo data (7 companies: financial JSONs + price JSONs) bundled into the repo
- README: professional + portfolio-quality with detailed methodology section
- Inline comments for scraper parsing, optimization math, Beneish formula, composite score weights
- Secrets audit: confirm no API keys committed, `.env` confirmed in `.gitignore`

**Not in scope:** Screenshots (deferred), Render deployment, any new features

</domain>

<decisions>
## Implementation Decisions

### Deployment Platform
- **D-01:** Deploy to **Railway** (not Render). Railway's Nixpacks auto-detects Python; better Reflex community reports; simpler configuration via `railway.toml`.
- **D-02:** No environment variables needed in the deployed app — the app uses flat JSON files only. Strip `ALPHA_VANTAGE_API_KEY` and `DATABASE_URL` from any deployment config (these are leftover dev artifacts in `.env`, not used by the app).
- **D-03:** Deployment config: `railway.toml` at project root. Start command: `reflex run --env prod` (or equivalent for production mode). Build command handles `pip install -r requirements.txt`.
- **D-04:** `requirements.txt` must be audited before deploy — `scipy` is missing (needed by Phase 4 optimizer). Add it before creating the Railway config.

### Demo Data Bundling
- **D-05:** Un-gitignore the 7 demo companies' files by adding explicit `!` exceptions to `.gitignore`. Ship **both** financial JSONs and price JSONs so the app works fully on first visit (valuation metrics + portfolio optimization fully functional).
- **D-06:** Files to un-gitignore:
  - Financial JSONs (data/): `АПУ_2025.json`, `Хаан_банк_2025.json`, `Мандал_даатгал_2025.json`, `Сүү_2025.json`, `Моносхүнс_2025.json`, `Дархан_нэхий_ХК_2025.json`, `_Премиум_Нэксус_ХК_2025.json`, `index.json`
  - Price JSONs (data/prices/): `АПУ.json`, `Хаан банк.json`, `Мандал даатгал.json`, `Сүү.json`, `Моносхүнс.json`, `Дархан нэхий ХК.json`, `Премиум Нэксус  ХК.json`
  - `data/company_registry.json` is already un-gitignored — keep as-is.
- **D-07:** All other `data/*.json` and `data/prices/*.json` (the 155 non-demo companies) remain gitignored. The `.gitignore` pattern `data/*.json` stays; individual demo files get `!data/filename.json` exceptions below it.

### README
- **D-08:** Tone: **both capstone evaluator and GitHub portfolio**. Professional structure that evaluators can check against rubric, but with good visual hierarchy and clear value proposition for GitHub visitors.
- **D-09:** Include a **detailed methodology section** covering:
  - Piotroski F-Score (9 criteria listed, note F7 always N/A for MSE data)
  - Beneish M-Score (8 indices listed, threshold −1.78, note DEPI always N/A)
  - Altman Z-Score (zones: Safe > 2.99, Grey 1.23–2.99, Distress < 1.23)
  - Composite Health Score formula (weights: profitability 25%, liquidity 20%, solvency 20%, activity 15%, Altman 10%, Piotroski 10%; −10 Beneish penalty)
  - Mean-variance optimization (max-Sharpe SLSQP, efficient frontier sampling)
- **D-10:** README sections (in order): project description + live demo URL → features → methodology → tech stack → data sources (with links to mse.mn and old.mse.mn) → local setup (step-by-step) → known issues/limitations → future improvements → author
- **D-11:** No screenshots for this phase — deferred for later.
- **D-12:** Known issues to document: Piotroski F7 always N/A (no shares outstanding in MSE Excel files), Beneish DEPI always N/A (no depreciation line item), P/E and P/BV require manual shares-outstanding input to unlock.

### Inline Comments (DOCS-02)
- **D-13:** Add inline comments explaining intent (not just what the code does) to:
  - `financial_dashboard/analysis/portfolio_optimization.py` — SLSQP objective function, CVaR formula, frontier sampling approach
  - `financial_dashboard/parser/excel_parser.py` — Mongolian header mapping logic, why 7 dictionaries
  - `financial_dashboard/analysis/ratios.py` — Beneish M-Score formula (each of the 8 indices), Altman Z-Score coefficients, composite score weights
- **D-14:** Comments should explain **why** (formula source, threshold meaning, known limitation) not just what. Target: someone reading the code for the first time should understand each formula without looking it up.

### Secrets / Security (DOCS-03)
- **D-15:** `.env` is already in `.gitignore` — confirmed correct.
- **D-16:** Audit all Python files for hardcoded credentials before the deploy commit. No secrets should be present in any committed file.
- **D-17:** Railway deployment requires zero secrets configured — no env vars panel needed.

### Claude's Discretion
- Exact `railway.toml` and `nixpacks.toml` configuration details — research Reflex 0.8.26 Railway deploy requirements and use best current approach.
- Order and exact wording of README sections — follow D-10 structure but adapt prose as needed.
- Which specific code lines need comments vs which are self-explanatory — follow D-13 file list but use judgment on which formulas need explanation.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — DEPLOY-01, DEPLOY-02, DOCS-01, DOCS-02, DOCS-03 acceptance criteria
- `.planning/PROJECT.md` — Vision, constraints, tech stack, known limitations (F7 N/A, DEPI N/A, no shares outstanding)

### Existing Codebase
- `financial_dashboard/analysis/portfolio_optimization.py` — Phase 4 optimizer; needs scipy, inline comments per D-13
- `financial_dashboard/analysis/ratios.py` — Beneish, Altman, composite score; inline comments per D-13
- `financial_dashboard/parser/excel_parser.py` — Mongolian header mapping; inline comments per D-13
- `requirements.txt` — Missing scipy; must be fixed before deploy
- `.gitignore` — Currently gitignores `data/*.json` (except `company_registry.json`); must add demo file exceptions per D-06
- `rxconfig.py` — Reflex app config; relevant to Railway start command
- `README.md` — Existing v1.0 README; will be fully rewritten per D-08 through D-12

### Data Files to Un-gitignore
- `data/index.json` — Company manifest (already has 7 entries)
- `data/АПУ_2025.json`, `data/Хаан_банк_2025.json`, `data/Мандал_даатгал_2025.json`, `data/Сүү_2025.json`, `data/Моносхүнс_2025.json`, `data/Дархан_нэхий_ХК_2025.json`, `data/_Премиум_Нэксус_ХК_2025.json`
- `data/prices/АПУ.json`, `data/prices/Хаан банк.json`, `data/prices/Мандал даатгал.json`, `data/prices/Сүү.json`, `data/prices/Моносхүнс.json`, `data/prices/Дархан нэхий ХК.json`, `data/prices/Премиум Нэксус  ХК.json`

</canonical_refs>

<deferred>
## Deferred Ideas

- **Screenshots** — User deferred for now. When ready: Screener, Upload flow, Portfolio page (Analysis tab), Company detail page. Place in `assets/screenshots/`.
</deferred>

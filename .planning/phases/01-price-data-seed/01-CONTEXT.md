# Phase 1: Price Data Seed - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a one-time price data seed: scrape historical OHLCV price data from old.mse.mn for all 162 MSE-listed companies and store as flat JSON files. A pre-built company registry maps all companies to their MSE IDs. A "Refresh Prices" button on the upload page re-scrapes companies whose financial data is already in the system. This phase lays the data foundation for Phase 3 (valuation charts) and Phase 4 (portfolio optimization covariance matrix).

</domain>

<decisions>
## Implementation Decisions

### Scope
- **D-01:** Seed run scrapes ALL 162 MSE-listed companies (Classification I, II, III) — not just the 7 demo companies. Full market price history is available for any future upload.

### Company Registry
- **D-02:** Use a pre-built `data/company_registry.json` file (manually curated, not scraped from companies_info pages). This avoids a dependency on companies_info page structure.
- **D-03:** Registry entries include 4 fields: `name` (Mongolian company name), `mse_id` (integer), `ticker` (English shortcode), `tier` (classification: "I", "II", or "III").
- **D-04:** Known IDs from Excel filenames: АПУ=90, Дархан нэхий ХК=71, Сүү=135, Мандал даатгал=547, Моносхүнс=551, Премиум Нэксус ХК=557, Хаан банк=563. Remaining ~155 IDs must be researched/discovered and added to the registry.

### Price File Naming
- **D-05:** Price files are keyed by Mongolian company name — `data/prices/АПУ.json` — consistent with the existing `data/` convention (`АПУ_2025.json`). No encoding translation required at lookup time.

### UI Refresh Trigger
- **D-06:** A "Refresh Prices" button lives on the upload/home page (not the company detail page). It re-scrapes only companies already present in `index.json` (uploaded companies), not all 162. This keeps the UI refresh fast and practical.
- **D-07:** The button shows a loading state during scraping and displays success/error feedback per company when complete.

### Scraper Behavior
- **D-08:** Uses `requests` + `BeautifulSoup4` (already decided at project level). Add both to `requirements.txt`.
- **D-09:** Per-company errors are logged and skipped — the full run does not crash on a single failure.
- **D-10:** Already-scraped files are not re-scraped on retry (idempotent seed run). Check for file existence before scraping.
- **D-11:** Source URL: `old.mse.mn/en/company/{mse_id}` — server-rendered HTML, OHLCV + Date columns.

### Claude's Discretion
- Rate limiting / politeness delay between requests (sleep interval, user-agent header) — Claude decides
- JSON structure inside each price file (array of records vs date-indexed dict) — Claude decides, but must be consistent with what Phase 3 expects (time-series list preferred)
- Progress logging format during seed run (stdout, log file, or both)
- Whether to paginate or scrape all pages in one pass

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project
- `.planning/PROJECT.md` — Vision, constraints, tech stack, key decisions (scraper library, storage format, Reflex gotchas)
- `.planning/REQUIREMENTS.md` — SCRP-01 through SCRP-04 acceptance criteria

### Existing Codebase
- `financial_dashboard/storage/json_store.py` — Storage patterns: DATA_DIR path resolution, index.json structure, naming conventions (Mongolian company name + year)
- `data/index.json` — Current 7-company index; price lookup key must match the `company` field here
- `financial_dashboard/state.py` — UploadState patterns; Reflex state var typing rules apply to any new PriceState

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `financial_dashboard/storage/json_store.py`: `DATA_DIR`, `load_index()`, `save_parsed_data()` pattern — price scraper should follow the same DATA_DIR root and use a `prices/` subdirectory
- `data/index.json`: The `company` field (Mongolian name) is the canonical company identifier; price file lookup key must match this field exactly

### Established Patterns
- Storage: flat JSON files under `data/`, path resolved via `Path(__file__).parent.parent.parent / "data"`
- State vars: typed `list[dict[str, str]]` — no raw dicts; any new Reflex state for price loading must follow this
- Tailwind v4 via `class_name` strings; `rx.cond()` for conditional rendering in UI

### Integration Points
- Upload page (`financial_dashboard/pages/`) — "Refresh Prices" button adds to this existing page
- `index.json` — scraper reads this to determine which companies to refresh in UI mode
- `data/prices/` — new subdirectory; must be created by the scraper if absent

</code_context>

<specifics>
## Specific Ideas

- MSE company IDs already embedded in uploaded Excel filenames: `_90 20252report.xls` → APU=90. The 7 known IDs can bootstrap the registry.
- "Refresh Prices" on upload page only re-scrapes companies in `index.json` — dynamic, not hardcoded to 7.

</specifics>

<deferred>
## Deferred Ideas

- Scraping `companies_info/1,/2,/3` to auto-discover IDs — user chose pre-built registry instead
- Per-company refresh button on the company detail page — user chose upload page global button instead

</deferred>

---

*Phase: 01-price-data-seed*
*Context gathered: 2026-03-24*

# GSD State

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements → creating roadmap
Last activity: 2026-03-24 — Milestone v1.1 started

## Milestone

**v1.1: Complete MSE Analytica**
Goal: Full 6-step fundamental analysis workflow — scraped price data, valuation, sector-aware ratios, portfolio optimization, deployed.

## Accumulated Context

### From MVP (v1.0 — shipped)
- 7 companies parsed and working in demo mode
- Bank ratio engine (bank_ratios.py) and insurance ratio engine (insurance_ratios.py) are BUILT but never imported/called
- state.py uses `compute_ratios()` for ALL companies including Khan Bank and Мандал даатгал — wrong
- Company page shows only 9 of 26 computed ratios
- No charts of any kind implemented
- No sector field in index.json
- screener_filter state var exists but no UI dropdown
- data/*.json is gitignored; .gitkeep preserves folder
- Tailwind v4 via TailwindV4Plugin — class_name strings only, no rx.color() calls
- Reflex UntypedVarError risk: state vars must be typed (str/int/bool/list[dict]) not raw dicts

### Known Reflex Gotchas
- State vars cannot be raw dicts — must be list[dict[str,str]] or flat typed vars
- rx.cond() required for conditional rendering (no Python if/else in components)
- rx.foreach() required for list iteration in components
- Charts: Reflex has rx.recharts (Recharts wrapper) — use for all charts
- Event handlers must be async or sync — no mixing

### Price Scraper Context
- URL: https://old.mse.mn/en/company/{id}
- APU confirmed ID: 90
- Page is server-rendered HTML (requests + BeautifulSoup4 sufficient, no Selenium needed)
- Data columns: №, High, Low, Open, Close, Traded (Volume), Value (Turnover MNT), Date
- ~1,400 records per company, all in one scrollable table (no pagination)
- Other company IDs need to be discovered (try sequential IDs or company list page)

## Blockers

None — waiting on roadmap creation.

## Pending Todos

None yet — will be generated from roadmap.

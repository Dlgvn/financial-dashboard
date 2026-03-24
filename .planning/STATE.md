# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-24)

**Core value:** Upload an MSE Excel file and get a complete fundamental analysis — ratios, forensic scores, valuation, and portfolio optimization — in one place, in one click.
**Current focus:** Phase 1 — Price Scraper

## Current Position

Phase: 1 of 5 (Price Scraper)
Plan: 0 of ? in current phase
Status: Ready to plan
Last activity: 2026-03-24 — Roadmap created, Phase 1 ready to plan

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Price Scraper | - | - | - |
| 2. Sector Routing, Company Detail & Screener | - | - | - |
| 3. Valuation Metrics | - | - | - |
| 4. Portfolio Optimization | - | - | - |
| 5. Deployment & Documentation | - | - | - |

*Updated after each plan completion*

## Accumulated Context

### Decisions

- Scraper: requests + BeautifulSoup4 (server-rendered HTML, no JS rendering needed)
- Price storage: data/prices/{company}.json alongside financial data JSONs
- Sector detection: Add `sector` field to index.json manually for 7 demo companies
- Valuation: Show EV/EBITDA + FCF yield always; P/E + P/BV only if shares outstanding provided
- Portfolio optimization: Simple mean-variance (not Black-Litterman views UI) for v1.1

### Known Reflex Gotchas

- State vars cannot be raw dicts — must be list[dict[str,str]] or flat typed vars
- rx.cond() required for conditional rendering (no Python if/else in components)
- rx.foreach() required for list iteration in components
- Charts: use rx.recharts (Recharts wrapper) — no other chart lib
- Tailwind v4 via TailwindV4Plugin — class_name strings only, no rx.color() calls

### Pending Todos

None yet.

### Blockers/Concerns

- APU=90 confirmed; remaining 6 company MSE IDs must be discovered during Phase 1 scraping
- Shares outstanding not in MSE Excel files — optional manual input unlocks P/E and P/BV (by design)
- bank_ratios.py and insurance_ratios.py are BUILT but never imported/called in state.py — wired in Phase 2

## Session Continuity

Last session: 2026-03-24
Stopped at: Roadmap and STATE.md initialized; no plans created yet
Resume file: None

# Milestones

## v1.0 — MVP (Shipped 2026-03-24)

**Goal:** Working end-to-end MVP for MSE Analytica.

**What shipped:**
- Upload .xls/.xlsx MSE Excel files via drag-drop
- Auto-parse Mongolian-language financial statements (7 header dictionaries)
- 26 financial ratios across 6 categories (standard companies)
- Piotroski F-Score, Beneish M-Score, Altman Z-Score, Composite Health Score
- Company screener page with health badges
- Company detail page (9 ratios shown)
- Portfolio: add/remove, equal weighting, blended health score
- Demo mode: 7 MSE companies pre-loaded
- Dark OLED theme (Tailwind v4, bg-slate-950)
- Bank ratio engine built (19 ratios) — not wired
- Insurance ratio engine built (15+ ratios) — not wired

**Known gaps carried forward to v1.1:**
- Bank/insurance engines not called in state.py
- Only 9 of 26 ratios shown on company page
- No charts implemented
- No sector field in index.json
- No deployment

---

## v1.1 — Complete MSE Analytica (In Progress)

Started: 2026-03-24
Target: Rubric-excellent (95–100%), fully deployed

See `.planning/PROJECT.md` for full scope.

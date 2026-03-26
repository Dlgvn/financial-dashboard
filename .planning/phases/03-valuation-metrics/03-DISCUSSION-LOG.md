# Phase 3: Valuation Metrics - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26

---

## Area: Formula Scope

**Q: EV/EBITDA needs market cap — how to handle without shares?**
- Options: EV/EBITDA requires shares too | Partial EV (debt-only) | Skip EV/EBITDA
- Selected: **EV/EBITDA requires shares too**

**Q: FCF yield without shares — which proxy?**
- User response: "total share is displayed in MSE website we maybe handle this"
- Key insight: shares outstanding is on the MSE website — scraping is feasible

**Q: Scrape shares outstanding automatically?**
- Options: Scrape from MSE | Keep manual input | Both with fallback
- Selected: **Scrape from MSE (extend existing price scraper)**

**Q: FCF yield formula with scraped shares + last close price?**
- Options: FCF / Market Cap | FCF / Revenue
- Selected: **FCF / Market Cap** (standard definition)

---

## Area: Price Chart Controls

**Q: Default time range?**
- Options: All history | 1 year default + range toggle
- Selected: **1 year default + range toggle**

**Q: Range toggle buttons?**
- Options: 1M / 6M / 1Y / All | 6M / 1Y / 3Y / All
- Selected: **1M / 6M / 1Y / All**

**Q: Additional overlays?**
- Options: Close line only | Close line + volume bars | Close line + 50-day MA
- Selected: **Close line + volume bars**

---

## Area: Shares Outstanding Input UX

**Q: If shares couldn't be scraped, manual fallback?**
- Options: Yes — editable input field | No — show message with MSE link
- Selected: **Yes — show editable input field**

**Q: Where on the Valuation tab?**
- Options: Top of tab above ratios | Below ratios above chart | Edit icon next to each ratio
- Selected: **Edit icon next to each ratio** (✎ icon on each card when shares unavailable)

---

## Area: Metrics Layout

**Q: How are the 4 ratio cards arranged?**
- Options: 2×2 grid above chart | 4-card horizontal row above chart | Chart top metrics below
- Selected: **4-card horizontal row above chart** (EV/EBITDA | FCF Yield | P/E | P/BV)

**Q: When shares outstanding missing, what do cards show?**
- Options: N/A with edit icon | Locked cards with padlock | Hide entirely
- Selected: **N/A with edit icon** (✎ pencil reveals inline input)

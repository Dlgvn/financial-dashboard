# Phase 1: Price Data Seed - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-24
**Phase:** 1 — Price Data Seed

---

## Area: Scope

**Q: Should Phase 1 scrape all 162 MSE-listed companies or just the 7 demo companies?**

Options presented:
- All 162 companies ← **Selected**
- 7 demo companies only
- 7 now + scaffold for 162

*Rationale: Full seed means price data is waiting for any company a user later uploads. Phase 4 portfolio optimization benefits from full market history. Aligns with ROADMAP goal.*

---

## Area: Company ID Discovery

**Q: How should the scraper discover MSE company IDs for all 162 companies?**

Options presented:
- Scrape companies_info pages
- Pre-built registry file ← **Selected**

*Rationale: Pre-built registry avoids dependency on companies_info page structure. 7 IDs already known from Excel filenames.*

**Q: What fields should company_registry.json include per entry?**

Options presented:
- Minimal: name + MSE ID
- Full: name + MSE ID + ticker + classification tier ← **Selected**

*Rationale: Matches ROADMAP success criterion exactly; ticker enables clean English-keyed lookups if needed in future phases.*

---

## Area: Price File Naming

**Q: What key should price files use as their filename?**

Options presented:
- Mongolian company name ← **Selected**
- English ticker from registry
- MSE numeric ID

*Rationale: Consistent with existing data/ pattern (АПУ_2025.json). State.py already identifies companies by Mongolian name. No translation needed at lookup time.*

---

## Area: UI Refresh Trigger

**Q: Where should the 'Refresh Prices' UI trigger live?**

Options presented:
- Company detail page only
- Upload page only (global) ← **Selected**
- Both

*Rationale: Matches ROADMAP UI hint. Cleaner UX — one place to refresh all prices.*

**Q: Should 'Refresh All' re-scrape all 162 companies or only specific companies?**

Options presented:
- 7 demo companies only
- All 162 companies
- Companies with uploaded financial statements ← **Selected** (user-specified)

*User note: "Companies only that uploaded financial statements" — dynamic, reads from index.json. Not hardcoded to 7, not 162 via UI.*

---

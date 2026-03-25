---
phase: 2
slug: sector-routing-company-detail-screener
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | none — tests/ directory auto-discovered |
| **Quick run command** | `python -m pytest tests/test_sector_routing.py -x` |
| **Full suite command** | `python -m pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_sector_routing.py -x`
- **After every plan wave:** Run `python -m pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 0 | SECTOR-01 | unit | `python -m pytest tests/test_sector_routing.py::test_index_json_has_sector -x` | ❌ W0 | ⬜ pending |
| 2-01-02 | 01 | 0 | SECTOR-02 | unit | `python -m pytest tests/test_sector_routing.py::test_bank_routing -x` | ❌ W0 | ⬜ pending |
| 2-01-03 | 01 | 0 | SECTOR-03 | unit | `python -m pytest tests/test_sector_routing.py::test_insurance_routing -x` | ❌ W0 | ⬜ pending |
| 2-01-04 | 01 | 1 | COMP-01 | unit | `python -m pytest tests/test_sector_routing.py::test_all_ratios_present -x` | ❌ W0 | ⬜ pending |
| 2-02-01 | 02 | 1 | COMP-03 | unit | `python -m pytest tests/test_sector_routing.py::test_dupont_identity -x` | ❌ W0 | ⬜ pending |
| 2-02-02 | 02 | 1 | COMP-04 | unit | `python -m pytest tests/test_sector_routing.py::test_red_flags_baseline -x` | ❌ W0 | ⬜ pending |
| 2-03-01 | 03 | 1 | SCREEN-01 | unit | `python -m pytest tests/test_sector_routing.py::test_screener_filter -x` | ❌ W0 | ⬜ pending |
| 2-03-02 | 03 | 1 | SCREEN-02 | unit | `python -m pytest tests/test_sector_routing.py::test_screener_sort -x` | ❌ W0 | ⬜ pending |
| 2-02-03 | 02 | 1 | COMP-02 | manual | Visual inspection — 5 tabs render without page reload | manual only | ⬜ pending |
| 2-02-04 | 02 | 1 | COMP-05 | manual | Visual inspection — semicircle gauge renders with color zones | manual only | ⬜ pending |
| 2-02-05 | 02 | 1 | COMP-06 | manual | Visual inspection — radar chart renders with 6 axes | manual only | ⬜ pending |
| 2-02-06 | 02 | 1 | COMP-07 | manual | Visual inspection — Beneish horizontal bar chart with threshold line | manual only | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_sector_routing.py` — stubs for SECTOR-01, SECTOR-02, SECTOR-03, COMP-01, COMP-03, COMP-04, SCREEN-01, SCREEN-02

*No framework install needed — pytest 9.0.2 already available.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 5-tab navigation renders, switching tabs shows correct content without page reload | COMP-02 | Reflex UI — no headless test framework available | Open Khan Bank company page, click each tab, verify content changes |
| Health gauge semicircle arc with red/amber/green zones | COMP-05 | Visual chart rendering | Open APU company page, Ratios tab, verify gauge shows score with correct color zone |
| Radar chart with 6 labeled axes | COMP-06 | Visual chart rendering | Open APU company page, verify 6 axes: Profitability, Liquidity, Solvency, Activity, Altman Z, Piotroski |
| Beneish horizontal bar chart with threshold line at ~1.0 | COMP-07 | Visual chart rendering | Open APU company page, Forensic tab, verify horizontal bars with threshold line |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

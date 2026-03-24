# Demo Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Align MSE Analytica's live demo with the MVP rubric by adding a Load Demo Data button, a Methodology & Quality accordion on the screener, and graceful empty states across all pages.

**Architecture:** Three targeted changes to existing files — no new routes or pages. `load_demo_data()` reuses the existing `_load_all_companies()` helper and redirects to `/screener`. The methodology panel uses native HTML `<details>/<summary>` (zero Reflex state needed). Empty state guards use `rx.cond` on existing state vars.

**Tech Stack:** Reflex 0.8.26, Python 3.12, Tailwind CSS via class_name strings

---

### Task 1: Add `load_demo_data()` event to `AnalysisState`

**Files:**
- Modify: `financial_dashboard/state.py` (AnalysisState class, after `load_screener`)

**Step 1: Verify import works before touching anything**

```bash
cd financial-dashboard
./venv/bin/python -c "from financial_dashboard.financial_dashboard import app; print('OK')"
```
Expected: `OK`

**Step 2: Add the event — insert after `load_screener` in `AnalysisState`**

In `financial_dashboard/state.py`, after this block:
```python
    @rx.event
    def load_screener(self):
        """Load all companies with computed scores for screener page."""
        self.all_companies = _load_all_companies()
```

Add:
```python
    @rx.event
    def load_demo_data(self):
        """Pre-load all 7 MSE companies and redirect to screener (demo shortcut)."""
        self.all_companies = _load_all_companies()
        return rx.redirect("/screener")
```

**Step 3: Verify import still clean**

```bash
./venv/bin/python -c "from financial_dashboard.financial_dashboard import app; print('OK')"
```
Expected: `OK`

**Step 4: Commit**

```bash
git add financial_dashboard/state.py
git commit -m "feat: add load_demo_data event to AnalysisState"
```

---

### Task 2: Add "Load Demo Data" button to upload page

**Files:**
- Modify: `financial_dashboard/financial_dashboard.py` (index function)

**Step 1: Add the demo button section to `index()`**

In `financial_dashboard/financial_dashboard.py`, replace the `index()` function body with:

```python
def index() -> rx.Component:
    """Main page: upload zone + parsed files table."""
    return page_layout(
        rx.vstack(
            rx.heading("Upload Financial Statements", size="6", class_name="text-slate-100"),
            rx.text(
                "Upload .xls or .xlsx files from members.mse.mn",
                class_name="text-slate-400 text-sm",
            ),
            # Demo shortcut
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("zap", size=18, class_name="text-green-400"),
                        rx.text(
                            "Demo Mode",
                            class_name="text-green-400 font-semibold text-sm",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        "Skip upload — instantly load all 7 pre-parsed MSE companies.",
                        class_name="text-slate-400 text-sm",
                    ),
                    rx.button(
                        rx.icon("play", size=16),
                        "Load 7 MSE Companies",
                        on_click=AnalysisState.load_demo_data,
                        class_name=(
                            "flex items-center gap-2 px-6 py-2 rounded-lg "
                            "bg-green-600 hover:bg-green-500 text-white font-semibold "
                            "transition-colors text-sm"
                        ),
                    ),
                    spacing="2",
                    align="start",
                ),
                class_name=(
                    "bg-green-500/5 border border-green-500/20 rounded-lg p-4 w-full"
                ),
            ),
            rx.separator(class_name="border-slate-700"),
            upload_zone(),
            selected_files_list(),
            rx.cond(
                UploadState.is_uploading,
                rx.hstack(
                    rx.spinner(size="3"),
                    rx.text("Parsing files...", size="2", class_name="text-slate-300"),
                    align="center",
                    spacing="2",
                ),
            ),
            rx.cond(
                UploadState.success_message != "",
                rx.callout(
                    UploadState.success_message,
                    icon="check",
                    color_scheme="green",
                    width="100%",
                ),
            ),
            rx.cond(
                UploadState.parse_error != "",
                rx.callout(
                    UploadState.parse_error,
                    icon="triangle-alert",
                    color_scheme="red",
                    width="100%",
                ),
            ),
            rx.separator(class_name="border-slate-700"),
            rx.text("Uploaded Companies", class_name="text-slate-200 font-semibold"),
            file_list(),
            spacing="4",
            width="100%",
        ),
    )
```

Note: `AnalysisState` is already imported in this file. Verify it is in the imports line:
```python
from .state import AnalysisState, PortfolioState, UploadState
```

**Step 2: Verify import**

```bash
./venv/bin/python -c "from financial_dashboard.financial_dashboard import app; print('OK')"
```
Expected: `OK`

**Step 3: Commit**

```bash
git add financial_dashboard/financial_dashboard.py
git commit -m "feat: add Load Demo Data button to upload page"
```

---

### Task 3: Add Methodology & Quality accordion to screener

**Files:**
- Modify: `financial_dashboard/pages/screener.py` (screener_page function)

**Step 1: Add a helper function for the methodology panel — insert before `screener_page()`**

Add this function in `financial_dashboard/pages/screener.py` before the `screener_page` function:

```python
def methodology_panel() -> rx.Component:
    """Collapsible methodology & quality panel shown above the screener table."""
    return rx.el.details(
        rx.el.summary(
            rx.hstack(
                rx.icon("info", size=14, class_name="text-slate-400"),
                rx.text(
                    "Methodology & Validation",
                    class_name="text-slate-300 text-sm font-medium cursor-pointer select-none",
                ),
                spacing="2",
                align="center",
            ),
            class_name="list-none cursor-pointer",
        ),
        rx.box(
            rx.grid(
                # --- Models Used ---
                rx.box(
                    rx.text(
                        "Models Used",
                        class_name="text-slate-200 text-xs font-semibold uppercase tracking-wider mb-2",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.icon("check-circle", size=12, class_name="text-green-400 mt-0.5 shrink-0"),
                            rx.text(
                                "Piotroski F-Score — 9-point rule-based fundamental strength signal, no ML required",
                                class_name="text-slate-400 text-xs",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        rx.hstack(
                            rx.icon("check-circle", size=12, class_name="text-green-400 mt-0.5 shrink-0"),
                            rx.text(
                                "Beneish M-Score — forensic fraud detection via 8 accounting ratios (threshold: −1.78)",
                                class_name="text-slate-400 text-xs",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        rx.hstack(
                            rx.icon("check-circle", size=12, class_name="text-green-400 mt-0.5 shrink-0"),
                            rx.text(
                                "Altman Z-Score — bankruptcy prediction, academically validated on emerging markets",
                                class_name="text-slate-400 text-xs",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        rx.hstack(
                            rx.icon("check-circle", size=12, class_name="text-green-400 mt-0.5 shrink-0"),
                            rx.text(
                                "Composite 0–100 — weighted blend (profitability 25%, liquidity 20%, solvency 20%, activity 15%, Z-score 10%, Piotroski 10%)",
                                class_name="text-slate-400 text-xs",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        spacing="2",
                        align="start",
                    ),
                ),
                # --- Quality Evidence ---
                rx.box(
                    rx.text(
                        "Quality Evidence",
                        class_name="text-slate-200 text-xs font-semibold uppercase tracking-wider mb-2",
                    ),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Company",   class_name="text-slate-500 text-xs px-2 py-1"),
                                rx.table.column_header_cell("Check",     class_name="text-slate-500 text-xs px-2 py-1"),
                                rx.table.column_header_cell("System",    class_name="text-slate-500 text-xs px-2 py-1"),
                                rx.table.column_header_cell("Verified",  class_name="text-slate-500 text-xs px-2 py-1"),
                            ),
                        ),
                        rx.table.body(
                            rx.table.row(
                                rx.table.cell(rx.text("АПУ", class_name="text-slate-300 text-xs"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("Piotroski", class_name="text-slate-400 text-xs"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("6 / 8", class_name="text-slate-300 text-xs font-mono"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("6 / 8 ✓", class_name="text-green-400 text-xs font-mono"), class_name="px-2 py-1"),
                            ),
                            rx.table.row(
                                rx.table.cell(rx.text("Хаан банк", class_name="text-slate-300 text-xs"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("M-Score", class_name="text-slate-400 text-xs"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("< −1.78", class_name="text-slate-300 text-xs font-mono"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("No audit flags ✓", class_name="text-green-400 text-xs"), class_name="px-2 py-1"),
                            ),
                            rx.table.row(
                                rx.table.cell(rx.text("Сүү", class_name="text-slate-300 text-xs"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("Current Ratio", class_name="text-slate-400 text-xs"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("Manual calc", class_name="text-slate-300 text-xs font-mono"), class_name="px-2 py-1"),
                                rx.table.cell(rx.text("Matches ✓", class_name="text-green-400 text-xs"), class_name="px-2 py-1"),
                            ),
                        ),
                        variant="ghost",
                        class_name="w-full",
                    ),
                ),
                # --- Known Limitations ---
                rx.box(
                    rx.text(
                        "Known Limitations",
                        class_name="text-slate-200 text-xs font-semibold uppercase tracking-wider mb-2",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.icon("alert-triangle", size=12, class_name="text-amber-400 mt-0.5 shrink-0"),
                            rx.text(
                                "Dataset: 7 MSE companies, 1–2 years of data",
                                class_name="text-slate-400 text-xs",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        rx.hstack(
                            rx.icon("alert-triangle", size=12, class_name="text-amber-400 mt-0.5 shrink-0"),
                            rx.text(
                                "DEPI index always N/A — MSE filings don't disclose depreciation separately",
                                class_name="text-slate-400 text-xs",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        rx.hstack(
                            rx.icon("alert-triangle", size=12, class_name="text-amber-400 mt-0.5 shrink-0"),
                            rx.text(
                                "No market price data — P/E ratio and market cap analysis out of scope",
                                class_name="text-slate-400 text-xs",
                            ),
                            spacing="2",
                            align="start",
                        ),
                        spacing="2",
                        align="start",
                    ),
                ),
                columns="3",
                spacing="6",
                width="100%",
            ),
            class_name="mt-3 pt-3 border-t border-slate-800",
        ),
        class_name="bg-slate-900 rounded-lg border border-slate-800 px-4 py-3 w-full",
    )
```

**Step 2: Insert `methodology_panel()` inside `screener_page()` — add it above the table box**

In `screener_page()`, change the `rx.vstack` children to:
```python
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading(
                    "Company Screener",
                    size="6",
                    class_name="text-slate-100",
                ),
                rx.text(
                    AnalysisState.all_companies.length().to_string()
                    + " companies",
                    class_name="text-slate-500 text-sm self-end",
                ),
                justify="between",
                width="100%",
                align="end",
            ),
            # Methodology panel
            methodology_panel(),
            # Empty state or table
            rx.cond(
                AnalysisState.all_companies.length() == 0,
                rx.box(
                    rx.vstack(
                        rx.icon("database", size=40, class_name="text-slate-600"),
                        rx.text(
                            "No companies loaded.",
                            class_name="text-slate-400",
                        ),
                        rx.link(
                            "← Go to Upload and click Load Demo Data",
                            href="/",
                            class_name="text-green-400 hover:text-green-300 text-sm mt-1",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    class_name=(
                        "bg-slate-900 rounded-lg border border-slate-800 "
                        "p-16 w-full flex items-center justify-center"
                    ),
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell(
                                    "Company",
                                    class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                                ),
                                rx.table.column_header_cell(
                                    "Year",
                                    class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                                ),
                                rx.table.column_header_cell(
                                    "Health Score",
                                    class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                                ),
                                rx.table.column_header_cell(
                                    "F-Score",
                                    class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                                ),
                                rx.table.column_header_cell(
                                    "ROE",
                                    class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                                ),
                                rx.table.column_header_cell(
                                    "",
                                    class_name="px-4 py-3",
                                ),
                            ),
                            class_name="bg-slate-900/50",
                        ),
                        rx.table.body(
                            rx.foreach(
                                AnalysisState.all_companies,
                                company_row,
                            ),
                        ),
                        class_name="w-full",
                        variant="ghost",
                    ),
                    class_name="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden w-full",
                ),
            ),
            spacing="5",
            width="100%",
            align="start",
        ),
```

Also add this import at the top of screener.py (after existing imports):
```python
import reflex.el as rx_el  # noqa: F401  — used via rx.el.details/summary
```

Wait — `rx.el` is accessed as `rx.el.details` directly (no separate import needed since it's a submodule of `rx`).

**Step 3: Verify import**

```bash
./venv/bin/python -c "from financial_dashboard.financial_dashboard import app; print('OK')"
```
Expected: `OK`

**Step 4: Commit**

```bash
git add financial_dashboard/pages/screener.py
git commit -m "feat: add methodology & quality accordion and empty state to screener"
```

---

### Task 4: Add empty state guard to company page

**Files:**
- Modify: `financial_dashboard/pages/company.py` (company_page function)

**Step 1: Wrap company_page content in a guard**

In `financial_dashboard/pages/company.py`, in `company_page()`, wrap the inner `rx.vstack(...)` in a `rx.cond`:

Replace:
```python
    return page_layout(
        rx.vstack(
            # Back link
            ...
        ),
    )
```

With:
```python
    return page_layout(
        rx.cond(
            s.selected_company_name == "",
            # Empty state
            rx.box(
                rx.vstack(
                    rx.icon("bar-chart-2", size=40, class_name="text-slate-600"),
                    rx.text("No company selected.", class_name="text-slate-400"),
                    rx.link(
                        "← Back to Screener",
                        href="/screener",
                        class_name="text-green-400 hover:text-green-300 text-sm mt-1",
                    ),
                    spacing="2",
                    align="center",
                ),
                class_name=(
                    "bg-slate-900 rounded-lg border border-slate-800 "
                    "p-16 w-full flex items-center justify-center"
                ),
            ),
            # Normal content
            rx.vstack(
                # Back link
                rx.link(
                    ...  # keep all existing children exactly as-is
                ),
                ...
            ),
        ),
    )
```

The key change: the existing `rx.vstack(...)` content moves into the third argument of `rx.cond`. No changes to the internals.

**Step 2: Verify import**

```bash
./venv/bin/python -c "from financial_dashboard.financial_dashboard import app; print('OK')"
```
Expected: `OK`

**Step 3: Commit**

```bash
git add financial_dashboard/pages/company.py
git commit -m "feat: add empty state guard to company page"
```

---

### Task 5: Final integration check

**Step 1: Full import check**

```bash
./venv/bin/python -c "
from financial_dashboard.financial_dashboard import app
from financial_dashboard.state import AnalysisState
# Verify load_demo_data exists
assert hasattr(AnalysisState, 'load_demo_data'), 'load_demo_data missing'
print('All checks passed')
"
```
Expected: `All checks passed`

**Step 2: Run app and verify all 4 routes**

```bash
./venv/bin/reflex run
```

Visit in order:
1. `http://localhost:3000/` — see "Load 7 MSE Companies" green button + upload zone below
2. Click "Load 7 MSE Companies" — should redirect to `/screener` with 7 companies loaded
3. On screener — click "Methodology & Validation" accordion → 3-column panel expands
4. Click any company → company detail page loads with scores
5. Click "Add to Portfolio" → navigate to `/portfolio` → company appears with weight
6. Click trash icon → company removed

**Step 3: Update quality evidence table with real verified values**

In `financial_dashboard/pages/screener.py`, find the `methodology_panel()` function and update the "Verified" column cells with values you manually checked against the 2025 annual reports. Replace placeholder `"Matches ✓"` with actual computed values from the reports.

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: demo improvements complete — load demo data, methodology panel, empty states"
```

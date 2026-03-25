"""Upload state management for MSE Analytica."""

import json
from pathlib import Path

import reflex as rx

from .analysis.ratios import (
    compute_beneish,
    compute_composite_score,
    compute_piotroski,
    compute_ratios,
)
from .parser.excel_parser import parse_excel_file
from .scraper.price_scraper import scrape_company_prices, save_price_data
from .scraper.registry_loader import find_mse_id
from .storage.json_store import (
    DATA_DIR,
    delete_parsed_file,
    load_index,
    save_parsed_data,
)


class UploadState(rx.State):
    """Manages file upload, parsing, and display state."""

    # Upload status
    is_uploading: bool = False
    upload_progress: int = 0

    # File list from index.json (sheets_parsed stored as comma-joined string)
    uploaded_files: list[dict[str, str]] = []

    # Feedback messages
    parse_error: str = ""
    success_message: str = ""

    # Price refresh state
    is_refreshing_prices: bool = False
    price_refresh_log: list[dict[str, str]] = []
    price_refresh_summary: str = ""

    # Currently selected file
    selected_file: str = ""

    def _refresh_file_list(self):
        """Reload uploaded files from index.json."""
        index = load_index()
        files = index.get("files", [])
        # Flatten sheets_parsed list to a string for Reflex rendering
        for f in files:
            if isinstance(f.get("sheets_parsed"), list):
                f["sheets_parsed"] = ", ".join(f["sheets_parsed"])
        self.uploaded_files = files

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        """Handle uploaded files: parse Excel and save as JSON."""
        self.is_uploading = True
        self.parse_error = ""
        self.success_message = ""
        yield

        parsed_count = 0
        errors = []

        for file in files:
            filename = file.filename or "unknown.xlsx"
            try:
                file_bytes = file.file.read()

                if not filename.lower().endswith((".xlsx", ".xls")):
                    errors.append(f"{filename}: Not an Excel file (.xlsx/.xls)")
                    continue

                parsed = parse_excel_file(file_bytes, filename)
                save_parsed_data(parsed)
                parsed_count += 1

            except ValueError as e:
                errors.append(f"{filename}: {e}")
            except Exception as e:
                errors.append(f"{filename}: Unexpected error - {e}")

        self.is_uploading = False
        self.upload_progress = 0
        self._refresh_file_list()

        if parsed_count > 0:
            self.success_message = (
                f"Successfully parsed {parsed_count} file(s)."
            )
        if errors:
            self.parse_error = " | ".join(errors)

    @rx.event
    def on_load(self):
        """Load file list when page loads."""
        self._refresh_file_list()

    @rx.event
    def select_file(self, filename: str):
        """Select a file for viewing."""
        self.selected_file = filename

    @rx.event
    def delete_file(self, filename: str):
        """Delete a parsed file and refresh the list."""
        self.parse_error = ""
        self.success_message = ""
        try:
            delete_parsed_file(filename)
            self.success_message = f"Deleted {filename}."
            self.selected_file = ""
        except Exception as e:
            self.parse_error = f"Error deleting {filename}: {e}"
        self._refresh_file_list()

    @rx.event
    def clear_messages(self):
        """Clear success and error messages."""
        self.parse_error = ""
        self.success_message = ""

    @rx.event
    async def refresh_prices(self):
        """Re-scrape prices for companies currently in index.json."""
        self.is_refreshing_prices = True
        self.price_refresh_log = []
        self.price_refresh_summary = ""
        yield

        index = load_index()
        companies = list({e["company"] for e in index.get("files", [])})

        ok = 0
        failed = 0
        log_entries: list[dict[str, str]] = []

        for company in companies:
            try:
                mse_id = find_mse_id(company)
                records = scrape_company_prices(mse_id, company)
                save_price_data(company, mse_id, records)
                log_entries.append({
                    "company": company,
                    "status": "ok",
                    "detail": f"{len(records)} records"
                })
                ok += 1
            except Exception as e:
                log_entries.append({
                    "company": company,
                    "status": "error",
                    "detail": str(e)
                })
                failed += 1
            self.price_refresh_log = list(log_entries)
            yield

        self.is_refreshing_prices = False
        self.price_refresh_summary = f"{ok} updated, {failed} failed"
        yield


def _load_all_companies() -> list[dict]:
    """Load all parsed company JSONs and compute scores for each."""
    index_path = DATA_DIR / "index.json"
    if not index_path.exists():
        return []
    with open(index_path) as f:
        index = json.load(f)

    results = []
    for entry in index.get("files", []):
        try:
            fp = DATA_DIR / entry["filename"]
            with open(fp) as f:
                data = json.load(f)

            ratios    = compute_ratios(data)
            piotroski = compute_piotroski(data)
            beneish   = compute_beneish(data)
            composite = compute_composite_score(ratios, piotroski, beneish)

            roe = ratios["current"].get("profitability", {}).get("roe")
            f_score = piotroski["f_score"]
            max_score = piotroski["max_score"]
            results.append({
                "filename":    entry["filename"],
                "company":     entry["company"],
                "url":         f"/company/{entry['company']}",
                "year":        entry.get("year", ""),
                "sector":      entry.get("sector", ""),
                "score":       composite["score"],
                "label":       composite["label"],
                "color":       composite["color"],
                "roe_str":     f"{roe * 100:.1f}%" if roe is not None else "N/A",
                "f_score_str": f"{f_score} / {max_score}" if f_score is not None else "N/A",
            })
        except Exception as e:
            print(f"[_load_all_companies] Skipping {entry.get('filename', '?')}: {e}")
            continue
    return results


def _fmt(v, decimals: int = 2) -> str:
    """Format a float/int for display, or 'N/A' if None."""
    return f"{v:.{decimals}f}" if v is not None else "N/A"


def _crit(v) -> int:
    """Convert Piotroski criterion (1/0/None) to int (-1 for None)."""
    if v is None:
        return -1
    return int(v)


class AnalysisState(UploadState):
    """State for company screener and individual company analysis."""

    # Screener
    all_companies: list[dict] = []
    screener_filter: str = "All"     # sector filter value

    # Company detail — raw dicts (kept for any backend use)
    selected_company_name: str = ""
    company_ratios:    dict = {}
    company_piotroski: dict = {}
    company_beneish:   dict = {}
    company_composite: dict = {}

    # Flat display vars — composite
    company_score: int = 0
    company_health_label: str = ""
    company_health_color: str = ""

    # Flat display vars — scores
    company_f_score_display: str = ""
    company_m_score_display: str = ""
    company_m_interp: str = ""

    # Flat display vars — ratios (pre-formatted strings)
    company_roa: str = ""
    company_roe: str = ""
    company_net_margin: str = ""
    company_current_ratio: str = ""
    company_quick_ratio: str = ""
    company_debt_equity: str = ""
    company_interest_cov: str = ""
    company_asset_turnover: str = ""
    company_z_score: str = ""

    # Flat display vars — Piotroski criteria (1/0/-1)
    company_f1: int = -1
    company_f2: int = -1
    company_f3: int = -1
    company_f4: int = -1
    company_f5: int = -1
    company_f6: int = -1
    company_f8: int = -1
    company_f9: int = -1

    # Flat display vars — Beneish indices (pre-formatted strings)
    company_dsri: str = ""
    company_gmi: str = ""
    company_aqi: str = ""
    company_sgi: str = ""
    company_sgai: str = ""
    company_lvgi: str = ""
    company_tata: str = ""

    @rx.event
    def load_screener(self):
        """Load all companies with computed scores for screener page."""
        self.all_companies = _load_all_companies()

    @rx.event
    def load_demo_data(self):
        """Pre-load all 7 MSE companies and redirect to screener (demo shortcut)."""
        self.all_companies = _load_all_companies()
        return rx.redirect("/screener")

    @rx.event
    def load_company(self, company_name: str):
        """Load and compute full analysis for one company."""
        self.selected_company_name = company_name
        index_path = DATA_DIR / "index.json"
        if not index_path.exists():
            return
        with open(index_path) as f:
            index = json.load(f)

        filename = next(
            (e["filename"] for e in index.get("files", [])
             if e["company"] == company_name),
            None
        )
        if not filename:
            return

        fp = DATA_DIR / filename
        with open(fp) as f:
            data = json.load(f)

        self.company_ratios    = compute_ratios(data)
        self.company_piotroski = compute_piotroski(data)
        self.company_beneish   = compute_beneish(data)
        self.company_composite = compute_composite_score(
            self.company_ratios, self.company_piotroski, self.company_beneish
        )

        # --- Populate flat display vars ---
        comp  = self.company_composite
        piots = self.company_piotroski
        ben   = self.company_beneish
        curr  = self.company_ratios.get("current", {})

        self.company_score        = comp.get("score", 0)
        self.company_health_label = comp.get("label", "")
        self.company_health_color = comp.get("color", "")

        fs = piots.get("f_score")
        ms = piots.get("max_score")
        self.company_f_score_display = f"{fs} / {ms}" if fs is not None else "N/A"
        mv = ben.get("m_score")
        self.company_m_score_display = f"{mv:.2f}" if mv is not None else "N/A"
        self.company_m_interp = ben.get("interpretation", "")

        prof = curr.get("profitability", {})
        liq  = curr.get("liquidity", {})
        solv = curr.get("solvency", {})
        act  = curr.get("activity", {})
        zs   = curr.get("z_score", {})

        self.company_roa          = _fmt(prof.get("roa"))
        self.company_roe          = _fmt(prof.get("roe"))
        self.company_net_margin   = _fmt(prof.get("net_margin"))
        self.company_current_ratio = _fmt(liq.get("current_ratio"))
        self.company_quick_ratio  = _fmt(liq.get("quick_ratio"))
        self.company_debt_equity  = _fmt(solv.get("debt_to_equity"))
        self.company_interest_cov = _fmt(solv.get("interest_coverage"))
        self.company_asset_turnover = _fmt(act.get("total_asset_turnover"))
        self.company_z_score      = _fmt(zs.get("z_score"))

        crit = piots.get("criteria", {})
        self.company_f1 = _crit(crit.get("f1_roa_positive"))
        self.company_f2 = _crit(crit.get("f2_ocf_positive"))
        self.company_f3 = _crit(crit.get("f3_roa_improving"))
        self.company_f4 = _crit(crit.get("f4_accruals"))
        self.company_f5 = _crit(crit.get("f5_leverage_down"))
        self.company_f6 = _crit(crit.get("f6_liquidity_up"))
        self.company_f8 = _crit(crit.get("f8_gross_margin_up"))
        self.company_f9 = _crit(crit.get("f9_asset_turnover_up"))

        idx = ben.get("indices", {})
        self.company_dsri  = _fmt(idx.get("dsri"))
        self.company_gmi   = _fmt(idx.get("gmi"))
        self.company_aqi   = _fmt(idx.get("aqi"))
        self.company_sgi   = _fmt(idx.get("sgi"))
        self.company_sgai  = _fmt(idx.get("sgai"))
        self.company_lvgi  = _fmt(idx.get("lvgi"))
        self.company_tata  = _fmt(idx.get("tata"))

    @rx.event
    def on_load_company(self):
        """Called on page load -- reads company name from URL params."""
        company = self.router.page.params.get("company", "")
        if company:
            self.load_company(company)

    @rx.var
    def filtered_companies(self) -> list[dict]:
        if self.screener_filter == "All":
            return self.all_companies
        return [
            c for c in self.all_companies
            if c.get("sector") == self.screener_filter
        ]


class PortfolioState(AnalysisState):
    """State for portfolio management."""

    # List of { company, filename, weight, score, label, color }
    holdings: list[dict] = []

    @rx.event
    def add_to_portfolio(self, company: str):
        """Add a company to portfolio with equal weight."""
        if any(h["company"] == company for h in self.holdings):
            return  # already in portfolio
        entry = next(
            (c for c in self.all_companies if c["company"] == company),
            None
        )
        if not entry:
            return
        n = len(self.holdings) + 1
        # Rebalance to equal weights
        new_weight = round(1 / n, 4)
        weight_str = f"{new_weight * 100:.1f}%"
        holdings = [
            {**h, "weight": new_weight, "weight_str": weight_str}  # score_str preserved via **h
            for h in self.holdings
        ]
        holdings.append({
            "company":    entry["company"],
            "filename":   entry["filename"],
            "url":        entry.get("url", f"/company/{entry['company']}"),
            "weight":     new_weight,
            "weight_str": f"{new_weight * 100:.1f}%",
            "score":      entry["score"],
            "score_str":  str(entry["score"]),
            "label":      entry["label"],
            "color":      entry["color"],
        })
        self.holdings = holdings

    @rx.event
    def remove_from_portfolio(self, company: str):
        """Remove a company and rebalance weights."""
        holdings = [h for h in self.holdings if h["company"] != company]
        n = len(holdings)
        if n > 0:
            new_weight = round(1 / n, 4)
            weight_str = f"{new_weight * 100:.1f}%"
            holdings = [{**h, "weight": new_weight, "weight_str": weight_str} for h in holdings]
        self.holdings = holdings

    @rx.var
    def portfolio_health(self) -> int:
        """Blended health score across portfolio (weighted average)."""
        if not self.holdings:
            return 0
        total = sum(h["score"] * h["weight"] for h in self.holdings)
        return int(round(total))

    @rx.var
    def in_portfolio(self) -> list[str]:
        """List of company names currently in portfolio."""
        return [h["company"] for h in self.holdings]

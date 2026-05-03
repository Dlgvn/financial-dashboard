"""Upload state management for MSE Analytica."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import reflex as rx

from .analysis.ratios import (
    compute_beneish,
    compute_composite_score,
    compute_bank_composite_score,
    compute_insurance_composite_score,
    compute_finance_composite_score,
    compute_piotroski,
    compute_ratios,
)
from .analysis.bank_ratios import compute_bank_ratios
from .analysis.insurance_ratios import compute_insurance_ratios
from .analysis.finance_ratios import compute_finance_ratios
from .analysis.sector_forensics import (
    compute_bank_forensic,
    compute_insurance_forensic,
    compute_finance_forensic,
)
from .analysis.ai_red_flags import compute_red_flags_ai
from .parser.excel_parser import parse_excel_file
from .analysis.valuation import compute_valuation_metrics
from .scraper.price_scraper import scrape_company_prices, save_price_data, PRICES_DIR, price_filename
from .scraper.registry_loader import find_mse_id, find_sub_sector
from .storage.json_store import (
    DATA_DIR,
    delete_parsed_file,
    load_index,
    save_parsed_data,
)

def _detect_sector_from_data(data: dict) -> str:
    if "bank_balance_sheet" in data or "bank_income_statement" in data:
        return "Banking"
    if "insurance_balance_sheet" in data or "insurance_income_statement" in data:
        return "Insurance"
    if "securities_balance_sheet" in data or "securities_income_statement" in data:
        return "Finance"
    return "Standard"


def _detect_finance_subsector(company_name: str) -> str:
    """Classify a Finance-sector company into its NBFI subsector.

    Registry lookup takes precedence; name-pattern heuristics are the fallback.
    """
    registry_sub = find_sub_sector(company_name)
    if registry_sub:
        return registry_sub
    name = company_name.upper()
    if "ББСБ" in name or "ЛЭНД" in name or "МОННАБ" in name:
        return "ББСБ (Lending NBFI)"
    if "СЕКЮРИТ" in name or "СЕК" in name or "БИДИСЕК" in name:
        return "Securities/Brokerage"
    if "ХОЛДИНГ" in name or "ИНВЕСТМЕНТ" in name or "НЭГДЭЛ" in name or "ИННОВЭЙШН" in name:
        return "Investment/Holding"
    return "Finance"


def _compute_red_flags(ratios: dict, beneish: dict) -> list[dict[str, str]]:
    flags = []

    # Check DSRI > 1.1
    indices = beneish.get("indices", {})
    dsri = indices.get("dsri")
    if dsri is not None and dsri > 1.1:
        flags.append({"flag": "Receivables Outpacing Revenue", "explanation": f"DSRI = {dsri:.2f} (>1.1). Receivables growing faster than revenue may signal aggressive revenue recognition."})

    # Check TATA > 0.05
    tata = indices.get("tata")
    if tata is not None and tata > 0.05:
        flags.append({"flag": "Earnings Quality Warning", "explanation": f"TATA = {tata:.3f} (>0.05). High accruals relative to total assets indicate lower earnings quality."})

    # Check debt/equity increase > 25%
    curr_ratios = ratios.get("current", {})
    prev_ratios = ratios.get("prev", {})
    curr_de = curr_ratios.get("solvency", {}).get("debt_to_equity")
    prev_de = prev_ratios.get("solvency", {}).get("debt_to_equity")
    if curr_de is not None and prev_de is not None and prev_de > 0:
        change = (curr_de - prev_de) / abs(prev_de)
        if change > 0.25:
            flags.append({"flag": "Leverage Spike", "explanation": f"Debt/Equity rose from {prev_de:.2f} to {curr_de:.2f} (+{change*100:.0f}%). Significant leverage increase warrants scrutiny."})

    # Check M-Score > -1.78 when reliable
    if beneish.get("reliable"):
        m_score = beneish.get("m_score")
        if m_score is not None and m_score > -1.78:
            flags.append({"flag": "Beneish Manipulation Signal", "explanation": f"M-Score = {m_score:.2f} (>-1.78). Model suggests possible earnings manipulation. Investigate further."})

    # Check current ratio dropped below 1.0
    curr_cr = curr_ratios.get("liquidity", {}).get("current_ratio")
    prev_cr = prev_ratios.get("liquidity", {}).get("current_ratio")
    if curr_cr is not None and curr_cr < 1.0 and (prev_cr is None or prev_cr >= 1.0):
        flags.append({"flag": "Liquidity Deterioration", "explanation": f"Current ratio = {curr_cr:.2f} (<1.0). Company may struggle to meet short-term obligations."})

    if not flags:
        return [{"flag": "No Major Red Flags", "explanation": "No significant accounting anomalies detected."}]
    return flags


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
                records, shares = scrape_company_prices(mse_id, company)
                save_price_data(company, mse_id, records, shares_outstanding=shares)
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

            sector    = entry.get("sector") or _detect_sector_from_data(data)
            piotroski = compute_piotroski(data)
            beneish   = compute_beneish(data)

            if sector == "Banking":
                bank_result = compute_bank_ratios(data)
                bank_curr = bank_result.get("current", {})
                bank_prof = bank_curr.get("profitability", {})
                composite = compute_bank_composite_score(bank_result)
                roe = bank_prof.get("roe")
            elif sector == "Insurance":
                ins_result = compute_insurance_ratios(data)
                ins_curr = ins_result.get("current", {})
                ins_prof = ins_curr.get("profitability", {})
                composite = compute_insurance_composite_score(ins_result)
                roe = ins_prof.get("roe")
            elif sector == "Finance":
                fin_result = compute_finance_ratios(data)
                fin_curr = fin_result.get("current", {})
                fin_prof = fin_curr.get("profitability", {})
                composite = compute_finance_composite_score(fin_result)
                roe = fin_prof.get("roe")
            else:
                ratios    = compute_ratios(data)
                composite = compute_composite_score(ratios, piotroski, beneish)
                roe = ratios["current"].get("profitability", {}).get("roe")

            _financial_sector = sector in ("Banking", "Insurance", "Finance")
            f_score = piotroski["f_score"]
            max_score = piotroski["max_score"]
            results.append({
                "filename":    entry["filename"],
                "company":     entry["company"],
                "url":         f"/company/{entry['company']}",
                "year":        entry.get("year", ""),
                "sector":      sector,
                "score":       composite["score"],
                "label":       composite["label"],
                "color":       composite["color"],
                "roe":         roe if roe is not None else 0.0,
                "roe_str":     f"{roe * 100:.1f}%" if roe is not None else "N/A",
                "f_score":     int(f_score) if (f_score is not None and not _financial_sector) else 0,
                "f_score_str": "N/A" if _financial_sector else (f"{f_score} / {max_score}" if f_score is not None else "N/A"),
            })
        except Exception as e:
            print(f"[_load_all_companies] Skipping {entry.get('filename', '?')}: {e}")
            continue
    return results


def _fmt(v, decimals: int = 2) -> str:
    """Format a float/int for display, or 'N/A' if None."""
    return f"{v:.{decimals}f}" if v is not None else "N/A"


def _pct(v, decimals: int = 2) -> str:
    """Format a ratio (0–1 decimal) as a percentage string, or 'N/A' if None."""
    return f"{v * 100:.{decimals}f}" if v is not None else "N/A"


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

    # Sector identity
    company_sector: str = ""
    company_is_bank: bool = False
    company_is_insurance: bool = False
    company_is_finance: bool = False
    company_finance_subsector: str = ""   # "ББСБ (Lending NBFI)" | "Securities" | "Investment/Holding" | "Finance"

    # Chart data vars (must be list[dict] for rx.recharts)
    company_gauge_data: list[dict] = []
    company_radar_data: list[dict] = []
    company_beneish_chart_data: list[dict] = []

    # Sector-specific forensic (Banking / Insurance / Finance)
    company_sector_forensic_criteria: list[dict] = []
    company_sector_forensic_score_display: str = ""
    company_sector_forensic_chart_data: list[dict] = []

    # DuPont vars (current and prior year)
    company_net_margin_dupont: str = ""
    company_net_margin_prev: str = ""
    company_asset_turnover_dupont: str = ""
    company_asset_turnover_prev: str = ""
    company_equity_multiplier_curr: str = ""
    company_equity_multiplier_prev: str = ""
    company_roe_dupont: str = ""
    company_roe_prev: str = ""
    # Sector-aware DuPont labels and formula description
    company_dupont_factor1_label: str = "Net Margin"
    company_dupont_factor1_unit: str = "%"
    company_dupont_factor2_label: str = "Asset Turnover"
    company_dupont_factor2_unit: str = "times"
    company_dupont_formula_text: str = "ROE = Net Profit Margin × Asset Turnover × Equity Multiplier"
    company_dupont_show_factor2: bool = True

    # Red flags
    company_red_flags: list[dict] = []
    company_red_flags_loading: bool = False

    # Additional standard ratios (17 beyond existing 9)
    company_gross_margin: str = ""
    company_operating_margin: str = ""
    company_ebit_margin: str = ""
    company_cash_ratio: str = ""
    company_working_capital: str = ""
    company_debt_to_assets: str = ""
    company_equity_ratio: str = ""
    company_ocf_ratio: str = ""
    company_cf_to_debt: str = ""
    company_reinvestment_ratio: str = ""
    company_fixed_asset_turnover: str = ""
    company_inventory_turnover: str = ""
    company_days_inventory: str = ""
    company_receivables_turnover: str = ""
    company_days_sales_outstanding: str = ""
    company_payables_turnover: str = ""
    company_days_payable_outstanding: str = ""
    company_cash_conversion_cycle: str = ""
    company_z_x1: str = ""
    company_z_x2: str = ""
    company_z_x3: str = ""
    company_z_x4: str = ""
    company_z_x5: str = ""

    # Bank ratio flat vars (17)
    company_bank_nim: str = ""
    company_bank_npl_ratio: str = ""
    company_bank_ldr: str = ""
    company_bank_cost_to_income: str = ""
    company_bank_roa: str = ""
    company_bank_roe: str = ""
    company_bank_net_margin: str = ""
    company_bank_interest_income_ratio: str = ""
    company_bank_equity_multiplier: str = ""
    company_bank_equity_to_assets: str = ""
    company_bank_coverage_ratio: str = ""
    company_bank_loan_loss_reserve_ratio: str = ""
    company_bank_provision_to_loans: str = ""
    company_bank_cash_to_deposits: str = ""
    company_bank_loans_to_assets: str = ""
    company_bank_securities_to_assets: str = ""
    company_bank_fee_income_ratio: str = ""

    # Finance / NBFI ratio flat vars (14)
    company_fin_nim: str = ""
    company_fin_yield_on_earning_assets: str = ""
    company_fin_cost_of_funds: str = ""
    company_fin_interest_spread: str = ""
    company_fin_roa: str = ""
    company_fin_roe: str = ""
    company_fin_net_margin: str = ""
    company_fin_cost_to_income: str = ""
    company_fin_operating_expense_ratio: str = ""
    company_fin_non_interest_income_ratio: str = ""
    company_fin_asset_utilisation: str = ""
    company_fin_debt_to_equity: str = ""
    company_fin_debt_to_assets: str = ""
    company_fin_equity_ratio: str = ""
    company_fin_equity_multiplier: str = ""
    company_fin_cash_ratio: str = ""
    company_fin_ocf_ratio: str = ""
    company_fin_loan_to_assets: str = ""
    company_fin_npa_ratio: str = ""
    company_fin_receivables_to_assets: str = ""
    company_fin_provision_coverage: str = ""

    # Insurance ratio flat vars (15)
    company_ins_loss_ratio: str = ""
    company_ins_expense_ratio: str = ""
    company_ins_combined_ratio: str = ""
    company_ins_roa: str = ""
    company_ins_roe: str = ""
    company_ins_net_margin: str = ""
    company_ins_investment_income_ratio: str = ""
    company_ins_underwriting_margin: str = ""
    company_ins_solvency_ratio: str = ""
    company_ins_leverage_ratio: str = ""
    company_ins_equity_to_liabilities: str = ""
    company_ins_reserve_coverage: str = ""
    company_ins_ocf_ratio: str = ""
    company_ins_investment_ratio: str = ""
    company_ins_cash_to_liabilities: str = ""

    # Screener sort state
    screener_sort_col: str = "score"
    screener_sort_asc: bool = False

    # Valuation display vars
    company_ev_ebitda: str = ""
    company_fcf_yield: str = ""
    company_pe: str = ""
    company_pbv: str = ""
    company_shares_outstanding: str = ""
    # Sector tag drives which additional cards are shown
    company_valuation_sector: str = "standard"
    # Bank / NBFI metrics
    company_ptbv: str = ""
    company_p_ppop: str = ""
    company_p_nii: str = ""
    # Insurance metrics
    company_p_npe: str = ""
    company_p_uwp: str = ""
    # Holding company metrics
    company_p_inv_sec: str = ""
    # Securities / Broker metrics
    company_p_revenue: str = ""

    # Shares input UI state
    company_shares_input_open: bool = False
    company_shares_input_value: str = ""

    # Price chart data (list[dict[str, str]] per Reflex constraint)
    company_price_chart_data: list[dict[str, str]] = []
    company_volume_chart_data: list[dict[str, str]] = []

    # Range toggle
    valuation_range: str = "1Y"

    @rx.event
    def load_screener(self):
        """Load all companies with computed scores for screener page."""
        self.all_companies = _load_all_companies()

    @rx.event
    async def load_company(self, company_name: str):
        """Load and compute full analysis for one company."""
        self.selected_company_name = company_name
        index_path = DATA_DIR / "index.json"
        if not index_path.exists():
            return
        with open(index_path) as f:
            index = json.load(f)

        entry = next(
            (e for e in index.get("files", [])
             if e["company"] == company_name),
            None
        )
        if not entry:
            return
        filename = entry["filename"]

        fp = DATA_DIR / filename
        with open(fp) as f:
            data = json.load(f)

        # --- Detect sector from index.json (authoritative), fall back to data-key heuristic ---
        sector = entry.get("sector") or _detect_sector_from_data(data)
        self.company_sector = sector
        self.company_is_bank = sector == "Banking"
        self.company_is_insurance = sector == "Insurance"
        self.company_is_finance = sector == "Finance"

        # --- Compute ratios based on sector ---
        self.company_piotroski = compute_piotroski(data)
        self.company_beneish   = compute_beneish(data)

        if sector == "Banking":
            bank_result = compute_bank_ratios(data)
            # Store bank ratios in company_ratios for composite scoring compatibility
            # Map bank profitability to standard format for composite score
            self.company_ratios = bank_result
            # For composite score, build a compatible ratios dict using bank data
            bank_curr = bank_result.get("current", {})
            bank_prof = bank_curr.get("profitability", {})
            bank_cap = bank_curr.get("capital_adequacy", {})
            bank_liq = bank_curr.get("liquidity", {})
            self.company_composite = compute_bank_composite_score(bank_result)
            # Populate bank flat vars
            bank_aq = bank_curr.get("asset_quality", {})
            bank_eff = bank_curr.get("efficiency", {})
            self.company_bank_nim = _pct(bank_prof.get("nim"))
            self.company_bank_npl_ratio = _pct(bank_aq.get("npl_ratio"))
            self.company_bank_ldr = _pct(bank_liq.get("ldr"))
            self.company_bank_cost_to_income = _pct(bank_eff.get("cost_to_income"))
            self.company_bank_roa = _pct(bank_prof.get("roa"))
            self.company_bank_roe = _pct(bank_prof.get("roe"))
            self.company_bank_net_margin = _pct(bank_prof.get("net_margin"))
            self.company_bank_interest_income_ratio = _pct(bank_prof.get("interest_income_ratio"))
            self.company_bank_equity_multiplier = _fmt(bank_cap.get("equity_multiplier"))
            self.company_bank_equity_to_assets = _pct(bank_cap.get("equity_to_assets"))
            self.company_bank_coverage_ratio = _fmt(bank_aq.get("coverage_ratio"))
            self.company_bank_loan_loss_reserve_ratio = _pct(bank_aq.get("loan_loss_reserve_ratio"))
            self.company_bank_provision_to_loans = _pct(bank_aq.get("provision_to_loans"))
            self.company_bank_cash_to_deposits = _pct(bank_liq.get("cash_to_deposits"))
            self.company_bank_loans_to_assets = _pct(bank_liq.get("loans_to_assets"))
            self.company_bank_securities_to_assets = _pct(bank_liq.get("securities_to_assets"))
            self.company_bank_fee_income_ratio = _pct(bank_eff.get("fee_income_ratio"))
            # Standard display vars using bank proxies
            self.company_roa = _pct(bank_prof.get("roa"))
            self.company_roe = _pct(bank_prof.get("roe"))
            self.company_net_margin = _pct(bank_prof.get("net_margin"))
            self.company_current_ratio = _fmt(bank_liq.get("ldr"))
            self.company_quick_ratio = "N/A"
            self.company_debt_equity = "N/A"
            self.company_interest_cov = "N/A"
            self.company_asset_turnover = "N/A"
            self.company_z_score = "N/A"
            _bf = compute_bank_forensic(bank_result)
            self.company_sector_forensic_criteria = _bf["criteria"]
            self.company_sector_forensic_score_display = f"{_bf['score']} / {_bf['max_score']}"
            self.company_sector_forensic_chart_data = _bf["chart_data"]
            # Banking DuPont: ROE = ROA × Equity Multiplier (2-factor)
            bank_prev = bank_result.get("prev", {})
            bank_prev_prof = bank_prev.get("profitability", {})
            bank_prev_cap  = bank_prev.get("capital_adequacy", {})
            self.company_dupont_factor1_label = "ROA"
            self.company_dupont_factor1_unit  = "%"
            self.company_dupont_factor2_label = ""
            self.company_dupont_factor2_unit  = ""
            self.company_dupont_show_factor2  = False
            self.company_dupont_formula_text  = "ROE = ROA × Equity Multiplier"
            self.company_net_margin_dupont    = _pct(bank_prof.get("roa"))
            self.company_net_margin_prev      = _pct(bank_prev_prof.get("roa"))
            self.company_asset_turnover_dupont = ""
            self.company_asset_turnover_prev   = ""
            self.company_equity_multiplier_curr = _fmt(bank_cap.get("equity_multiplier"))
            self.company_equity_multiplier_prev = _fmt(bank_prev_cap.get("equity_multiplier"))
            self.company_roe_dupont = _pct(bank_prof.get("roe"))
            self.company_roe_prev   = _pct(bank_prev_prof.get("roe"))

        elif sector == "Insurance":
            ins_result = compute_insurance_ratios(data)
            self.company_ratios = ins_result
            ins_curr = ins_result.get("current", {})
            ins_prof = ins_curr.get("profitability", {})
            ins_solv = ins_curr.get("solvency", {})
            ins_liq = ins_curr.get("liquidity", {})
            ins_uw = ins_curr.get("underwriting", {})
            self.company_composite = compute_insurance_composite_score(ins_result)
            # Populate insurance flat vars
            self.company_ins_loss_ratio = _pct(ins_uw.get("loss_ratio"))
            self.company_ins_expense_ratio = _pct(ins_uw.get("expense_ratio"))
            self.company_ins_combined_ratio = _pct(ins_uw.get("combined_ratio"))
            self.company_ins_roa = _pct(ins_prof.get("roa"))
            self.company_ins_roe = _pct(ins_prof.get("roe"))
            self.company_ins_net_margin = _pct(ins_prof.get("net_margin"))
            self.company_ins_investment_income_ratio = _pct(ins_prof.get("investment_income_ratio"))
            self.company_ins_underwriting_margin = _pct(ins_prof.get("underwriting_margin"))
            self.company_ins_solvency_ratio = _pct(ins_solv.get("solvency_ratio"))
            self.company_ins_leverage_ratio = _fmt(ins_solv.get("leverage_ratio"))
            self.company_ins_equity_to_liabilities = _fmt(ins_solv.get("equity_to_liabilities"))
            self.company_ins_reserve_coverage = _fmt(ins_solv.get("reserve_coverage"))
            self.company_ins_ocf_ratio = _pct(ins_liq.get("ocf_ratio"))
            self.company_ins_investment_ratio = _pct(ins_liq.get("investment_ratio"))
            self.company_ins_cash_to_liabilities = _pct(ins_liq.get("cash_to_liabilities"))
            # Standard display vars using insurance proxies
            self.company_roa = _pct(ins_prof.get("roa"))
            self.company_roe = _pct(ins_prof.get("roe"))
            self.company_net_margin = _pct(ins_prof.get("net_margin"))
            self.company_current_ratio = "N/A"
            self.company_quick_ratio = "N/A"
            self.company_debt_equity = _fmt(ins_solv.get("leverage_ratio"))
            self.company_interest_cov = "N/A"
            self.company_asset_turnover = "N/A"
            self.company_z_score = "N/A"
            _if = compute_insurance_forensic(ins_result)
            self.company_sector_forensic_criteria = _if["criteria"]
            self.company_sector_forensic_score_display = f"{_if['score']} / {_if['max_score']}"
            self.company_sector_forensic_chart_data = _if["chart_data"]
            # Insurance DuPont: ROE = Net Margin × Asset Utilization × Equity Multiplier
            # Asset Utilization = premiums / total_assets (revenue proxy for insurers)
            ins_prev = ins_result.get("prev", {})
            ins_prev_prof = ins_prev.get("profitability", {})
            ins_prev_solv = ins_prev.get("solvency", {})
            ins_leverage   = ins_solv.get("leverage_ratio")       # liabilities / equity
            ins_leverage_p = ins_prev_solv.get("leverage_ratio")
            # Equity Multiplier = 1 + leverage_ratio = assets / equity
            ins_eq_mult   = (1 + ins_leverage)   if ins_leverage   is not None else None
            ins_eq_mult_p = (1 + ins_leverage_p) if ins_leverage_p is not None else None
            # Asset Utilization: use premiums/assets — stored in insurance ratios as a proxy via
            # net_margin = net_income/premiums and roa = net_income/assets → AU = roa/net_margin
            ins_roa_v   = ins_prof.get("roa")
            ins_nm_v    = ins_prof.get("net_margin")
            ins_roa_p   = ins_prev_prof.get("roa")
            ins_nm_p    = ins_prev_prof.get("net_margin")
            ins_au      = (ins_roa_v / ins_nm_v)   if (ins_roa_v is not None and ins_nm_v and ins_nm_v != 0) else None
            ins_au_prev = (ins_roa_p / ins_nm_p)   if (ins_roa_p is not None and ins_nm_p and ins_nm_p != 0) else None
            self.company_dupont_factor1_label = "Net Margin"
            self.company_dupont_factor1_unit  = "%"
            self.company_dupont_factor2_label = "Asset Utilization"
            self.company_dupont_factor2_unit  = "times"
            self.company_dupont_show_factor2  = True
            self.company_dupont_formula_text  = "ROE = Net Margin × Asset Utilization × Equity Multiplier"
            self.company_net_margin_dupont    = _pct(ins_nm_v)
            self.company_net_margin_prev      = _pct(ins_nm_p)
            self.company_asset_turnover_dupont = _fmt(ins_au)
            self.company_asset_turnover_prev   = _fmt(ins_au_prev)
            self.company_equity_multiplier_curr = _fmt(ins_eq_mult)
            self.company_equity_multiplier_prev = _fmt(ins_eq_mult_p)
            self.company_roe_dupont = _pct(ins_prof.get("roe"))
            self.company_roe_prev   = _pct(ins_prev_prof.get("roe"))

        elif sector == "Finance":
            fin_result = compute_finance_ratios(data)
            self.company_ratios = fin_result
            fin_curr = fin_result.get("current", {})
            fin_prof = fin_curr.get("profitability", {})
            fin_eff  = fin_curr.get("efficiency", {})
            fin_lev  = fin_curr.get("leverage", {})
            fin_liq  = fin_curr.get("liquidity", {})
            fin_aq   = fin_curr.get("asset_quality", {})
            self.company_composite = compute_finance_composite_score(fin_result)
            # Populate Finance flat vars
            self.company_fin_nim = _pct(fin_prof.get("nim"))
            self.company_fin_yield_on_earning_assets = _pct(fin_prof.get("yield_on_earning_assets"))
            self.company_fin_cost_of_funds = _pct(fin_prof.get("cost_of_funds"))
            self.company_fin_interest_spread = _pct(fin_prof.get("interest_spread"))
            self.company_fin_roa = _pct(fin_prof.get("roa"))
            self.company_fin_roe = _pct(fin_prof.get("roe"))
            self.company_fin_net_margin = _pct(fin_prof.get("net_margin"))
            self.company_fin_cost_to_income = _pct(fin_eff.get("cost_to_income"))
            self.company_fin_operating_expense_ratio = _pct(fin_eff.get("operating_expense_ratio"))
            self.company_fin_non_interest_income_ratio = _pct(fin_eff.get("non_interest_income_ratio"))
            self.company_fin_asset_utilisation = _pct(fin_eff.get("asset_utilisation"))
            self.company_fin_debt_to_equity = _fmt(fin_lev.get("debt_to_equity"))
            self.company_fin_debt_to_assets = _pct(fin_lev.get("debt_to_assets"))
            self.company_fin_equity_ratio = _pct(fin_lev.get("equity_ratio"))
            self.company_fin_equity_multiplier = _fmt(fin_lev.get("equity_multiplier"))
            self.company_fin_cash_ratio = _pct(fin_liq.get("cash_ratio"))
            self.company_fin_ocf_ratio = _fmt(fin_liq.get("ocf_ratio"))
            self.company_fin_loan_to_assets = _pct(fin_liq.get("loan_to_assets"))
            self.company_fin_npa_ratio = _pct(fin_aq.get("npa_ratio"))
            self.company_fin_receivables_to_assets = _pct(fin_aq.get("receivables_to_assets"))
            self.company_fin_provision_coverage = _fmt(fin_aq.get("provision_coverage"))
            # Standard display vars using Finance proxies
            self.company_roa = _pct(fin_prof.get("roa"))
            self.company_roe = _pct(fin_prof.get("roe"))
            self.company_net_margin = _pct(fin_prof.get("net_margin"))
            self.company_current_ratio = "N/A"
            self.company_quick_ratio = "N/A"
            self.company_debt_equity = _fmt(fin_lev.get("debt_to_equity"))
            self.company_interest_cov = "N/A"
            self.company_asset_turnover = "N/A"
            self.company_z_score = "N/A"
            _ff = compute_finance_forensic(fin_result)
            self.company_sector_forensic_criteria = _ff["criteria"]
            self.company_sector_forensic_score_display = f"{_ff['score']} / {_ff['max_score']}"
            self.company_sector_forensic_chart_data = _ff["chart_data"]
            # Finance/NBFI DuPont: ROE = Net Margin × Asset Utilization × Equity Multiplier
            # Exact identity: (NI/TotalIncome) × (TotalIncome/Assets) × (Assets/Equity) = NI/Equity
            # Applies to all Finance subsectors (ББСБ lenders, securities firms, holding companies)
            fin_prev      = fin_result.get("prev", {})
            fin_prev_prof = fin_prev.get("profitability", {})
            fin_prev_eff  = fin_prev.get("efficiency", {})
            fin_prev_lev  = fin_prev.get("leverage", {})
            self.company_finance_subsector    = _detect_finance_subsector(
                fin_result.get("company", "")
            )
            self.company_dupont_factor1_label = "Net Margin"
            self.company_dupont_factor1_unit  = "%"
            self.company_dupont_factor2_label = "Asset Utilization"
            self.company_dupont_factor2_unit  = "times"
            self.company_dupont_show_factor2  = True
            self.company_dupont_formula_text  = "ROE = Net Margin × Asset Utilization × Equity Multiplier"
            self.company_net_margin_dupont    = _pct(fin_prof.get("net_margin"))
            self.company_net_margin_prev      = _pct(fin_prev_prof.get("net_margin"))
            self.company_asset_turnover_dupont = _fmt(fin_eff.get("asset_utilisation"))
            self.company_asset_turnover_prev   = _fmt(fin_prev_eff.get("asset_utilisation"))
            self.company_equity_multiplier_curr = _fmt(fin_lev.get("equity_multiplier"))
            self.company_equity_multiplier_prev = _fmt(fin_prev_lev.get("equity_multiplier"))
            self.company_roe_dupont = _pct(fin_prof.get("roe"))
            self.company_roe_prev   = _pct(fin_prev_prof.get("roe"))

        else:
            # Standard sector
            self.company_ratios = compute_ratios(data)
            self.company_composite = compute_composite_score(
                self.company_ratios, self.company_piotroski, self.company_beneish
            )
            self.company_sector_forensic_criteria = []
            self.company_sector_forensic_score_display = ""
            self.company_sector_forensic_chart_data = []
            curr = self.company_ratios.get("current", {})
            prof = curr.get("profitability", {})
            liq  = curr.get("liquidity", {})
            solv = curr.get("solvency", {})
            act  = curr.get("activity", {})
            zs   = curr.get("z_score", {})
            perf = curr.get("performance", {})

            self.company_roa          = _pct(prof.get("roa"))
            self.company_roe          = _pct(prof.get("roe"))
            self.company_net_margin   = _pct(prof.get("net_margin"))
            self.company_current_ratio = _fmt(liq.get("current_ratio"))
            self.company_quick_ratio  = _fmt(liq.get("quick_ratio"))
            self.company_debt_equity  = _fmt(solv.get("debt_to_equity"))
            self.company_interest_cov = _fmt(solv.get("interest_coverage"))
            self.company_asset_turnover = _fmt(act.get("total_asset_turnover"))
            self.company_z_score      = _fmt(zs.get("z_score"))

            # Additional standard ratio vars
            self.company_gross_margin = _pct(prof.get("gross_margin"))
            self.company_operating_margin = _pct(prof.get("operating_margin"))
            self.company_ebit_margin = _pct(prof.get("ebit_margin"))
            self.company_cash_ratio = _fmt(liq.get("cash_ratio"))
            wc = liq.get("working_capital")
            self.company_working_capital = _fmt(wc)
            self.company_debt_to_assets = _fmt(solv.get("debt_to_assets"))
            self.company_equity_ratio = _fmt(solv.get("equity_ratio"))
            self.company_ocf_ratio = _fmt(perf.get("ocf_ratio"))
            self.company_cf_to_debt = _fmt(perf.get("cf_to_debt"))
            self.company_reinvestment_ratio = _fmt(perf.get("reinvestment_ratio"))
            self.company_fixed_asset_turnover = _fmt(act.get("fixed_asset_turnover"))
            self.company_inventory_turnover = _fmt(act.get("inventory_turnover"))
            self.company_days_inventory = _fmt(act.get("days_inventory"))
            self.company_receivables_turnover = _fmt(act.get("receivables_turnover"))
            self.company_days_sales_outstanding = _fmt(act.get("days_sales_outstanding"))
            self.company_payables_turnover = _fmt(act.get("payables_turnover"))
            self.company_days_payable_outstanding = _fmt(act.get("days_payable_outstanding"))
            self.company_cash_conversion_cycle = _fmt(act.get("cash_conversion_cycle"))
            self.company_z_x1 = _fmt(zs.get("x1_wc_ta"))
            self.company_z_x2 = _fmt(zs.get("x2_re_ta"))
            self.company_z_x3 = _fmt(zs.get("x3_ebit_ta"))
            self.company_z_x4 = _fmt(zs.get("x4_eq_tl"))
            self.company_z_x5 = _fmt(zs.get("x5_rev_ta"))

            # DuPont vars — standard 3-factor
            self.company_dupont_factor1_label = "Net Margin"
            self.company_dupont_factor1_unit  = "%"
            self.company_dupont_factor2_label = "Asset Turnover"
            self.company_dupont_factor2_unit  = "times"
            self.company_dupont_show_factor2  = True
            self.company_dupont_formula_text  = "ROE = Net Profit Margin × Asset Turnover × Equity Multiplier"
            prev_data = self.company_ratios.get("prev", {})
            prev_prof = prev_data.get("profitability", {})
            prev_act  = prev_data.get("activity", {})
            prev_solv = prev_data.get("solvency", {})

            self.company_net_margin_dupont = _pct(prof.get("net_margin"))
            self.company_net_margin_prev   = _pct(prev_prof.get("net_margin"))
            self.company_asset_turnover_dupont = _fmt(act.get("total_asset_turnover"))
            self.company_asset_turnover_prev   = _fmt(prev_act.get("total_asset_turnover"))

            d2e = solv.get("debt_to_equity")
            self.company_equity_multiplier_curr = _fmt(1 + d2e if d2e is not None else None)
            d2e_prev = prev_solv.get("debt_to_equity")
            self.company_equity_multiplier_prev = _fmt(1 + d2e_prev if d2e_prev is not None else None)

            self.company_roe_dupont = _pct(prof.get("roe"))
            self.company_roe_prev   = _pct(prev_prof.get("roe"))

        # --- Populate flat display vars (common to all sectors) ---
        comp  = self.company_composite
        piots = self.company_piotroski
        ben   = self.company_beneish

        self.company_score        = comp.get("score", 0)
        self.company_health_label = comp.get("label", "")
        self.company_health_color = comp.get("color", "")

        if sector in ("Banking", "Insurance", "Finance"):
            self.company_f_score_display = "N/A"
            self.company_m_score_display = "N/A"
            self.company_m_interp = "Not applicable"
        else:
            fs = piots.get("f_score")
            ms = piots.get("max_score")
            self.company_f_score_display = f"{fs} / {ms}" if fs is not None else "N/A"
            mv = ben.get("m_score")
            self.company_m_score_display = f"{mv:.2f}" if mv is not None else "N/A"
            self.company_m_interp = ben.get("interpretation", "")

        if sector in ("Banking", "Insurance", "Finance"):
            self.company_f1 = -1
            self.company_f2 = -1
            self.company_f3 = -1
            self.company_f4 = -1
            self.company_f5 = -1
            self.company_f6 = -1
            self.company_f8 = -1
            self.company_f9 = -1
            self.company_dsri = "N/A"
            self.company_gmi  = "N/A"
            self.company_aqi  = "N/A"
            self.company_sgi  = "N/A"
            self.company_sgai = "N/A"
            self.company_lvgi = "N/A"
            self.company_tata = "N/A"
        else:
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

        # --- Chart data vars ---
        score = self.company_score
        fill = "#22c55e" if score >= 70 else ("#f59e0b" if score >= 40 else "#ef4444")
        self.company_gauge_data = [{"name": "score", "value": score, "fill": fill}]

        breakdown = self.company_composite.get("breakdown", {})
        _sector = self.company_sector
        if _sector == "Banking":
            self.company_radar_data = [
                {"category": "Capital",       "score": breakdown.get("capital") or 0},
                {"category": "Asset Quality", "score": breakdown.get("asset_quality") or 0},
                {"category": "Earnings",      "score": breakdown.get("earnings") or 0},
                {"category": "Liquidity",     "score": breakdown.get("liquidity") or 0},
                {"category": "Efficiency",    "score": breakdown.get("efficiency") or 0},
            ]
        elif _sector == "Insurance":
            self.company_radar_data = [
                {"category": "Underwriting",  "score": breakdown.get("underwriting") or 0},
                {"category": "Solvency",      "score": breakdown.get("solvency") or 0},
                {"category": "Profitability", "score": breakdown.get("profitability") or 0},
                {"category": "Liquidity",     "score": breakdown.get("liquidity") or 0},
            ]
        elif _sector == "Finance":
            self.company_radar_data = [
                {"category": "Profitability", "score": breakdown.get("profitability") or 0},
                {"category": "Capital",       "score": breakdown.get("capital") or 0},
                {"category": "Efficiency",    "score": breakdown.get("efficiency") or 0},
                {"category": "Liquidity",     "score": breakdown.get("liquidity") or 0},
            ]
        else:
            self.company_radar_data = [
                {"category": "Profitability", "score": breakdown.get("profitability") or 0},
                {"category": "Liquidity",     "score": breakdown.get("liquidity") or 0},
                {"category": "Solvency",      "score": breakdown.get("solvency") or 0},
                {"category": "Activity",      "score": breakdown.get("activity") or 0},
                {"category": "Altman Z",      "score": breakdown.get("altman") or 0},
                {"category": "Piotroski",     "score": breakdown.get("piotroski") or 0},
            ]

        if sector in ("Banking", "Insurance", "Finance"):
            self.company_beneish_chart_data = []
        else:
            beneish_idx = self.company_beneish.get("indices", {})
            self.company_beneish_chart_data = [
                {"index": k.upper(), "value": round(v, 3) if v is not None else 0,
                 "fill": "#ef4444" if (v is not None and v > 1.0) else "#60a5fa"}
                for k, v in beneish_idx.items() if k != "depi"
            ]

        # --- Red flags: seed with rule-based instantly ---
        self.company_red_flags = _compute_red_flags(self.company_ratios, self.company_beneish)

        # --- Valuation data ---
        self._load_valuation_data(company_name)

        # --- Flush UI so company page renders, then run AI red flags ---
        yield
        self.company_red_flags_loading = True
        yield

        price_records: list = []
        price_file = PRICES_DIR / price_filename(company_name)
        if price_file.exists():
            with open(price_file, encoding="utf-8") as f:
                price_data = json.load(f)
            price_records = price_data.get("records", [])

        dupont_vars = {
            "formula": self.company_dupont_formula_text,
            "factor1_label": self.company_dupont_factor1_label,
            "factor1_curr": self.company_net_margin_dupont,
            "factor1_prev": self.company_net_margin_prev,
            "factor2_label": self.company_dupont_factor2_label,
            "factor2_curr": self.company_asset_turnover_dupont,
            "factor2_prev": self.company_asset_turnover_prev,
            "equity_multiplier_curr": self.company_equity_multiplier_curr,
            "equity_multiplier_prev": self.company_equity_multiplier_prev,
            "roe_curr": self.company_roe_dupont,
            "roe_prev": self.company_roe_prev,
        }
        valuation_vars = {
            "pe": self.company_pe,
            "pbv": self.company_pbv,
            "ev_ebitda": self.company_ev_ebitda,
            "fcf_yield": self.company_fcf_yield,
            "ptbv": self.company_ptbv,
            "p_ppop": self.company_p_ppop,
            "p_nii": self.company_p_nii,
            "p_npe": self.company_p_npe,
            "p_uwp": self.company_p_uwp,
            "p_inv_sec": self.company_p_inv_sec,
            "p_revenue": self.company_p_revenue,
        }

        flags = await compute_red_flags_ai(
            company_name=company_name,
            sector=self.company_sector,
            company_ratios=self.company_ratios,
            company_beneish=self.company_beneish,
            forensic_criteria=self.company_sector_forensic_criteria,
            forensic_score_display=self.company_sector_forensic_score_display,
            dupont_vars=dupont_vars,
            valuation_vars=valuation_vars,
            price_records=price_records,
        )
        self.company_red_flags = flags
        self.company_red_flags_loading = False

    def _load_valuation_data(self, company_name: str):
        """Load price JSON, compute valuation ratios, and slice chart data by range."""
        price_file = PRICES_DIR / price_filename(company_name)
        if not price_file.exists():
            self.company_ev_ebitda = "N/A"
            self.company_fcf_yield = "N/A"
            self.company_pe = "N/A"
            self.company_pbv = "N/A"
            self.company_ptbv = "N/A"
            self.company_p_ppop = "N/A"
            self.company_p_nii = "N/A"
            self.company_p_npe     = "N/A"
            self.company_p_uwp     = "N/A"
            self.company_p_inv_sec = "N/A"
            self.company_p_revenue = "N/A"
            self.company_shares_outstanding = ""
            self.company_price_chart_data = []
            self.company_volume_chart_data = []
            return

        with open(price_file, encoding="utf-8") as f:
            price_data = json.load(f)

        records = price_data.get("records", [])

        # Determine shares outstanding: scraped value from price JSON
        scraped_shares = price_data.get("shares_outstanding")

        # Load financial data once: used for both shares override and valuation computation
        fin_data_for_valuation: dict = {}
        manual_shares = None
        index_path = DATA_DIR / "index.json"
        if index_path.exists():
            with open(index_path) as f:
                index = json.load(f)
            entry = next(
                (e for e in index.get("files", []) if e["company"] == company_name),
                None,
            )
            if entry:
                fin_file = DATA_DIR / entry["filename"]
                if fin_file.exists():
                    with open(fin_file, encoding="utf-8") as f:
                        fin_data_for_valuation = json.load(f)
                    manual_shares = fin_data_for_valuation.get("shares_outstanding_override")

        # Manual override takes precedence over scraped value
        effective_shares = manual_shares if manual_shares is not None else scraped_shares

        self.company_shares_outstanding = str(effective_shares) if effective_shares is not None else ""

        # Get last close price from most recent record
        last_close_price = None
        if records:
            last_record = records[-1]
            try:
                last_close_price = float(last_record["close"])
            except (ValueError, KeyError):
                last_close_price = None

        # Apply reporting unit multiplier so financial figures (often in thousands of MNT)
        # are scaled to raw MNT before being compared with market cap.
        unit_mult = fin_data_for_valuation.get("metadata", {}).get("reporting_unit_multiplier")
        if unit_mult is None:
            # Legacy files pre-date unit detection: infer from MCap/Assets ratio.
            # If ratio > 20, the assets figure is almost certainly in thousands.
            bs_leg = (fin_data_for_valuation.get("balance_sheet")
                      or fin_data_for_valuation.get("bank_balance_sheet")
                      or fin_data_for_valuation.get("insurance_balance_sheet")
                      or {})
            total_assets = bs_leg.get("total_assets")
            if (effective_shares and last_close_price and total_assets and total_assets > 0
                    and (effective_shares * last_close_price) / total_assets > 20):
                unit_mult = 1_000
            else:
                unit_mult = 1

        result = compute_valuation_metrics(fin_data_for_valuation, effective_shares, last_close_price, unit_mult)

        # Format results for display
        self.company_valuation_sector = result["sector"]
        self.company_ev_ebitda = _fmt(result["ev_ebitda"], 1)
        fcf = result["fcf_yield"]
        self.company_fcf_yield = _fmt(fcf * 100 if fcf is not None else None, 1)
        self.company_pe = _fmt(result["pe"], 1)
        self.company_pbv = _fmt(result["pbv"], 1)
        # Bank / NBFI
        self.company_ptbv   = _fmt(result["ptbv"],   1)
        self.company_p_ppop = _fmt(result["p_ppop"], 1)
        self.company_p_nii  = _fmt(result["p_nii"],  1)
        # Insurance
        self.company_p_npe  = _fmt(result["p_npe"],  1)
        self.company_p_uwp  = _fmt(result["p_uwp"],  1)
        # Holding
        self.company_p_inv_sec = _fmt(result["p_inv_sec"], 1)
        # Securities
        self.company_p_revenue = _fmt(result["p_revenue"], 1)

        # Slice price records by selected range
        self._slice_price_records(records)

    def _slice_price_records(self, records: list[dict]):
        """Filter records by valuation_range and populate chart data state vars."""
        range_days = {
            "1M": 30,
            "6M": 180,
            "1Y": 365,
        }
        cutoff_str: str | None = None
        if self.valuation_range in range_days:
            cutoff_date = datetime.now() - timedelta(days=range_days[self.valuation_range])
            cutoff_str = cutoff_date.strftime("%Y-%m-%d")

        if cutoff_str:
            filtered = [r for r in records if r.get("date", "") >= cutoff_str]
        else:
            # "All" range — no cutoff
            filtered = records

        self.company_price_chart_data = [
            {"date": r["date"], "close": r["close"]} for r in filtered
        ]
        self.company_volume_chart_data = [
            {"date": r["date"], "volume": int(r["volume"]) if r.get("volume") is not None else 0}
            for r in filtered
        ]

    @rx.event
    def set_valuation_range(self, range_value: str):
        """Set the price chart range and re-slice the chart data."""
        self.valuation_range = range_value
        # Re-read price JSON and re-slice
        company_name = self.selected_company_name
        if not company_name:
            return
        price_file = PRICES_DIR / price_filename(company_name)
        if not price_file.exists():
            self.company_price_chart_data = []
            self.company_volume_chart_data = []
            return
        with open(price_file, encoding="utf-8") as f:
            price_data = json.load(f)
        records = price_data.get("records", [])
        self._slice_price_records(records)

    @rx.event
    def toggle_shares_input(self):
        """Toggle the manual shares outstanding input form."""
        self.company_shares_input_open = not self.company_shares_input_open
        if self.company_shares_input_open:
            self.company_shares_input_value = ""

    @rx.event
    def set_shares_input_value(self, value: str):
        """Update the shares input field value."""
        self.company_shares_input_value = value

    @rx.event
    def save_shares_outstanding(self, value: str):
        """Save a manually entered shares outstanding to the company's financial JSON.

        Parses the input (strips commas and spaces), writes as
        shares_outstanding_override to the financial JSON, then recomputes
        valuation metrics and closes the input form.
        """
        company_name = self.selected_company_name
        if not company_name:
            return

        # Normalize input: remove commas, spaces; parse to int
        normalized = value.strip().replace(",", "").replace(" ", "")
        try:
            shares_int = int(normalized)
        except ValueError:
            return  # Invalid input — silently ignore

        # Write override to the company's financial JSON
        index_path = DATA_DIR / "index.json"
        if not index_path.exists():
            return
        with open(index_path) as f:
            index = json.load(f)
        entry = next(
            (e for e in index.get("files", []) if e["company"] == company_name),
            None,
        )
        if not entry:
            return
        fin_file = DATA_DIR / entry["filename"]
        if fin_file.exists():
            with open(fin_file, encoding="utf-8") as f:
                fin_data = json.load(f)
        else:
            fin_data = {}

        fin_data["shares_outstanding_override"] = shares_int

        with open(fin_file, "w", encoding="utf-8") as f:
            json.dump(fin_data, f, ensure_ascii=False, indent=2)

        # Recompute valuation metrics with new shares
        self._load_valuation_data(company_name)
        self.company_shares_input_open = False

    @rx.event
    def on_load_company(self):
        """Called on page load -- reads company name from URL params."""
        company = self.router.page.params.get("company", "")
        if company:
            return AnalysisState.load_company(company)

    @rx.event
    def set_screener_filter(self, value: str):
        self.screener_filter = value

    @rx.event
    def sort_screener(self, col: str):
        if self.screener_sort_col == col:
            self.screener_sort_asc = not self.screener_sort_asc
        else:
            self.screener_sort_col = col
            self.screener_sort_asc = True

    @rx.var
    def filtered_companies(self) -> list[dict]:
        companies = self.all_companies if self.screener_filter == "All" \
            else [c for c in self.all_companies if c.get("sector") == self.screener_filter]
        col = self.screener_sort_col
        reverse = not self.screener_sort_asc
        str_cols = {"company", "sector", "label", "color"}
        try:
            if col in str_cols:
                return sorted(companies, key=lambda c: (c.get(col) or "").lower(), reverse=reverse)
            return sorted(companies, key=lambda c: (c.get(col) or 0), reverse=reverse)
        except Exception:
            return companies


class PortfolioState(AnalysisState):
    """State for portfolio management."""

    # List of { company, filename, weight, weight_pct, weight_str, score, score_str, label, color, sector }
    holdings: list[dict] = []

    # --- Phase 4: Portfolio Optimization vars ---
    active_portfolio_tab: str = "holdings"

    # Sector donut chart data (per D-20)
    sector_chart_data: list[dict[str, str]] = []

    # Efficient frontier scatter data (per D-15)
    frontier_data: list[dict[str, str]] = []

    # Current portfolio point on frontier (per D-18)
    current_point_data: list[dict[str, str]] = []

    # Optimization table rows (per D-09)
    optimization_data: list[dict[str, str]] = []

    # Risk metric display strings (per D-13, D-14)
    sortino_str: str = "N/A"
    max_drawdown_str: str = "N/A"
    cvar_str: str = "N/A"

    # Whether analysis can be shown (per D-04)
    can_show_analysis: bool = False

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
            {**h, "weight": new_weight, "weight_str": weight_str, "weight_pct": f"{new_weight * 100:.1f}"}  # score_str preserved via **h
            for h in self.holdings
        ]
        holdings.append({
            "company":    entry["company"],
            "filename":   entry["filename"],
            "url":        entry.get("url", f"/company/{entry['company']}"),
            "weight":     new_weight,
            "weight_str": f"{new_weight * 100:.1f}%",
            "weight_pct": f"{new_weight * 100:.1f}",
            "score":      entry["score"],
            "score_str":  str(entry["score"]),
            "label":      entry["label"],
            "color":      entry["color"],
            "sector":     entry.get("sector", "Standard"),
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
            holdings = [{**h, "weight": new_weight, "weight_str": weight_str, "weight_pct": f"{new_weight * 100:.1f}"} for h in holdings]
        self.holdings = holdings

    @rx.event
    def on_tab_change(self, tab: str):
        """Handle portfolio tab change; trigger analysis when switching to analysis tab."""
        self.active_portfolio_tab = tab
        if tab == "analysis" and len(self.holdings) >= 2:
            self._run_portfolio_analysis()

    @rx.event
    def set_holding_weight(self, company: str, new_value: str):
        """Update a holding's weight and rebalance all others proportionally."""
        from .analysis.portfolio_optimization import rebalance_weights, compute_sector_breakdown
        self.holdings = rebalance_weights(self.holdings, company, new_value)
        self.sector_chart_data = compute_sector_breakdown(self.holdings)

    @rx.event
    def apply_optimal_weights(self):
        """Apply mean-variance optimal weights to all holdings."""
        if not self.optimization_data:
            return
        opt_map = {row["company"]: row["optimal"] for row in self.optimization_data}
        from .analysis.portfolio_optimization import rebalance_weights, compute_sector_breakdown
        holdings = list(self.holdings)
        for h in holdings:
            opt_pct = float(opt_map.get(h["company"], h.get("weight_pct", "0")))
            w = round(opt_pct / 100, 4)
            h["weight"] = w
            h["weight_pct"] = str(round(opt_pct, 1))
            h["weight_str"] = f"{opt_pct:.1f}%"
        self.holdings = holdings
        self.sector_chart_data = compute_sector_breakdown(self.holdings)
        self._run_portfolio_analysis()

    def _run_portfolio_analysis(self):
        """Internal: compute optimization, risk metrics, frontier, and sector breakdown."""
        from .analysis.portfolio_optimization import (
            load_price_returns, align_returns, compute_portfolio_returns,
            compute_risk_metrics, mean_variance_optimize, sample_frontier,
            compute_sector_breakdown,
        )
        import numpy as np

        company_names = [h["company"] for h in self.holdings]
        returns_map = load_price_returns(company_names)

        # Guard: need >= 2 companies with price data (per D-04)
        if len(returns_map) < 2:
            self.can_show_analysis = False
            self.sortino_str = "N/A"
            self.max_drawdown_str = "N/A"
            self.cvar_str = "N/A"
            self.frontier_data = []
            self.current_point_data = []
            self.optimization_data = []
            return

        self.can_show_analysis = True
        names, matrix = align_returns(returns_map)

        # Current weights for companies with price data, normalized
        weights_dict = {h["company"]: float(h["weight"]) for h in self.holdings}
        current_weights = np.array([weights_dict.get(n, 0.0) for n in names])
        total = current_weights.sum()
        if total > 0:
            current_weights = current_weights / total

        # Risk metrics (PORT-05, D-12)
        port_returns = compute_portfolio_returns(current_weights, matrix)
        metrics = compute_risk_metrics(port_returns)
        self.sortino_str = f"{metrics['sortino']:.2f}" if metrics["sortino"] is not None else "N/A"
        self.max_drawdown_str = f"{metrics['max_drawdown'] * 100:.1f}%" if metrics["max_drawdown"] is not None else "N/A"
        self.cvar_str = f"{metrics['cvar_95'] * 100:.2f}%" if metrics["cvar_95"] is not None else "N/A"

        # Optimization (PORT-04, D-09)
        opt = mean_variance_optimize(matrix, names)
        opt_weights = opt["weights"]
        self.optimization_data = [
            {
                "company": n,
                "current": str(round(weights_dict.get(n, 0.0) * 100, 1)),
                "optimal": str(opt_weights.get(n, 0.0)),
                "arrow": "\u2191" if opt_weights.get(n, 0.0) > weights_dict.get(n, 0.0) * 100 else "\u2193",
            }
            for n in names
        ]

        # Frontier (PORT-06, D-15)
        self.frontier_data = sample_frontier(matrix, n_samples=200)

        # Current portfolio point (D-18)
        mean_rets = np.mean(matrix, axis=0) * 252
        cov_mat = np.cov(matrix.T) * 252
        curr_ret = float(np.dot(current_weights, mean_rets) * 100)
        curr_risk = float(np.sqrt(current_weights @ cov_mat @ current_weights) * 100)
        self.current_point_data = [{"risk": str(round(curr_risk, 2)), "return": str(round(curr_ret, 2))}]

        # Sector breakdown (PORT-02, D-20)
        self.sector_chart_data = compute_sector_breakdown(self.holdings)

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

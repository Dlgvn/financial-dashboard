"""Upload state management for MSE Analytica."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import reflex as rx

from .analysis.ratios import (
    compute_beneish,
    compute_composite_score,
    compute_piotroski,
    compute_ratios,
)
from .analysis.bank_ratios import compute_bank_ratios
from .analysis.insurance_ratios import compute_insurance_ratios
from .parser.excel_parser import parse_excel_file
from .analysis.valuation import compute_valuation_metrics
from .scraper.price_scraper import scrape_company_prices, save_price_data, PRICES_DIR, price_filename
from .scraper.registry_loader import find_mse_id
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
    return "Standard"


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
                bank_cap  = bank_curr.get("capital_adequacy", {})
                bank_liq  = bank_curr.get("liquidity", {})
                compat_ratios = {
                    "current": {
                        "profitability": {
                            "roa": bank_prof.get("roa"),
                            "roe": bank_prof.get("roe"),
                            "net_margin": bank_prof.get("net_margin"),
                        },
                        "liquidity": {
                            "current_ratio": bank_liq.get("ldr"),
                            "quick_ratio": None,
                            "cash_ratio": bank_liq.get("cash_to_deposits"),
                        },
                        "solvency": {
                            "debt_to_equity": None,
                            "debt_to_assets": None,
                            "equity_ratio": bank_cap.get("equity_to_assets"),
                            "interest_coverage": None,
                        },
                        "activity": {
                            "total_asset_turnover": None,
                            "days_sales_outstanding": None,
                            "inventory_turnover": None,
                        },
                        "z_score": {"z_score": None},
                    },
                    "prev": {"profitability": {}, "liquidity": {}, "solvency": {}, "activity": {}, "z_score": {}},
                }
                composite = compute_composite_score(compat_ratios, piotroski, beneish)
                roe = bank_prof.get("roe")
            elif sector == "Insurance":
                ins_result = compute_insurance_ratios(data)
                ins_curr = ins_result.get("current", {})
                ins_prof = ins_curr.get("profitability", {})
                ins_solv = ins_curr.get("solvency", {})
                ins_liq  = ins_curr.get("liquidity", {})
                compat_ratios = {
                    "current": {
                        "profitability": {
                            "roa": ins_prof.get("roa"),
                            "roe": ins_prof.get("roe"),
                            "net_margin": ins_prof.get("net_margin"),
                        },
                        "liquidity": {
                            "current_ratio": None,
                            "quick_ratio": None,
                            "cash_ratio": ins_liq.get("cash_to_liabilities"),
                        },
                        "solvency": {
                            "debt_to_equity": ins_solv.get("leverage_ratio"),
                            "debt_to_assets": None,
                            "equity_ratio": ins_solv.get("solvency_ratio"),
                            "interest_coverage": None,
                        },
                        "activity": {
                            "total_asset_turnover": None,
                            "days_sales_outstanding": None,
                            "inventory_turnover": None,
                        },
                        "z_score": {"z_score": None},
                    },
                    "prev": {"profitability": {}, "liquidity": {}, "solvency": {}, "activity": {}, "z_score": {}},
                }
                composite = compute_composite_score(compat_ratios, piotroski, beneish)
                roe = ins_prof.get("roe")
            else:
                ratios    = compute_ratios(data)
                composite = compute_composite_score(ratios, piotroski, beneish)
                roe = ratios["current"].get("profitability", {}).get("roe")

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
                "f_score":     int(f_score) if f_score is not None else 0,
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

    # Sector identity
    company_sector: str = ""
    company_is_bank: bool = False
    company_is_insurance: bool = False

    # Chart data vars (must be list[dict] for rx.recharts)
    company_gauge_data: list[dict] = []
    company_radar_data: list[dict] = []
    company_beneish_chart_data: list[dict] = []

    # DuPont vars (current and prior year)
    company_net_margin_dupont: str = ""
    company_net_margin_prev: str = ""
    company_asset_turnover_dupont: str = ""
    company_asset_turnover_prev: str = ""
    company_equity_multiplier_curr: str = ""
    company_equity_multiplier_prev: str = ""
    company_roe_dupont: str = ""
    company_roe_prev: str = ""

    # Red flags
    company_red_flags: list[dict] = []

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

    # Bank ratio flat vars (19)
    company_bank_nim: str = ""
    company_bank_car: str = ""
    company_bank_npl_ratio: str = ""
    company_bank_ldr: str = ""
    company_bank_cost_to_income: str = ""
    company_bank_roa: str = ""
    company_bank_roe: str = ""
    company_bank_net_margin: str = ""
    company_bank_interest_income_ratio: str = ""
    company_bank_tier1_ratio: str = ""
    company_bank_equity_multiplier: str = ""
    company_bank_equity_to_assets: str = ""
    company_bank_coverage_ratio: str = ""
    company_bank_loan_loss_reserve_ratio: str = ""
    company_bank_provision_to_loans: str = ""
    company_bank_cash_to_deposits: str = ""
    company_bank_loans_to_assets: str = ""
    company_bank_securities_to_assets: str = ""
    company_bank_fee_income_ratio: str = ""

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
            compat_ratios = {
                "current": {
                    "profitability": {
                        "roa": bank_prof.get("roa"),
                        "roe": bank_prof.get("roe"),
                        "net_margin": bank_prof.get("net_margin"),
                    },
                    "liquidity": {
                        "current_ratio": bank_liq.get("ldr"),  # use LDR as proxy
                        "quick_ratio": None,
                        "cash_ratio": bank_liq.get("cash_to_deposits"),
                    },
                    "solvency": {
                        "debt_to_equity": None,
                        "debt_to_assets": None,
                        "equity_ratio": bank_cap.get("equity_to_assets"),
                        "interest_coverage": None,
                    },
                    "activity": {
                        "total_asset_turnover": None,
                        "days_sales_outstanding": None,
                        "inventory_turnover": None,
                    },
                    "z_score": {"z_score": None},
                },
                "prev": {"profitability": {}, "liquidity": {}, "solvency": {}, "activity": {}, "z_score": {}},
            }
            self.company_composite = compute_composite_score(
                compat_ratios, self.company_piotroski, self.company_beneish
            )
            # Populate bank flat vars
            bank_aq = bank_curr.get("asset_quality", {})
            bank_eff = bank_curr.get("efficiency", {})
            self.company_bank_nim = _fmt(bank_prof.get("nim"))
            self.company_bank_car = _fmt(bank_cap.get("car"))
            self.company_bank_npl_ratio = _fmt(bank_aq.get("npl_ratio"))
            self.company_bank_ldr = _fmt(bank_liq.get("ldr"))
            self.company_bank_cost_to_income = _fmt(bank_eff.get("cost_to_income"))
            self.company_bank_roa = _fmt(bank_prof.get("roa"))
            self.company_bank_roe = _fmt(bank_prof.get("roe"))
            self.company_bank_net_margin = _fmt(bank_prof.get("net_margin"))
            self.company_bank_interest_income_ratio = _fmt(bank_prof.get("interest_income_ratio"))
            self.company_bank_tier1_ratio = _fmt(bank_cap.get("tier1_ratio"))
            self.company_bank_equity_multiplier = _fmt(bank_cap.get("equity_multiplier"))
            self.company_bank_equity_to_assets = _fmt(bank_cap.get("equity_to_assets"))
            self.company_bank_coverage_ratio = _fmt(bank_aq.get("coverage_ratio"))
            self.company_bank_loan_loss_reserve_ratio = _fmt(bank_aq.get("loan_loss_reserve_ratio"))
            self.company_bank_provision_to_loans = _fmt(bank_aq.get("provision_to_loans"))
            self.company_bank_cash_to_deposits = _fmt(bank_liq.get("cash_to_deposits"))
            self.company_bank_loans_to_assets = _fmt(bank_liq.get("loans_to_assets"))
            self.company_bank_securities_to_assets = _fmt(bank_liq.get("securities_to_assets"))
            self.company_bank_fee_income_ratio = _fmt(bank_eff.get("fee_income_ratio"))
            # Standard display vars using bank proxies
            self.company_roa = _fmt(bank_prof.get("roa"))
            self.company_roe = _fmt(bank_prof.get("roe"))
            self.company_net_margin = _fmt(bank_prof.get("net_margin"))
            self.company_current_ratio = _fmt(bank_liq.get("ldr"))
            self.company_quick_ratio = "N/A"
            self.company_debt_equity = "N/A"
            self.company_interest_cov = "N/A"
            self.company_asset_turnover = "N/A"
            self.company_z_score = "N/A"

        elif sector == "Insurance":
            ins_result = compute_insurance_ratios(data)
            self.company_ratios = ins_result
            ins_curr = ins_result.get("current", {})
            ins_prof = ins_curr.get("profitability", {})
            ins_solv = ins_curr.get("solvency", {})
            ins_liq = ins_curr.get("liquidity", {})
            ins_uw = ins_curr.get("underwriting", {})
            compat_ratios = {
                "current": {
                    "profitability": {
                        "roa": ins_prof.get("roa"),
                        "roe": ins_prof.get("roe"),
                        "net_margin": ins_prof.get("net_margin"),
                    },
                    "liquidity": {
                        "current_ratio": None,
                        "quick_ratio": None,
                        "cash_ratio": ins_liq.get("cash_to_liabilities"),
                    },
                    "solvency": {
                        "debt_to_equity": ins_solv.get("leverage_ratio"),
                        "debt_to_assets": None,
                        "equity_ratio": ins_solv.get("solvency_ratio"),
                        "interest_coverage": None,
                    },
                    "activity": {
                        "total_asset_turnover": None,
                        "days_sales_outstanding": None,
                        "inventory_turnover": None,
                    },
                    "z_score": {"z_score": None},
                },
                "prev": {"profitability": {}, "liquidity": {}, "solvency": {}, "activity": {}, "z_score": {}},
            }
            self.company_composite = compute_composite_score(
                compat_ratios, self.company_piotroski, self.company_beneish
            )
            # Populate insurance flat vars
            self.company_ins_loss_ratio = _fmt(ins_uw.get("loss_ratio"))
            self.company_ins_expense_ratio = _fmt(ins_uw.get("expense_ratio"))
            self.company_ins_combined_ratio = _fmt(ins_uw.get("combined_ratio"))
            self.company_ins_roa = _fmt(ins_prof.get("roa"))
            self.company_ins_roe = _fmt(ins_prof.get("roe"))
            self.company_ins_net_margin = _fmt(ins_prof.get("net_margin"))
            self.company_ins_investment_income_ratio = _fmt(ins_prof.get("investment_income_ratio"))
            self.company_ins_underwriting_margin = _fmt(ins_prof.get("underwriting_margin"))
            self.company_ins_solvency_ratio = _fmt(ins_solv.get("solvency_ratio"))
            self.company_ins_leverage_ratio = _fmt(ins_solv.get("leverage_ratio"))
            self.company_ins_equity_to_liabilities = _fmt(ins_solv.get("equity_to_liabilities"))
            self.company_ins_reserve_coverage = _fmt(ins_solv.get("reserve_coverage"))
            self.company_ins_ocf_ratio = _fmt(ins_liq.get("ocf_ratio"))
            self.company_ins_investment_ratio = _fmt(ins_liq.get("investment_ratio"))
            self.company_ins_cash_to_liabilities = _fmt(ins_liq.get("cash_to_liabilities"))
            # Standard display vars using insurance proxies
            self.company_roa = _fmt(ins_prof.get("roa"))
            self.company_roe = _fmt(ins_prof.get("roe"))
            self.company_net_margin = _fmt(ins_prof.get("net_margin"))
            self.company_current_ratio = "N/A"
            self.company_quick_ratio = "N/A"
            self.company_debt_equity = _fmt(ins_solv.get("leverage_ratio"))
            self.company_interest_cov = "N/A"
            self.company_asset_turnover = "N/A"
            self.company_z_score = "N/A"

        else:
            # Standard sector
            self.company_ratios = compute_ratios(data)
            self.company_composite = compute_composite_score(
                self.company_ratios, self.company_piotroski, self.company_beneish
            )
            curr = self.company_ratios.get("current", {})
            prof = curr.get("profitability", {})
            liq  = curr.get("liquidity", {})
            solv = curr.get("solvency", {})
            act  = curr.get("activity", {})
            zs   = curr.get("z_score", {})
            perf = curr.get("performance", {})

            self.company_roa          = _fmt(prof.get("roa"))
            self.company_roe          = _fmt(prof.get("roe"))
            self.company_net_margin   = _fmt(prof.get("net_margin"))
            self.company_current_ratio = _fmt(liq.get("current_ratio"))
            self.company_quick_ratio  = _fmt(liq.get("quick_ratio"))
            self.company_debt_equity  = _fmt(solv.get("debt_to_equity"))
            self.company_interest_cov = _fmt(solv.get("interest_coverage"))
            self.company_asset_turnover = _fmt(act.get("total_asset_turnover"))
            self.company_z_score      = _fmt(zs.get("z_score"))

            # Additional standard ratio vars
            self.company_gross_margin = _fmt(prof.get("gross_margin"))
            self.company_operating_margin = _fmt(prof.get("operating_margin"))
            self.company_ebit_margin = _fmt(prof.get("ebit_margin"))
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

            # DuPont vars
            prev_data = self.company_ratios.get("prev", {})
            prev_prof = prev_data.get("profitability", {})
            prev_act  = prev_data.get("activity", {})
            prev_solv = prev_data.get("solvency", {})

            self.company_net_margin_dupont = _fmt(prof.get("net_margin"))
            self.company_net_margin_prev   = _fmt(prev_prof.get("net_margin"))
            self.company_asset_turnover_dupont = _fmt(act.get("total_asset_turnover"))
            self.company_asset_turnover_prev   = _fmt(prev_act.get("total_asset_turnover"))

            d2e = solv.get("debt_to_equity")
            self.company_equity_multiplier_curr = _fmt(1 + d2e if d2e is not None else None)
            d2e_prev = prev_solv.get("debt_to_equity")
            self.company_equity_multiplier_prev = _fmt(1 + d2e_prev if d2e_prev is not None else None)

            self.company_roe_dupont = _fmt(prof.get("roe"))
            self.company_roe_prev   = _fmt(prev_prof.get("roe"))

        # --- Populate flat display vars (common to all sectors) ---
        comp  = self.company_composite
        piots = self.company_piotroski
        ben   = self.company_beneish

        self.company_score        = comp.get("score", 0)
        self.company_health_label = comp.get("label", "")
        self.company_health_color = comp.get("color", "")

        fs = piots.get("f_score")
        ms = piots.get("max_score")
        self.company_f_score_display = f"{fs} / {ms}" if fs is not None else "N/A"
        mv = ben.get("m_score")
        self.company_m_score_display = f"{mv:.2f}" if mv is not None else "N/A"
        self.company_m_interp = ben.get("interpretation", "")

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
        self.company_radar_data = [
            {"category": "Profitability", "score": breakdown.get("profitability") or 0},
            {"category": "Liquidity",     "score": breakdown.get("liquidity") or 0},
            {"category": "Solvency",      "score": breakdown.get("solvency") or 0},
            {"category": "Activity",      "score": breakdown.get("activity") or 0},
            {"category": "Altman Z",      "score": breakdown.get("altman") or 0},
            {"category": "Piotroski",     "score": breakdown.get("piotroski") or 0},
        ]

        beneish_idx = self.company_beneish.get("indices", {})
        self.company_beneish_chart_data = [
            {"index": k.upper(), "value": round(v, 3) if v is not None else 0,
             "fill": "#ef4444" if (v is not None and v > 1.0) else "#60a5fa"}
            for k, v in beneish_idx.items() if k != "depi"
        ]

        # --- Red flags ---
        self.company_red_flags = _compute_red_flags(self.company_ratios, self.company_beneish)

        # --- Valuation data ---
        self._load_valuation_data(company_name)

    def _load_valuation_data(self, company_name: str):
        """Load price JSON, compute valuation ratios, and slice chart data by range."""
        price_file = PRICES_DIR / price_filename(company_name)
        if not price_file.exists():
            self.company_ev_ebitda = "N/A"
            self.company_fcf_yield = "N/A"
            self.company_pe = "N/A"
            self.company_pbv = "N/A"
            self.company_shares_outstanding = ""
            self.company_price_chart_data = []
            self.company_volume_chart_data = []
            return

        with open(price_file, encoding="utf-8") as f:
            price_data = json.load(f)

        records = price_data.get("records", [])

        # Determine shares outstanding: scraped value from price JSON
        scraped_shares = price_data.get("shares_outstanding")

        # Check for manual override in the company's financial JSON
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
                        fin_data = json.load(f)
                    manual_shares = fin_data.get("shares_outstanding_override")

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

        # Load the company's financial data for valuation computation
        fin_data_for_valuation: dict = {}
        index_path2 = DATA_DIR / "index.json"
        if index_path2.exists():
            with open(index_path2) as f:
                index2 = json.load(f)
            entry2 = next(
                (e for e in index2.get("files", []) if e["company"] == company_name),
                None,
            )
            if entry2:
                fin_file2 = DATA_DIR / entry2["filename"]
                if fin_file2.exists():
                    with open(fin_file2, encoding="utf-8") as f:
                        fin_data_for_valuation = json.load(f)

        result = compute_valuation_metrics(fin_data_for_valuation, effective_shares, last_close_price)

        # Format results for display
        self.company_ev_ebitda = _fmt(result["ev_ebitda"], 1)
        fcf = result["fcf_yield"]
        self.company_fcf_yield = _fmt(fcf * 100 if fcf is not None else None, 1)
        self.company_pe = _fmt(result["pe"], 1)
        self.company_pbv = _fmt(result["pbv"], 1)

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
            {"date": r["date"], "volume": r["volume"]} for r in filtered
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
            self.load_company(company)

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
        try:
            return sorted(companies, key=lambda c: (c.get(col) or 0), reverse=reverse)
        except Exception:
            return companies


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

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

            results.append({
                "filename":  entry["filename"],
                "company":   entry["company"],
                "year":      entry.get("year", ""),
                "sector":    entry.get("sector", ""),
                "score":     composite["score"],
                "label":     composite["label"],
                "color":     composite["color"],
                "z_score":   ratios["current"].get("z_score", {}).get("z_score"),
                "roe":       ratios["current"].get("profitability", {}).get("roe"),
                "f_score":   piotroski["f_score"],
                "m_score":   beneish["m_score"],
            })
        except Exception as e:
            print(f"[_load_all_companies] Skipping {entry.get('filename', '?')}: {e}")
            continue
    return results


class AnalysisState(UploadState):
    """State for company screener and individual company analysis."""

    # Screener
    all_companies: list[dict] = []
    screener_filter: str = "All"     # sector filter value

    # Company detail
    selected_company_name: str = ""
    company_ratios:    dict = {}
    company_piotroski: dict = {}
    company_beneish:   dict = {}
    company_composite: dict = {}

    @rx.event
    def load_screener(self):
        """Load all companies with computed scores for screener page."""
        self.all_companies = _load_all_companies()

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
        holdings = [
            {**h, "weight": new_weight}
            for h in self.holdings
        ]
        holdings.append({
            "company":  entry["company"],
            "filename": entry["filename"],
            "weight":   new_weight,
            "score":    entry["score"],
            "label":    entry["label"],
            "color":    entry["color"],
        })
        self.holdings = holdings

    @rx.event
    def remove_from_portfolio(self, company: str):
        """Remove a company and rebalance weights."""
        holdings = [h for h in self.holdings if h["company"] != company]
        n = len(holdings)
        if n > 0:
            new_weight = round(1 / n, 4)
            holdings = [{**h, "weight": new_weight} for h in holdings]
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

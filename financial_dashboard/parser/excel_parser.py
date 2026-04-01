"""Core Excel parsing logic for MSE financial statements.

Parses .xlsx and .xls files downloaded from members.mse.mn containing
Mongolian-language financial statements and extracts structured data.

Real MSE file layout (confirmed from members.mse.mn):
  - Column A (0): sometimes company info row, otherwise empty
  - Column B (1): row numbers like "1.1.1"
  - Column C (2): Mongolian header text (Үзүүлэлт)
  - Column D (3): Previous year values (Эхний үлдэгдэл)
  - Column E (4): Current year values (Эцсийн үлдэгдэл)

Uses openpyxl for .xlsx files and xlrd for .xls files.
"""

import io
import re
from datetime import datetime

import xlrd
from openpyxl import load_workbook

from .header_mappings import (
    HEADERS_BY_TYPE,
    SHEET_TYPE_PATTERNS,
    match_header,
    normalize_header,
)

# Column indices in MSE financial statement files
HEADER_COL = 2   # Column C: Mongolian header text
PREV_COL = 3     # Column D: Previous year value
CURR_COL = 4     # Column E: Current year value


def parse_excel_file(file_bytes: bytes, filename: str) -> dict:
    """Parse an Excel file containing MSE financial statements.

    Args:
        file_bytes: Raw bytes of the uploaded Excel file.
        filename: Original filename (used to extract company/year metadata).

    Returns:
        Structured dict with metadata and parsed financial data.

    Raises:
        ValueError: If the file cannot be parsed or contains no recognizable data.
    """
    is_xls = filename.lower().endswith(".xls")

    if is_xls:
        return _parse_xls(file_bytes, filename)
    else:
        return _parse_xlsx(file_bytes, filename)


def _parse_xlsx(file_bytes: bytes, filename: str) -> dict:
    """Parse a .xlsx file using openpyxl."""
    try:
        wb = load_workbook(
            filename=io.BytesIO(file_bytes),
            read_only=True,
            data_only=True,
        )
    except Exception as e:
        raise ValueError(f"Cannot open Excel file: {e}")

    company, year = _extract_metadata_from_filename(filename)
    result = _make_result_dict(filename, company, year)

    for sheet_name in wb.sheetnames:
        sheet_type = _detect_sheet_type(sheet_name)
        if not sheet_type:
            continue

        ws = wb[sheet_name]
        # 7 separate dictionaries (one per statement type) prevent false matches:
        # bank terminology overlaps with standard terminology in Mongolian. Merged into
        # one dict, "зээл" (loans, bank-specific) would map to the wrong field for
        # non-bank companies. Dispatcher selects the correct dict from detected sheet type.
        headers_dict = HEADERS_BY_TYPE[sheet_type]
        parsed_data = _parse_openpyxl_sheet(ws, headers_dict)

        if parsed_data:
            result[sheet_type] = parsed_data
            result["metadata"]["sheets_parsed"].append(sheet_type)

        # Extract company name from sheet content (always prefer over filename)
        extracted = _extract_company_from_openpyxl_sheet(ws)
        if extracted:
            result["metadata"]["company"] = extracted

    wb.close()

    if not result["metadata"]["sheets_parsed"]:
        raise ValueError(
            "No recognizable financial statement sheets found. "
            "Expected Mongolian-language sheets (e.g., Балансын тайлан, "
            "Орлогын тайлан, Мөнгөн гүйлгээний тайлан)."
        )

    return result


def _parse_xls(file_bytes: bytes, filename: str) -> dict:
    """Parse a .xls file using xlrd."""
    try:
        wb = xlrd.open_workbook(file_contents=file_bytes)
    except Exception as e:
        raise ValueError(f"Cannot open Excel file: {e}")

    company, year = _extract_metadata_from_filename(filename)
    result = _make_result_dict(filename, company, year)

    for sheet_name in wb.sheet_names():
        sheet_type = _detect_sheet_type(sheet_name)
        if not sheet_type:
            continue

        ws = wb.sheet_by_name(sheet_name)
        headers_dict = HEADERS_BY_TYPE[sheet_type]
        parsed_data = _parse_xlrd_sheet(ws, headers_dict)

        if parsed_data:
            result[sheet_type] = parsed_data
            result["metadata"]["sheets_parsed"].append(sheet_type)

        # Extract company name from sheet content (always prefer over filename)
        extracted = _extract_company_from_xlrd_sheet(ws)
        if extracted:
            result["metadata"]["company"] = extracted

    if not result["metadata"]["sheets_parsed"]:
        raise ValueError(
            "No recognizable financial statement sheets found. "
            "Expected Mongolian-language sheets (e.g., Балансын тайлан, "
            "Орлогын тайлан, Мөнгөн гүйлгээний тайлан)."
        )

    return result


def _make_result_dict(filename: str, company: str, year: str) -> dict:
    """Create the base result dictionary."""
    return {
        "metadata": {
            "filename": filename,
            "company": company,
            "year": year,
            "parsed_at": datetime.now().isoformat(),
            "sheets_parsed": [],
        },
        "balance_sheet": {},
        "income_statement": {},
        "cash_flow": {},
    }


def _extract_metadata_from_filename(filename: str) -> tuple[str, str]:
    """Extract company name and year from filename.

    Supports patterns like:
        APU_2023.xlsx -> ("APU", "2023")
        APU 2023.xlsx -> ("APU", "2023")
        354_finance_report_xls_698c1feac88ac.xls -> ("unknown", "unknown")
    """
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename

    year_match = re.search(r"(20\d{2})", stem)
    year = year_match.group(1) if year_match else "unknown"

    if year_match:
        company = stem[: year_match.start()].strip().rstrip("_- ")
    else:
        company = stem.strip()

    # If company looks like a hash or random string, treat as unknown
    if company and re.match(r"^[\da-f_]+$", company):
        company = "unknown"

    return company if company else "unknown", year


def _extract_company_name_from_text(text: str) -> str | None:
    """Extract company name from cell text like 'Байгууллагын нэр: Сүү'."""
    if not text:
        return None
    text = str(text).strip()
    match = re.search(r"байгууллагын нэр\s*:\s*(.+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _extract_company_from_openpyxl_sheet(ws) -> str | None:
    """Scan first few rows of an openpyxl sheet for company name."""
    for row in ws.iter_rows(min_row=1, max_row=5, max_col=5):
        for cell in row:
            if cell.value:
                name = _extract_company_name_from_text(cell.value)
                if name:
                    return name
    return None


def _extract_company_from_xlrd_sheet(ws) -> str | None:
    """Scan first few rows of an xlrd sheet for company name."""
    for row_idx in range(min(5, ws.nrows)):
        for col_idx in range(min(5, ws.ncols)):
            val = ws.cell_value(row_idx, col_idx)
            if val:
                name = _extract_company_name_from_text(val)
                if name:
                    return name
    return None


def _detect_sheet_type(sheet_name: str) -> str | None:
    """Detect the financial statement type from sheet name.

    # Sheet type is detected from tab name patterns before header mapping:
    # determines which of the 7 dictionaries (standard BS/IS/CF, bank BS/IS,
    # insurance BS/IS) to apply. Companies filing under different regulatory
    # frameworks use entirely different Mongolian account terminology.
    """
    normalized = normalize_header(sheet_name)
    # Check longer patterns first for specificity
    for pattern, sheet_type in sorted(
        SHEET_TYPE_PATTERNS.items(), key=lambda x: len(x[0]), reverse=True
    ):
        if pattern in normalized:
            return sheet_type
    return None


def _parse_openpyxl_sheet(ws, headers_dict: dict[str, str]) -> dict:
    """Parse an openpyxl worksheet (.xlsx).

    Scans column C (index 2) for Mongolian headers, reads values
    from columns D (index 3 = prev year) and E (index 4 = current year).
    """
    parsed = {}

    for row in ws.iter_rows(min_col=1, max_col=6):
        # Get header text from column C (index 2)
        if len(row) <= HEADER_COL:
            continue
        header_cell = row[HEADER_COL]
        if header_cell.value is None:
            continue

        english_key = match_header(header_cell.value, headers_dict)
        if english_key is None:
            continue

        # Read previous year (col D) and current year (col E)
        prev_val = _safe_cell_value(row, PREV_COL)
        curr_val = _safe_cell_value(row, CURR_COL)

        if curr_val is not None:
            parsed[english_key] = curr_val
        if prev_val is not None:
            parsed[f"{english_key}_prev"] = prev_val

    return parsed


def _parse_xlrd_sheet(ws, headers_dict: dict[str, str]) -> dict:
    """Parse an xlrd worksheet (.xls).

    Scans column C (index 2) for Mongolian headers, reads values
    from columns D (index 3 = prev year) and E (index 4 = current year).
    """
    parsed = {}

    for row_idx in range(ws.nrows):
        # Get header text from column C (index 2)
        if ws.ncols <= HEADER_COL:
            continue
        header_val = ws.cell_value(row_idx, HEADER_COL)
        if not header_val:
            continue

        english_key = match_header(header_val, headers_dict)
        if english_key is None:
            continue

        # Read previous year (col D) and current year (col E)
        prev_val = _safe_xlrd_value(ws, row_idx, PREV_COL)
        curr_val = _safe_xlrd_value(ws, row_idx, CURR_COL)

        if curr_val is not None:
            parsed[english_key] = curr_val
        if prev_val is not None:
            parsed[f"{english_key}_prev"] = prev_val

    return parsed


def _safe_cell_value(row, col_idx: int) -> float | None:
    """Safely get a numeric value from an openpyxl row at col_idx."""
    if col_idx >= len(row):
        return None
    val = row[col_idx].value
    if val is None:
        return None
    if _is_numeric(val):
        return _to_number(val)
    return None


def _safe_xlrd_value(ws, row_idx: int, col_idx: int) -> float | None:
    """Safely get a numeric value from an xlrd sheet."""
    if col_idx >= ws.ncols:
        return None
    val = ws.cell_value(row_idx, col_idx)
    if val is None or val == "":
        return None
    if _is_numeric(val):
        return _to_number(val)
    return None


def _is_numeric(value) -> bool:
    """Check if a value is numeric (int, float, or numeric string)."""
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        cleaned = value.replace(",", "").replace(" ", "").strip()
        try:
            float(cleaned)
            return True
        except ValueError:
            return False
    return False


def _to_number(value) -> float:
    """Convert a value to a number."""
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).replace(",", "").replace(" ", "").strip()
    return float(cleaned)

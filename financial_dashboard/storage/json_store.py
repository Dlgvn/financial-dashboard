"""JSON file storage for parsed financial data.

Saves parsed Excel data as individual JSON files in the data/ directory
and maintains an index.json manifest for quick lookups.
"""

import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"
INDEX_FILE = DATA_DIR / "index.json"


def _ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_parsed_data(parsed_dict: dict) -> str:
    """Save parsed financial data to a JSON file.

    Args:
        parsed_dict: The structured dict returned by parse_excel_file().

    Returns:
        The filename of the saved JSON file.
    """
    _ensure_data_dir()

    meta = parsed_dict["metadata"]
    company = meta["company"].replace(" ", "_")
    year = meta["year"]
    json_filename = f"{company}_{year}.json"
    json_path = DATA_DIR / json_filename

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(parsed_dict, f, ensure_ascii=False, indent=2)

    sector = _detect_sector(parsed_dict)
    _update_index(meta, json_filename, sector=sector)
    return json_filename


def _detect_sector(parsed_dict: dict) -> str:
    """Auto-detect sector from parsed data keys.

    Returns:
        "Banking" if bank sheets present,
        "Insurance" if insurance sheets present,
        "Standard" otherwise.
    """
    if "bank_balance_sheet" in parsed_dict or "bank_income_statement" in parsed_dict:
        return "Banking"
    if "insurance_balance_sheet" in parsed_dict or "insurance_income_statement" in parsed_dict:
        return "Insurance"
    return "Standard"


def _update_index(metadata: dict, json_filename: str, sector: str = "Standard"):
    """Update index.json with the new file entry."""
    index = load_index()

    entry = {
        "filename": json_filename,
        "original_file": metadata["filename"],
        "company": metadata["company"],
        "year": metadata["year"],
        "sector": sector,
        "sheets_parsed": metadata["sheets_parsed"],
        "parsed_at": metadata["parsed_at"],
    }

    # Replace existing entry for same company/year, or append
    index["files"] = [
        f for f in index["files"]
        if f["filename"] != json_filename
    ]
    index["files"].append(entry)

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def load_index() -> dict:
    """Load the index.json manifest.

    Returns:
        Dict with a "files" key containing list of file entries.
    """
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"files": []}


def load_parsed_file(json_filename: str) -> dict:
    """Load a parsed JSON file by its filename.

    Args:
        json_filename: Name of the JSON file (e.g., "APU_2023.json").

    Returns:
        The parsed financial data dict.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    json_path = DATA_DIR / json_filename
    if not json_path.exists():
        raise FileNotFoundError(f"File not found: {json_filename}")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_parsed_file(json_filename: str):
    """Delete a parsed JSON file and remove it from the index.

    Args:
        json_filename: Name of the JSON file to delete.
    """
    json_path = DATA_DIR / json_filename
    if json_path.exists():
        os.remove(json_path)

    index = load_index()
    index["files"] = [
        f for f in index["files"]
        if f["filename"] != json_filename
    ]
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

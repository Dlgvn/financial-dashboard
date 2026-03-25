"""Registry loader for MSE company data from data/company_registry.json."""

import json
from pathlib import Path

_REGISTRY_PATH = Path(__file__).parent.parent.parent / "data" / "company_registry.json"

_registry: list[dict] | None = None


def _load() -> list[dict]:
    """Lazy-load and cache the company registry from disk."""
    global _registry
    if _registry is None:
        _registry = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    return _registry


def _normalize(name: str) -> str:
    """Normalize a company name for lookup: remove all quotes, collapse spaces, lowercase."""
    # Remove all quote characters
    result = name.replace('"', "").replace("'", "")
    # Collapse multiple spaces into one, strip leading/trailing whitespace
    result = " ".join(result.split())
    return result.lower()


def find_mse_id(company_name: str) -> int:
    """Look up the MSE company ID by company name.

    Normalizes both the query and registry entries by stripping whitespace,
    embedded quote characters, and lowercasing before comparing.

    Args:
        company_name: The company's Mongolian name (may contain embedded quotes).

    Returns:
        The integer MSE company ID.

    Raises:
        KeyError: If no matching company is found in the registry.
    """
    registry = _load()
    query = _normalize(company_name)
    for entry in registry:
        if _normalize(entry["name"]) == query:
            return entry["mse_id"]
    raise KeyError(
        f"Company not found in registry: {company_name!r} (normalized: {query!r})"
    )


def all_companies() -> list[dict]:
    """Return the full company registry as a list of dicts."""
    return _load()

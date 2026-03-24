# Phase 1: Price Data Seed — Research

**Researched:** 2026-03-24
**Domain:** Web scraping (requests + BeautifulSoup4), flat JSON storage, Reflex async state events
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Seed run scrapes ALL 162 MSE-listed companies (Classification I, II, III).
- **D-02:** Company registry is a pre-built `data/company_registry.json` (manually curated, not auto-scraped from companies_info pages).
- **D-03:** Registry fields: `name` (Mongolian), `mse_id` (int), `ticker` (English shortcode), `tier` ("I", "II", or "III").
- **D-04:** Known IDs: АПУ=90, Дархан нэхий ХК=71, Сүү=135, Мандал даатгал=547, Моносхүнс=551, Премиум Нэксус ХК=557, Хаан банк=563. Remaining ~155 IDs discovered and added to registry.
- **D-05:** Price files keyed by Mongolian company name — `data/prices/АПУ.json`.
- **D-06:** "Refresh Prices" button on the upload/home page only; re-scrapes companies already in `index.json`.
- **D-07:** Button shows loading state during scraping and displays per-company success/error feedback when complete.
- **D-08:** Uses `requests` + `BeautifulSoup4`. Add both to `requirements.txt`.
- **D-09:** Per-company errors logged and skipped — full run does not crash on single failure.
- **D-10:** Already-scraped files not re-scraped on retry (idempotent). Check file existence before scraping.
- **D-11:** Source URL: `old.mse.mn/en/company/{mse_id}` — server-rendered HTML, OHLCV + Date columns.

### Claude's Discretion

- Rate limiting / politeness delay between requests (sleep interval, user-agent header)
- JSON structure inside each price file (array of records vs date-indexed dict)
- Progress logging format during seed run (stdout, log file, or both)
- Whether to paginate or scrape all pages in one pass

### Deferred Ideas (OUT OF SCOPE)

- Scraping `companies_info/1,/2,/3` to auto-discover IDs (user chose pre-built registry)
- Per-company refresh button on the company detail page (user chose upload page global button)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SCRP-01 | System scrapes historical price data (Open/High/Low/Close/Volume/Date) from `old.mse.mn/en/company/{id}` using requests + BeautifulSoup4 | HTML table structure fully verified by live fetch; parser pattern documented below |
| SCRP-02 | System stores price history as JSON in `data/prices/{company}.json` | Storage pattern mirrors existing `json_store.py`; JSON schema defined below |
| SCRP-03 | System maintains mapping of all 7 demo company names to their MSE company IDs | 7 known IDs confirmed; registry bootstrap data provided below; full 161-company ID list scraped |
| SCRP-04 | User can trigger "Refresh Prices" from UI; system shows loading state and success/error feedback | Reflex async generator pattern confirmed in existing `handle_upload`; implementation pattern documented |
</phase_requirements>

---

## Summary

The MSE old website (`old.mse.mn`) serves all historical price records for a company on a **single HTML page** with no pagination. For APU (ID=90) this is 2,810 rows loaded in one HTTP GET. The page is plain server-rendered HTML — no JavaScript execution required, requests + BeautifulSoup4 is confirmed correct.

The company classification pages (`/en/companies_info/1/168`, `/en/companies_info/2/168`, `/en/companies_info/3/169`) are live and return 1.2 MB HTML pages containing all company links. Live scraping of those three pages yields 161 unique company IDs across the three tiers — consistent with the "162" target (one company may be newly listed or counted differently). The Mongolian company name is available on each company's profile page; the English ticker-like short code is in the dropdown on the home page.

The Reflex async generator pattern (using `yield` inside an `async def` event handler) is already established in `handle_upload` and works cleanly for streaming loading-state updates. The "Refresh Prices" button integrates into the existing `index()` page in `financial_dashboard.py` and wires to a new `PriceState` (or method on `UploadState`).

**Primary recommendation:** Build `scripts/seed_prices.py` as a standalone CLI script first; wire the Reflex button as a thin call to the same underlying scraper logic.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests | 2.32.3 (installed) / 2.32.5 (latest) | HTTP GET to old.mse.mn | Project-locked decision D-08; already installed |
| beautifulsoup4 | 4.12.3 (installed) / 4.14.3 (latest) | Parse HTML price table | Project-locked decision D-08 |
| lxml or html.parser | stdlib / pip | BS4 parser backend | `html.parser` is stdlib, zero extra install; `lxml` faster for large pages |
| json | stdlib | Serialize price records to file | Already used throughout project |
| pathlib | stdlib | Path construction (DATA_DIR pattern) | Already established in json_store.py |
| time | stdlib | Politeness sleep between requests | No extra install |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| logging | stdlib | Progress + error logging during seed run | Prefer over print() for structured log levels |
| argparse | stdlib | CLI flags for seed script (--force-rescrape, --company-filter) | Optional but makes the script testable |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| html.parser (BS4) | lxml | lxml is 3-5x faster but requires `pip install lxml`; for 162 companies html.parser is fine |
| requests | httpx | httpx supports async; not needed here since seed script is synchronous |
| flat list JSON | date-keyed dict | Date-keyed dict enables O(1) date lookup but makes list iteration awkward; Phase 3 needs chronological list for charts |

**Installation (additions to requirements.txt):**
```bash
requests>=2.32.0
beautifulsoup4>=4.12.0
```
Both are already installed in the venv. Only the `requirements.txt` entry is missing.

---

## Architecture Patterns

### Recommended Project Structure

```
scripts/
└── seed_prices.py           # Standalone CLI seed script (run once)
financial_dashboard/
├── scraper/
│   ├── __init__.py
│   ├── price_scraper.py     # Core scraping logic: fetch + parse one company
│   └── registry_loader.py  # Load/query company_registry.json
└── state.py                 # Add PriceRefreshState mixin or extend UploadState
data/
├── company_registry.json    # Pre-built; 161 companies, 4 fields each
├── prices/
│   ├── АПУ.json
│   ├── Хаан банк.json
│   └── ...                  # One file per company (Mongolian name)
└── index.json               # Unchanged; "company" field = price file lookup key
```

### Pattern 1: HTML Table Parsing — Verified Structure

**What:** The price table on `old.mse.mn/en/company/{id}` has class `trade_history_result`. Columns in order: `№`, `High`, `Low`, `Open`, `Close`, `Volume`, `Value`, `Date`. All data is in `<tbody><tr><td>` elements. Numbers use comma thousands separators (e.g., `3,700`). No pagination — all records on one page.

**Verified row count:** APU (ID=90) returns 2,810 rows in a single HTTP GET as of 2026-03-24.

**Example:**
```python
# Source: live fetch of http://old.mse.mn/en/company/90 (verified 2026-03-24)
import requests
from bs4 import BeautifulSoup

def scrape_company_prices(mse_id: int, company_name: str) -> list[dict]:
    url = f"http://old.mse.mn/en/company/{mse_id}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MSEAnalytica/1.0)"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", class_="trade_history_result")
    if not table:
        raise ValueError(f"Price table not found for company {company_name} (id={mse_id})")

    records = []
    for row in table.find("tbody").find_all("tr"):
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        # cells: [№, High, Low, Open, Close, Volume, Value, Date]
        if len(cells) < 8:
            continue
        records.append({
            "date":   cells[7],           # "2014-09-16"
            "open":   cells[3].replace(",", ""),
            "high":   cells[1].replace(",", ""),
            "low":    cells[2].replace(",", ""),
            "close":  cells[4].replace(",", ""),
            "volume": cells[5].replace(",", ""),
        })
    return records
```

### Pattern 2: Price File Storage

**What:** Mirror the existing `json_store.py` DATA_DIR convention. Create `data/prices/` subdirectory. File name = Mongolian company name (matches `index.json` `company` field exactly).

**JSON schema (array of records — time-series list for Phase 3 chart):**
```python
# data/prices/АПУ.json
{
  "company": "АПУ",
  "mse_id": 90,
  "scraped_at": "2026-03-24T12:00:00",
  "records": [
    {"date": "2014-09-16", "open": "3655", "high": "3700", "low": "3650", "close": "3700", "volume": "510"},
    ...
  ]
}
```

**Why array, not date-dict:** Phase 3 needs chronological list for Recharts `LineChart`. An array maps directly to `data` prop without transformation. Sorting by date on write (ascending) gives Phase 3 a ready-to-use dataset.

**Storage function:**
```python
from pathlib import Path
import json
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PRICES_DIR = DATA_DIR / "prices"

def save_price_data(company_name: str, mse_id: int, records: list[dict]) -> str:
    PRICES_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{company_name}.json"
    path = PRICES_DIR / filename
    payload = {
        "company": company_name,
        "mse_id": mse_id,
        "scraped_at": datetime.now().isoformat(),
        "records": sorted(records, key=lambda r: r["date"]),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return filename

def price_file_exists(company_name: str) -> bool:
    return (PRICES_DIR / f"{company_name}.json").exists()
```

### Pattern 3: Idempotent Seed Script

**What:** Before scraping, check `price_file_exists()`. Skip if exists. This satisfies D-10.

```python
# scripts/seed_prices.py  (run as: python scripts/seed_prices.py)
import json, time, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

REGISTRY_PATH = Path("data/company_registry.json")
SLEEP_SECONDS = 0.5   # politeness delay

def run_seed(force: bool = False):
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    total = len(registry)
    ok, skipped, failed = 0, 0, 0

    for i, entry in enumerate(registry, 1):
        name = entry["name"]
        mse_id = entry["mse_id"]
        log.info(f"[{i}/{total}] {name} (id={mse_id})")

        if not force and price_file_exists(name):
            log.info(f"  -> SKIP (file exists)")
            skipped += 1
            continue

        try:
            records = scrape_company_prices(mse_id, name)
            save_price_data(name, mse_id, records)
            log.info(f"  -> OK ({len(records)} records)")
            ok += 1
        except Exception as e:
            log.warning(f"  -> FAIL: {e}")
            failed += 1

        time.sleep(SLEEP_SECONDS)

    log.info(f"Done. OK={ok} SKIPPED={skipped} FAILED={failed}")
```

### Pattern 4: Reflex "Refresh Prices" Button — Async Generator

**What:** Reflex supports streaming state updates via `async def` event handlers that `yield`. The existing `handle_upload` in `state.py` confirms this pattern works on Reflex 0.8.26.

**State additions (extend UploadState or new mixin):**
```python
# In state.py — add to UploadState or as a new class PriceRefreshState(UploadState)
is_refreshing_prices: bool = False
price_refresh_log: list[dict[str, str]] = []   # [{"company": "АПУ", "status": "ok"}]
price_refresh_summary: str = ""

@rx.event
async def refresh_prices(self):
    """Re-scrape prices for all companies currently in index.json."""
    self.is_refreshing_prices = True
    self.price_refresh_log = []
    self.price_refresh_summary = ""
    yield

    from .scraper.price_scraper import scrape_company_prices, save_price_data
    from .scraper.registry_loader import find_mse_id

    index = load_index()
    companies = list({e["company"] for e in index.get("files", [])})

    ok, failed = 0, 0
    log = []
    for company in companies:
        try:
            mse_id = find_mse_id(company)  # looks up company_registry.json
            records = scrape_company_prices(mse_id, company)
            save_price_data(company, mse_id, records)
            log.append({"company": company, "status": "ok", "count": str(len(records))})
            ok += 1
        except Exception as e:
            log.append({"company": company, "status": "error", "count": str(e)})
            failed += 1
        self.price_refresh_log = log
        yield   # stream each company result to the UI

    self.is_refreshing_prices = False
    self.price_refresh_summary = f"{ok} updated, {failed} failed"
    yield
```

**UI button (in `financial_dashboard.py` index function):**
```python
rx.button(
    rx.cond(
        UploadState.is_refreshing_prices,
        rx.spinner(size="2"),
        rx.icon("refresh-cw", size=16),
    ),
    "Refresh Prices",
    on_click=UploadState.refresh_prices,
    is_disabled=UploadState.is_refreshing_prices,
    class_name=(
        "flex items-center gap-2 px-4 py-2 rounded-lg "
        "bg-blue-600 hover:bg-blue-500 text-white font-semibold "
        "transition-colors text-sm disabled:opacity-50"
    ),
),
```

### Pattern 5: Company Registry Bootstrap

**What:** `data/company_registry.json` must be created before the seed script runs. The 7 known demo companies are confirmed. The remaining ~154 IDs are obtainable from the live classification pages.

**7 confirmed demo companies:**
| Mongolian Name | MSE ID | Tier |
|---|---|---|
| АПУ | 90 | I |
| Дархан нэхий ХК | 71 | I |
| Сүү | 135 | I |
| Мандал даатгал | 547 | I |
| Моносхүнс | 551 | I |
| Премиум Нэксус ХК | 557 | I |
| Хаан банк | 563 | I |

**Full ID list (161 companies discovered by live scrape of classification pages on 2026-03-24):**

- **Class I (24 companies):** 71, 90, 135, 326, 354, 458, 522, 541, 542, 544, 545, 547, 548, 549, 550, 551, 553, 557, 562, 563, 564, 567, 568, 569
- **Class II (43 companies):** 2, 7, 9, 13, 17, 22, 25, 34, 38, 88, 162, 191, 195, 208, 209, 234, 308, 309, 366, 378, 379, 396, 402, 438, 441, 444, 445, 460, 466, 484, 521, 525, 528, 530, 537, 543, 546, 554, 561, 565, 570, 572, 573
- **Class III (94 companies):** 8, 23, 33, 40, 41, 54, 56, 61, 65, 67, 68, 69, 78, 80, 86, 94, 96, 97, 98, 108, 118, 119, 120, 125, 133, 136, 142, 143, 148, 152, 154, 175, 176, 179, 187, 196, 200, 201, 204, 207, 214, 217, 227, 231, 236, 239, 246, 252, 254, 269, 290, 300, 311, 317, 325, 331, 332, 369, 376, 377, 380, 385, 386, 389, 394, 408, 409, 420, 425, 431, 435, 448, 452, 454, 455, 459, 461, 464, 469, 471, 476, 490, 492, 503, 505, 506, 508, 517, 524, 527, 532, 536, 540, 571

Note: MSE itself (ID=510) appears on all three pages but is the exchange operator, not a company to scrape. Total unique companies = 161. The discrepancy vs "162" goal is likely one newly-listed company; the plan should document 161 and note the registry can be extended.

The registry creation is itself a Wave 0 task: build a script or manually assemble `company_registry.json` using the English names from the classification pages, match to Mongolian names from individual company pages, and confirm tickers.

**Registry entry shape:**
```json
[
  {"name": "АПУ", "mse_id": 90, "ticker": "APU", "tier": "I"},
  {"name": "Хаан банк", "mse_id": 563, "ticker": "KHAN", "tier": "I"}
]
```

### Anti-Patterns to Avoid

- **Using Mongolian name from companies_info pages as file key without verification:** The English pages list English company names (e.g., "APU", "Khan bank JSC"). The Mongolian name must be retrieved from each company's individual page or from the existing `index.json` `company` field. For the 7 demo companies, the `index.json` `company` field is the authoritative Mongolian name. For remaining 154, use Mongolian page or keep English from classification pages if Mongolian name is not needed at scrape time (just for the registry `name` field).

- **Removing commas from numbers before storing:** Store prices as strings (already comma-stripped). The Phase 3 consumer should parse to float. Alternatively store as int/float directly — but keep consistent.

- **Blocking the Reflex event loop with a long synchronous scrape:** The `yield` pattern after each company ensures the UI updates incrementally. Without yields the browser appears frozen until all 7 companies finish.

- **Hardcoding `data/prices/` path:** Use `DATA_DIR / "prices"` from the same path-resolution pattern in `json_store.py` so the path is correct regardless of working directory.

- **Not creating `data/prices/` before first write:** Use `mkdir(parents=True, exist_ok=True)` the same way `_ensure_data_dir()` does it.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTML parsing | Custom regex on raw HTML | BeautifulSoup4 `find()` / `find_all()` | Attribute matching, malformed HTML tolerance, whitespace handling |
| HTTP retries | Manual try/retry loop | `requests` with `timeout` + catch `requests.exceptions.RequestException` | requests handles connection pooling; simple retry is fine at this scale |
| File existence check | Glob or os.listdir | `Path.exists()` | One-liner, already used in project |
| JSON serialization with Mongolian text | Custom encoder | `json.dump(..., ensure_ascii=False)` | Already established pattern in json_store.py |
| Date sorting | Custom comparator | `sorted(records, key=lambda r: r["date"])` | ISO date strings sort lexicographically correctly |

**Key insight:** The scraper is simple because the site is server-rendered with no auth, no JS, no pagination. Don't add complexity (Selenium, Playwright, async httpx) that isn't needed.

---

## Common Pitfalls

### Pitfall 1: `trade_history_result` Table Class May Be Missing for Some Companies

**What goes wrong:** Some companies (newly listed, or delisted, or with zero trading history) may not have the `trade_history_result` table on their page. The `soup.find()` returns `None` and calling `.find("tbody")` on `None` raises `AttributeError`.

**Why it happens:** Not all 161 MSE IDs have price history. New listings, zero-trade companies, or suspended securities may only have profile info.

**How to avoid:** Check `if not table: raise ValueError(f"No price table")` — the per-company error catch in the seed script handles this gracefully per D-09.

**Warning signs:** Zero records written for an ID that should have data.

### Pitfall 2: Comma-Formatted Numbers in Price Cells

**What goes wrong:** Price cells contain `"3,700"` not `"3700"`. Direct `int()` conversion raises `ValueError`.

**Why it happens:** The MSE site formats numbers with comma separators.

**How to avoid:** Always `cell.replace(",", "")` before numeric conversion, or store as string and let consumers parse. Recommendation: store as string, strip commas.

**Warning signs:** `ValueError: invalid literal for int() with base 10: '3,700'`

### Pitfall 3: Reflex State Var Type Violations

**What goes wrong:** Adding `price_refresh_log: list[dict] = []` works at runtime but can cause Reflex serialization errors or type check failures. Reflex requires `list[dict[str, str]]` for state vars that are rendered in `rx.foreach`.

**Why it happens:** Reflex serializes state to JSON for SSE updates. Raw `dict` is not strongly typed enough for the serializer in some contexts.

**How to avoid:** Declare as `list[dict[str, str]] = []`. Ensure all values in the dict are strings (convert ints to str before assigning). Established pattern in `UploadState.uploaded_files`.

**Warning signs:** `TypeError` or blank UI rendering for the foreach component.

### Pitfall 4: MSE Site Slowness / Timeouts for Large Responses

**What goes wrong:** Pages for companies with long trading histories (~2,800+ rows) return 600–700 KB HTML. On a slow connection or server-side rate limiting, requests may time out.

**Why it happens:** No CDN, old server infrastructure. 162 rapid sequential requests may trigger throttling.

**How to avoid:** Use `timeout=30` in requests. Use `time.sleep(0.5)` between requests (0.5 seconds = ~81 seconds total for 162 companies — acceptable). Use a User-Agent header that identifies the project.

**Warning signs:** `requests.exceptions.ReadTimeout` or `ConnectionError`.

### Pitfall 5: File Naming Collision with Mongolian Unicode

**What goes wrong:** Mongolian company names contain Unicode characters. File systems on macOS/Linux handle UTF-8 filenames fine, but `data/prices/"_Премиум_Нэксус_"_ХК.json` (note the quotes) would be problematic.

**Why it happens:** The `company` field in `index.json` for Premium Nexus is `"\" Премиум Нэксус \" ХК"` — it includes embedded quote characters.

**How to avoid:** Sanitize the company name before using as filename. Strip leading/trailing quote characters and whitespace. The price file should be named `Премиум Нэксус ХК.json` not `" Премиум Нэксус " ХК.json`.

**Warning signs:** File creation failure on some OS, or `FileNotFoundError` at lookup time due to name mismatch.

**Sanitization pattern:**
```python
def price_filename(company_name: str) -> str:
    """Sanitize company name for use as a filename."""
    name = company_name.strip().strip('"').strip()
    # Replace filesystem-unsafe chars if any remain
    for ch in ['"', '/', '\\', ':', '*', '?', '<', '>', '|']:
        name = name.replace(ch, '')
    return f"{name}.json"
```

### Pitfall 6: `index.json` Company Name Mismatch with Registry

**What goes wrong:** The registry uses `name` from one source; `index.json` uses the parsed Excel company name. If there's a mismatch (e.g., `"Премиум Нэксус ХК"` vs `"\" Премиум Нэксус \" ХК"`), the Refresh button can't find the registry entry and fails silently.

**Why it happens:** Excel files may embed quotes in company names (the parser preserves them). The `find_mse_id(company)` lookup must handle this.

**How to avoid:** In `find_mse_id()`, normalize both the query name and registry names before comparing (strip, strip quotes, lowercase comparison). Log a warning if no match found rather than returning `None` silently.

---

## Code Examples

### Full Scraper Function (Verified Against Live Site)

```python
# Source: live fetch verified 2026-03-24, HTML structure confirmed
import requests
from bs4 import BeautifulSoup
import time, logging

log = logging.getLogger(__name__)
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MSEAnalytica-Scraper/1.0)"}

def scrape_company_prices(mse_id: int, company_name: str) -> list[dict]:
    """Scrape OHLCV price history for one company. Returns list sorted by date ascending."""
    url = f"http://old.mse.mn/en/company/{mse_id}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", class_="trade_history_result")
    if not table:
        raise ValueError(f"No price table found (id={mse_id}, name={company_name})")

    records = []
    tbody = table.find("tbody")
    if not tbody:
        return records

    for row in tbody.find_all("tr"):
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        # Expected: [№, High, Low, Open, Close, Volume, Value, Date]
        if len(cells) < 8:
            continue
        records.append({
            "date":   cells[7],
            "open":   cells[3].replace(",", ""),
            "high":   cells[1].replace(",", ""),
            "low":    cells[2].replace(",", ""),
            "close":  cells[4].replace(",", ""),
            "volume": cells[5].replace(",", ""),
        })

    return sorted(records, key=lambda r: r["date"])
```

### Registry Loader

```python
# financial_dashboard/scraper/registry_loader.py
import json
from pathlib import Path

_REGISTRY_PATH = Path(__file__).parent.parent.parent / "data" / "company_registry.json"
_registry: list[dict] | None = None

def _load() -> list[dict]:
    global _registry
    if _registry is None:
        _registry = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    return _registry

def find_mse_id(company_name: str) -> int:
    """Find MSE ID by company name. Raises KeyError if not found."""
    query = company_name.strip().strip('"').strip().lower()
    for entry in _load():
        if entry["name"].strip().strip('"').strip().lower() == query:
            return int(entry["mse_id"])
    raise KeyError(f"Company not found in registry: {company_name!r}")

def all_companies() -> list[dict]:
    return _load()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| Selenium/Playwright for JS-heavy sites | requests + BS4 for server-rendered HTML | N/A | old.mse.mn is server-rendered — no JS needed, simpler stack |
| Scraping all records with pagination | Single-page load (no pagination on old.mse.mn) | N/A | Confirmed: all history on one page, simpler scraper |
| Reflex event handlers as plain `def` | `async def` with `yield` for streaming UI updates | Reflex 0.3+ | Yield inside async event = streaming SSE state updates |

---

## Open Questions

1. **Mongolian names for 154 non-demo companies**
   - What we know: English names scraped from classification pages (e.g., "APU", "Khan bank JSC")
   - What's unclear: The Mongolian name for each company (needed for `company_registry.json` `name` field and `data/prices/` filename)
   - Recommendation: For the seed script, English names are sufficient as the `name` field since the 7 demo companies are the only ones whose price files get looked up by `index.json` `company` (Mongolian) key. The registry creation Wave 0 task should note that non-demo company names can be English until a Mongolian lookup pass is run. Alternatively, fetch each company's individual page to read the Mongolian name from the page title.

2. **162 vs 161 companies**
   - What we know: Live scrape of all 3 classification pages yielded 161 unique company IDs as of 2026-03-24
   - What's unclear: Whether one company was missed (delisted, or only on newer mse.mn), or the "162" figure is slightly stale
   - Recommendation: Use 161 as the working count. Document in registry file header. The plan should not hard-block on "exactly 162".

3. **`" Премиум Нэксус " ХК` name normalization**
   - What we know: `index.json` stores this company as `"\" Премиум Нэксус \" ХК"` (with embedded quotes)
   - What's unclear: Whether Phase 3 price lookup uses the raw `index.json` `company` value or a normalized version
   - Recommendation: The `find_mse_id` function and `price_filename` function both normalize (strip quotes) on both sides of comparison and file naming. Document this normalization contract clearly.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | All scripts | ✓ | 3.12.5 | — |
| requests | HTTP scraping | ✓ | 2.32.3 (installed), 2.32.5 (latest) | — |
| beautifulsoup4 | HTML parsing | ✓ | 4.12.3 (installed), 4.14.3 (latest) | — |
| old.mse.mn (HTTP) | Price data | ✓ | Live as of 2026-03-24 | — (no fallback; external dependency) |
| pytest | Test execution | ✗ | — | Must install: `pip install pytest` |

**Missing dependencies with no fallback:**
- `old.mse.mn` — external site; if it goes down, seed script fails. No fallback. Mitigated by running seed once and committing results.

**Missing dependencies with fallback:**
- pytest — not installed in venv; Wave 0 must add `pip install pytest` to setup.

---

## Validation Architecture

No `config.json` found — nyquist_validation defaults to **enabled**.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (not yet installed) |
| Config file | none — see Wave 0 |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCRP-01 | `scrape_company_prices(90, "АПУ")` returns list with `date`, `open`, `high`, `low`, `close`, `volume` keys | unit (live HTTP) | `pytest tests/test_price_scraper.py::test_scrape_apu -x` | ❌ Wave 0 |
| SCRP-01 | `scrape_company_prices` raises `ValueError` when no price table present | unit (mock) | `pytest tests/test_price_scraper.py::test_no_table -x` | ❌ Wave 0 |
| SCRP-02 | `save_price_data` creates `data/prices/АПУ.json` with correct schema | unit | `pytest tests/test_price_scraper.py::test_save_price_data -x` | ❌ Wave 0 |
| SCRP-02 | `price_file_exists` returns True after save, False before | unit | `pytest tests/test_price_scraper.py::test_idempotency -x` | ❌ Wave 0 |
| SCRP-03 | `find_mse_id("АПУ")` returns 90; all 7 demo companies resolvable | unit | `pytest tests/test_registry_loader.py::test_known_ids -x` | ❌ Wave 0 |
| SCRP-04 | Verify Reflex state vars `is_refreshing_prices` and `price_refresh_log` exist and are typed correctly | unit (state inspection) | `pytest tests/test_price_state.py::test_state_vars -x` | ❌ Wave 0 |

Note: SCRP-01 live HTTP test requires network access. Tag it `@pytest.mark.network` and allow skipping in CI.

### Sampling Rate

- **Per task commit:** `pytest tests/test_price_scraper.py tests/test_registry_loader.py -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** All tests green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_price_scraper.py` — covers SCRP-01, SCRP-02
- [ ] `tests/test_registry_loader.py` — covers SCRP-03
- [ ] `tests/test_price_state.py` — covers SCRP-04
- [ ] `tests/conftest.py` — shared fixtures (temp data dir, mock HTTP response)
- [ ] Framework install: `pip install pytest` — not present in venv

---

## Project Constraints (from CLAUDE.md)

No `CLAUDE.md` found in project root. The following constraints are inferred from `STATE.md`, `PROJECT.md`, and existing code patterns:

- **Framework:** Reflex 0.8.26 — must not change
- **Python:** 3.12 only
- **State vars:** Must be typed (`list[dict[str, str]]`, `bool`, `str`) — no raw `dict` as top-level state var
- **Conditional rendering:** Use `rx.cond()` — no Python `if/else` in component functions
- **List rendering:** Use `rx.foreach()` — no Python `for` loops in components
- **Styling:** Tailwind v4 via `class_name` strings only — no `rx.color()` calls
- **Charts:** `rx.recharts` only — no matplotlib/plotly/etc in the UI
- **Storage root:** `DATA_DIR = Path(__file__).parent.parent.parent / "data"` — all file I/O relative to this
- **Encoding:** `ensure_ascii=False` on all JSON writes (Mongolian text)
- **No secrets in repo:** `.env` in `.gitignore`

---

## Sources

### Primary (HIGH confidence)

- Live HTTP fetch of `http://old.mse.mn/en/company/90` (2026-03-24) — table class `trade_history_result`, column order, no pagination, 2,810 rows confirmed
- Live HTTP fetch of `https://old.mse.mn/en/companies_info/1/168`, `/2/168`, `/3/169` (2026-03-24) — 161 company IDs across three tiers
- `financial_dashboard/storage/json_store.py` (project source) — DATA_DIR pattern, JSON write conventions
- `data/index.json` (project source) — canonical `company` field values for 7 demo companies
- `financial_dashboard/state.py` (project source) — async generator yield pattern, state var typing rules
- `financial_dashboard/financial_dashboard.py` (project source) — index() page structure for button placement

### Secondary (MEDIUM confidence)

- `requests` 2.32.3 installed / 2.32.5 latest (pip index verified 2026-03-24)
- `beautifulsoup4` 4.12.3 installed / 4.14.3 latest (pip index verified 2026-03-24)

### Tertiary (LOW confidence)

- Reflex 0.8.26 async generator behavior — confirmed by working code in project; not independently verified against Reflex changelog for this exact version

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — both libraries installed in venv, confirmed working
- HTML structure: HIGH — live-fetched and parsed the actual site
- Company ID discovery: HIGH — live-fetched all 3 classification pages
- Architecture patterns: HIGH — mirrors existing project conventions exactly
- Reflex async yield: HIGH — pattern copied from working `handle_upload` in state.py
- Pitfalls: HIGH — most derived from inspecting actual data (commas in numbers, quote in company name verified in index.json)
- Test infrastructure: HIGH — confirmed pytest not installed in venv

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (old.mse.mn is stable but unmaintained; HTML structure unlikely to change; company count may shift)

"""Mongolian-to-English header mappings for MSE financial statements.

These dictionaries map Mongolian financial terms (as they appear in .xlsx/.xls
files downloaded from members.mse.mn) to standardized English keys.

Matching uses substring containment (not exact match) because real headers
often include parenthetical suffixes like "(цэвэр)" or "(алдагдал)".
Longer patterns are checked first to avoid false matches.
"""

import re


def normalize_header(text: str) -> str:
    """Normalize a header string for matching.

    Strips whitespace, lowercases, and collapses multiple spaces.
    """
    if not text:
        return ""
    result = str(text).strip().lower()
    result = re.sub(r"\s+", " ", result)
    return result


def match_header(text: str, headers_dict: dict[str, str]) -> str | None:
    """Find the best matching English key for a Mongolian header.

    Uses substring containment, checking longer patterns first
    to avoid false positives (e.g., "урт хугацаат зээл" should not
    match "зээл" first).
    """
    normalized = normalize_header(text)
    if not normalized:
        return None

    # Sort by pattern length descending so longer/more specific patterns win
    for pattern, english_key in sorted(
        headers_dict.items(), key=lambda x: len(x[0]), reverse=True
    ):
        if pattern in normalized:
            return english_key
    return None


# --- Balance Sheet (Санхүүгийн байдлын тайлан / Балансын тайлан) ---
BALANCE_SHEET_HEADERS: dict[str, str] = {
    # Assets
    "мөнгө,түүнтэй адилтгах хөрөнгө": "cash_and_equivalents",
    "мөнгө, түүнтэй адилтгах хөрөнгө": "cash_and_equivalents",
    "мөнгө ба түүнтэй адилтгах хөрөнгө": "cash_and_equivalents",
    "дансны авлага": "accounts_receivable",
    "татвар, ндш – ийн авлага": "tax_receivable",
    "бусад авлага": "other_receivables",
    "бусад санхүүгийн хөрөнгө": "other_financial_assets",
    "бараа материал": "inventory",
    "урьдчилж төлсөн зардал": "prepaid_expenses",
    "бусад эргэлтийн хөрөнгө": "other_current_assets",
    "эргэлтийн хөрөнгийн дүн": "total_current_assets",
    "эргэлтийн хөрөнгө": "current_assets_section",
    # Non-current assets
    "үндсэн хөрөнгө": "fixed_assets",
    "биет бус хөрөнгө": "intangible_assets",
    "биологийн хөрөнгө": "biological_assets",
    "урт хугацаат хөрөнгө оруулалт": "long_term_investments",
    "хойшлогдсон татварын хөрөнгө": "deferred_tax_asset",
    "бусад эргэлтийн бус хөрөнгө": "other_non_current_assets",
    "эргэлтийн бус хөрөнгийн дүн": "total_non_current_assets",
    "эргэлтийн бус хөрөнгө": "non_current_assets_section",
    "нийт хөрөнгийн дүн": "total_assets",
    "нийт хөрөнгө": "total_assets",
    # Liabilities
    "дансны өглөг": "accounts_payable",
    "цалингийн өглөг": "salaries_payable",
    "татварын өр": "taxes_payable",
    "ндш - ийн өглөг": "social_security_payable",
    "богино хугацаат зээл": "short_term_loans",
    "хүүний өглөг": "interest_payable",
    "ногдол ашгийн өглөг": "dividends_payable",
    "урьдчилж орсон орлого": "unearned_revenue",
    "бусад богино хугацаат өр төлбөр": "other_current_liabilities",
    "богино хугацаат өр төлбөрийн дүн": "total_current_liabilities",
    "урт хугацаат зээл": "long_term_loans",
    "хойшлогдсон татварын өр": "deferred_tax_liability",
    "бусад урт хугацаат өр төлбөр": "other_non_current_liabilities",
    "урт хугацаат өр төлбөрийн дүн": "total_non_current_liabilities",
    "өр төлбөрийн нийт дүн": "total_liabilities",
    "нийт өр төлбөр": "total_liabilities",
    # Equity
    "нэмж төлөгдсөн капитал": "additional_paid_in_capital",
    "хуримтлагдсан ашиг": "retained_earnings",
    "хуваарилагдаагүй ашиг": "retained_earnings",
    "эздийн өмчийн дүн": "total_equity",
    "нийт эздийн өмч": "total_equity",
    "эздийн өмч": "total_equity",
    "өр төлбөр ба эздийн өмчийн дүн": "total_liabilities_and_equity",
}

# --- Income Statement (Орлогын дэлгэрэнгүй тайлан) ---
INCOME_STATEMENT_HEADERS: dict[str, str] = {
    "борлуулалтын орлого": "revenue",
    "цэвэр борлуулалт": "net_revenue",
    "борлуулалтын өртөг": "cost_of_goods_sold",
    "борлуулсан бүтээгдэхүүний өртөг": "cost_of_goods_sold",
    "нийт ашиг": "gross_profit",
    "түрээсийн орлого": "rental_income",
    "хүүний орлого": "interest_income",
    "ногдол ашгийн орлого": "dividend_income",
    "бусад орлого": "other_income",
    "борлуулалт, маркетингийн зардал": "selling_expenses",
    "борлуулалтын зардал": "selling_expenses",
    "ерөнхий ба удирдлагын зардал": "general_and_admin_expenses",
    "удирдлагын зардал": "admin_expenses",
    "санхүүгийн зардал": "financial_expense",
    "хүүний зардал": "interest_expense",
    "бусад зардал": "other_expenses",
    "гадаад валютын ханшийн зөрүү": "foreign_exchange_gain_loss",
    "татвар төлөхийн өмнөх ашиг": "profit_before_tax",
    "татварын өмнөх ашиг": "profit_before_tax",
    "орлогын татварын зардал": "income_tax_expense",
    "татварын дараахь ашиг": "profit_after_tax",
    "тайлант үеийн цэвэр ашиг": "net_income",
    "цэвэр ашиг": "net_income",
    "орлогын нийт дүн": "total_comprehensive_income",
    "нийт орлого": "total_revenue",
}

# --- Cash Flow Statement (Мөнгөн гүйлгээний тайлан) ---
CASH_FLOW_HEADERS: dict[str, str] = {
    # Operating
    "үндсэн үйл ажиллагааны цэвэр мөнгөн гүйлгээний дүн": "operating_cash_flow",
    "үндсэн үйл ажиллагааны мөнгөн гүйлгээ": "operating_activities_section",
    "үйл ажиллагааны мөнгөн гүйлгээ": "operating_activities_section",
    # Investing
    "хөрөнгө оруулалтын үйл ажиллагааны цэвэр мөнгөн гүйлгээний дүн": "investing_cash_flow",
    "хөрөнгө оруулалтын үйл ажиллагааны мөнгөн гүйлгээ": "investing_activities_section",
    # Financing
    "санхүүгийн үйл ажиллагааны цэвэр мөнгөн гүйлгээний дүн": "financing_cash_flow",
    "санхүүгийн үйл ажиллагааны мөнгөн гүйлгээ": "financing_activities_section",
    "санхүүжилтийн үйл ажиллагааны мөнгөн гүйлгээ": "financing_activities_section",
    # Totals
    "бүх цэвэр мөнгөн гүйлгээ": "net_change_in_cash",
    "мөнгөн хөрөнгийн цэвэр өөрчлөлт": "net_change_in_cash",
    "валютын ханшийн зөрүү": "exchange_rate_effect",
    "мөнгө, түүнтэй адилтгах хөрөнгийн эхний үлдэгдэл": "cash_beginning",
    "мөнгө, түүнтэй адилтгах хөрөнгийн эцсийн үлдэгдэл": "cash_ending",
}

# --- Sheet type detection ---
# Supports both Mongolian-only and hybrid (e.g., "СБД Balance Sheet") names
SHEET_TYPE_PATTERNS: dict[str, str] = {
    # Mongolian patterns
    "баланс": "balance_sheet",
    "санхүүгийн байдлын тайлан": "balance_sheet",
    "санхүү байдлын тайлан": "balance_sheet",
    "сбд": "balance_sheet",
    "орлогын тайлан": "income_statement",
    "орлогын дэлгэрэнгүй тайлан": "income_statement",
    "ашиг алдагдлын тайлан": "income_statement",
    "одт": "income_statement",
    "мөнгөн гүйлгээний тайлан": "cash_flow",
    "мөнгөн гүйлгээ": "cash_flow",
    "мгт": "cash_flow",
    # English patterns (for hybrid sheet names)
    "balance sheet": "balance_sheet",
    "income statement": "income_statement",
    "cash flow": "cash_flow",
}

# Map sheet types to their corresponding header dictionaries
HEADERS_BY_TYPE: dict[str, dict[str, str]] = {
    "balance_sheet": BALANCE_SHEET_HEADERS,
    "income_statement": INCOME_STATEMENT_HEADERS,
    "cash_flow": CASH_FLOW_HEADERS,
}

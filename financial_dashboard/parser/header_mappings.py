"""
Header mapping dictionaries for Mongolian MSE financial statement parsing.

Seven separate dictionaries are used (instead of one merged dict) because each statement type
(standard BS/IS/CF, bank BS/IS, insurance BS/IS) uses entirely different Mongolian terminology.
Merging them would cause false matches where a bank-specific term incorrectly maps to a
standard field in a non-bank company's statement.

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

    # Normalization required: MSE files have inconsistent spacing, capitalization, and trailing
    # whitespace in cell values. Normalizing before lookup prevents missed matches on identical
    # concepts with minor formatting differences.
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

    # Longer patterns checked first: "урт хугацаат зээл" (long-term loans) must match before
    # "зээл" (generic loans). Without length ordering, the shorter pattern would match first,
    # mapping all loan types to the generic field incorrectly.
    for pattern, english_key in sorted(
        headers_dict.items(), key=lambda x: len(x[0]), reverse=True
    ):
        if pattern in normalized:
            return english_key
    return None


# --- Balance Sheet (Санхүүгийн байдлын тайлан / Балансын тайлан) ---
BALANCE_SHEET_HEADERS: dict[str, str] = {
    # Assets
    # Three near-identical keys for cash_and_equivalents: MSE files use comma-space variants and
    # the Mongolian conjunction "ба" variant inconsistently across companies and years.
    # All three must be present to ensure correct mapping regardless of file version.
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

# --- Bank Balance Sheet (Банкны санхүүгийн байдлын тайлан) ---
# Bank-specific items that don't appear in regular company balance sheets.
BANK_BALANCE_SHEET_HEADERS: dict[str, str] = {
    # Loans & receivables
    "зээл ба урьдчилгаа": "total_loans",
    "зээлийн багц": "total_loans",
    "нийт зээл": "total_loans",
    "хэрэглээний зээл": "consumer_loans",
    "ипотекийн зээл": "mortgage_loans",
    "бизнесийн зээл": "business_loans",
    "зээлийн алдагдлын нөөц": "loan_loss_reserves",
    "чанаргүй зээл": "non_performing_loans",
    # Deposits & funding
    "харилцах данс": "demand_deposits",
    "хадгаламж": "savings_deposits",
    "харилцах, хадгаламжийн данс": "total_deposits",
    "нийт хадгаламж": "total_deposits",
    "хугацаатай хадгаламж": "time_deposits",
    # Capital
    "үндсэн капитал": "tier1_capital",
    "1-р зэрэглэлийн капитал": "tier1_capital",
    "нэмэлт капитал": "tier2_capital",
    "2-р зэрэглэлийн капитал": "tier2_capital",
    "нийт хөрөнгийн хүрэлцээний харьцаа": "capital_adequacy_ratio",
    "эрсдэлд жинлэгдсэн хөрөнгө": "risk_weighted_assets",
    # Earning assets
    "үнэт цаас": "investment_securities",
    "хөрөнгө оруулалт": "investment_securities",
    "банк хоорондын байршуулалт": "interbank_placements",
    # Standard items (reuse from regular BS)
    "мөнгө ба түүнтэй адилтгах хөрөнгө": "cash_and_equivalents",
    "мөнгө,түүнтэй адилтгах хөрөнгө": "cash_and_equivalents",
    "нийт хөрөнгийн дүн": "total_assets",
    "нийт хөрөнгө": "total_assets",
    "өр төлбөрийн нийт дүн": "total_liabilities",
    "нийт өр төлбөр": "total_liabilities",
    "эздийн өмчийн дүн": "total_equity",
    "нийт эздийн өмч": "total_equity",
    "хуримтлагдсан ашиг": "retained_earnings",
}

# --- Bank Income Statement (Банкны орлогын тайлан) ---
BANK_INCOME_STATEMENT_HEADERS: dict[str, str] = {
    # Interest
    "хүүний орлого": "interest_income",
    "зээлийн хүүний орлого": "interest_income",
    "нийт хүүний орлого": "interest_income",
    "хүүний зардал": "interest_expense",
    "хадгаламжийн хүүний зардал": "interest_expense",
    "цэвэр хүүний орлого": "net_interest_income",
    # Fee & commission
    "шимтгэлийн орлого": "fee_income",
    "хураамж шимтгэлийн орлого": "fee_income",
    "шимтгэлийн зардал": "fee_expense",
    # Provisions
    "зээлийн алдагдлын нөөцийн зардал": "loan_loss_provision",
    "зээлийн эрсдэлийн нөөц": "loan_loss_provision",
    "нөөцийн зардал": "loan_loss_provision",
    # Operating
    "ерөнхий ба удирдлагын зардал": "admin_expenses",
    "үйл ажиллагааны зардал": "operating_expenses",
    "цалин хөлс": "staff_costs",
    # Trading & other income
    "арилжааны орлого": "trading_income",
    "бусад үйл ажиллагааны орлого": "other_operating_income",
    "бусад орлого": "other_income",
    # Bottom line
    "татвар төлөхийн өмнөх ашиг": "profit_before_tax",
    "орлогын татварын зардал": "income_tax_expense",
    "тайлант үеийн цэвэр ашиг": "net_income",
    "цэвэр ашиг": "net_income",
    "нийт орлого": "total_revenue",
}

# --- Sheet type detection ---
# Supports both Mongolian-only and hybrid (e.g., "СБД Balance Sheet") names
SHEET_TYPE_PATTERNS: dict[str, str] = {
    # MSE uses these Mongolian acronyms as shorthand sheet tab names in some company files:
    # "сбд" = санхүүгийн байдлын дэлгэрэнгүй (detailed balance sheet)
    # "одт" = орлогын дэлгэрэнгүй тайлан (detailed income statement)
    # "мгт" = мөнгөн гүйлгээний тайлан (cash flow statement)
    # Short forms must be matched here — some companies use full names, others abbreviations.
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
    # Bank-specific sheet names
    "банкны санхүүгийн байдлын тайлан": "bank_balance_sheet",
    "банкны баланс": "bank_balance_sheet",
    "банкны орлогын тайлан": "bank_income_statement",
    "банкны ашиг алдагдлын тайлан": "bank_income_statement",
    # Insurance-specific sheet names
    "даатгалын санхүүгийн байдлын тайлан": "insurance_balance_sheet",
    "даатгалын баланс": "insurance_balance_sheet",
    "даатгалын орлогын тайлан": "insurance_income_statement",
    "даатгалын ашиг алдагдлын тайлан": "insurance_income_statement",
    "даатгалын компанийн": "insurance_balance_sheet",
}

# --- Insurance Balance Sheet (Даатгалын компанийн санхүүгийн байдлын тайлан) ---
# Insurance-specific items that don't appear in regular company balance sheets.
INSURANCE_BALANCE_SHEET_HEADERS: dict[str, str] = {
    # Premium receivables
    "даатгалын хураамжийн авлага": "premium_receivables",
    "хураамжийн авлага": "premium_receivables",
    "даатгагчдаас авах авлага": "premium_receivables",
    # Reinsurance assets
    "буцаан даатгалаар хүлээн авах": "reinsurance_receivables",
    "буцаан даатгалын авлага": "reinsurance_receivables",
    "давхар даатгалын авлага": "reinsurance_receivables",
    "буцаан даатгалд шилжүүлсэн нөөц": "reinsurance_share_of_reserves",
    # Investments (insurance float)
    "хөрөнгө оруулалт": "investments",
    "санхүүгийн хөрөнгө оруулалт": "investments",
    "үнэт цаас": "investment_securities",
    "бонд": "bonds",
    "хувьцаанд оруулсан хөрөнгө оруулалт": "equity_investments",
    "хугацаатай хадгаламж": "term_deposits",
    # Deferred acquisition costs
    "хойшлогдсон өртөг олж авах зардал": "deferred_acquisition_costs",
    "хойшлогдсон шимтгэлийн зардал": "deferred_acquisition_costs",
    # Insurance liabilities (reserves)
    "даатгалын нөөц": "insurance_reserves",
    "нэхэмжлэлийн нөөц": "claim_reserves",
    "үл төлөгдсөн нэхэмжлэлийн нөөц": "claim_reserves",
    "нэхэмжлэлийн өр": "claims_payable",
    "хураамжийн нөөц": "premium_reserve",
    "чөлөөлөгдөөгүй хураамжийн нөөц": "unearned_premium_reserve",
    "урьдчилж орсон хураамж": "unearned_premium_reserve",
    "буцаан даатгалын өглөг": "reinsurance_payables",
    "давхар даатгалын өглөг": "reinsurance_payables",
    # Standard items (reuse from regular BS)
    "мөнгө,түүнтэй адилтгах хөрөнгө": "cash_and_equivalents",
    "мөнгө, түүнтэй адилтгах хөрөнгө": "cash_and_equivalents",
    "мөнгө ба түүнтэй адилтгах хөрөнгө": "cash_and_equivalents",
    "бусад авлага": "other_receivables",
    "үндсэн хөрөнгө": "fixed_assets",
    "биет бус хөрөнгө": "intangible_assets",
    "нийт хөрөнгийн дүн": "total_assets",
    "нийт хөрөнгө": "total_assets",
    "өр төлбөрийн нийт дүн": "total_liabilities",
    "нийт өр төлбөр": "total_liabilities",
    "эздийн өмчийн дүн": "total_equity",
    "нийт эздийн өмч": "total_equity",
    "хуримтлагдсан ашиг": "retained_earnings",
    "нэмж төлөгдсөн капитал": "additional_paid_in_capital",
}

# --- Insurance Income Statement (Даатгалын компанийн орлогын тайлан) ---
INSURANCE_INCOME_STATEMENT_HEADERS: dict[str, str] = {
    # Premiums
    "даатгалын хураамжийн орлого": "gross_premiums_written",
    "нийт даатгалын хураамж": "gross_premiums_written",
    "хураамжийн орлого": "gross_premiums_written",
    "цэвэр даатгалын хураамж": "net_premiums_earned",
    "цэвэр хураамжийн орлого": "net_premiums_earned",
    "олсон хураамж": "net_premiums_earned",
    # Reinsurance
    "буцаан даатгалд шилжүүлсэн хураамж": "reinsurance_premiums_ceded",
    "давхар даатгалд шилжүүлсэн хураамж": "reinsurance_premiums_ceded",
    "буцаан даатгалаас хүлээн авсан нэхэмжлэл": "reinsurance_recoveries",
    # Claims
    "нэхэмжлэлийн зардал": "claims_incurred",
    "нэхэмжлэл төлсөн": "claims_paid",
    "төлсөн нэхэмжлэл": "claims_paid",
    "нэхэмжлэл": "claims_incurred",
    "даатгалын нөөцийн өөрчлөлт": "change_in_reserves",
    "нөөцийн өөрчлөлт": "change_in_reserves",
    # Commissions & acquisition
    "шимтгэлийн зардал": "commission_expense",
    "олж авах зардал": "acquisition_costs",
    "брокерийн шимтгэл": "broker_commission",
    # Investment income
    "хөрөнгө оруулалтын орлого": "investment_income",
    "хүүний орлого": "interest_income",
    "ногдол ашгийн орлого": "dividend_income",
    "үнэт цаасны орлого": "securities_income",
    # Operating expenses
    "ерөнхий ба удирдлагын зардал": "admin_expenses",
    "үйл ажиллагааны зардал": "operating_expenses",
    "бусад орлого": "other_income",
    "бусад зардал": "other_expenses",
    # Bottom line
    "татвар төлөхийн өмнөх ашиг": "profit_before_tax",
    "орлогын татварын зардал": "income_tax_expense",
    "тайлант үеийн цэвэр ашиг": "net_income",
    "цэвэр ашиг": "net_income",
    "нийт орлого": "total_revenue",
}

# Map sheet types to their corresponding header dictionaries
HEADERS_BY_TYPE: dict[str, dict[str, str]] = {
    "balance_sheet": BALANCE_SHEET_HEADERS,
    "income_statement": INCOME_STATEMENT_HEADERS,
    "cash_flow": CASH_FLOW_HEADERS,
    "bank_balance_sheet": BANK_BALANCE_SHEET_HEADERS,
    "bank_income_statement": BANK_INCOME_STATEMENT_HEADERS,
    "insurance_balance_sheet": INSURANCE_BALANCE_SHEET_HEADERS,
    "insurance_income_statement": INSURANCE_INCOME_STATEMENT_HEADERS,
}

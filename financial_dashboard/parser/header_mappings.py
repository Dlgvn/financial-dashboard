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
    # ── Structural / label rows — silenced to avoid UNMATCHED warnings ────────
    "үзүүлэлт": "label_column",                              # header row label ("Indicator")
    "хөрөнгө": "assets_section",                             # "ASSETS" section header
    "өр төлбөр": "liabilities_section",                      # "LIABILITIES" section header
    "өөрийн хөрөнгө": "equity_section",                      # "OWN EQUITY" section header
    "өр төлбөр ба өөрийн хөрөнгө": "liabilities_and_equity_section",
    "тэнцлийн гадуурх данс": "off_balance_sheet_section",
    # ── Totals — BoM format uses "өөрийн хөрөнгө" (not "эздийн өмч") ──────────
    # "өр төлбөр ба өөрийн хөрөнгийн дүн" MUST be checked before "өөрийн хөрөнгийн дүн"
    # (longer first), so total_assets doesn't incorrectly consume the equity row.
    "өр төлбөр ба өөрийн хөрөнгийн дүн": "total_assets",   # BoM: grand total (L+E = A)
    "өөрийн хөрөнгийн дүн": "total_equity",                 # BoM: total equity
    "нийт хөрөнгийн дүн": "total_assets",
    "нийт хөрөнгө": "total_assets",
    "өр төлбөрийн нийт дүн": "total_liabilities",
    "нийт өр төлбөр": "total_liabilities",
    "эздийн өмчийн дүн": "total_equity",
    "нийт эздийн өмч": "total_equity",
    # ── Loans — BoM reports net loans in parenthetical form ──────────────────
    "зээл (цэвэр дүнгээр)": "total_loans",                  # BoM: net loans (after reserves)
    "зээл ба урьдчилгаа": "total_loans",
    "зээлийн багц": "total_loans",
    "нийт зээл": "total_loans",
    "харилцагчдад олгосон зээл": "total_loans",
    "олгосон зээлийн дүн": "total_loans",
    "зээлийн нийт дүн": "total_loans",
    "хэрэглээний зээл": "consumer_loans",
    "ипотекийн зээл": "mortgage_loans",
    "бизнесийн зээл": "business_loans",
    # ── NPL sub-categories — BoM breaks loans into 4 quality buckets ─────────
    # хэвийн = normal, хэвийн бус = substandard, эргэлзээтэй = doubtful, муу = bad/loss
    # All three non-normal buckets are summed to NPL in bank_ratios.py.
    "хэвийн зээл": "normal_loans",
    "хэвийн бус зээл": "substandard_loans",
    "эргэлзээтэй зээл": "doubtful_loans",
    "муу зээл": "bad_loans",
    "чанаргүй зээл": "non_performing_loans",               # legacy single-field NPL
    "хугацаа хэтэрсэн зээл": "non_performing_loans",
    "зээлийн хойшлогдсон төлбөр": "deferred_loan_fees",   # deferred origination fees (often negative)
    "зээлд хуримтлуулж тооцсон хүүгийн авлага": "accrued_loan_interest",
    # ── Loan loss reserves — stored as NEGATIVE contra-asset in BoM format ───
    # bank_ratios.py uses abs() before ratio computation.
    "зээлийн эрсдэлийн сан": "loan_loss_reserves",          # BoM: credit risk fund (negative)
    "зээлийн алдагдлын нөөц": "loan_loss_reserves",
    "зээлийн эрсдэлийн нөөц": "loan_loss_reserves",
    "алдагдлын нөөц": "loan_loss_reserves",
    # ── Deposits — BoM liability side ────────────────────────────────────────
    # "харилцах, хадгаламжийн данс" and "харилцах данс" are longer → checked first,
    # so plain "харилцах" only matches the BoM demand-deposit liability row.
    "харилцагчдын хадгаламж": "total_deposits",
    "харилцагчийн хадгаламж": "total_deposits",
    "харилцах, хадгаламжийн данс": "total_deposits",
    "нийт хадгаламж": "total_deposits",
    "харилцах данс": "demand_deposits",
    "харилцах": "total_deposits",                           # BoM: demand deposits (largest bucket)
    "хадгаламж": "savings_deposits",
    "хугацаатай хадгаламж": "time_deposits",
    # ── Capital ───────────────────────────────────────────────────────────────
    "хувь нийлүүлсэн хөрөнгө": "additional_paid_in_capital",  # BoM: paid-in capital
    # ── Investments / earning assets ─────────────────────────────────────────
    # "мөнгөтэй адилтгах хөрөнгө" = T-bills and short bonds held by bank (cash equivalents)
    "мөнгөтэй адилтгах хөрөнгө": "investment_securities",   # BoM: near-cash securities
    "үнэт цаас": "investment_securities",
    "хөрөнгө оруулалт": "investment_securities",
    "банк хоорондын байршуулалт": "interbank_placements",
    "монголбанкинд байршуулсан хөрөнгө": "interbank_placements",
    # ── Interbank placements — various BoM sub-items ─────────────────────────
    # Longer patterns first: "бусад банк, санхүүгийн..." before "банк, санхүүгийн..."
    "бусад банк, санхүүгийн байгууллагад байршуулсан хөрөнгө": "other_interbank_placements",
    "банк, санхүүгийн байгууллагад байршуулсан хөрөнгийн эрсдэлийн сан": "interbank_risk_reserve",
    "банк, санхүүгийн байгууллагад байршуулсан хөрөнгөнд хуримтлуулж тооцсон хүүгийн авлага": "accrued_interest_on_interbank",
    "банк, санхүүгийн байгууллагад байршуулсан хөрөнгө": "interbank_placements",
    "банк, санхүүгийн байгууллагад байршуулсан мөнгө": "interbank_placements",
    "бусад хөрөнгө": "other_assets",
    # ── Cash ─────────────────────────────────────────────────────────────────
    "бэлэн мөнгө": "cash_and_equivalents",                   # BoM: vault cash
    "мөнгө ба түүнтэй адилтгах хөрөнгө": "cash_and_equivalents",
    "мөнгө,түүнтэй адилтгах хөрөнгө": "cash_and_equivalents",
    "мөнгө, түүнтэй адилтгах хөрөнгө": "cash_and_equivalents",
    "мөнгө, түүнтэй адилтгах хөрөнгийн дүн": "cash_and_equivalents",
    "мөнгөн хөрөнгөнд хуримтлуулж тооцсон хүүгийн авлага": "accrued_interest_receivable",
    # ── Other asset sub-items ─────────────────────────────────────────────────
    "дериватив санхүүгийн хөрөнгө": "derivative_assets",
    "банк, салбар хоорондын тооцоо": "interbank_settlements",
    "өмчлөх бусад хөрөнгө (цэвэр дүнгээр)": "other_repossessed_assets",
    "бусад санхүүгийн хөрөнгө": "other_financial_assets",
    "бусад санхүүгийн бус хөрөнгө": "other_non_financial_assets",
    "бусад тооцоо": "other_receivables",
    "бараа материал, үнэ бүхий зүйл": "inventory",
    "үнэт металл (цэвэр дүнгээр)": "precious_metals",
    "татварын авлага": "tax_receivable",
    "хойшлогдсон татварын хөрөнгө": "deferred_tax_asset",
    "борлуулах зориулалттай хөрөнгө": "assets_held_for_sale",
    "биет бус хөрөнгө": "intangible_assets",
    "үндсэн хөрөнгө": "fixed_assets",
    "бусад": "other",
    # ── Funding / borrowings ──────────────────────────────────────────────────
    # Longer patterns first to avoid partial matches
    "банк, санхүүгийн байгууллагаас татсан эх үүсвэрт хуримтлуулж тооцсон хүүгийн өглөг": "accrued_interest_on_borrowings",
    "банк, санхүүгийн байгууллагаас татсан эх үүсвэр": "bank_borrowings",
    "бусад эх үүсвэрт хуримтлуулж тооцсон хүүгийн өглөг": "accrued_interest_on_other_funding",
    "бусад эх үүсвэрийн хойшлогдсон төлбөр": "deferred_other_funding",
    "эх үүсвэрийн хойшлогдсон төлбөр": "deferred_funding_costs",
    "бусад эх үүсвэр": "other_funding",
    "банкнаас гаргасан өрийн бичиг": "bonds_issued",
    "төслийн зээлийн санхүүжилт": "project_financing",
    "хамтын зээлжүүлэлтийн эх үүсвэр": "syndicated_loans",
    # ── Other liability sub-items ─────────────────────────────────────────────
    "дериватив санхүүгийн өр төлбөр": "derivative_liabilities",
    "бусад санхүүгийн өр төлбөр": "other_financial_liabilities",
    "бусад санхүүгийн бус өр төлбөр": "other_non_financial_liabilities",
    "хоёрдогч өглөг": "subordinated_debt",
    "давуу эрхийн хувьцаа (өр төлбөр)": "preferred_shares_liability",
    # ── Equity components ─────────────────────────────────────────────────────
    "давуу эрхийн хувьцаа": "preferred_shares",
    "энгийн хувьцаа": "common_shares",
    "халаасны хувьцаа": "treasury_shares",
    "дахин үнэлгээний нэмэгдэл": "revaluation_surplus",
    "бусад өөрийн хөрөнгө": "other_equity",
    "хувьцааны опцион": "stock_options",
    "нөөцийн сан": "reserve_fund",
    "гадаад валютын хөрвүүлэлтийн нөөц": "fx_translation_reserve",
    "эрсдэлийн сангийн нөөц": "risk_reserve_fund",
    "нийгмийн хөгжлийн сан": "social_development_fund",
    "хувьцаанд хөрвөх эх үүсвэр (өөрийн хөрөнгө)": "convertible_equity",
    "хейджийн хэрэгслийн дахин үнэлгээний сан": "hedge_revaluation_fund",
    # ── Off-balance sheet ────────────────────────────────────────────────────
    "зээл, зээлтэй адилтгах хөрөнгөд хамаарах үүрэг (цэвэр дүнгээр)": "contingent_loan_commitments",
    # ── Other standard items ──────────────────────────────────────────────────
    "хуримтлагдсан ашиг": "retained_earnings",
    "нэмж төлөгдсөн капитал": "additional_paid_in_capital",
}

# --- Bank Income Statement (Банкны орлогын тайлан) ---
BANK_INCOME_STATEMENT_HEADERS: dict[str, str] = {
    # ── Sub-item disambiguation (MUST come before total-row patterns) ─────────
    # BoM IS embeds partial sub-item labels that contain the same phrase as the
    # total row. Longer patterns are checked first, so these sub-items get
    # mapped to other_income / other_expenses rather than overwriting the totals.
    "бусад хүүгийн орлого": "other_income",                # sub-item of interest income
    "бусад хүүгийн зардал": "other_expenses",              # sub-item of interest expense
    "зээлийн хүүгийн зардал": "other_expenses",            # sub-item: loan funding cost
    "үнэт цаасны хүүгийн зардал": "other_expenses",        # sub-item: bond funding cost
    "бусад хүүгийн бус орлого": "other_income",            # sub-item of non-interest income
    "бусад эрсдэлийн сангийн зардал": "other_expenses",    # sub-item of provision expense
    "үйл ажиллагааны бусад зардал": "operating_expenses",  # BoM: other operating costs
    # ── Interest income / expense — BoM uses "хүүгийн" (-гийн), not "хүүний" (-ний) ──
    "нийт хүүний орлого": "interest_income",               # legacy variant
    "зээлийн хүүний орлого": "interest_income",
    "хүүний орлого": "interest_income",
    "хүүгийн орлого": "interest_income",                   # BoM: total interest income
    "хүүний зардал": "interest_expense",
    "хадгаламжийн хүүний зардал": "interest_expense",
    "нийт хүүний зардал": "interest_expense",
    "хүүгийн зардал": "interest_expense",                  # BoM: total interest expense
    # ── Net Interest Income ───────────────────────────────────────────────────
    # BoM labels NII as "ЦЭВЭР ХҮҮГИЙН ОРЛОГО(1-2)"; after normalization the
    # pattern "цэвэр хүүгийн орлого" matches it as a substring.
    "цэвэр хүүгийн орлого": "net_interest_income",         # BoM: NII (also matches uppercase form)
    "хүүний цэвэр орлого": "net_interest_income",
    "цэвэр хүүний орлого": "net_interest_income",
    # ── Loan loss provision ───────────────────────────────────────────────────
    "эрсдэлийн сангийн зардал": "loan_loss_provision",     # BoM: credit risk fund expense
    "зээлийн алдагдлын нөөцийн зардал": "loan_loss_provision",
    "зээлийн эрсдэлийн нөөцийн зардал": "loan_loss_provision",
    "алдагдлын нөөцийн зардал": "loan_loss_provision",
    "зээлийн эрсдэлийн нөөц": "loan_loss_provision",
    "нөөцийн зардал": "loan_loss_provision",
    # ── Non-interest income / expense (fee_income used for Non-Interest Income Ratio) ──
    "хүүгийн бус орлого": "fee_income",                    # BoM: total non-interest income
    "хүүгийн бус зардал": "operating_expenses",            # BoM: total non-interest expense
    # ── Fee & commission ─────────────────────────────────────────────────────
    "шимтгэлийн цэвэр орлого": "fee_income",
    "цэвэр шимтгэлийн орлого": "fee_income",
    "нийт шимтгэлийн орлого": "fee_income",
    "хураамж шимтгэлийн орлого": "fee_income",
    "шимтгэлийн орлого": "fee_income",
    "шимтгэлийн зардал": "fee_expense",
    # ── Admin / operating expenses ────────────────────────────────────────────
    "ерөнхий ба удирдлагын зардал": "admin_expenses",
    "үйл ажиллагааны зардал": "operating_expenses",
    "нийт үйл ажиллагааны зардал": "operating_expenses",
    "цалин хөлс": "staff_costs",
    "ажиллагсдын зардал": "staff_costs",
    # ── Trading & other income ────────────────────────────────────────────────
    "арилжааны орлого": "trading_income",
    "гадаад валютын арилжааны орлого": "trading_income",
    "бусад үйл ажиллагааны орлого": "other_operating_income",
    "бусад орлого": "other_income",
    # ── Total operating income (Cost-to-Income denominator) ───────────────────
    "нийт үйл ажиллагааны орлого": "total_revenue",
    "банкны орлогын нийт дүн": "total_revenue",
    "нийт орлого": "total_revenue",
    "орлогын нийт дүн": "total_revenue",
    # ── Interest income sub-items (breakdown rows, not used in ratios) ────────
    # These appear as sub-items under "хүүгийн орлого" in BoM IS format.
    "монголбанкинд байршуулсан хөрөнгийн хүү": "other_income",       # interest on BoM placements
    "банк, санхүүгийн байгууллагад байршуулсан хөрөнгийн хүү": "other_income",
    "үнэт цаасны хүүгийн орлого": "other_income",                     # securities interest sub-item
    "зээлийн хүүгийн орлого": "other_income",                         # loan interest sub-item
    # ── Interest expense sub-items ────────────────────────────────────────────
    "харилцахад төлсөн хүү": "other_expenses",                        # interest on demand deposits
    "хадгаламжинд төлсөн хүү": "other_expenses",                      # interest on savings deposits
    # ── FX / valuation adjustment ─────────────────────────────────────────────
    "ханш, үнэлгээний тэгшитгэлийн орлого": "trading_income",
    "ханш, үнэлгээний тэгшитгэлийн зардал": "trading_expenses",
    "арилжааны зардал": "trading_expenses",
    "бусад зардал, гарз": "other_expenses",
    # ── Net income after provisions (intermediate subtotal row) ───────────────
    "эрсдэлийн сангийн дараах цэвэр орлого": "net_income_after_provisions",
    # ── Other comprehensive income / OCI section ──────────────────────────────
    "бусад дэлгэрэнгүй орлого": "other_comprehensive_income",
    "үндсэн хөрөнгө ба биет бус хөрөнгийн дахин үнэлгээний нэмэгдэл дансны өсөлт, бууралт": "fixed_asset_revaluation_change",
    "борлуулахад бэлэн үнэт цаасны дахин үнэлгээний өсөлт, бууралт": "afs_securities_revaluation_change",
    "ханш, үнэлгээний тэгшитгэлийн сангийн өсөлт, бууралт": "fx_reserve_change",
    "эрсдэлийн сангийн нөөцийн өсөлт, бууралт": "risk_reserve_change",
    "нийгмийн хөгжлийн сан": "social_development_fund",
    "зогсоосон үйл ажиллагааны цэвэр орлого, зардал": "discontinued_operations",
    "бусад зардал": "other_expenses",
    "бусад": "other",
    # ── Bottom line ───────────────────────────────────────────────────────────
    # BoM bottom line is "Тайлант хугацааны нийт дэлгэрэнгүй орлогын дүн" (total
    # comprehensive income); there is no separate "татварын дараах ашиг" row.
    "тайлант хугацааны нийт дэлгэрэнгүй орлогын дүн": "net_income",  # BoM: total comp. income
    "татвар төлөхийн өмнөх ашиг": "profit_before_tax",
    "татварын өмнөх ашиг": "profit_before_tax",
    "орлогын татварын зардал": "income_tax_expense",
    "татварын зардал": "income_tax_expense",
    "татварын дараах ашиг": "net_income",
    "тайлант үеийн цэвэр ашиг": "net_income",
    "цэвэр ашиг": "net_income",
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
}

# --- Insurance Balance Sheet (Даатгалын компанийн санхүүгийн байдлын тайлан) ---
# Insurance-specific items that don't appear in regular company balance sheets.
INSURANCE_BALANCE_SHEET_HEADERS: dict[str, str] = {
    # ── Structural / label rows ───────────────────────────────────────────────
    "үзүүлэлт": "label_column",
    "хөрөнгө": "assets_section",
    "өр төлбөр ба эздийн өмч": "liabilities_and_equity_section",
    "өр төлбөр": "liabilities_section",
    "эздийн өмч": "equity_section",
    # ── Cash / bank assets ────────────────────────────────────────────────────
    "мөнгө, түүнтэй адилтгах хөрөнгийн дүн": "cash_and_equivalents",  # FRC: cash total row
    "мөнгө,түүнтэй адилтгах хөрөнгө": "cash_and_equivalents",
    "мөнгө, түүнтэй адилтгах хөрөнгө": "cash_and_equivalents",
    "мөнгө ба түүнтэй адилтгах хөрөнгө": "cash_and_equivalents",
    "бэлэн мөнгө": "cash_and_equivalents",
    "харилцахад байгаа мөнгө": "cash_at_bank",                         # FRC: money in bank accounts
    "банк санхүүгийн байгууллагад байршуулсан хөрөнгө": "interbank_placements",
    "мөнгөн хөрөнгөнд хуримтлуулж тооцсон хүүний авлага": "accrued_interest_receivable",
    # ── Premium receivables ───────────────────────────────────────────────────
    "даатгалын авлагын дүн": "total_insurance_receivables",            # FRC: total insurance receivables
    "даатгалын хураамжийн авлага": "premium_receivables",
    "хураамжийн авлага": "premium_receivables",
    "даатгагчдаас авах авлага": "premium_receivables",
    "даатгалын авлага": "premium_receivables",
    "буруутай этгээдээс авах авлага": "subrogation_receivable",        # recovery from liable parties
    "давхар даатгалаас авах авлага": "reinsurance_receivables",
    # ── Reinsurance assets ────────────────────────────────────────────────────
    # Longer patterns first
    "нөхөн төлбөрийн нөөцийн сангийн давхар даатгагчид ногдох хэсэг": "reinsurance_share_of_reserves",
    "хойшлогдсон давхар даатгалын хураамж": "deferred_reinsurance_premium",
    "буцаан даатгалаар хүлээн авах": "reinsurance_receivables",
    "буцаан даатгалын авлага": "reinsurance_receivables",
    "давхар даатгалын авлага": "reinsurance_receivables",
    "буцаан даатгалд шилжүүлсэн нөөц": "reinsurance_share_of_reserves",
    "даатгалын хөрөнгө": "insurance_assets_section",
    # ── Other financial assets ────────────────────────────────────────────────
    "бусад санхүүгийн хөрөнгийн дүн": "total_other_financial_assets",
    "бусад санхүүгийн хөрөнгө": "other_financial_assets",
    "дериватив санхүүгийн хэрэглүүр": "derivative_assets",
    # ── Other non-financial assets ────────────────────────────────────────────
    "бусад санхүүгийн бус  хөрөнгийн дүн": "total_other_non_financial_assets",  # double-space variant
    "бусад санхүүгийн бус хөрөнгийн дүн": "total_other_non_financial_assets",
    "бусад санхүүгийн бус хөрөнгө": "other_non_financial_assets",
    "ндш авлага, бусад татварын авлага": "tax_receivable",
    "ааноататварын авлага": "corporate_tax_receivable",               # "ААНОАТ" = corporate income tax
    "хойшлогдсон татварын хөрөнгө": "deferred_tax_asset",
    "бараа материал": "inventory",
    "урьдчилж төлсөн зардал/тооцоо": "prepaid_expenses",
    "урьдчилж төлсөн зардал": "prepaid_expenses",
    "өмчлөх бусад хөрөнгө": "other_repossessed_assets",
    # ── Investments (insurance float) ─────────────────────────────────────────
    "хөрөнгө оруулалт": "investments",
    "санхүүгийн хөрөнгө оруулалт": "investments",
    "үнэт цаас": "investment_securities",
    "бонд": "bonds",
    "хувьцаанд оруулсан хөрөнгө оруулалт": "equity_investments",
    "хугацаатай хадгаламж": "term_deposits",
    "хадгаламж, хадгаламжийн сертификат": "term_deposits",           # FRC: deposit investments
    # ── Deferred acquisition costs ────────────────────────────────────────────
    "хойшлогдсон өртөг олж авах зардал": "deferred_acquisition_costs",
    "хойшлогдсон шимтгэлийн зардал": "deferred_acquisition_costs",
    # ── Fixed / intangible assets ────────────────────────────────────────────
    "үндсэн хөрөнгө": "fixed_assets",
    "биет бус хөрөнгө": "intangible_assets",
    # ── Insurance liabilities (reserves) ─────────────────────────────────────
    # Longer patterns first
    "нөхөн төлбөрийн нөөц сангийн дүн": "claim_reserves",            # FRC: total claims reserve
    "учирсан боловч мэдэгдээгүй хохирлын нөөц сан": "ibnr_reserve",  # IBNR
    "мэдсэн боловч төлөөгүй хохирлын нөөц сан": "rbns_reserve",      # RBNS
    "учирч болзошгүй хохирлын нөөц сан": "ulae_reserve",             # contingent loss reserve
    "нөхөн төлбөрийн нөөц сан": "claim_reserves",
    "даатгалын нөөц": "insurance_reserves",
    "нэхэмжлэлийн нөөц": "claim_reserves",
    "үл төлөгдсөн нэхэмжлэлийн нөөц": "claim_reserves",
    "нэхэмжлэлийн өр": "claims_payable",
    "хураамжийн нөөц": "premium_reserve",
    "чөлөөлөгдөөгүй хураамжийн нөөц": "unearned_premium_reserve",
    "урьдчилж орсон хураамж": "unearned_premium_reserve",
    # ── Insurance payables ────────────────────────────────────────────────────
    "даатгалын өглөгийн дүн": "total_insurance_payables",
    "даатгалын хураамжийн буцаалтын өглөг": "premium_refund_payable",
    "нөхөн төлбөрийн өглөг": "claims_payable",
    "даатгалын гэрээний шимтгэлийн өглөг": "contract_commission_payable",
    "давхар даатгагчид өгөх өглөг": "reinsurance_payables",
    "буцаан даатгалын өглөг": "reinsurance_payables",
    "давхар даатгалын өглөг": "reinsurance_payables",
    "даатгалын өглөг": "insurance_payables_section",
    # ── Other financial liabilities ───────────────────────────────────────────
    "бусад санхүүгийн өр төлбөрийн дүн": "total_other_financial_liabilities",
    "бусад санхүүгийн өр төлбөр": "other_financial_liabilities",
    "зээлийн өглөг, хүү": "loan_payable_with_interest",
    "өрийн бичиг, хүү": "bonds_payable_with_interest",
    "санхүүгийн түрээсийн өр төлбөр": "finance_lease_liability",
    "ногдол ашгийн өглөг": "dividends_payable",
    "деривативын өр төлбөр": "derivative_liabilities",
    "бусад өр төлбөр": "other_liabilities",
    # ── Other non-financial liabilities ──────────────────────────────────────
    "бусад санхүүгийн бус өр төлбөрийн дүн": "total_other_non_financial_liabilities",
    "бусад санхүүгийн бус өр төлбөр": "other_non_financial_liabilities",
    "цалингийн өглөг": "salaries_payable",
    "ндш-ийн өглөг": "social_insurance_payable",
    "ааноататварын өглөг": "corporate_tax_payable",
    "хойшлогдсон татварын өглөг": "deferred_tax_liability",
    "урьдчилж орсон орлого": "unearned_revenue",
    "нийгмийн хөгжлийн сангийн өр төлбөр": "social_development_fund_liability",
    "хуулийн байууллагаар шийдэгдэж байгаа зүйлсийн өр төлбөр": "legal_proceedings_liability",
    "мөнгөөр төлөгдөх хувьцааны опцион": "cash_settled_stock_options",
    "тэтгэврийн сангийн өр төлбөр": "pension_fund_liability",
    "санхүүгийн түрээсийн хэрэгжээгүй орлого": "unearned_finance_lease_income",
    "хоёрдогч өглөг, хүү": "subordinated_debt_with_interest",
    "давуу эрхийн хувьцаа (хөрвөхгүй)": "non_convertible_preferred_shares",
    # ── Equity components ─────────────────────────────────────────────────────
    "эзэмшигчдийн өмч": "shareholders_equity",
    "тогтвортой байдлын сан": "stability_fund",
    "хөрөнгийн дахин үнэлгээний нэмэгдэл": "revaluation_surplus",
    "гадаад валютын хөрвүүлэлтийн нөөц": "fx_translation_reserve",
    "эздийн өмчийн бусад хэсэг": "other_equity_components",
    # ── Totals ───────────────────────────────────────────────────────────────
    "даатгалын хөрөнгийн дүн": "total_assets",                       # FRC: total insurance assets
    "нийт хөрөнгийн дүн": "total_assets",
    "нийт хөрөнгө": "total_assets",
    "өр төлбөрийн нийт дүн": "total_liabilities",
    "нийт өр төлбөр": "total_liabilities",
    "эздийн өмчийн дүн": "total_equity",
    "нийт эздийн өмч": "total_equity",
    "хуримтлагдсан ашиг": "retained_earnings",
    "нэмж төлөгдсөн капитал": "additional_paid_in_capital",
    "бусад авлага": "other_receivables",
}

# --- Insurance Income Statement (Даатгалын компанийн орлогын тайлан) ---
INSURANCE_INCOME_STATEMENT_HEADERS: dict[str, str] = {
    # Premiums — gross written
    "даатгалын хураамжийн орлого": "gross_premiums_written",
    "нийт даатгалын хураамж": "gross_premiums_written",
    "хураамжийн орлого": "gross_premiums_written",
    # Premiums — earned / net (FRC format uses "нөхөн төлбөр" terminology)
    "орлогод тооцсон хураамж": "net_premiums_earned",       # earned premium (FRC IS line 6)
    "даатгалын хураамжийн цэвэр орлого": "net_premiums_earned",  # net premium income
    "цэвэр даатгалын хураамж": "net_premiums_earned",
    "цэвэр хураамжийн орлого": "net_premiums_earned",
    "олсон хураамж": "net_premiums_earned",
    # Reinsurance
    "давхар даатгалын хураамжийн зардал": "reinsurance_premiums_ceded",  # FRC: reinsurance cost
    "буцаан даатгалд шилжүүлсэн хураамж": "reinsurance_premiums_ceded",
    "давхар даатгалд шилжүүлсэн хураамж": "reinsurance_premiums_ceded",
    "буцаан даатгалаас хүлээн авсан нэхэмжлэл": "reinsurance_recoveries",
    "давхар даатгалын шимтгэлийн орлого": "reinsurance_recoveries",      # FRC: reinsurance commission income
    # Claims — FRC format uses "нөхөн төлбөр" (compensation), not "нэхэмжлэл" (claim request)
    "зардалд тооцсон нөхөн төлбөр": "claims_incurred",      # FRC IS: net actuarial claims charged to expense
    "нөхөн төлбөрийн цэвэр зардал": "claims_incurred",      # FRC IS: net claims expense (after reinsurance)
    "нийт нөхөн төлбөрийн зардал": "claims_paid",           # FRC IS: gross claims paid
    "нэхэмжлэлийн зардал": "claims_incurred",               # legacy term (some older files)
    "нэхэмжлэл төлсөн": "claims_paid",
    "төлсөн нэхэмжлэл": "claims_paid",
    "нэхэмжлэл": "claims_incurred",
    # Change in reserves
    "нөхөн төлбөрийн нөөцийн сангийн өөрчлөлт": "change_in_reserves",  # FRC: claims reserve movement
    "даатгалын нөөцийн өөрчлөлт": "change_in_reserves",
    "нөөцийн өөрчлөлт": "change_in_reserves",
    # Commissions & acquisition
    "даатгалын гэрээний зардал": "commission_expense",       # FRC: insurance contract expense (acquisition)
    "шимтгэлийн зардал": "commission_expense",
    "олж авах зардал": "acquisition_costs",
    "брокерийн шимтгэл": "broker_commission",
    # Investment income
    "хөрөнгө оруулалтын орлого": "investment_income",
    "хүүний орлого": "interest_income",
    "ногдол ашгийн орлого": "dividend_income",
    "үнэт цаасны орлого": "securities_income",
    # Operating expenses
    "борлуулалт, маркетингийн зардал": "selling_expenses",  # FRC IS: sales & marketing
    "ерөнхий ба удирдлагын зардал": "admin_expenses",
    "үйл ажиллагааны зардал": "operating_expenses",
    "санхүүгийн зардал": "financial_expense",               # FRC IS: financial costs
    "бусад орлого": "other_income",
    "бусад зардал": "other_expenses",
    # ── Label rows ────────────────────────────────────────────────────────────
    "үзүүлэлт": "label_column",
    "даатгалын үйл ажиллагаа": "insurance_operations_section",
    # ── Insurance operations sub-items ───────────────────────────────────────
    # FRC IS uses these specific breakdown rows under insurance operating result
    "даатгалын үйл ажиллагааны ашиг(алдагдал)(6-11-12+13+14)": "insurance_operating_profit",
    "даатгалын үйл ажиллагааны ашиг": "insurance_operating_profit",
    "хойшлуулсан давхар даатгалын хураамжийн өөрчлөлт": "change_in_deferred_reinsurance",
    "нөхөн төлбөрийн нөөцийн сангийн давхар даатгагчид ногдох хэсгийн өөрчлөлт": "reinsurance_share_reserve_change",
    "учирч болзошгүй хохирлын нөөцийн сангийн өөрчлөлт": "contingent_reserve_change",
    "давхар даатгагчийн хариуцсан нөхөн төлбөр": "reinsurance_recoveries",
    "буруутай этгээдээс авах нөхөн төлбөр": "subrogation_recoveries",
    "даатгалын хураамжийн буцаалт": "premium_refund",
    # ── Other income items ────────────────────────────────────────────────────
    "түрээсийн орлого": "rental_income",
    "эрхийн шимтгэлийн орлого": "license_fee_income",
    "гадаад вальютийн ханшийн зөрүүний олз(гарз)": "fx_gain_loss",   # "вальют" spelling variant
    "гадаад валютын ханшийн зөрүү": "fx_gain_loss",
    "биет бус хөрөнгө данснаас хассаны олз(гарз)": "intangible_disposal_gain_loss",
    "бусад ашиг алдагдал": "other_profit_loss",
    # ── OCI / equity movements ────────────────────────────────────────────────
    "хөрөнгийн дахин үнэлгээний нэмэгдлийн зөрүү": "revaluation_surplus_change",
    "гадаад вальютын хөрвүүлэлтийн зөрүү": "fx_translation_change",
    "бусад олз(гарз)": "other_gains_losses",
    # ── EPS ───────────────────────────────────────────────────────────────────
    "нэгж хувьцаанд ногдох суурь ашиг(алдагдал)": "basic_eps",
    # ── Bottom line — FRC uses "татварын дараах" (without "хь" suffix used in standard IS)
    "татвар төлөхийн өмнөх ашиг": "profit_before_tax",
    "орлогын татварын зардал": "income_tax_expense",
    "татварын дараах ашиг": "net_income",                   # FRC: profit after tax (алдагдал variant)
    "тайлант үеийн цэвэр ашиг": "net_income",
    "цэвэр ашиг": "net_income",
    "орлогын нийт дүн": "total_comprehensive_income",       # FRC: total comprehensive income
    "нийт орлого": "total_revenue",
}

# --- Securities / Investment Company Balance Sheet (FRC format) ---
# Securities brokers, investment companies, and holding companies that file under the
# Financial Regulatory Commission (FRC) format.  These firms use standard Mongolian
# balance sheet terminology (like BALANCE_SHEET_HEADERS) but also hold large investment
# securities portfolios and use broker-specific receivable/payable terminology.
# This dict is a superset of BALANCE_SHEET_HEADERS with additional securities-specific terms.
SECURITIES_BALANCE_SHEET_HEADERS: dict[str, str] = {
    # ── Investment securities — PRIMARY earning asset (MUST come before "хөрөнгө") ──
    # FRC standard format labels the securities portfolio "Санхүүгийн хөрөнгө"
    # ("Financial assets").  This is a CURRENT asset for broker-dealers holding
    # client securities and their own trading book.
    # "санхүүгийн хөрөнгө" (18 chars) > "хөрөнгө" (7 chars) — checked first,
    # prevents the short "хөрөнгө" pattern from consuming this 28B+ asset row.
    "санхүүгийн хөрөнгө оруулалтын зориулалттай үл хөдлөх хөрөнгө": "other_non_financial_assets",
    "санхүүгийн хөрөнгө оруулалт": "investment_securities",
    "санхүүгийн хөрөнгө": "investment_securities",
    # ── Standard BS items (duplicated from BALANCE_SHEET_HEADERS) ────────────
    "мөнгө,түүнтэй адилтгах хөрөнгө": "cash_and_equivalents",
    "мөнгө, түүнтэй адилтгах хөрөнгө": "cash_and_equivalents",
    "мөнгө ба түүнтэй адилтгах хөрөнгө": "cash_and_equivalents",
    "бэлэн мөнгө": "cash_and_equivalents",
    "мөнгө, түүнтэй адилтгах хөрөнгийн дүн": "cash_and_equivalents",
    "дансны авлага": "accounts_receivable",
    "татвар, ндш – ийн авлага": "tax_receivable",
    "татварын авлага": "tax_receivable",
    "бусад авлага": "other_receivables",
    "урьдчилж төлсөн зардал": "prepaid_expenses",
    "бараа материал": "inventory",
    "бусад эргэлтийн хөрөнгийн дүн": "total_current_assets",
    "эргэлтийн хөрөнгийн дүн": "total_current_assets",
    "эргэлтийн хөрөнгө": "current_assets_section",
    "үндсэн хөрөнгө": "fixed_assets",
    "биет бус хөрөнгө": "intangible_assets",
    "хойшлогдсон татварын хөрөнгө": "deferred_tax_asset",
    "бусад эргэлтийн бус хөрөнгийн дүн": "total_non_current_assets",
    "эргэлтийн бус хөрөнгийн дүн": "total_non_current_assets",
    "эргэлтийн бус хөрөнгө": "non_current_assets_section",
    "нийт хөрөнгийн дүн": "total_assets",
    "нийт хөрөнгө": "total_assets",
    "дансны өглөг": "accounts_payable",
    "цалингийн өглөг": "salaries_payable",
    "татварын өр": "taxes_payable",
    "ндш - ийн өглөг": "social_security_payable",
    "хүүний өглөг": "interest_payable",
    "ногдол ашгийн өглөг": "dividends_payable",
    "урьдчилж орсон орлого": "unearned_revenue",
    "богино хугацаат өр төлбөрийн дүн": "total_current_liabilities",
    "богино хугацаат зээл": "short_term_loans",
    "урт хугацаат зээл": "long_term_loans",
    "хойшлогдсон татварын өр": "deferred_tax_liability",
    "урт хугацаат өр төлбөрийн дүн": "total_non_current_liabilities",
    "өр төлбөрийн нийт дүн": "total_liabilities",
    "нийт өр төлбөр": "total_liabilities",
    "нэмж төлөгдсөн капитал": "additional_paid_in_capital",
    "хуримтлагдсан ашиг": "retained_earnings",
    "хуваарилагдаагүй ашиг": "retained_earnings",
    "эздийн өмчийн дүн": "total_equity",
    "нийт эздийн өмч": "total_equity",
    "эздийн өмч": "total_equity",
    "өр төлбөр ба эздийн өмчийн дүн": "total_liabilities_and_equity",
    # ── Structural label rows (silenced) ──────────────────────────────────────
    "үзүүлэлт": "label_column",
    "хөрөнгө": "assets_section",
    "өр төлбөр": "liabilities_section",
    # ── Investment securities — primary earning asset for securities firms ────
    # FRC format uses various labels; longer patterns checked first.
    "хувьцаа, үнэт цаасны хөрөнгө оруулалт": "investment_securities",
    "үнэт цаасны хөрөнгө оруулалт": "investment_securities",
    "санхүүгийн хөрөнгө оруулалт": "investment_securities",
    "урт хугацаат хөрөнгө оруулалт": "long_term_investments",
    "хөрөнгө оруулалт": "investment_securities",
    "үнэт цаас": "investment_securities",
    "бонд": "investment_securities",
    # ── Broker receivables / client accounts ─────────────────────────────────
    # Securities brokers hold client funds and securities on behalf of clients.
    # These map to other_financial_assets so the loan_portfolio proxy can use them.
    "үйлчлүүлэгчдийн үнэт цаасны авлага": "other_financial_assets",
    "үйлчлүүлэгчдийн авлага": "other_financial_assets",
    "брокерийн авлага": "other_financial_assets",
    "зуучлалын авлага": "other_financial_assets",
    "үнэт цаасны арилжааны авлага": "other_financial_assets",
    "санхүүгийн авлага": "other_financial_assets",
    "бусад санхүүгийн хөрөнгө": "other_financial_assets",
    # ── Interbank / bank placements ───────────────────────────────────────────
    "банк санхүүгийн байгууллагад байршуулсан хөрөнгө": "interbank_placements",
    "банкинд байршуулсан хөрөнгө": "interbank_placements",
    # ── Debt funding ──────────────────────────────────────────────────────────
    "банкнаас авсан зээл": "bank_borrowings",
    "банк санхүүгийн байгууллагаас авсан зээл": "bank_borrowings",
    "гаргасан өрийн бичиг": "bonds_issued",
    "өрийн бичиг": "bonds_issued",
    "бусад санхүүгийн өр төлбөр": "other_financial_liabilities",
    # ── Client accounts payable (broker liabilities) ──────────────────────────
    "үйлчлүүлэгчдийн данс": "other_financial_liabilities",
    "харилцагчийн данс": "other_financial_liabilities",
    "брокерийн өглөг": "other_financial_liabilities",
    "үнэт цаасны арилжааны өглөг": "other_financial_liabilities",
    # ── Other assets ─────────────────────────────────────────────────────────
    "бусад санхүүгийн бус хөрөнгө": "other_non_financial_assets",
    "бусад эргэлтийн хөрөнгө": "other_current_assets",
    "борлуулах зорилгоор эзэмшиж буй эргэлтийн бус хөрөнгө": "assets_held_for_sale",
    # ── Equity components ────────────────────────────────────────────────────
    "хөрөнгийн дахин үнэлгээний нэмэгдэл": "revaluation_surplus",
    "гадаад валютын хөрвүүлэлтийн нөөц": "fx_translation_reserve",
    "эздийн өмчийн бусад хэсэг": "other_equity",
    "халаасны хувьцаа": "treasury_shares",
    # ── Silence equity sub-items (ownership breakdown rows) ──────────────────
    # FRC standard BS splits equity into state / private / joint-stock ownership
    # sub-lines.  These are sub-items of paid-in capital, not separate equity totals.
    "өмч -төрийн": "label_column",
    "-хувийн": "label_column",
    "-хувьцаат": "label_column",
    # ── Contingency reserves (current liability sub-item) ─────────────────────
    "нөөц /өр төлбөр/": "other_current_liabilities",
    "бусад богино хугацаат өр төлбөр": "other_current_liabilities",
    "бусад": "other",
}

# --- Securities / Investment Company Income Statement (FRC format) ---
# Superset of INCOME_STATEMENT_HEADERS with securities-specific income line items.
SECURITIES_INCOME_STATEMENT_HEADERS: dict[str, str] = {
    # ── Standard IS items (duplicated from INCOME_STATEMENT_HEADERS) ──────────
    "борлуулалтын орлого": "revenue",
    "цэвэр борлуулалт": "net_revenue",
    "борлуулалтын өртөг": "cost_of_goods_sold",
    "борлуулсан бүтээгдэхүүний өртөг": "cost_of_goods_sold",
    "нийт ашиг": "gross_profit",
    "түрээсийн орлого": "rental_income",
    "ногдол ашгийн орлого": "dividend_income",
    "гадаад валютын ханшийн зөрүү": "foreign_exchange_gain_loss",
    "татвар төлөхийн өмнөх ашиг": "profit_before_tax",
    "татварын өмнөх ашиг": "profit_before_tax",
    "орлогын татварын зардал": "income_tax_expense",
    "татварын дараахь ашиг": "profit_after_tax",
    "тайлант үеийн цэвэр ашиг": "net_income",
    "цэвэр ашиг": "net_income",
    "орлогын нийт дүн": "total_comprehensive_income",
    "нийт орлого": "total_revenue",
    "борлуулалт, маркетингийн зардал": "selling_expenses",
    "борлуулалтын зардал": "selling_expenses",
    "ерөнхий ба удирдлагын зардал": "general_and_admin_expenses",
    "удирдлагын зардал": "admin_expenses",
    "санхүүгийн зардал": "financial_expense",
    "бусад зардал": "other_expenses",
    "бусад орлого": "other_income",
    # ── Interest income — both standard (-ний) and BoM (-гийн) variants ───────
    "нийт хүүний орлого": "interest_income",
    "зээлийн хүүний орлого": "interest_income",
    "хүүний орлого": "interest_income",
    "хүүгийн орлого": "interest_income",             # BoM variant
    "хүүний зардал": "interest_expense",
    "нийт хүүний зардал": "interest_expense",
    "хүүгийн зардал": "interest_expense",             # BoM variant
    # ── Fee / commission income — primary revenue for securities brokers ──────
    # Longer patterns checked first
    "шимтгэлийн цэвэр орлого": "fee_income",
    "цэвэр шимтгэлийн орлого": "fee_income",
    "нийт шимтгэлийн орлого": "fee_income",
    "хураамж шимтгэлийн орлого": "fee_income",
    "брокерийн шимтгэлийн орлого": "fee_income",
    "зуучлалын шимтгэлийн орлого": "fee_income",
    "үнэт цаасны шимтгэлийн орлого": "fee_income",
    "шимтгэлийн орлого": "fee_income",
    "брокерийн хураамж": "fee_income",
    "зуучлалын хураамж": "fee_income",
    "комиссийн орлого": "commission_income",
    # ── Total operating income — PRIMARY revenue line for securities firms ────
    # FRC standard IS row 1: "Үйл ажиллагааны орлого" = sum of broker/underwriting/
    # trading sub-items.  Mapping the TOTAL here means sub-items that contain the
    # substring "үйл ажиллагааны орлого" (e.g. "Брокер, дилерийн үйл ажиллагааны
    # орлого") also resolve to revenue, but first-match-wins keeps the total row.
    "үйл ажиллагааны орлого": "revenue",
    # ── Operating income sub-items — mapped for breakdown reporting ───────────
    # These resolve via first-match-wins: revenue is already set from the total row,
    # so sub-item values are silenced in income totals but stored for granularity.
    "брокер, дилерийн үйл ажиллагааны орлого": "fee_income",
    "андеррайтерийн үйл ажиллагааны орлого": "commission_income",
    # ── Securities trading / valuation income ────────────────────────────────
    # Rows 1.3–1.4 in FRC IS are SUB-ITEMS of row 1 "Үйл ажиллагааны орлого"
    # (already captured as revenue = 7.47B).  Silencing them prevents double-
    # counting in _get_total_income.  The standalone gains (row 14) are separate.
    "үнэт цаасны арилжааны цэвэр орлого": "label_column",              # IS sub-item 1.3
    "үнэт цаасны үнэлгээний тэгшитгэлийн цэвэр орлого": "label_column",# IS sub-item 1.4
    "үнэт цаасны арилжааны орлого": "label_column",
    "үнэт цаасны арилжааны ашиг": "label_column",
    "арилжааны орлого": "trading_income",
    "гадаад валютын арилжааны орлого": "trading_income",
    "хөрөнгө оруулалтын орлого": "other_income",
    "үнэт цаасны орлого": "other_income",
    # ── Standalone other gains (IS row 14) ───────────────────────────────────
    # "Бусад ашиг (алдагдал)" = large portfolio revaluation / disposal gains.
    # This is NOT a sub-item of row 1 — it's a separate income line after expenses.
    # Maps to trading_income (the only income key not yet claimed by sub-items).
    # With the revenue>0 guard in _get_total_income, this is included in the total
    # without double-counting with revenue.
    "бусад ашиг ( алдагдал)": "trading_income",
    "бусад ашиг (алдагдал)": "trading_income",
    # ── Profit after tax spelling variant (file omits 'ь') ───────────────────
    # File: "Татварын дараах ашиг (алдагдал)" — without 'ь' in "дараах"
    # Dict has "татварын дараахь ашиг" (with ь) which doesn't substring-match.
    "татварын дараах ашиг": "profit_after_tax",
    # ── Asset disposal gains ─────────────────────────────────────────────────
    "үндсэн хөрөнгө данснаас хассаны олз (гарз)": "other_income",
    "биет бус хөрөнгө данснаас хассаны олз (гарз)": "label_column",
    # ── Equity-method income (sub-item of dividend income, first-match-wins) ──
    "хувьцааны ногдол ашиг": "dividend_income",
    # "Харaaт" in this file uses Latin 'a' (U+0061) for the double-а — data entry artifact.
    # Both the Latin-mixed and pure-Cyrillic variants are listed to silence the warning.
    "хар\u0061\u0061т болон хамтарсан компаниас олсон ашиг": "label_column",  # Latin-a variant (file)
    "харaaт болон хамтарсан компаниас олсон ашиг": "label_column",             # Latin-a spelled out
    "хар\u0430\u0430т болон хамтарсан компаниас олсон ашиг": "label_column",   # All-Cyrillic а variant
    "харат болон хамтарсан компаниас олсон ашиг": "label_column",
    "харат болон хамтарсан": "label_column",
    # ── OCI section (all zero for most securities firms) ─────────────────────
    "бусад дэлгэрэнгүй орлого": "other_comprehensive_income",
    "хөрөнгийн дахин үнэлгээний нэмэгдлийн зөрүү": "label_column",
    "гадаад валютынхөрвүүлэлтийн зөрүү": "label_column",   # no-space variant in file
    "гадаад валютын хөрвүүлэлтийн зөрүү": "label_column",
    "бусад  олз (гарз)": "label_column",                    # double-space variant
    "бусад олз (гарз)": "label_column",
    # ── EPS / stopped operations ──────────────────────────────────────────────
    "нэгж хувьцаанд ногдох суурь ашиг (алдагдал)": "basic_eps",
    "зогсоосон үйл ажиллагааны татварын дараах ашиг (алдагдал)": "label_column",
    # ── Operating expenses ────────────────────────────────────────────────────
    "үйл ажиллагааны зардал": "operating_expenses",
    "нийт үйл ажиллагааны зардал": "operating_expenses",
    "үйл ажиллагааны бусад зардал": "operating_expenses",
    # ── Label rows ────────────────────────────────────────────────────────────
    "үзүүлэлт": "label_column",
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
    "securities_balance_sheet": SECURITIES_BALANCE_SHEET_HEADERS,
    "securities_income_statement": SECURITIES_INCOME_STATEMENT_HEADERS,
}

"""Groq AI-powered red flags analysis.

Replaces the hardcoded 5-rule _compute_red_flags() with a sector-aware LLM
analysis that synthesises ratios, DuPont decomposition, forensic scoring,
valuation multiples, and stock price context into structured risk flags.

Each flag has:
  flag        — short title
  explanation — detailed narrative with actual numbers
  severity    — "high" | "medium" | "low" | "clear"
"""

import json
import os
import logging
from pathlib import Path

# Load .env from project root if GROQ_API_KEY not already set
if not os.environ.get("GROQ_API_KEY"):
    _env_file = Path(__file__).parent.parent.parent / ".env"
    if _env_file.exists():
        for _line in _env_file.read_text().splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())

logger = logging.getLogger(__name__)

_SECTOR_CONTEXT = {
    "Banking": """You are analysing a MONGOLIAN BANK. Key metrics to focus on:
- Asset quality: NPL Ratio (>5% is concerning), Coverage Ratio (<1.0x is dangerous)
- Liquidity: LDR (>90% is high risk), Cash-to-Deposits
- Profitability: NIM compression, ROA trend, ROE trend
- Capital: Equity-to-Assets declining means leverage is rising
- Efficiency: Cost-to-Income worsening means operational weakness
- Do NOT flag D/E ratio as a standalone issue — banks are inherently leveraged.
- Do NOT use Beneish or Piotroski criteria — they are not applicable to banks.""",

    "Insurance": """You are analysing a MONGOLIAN INSURANCE COMPANY. Key metrics to focus on:
- Underwriting: Combined Ratio >100% means the insurer LOSES money on insurance itself
- Loss Ratio rising: claims exceeding premiums is the most dangerous signal
- Solvency Ratio <20% breaches regulatory minimum (Mongolia FRC standard)
- Reserve Coverage <1.0x means insufficient reserves for outstanding claims
- Heavy reliance on investment income (investment_income_ratio >50%) signals the underwriting business is unprofitable
- Premium growth stalling while losses rise is a structural warning
- Do NOT use Beneish or Piotroski criteria — they are not applicable to insurers.""",

    "Finance": """You are analysing a MONGOLIAN FINANCE / NBFI COMPANY (lending firm, securities firm, or holding company). Key metrics to focus on:
- NIM compression: narrowing spread between yield on earning assets and cost of funds
- NPA Ratio rising: non-performing assets signal deteriorating loan quality
- D/E accelerating beyond 6x is a regulatory risk for NBFIs
- Cost-to-Income >60% signals operational inefficiency
- Provision Coverage <1.0x means loan loss reserves are inadequate
- Negative OCF while reporting profits is an earnings quality warning
- Interest Spread narrowing = profitability squeeze from both sides
- Do NOT use Beneish or Piotroski criteria — they are not applicable to NBFIs.""",

    "Standard": """You are analysing a MONGOLIAN STANDARD COMPANY (manufacturing, trading, retail, or other non-financial). Apply full forensic analysis:
- Beneish M-Score: >-1.78 signals possible earnings manipulation
- DSRI >1.1: receivables outpacing revenue (aggressive revenue recognition)
- TATA >0.05: high accruals signal lower earnings quality
- Piotroski F-Score: declining score means deteriorating financial health
- Current Ratio dropping below 1.0: short-term liquidity crisis
- D/E spike >25% YoY: leverage acceleration
- DuPont decomposition: identify which driver (margin, turnover, leverage) is deteriorating ROE
- Altman Z-Score: <1.81 = distress zone, 1.81-2.99 = grey zone""",
}

_PROMPT_TEMPLATE = """You are a senior financial analyst specialising in Mongolian Stock Exchange (MSE) listed companies.

{sector_context}

Below is structured financial data for **{company_name}** (sector: {sector}).

## Current Period Ratios
{current_ratios}

## Prior Period Ratios
{prev_ratios}

## Forensic Score
{forensic}

## DuPont Decomposition
{dupont}

## Valuation Multiples
{valuation}

## Stock Price Context
{price_context}

## Beneish Indices (Standard sector only)
{beneish}

---

Analyse this data holistically and identify the most important risk signals.

Return a JSON array of flag objects. Each object must have exactly these keys:
- "flag": short title (max 6 words)
- "explanation": 1-2 sentences with specific numbers from the data
- "severity": one of "high", "medium", "low", or "clear"

Rules:
- Maximum 5 flags total.
- If severity is "clear", use flag = "No Major Red Flags" and explain what looks healthy.
- Only include "clear" when there are genuinely NO concerning signals.
- When there ARE issues, do NOT include a "clear" entry — only list actual red flags.
- Cross-reference multiple signals (e.g. NIM compression + rising NPA = compounding risk).
- Reference actual numbers from the data, not generic statements.
- Be specific to the sector — do not flag ratios that are not applicable.
- Return ONLY the JSON array, no markdown, no explanation outside the array.
"""


def _fmt_ratio_section(ratios: dict) -> str:
    """Flatten a nested ratio dict into a readable string."""
    if not ratios:
        return "No data"
    lines = []
    for category, values in ratios.items():
        if isinstance(values, dict):
            for k, v in values.items():
                if v is not None:
                    if isinstance(v, float):
                        lines.append(f"  {category}.{k}: {v:.4f}")
                    else:
                        lines.append(f"  {category}.{k}: {v}")
    return "\n".join(lines) if lines else "No data"


def _fmt_price_context(price_records: list) -> str:
    if not price_records:
        return "No price data available"
    closes = []
    for r in price_records:
        try:
            closes.append(float(r["close"]))
        except (KeyError, ValueError):
            pass
    if not closes:
        return "No price data available"
    recent = closes[-1]
    high_52 = max(closes[-252:]) if len(closes) >= 252 else max(closes)
    low_52 = min(closes[-252:]) if len(closes) >= 252 else min(closes)
    pct_from_high = (recent - high_52) / high_52 * 100 if high_52 else 0
    pct_from_low = (recent - low_52) / low_52 * 100 if low_52 else 0
    trend_3m = ""
    if len(closes) >= 63:
        chg = (closes[-1] - closes[-63]) / closes[-63] * 100
        trend_3m = f", 3-month change: {chg:+.1f}%"
    return (
        f"Last close: {recent:,.0f} MNT | "
        f"52-week high: {high_52:,.0f} ({pct_from_high:+.1f}% from high) | "
        f"52-week low: {low_52:,.0f} ({pct_from_low:+.1f}% from low)"
        f"{trend_3m}"
    )


def _fmt_dupont(sector: str, state_vars: dict) -> str:
    formula = state_vars.get("formula", "")
    f1_label = state_vars.get("factor1_label", "")
    f1_curr = state_vars.get("factor1_curr", "")
    f1_prev = state_vars.get("factor1_prev", "")
    f2_label = state_vars.get("factor2_label", "")
    f2_curr = state_vars.get("factor2_curr", "")
    f2_prev = state_vars.get("factor2_prev", "")
    em_curr = state_vars.get("equity_multiplier_curr", "")
    em_prev = state_vars.get("equity_multiplier_prev", "")
    roe_curr = state_vars.get("roe_curr", "")
    roe_prev = state_vars.get("roe_prev", "")

    lines = [f"Formula: {formula}"]
    lines.append(f"  {f1_label}: {f1_curr} (prev: {f1_prev})")
    if f2_label:
        lines.append(f"  {f2_label}: {f2_curr} (prev: {f2_prev})")
    lines.append(f"  Equity Multiplier: {em_curr} (prev: {em_prev})")
    lines.append(f"  ROE: {roe_curr} (prev: {roe_prev})")
    return "\n".join(lines)


def _fmt_forensic(forensic_criteria: list, score_display: str) -> str:
    if not forensic_criteria:
        return "Not applicable"
    lines = [f"Score: {score_display}"]
    for c in forensic_criteria:
        status = "PASS" if c.get("pass") == 1 else ("FAIL" if c.get("pass") == 0 else "N/A")
        lines.append(f"  [{status}] {c.get('label', '')}: {c.get('explanation', '')}")
    return "\n".join(lines)


def _fmt_valuation(state_vars: dict) -> str:
    fields = [
        ("P/E", "pe"), ("P/BV", "pbv"), ("EV/EBITDA", "ev_ebitda"),
        ("FCF Yield", "fcf_yield"), ("P/PTBV", "ptbv"),
        ("P/PPOP", "p_ppop"), ("P/NII", "p_nii"),
        ("P/NPE", "p_npe"), ("P/UWP", "p_uwp"),
    ]
    lines = []
    for label, key in fields:
        v = state_vars.get(key, "N/A")
        if v and v != "N/A":
            lines.append(f"  {label}: {v}")
    return "\n".join(lines) if lines else "No valuation data"


def _fmt_beneish(beneish: dict, sector: str) -> str:
    if sector != "Standard":
        return "Not applicable for this sector"
    indices = beneish.get("indices", {})
    m_score = beneish.get("m_score")
    interp = beneish.get("interpretation", "")
    reliable = beneish.get("reliable", False)
    lines = [
        f"M-Score: {m_score:.2f} ({interp})" if m_score is not None else "M-Score: N/A",
        f"Reliable: {reliable}",
    ]
    for k, v in indices.items():
        if v is not None:
            lines.append(f"  {k.upper()}: {v:.4f}")
    return "\n".join(lines)


async def compute_red_flags_ai(
    company_name: str,
    sector: str,
    company_ratios: dict,
    company_beneish: dict,
    forensic_criteria: list,
    forensic_score_display: str,
    dupont_vars: dict,
    valuation_vars: dict,
    price_records: list,
) -> list[dict]:
    """Call Groq API to generate sector-aware red flags.

    Returns list of {flag, explanation, severity} dicts.
    Falls back to rule-based flags on any error.
    """
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        logger.warning("GROQ_API_KEY not set — using rule-based fallback")
        return _rule_based_fallback(company_ratios, company_beneish)

    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=api_key)

        curr_ratios = company_ratios.get("current", {})
        prev_ratios = company_ratios.get("prev", {})

        prompt = _PROMPT_TEMPLATE.format(
            sector_context=_SECTOR_CONTEXT.get(sector, _SECTOR_CONTEXT["Standard"]),
            company_name=company_name,
            sector=sector,
            current_ratios=_fmt_ratio_section(curr_ratios),
            prev_ratios=_fmt_ratio_section(prev_ratios),
            forensic=_fmt_forensic(forensic_criteria, forensic_score_display),
            dupont=_fmt_dupont(sector, dupont_vars),
            valuation=_fmt_valuation(valuation_vars),
            price_context=_fmt_price_context(price_records),
            beneish=_fmt_beneish(company_beneish, sector),
        )

        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1024,
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        flags = json.loads(raw)
        if not isinstance(flags, list):
            raise ValueError("Expected JSON array")

        # Validate shape
        validated = []
        for f in flags:
            if isinstance(f, dict) and "flag" in f and "explanation" in f:
                validated.append({
                    "flag": str(f.get("flag", "")),
                    "explanation": str(f.get("explanation", "")),
                    "severity": str(f.get("severity", "medium")),
                })
        return validated if validated else _rule_based_fallback(company_ratios, company_beneish)

    except Exception as e:
        logger.error("Groq red flags failed: %s", e)
        return _rule_based_fallback(company_ratios, company_beneish)


def _rule_based_fallback(ratios: dict, beneish: dict) -> list[dict]:
    """Original 5-rule fallback used when Groq is unavailable."""
    flags = []
    indices = beneish.get("indices", {})

    dsri = indices.get("dsri")
    if dsri is not None and dsri > 1.1:
        flags.append({"flag": "Receivables Outpacing Revenue", "severity": "medium",
                      "explanation": f"DSRI = {dsri:.2f} (>1.1). Receivables growing faster than revenue may signal aggressive revenue recognition."})

    tata = indices.get("tata")
    if tata is not None and tata > 0.05:
        flags.append({"flag": "Earnings Quality Warning", "severity": "medium",
                      "explanation": f"TATA = {tata:.3f} (>0.05). High accruals relative to total assets indicate lower earnings quality."})

    curr_ratios = ratios.get("current", {})
    prev_ratios = ratios.get("prev", {})
    curr_de = curr_ratios.get("solvency", {}).get("debt_to_equity")
    prev_de = prev_ratios.get("solvency", {}).get("debt_to_equity")
    if curr_de is not None and prev_de is not None and prev_de > 0:
        change = (curr_de - prev_de) / abs(prev_de)
        if change > 0.25:
            flags.append({"flag": "Leverage Spike", "severity": "medium",
                          "explanation": f"Debt/Equity rose from {prev_de:.2f} to {curr_de:.2f} (+{change*100:.0f}%). Significant leverage increase warrants scrutiny."})

    if beneish.get("reliable"):
        m_score = beneish.get("m_score")
        if m_score is not None and m_score > -1.78:
            flags.append({"flag": "Beneish Manipulation Signal", "severity": "high",
                          "explanation": f"M-Score = {m_score:.2f} (>-1.78). Model suggests possible earnings manipulation."})

    curr_cr = curr_ratios.get("liquidity", {}).get("current_ratio")
    prev_cr = prev_ratios.get("liquidity", {}).get("current_ratio")
    if curr_cr is not None and curr_cr < 1.0 and (prev_cr is None or prev_cr >= 1.0):
        flags.append({"flag": "Liquidity Deterioration", "severity": "high",
                      "explanation": f"Current ratio = {curr_cr:.2f} (<1.0). Company may struggle to meet short-term obligations."})

    if not flags:
        return [{"flag": "No Major Red Flags", "explanation": "No significant accounting anomalies detected.", "severity": "clear"}]
    return flags

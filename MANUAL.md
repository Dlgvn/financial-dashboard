# Financial Dashboard — User Guide

> A complete reference for reading, interpreting, and acting on every number in the dashboard.
> Audience: business analysts, investors, and executives. No programming knowledge required.

---

## Table of Contents

1. [What Is This Dashboard?](#chapter-1--what-is-this-dashboard)
2. [Navigating the Dashboard](#chapter-2--navigating-the-dashboard)
3. [Reading the Health Score (0–100)](#chapter-3--reading-the-health-score-0100)
4. [Standard Company Ratios](#chapter-4--standard-company-ratios)
   - 4.1 [Activity Ratios](#41-activity-ratios)
   - 4.2 [Liquidity Ratios](#42-liquidity-ratios)
   - 4.3 [Solvency Ratios](#43-solvency-ratios)
   - 4.4 [Profitability Ratios](#44-profitability-ratios)
   - 4.5 [Cash Flow Performance Ratios](#45-cash-flow-performance-ratios)
   - 4.6 [DuPont Analysis](#46-dupont-analysis)
   - 4.7 [Altman Z-Score](#47-altman-z-score)
5. [Piotroski F-Score](#chapter-5--piotroski-f-score)
6. [Beneish M-Score (Manipulation Detector)](#chapter-6--beneish-m-score-manipulation-detector)
7. [Banking Sector Ratios](#chapter-7--banking-sector-ratios)
8. [Insurance Sector Ratios](#chapter-8--insurance-sector-ratios)
9. [Finance / NBFI Sector Ratios](#chapter-9--finance--nbfi-sector-ratios)
10. [Valuation Multiples](#chapter-10--valuation-multiples)
11. [Red Flags](#chapter-11--red-flags)
12. [Portfolio Analysis](#chapter-12--portfolio-analysis)
- [Appendix A — Quick-Reference Benchmarks](#appendix-a--quick-reference-benchmarks-by-sector)
- [Appendix B — Glossary](#appendix-b--glossary)

---

## Chapter 1 — What Is This Dashboard?

### 1.1 Purpose

This dashboard is a financial analysis tool built specifically for companies listed on the **Mongolian Stock Exchange (MSE)**. It reads the annual financial statements that companies file with the exchange, calculates dozens of standard financial ratios, and presents the results in a clear, colour-coded format so you can quickly assess a company's health — and compare it to peers.

Think of it as having a financial analyst run a full report on every company you care about, automatically, every time you load new data.

### 1.2 What Data It Uses

The dashboard works with two types of data:

**1. Financial Statements (uploaded by you)**
These are the structured JSON files exported from the company's annual report. They contain three core statements:
- **Balance Sheet** — a snapshot of what the company owns (assets) and owes (liabilities and equity) at year-end.
- **Income Statement** — a record of revenue earned and expenses paid over the year, ending at net income (profit).
- **Cash Flow Statement** — tracks actual cash moving in and out: from operations, investments, and financing.

For banks, insurers, and finance companies, additional sector-specific data is also extracted (e.g., loan portfolios, premium income, deposit balances).

**2. Price Data (fetched from MSE)**
This is the daily trading history for each listed company: opening price, closing price, high, low, and trading volume. The dashboard uses this to calculate valuation multiples (e.g., P/E ratio) and display a 52-week price chart.

### 1.3 Supported Company Types

The dashboard recognises four types of companies and applies tailored analysis to each:

| Type | Examples | Specialised Analysis |
|------|----------|----------------------|
| **Standard** | Manufacturing, retail, mining, food production | Altman Z-Score, Piotroski F-Score, Beneish M-Score |
| **Bank** | Commercial banks | CAMELS framework, NPL ratio, Loan-to-Deposit ratio |
| **Insurance** | Insurance companies | Combined ratio, Loss ratio, Solvency ratio |
| **Finance / NBFI** | Lending companies, securities firms, holding companies | Yield on earning assets, NPA ratio, Cost of funds |

The company type is detected automatically from the structure of the uploaded financial data.

---

## Chapter 2 — Navigating the Dashboard

### 2.1 Home Page — Uploading Companies

When you first open the dashboard, you see the **Home page**. From here:

- **Upload a company** by dragging a JSON financial statement file onto the upload zone, or clicking to browse.
- Once uploaded, the company appears in the list below with a "View" button.
- Click **"Refresh Prices"** to fetch the latest MSE trading data for all uploaded companies.

### 2.2 Screener — Comparing All Companies

The **Screener** page shows every uploaded company in a single table. You can sort by any column — most usefully by the **Health Score** to rank companies from strongest to weakest at a glance.

Columns shown:
- Company name (click to open the detail page)
- Sector type
- Composite Health Score (colour-coded badge)
- ROE (Return on Equity)
- "Add to Portfolio" button

### 2.3 Company Detail — Six Tabs

Clicking any company opens a six-tab detail view. Each tab answers a different question:

#### Overview Tab
*"Is this company fundamentally healthy?"*

Shows a **radial health gauge** (0–100) and a **radar chart** breaking down performance across categories (profitability, liquidity, solvency, etc.). Also shows a **Key Metrics card** and a **Risk Signals** section highlighting the most important concerns.

#### Ratios Tab
*"What do the individual numbers look like?"*

Displays all calculated ratios in grouped tables. Each ratio cell is colour-coded:
- 🟢 **Green** — the ratio is at or above a healthy benchmark
- 🟡 **Amber** — approaching a threshold, worth monitoring
- 🔴 **Red** — below the acceptable threshold, a concern

Each ratio also shows the **year-over-year (YoY) change** so you can see whether the company is improving or deteriorating.

#### Forensic Tab
*"Are there signs of financial stress or irregular reporting?"*

For standard companies: shows the **Piotroski F-Score** (9-point strength test) and **Beneish M-Score** (manipulation detector).

For banks, insurers, and finance companies: shows a sector-specific **8-criterion forensic checklist** with a YoY trend chart for key metrics.

#### Valuation Tab
*"How expensive is this stock relative to its fundamentals?"*

Shows sector-appropriate **valuation multiples** (P/E, P/BV, etc.) and a **52-week price chart**.

#### DuPont Tab
*"What is driving the company's return on equity?"*

Breaks ROE into three components — **Net Profit Margin × Asset Turnover × Equity Multiplier** — and shows how each changed year-over-year.

#### Red Flags Tab
*"What are the most urgent warning signs?"*

Shows an instant list of **rule-based red flags** (triggered by hard thresholds), followed by an **AI-generated analysis** that provides context and severity ratings (HIGH / MEDIUM / LOW / CLEAR).

### 2.4 Portfolio Page

The **Portfolio** page lets you build and analyse a portfolio of MSE companies.

**Holdings tab:** Add companies from the Screener, adjust their portfolio weights with sliders, and click "Equal Weight" to distribute weights evenly.

**Analysis tab:** See the **efficient frontier** — a scatter plot of 200 randomly generated portfolio combinations, showing the trade-off between risk (x-axis) and return (y-axis). The system also calculates the **optimal Max-Sharpe portfolio** (the combination with the best return per unit of risk) and compares it to your current allocation.

Risk metrics shown:
- **Sortino Ratio** — return relative to downside risk only (ignores upside volatility)
- **Maximum Drawdown** — the largest peak-to-trough loss in the historical period
- **CVaR 95%** — the average loss in the worst 5% of trading days ("tail risk")

---

## Chapter 3 — Reading the Health Score (0–100)

### 3.1 What the Score Means

The **Composite Health Score** is a single number from 0 to 100 that summarises a company's financial condition. It combines multiple ratios from different categories into one weighted score.

| Score | Badge Colour | Label | What It Means |
|-------|-------------|-------|---------------|
| 70–100 | 🟢 Green | **Healthy** | Ratios are broadly above benchmarks; manageable risk |
| 40–69 | 🟡 Amber | **Caution** | Some ratios are weak; monitor closely |
| 0–39 | 🔴 Red | **Distress** | Multiple ratios are below acceptable levels; high risk |

The score is **not a prediction** — it is a snapshot of the current financial period. A healthy score today does not guarantee future performance.

### 3.2 Standard Company Score

Weights applied to each category:

| Category | Weight | Ratios Used |
|----------|--------|-------------|
| Profitability | 25% | ROA, ROE, Net Profit Margin |
| Liquidity | 20% | Current Ratio, Quick Ratio, Cash Ratio |
| Solvency | 20% | Debt-to-Equity, Debt-to-Assets, Interest Coverage |
| Activity | 15% | Asset Turnover, Days Sales Outstanding, Inventory Turnover |
| Altman Z-Score | 10% | Composite Z score (see §4.7) |
| Piotroski F-Score | 10% | F-score out of 9 (see Chapter 5) |

**Beneish Penalty:** If the Beneish M-Score suggests possible earnings manipulation (see Chapter 6), **10 points are deducted** from the final score.

**Missing data:** If a ratio cannot be calculated (e.g., the company has no inventory), its weight is redistributed proportionally to the other available categories.

### 3.3 Bank Score (CAMELS Framework)

Banks are scored using the internationally recognised **CAMELS** framework:

| Component | Weight | Ratios Used |
|-----------|--------|-------------|
| Capital Adequacy | 25% | Equity/Assets, Equity Multiplier |
| Asset Quality | 25% | NPL Ratio, Coverage Ratio, Loan Loss Reserve |
| Earnings | 20% | ROA, ROE, Net Interest Margin |
| Liquidity | 20% | Loan-to-Deposit Ratio, Cash-to-Deposits |
| Management/Efficiency | 10% | Cost-to-Income Ratio |

### 3.4 Insurance Score

| Component | Weight | Ratios Used |
|-----------|--------|-------------|
| Underwriting Quality | 30% | Combined Ratio, Loss Ratio, Expense Ratio |
| Solvency / Capital | 25% | Solvency Ratio, Leverage Ratio, Reserve Coverage |
| Profitability | 25% | ROA, ROE, Net Profit Margin |
| Liquidity | 20% | Investment Ratio, Cash/Liabilities, OCF Ratio |

If underwriting data is unavailable, its 30% weight redistributes to the profitability component.

### 3.5 Finance / NBFI Score

| Component | Weight | Ratios Used |
|-----------|--------|-------------|
| Profitability | 30% | NIM, ROA, ROE, Net Profit Margin |
| Capital / Leverage | 25% | Debt-to-Equity, Equity Ratio |
| Efficiency | 25% | Cost-to-Income, Asset Utilisation |
| Liquidity | 20% | Cash Ratio, Loan-to-Assets |

---

## Chapter 4 — Standard Company Ratios

> **Colour legend for this chapter:**
> 🟢 = healthy benchmark met · 🟡 = approaching threshold · 🔴 = below threshold

---

### 4.1 Activity Ratios

Activity ratios measure how efficiently a company uses its assets to generate revenue. Higher turnover generally means better efficiency.

---

#### Total Asset Turnover

**What it measures:** How many tenge (M₮) of revenue the company generates for every tenge of assets it holds.

**Formula:**
```
Total Asset Turnover = Revenue / Total Assets
```

**Variables:**
- **Revenue** (Income Statement): total sales for the year
- **Total Assets** (Balance Sheet): everything the company owns — cash, equipment, property, receivables

**Why it matters:** A higher ratio means the company is squeezing more sales out of its asset base. A declining ratio may indicate the company is accumulating assets without a matching increase in sales.

**Worked example:**
- Revenue = 5,000 M₮, Total Assets = 4,000 M₮
- Total Asset Turnover = 5,000 / 4,000 = **1.25×**
- Interpretation: the company generates 1.25 M₮ of revenue per 1 M₮ of assets — reasonable for a manufacturer.

**How to interpret:**

| Result | Meaning |
|--------|---------|
| > 1.5× | 🟢 Highly efficient |
| 0.8–1.5× | 🟡 Acceptable |
| < 0.8× | 🔴 Poor asset utilisation |

---

#### Fixed Asset Turnover

**What it measures:** Revenue generated per tenge of fixed assets (property, plant, equipment).

**Formula:**
```
Fixed Asset Turnover = Revenue / Fixed Assets
```

**Variables:**
- **Fixed Assets** (Balance Sheet): long-term physical assets like machinery and buildings

**Why it matters:** Measures how productively the company uses its capital-intensive assets. Particularly important for manufacturers and miners.

**Worked example:**
- Revenue = 5,000 M₮, Fixed Assets = 2,000 M₮
- Fixed Asset Turnover = 5,000 / 2,000 = **2.5×**

**How to interpret:**

| Result | Meaning |
|--------|---------|
| > 3× | 🟢 Excellent |
| 1.5–3× | 🟡 Normal range |
| < 1.5× | 🔴 Underutilised capital |

---

#### Inventory Turnover

**What it measures:** How many times per year the company sells through its entire inventory.

**Formula:**
```
Inventory Turnover = Cost of Goods Sold / Inventory
```

**Variables:**
- **Cost of Goods Sold (COGS)** (Income Statement): direct cost of producing goods sold
- **Inventory** (Balance Sheet): goods held for sale, or raw materials

**Why it matters:** Low inventory turnover means goods are sitting unsold — tying up cash and risking obsolescence. High turnover means the company moves stock quickly.

**Worked example:**
- COGS = 3,000 M₮, Inventory = 500 M₮
- Inventory Turnover = 3,000 / 500 = **6×** (sells through stock every 2 months)

**How to interpret:**

| Result | Meaning |
|--------|---------|
| > 8× | 🟢 Rapid stock movement |
| 4–8× | 🟡 Normal |
| < 4× | 🔴 Slow-moving inventory |

---

#### Days Inventory Outstanding (DIO)

**What it measures:** How many days, on average, goods sit in inventory before being sold.

**Formula:**
```
DIO = 365 / Inventory Turnover
```

**Why it matters:** A direct, intuitive version of inventory turnover — expressed in days instead of times per year. Shorter is better.

**Worked example:**
- Inventory Turnover = 6× → DIO = 365 / 6 = **61 days**

**How to interpret:**

| Result | Meaning |
|--------|---------|
| < 45 days | 🟢 Fast |
| 45–90 days | 🟡 Typical |
| > 90 days | 🔴 Slow; potential obsolescence risk |

---

#### Receivables Turnover

**What it measures:** How many times per year the company collects its outstanding customer debts.

**Formula:**
```
Receivables Turnover = Revenue / Accounts Receivable
```

**Variables:**
- **Accounts Receivable** (Balance Sheet): money owed by customers who have been invoiced but not yet paid

**Why it matters:** High receivables turnover means customers pay quickly. Low turnover means cash is stuck in unpaid invoices.

**Worked example:**
- Revenue = 5,000 M₮, Accounts Receivable = 600 M₮
- Receivables Turnover = 5,000 / 600 = **8.3×**

---

#### Days Sales Outstanding (DSO)

**What it measures:** The average number of days it takes to collect payment from customers.

**Formula:**
```
DSO = 365 / Receivables Turnover
```

**Why it matters:** If DSO is rising year-over-year, customers are taking longer to pay — a warning sign for cash flow.

**Worked example:**
- Receivables Turnover = 8.3× → DSO = 365 / 8.3 = **44 days**

**How to interpret:**

| Result | Meaning |
|--------|---------|
| < 30 days | 🟢 Fast collection |
| 30–60 days | 🟡 Typical |
| > 60 days | 🔴 Slow; cash flow risk |

---

#### Payables Turnover

**What it measures:** How many times per year the company pays its suppliers.

**Formula:**
```
Payables Turnover = Cost of Goods Sold / Accounts Payable
```

**Variables:**
- **Accounts Payable** (Balance Sheet): money the company owes to its own suppliers

**Why it matters:** Lower payables turnover means the company takes longer to pay suppliers — which can be a sign of financial stress or, if deliberate, smart cash management.

---

#### Days Payable Outstanding (DPO)

**What it measures:** The average number of days the company takes to pay its suppliers.

**Formula:**
```
DPO = 365 / Payables Turnover
```

**Why it matters:** A higher DPO means the company holds onto cash longer before paying bills. This is often a sign of negotiating power with suppliers. But an extremely high DPO may indicate the company is struggling to pay.

**Worked example:**
- COGS = 3,000 M₮, Accounts Payable = 400 M₮
- Payables Turnover = 3,000 / 400 = 7.5×
- DPO = 365 / 7.5 = **49 days**

**How to interpret:**

| Result | Meaning |
|--------|---------|
| 30–60 days | 🟢 Normal trade credit terms |
| > 90 days | 🟡 May signal cash pressure |
| Extremely high | 🔴 Possible inability to pay suppliers |

---

#### Cash Conversion Cycle (CCC)

**What it measures:** The total number of days between paying for raw materials and collecting cash from customers.

**Formula:**
```
CCC = DIO + DSO − DPO
```

**Why it matters:** The CCC measures how long cash is "locked up" in operations. A lower (or negative) CCC means the company collects cash before it has to pay suppliers — an excellent position. A very high CCC means the business is constantly hungry for working capital.

**Worked example:**
- DIO = 61, DSO = 44, DPO = 49
- CCC = 61 + 44 − 49 = **56 days**

**How to interpret:**

| Result | Meaning |
|--------|---------|
| < 30 days | 🟢 Excellent cash conversion |
| 30–80 days | 🟡 Acceptable |
| > 80 days | 🔴 High working capital need |
| Negative | 🟢🟢 Best case: customers pay before suppliers must be paid |

---

### 4.2 Liquidity Ratios

Liquidity ratios measure whether the company has enough short-term assets to cover its short-term obligations. These ratios protect against the risk of a company running out of cash.

---

#### Current Ratio

**What it measures:** Whether the company can pay all its short-term debts using its short-term assets.

**Formula:**
```
Current Ratio = Total Current Assets / Total Current Liabilities
```

**Variables:**
- **Current Assets** (Balance Sheet): cash, receivables, inventory — anything convertible to cash within one year
- **Current Liabilities** (Balance Sheet): debts due within one year

**Why it matters:** A ratio below 1.0 means the company owes more in the short term than it has in liquid assets — a serious warning sign.

**Worked example:**
- Current Assets = 2,000 M₮, Current Liabilities = 1,200 M₮
- Current Ratio = 2,000 / 1,200 = **1.67×**

**How to interpret:**

| Result | Meaning |
|--------|---------|
| > 2.0× | 🟢 Comfortable buffer |
| 1.0–2.0× | 🟡 Acceptable; watch trend |
| < 1.0× | 🔴 Short-term liquidity risk |

---

#### Quick Ratio

**What it measures:** A stricter version of the Current Ratio that excludes inventory (which may be hard to sell quickly).

**Formula:**
```
Quick Ratio = (Current Assets − Inventory) / Current Liabilities
```

**Why it matters:** Inventory can take time to sell or may lose value. The Quick Ratio asks: even without selling inventory, can the company meet its short-term obligations?

**Worked example:**
- Current Assets = 2,000 M₮, Inventory = 500 M₮, Current Liabilities = 1,200 M₮
- Quick Ratio = (2,000 − 500) / 1,200 = **1.25×**

**How to interpret:**

| Result | Meaning |
|--------|---------|
| > 1.5× | 🟢 Very liquid |
| 0.8–1.5× | 🟡 Adequate |
| < 0.8× | 🔴 Concern; relies on selling inventory to pay bills |

---

#### Cash Ratio

**What it measures:** The strictest liquidity test — only cash against current liabilities.

**Formula:**
```
Cash Ratio = Cash and Cash Equivalents / Current Liabilities
```

**Why it matters:** In a crisis, only cash is immediately available. This ratio asks: if everything froze today, could the company survive from its cash alone?

**Worked example:**
- Cash = 400 M₮, Current Liabilities = 1,200 M₮
- Cash Ratio = 400 / 1,200 = **0.33×**

**How to interpret:**

| Result | Meaning |
|--------|---------|
| > 0.5× | 🟢 Strong cash position |
| 0.2–0.5× | 🟡 Normal |
| < 0.2× | 🔴 Very tight cash; vulnerable to disruption |

---

#### Working Capital

**What it measures:** The absolute amount of short-term financial cushion, in M₮.

**Formula:**
```
Working Capital = Current Assets − Current Liabilities
```

**Why it matters:** Unlike ratios, Working Capital is an absolute number — it tells you the size of the buffer in monetary terms. Negative working capital means the company owes more short-term than it holds in liquid assets.

**Worked example:**
- Current Assets = 2,000 M₮, Current Liabilities = 1,200 M₮
- Working Capital = **800 M₮**

---

### 4.3 Solvency Ratios

Solvency ratios measure long-term financial stability — specifically whether the company's debt load is sustainable.

---

#### Debt-to-Equity

**What it measures:** For every tenge of owner equity, how many tenge of debt does the company carry?

**Formula:**
```
Debt-to-Equity = Total Liabilities / Total Equity
```

**Variables:**
- **Total Liabilities** (Balance Sheet): everything the company owes — short and long-term
- **Total Equity** (Balance Sheet): shareholders' stake, i.e., what's left after subtracting liabilities from assets

**Why it matters:** High debt relative to equity amplifies both gains and losses. A company with D/E of 5× means creditors have five times more claim on assets than shareholders — risky if revenues drop.

**Worked example:**
- Total Liabilities = 3,000 M₮, Total Equity = 1,000 M₮
- Debt-to-Equity = 3,000 / 1,000 = **3.0×**

**How to interpret:**

| Result | Meaning |
|--------|---------|
| < 1.0× | 🟢 Low leverage; conservative |
| 1.0–2.5× | 🟡 Moderate; normal for many industries |
| > 2.5× | 🔴 High leverage; vulnerable to downturns |

*Note: Finance companies and banks naturally operate with higher leverage (see Chapters 7 and 9).*

---

#### Debt-to-Assets

**What it measures:** What fraction of the company's assets are funded by debt?

**Formula:**
```
Debt-to-Assets = Total Liabilities / Total Assets
```

**Why it matters:** Shows how much of the asset base is owned by creditors vs. shareholders. Above 0.6 (60%) means most assets are debt-financed.

**Worked example:**
- Total Liabilities = 3,000 M₮, Total Assets = 4,000 M₮
- Debt-to-Assets = 3,000 / 4,000 = **0.75** (75%)

---

#### Equity Ratio

**What it measures:** The mirror of Debt-to-Assets — what fraction of assets is funded by shareholders' own money?

**Formula:**
```
Equity Ratio = Total Equity / Total Assets
```

**Why it matters:** A higher equity ratio means a more conservatively financed company. At least 30–40% equity is generally considered a safe cushion for standard companies.

**Worked example:**
- Total Equity = 1,000 M₮, Total Assets = 4,000 M₮
- Equity Ratio = 1,000 / 4,000 = **0.25** (25%)

---

#### Interest Coverage

**What it measures:** How many times the company's operating profit can cover its interest payments.

**Formula:**
```
Interest Coverage = EBIT / Financial Expense

where: EBIT = Profit Before Tax + Financial Expense
```

**Variables:**
- **EBIT** (Earnings Before Interest and Tax): operating profit before deducting interest and taxes
- **Financial Expense** (Income Statement): interest paid on loans

**Why it matters:** Below 1.5× means the company barely earns enough to service its debt — a serious distress signal.

**Worked example:**
- Profit Before Tax = 300 M₮, Financial Expense = 100 M₮
- EBIT = 300 + 100 = 400 M₮
- Interest Coverage = 400 / 100 = **4.0×**

**How to interpret:**

| Result | Meaning |
|--------|---------|
| > 5× | 🟢 Debt easily serviced |
| 2–5× | 🟡 Acceptable |
| < 2× | 🔴 Debt burden is a risk |
| < 1× | 🔴🔴 Cannot cover interest from operations |

---

### 4.4 Profitability Ratios

Profitability ratios measure how effectively the company converts revenue and assets into profit.

---

#### Gross Profit Margin

**What it measures:** How much of each tenge of revenue remains after paying for the direct cost of goods sold.

**Formula:**
```
Gross Profit Margin = Gross Profit / Revenue
```

**Variables:**
- **Gross Profit** (Income Statement): Revenue minus Cost of Goods Sold
- **Revenue** (Income Statement): total sales

**Why it matters:** The gross margin reflects pricing power and production efficiency. A declining gross margin often means costs are rising faster than the company can raise prices.

**Worked example:**
- Revenue = 5,000 M₮, COGS = 3,200 M₮, Gross Profit = 1,800 M₮
- Gross Profit Margin = 1,800 / 5,000 = **36%**

---

#### Operating Margin (EBIT Margin)

**What it measures:** Profit from core operations as a percentage of revenue, after paying all operating costs.

**Formula:**
```
Operating Margin = EBIT / Revenue

where: EBIT = Profit Before Tax + Financial Expense
```

**Why it matters:** Unlike Gross Margin, this includes selling, administrative, and overhead costs. It shows the true profitability of the business before financing decisions.

**Worked example:**
- EBIT = 400 M₮, Revenue = 5,000 M₮
- Operating Margin = 400 / 5,000 = **8%**

---

#### Net Profit Margin

**What it measures:** How much of each tenge of revenue ends up as net income after all costs, including taxes and interest.

**Formula:**
```
Net Profit Margin = Net Income / Revenue
```

**Variables:**
- **Net Income** (Income Statement): the "bottom line" — profit after all deductions

**Why it matters:** This is the ultimate profitability measure. A company can have strong revenue and still have a thin or negative net margin if costs are poorly controlled.

**Worked example:**
- Net Income = 250 M₮, Revenue = 5,000 M₮
- Net Profit Margin = 250 / 5,000 = **5%**

**How to interpret:**

| Result | Meaning |
|--------|---------|
| > 10% | 🟢 Strong |
| 3–10% | 🟡 Acceptable |
| < 3% | 🔴 Thin margins; vulnerable |
| Negative | 🔴🔴 Loss-making |

---

#### ROA — Return on Assets

**What it measures:** How much profit the company generates relative to the size of its total asset base.

**Formula:**
```
ROA = Net Income / Total Assets
```

**Why it matters:** ROA answers: how effectively is management using the company's assets to earn profit? Two companies with the same revenue but different ROA have very different asset efficiency.

**Worked example:**
- Net Income = 250 M₮, Total Assets = 4,000 M₮
- ROA = 250 / 4,000 = **6.25%**

**How to interpret:**

| Result | Meaning |
|--------|---------|
| > 10% | 🟢 Excellent asset efficiency |
| 5–10% | 🟡 Good |
| 2–5% | 🟡 Modest |
| < 2% | 🔴 Poor |
| Negative | 🔴🔴 Generating losses |

---

#### ROE — Return on Equity

**What it measures:** How much profit shareholders earn on their invested capital.

**Formula:**
```
ROE = Net Income / Total Equity
```

**Why it matters:** ROE is the single number most investors use to evaluate a company. A company with 20% ROE is generating 20 tenge of profit for every 100 tenge shareholders have invested. However, ROE can be inflated by excessive debt (see DuPont analysis, §4.6).

**Worked example:**
- Net Income = 250 M₮, Total Equity = 1,000 M₮
- ROE = 250 / 1,000 = **25%**

**How to interpret:**

| Result | Meaning |
|--------|---------|
| > 20% | 🟢 Excellent returns for shareholders |
| 10–20% | 🟡 Good |
| 5–10% | 🟡 Modest |
| < 5% | 🔴 Weak |
| Negative | 🔴🔴 Destroying shareholder value |

---

### 4.5 Cash Flow Performance Ratios

These ratios compare the company's **actual cash generation** against its obligations — a cross-check on profit quality.

---

#### Operating Cash Flow Ratio

**What it measures:** Whether the company generates enough operating cash to cover its short-term liabilities.

**Formula:**
```
Operating CF Ratio = Operating Cash Flow / Current Liabilities
```

**Variables:**
- **Operating Cash Flow** (Cash Flow Statement): cash actually collected from running the business — not the same as profit

**Why it matters:** A company can show accounting profit while still burning cash. If operating CF is negative, the business is not self-sustaining.

**Worked example:**
- Operating CF = 600 M₮, Current Liabilities = 1,200 M₮
- Operating CF Ratio = 600 / 1,200 = **0.5×**

---

#### Cash Flow to Debt

**What it measures:** How many years it would take to repay all debt from operating cash flow alone.

**Formula:**
```
Cash Flow to Debt = Operating Cash Flow / Total Liabilities
```

**Why it matters:** A ratio of 0.2 means it would take 5 years to pay off all debt purely from operations — useful for assessing debt sustainability.

---

#### Reinvestment Ratio

**What it measures:** How much of operating cash flow is being reinvested back into the business.

**Formula:**
```
Reinvestment Ratio = Investing Cash Flow / Operating Cash Flow
```

**Note:** Investing Cash Flow is usually negative (cash spent on investments). A ratio closer to −1.0 means the company is reinvesting nearly all its earnings.

**Why it matters:** High reinvestment is a sign of a growth-oriented company. Low reinvestment may mean the company is mature, declining, or hoarding cash.

---

### 4.6 DuPont Analysis

DuPont analysis breaks ROE into three parts to reveal *why* a company has a high or low return on equity.

**Formula:**
```
ROE = Net Profit Margin × Asset Turnover × Equity Multiplier
```

Where:
- **Net Profit Margin** = Net Income / Revenue (how much profit per sale)
- **Asset Turnover** = Revenue / Total Assets (how much revenue per asset)
- **Equity Multiplier** = Total Assets / Total Equity (how much leverage is used)

**Why it matters:** A company can achieve 20% ROE in very different ways:

| Company | Net Margin | Asset Turnover | Equity Multiplier | ROE |
|---------|-----------|----------------|-------------------|-----|
| A (luxury brand) | 20% | 0.5× | 2.0× | 20% |
| B (supermarket) | 2% | 5.0× | 2.0× | 20% |
| C (leveraged) | 5% | 2.0× | 2.0× → 4.0× | 40% |

Company C's high ROE is driven entirely by debt — if revenues fall, it could quickly turn negative. This distinction is invisible if you only look at ROE.

The **DuPont tab** in the dashboard shows all three components and their YoY changes, so you can see exactly what's driving performance improvement or decline.

---

### 4.7 Altman Z-Score

The Altman Z-Score was created in 1968 by Edward Altman to predict corporate bankruptcy. It combines five financial ratios into a single score.

**Formula:**
```
Z = 1.2·X1 + 1.4·X2 + 3.3·X3 + 0.6·X4 + 1.0·X5
```

**The five components:**

| Component | Formula | What It Measures |
|-----------|---------|-----------------|
| X1 | Working Capital / Total Assets | Short-term liquidity relative to size |
| X2 | Retained Earnings / Total Assets | Accumulated profitability over lifetime |
| X3 | EBIT / Total Assets | Operating efficiency and earning power |
| X4 | Total Equity / Total Liabilities | Financial cushion against insolvency |
| X5 | Revenue / Total Assets | Asset utilisation / sales efficiency |

**Worked example:**
- X1 = 800/4,000 = 0.20
- X2 = 600/4,000 = 0.15
- X3 = 400/4,000 = 0.10
- X4 = 1,000/3,000 = 0.33
- X5 = 5,000/4,000 = 1.25
- Z = 1.2(0.20) + 1.4(0.15) + 3.3(0.10) + 0.6(0.33) + 1.0(1.25)
- Z = 0.24 + 0.21 + 0.33 + 0.20 + 1.25 = **2.23**

**Interpretation zones:**

| Z-Score | Zone | Meaning |
|---------|------|---------|
| > 2.99 | 🟢 Safe Zone | Low probability of bankruptcy |
| 1.23 – 2.99 | 🟡 Grey Zone | Uncertain; watch carefully |
| < 1.23 | 🔴 Distress Zone | High probability of financial distress |

*Note: The Altman Z-Score was calibrated on US manufacturing companies. It is used here as a directional indicator, not a precise prediction, particularly given the differences in the Mongolian market context.*

---

## Chapter 5 — Piotroski F-Score

The **Piotroski F-Score** was developed by Joseph Piotroski in 2000 to separate financially strong companies from weak ones using publicly available accounting data. It assigns 1 point for each criterion passed, for a maximum score of 9.

**The nine criteria:**

| # | Criterion | Passes When | What It Tests |
|---|-----------|-------------|---------------|
| F1 | ROA is positive | Net Income / Total Assets > 0 | Basic profitability |
| F2 | Operating cash flow is positive | Operating CF > 0 | Cash generation quality |
| F3 | ROA is improving | ROA this year > ROA last year | Profitability trend |
| F4 | Accruals are low | Operating CF / Total Assets > ROA | Cash earnings exceed accrual earnings |
| F5 | Leverage is decreasing | Debt-to-Assets this year < last year | Debt reduction trend |
| F6 | Current ratio is improving | Current Ratio this year > last year | Liquidity trend |
| F7 | No share dilution | *Not available for MSE filings — always N/A* | — |
| F8 | Gross margin is improving | Gross Margin this year > last year | Pricing / cost trend |
| F9 | Asset turnover is improving | Asset Turnover this year > last year | Efficiency trend |

**Why F4 (Accruals) matters:** Accounting profit can be inflated by accruals — revenue recognised before cash is received, or expenses deferred. If operating cash flow is *lower* than the reported profit (ROA), earnings quality is suspect. If OCF / TA > ROA, cash collections support the accounting profit.

**Interpretation:**

| F-Score | Label | Meaning |
|---------|-------|---------|
| 7 – 9 | 🟢 Strong | Most signals are positive; financially robust |
| 3 – 6 | 🟡 Neutral | Mixed signals; no strong conclusion |
| 0 – 2 | 🔴 Weak | Most signals are negative; high risk |

---

## Chapter 6 — Beneish M-Score (Manipulation Detector)

The **Beneish M-Score** was developed by Messod Beneish in 1999 to detect earnings manipulation. It uses eight financial indices to flag companies that may be artificially inflating reported profits.

**Formula:**
```
M = −4.84
  + 0.920 × DSRI
  + 0.528 × GMI
  + 0.404 × AQI
  + 0.892 × SGI
  + 0.115 × DEPI
  − 0.172 × SGAI
  + 4.679 × TATA
  − 0.327 × LVGI
```

**The eight indices:**

---

#### DSRI — Days Sales Receivables Index

**Formula:**
```
DSRI = (Accounts Receivable this year / Revenue this year)
       ÷
       (Accounts Receivable last year / Revenue last year)
```

**What it detects:** If receivables are growing much faster than revenue (DSRI > 1.5), it may indicate the company is recording sales that have not yet resulted in cash — a classic manipulation technique.

---

#### GMI — Gross Margin Index

**Formula:**
```
GMI = (Gross Margin last year / Revenue last year)
      ÷
      (Gross Margin this year / Revenue this year)
```

**What it detects:** A deteriorating gross margin (GMI > 1) creates pressure to manipulate earnings to maintain reported profitability.

---

#### AQI — Asset Quality Index

**Formula:**
```
AQI = (1 − (Current Assets + Fixed Assets) / Total Assets) this year
      ÷
      (1 − (Current Assets + Fixed Assets) / Total Assets) last year
```

**What it detects:** A rising AQI indicates an increasing proportion of the asset base is in intangible or deferred items — potentially capitalised expenses that should have been written off.

---

#### SGI — Sales Growth Index

**Formula:**
```
SGI = Revenue this year / Revenue last year
```

**What it detects:** High growth companies are under pressure to maintain their growth trajectory and are more likely to manipulate earnings to meet expectations.

---

#### DEPI — Depreciation Index

**Formula:** *(Not available for MSE filings — depreciation data is not consistently reported)*

**What it detects:** A declining depreciation rate relative to assets (DEPI > 1) can suggest the company is extending asset useful lives to reduce depreciation expense and boost reported profit.

---

#### SGAI — SG&A Index

**Formula:**
```
SGAI = (Selling & Admin Expenses / Revenue) this year
       ÷
       (Selling & Admin Expenses / Revenue) last year
```

**What it detects:** Disproportionate growth in selling, general, and administrative expenses relative to sales (SGAI > 1) may indicate declining operating efficiency or unusual cost deferrals.

---

#### TATA — Total Accruals to Total Assets

**Formula:**
```
TATA = (Net Income − Operating Cash Flow) / Total Assets
```

**What it detects:** This is the most powerful manipulation indicator. A large positive TATA means reported profit greatly exceeds cash collected — a red flag for accrual-based inflation of earnings. Normal companies have TATA close to zero or negative.

---

#### LVGI — Leverage Index

**Formula:**
```
LVGI = ((Long-Term Debt + Current Liabilities) / Total Assets) this year
       ÷
       ((Long-Term Debt + Current Liabilities) / Total Assets) last year
```

**What it detects:** Increasing leverage (LVGI > 1) may indicate deteriorating financial health — and creates incentive to manipulate earnings upward to reassure creditors.

---

**Interpretation:**

| M-Score | Interpretation |
|---------|---------------|
| > −1.78 | 🔴 Possible manipulation — earnings quality is suspect |
| −1.78 to −2.22 | 🟡 Grey zone — inconclusive |
| < −2.22 | 🟢 Likely clean — no strong manipulation signals |

*Important caveat:* The M-Score was calibrated on US companies. It should be treated as a screening tool that raises questions, not a definitive accusation. Low reliability is flagged when fewer than 5 of the 8 indices can be calculated.

**Dashboard effect:** If M-Score > −1.78 AND at least 5 indices are available, the Health Score receives a **−10 point penalty**.

---

## Chapter 7 — Banking Sector Ratios

Banks operate very differently from standard companies — they use deposits (liabilities) as the raw material to generate loans (assets). Standard ratios like Debt-to-Equity do not apply in the usual way. The dashboard uses a banking-specific ratio set aligned with the international **CAMELS** framework.

> **Colour legend:** 🟢 healthy · 🟡 watch · 🔴 concern

---

### 7.1 Profitability Ratios

#### Net Interest Margin (NIM)

**What it measures:** The difference between interest income earned on loans and interest paid on deposits, expressed as a percentage of earning assets.

**Formula:**
```
NIM = Net Interest Income / Earning Assets

where: Net Interest Income = Interest Income − Interest Expense
       Earning Assets = Total loans + investment securities
```

**Why it matters:** NIM is the core profitability driver for banks. A bank that borrows at 8% and lends at 14% has a 6% NIM. Declining NIM may indicate rising funding costs or competitive pressure on lending rates.

**Worked example:**
- Interest Income = 8,000 M₮, Interest Expense = 4,000 M₮
- Net Interest Income = 4,000 M₮
- Earning Assets = 40,000 M₮
- NIM = 4,000 / 40,000 = **10%** (Mongolian banks typically range 6–15%)

**How to interpret:**

| Result | Meaning |
|--------|---------|
| > 6% | 🟢 Strong |
| 3–6% | 🟡 Acceptable |
| < 3% | 🔴 Thin margins |

---

#### ROA, ROE, Net Profit Margin

These ratios use the same formulas as standard companies (see §4.4), but with different benchmarks because banks are highly leveraged by nature.

**Bank benchmarks:**

| Ratio | 🟢 Good | 🔴 Concern |
|-------|---------|-----------|
| ROA | > 1% | < 0.5% |
| ROE | > 10% | < 5% |
| Net Profit Margin | > 15% | < 5% |

---

#### Interest Income Ratio

**What it measures:** What fraction of total bank revenue comes from interest (vs. fee income).

**Formula:**
```
Interest Income Ratio = Interest Income / Total Revenue
```

**Why it matters:** Banks with very high interest income concentration are more sensitive to interest rate changes. Diversified fee income provides stability.

---

### 7.2 Capital Adequacy Ratios

#### Equity-to-Assets

**What it measures:** The proportion of the bank's assets funded by shareholders' own equity.

**Formula:**
```
Equity-to-Assets = Total Equity / Total Assets
```

**Why it matters:** Banks operate with very high leverage (most assets funded by deposits). The equity cushion is what absorbs losses before depositors are affected. International standards (Basel III) require at minimum ~8%.

**How to interpret:**

| Result | Meaning |
|--------|---------|
| > 12% | 🟢 Well-capitalised |
| 8–12% | 🟡 Adequate |
| < 8% | 🔴 Undercapitalised |

---

#### Equity Multiplier

**What it measures:** How many tenge of assets the bank controls per tenge of shareholder equity — the inverse of Equity-to-Assets.

**Formula:**
```
Equity Multiplier = Total Assets / Total Equity
```

**How to interpret:**

| Result | Meaning |
|--------|---------|
| < 8× | 🟢 Conservative |
| 8–12× | 🟡 Normal for banks |
| > 15× | 🔴 Highly leveraged |

---

### 7.3 Asset Quality Ratios

#### NPL Ratio — Non-Performing Loan Ratio

**What it measures:** The percentage of loans that are not being repaid as agreed (typically 90+ days overdue).

**Formula:**
```
NPL Ratio = Non-Performing Loans / Total Loans
```

**Why it matters:** The NPL ratio is the most direct measure of lending quality. Rising NPLs consume the bank's capital and earnings.

**How to interpret:**

| Result | Meaning |
|--------|---------|
| < 2% | 🟢 Excellent credit quality |
| 2–5% | 🟡 Watch |
| > 5% | 🔴 Asset quality deteriorating |

---

#### Coverage Ratio (Loan Loss Reserve Ratio)

**What it measures:** Whether the bank has set aside enough provisions to cover its non-performing loans.

**Formula:**
```
Coverage Ratio = Loan Loss Reserves / Non-Performing Loans
```

**Why it matters:** A coverage ratio above 100% means the bank has more provisions than its current bad loans — a comfortable buffer. Below 100% means some losses are not yet provisioned.

**How to interpret:**

| Result | Meaning |
|--------|---------|
| > 150% | 🟢 Conservatively provisioned |
| 100–150% | 🟡 Adequate |
| < 100% | 🔴 Under-provisioned; potential losses to absorb |

---

#### Loan Loss Reserve Ratio & Provision to Loans

**Loan Loss Reserve Ratio** = Loan Loss Reserves / Total Loans — shows the overall buffer relative to the entire portfolio.

**Provision to Loans** = Loan Loss Provision (the year's expense) / Total Loans — shows how much the bank is charging to earnings this year to cover expected future loan losses.

---

### 7.4 Liquidity Ratios

#### Loan-to-Deposit Ratio (LDR)

**What it measures:** For every tenge deposited, how many tenge has the bank lent out?

**Formula:**
```
LDR = Total Loans / Total Deposits
```

**Why it matters:** This is the most important bank liquidity ratio. An LDR of 95% means the bank has lent out almost everything deposited — leaving little buffer if depositors suddenly want their money back. Below 70% means the bank is sitting on idle deposits and not efficiently deploying capital.

**Worked example:**
- Loans = 45,000 M₮, Deposits = 50,000 M₮
- LDR = 45,000 / 50,000 = **90%**

**How to interpret:**

| Result | Meaning |
|--------|---------|
| 70–90% | 🟢 Sweet spot |
| 90–110% | 🟡 Elevated; monitor liquidity |
| > 110% | 🔴 Overextended; liquidity risk |
| < 60% | 🟡 Over-liquid; efficiency concern |

---

#### Cash-to-Deposits, Loans-to-Assets, Securities-to-Assets

These additional liquidity measures provide further texture:

| Ratio | Formula | What It Shows |
|-------|---------|---------------|
| Cash to Deposits | Cash / Total Deposits | Immediate liquidity buffer |
| Loans to Assets | Total Loans / Total Assets | How much of the bank is lending vs. other activities |
| Securities to Assets | Investment Securities / Total Assets | Bond/securities portfolio as a liquidity reserve |

---

### 7.5 Efficiency Ratios

#### Cost-to-Income Ratio

**What it measures:** The percentage of operating income consumed by operating expenses — the "efficiency ratio" of banking.

**Formula:**
```
Cost-to-Income = Operating Expenses / Operating Income
```

**Why it matters:** A lower ratio is better. If a bank spends 70 tenge to earn 100 tenge, its efficiency ratio is 70% — leaving only 30 tenge to cover credit losses and profit.

**How to interpret:**

| Result | Meaning |
|--------|---------|
| < 40% | 🟢 Excellent efficiency |
| 40–55% | 🟡 Good |
| 55–70% | 🟡 Watch |
| > 70% | 🔴 Cost control needed |

---

### 7.6 Banking Forensic Score (B1–B8)

For banks, the standard Piotroski/Beneish scores are replaced by a sector-specific 8-point checklist:

| # | Criterion | Passes When |
|---|-----------|-------------|
| B1 | ROA positive | ROA > 0 |
| B2 | ROA improving | ROA this year > last year |
| B3 | NPL decreasing | NPL ratio this year < last year |
| B4 | Coverage adequate | Loan Loss Reserves / NPL ≥ 1.0 |
| B5 | LDR not excessive | Loan-to-Deposit ≤ 90% |
| B6 | Efficiency improving | Cost-to-Income this year < last year |
| B7 | NIM stable or improving | NIM this year ≥ last year |
| B8 | Capital strengthening | Equity/Assets this year > last year |

---

## Chapter 8 — Insurance Sector Ratios

Insurance companies earn money by collecting premiums and paying out claims. Their financial analysis focuses on **underwriting profitability** (are claims smaller than premiums?) and **solvency** (can they pay all future claims?).

---

### 8.1 Underwriting Ratios

#### Loss Ratio

**What it measures:** What percentage of earned premiums is paid out as claims.

**Formula:**
```
Loss Ratio = Claims Incurred / Net Premiums Earned
```

**Why it matters:** If an insurer collects 100 M₮ in premiums and pays 80 M₮ in claims, the loss ratio is 80%. A ratio approaching or exceeding 100% means the core insurance business is unprofitable.

**Worked example:**
- Claims = 600 M₮, Net Premiums = 1,000 M₮
- Loss Ratio = 600 / 1,000 = **60%** 🟢

**How to interpret:**

| Result | Meaning |
|--------|---------|
| < 60% | 🟢 Excellent underwriting |
| 60–75% | 🟡 Good |
| 75–100% | 🟡 Watch; claims pressure |
| > 100% | 🔴 Paying out more than earning in premiums |

---

#### Expense Ratio

**What it measures:** What percentage of earned premiums is spent on running the insurance operation (administration, agent commissions, etc.).

**Formula:**
```
Expense Ratio = Underwriting Expenses / Net Premiums Earned
```

**How to interpret:**

| Result | Meaning |
|--------|---------|
| < 20% | 🟢 Lean operation |
| 20–30% | 🟡 Normal |
| > 35% | 🔴 High overhead |

---

#### Combined Ratio

**What it measures:** The total cost of the insurance business — claims plus operating expenses — as a percentage of premiums. This is the single most important underwriting metric.

**Formula:**
```
Combined Ratio = Loss Ratio + Expense Ratio
```

**Why it matters:** A Combined Ratio below 100% means the insurer is making an **underwriting profit** — it spends less on claims and expenses than it collects in premiums. Above 100% is an underwriting loss, which must be offset by investment income.

**Worked example:**
- Loss Ratio = 60%, Expense Ratio = 28%
- Combined Ratio = 60% + 28% = **88%** 🟢 (12% underwriting profit)

**How to interpret:**

| Result | Meaning |
|--------|---------|
| < 90% | 🟢 Strong underwriting profit |
| 90–100% | 🟡 Marginal profit |
| 100–110% | 🔴 Underwriting loss; depends on investment income |
| > 110% | 🔴🔴 Significant losses |

---

### 8.2 Profitability Ratios

ROA, ROE, Net Profit Margin use the same formulas as §4.4 but with insurance-specific benchmarks:

| Ratio | 🟢 Good | 🔴 Concern |
|-------|---------|-----------|
| ROA | > 3% | < 1% |
| ROE | > 12% | < 5% |
| Net Profit Margin | > 10% | < 0% |

#### Underwriting Profit Margin

**Formula:**
```
Underwriting Profit Margin = (Net Premiums − Claims − Underwriting Expenses) / Net Premiums
```

This is simply 1 − Combined Ratio, but expressed as a signed margin.

---

### 8.3 Solvency Ratios

#### Solvency Ratio

**What it measures:** The equity cushion as a percentage of total assets.

**Formula:**
```
Solvency Ratio = Total Equity / Total Assets
```

**Why it matters:** Insurance regulators require a minimum solvency ratio to ensure companies can pay all future claims. In Mongolia, the Financial Regulatory Commission (FRC) sets this threshold.

**How to interpret:**

| Result | Meaning |
|--------|---------|
| > 30% | 🟢 Well-capitalised |
| 20–30% | 🟡 Meets regulatory minimum |
| < 20% | 🔴 Regulatory concern |

---

#### Reserve Coverage Ratio

**What it measures:** Whether the insurer has set aside enough claim reserves to cover one full year of expected claims.

**Formula:**
```
Reserve Coverage = Claim Reserves / Claims Incurred
```

**How to interpret:**

| Result | Meaning |
|--------|---------|
| > 1.5× | 🟢 Conservative |
| 1.0–1.5× | 🟡 Adequate |
| < 1.0× | 🔴 Under-reserved |

---

### 8.4 Liquidity Ratios

| Ratio | Formula | Benchmark |
|-------|---------|-----------|
| Investment Ratio | Investments / Total Assets | > 40% 🟢 |
| Cash to Liabilities | Cash / Total Liabilities | > 5% 🟢 |
| OCF Ratio | Operating CF / Total Liabilities | Positive 🟢 |

The **Investment Ratio** is important for insurers because they invest premium float to generate additional income. A low investment ratio means the insurer is not productively deploying its capital.

---

### 8.5 Growth Ratios

| Ratio | Formula | What It Shows |
|-------|---------|---------------|
| Premium Growth | (Premiums this year − last year) / Premiums last year | Market expansion or contraction |
| Revenue Growth | (Revenue this year − last year) / Revenue last year | Overall business growth |

---

### 8.6 Insurance Forensic Score (I1–I8)

| # | Criterion | Passes When |
|---|-----------|-------------|
| I1 | ROA positive | ROA > 0 |
| I2 | ROA improving | ROA this year > last year |
| I3 | Underwriting profitable | Combined Ratio < 100% |
| I4 | Combined ratio improving | Combined Ratio this year < last year |
| I5 | Solvent | Solvency Ratio ≥ 100% (equity covers liabilities) |
| I6 | Reserves adequate | Reserve Coverage ≥ 1.0× |
| I7 | Loss ratio improving | Loss Ratio this year < last year |
| I8 | Cash flow positive | Operating CF > 0 |

---

## Chapter 9 — Finance / NBFI Sector Ratios

**Non-Bank Financial Institutions (NBFIs)** include lending companies (microfinance, consumer credit), securities firms, and holding companies. They function similarly to banks — borrowing money and lending it out — but operate under different regulations and serve different market segments.

---

### 9.1 Profitability Ratios

#### Yield on Earning Assets

**What it measures:** The average interest rate the NBFI earns on its loan portfolio and investments.

**Formula:**
```
Yield on Earning Assets = Interest Income / Earning Assets
```

**Variables:**
- **Interest Income** (Income Statement): all income earned from lending
- **Earning Assets**: loans outstanding + investment portfolio

**Why it matters:** This is the "top line" of a lending business. If a microfinance company lends at an average yield of 18%, that is its revenue-per-asset rate. Compare this to Cost of Funds (below) to understand the spread.

**Worked example:**
- Interest Income = 3,000 M₮, Earning Assets = 20,000 M₮
- Yield on Earning Assets = 3,000 / 20,000 = **15%**

---

#### Cost of Funds

**What it measures:** The average interest rate the NBFI pays to borrow money (its "cost of raw material").

**Formula:**
```
Cost of Funds = Interest Expense / Total Borrowings
```

**Worked example:**
- Interest Expense = 1,200 M₮, Total Borrowings = 15,000 M₮
- Cost of Funds = 1,200 / 15,000 = **8%**

---

#### Interest Spread

**What it measures:** The difference between what the NBFI earns on loans and what it pays for funding.

**Formula:**
```
Interest Spread = Yield on Earning Assets − Cost of Funds
```

**Worked example:**
- Yield = 15%, Cost of Funds = 8%
- Interest Spread = **7%**

**Why it matters:** The spread is the NBFI's gross profit margin from lending. A positive spread is fundamental to viability. A negative spread would mean the company is paying more for funds than it earns from lending.

**How to interpret:**

| Result | Meaning |
|--------|---------|
| > 5% | 🟢 Healthy spread |
| 3–5% | 🟡 Adequate |
| < 3% | 🔴 Thin; any cost increases will hurt |
| < 0% | 🔴🔴 Unsustainable |

---

#### Net Interest Margin (NIM)

The NIM for NBFIs uses the same formula as for banks (see §7.1) but has different benchmarks reflecting higher lending rates:

**How to interpret (NBFI context):**

| Result | Meaning |
|--------|---------|
| > 8% | 🟢 Strong (typical for microfinance) |
| 4–8% | 🟡 Acceptable |
| < 4% | 🔴 Thin margins |

---

#### ROA, ROE, Net Profit Margin

Same formulas as §4.4. NBFI-specific benchmarks:

| Ratio | 🟢 Good | 🔴 Concern |
|-------|---------|-----------|
| ROA | > 1.6% | < 0.5% |
| ROE | > 15% | < 5% |
| Net Profit Margin | > 10% | < 0% |

---

### 9.2 Efficiency Ratios

#### Cost-to-Income Ratio

Same formula as §7.5 (Operating Expenses / Operating Income).

**NBFI benchmark:**

| Result | Meaning |
|--------|---------|
| < 40% | 🟢 Excellent |
| 40–50% | 🟡 Good |
| > 60% | 🔴 High cost structure |

---

#### Operating Expense Ratio

**Formula:**
```
Operating Expense Ratio = Operating Expenses / Total Assets
```

Shows the cost to manage the asset base, independent of revenue.

---

#### Non-Interest Income Ratio

**Formula:**
```
Non-Interest Income Ratio = Non-Interest Income / Total Income
```

Shows how much income comes from fees, commissions, and other non-lending sources — important for revenue diversification.

---

#### Asset Utilisation

**Formula:**
```
Asset Utilisation = Total Income / Total Assets
```

Shows how much income the NBFI generates per tenge of assets — a combined measure of both yield and deployment.

---

### 9.3 Leverage Ratios

NBFIs naturally carry more debt than standard companies because lending is their business. Benchmarks are calibrated accordingly.

| Ratio | Formula | 🟢 Good | 🔴 Concern |
|-------|---------|---------|-----------|
| Debt-to-Equity | Total Borrowings / Total Equity | < 4× | > 8× |
| Debt-to-Assets | Total Borrowings / Total Assets | < 70% | > 85% |
| Equity Ratio | Total Equity / Total Assets | > 15% | < 10% |
| Equity Multiplier | Total Assets / Total Equity | < 6× | > 10× |

---

### 9.4 Liquidity Ratios

| Ratio | Formula | 🟢 Target |
|-------|---------|----------|
| Loan-to-Assets | Loan Portfolio / Total Assets | > 60% for mature lenders |
| Cash Ratio | Cash / Total Liabilities | > 5% |
| OCF Ratio | Operating CF / Total Liabilities | Positive |

The **Loan-to-Assets** ratio is flipped from what you might expect — a *higher* ratio is better for a lending-focused NBFI, because it means the company is actively deploying capital into loans rather than holding idle assets.

---

### 9.5 Asset Quality Ratios

#### NPA Ratio — Non-Performing Assets Ratio

**What it measures:** The percentage of the loan portfolio that is delinquent.

**Formula:**
```
NPA Ratio = Non-Performing Loans / Total Loan Portfolio
```

**How to interpret:**

| Result | Meaning |
|--------|---------|
| < 2% | 🟢 Excellent credit quality |
| 2–5% | 🟡 Watch |
| > 5% | 🔴 Asset quality deteriorating |

---

#### Provision Coverage

**Formula:**
```
Provision Coverage = Loan Loss Reserves / Non-Performing Loans
```

**How to interpret:** Same as bank Coverage Ratio (§7.3) — > 100% means fully provisioned.

---

### 9.6 Finance/NBFI Forensic Score (F1–F8)

| # | Criterion | Passes When |
|---|-----------|-------------|
| F1 | ROA positive | ROA > 0 |
| F2 | ROA improving | ROA this year > last year |
| F3 | NIM stable or improving | NIM this year ≥ last year |
| F4 | NPA decreasing | NPA ratio this year < last year |
| F5 | Efficiency improving | Cost-to-Income this year < last year |
| F6 | Leverage not increasing | Debt-to-Equity this year ≤ last year |
| F7 | Cash flow positive | Operating CF > 0 |
| F8 | Provisions adequate | Provision Coverage ≥ 1.0× |

---

## Chapter 10 — Valuation Multiples

Valuation multiples compare a company's **market price** to its **fundamental financial metrics**. They answer the question: *is this stock cheap or expensive relative to what the company earns or owns?*

All multiples require price data (fetched from MSE) plus the relevant financial metric.

---

### Universal Multiples (All Company Types)

#### P/E — Price-to-Earnings

**Formula:**
```
P/E = Market Capitalisation / Net Income
    = Share Price / Earnings Per Share
```

**What it means:** If P/E = 10×, you are paying 10 tenge for every 1 tenge of annual earnings. A lower P/E is generally cheaper, but a very low P/E may reflect poor growth prospects or distress.

**Context:** MSE-listed companies often trade at P/E ratios of 5–15×. International emerging markets average 10–20×.

---

#### P/BV — Price-to-Book Value

**Formula:**
```
P/BV = Market Capitalisation / Total Equity
```

**What it means:** If P/BV = 1.5×, the market values the company at 1.5 times its accounting net worth. Below 1× may indicate a deeply undervalued or troubled company.

---

### Standard Company Multiples

#### EV/EBIT

**Formula:**
```
EV/EBIT = Enterprise Value / EBIT

Enterprise Value = Market Capitalisation + Total Liabilities − Cash
```

**What it means:** Similar to P/E but adjusted for the company's debt structure. Useful for comparing companies with different capital structures.

*(Note: The dashboard uses EBIT as a proxy for EBITDA since depreciation data is not consistently available in MSE filings.)*

---

#### FCF Yield — Free Cash Flow Yield

**Formula:**
```
FCF Yield = (Operating CF + Investing CF) / Market Capitalisation
```

**What it means:** A high FCF yield means the company generates substantial cash relative to its market value — often a sign of undervaluation.

---

### Banking Multiples

| Multiple | Formula | What It Shows |
|----------|---------|---------------|
| P/TBV | MCap / (Equity − Intangibles) | Price vs. tangible assets only |
| P/PPOP | MCap / Pre-Provision Operating Profit | Price vs. earnings before credit costs |
| P/NII | MCap / Net Interest Income | Price vs. core lending income |

**P/TBV** is preferred over P/BV for banks because intangible assets (goodwill, etc.) cannot absorb loan losses — only tangible capital can.

---

### Insurance Multiples

| Multiple | Formula | What It Shows |
|----------|---------|---------------|
| P/NPE | MCap / Net Premiums Earned | Price vs. premium volume |
| P/UWP | MCap / Underwriting Profit | Price vs. core insurance profitability |

---

### Holding Company Multiples

| Multiple | Formula | What It Shows |
|----------|---------|---------------|
| P/NAV | MCap / Total Equity | Price vs. net asset value of the portfolio |

---

## Chapter 11 — Red Flags

The Red Flags tab provides two layers of warning analysis.

### 11.1 Rule-Based Flags (Instant Load)

These are triggered automatically whenever specific thresholds are crossed:

| Flag | Trigger Condition | What It Means |
|------|------------------|---------------|
| **DSRI Spike** | Receivables Index > 1.5 | Receivables growing much faster than revenue — possible revenue manipulation |
| **TATA Jump** | Total Accruals to Assets increasing significantly | Profit is driven by accruals, not cash — earnings quality concern |
| **D/E Acceleration** | Debt-to-Equity rising sharply year-over-year | Leverage increasing rapidly — financial risk growing |
| **M-Score Flag** | Beneish M-Score > −1.78 | Quantitative signal of possible earnings manipulation |
| **Current Ratio Drop** | Current Ratio deteriorating significantly | Liquidity is weakening year-over-year |

### 11.2 AI-Powered Flags

After the rule-based flags load, the dashboard sends all ratio data, forensic scores, valuation multiples, and price history to an AI model which generates a contextual analysis.

The AI analysis is **sector-aware** — it understands the difference between a 90% LDR for a bank (normal) versus 90% Debt-to-Assets for a manufacturer (alarming).

**Severity levels:**

| Badge | Colour | Meaning |
|-------|--------|---------|
| HIGH | 🔴 Red | Requires immediate attention; significant risk |
| MEDIUM | 🟡 Amber | Worth investigating; monitor closely |
| LOW | 🔵 Blue | Minor concern; context-dependent |
| CLEAR | 🟢 Green | No concern identified |

---

## Chapter 12 — Portfolio Analysis

### 12.1 Building a Portfolio

1. From the **Screener**, click "Add to Portfolio" for companies you want to track.
2. On the **Portfolio → Holdings tab**, adjust weights using the sliders.
3. Click **"Equal Weight"** to distribute weight evenly across all holdings.
4. Weights must sum to 100%.

### 12.2 Efficient Frontier

The **efficient frontier** is a scatter plot where:
- **X-axis** = annualised portfolio risk (standard deviation of daily returns)
- **Y-axis** = annualised portfolio return

Each dot represents one possible portfolio — a random mix of the same companies with different weightings. The curve formed by the outermost dots is the "frontier" — the set of portfolios that give the maximum return for a given level of risk.

**How to use it:** Portfolios below and to the right of the frontier are inefficient — you could achieve the same return with less risk, or more return with the same risk, by rebalancing.

The system generates **200 random portfolio combinations** to map the frontier.

### 12.3 Max-Sharpe Portfolio

The **Sharpe Ratio** measures return per unit of risk:
```
Sharpe Ratio = (Portfolio Return − Risk-Free Rate) / Portfolio Volatility
```

The dashboard uses a **risk-free rate of 12% per annum**, reflecting the approximate yield on Mongolian government securities. This is subtracted from both the portfolio return (in the optimiser) and each individual company's annual return (in the per-company stats table) before dividing by volatility.

The **Max-Sharpe portfolio** is the specific weight combination that maximises this ratio — theoretically the "best" risk-adjusted portfolio. The dashboard calculates this using a mathematical optimiser (SLSQP) with long-only constraints (no negative weights).

### 12.4 Risk Metrics

#### Sortino Ratio

```
Sortino Ratio = (Portfolio Return − Risk-Free Rate) / Downside Deviation
```

Similar to the Sharpe Ratio, but only penalises **downside** volatility (negative returns). Uses the same 12% risk-free rate. A portfolio that is volatile upward but stable downward has a high Sortino ratio — generally preferred.

#### Maximum Drawdown

The largest peak-to-trough percentage loss over the historical period. If a portfolio peaked at 100 M₮ and later fell to 70 M₮, the maximum drawdown is 30%.

#### CVaR 95% — Conditional Value at Risk

CVaR 95% is the average loss on the worst 5% of trading days. If daily returns are sorted from worst to best, CVaR takes the average of the bottom 5% — it quantifies "tail risk" or what happens when things go badly.

---

## Appendix A — Quick-Reference Benchmarks by Sector

### Standard Company Benchmarks

| Ratio | 🟢 Good | 🔴 Concern |
|-------|---------|-----------|
| Current Ratio | > 2.0× | < 1.0× |
| Quick Ratio | > 1.5× | < 0.8× |
| Debt-to-Equity | < 1.0× | > 2.5× |
| Interest Coverage | > 5× | < 2× |
| ROA | > 10% | < 2% |
| ROE | > 20% | < 5% |
| Net Profit Margin | > 10% | < 3% |
| Asset Turnover | > 1.5× | < 0.8× |
| DSO | < 30 days | > 60 days |
| Altman Z | > 2.99 (Safe) | < 1.23 (Distress) |
| Piotroski F | ≥ 7 (Strong) | ≤ 2 (Weak) |
| Beneish M | < −2.22 (Clean) | > −1.78 (Suspicious) |

### Bank Benchmarks

| Ratio | 🟢 Good | 🔴 Concern |
|-------|---------|-----------|
| NIM | > 6% | < 3% |
| ROA | > 1% | < 0.5% |
| ROE | > 10% | < 5% |
| NPL Ratio | < 2% | > 5% |
| Coverage Ratio | > 150% | < 100% |
| LDR | 70–90% | > 110% |
| Equity-to-Assets | > 12% | < 8% |
| Cost-to-Income | < 40% | > 70% |

### Insurance Benchmarks

| Ratio | 🟢 Good | 🔴 Concern |
|-------|---------|-----------|
| Combined Ratio | < 90% | > 100% |
| Loss Ratio | < 60% | > 85% |
| Expense Ratio | < 20% | > 35% |
| ROA | > 3% | < 1% |
| Solvency Ratio | > 30% | < 20% |
| Reserve Coverage | > 1.5× | < 1.0× |
| Investment Ratio | > 50% | < 30% |

### Finance / NBFI Benchmarks

| Ratio | 🟢 Good | 🔴 Concern |
|-------|---------|-----------|
| NIM | > 8% | < 4% |
| Interest Spread | > 5% | < 3% |
| Yield on Earning Assets | > 12% | < 6% |
| ROA | > 1.6% | < 0.5% |
| ROE | > 15% | < 5% |
| Cost-to-Income | < 40% | > 60% |
| Debt-to-Equity | < 4× | > 8× |
| NPA Ratio | < 2% | > 5% |
| Provision Coverage | > 100% | < 70% |
| Loan-to-Assets | > 60% | < 30% |

---

## Appendix B — Glossary

| Term | Definition |
|------|-----------|
| **Accruals** | Accounting entries that recognise income or expenses before cash changes hands. High accruals relative to cash flow can signal earnings manipulation. |
| **Balance Sheet** | A financial statement showing what a company owns (assets) and owes (liabilities), with the difference being equity. Snapshot at year-end. |
| **CAMELS** | International bank rating framework: Capital, Asset quality, Management, Earnings, Liquidity, Sensitivity to market risk. |
| **Cash Flow Statement** | Shows actual cash inflows and outflows from operations, investments, and financing activities. |
| **COGS** | Cost of Goods Sold — the direct cost of producing goods. |
| **DuPont** | Method of decomposing ROE into Margin × Turnover × Leverage to understand what drives profitability. |
| **EBIT** | Earnings Before Interest and Tax — operating profit. |
| **Earning Assets** | Assets that generate interest income: loans, bonds, and securities. |
| **Efficient Frontier** | The set of portfolio combinations that offer the highest return for a given level of risk. |
| **Equity** | Shareholders' net ownership stake = Assets − Liabilities. |
| **FRC** | Financial Regulatory Commission — Mongolia's financial sector regulator. |
| **Income Statement** | Shows revenue, expenses, and net income over the reporting period. |
| **Leverage** | Use of borrowed money to amplify returns (and risks). |
| **M₮** | Mongolian Tögrögs in millions (the unit used throughout this dashboard). |
| **Market Capitalisation** | Total market value of all outstanding shares = Share Price × Shares Outstanding. |
| **MSE** | Mongolian Stock Exchange. |
| **NBFI** | Non-Bank Financial Institution — lending company, securities firm, or holding company. |
| **Net Income** | The "bottom line" — profit after all costs, interest, and taxes. |
| **NPL** | Non-Performing Loan — a loan where the borrower has stopped making payments (usually 90+ days overdue). |
| **NPA** | Non-Performing Assets — similar to NPL; used for NBFI context. |
| **ROA** | Return on Assets = Net Income / Total Assets. |
| **ROE** | Return on Equity = Net Income / Total Equity. |
| **Sharpe Ratio** | (Return − Risk-Free Rate) / total volatility. Uses 12% p.a. risk-free rate. Higher is better. |
| **Sortino Ratio** | Return per unit of downside risk only. Higher is better. |
| **Solvency** | Ability to meet long-term financial obligations. |
| **Working Capital** | Current Assets − Current Liabilities. The short-term financial buffer. |
| **YoY** | Year-over-Year — comparing the current period to the same period in the prior year. |

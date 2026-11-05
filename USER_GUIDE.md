# Comprehensive User & System Architecture Guide
**AI Stock Market Research & Ranking Agent for NSE and BSE**

---

## 1. Introduction & Core Purpose

The **AI Stock Market Research & Ranking Agent for NSE and BSE** is an institutional-grade, full-stack quantitative equity research platform built natively on the **Django 5.x web framework**.

### What This Software Is:
- A **research and educational decision-support tool** for securities listed on the National Stock Exchange of India (NSE) and Bombay Stock Exchange (BSE).
- A **multi-agent quantitative engine** that synthesizes fundamental accounting data, technical momentum indicators, regulatory filings, news sentiment, and cash-flow valuations into an objective, transparent score out of 100.
- A **risk-management workstation** equipped with concentration guardrails, capital-at-risk position sizing, stop-loss calculators, and point-in-time historical backtesting.

### What This Software Is NOT:
- **No Guaranteed Returns**: It does NOT promise, predict, or guarantee positive returns or profits.
- **No Personalized Investment Advice**: It does NOT evaluate your personal net worth, tax status, or individual risk tolerance. Every investor must consult a SEBI-registered Investment Adviser (RIA).
- **Statutory Risk Disclosure**: Every report, screen, and export includes a mandatory regulatory compliance disclaimer.

---

## 2. High-Level System Architecture

The application operates as a synchronized pipeline connecting external exchange feeds, background quantitative and AI agents, the Django ORM database, and an institutional Bloomberg-style web UI:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   1. Market Data & Corporate Feeds                     │
│  yfinance Direct Feed (Live Quotes, FastInfo, Indices, Historical OHLCV)│
│  Exchange Disclosures & News (BSE/NSE Filings, RSS Feeds, Google News) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               2. Multi-Agent AI & Quantitative Layer                  │
│  8 Specialized Agents: Universe, Fundamentals, Technical, News,       │
│  Filings, Sector/Macro, Skeptical Risk, Composite Ranking             │
│  Models: 2-Stage Fade DCF, 9 Investor Philosophies, Portfolio Rules   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  3. Persistence & Database Layer                       │
│  Django 5.x ORM & SQLite Database (data/stock_django.db)               │
│  Models: Stock, PriceHistory, FundamentalData, AgentEvaluation, etc.   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│           4. Institutional Django Web Interface (Port 8000)            │
│  1. Home (Executive Dashboard)  | 2. Stock Analysis (Deep Dive & DCF)  │
│  3. Rankings (Screener/Reports) | 4. Portfolio Tools (Guardrails)      │
│  5. Backtesting (vs NIFTY 50)   | 6. Settings (Scoring Weights & LLM)  │
│  7. IPO Analysis (Forensics & 9 Strategies)                            │
│  REST API V1 (/api/v1/)                                                │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. The 8 Specialized AI Agents (How They Function in the Background)

The platform distributes complex stock analysis across **8 specialized agents**. Each agent acts like a dedicated research analyst inside an institutional hedge fund:

```
Universe Agent ──► Fundamentals Agent ──► Technical Agent ──► News Agent
      │                                                           │
      ▼                                                           ▼
Ranking Agent ◄── Skeptical Risk Agent ◄── Sector Agent ◄── Filings Agent
```

### Agent 1: Universe Screener Agent ([`src/agents/universe_agent.py`](file:///f:/Projects/Stock-AI-Agent/src/agents/universe_agent.py))
- **Role**: Gatekeeper and liquidity filter.
- **How It Works**:
  1. Ingests Nifty 500, BSE 500, or custom watchlists.
  2. Applies strict institutional screening: filters out penny stocks ($< ₹10$), removes illiquid securities ($< 50,000$ daily shares or turnover $< ₹50$ Lakhs), and flags companies below ₹500 Cr market capitalization.
  3. Eliminates securities with missing, corrupt, or insufficient trading history.

### Agent 2: Fundamental Analysis Agent ([`src/agents/fundamentals_agent.py`](file:///f:/Projects/Stock-AI-Agent/src/agents/fundamentals_agent.py))
- **Role**: Senior Financial Auditor and Value Analyst.
- **How It Works**:
  1. Computes multi-year compounding growth: Revenue CAGR and Net Profit CAGR.
  2. Calculates capital efficiency: **Return on Equity (ROE)**, **Return on Capital Employed (ROCE)**, and **Return on Assets (ROA)**.
  3. Solvency & Debt Stress Testing: **Debt-to-Equity ($D/E$) ratio** and **Interest Coverage Ratio** ($EBIT / Interest$).
  4. Cash Flow Quality: Verifies **Free Cash Flow (FCF)** vs Net Income (checks if reported profits translate into real cash).
  5. Computes valuation multiples: Trailing and forward $P/E$, $P/B$, $EV/EBITDA$, $PEG$ ratio, and Dividend Yield.

### Agent 3: Technical Indicators Agent ([`src/agents/technical_agent.py`](file:///f:/Projects/Stock-AI-Agent/src/agents/technical_agent.py))
- **Role**: Quantitative Technician and Market Timer.
- **How It Works**:
  1. Trend Analysis: Computes 50-day and 200-day Simple Moving Averages (**SMA 50**, **SMA 200**) to identify Golden Cross / Death Cross configurations.
  2. Momentum & Overbought/Oversold: Calculates 14-period **RSI** and **MACD** (12, 26, 9) signal crossovers.
  3. Volatility: Computes **Bollinger Bands** (20-day, $\pm 2\sigma$) and 14-day **Average True Range (ATR)**.
  4. Institutional Accumulation: Tracks **On-Balance Volume (OBV)** to detect smart-money accumulation before price breakouts.
  5. 52-Week Range: Measures proximity to 52-week High and Low.

### Agent 4: News & Sentiment Agent ([`src/agents/news_agent.py`](file:///f:/Projects/Stock-AI-Agent/src/agents/news_agent.py))
- **Role**: Real-Time Intelligence & News Analyst.
- **How It Works**:
  1. Continuously tracks Google News, RSS feeds, and business portals (BSE announcements, Moneycontrol, Economic Times).
  2. Performs Natural Language Processing (NLP) to classify events into Earnings Updates, Management Guidance, Capex/Expansions, Regulatory Actions, or Corporate Governance issues.
  3. **Strict Citation Standard**: Every qualitative claim must include its **Source Title**, **URL**, and **Publication Date**.

### Agent 5: Corporate Filings & Governance Agent ([`src/agents/filings_agent.py`](file:///f:/Projects/Stock-AI-Agent/src/agents/filings_agent.py))
- **Role**: Forensic Accounting & Governance Sleuth.
- **How It Works**:
  1. Inspects quarterly shareholding patterns: checks promoter holding percentages.
  2. **Promoter Pledge Sentry**: Flags any promoter pledge $> 10\%$ as an immediate high-risk penalty.
  3. Scans auditor reports for qualified opinions, auditor resignations, related-party transactions, or abnormal tax disparities.

### Agent 6: Sector & Macro Agent ([`src/agents/sector_agent.py`](file:///f:/Projects/Stock-AI-Agent/src/agents/sector_agent.py))
- **Role**: Sector Strategist and Peer Benchmarking Specialist.
- **How It Works**:
  1. Compares the target company against peer competitors within the exact same industry.
  2. Evaluates sector cyclicality and sensitivity to macroeconomic factors (e.g., RBI interest rate policy, commodity prices, USD/INR foreign exchange fluctuations).

### Agent 7: Skeptical Risk Agent ("Devil's Advocate") ([`src/agents/risk_agent.py`](file:///f:/Projects/Stock-AI-Agent/src/agents/risk_agent.py))
- **Role**: Chief Risk Officer who actively tries to disprove the investment thesis.
- **How It Works**:
  1. Analyzes 6 categorical risk buckets: **Valuation Risk**, **Debt Risk**, **Competitive Risk**, **Governance Risk**, **Cyclicality Risk**, and **Negative Catalysts**.
  2. **Mandatory Thesis Invalidation Conditions**: Enforces that every stock analysis MUST output at least three specific events that would prove the bull case wrong (e.g., *"Revenue deceleration below 6% for 2 quarters"* or *"Operating margin compression $> 250$ bps"*).

### Agent 8: Composite Ranking & Synthesis Agent ([`src/agents/ranking_agent.py`](file:///f:/Projects/Stock-AI-Agent/src/agents/ranking_agent.py))
- **Role**: Portfolio General and Final Arbiter.
- **How It Works**:
  1. Combines outputs from all agents into a unified, transparent mathematical formula out of 100.
  2. Assigns a research label: **Strong Buy** ($\ge 70$), **Research** ($50–69$), or **Watch** ($< 50$).
  3. Produces bull/bear cases and compiles the final executive research notes.

---

## 4. Quantitative Valuation & Financial Models Explained

### A. The Institutional 2-Stage Fade DCF Valuation Model ([`src/analysis/dcf_valuator.py`](file:///f:/Projects/Stock-AI-Agent/src/analysis/dcf_valuator.py))
Unlike simplistic online DCF calculators that apply an unrealistic constant growth rate forever, this platform utilizes a professional institutional **2-Stage Fade DCF model**:

1. **Stage 1 (Years 1 to 5 - Explicit High Growth)**:
   Cash flows grow at the explicit FCF CAGR ($g_1$) calculated from historical financial performance.
2. **Stage 2 (Years 6 to 10 - Fade Transition Period)**:
   In reality, high returns attract competition. Growth linearly fades year-by-year from $g_1$ down to the terminal growth rate $g_T$, preventing massive terminal overvaluation.
3. **Stage 3 (Terminal Value via Gordon Growth Model with Spread Protection)**:
   Terminal value is discounted using WACC ($r$) and terminal growth ($g_T$):
   $$TV_{10} = \frac{FCF_{10} \times (1 + g_T)}{r - g_T}$$
   *Safety Rule*: The denominator is safeguarded to enforce $\max(r - g_T, 1.5\%)$ to prevent mathematical blowups when discount rates approach growth rates.
4. **Equity & Net Debt Adjustment**:
   $$Intrinsic\ Value\ Per\ Share = PV(Forecast\ FCFs) + PV(Terminal\ Value) + Cash\ Per\ Share - Debt\ Per\ Share$$
5. **Graham Number & Peter Lynch Fair Value Comparables**:
   - **Benjamin Graham Number**: $\sqrt{22.5 \times EPS \times BVPS}$
   - **Peter Lynch Fair Value**: $EPS \times \min(\max(CAGR \times 100, 5), 30)$

---

### B. The 9 Legendary Investor Strategy Philosophies ([`src/analysis/investor_philosophy.py`](file:///f:/Projects/Stock-AI-Agent/src/analysis/investor_philosophy.py))
For every stock, the platform calculates 9 distinct strategy scores (0 to 100), research labels (`BUY`, `HOLD`, `AVOID`), reasons, and key risks:

| Investor Philosophy | Investment Style | Core Quantitative Filters |
| :--- | :--- | :--- |
| **1. Warren Buffett** | Economic Moat & Value Quality | ROCE $> 15\%$, low debt ($D/E < 0.5$), high free cash conversion, predictable earnings. |
| **2. Charlie Munger** | Rational Quality Compounding | Exceptional capital returns, pristine balance sheet, avoidance of unforced operational errors. |
| **3. Benjamin Graham** | Deep Value & Margin of Safety | Low price-to-book ($P/B < 1.5$), current assets $> 1.5\times$ liabilities, conservative debt. |
| **4. Peter Lynch** | Growth at Reasonable Price (GARP) | $PEG \approx 1.0$, earnings growth $15\%–25\%$, manageable leverage, strong product tailwinds. |
| **5. Joel Greenblatt** | Magic Formula Investing | Ranks highest Return on Capital ($ROCE$) combined with highest Earnings Yield ($EBIT / EV$). |
| **6. Rakesh Jhunjhunwala** | Long-Term Domestic Compounding | Massive Indian addressable market, high operating leverage, high return on capital. |
| **7. Philip Fisher** | Innovation & Management Quality | Scuttlebutt analysis, high R&D commitment, long-term sales orientation, superior margins. |
| **8. Dolly Khanna** | Asset-Light Small/Mid-Caps | Niche market leaders, high ROCE, conservative debt, strong dividend distribution. |
| **9. Porinju Veliyath** | Contrarian Turnaround Opportunities | Undervalued asset plays, corporate restructuring candidates, turnaround in margin trajectory. |

---

### C. The Transparent Factor Scoring Formula ([`src/analysis/scoring.py`](file:///f:/Projects/Stock-AI-Agent/src/analysis/scoring.py))
The platform does NOT use a black box. The final composite score (0–100) is calculated mathematically as:

$$\begin{aligned}
Final\ Score = &\; + 30\% \times Quality\ Score \\
&\; + 20\% \times Growth\ Score \\
&\; + 15\% \times Valuation\ Score \\
&\; + 15\% \times Momentum\ Score \\
&\; + 10\% \times News/Catalyst\ Score \\
&\; - 10\% \times Risk\ Penalty
\end{aligned}$$

*Note: All weights are fully customizable in the Settings tab (`/settings/`).*

---

## 5. Step-by-Step User Walkthrough (The 6 Platform Tabs)

### Tab 1: Home (Executive Market Dashboard)
- **URL**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **What You See**:
  1. **Top Navbar Live Ticker Bar**: Real-time quotes for NIFTY 50, SENSEX, BANK NIFTY, and NIFTY IT, with continuous auto-polling every 45 seconds.
  2. **Market Breadth Visualizer**: Ratio of advancing, declining, and unchanged stocks across the monitored universe.
  3. **Today's Top-Ranked Equities**: Top 6 scored stocks with rank badges, composite progress bars, and direct research buttons.
  4. **Recent Market & Risk Alerts**: Real-time surveillance notices covering valuation spikes, RBI rate policy updates, and corporate governance scans.
  5. **Top Daily Gainers & Losers**: Biggest percentage movers of the trading day.

---

### Tab 2: Stock Analysis (Deep Dive Workstation)
- **URL**: [http://127.0.0.1:8000/research/RELIANCE.NS/](http://127.0.0.1:8000/research/RELIANCE.NS/) (Replace ticker with any NSE/BSE security)
- **Features**:
  1. **Quick Search**: Enter any symbol (e.g. `TCS`, `INFY`, `HDFCBANK`, `500325`) in the global search bar with instant autocomplete.
  2. **"Sync Live Quote" Button**: Click to query the live exchange feed; immediately updates current price, day change, P/E, and composite score.
  3. **Institutional Adjustable & Responsive Price & Technicals Chart**:
     - **Timeframe Selector (Range Filter)**: One-click buttons for `1M` (1 month), `3M` (3 months), `6M` (6 months), and `1Y / ALL`. Dynamically slices data and recalculates period return % and visible High/Low.
     - **Technical Indicator Overlays**: Interactive pill toggles for **Close Price**, **SMA 50** (Amber), **SMA 200** (Emerald), **Bollinger Bands (20D, 2σ)** (Purple cloud), **Volume Bars** (Cyan sub-pane), and **Support/Resistance Levels** (Dashed guidance).
     - **Scale Adjuster**: Toggle between **Linear** and **Logarithmic** price scale.
     - **Canvas Height Controls**: Switch dynamically between **Compact (S: 320px)**, **Standard (M: 440px)**, and **Expanded (L: 600px)**.
     - **Fullscreen Mode (⛶)**: Expand chart to full window monitor mode for comprehensive technical analysis.
     - **Interactive Zoom & Pan**: Mouse wheel or touch pinch-to-zoom into any specific trading day range; drag to pan along the timeline. Click **"↺ Reset Zoom"** to restore original view instantly.
     - **Auto-Responsive Layout**: Dynamically recalculates canvas dimensions upon tab change, window resize, or mobile screen rotation.
  4. **The 6 Inner Sub-Tabs**:
     - **📊 Price & Technicals**: The adjustable chart with ATR, OBV, 52W High/Low distance, Bollinger Band values, and Support/Resistance breakdown.
     - **🏛️ 9 Investor Strategies**: Cards for Buffett, Munger, Graham, Lynch, Greenblatt, Jhunjhunwala, Fisher, Dolly Khanna, and Porinju Veliyath showing scores, badges, reasons, and key risks.
     - **🧮 Interactive DCF Model**: Live sliders for FCF growth, WACC, and terminal growth. Dragging sliders instantly recalculates intrinsic fair value and margin of safety via AJAX.
     - **💼 Fundamentals & Peers**: Full balance-sheet metrics (ROE, ROCE, Debt/Equity, Margins, FCF, PEG) and sector peer comparison table.
     - **📰 News & Catalysts**: Curated positive, neutral, and cautious developments with source URLs and dates.
     - **🛑 Risk & Invalidation**: Categorical risks (Valuation, Debt, Competition, Governance, Cyclicality) and 3 explicit thesis invalidation conditions.

---

### Tab 3: Rankings & Screener
- **URL**: [http://127.0.0.1:8000/rankings/](http://127.0.0.1:8000/rankings/)
- **Features**:
  1. **Multi-Factor Screener**: Filter universe by Exchange (NSE/BSE), Sector, Action (`Strong Buy`, `Research`, `Watch`), or Minimum Composite Score.
  2. **Dynamic Sorting**: Sort by Rank, Composite Score, Quality, Growth, Valuation, Momentum, Price, or Day Change.
  3. **Export CSV**: Instant one-click download of all filtered rankings in CSV format.
  4. **Top-20 Institutional Structured Report**: Click "📄 View Top-20 Report" or "⬇️ Download Markdown" to generate a publication-grade equity research report complete with executive summary, tables, bull/bear cases, invalidations, and compliance disclaimers.

---

### Tab 4: Portfolio Tools & Risk Controls
- **URL**: [http://127.0.0.1:8000/portfolio/](http://127.0.0.1:8000/portfolio/)
- **Features**:
  1. **Real-Time Holdings & P&L**: Tracks shares, buy price, live market price, invested value, current value, and profit/loss (₹ and %). Prices sync automatically with live market quotes.
  2. **Adjustable Sector Allocation Chart**:
     - Toggle between **Donut Chart (🍩)** and **Horizontal Bar Chart (📊)**.
     - Displays sector weights, concentration limit breach warnings (>30%), and auto-scales across mobile and desktop displays.
  3. **Risk Guardrails & Concentration Alerts**:
     - *Conservative Guideline*: Flags any single stock exceeding 10% of portfolio.
     - *Hard Cap Breach Alert*: Generates a critical alert if any single stock exceeds 20% of portfolio, recommending an exact share trim.
     - *Sector Cap Breach Alert*: Warns if any single industry exceeds 30% of total assets, prompting diversification.
  4. **Interactive Position-Size Calculator**: Inputs portfolio equity, max risk % per trade, entry price, and stop-loss price; outputs recommended number of shares and risk capital.
  5. **Stop-Loss & Target Calculator**: Calculates 1.5x and 2.5x Risk/Reward targets using ATR volatility or fixed percentage risk.
  6. **Automated Rebalancing Suggestions**: Actionable recommendations to rebalance out of overweight assets into under-allocated sectors.

---

### Tab 5: Quant Backtesting
- **URL**: [http://127.0.0.1:8000/backtest/](http://127.0.0.1:8000/backtest/)
- **Features**:
  1. **Point-in-Time Simulation**: Uses only data that was publicly available on each historical rebalance date (eliminating look-ahead bias).
  2. **Adjustable Equity Curve vs Benchmark Chart**:
     - **Timeframe Selector**: Toggle ranges across `6M`, `1Y`, `2Y`, and `ALL (3Y)`.
     - **Series Isolation**: Toggle visibility for **Strategy Portfolio** and **NIFTY 50 Benchmark**.
     - **Scale Controls**: Switch between Linear and Logarithmic scale.
     - **Height & View Modes**: S (320px), M (440px), L (600px), and Fullscreen expansion (⛶).
     - **Interactive Zoom & Pan**: Wheel/touch zoom with single-click "↺ Reset Zoom".
  3. **Risk & Return Metrics**: Displays CAGR, Annualized Volatility ($\sigma$), Sharpe Ratio, Maximum Drawdown, Alpha, Beta, and Win Rate.
  4. **Trade Execution Log**: Complete chronological matrix of all historical rebalancing trades.

---

### Tab 6: Settings & Factor Weights
- **URL**: [http://127.0.0.1:8000/settings/](http://127.0.0.1:8000/settings/)
- **Features**:
  1. **Scoring Weights Editor**: Edit individual weights for Quality (0.30), Growth (0.20), Valuation (0.15), Momentum (0.15), Catalysts (0.10), and Risk Penalty (-0.10). Click "Save Scoring Weights" or "Reset to Defaults".
  2. **Screening Defaults Review**: View thresholds for minimum market cap (₹500 Cr), minimum volume (50,000 shares), and penny stock exclusions.
  3. **LLM & Provider Configuration**: Displays the configured inference model (e.g. GPT-4o-mini), temperature, and persistence paths.
  4. **Statutory Compliance Text**: Comprehensive review of SEBI educational disclaimers.

---

### Tab 7: IPO Analysis & 9 Legendary Strategies ([`apps/ipo/`](file:///f:/Projects/Stock-AI-Agent/apps/ipo/))
- **URL**: [http://127.0.0.1:8000/ipo/](http://127.0.0.1:8000/ipo/)
- **Institutional 30+ Years Rigor**:
  1. **Comprehensive IPO Universe (Official Exchange Timetable & Chittorgarh Calibrated)**:
     - **Currently Open for Bidding (Closes Today — 23 Oct)**:
       - **Jio Platforms Limited (`JIO`)**: Bidding: **21 Oct to 23 Oct** (₹30,213 Cr 100% fresh issue, ₹1,065–₹1,119, Lot: 12 shares, GMP: +₹248 / +22.2%, 12.55x subscribed).
     - **Authentic Upcoming Pipeline (SEBI DRHP & Regulatory Approvals)**:
       - **HDB Financial Services (`HDBFS`)**: HDFC Bank subsidiary (₹12,500 Cr issue, ₹700–₹740, Lot: 20).
       - **Ather Energy Limited (`ATHER`)**: Pure-play EV manufacturer (₹2,981 Cr issue, ₹310–₹328, Lot: 46).
       - **Tata Capital Limited (`TATACAP`)**: Mandatory RBI Upper-Layer NBFC listing (₹16,500 Cr, ₹285–₹300, Lot: 50).
       - **National Stock Exchange of India (`NSE`)**: Market infrastructure monopoly (₹12,500 Cr, ₹3,800–₹4,000, Lot: 3).
       - **Imagine Marketing / boAt (`BOAT`)**: Consumer wearables (₹2,000 Cr, ₹320–₹340, Lot: 44).
       - **Zepto (`ZEPTO`)**: Quick commerce hypergrowth (₹4,500 Cr, ₹220–₹235, Lot: 60).
     - **Officially Listed IPOs (Verified Historic Exchange Dates on BSE & NSE)**:
       - **Waaree Energies Limited (`WAAREE`)**: Listed on **28 Oct 2024** (Bidding: 21–23 Oct 2024, ₹4,321.44 Cr, ₹1,427–₹1,503).
       - **Hyundai Motor India (`HYUNDAI`)**: Listed on **22 Oct 2024** (Bidding: 15–17 Oct 2024, ₹27,870.16 Cr, ₹1,865–₹1,960).
       - **Afcons Infrastructure (`AFCONS`)**: Listed on **04 Nov 2024** (Bidding: 25–29 Oct 2024, ₹5,430 Cr, ₹440–₹463).
       - **Sagility India (`SAGILITY`)**: Listed on **12 Nov 2024** (Bidding: 05–07 Nov 2024, ₹2,106.60 Cr, ₹28–₹30).
       - **Swiggy Limited (`SWIGGY`)**: Listed on **13 Nov 2024** (Bidding: 06–08 Nov 2024, ₹11,327 Cr, ₹371–₹390).
       - **ACME Solar Holdings (`ACMESOLAR`)**: Listed on **13 Nov 2024** (Bidding: 06–08 Nov 2024, ₹2,900 Cr, ₹275–₹289).
       - **Niva Bupa Health Insurance (`NIVABUPA`)**: Listed on **14 Nov 2024** (Bidding: 07–11 Nov 2024, ₹2,200 Cr, ₹70–₹74).
       - **NTPC Green Energy (`NTPCGREEN`)**: Listed on **27 Nov 2024** (Bidding: 19–22 Nov 2024, ₹10,000 Cr, ₹102–₹108).
       - **Bajaj Housing Finance (`BAJAJHFL`)**: Listed on **16 Sep 2024** (Bidding: 09–11 Sep 2024, ₹6,560 Cr, ₹66–₹70).
  2. **Surveillance & Filtering Controls**:
     - **Instant Status Tabs**: One-click filtering across `All`, `Ongoing / Open` (bidding live), `Upcoming` (DRHP/RHP filed), and `Listed`.
     - **Urgent Final-Day Bidding Tracking**: When today is the final bidding date for an open IPO (such as Reliance Jio `JIO`), the UI displays an urgent **`⚡ CLOSES TODAY (5 PM)`** badge on the dashboard and renders a dedicated ASBA / UPI cut-off banner on the deep-dive research page reminding investors that exchange windows on NSE & BSE close strictly at 17:00 IST.
     - **Global Search Integration**: Type "Jio", "NSE", "Tata", or "Ongoing" in the top search bar to immediately access the respective IPO evaluation card.
     - **Category & Factor Sorting**: Filter by Mainboard vs. SME issues, or sort by Composite Score, Grey Market Premium (GMP %), Issue Size (₹ Cr), or Bidding Date.
  3. **Prospectus (DRHP / RHP) Forensics**:
     - **Fresh Issue vs. Offer for Sale (OFS)**: Clear visual capital breakdown. Promotes issues retaining $> 60\%$ fresh capital for growth capex and penalizes issues where promoters/PE funds cash out ($> 70\%$ OFS).
     - **Grey Market Premium (GMP) & Listing Gains**: Live tracking of estimated listing prices and percentage premiums.
     - **Subscription Demand Tracking**: Real-time bidding multiples across Qualified Institutional Buyers (QIB), High Net-Worth Individuals (NII/HNI), and Retail Individual Investors.
     - **Restated Financials & Valuation**: 3-year CAGR for Revenue and PAT, pre-IPO ROE/ROCE, debt-to-equity leverage, and post-issue P/E vs. listed peer group median.
  4. **9 Legendary Investor Strategy Evaluations for IPOs**:
     - **Warren Buffett**: Skeptical of IPO seller timing; requires durable moats, high ROCE, and penalizes high OFS exit.
     - **Charlie Munger**: Inversion analysis: checks for aggressive pro-forma adjustments, promoter litigation, and auditor qualifications.
     - **Benjamin Graham**: Margin of safety check: demands steep valuation discount to listed peers and tangible asset backing.
     - **Peter Lynch**: GARP evaluation: scalable consumer/niche expansion with PEG $< 1.2$.
     - **Joel Greenblatt**: Magic Formula for IPOs: pre-issue ROCE $> 20\%$ combined with post-money Earnings Yield $> 7\%$.
     - **Rakesh Jhunjhunwala**: Big India secular expansion story: domestic leadership, operating leverage, and high institutional appetite.
     - **Philip Fisher**: Scuttlebutt quality: organic R&D commitment and transparent management disclosure in RHP.
     - **Dolly Khanna**: Niche manufacturing or asset-light small/mid-caps with high ROCE and clean balance sheet.
     - **Porinju Veliyath**: Contrarian turnaround or overlooked unglamorous issues priced below replacement cost.
  5. **3 Mandatory Thesis Invalidation Conditions**: Enforces specific post-listing failure triggers (anchor lock-in supply dump, margin compression, and capital diversion).
  6. **Dedicated REST API**: Programmatic endpoints at `/api/v1/ipos/` and `/ipo/api/list/`.

---

## 5B. Portfolio Analysis & Expert-Style Evaluation (`/portfolio/analysis/`)

The platform features an institutional portfolio surveillance and expert-review engine capable of parsing multi-format broker statements and evaluating entire portfolios across quantitative risk and legendary investment philosophies:

### 1. Universal Statement Ingestion Engine (`src/portfolio/portfolio_parser.py`)
- **Supported Formats**: CSV (`.csv`), Excel (`.xlsx`, `.xls`), PDF (`.pdf`), and Microsoft Word (`.docx`).
- **Broker Pre-Sets**: Automatically parses holding statements from **FYERS**, **Zerodha (Console)**, **Upstox**, **Groww**, **Angel One**, and **ICICI Direct**.
- **Data Extracted**: Stock Name, Ticker, Exchange, ISIN, Quantity, Average Buy Price, Current Market Price, Invested Value, Current Market Value, Unrealized P&L (₹ & %), Sector, Statement Date, and Client Metadata. Missing fields are enriched via database/market feeds or explicitly marked as `"Not available in uploaded file"`.
- **Pre-Flight Preview**: AJAX-driven preview modal allows inspecting detected headers, mapped fields, and sample rows before committing to database storage.

### 2. Portfolio-Level Quantitative Analytics (`src/portfolio/portfolio_analyzer.py`)
- **Core Metrics**: Total Invested Capital, Current Portfolio Value, Total Unrealized P&L, Overall Return %.
- **Performance Dispersion**: Automatic identification of top-performing alpha drivers and lagging drawdown contributors.
- **Exposure Breakdown**: Interactive sector allocation pie/donut chart, individual stock weights bar chart, and market-cap tier distribution (Large, Mid, Small, Micro, Penny).
- **Concentration Guardrails**: Single-stock prudential threshold alerts ($>15\%$ alert, $>20\%$ hard cap), sector alerts ($>30\%$), and duplicate/overlapping exposure detection (e.g. corporate conglomerate clusters such as Tata Group, dual gold ETF allocations).
- **Quantitative Scores**:
  - **Portfolio Quality Score (0–100)**: Capital-weighted fundamental score reflecting balance sheet strength, ROCE, and moat durability.
  - **Diversification Score (0–100)**: Herfindahl-Hirschman Index (HHI) breadth score penalized for excessive tail fragmentation.
  - **Portfolio Risk Score (0–100)**: Composite index assessing tail risk, leverage, and volatility.

### 3. 9 Legendary Investor Style Profiling (`src/portfolio/investor_styles.py`)
Scores the entire portfolio and every individual security against 9 canonical investment philosophies:
1. **Warren Buffett**: Durable Moat, ROCE $>18\%$, High Free Cash Flow.
2. **Charlie Munger**: Rational Quality, Anti-stupidity, Governance Integrity.
3. **Benjamin Graham**: Deep Value, Tangible Asset Margin of Safety, Low P/B.
4. **Peter Lynch**: Growth at Reasonable Price (GARP), EPS growth $>20\%$.
5. **Joel Greenblatt**: Magic Formula (High ROCE + High Earnings Yield).
6. **Rakesh Jhunjhunwala**: Domestic India Scalability, High Operating Leverage.
7. **Philip Fisher**: Proprietary Innovation, R&D Moat, Customer Stickiness.
8. **Dolly Khanna**: Niche Small/Mid-Cap Compounding Leadership.
9. **Porinju Veliyath**: Contrarian Turnaround, Asset Play, Special Situations.

Identifies:
- Dominant investment orientation (Value, Growth, Quality, or Mixed Barbell).
- Key holdings matching each strategy.
- Conflicting holdings that detract from portfolio compounding.

### 4. Senior Portfolio Review & Expert Forensics (`src/portfolio/portfolio_report.py`)
Generates an objective, non-advisory institutional review:
- **Executive Portfolio Summary**
- **Demonstrated Strengths**
- **Weaknesses & Capital Drag Points**
- **Risk & Surveillance Flags** (Solvency, Micro-Cap ASM/GSM scrutiny, Corporate clustering)
- **Neutral Research Observations**
- **Strategic Questions for the Investor** (Horizon, risk tolerance, capital allocation mandates)
- **Monitoring Checklist** with specific catalysts for key holdings.

### 5. Multi-Format Report Exporter
One-click report generation with the mandatory SEBI compliance disclaimer:
- **Markdown (`.md`)**: Full analytical brief for documentation and version control.
- **CSV (`.csv`)**: Normalized tabular dataset of all holdings and calculated ratios.
- **Excel (`.xlsx`)**: Professional multi-sheet workbook with custom typography and formatted borders.
- **PDF (`.pdf`)**: Formatted executive report with KPI matrices, holdings table, and expert notes.

---

## 6. How Real-Time Dynamic Market Feeds Work in the Background

The application connects directly to live market feeds via `yfinance`:

1. **60-Second In-Memory Index Cache**: The indices engine (`get_market_indices_summary`) queries live ticks for `^NSEI`, `^BSESN`, `^NSEBANK`, and `^CNXIT`. Quotes are cached for 60 seconds to prevent unnecessary API throttling while keeping data fresh.
2. **Dynamic Price, Multiples & Momentum Recalibration**: When market prices change, `sync_live_market_data()` updates:
   - Current market price, day change, and percentage change.
   - P/E and P/B valuation multiples based on the new price.
   - 50-day moving average distance and momentum factor score.
   - Composite ranking order across the screener.
3. **Background Live Ticker Polling**: `static/js/app.js` runs a 45-second background polling cycle against `/api/market/pulse/`, ensuring the navbar ticker bar pulses and displays live market prices without page refreshes.
4. **On-Demand Exchange Synchronization**: Users can click **"Sync Live Feeds"** on the navbar or **"Sync Live Quote"** on any stock page to immediately force an exchange fetch.

---

## 7. Developer REST API Reference

The platform includes full Django REST Framework endpoints accessible at `/api/v1/`:

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/v1/stocks/` | `GET` | List all active NSE/BSE securities with current prices and metadata. |
| `/api/v1/stocks/<symbol>/` | `GET` | Retrieve detailed price, fundamentals, and evaluation for a stock. |
| `/api/v1/rankings/` | `GET` | Retrieve multi-factor composite rankings, filterable by score and sector. |
| `/api/v1/market/summary/` | `GET` | Retrieve benchmark indices, market breadth, and active stock counts. |
| `/api/market/pulse/` | `GET` | Fast JSON pulse endpoint for live index quotes and market breadth. |
| `/api/market/sync/` | `GET/POST`| Triggers live exchange synchronization for monitored securities. |

---

## 8. Summary Checklist & Commands

### Starting the Platform
```powershell
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Run the development server
python manage.py runserver 8000
```
Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

### Running Test Verification
```powershell
# Run full pytest test suite (63 tests)
pytest -v

# Run Django test runner (37 tests)
python manage.py test tests
```

---
*Document Version: 2.0 (Production Institutional Release)*  
*Platform: Full-Stack Django 5.x Framework*  
*Target Universe: National Stock Exchange of India (NSE) & Bombay Stock Exchange (BSE)*

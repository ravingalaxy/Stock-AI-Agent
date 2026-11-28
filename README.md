# AI Stock Market Research & Ranking Agent for NSE and BSE

[![Python 3.10 | 3.11 | 3.12](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Django 5.0+](https://img.shields.io/badge/django-5.0+-green.svg)](https://www.djangoproject.com/)
[![Tests Passing](https://img.shields.io/badge/pytest-82%20passed%2C%200%20failed-brightgreen.svg)](tests/)
[![Stress Tested](https://img.shields.io/badge/concurrency-1000%20reqs%20%7C%200%20locks-brightgreen.svg)](tests/stress_test_concurrency.py)
[![Paper Safety](https://img.shields.io/badge/execution-paper%20only%20(triple--lock)-orange.svg)](#-triple-lock-paper-trading-safety-architecture)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](README.md)
[![Regulatory Compliance](https://img.shields.io/badge/compliance-SEBI%20Research%20Guidelines-orange.svg)](#-compliance-disclaimer--license)

> **⚠️ REGULATORY DISCLAIMER & SEBI COMPLIANCE NOTICE**:
> This software is an AI-assisted personal research, educational analysis, and quantitative decision-support tool only. It does **NOT** constitute personalized investment advice, portfolio management services (PMS), or financial recommendations under SEBI (Investment Advisers) Regulations, 2013 or SEBI (Research Analysts) Regulations, 2014. Stock market investments are subject to market risks. Read all related scheme and statutory documents carefully before investing. Past performance is not an indicator or guarantee of future returns. No assured or guaranteed returns are claimed or implied.

---

## 📌 Table of Contents
1. [Executive Vision: Bridging the Institutional Divide](#-executive-vision-bridging-the-institutional-divide)
2. [Architectural Philosophy: Deterministic Math First, AI Second](#-architectural-philosophy-deterministic-math-first-ai-second)
3. [Key Capabilities & Modules](#-key-capabilities--modules)
4. [Day Trading & Intraday Intelligence Module](#-day-trading--intraday-intelligence-module)
5. [System Architecture & Directory Topology](#-system-architecture--directory-topology)
6. [The 9 Legendary Investor Frameworks](#-the-9-legendary-investor-frameworks)
7. [Engineering Rigor & Concurrency Benchmark](#-engineering-rigor--concurrency-benchmark)
8. [Cross-Platform Portability & System Requirements](#-cross-platform-portability--system-requirements)
9. [Quick Start (One-Click Setup)](#-quick-start-one-click-setup)
10. [Manual Step-by-Step Installation](#-manual-step-by-step-installation)
11. [Environment Configuration (.env)](#-environment-configuration-env)
12. [REST API & Programmatic Endpoints](#-rest-api--programmatic-endpoints)
13. [Running Automated Tests & Quality Assurance](#-running-automated-tests--quality-assurance)
14. [Troubleshooting & FAQ](#-troubleshooting--faq)
15. [Compliance, Disclaimer & License](#-compliance-disclaimer--license)

---

## 💡 Executive Vision: Bridging the Institutional Divide

In the Indian equity markets (NSE & BSE), there is an extreme information asymmetry:
- **Institutions (FIIs, DIIs, Mutual Funds, Family Offices)** utilize $25,000–$30,000/year Bloomberg and FactSet terminals, proprietary quantitative models, and dedicated research analysts.
- **Retail Investors (150M+ Demat accounts)** are largely left with broker app feeds, social media "finfluencer" hype, speculative Telegram channels, and static screeners that show trailing ratios without actionable synthesis.

**The StockAgent AI project bridges this divide.** It places an **institutional-grade quantitative research workstation** into the hands of individual investors, boutique PMS managers, and researchers at **zero data cost** using resilient public exchange integrations.

---

## 🧠 Architectural Philosophy: Deterministic Math First, AI Second

Unlike superficial "AI wrapper" tools that ask generic LLMs for speculative market opinions, this platform is built on an institutional quantitative paradigm:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Raw Market Data & Exchange Ingestion (NSE & BSE via yfinance)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. Deterministic Quantitative Math Engines                             │
│    • 2-Stage DCF Valuation with Margin of Safety                       │
│    • Financial Health: Piotroski F-Score (0-9) & Altman Z-Score        │
│    • Momentum & Volatility: SMA 50/200, Bollinger Bands, RSI, MACD     │
│    • Intraday Execution: 15m ORB, Intraday VWAP, ATR Dynamic Exits     │
│    • Portfolio Forensic Math: Concentration, Cluster Risk, Sharpe Ratio│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. Multi-Agent Qualitative Synthesis & Invalidation                    │
│    • Fundamental Agent  • Technical Agent  • Risk Surveillance Agent   │
│    • 3 Mandatory Falsifiable Thesis Invalidation Kill-Switches         │
│    • 9 Legendary Super-Investor Philosophy Scoring                     │
│    • Contextual AI Advisor (FreeLLMAPI / OpenAI / Local Ollama)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. Institutional Presentation Layer (Django 5 Dark Theme + Chart.js)   │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Deterministic Financial Math**: Key metrics (DCF intrinsic valuation, WACC, debt-to-equity, Piotroski scores, intraday VWAP, stop-loss calculations) are computed with strict mathematical algorithms—completely eliminating LLM hallucinations where numbers matter.
2. **Multi-Agent Cross-Validation**: Multiple specialized agents inspect fundamentals, technical trendlines, regulatory filings, and macroeconomic tailwinds independently before generating a composite score.
3. **Falsifiable Invalidation Rules**: Every stock report includes **3 explicit exit conditions** that tell the investor exactly when the fundamental or quantitative thesis has broken.

---

## 🌟 Key Capabilities & Modules

| Module | URL Route | Core Capabilities |
|---|---|---|
| **Market Intelligence Dashboard** | `/` | Real-time market summary, live Nifty/Sensex ticker bar, top composite ranking list, market breadth visualizer, and active surveillance alerts. |
| **Day Trading & Intraday Intelligence** | `/daytrading/` | Full India-first Day Trading workstation integrating all **11 quantitative skills**: Scanner, News Sentiment, ORB/VWAP Entry, ATR Exits, Risk Engine, Capital Budgeting, Surveillance Alerts, Historical Time Machine, Company Fundamentals, SEBI Disclosures, and Paper Broker. Includes Chart.js Price/VWAP Visualizer & Volume Spike Leaderboard matching the Home Dashboard UI design. |
| **Stock Research Workstation** | `/research/<symbol>/` | Deep fundamental ratios (ROE, ROCE, P/E, Debt/Equity, FCF), responsive Chart.js technical graphs with moving averages (SMA 50/200, Bollinger Bands), interactive 2-stage DCF valuation model with live slider sensitivity, 3 falsifiable thesis invalidation rules, and 9 legendary investor strategy evaluations. |
| **Rankings Screener** | `/rankings/` | Multi-factor weighted composite scoring (Quality 30%, Growth 20%, Valuation 15%, Momentum 15%, Catalysts 10%, Risk -10%), dynamic sorting, sector filtering, and downloadable Top-20 institutional research reports in Markdown & CSV. |
| **Portfolio Diagnostic & Upload** | `/portfolio/analysis/` | Upload statements in **CSV, Excel (.xlsx, .xls), PDF, or Word (.docx)** formats (e.g., FYERS, Zerodha, Groww). Automatically extracts holdings, parses buy prices and live prices, generates Large/Mid/Small cap and Sector allocation breakdowns, runs stress testing, and scores alignment with 9 legendary investor styles. |
| **Top 10 Super-Portfolios** | `/portfolio/top-portfolios/` | Deep tracking of India's most celebrated super-investors (Radhakishan Damani, Rakesh Jhunjhunwala / Rare Enterprises, Vijay Kedia, Ashish Kacholia, Nemish Shah, Porinju Veliyath, Dolly Khanna, Sunil Singhania, Mukul Agrawal, Hemendra Kothari). Synchronize live market prices with one click, explore sector allocations, and discover co-investment overlaps with your personal portfolio. |
| **IPO Intelligence Engine** | `/ipo/` | Tracks ongoing, upcoming, and recently listed Mainboard & SME offerings. Analyzes DRHP/RHP metrics, Fresh Issue vs. OFS capital split, live Grey Market Premium (GMP), expected listing gains, institutional subscription rates (QIB, NII, Retail), and 9 legendary investor match ratings. |
| **Algorithmic Backtesting** | `/backtest/` | Point-in-time quantitative backtesting without look-ahead bias, periodic rebalancing (monthly/quarterly), cumulative equity curve vs. Nifty 50 benchmark, CAGR, Sharpe ratio, volatility, and maximum drawdown calculations. |
| **CLI & Automation Hub** | `/cli-analysis/` | Browser-based interactive terminal window executing background analysis workflows (`python -m src.main analyze --index bse500 --top 60`) with real-time log streaming. |
| **REST API v1** | `/api/v1/` & `/daytrading/api/` | Full Django REST Framework API providing programmatic JSON feeds for market tickers, stock research, rankings, IPO records, and day trading endpoints. |

---

## ⚡ Day Trading & Intraday Intelligence Module

The Day Trading & Intraday Intelligence module (`/daytrading/`) provides Dalal Street retail traders with institutional-grade intraday decision support. It combines **11 modular quantitative skills**, **interactive Chart.js visualizers**, a **server-side risk governor**, and an **AI Advisor** powered by FreeLLMAPI / OpenAI.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        GUI WORKSTATION (/daytrading/)                  │
│  [Ticker Selector]  [Timeframe: 5m/15m/1h]  [Live Ticker Status Bar]   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         ▼                                                     ▼
┌───────────────────────────────────┐ ┌───────────────────────────────────┐
│     CHART.JS VISUALIZATION SUITE  │ │       DAY TRADING RADAR SUITE     │
│ • Intraday 5m Price & VWAP Area   │ │ • Trader Scanner (ORB / Volume)   │
│ • Entry / Target / SL Levels      │ │ • News Sentiment & BSE Filings    │
│ • Volume Spike Leaderboard        │ │ • SEBI Insider Filings (PIT/Bulk) │
└─────────────────┬─────────────────┘ └─────────────────┬─────────────────┘
                  │                                     │
                  └─────────────────┬───────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      DETERMINISTIC EXECUTION & RISK                    │
│ • Trader Entry (ORB / VWAP Bounce) • Dynamic ATR Exits (Target 1 & 2)  │
│ • Trader Risk (2% Per-Trade Limit, 20% Position Cap, Daily Loss Cutoff)│
│ • Trader Broker (Paper-Only Sandbox, Indian Tax & Fee Calculation)     │
│ • Trader Time Machine (1,000-Run Monte Carlo Simulation)               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│            QUALITATIVE AI ADVISOR (FreeLLMAPI / OpenAI / Ollama)       │
│ • Contextual trade thesis generation • Catalyst & Sentiment synthesis │
└────────────────────────────────────────────────────────────────────────┘
```

### The 11 Quantitative Day Trading Skills

| Skill | Module File | Focus & Strategy | Core Output / Signals |
|---|---|---|---|
| **1. Trader Scanner** | `src/daytrading/scanner.py` | Screens liquid equities for Momentum, Opening Range Breakout (ORB), and Volume Spikes against 20-day moving averages. | Candidate watchlist with Relative Volume (RVol) ratios, ATR values, and momentum rankings. |
| **2. Trader News** | `src/daytrading/news.py` | Aggregates real-time Indian market news feeds (Yahoo Finance India RSS) and corporate filings. | Catalyst extraction, sentiment polarity (-1.0 to +1.0), and breaking regulatory flags. |
| **3. Trader Entry** | `src/daytrading/entry.py` | Identifies high-probability intraday setups: ORB 15-minute high/low breaks and VWAP bounce triggers. | Signal type (`BUY`/`SELL`/`HOLD`), entry price, rationale, and quantitative setup quality score. |
| **4. Trader Exit** | `src/daytrading/exit_planner.py` | Calculates mathematically rigorous stop-loss and profit targets using dynamic Average True Range (ATR). | Initial Stop-Loss (1.5x ATR), Target 1 (1:1.5 Risk/Reward), Target 2 (1:2.5 Risk/Reward), and 15:15 IST square-off. |
| **5. Trader Risk** | `src/daytrading/risk.py` | Enforces non-negotiable risk constraints to prevent capital blowouts. | Max 2% capital risk per trade, 20% single-position allocation cap, 5 concurrent positions max, and daily loss lockout. |
| **6. Trader Budget** | `src/daytrading/budget.py` | Comprehensive INR capital accounting and margin tracking. | Starting capital, available liquidity, utilized margin, realized P&L, unrealized P&L, and peak drawdown. |
| **7. Trader Alerts** | `src/daytrading/alerts.py` | Continuous market surveillance detecting threshold breaches. | Real-time notifications for ORB breaches, VWAP crossings, sudden volume surges (>2.5x), and price spikes. |
| **8. Trader Time Machine** | `src/daytrading/timemachine.py` | Historical 5-minute candle replay and 1,000-iteration Monte Carlo simulation. | Win-rate probability distributions, expected maximum drawdowns, Sharpe ratios, and realistic execution costs. |
| **9. Trader Analyst** | `src/daytrading/analyst.py` | Contextual fundamental overlay from `FundamentalData` models. | P/E, P/B, ROE, ROCE, Debt/Equity, and institutional shareholding trends for the intraday candidate. |
| **10. Trader Pelosi (India)** | `src/daytrading/disclosure.py` | Tracks public SEBI Prohibition of Insider Trading (PIT) disclosures and bulk/block deals. | Promoter buying/selling patterns, institutional bulk deal sizes, and high-conviction insider accumulation. |
| **11. Trader Broker** | `src/daytrading/paper_broker.py` | Simulated execution engine with realistic Indian market friction. | Simulated slippage (0.01%–0.05%), Indian statutory charges (STT, brokerage, GST, stamp duty), and paper safety enforcement. |

### Visual Design & Chart.js Visualizers
- **Design Parity with Home Dashboard**: Styled using the institutional `fintech.css` design system (`.fin-card`, `.kpi-grid`, `.fin-table`, and monospace numeric typography).
- **Intraday Price & VWAP Visualizer**: Responsive Chart.js 5-minute area chart plotting asset price alongside intraday VWAP, featuring dynamic horizontal guideline overlays:
  - 🔵 **Entry Price** (Blue dashed line)
  - 🟢 **Target 1 & Target 2** (Green dashed lines)
  - 🔴 **Stop-Loss** (Red dashed line)
- **Volume Spike Leaderboard**: Horizontal bar chart highlighting equities experiencing anomalous intraday trading volume compared to their 20-day moving averages.
- **AI Advisor Modal**: Powered by FreeLLMAPI / OpenAI / Ollama, delivering contextual analysis and risk commentary without modifying deterministic price levels.

### Triple-Lock Paper Trading Safety Architecture
1. **Enforced Sandbox Mode**: The execution engine strictly hardcodes `is_paper = True`. Direct real-money execution is architecturally impossible.
2. **Server-Side Risk Interceptor**: Trade proposals that violate the 2% per-trade capital risk rule or exceed the daily loss ceiling are rejected by the backend before reaching execution logic.
3. **Realistic Indian Cost Deduction**: All simulated trades incorporate exact Dalal Street fees:
   - Securities Transaction Tax (STT): 0.025% on equity intraday sell leg
   - Brokerage: ₹20 or 0.03% (whichever is lower)
   - Exchange Turnover Fees: 0.00297% (NSE)
   - SEBI Turnover Charges: ₹10 per crore
   - GST: 18% on (brokerage + exchange fees + SEBI fees)
   - Stamp Duty: 0.003% on buy leg

> For complete usage walkthroughs, see:
> - 📖 [USER_GUIDE.md](USER_GUIDE.md) — Comprehensive user guide for all 11 skills and GUI controls.
> - 🚀 [RUN_GUIDE.md](RUN_GUIDE.md) — Step-by-step local execution and verification instructions.
> - 🎨 [DASHBOARD_INTEGRATION_GUIDE.md](DASHBOARD_INTEGRATION_GUIDE.md) — Technical details on Chart.js and design system integration.

---

## 🏛️ System Architecture & Directory Topology

```
Stock-AI-Agent/
├── apps/                          # Django 5 Application Layer
│   ├── market/                    # Home dashboard, ticker feeds, market breadth
│   ├── research/                  # Fundamental workstation, DCF model, thesis invalidation
│   ├── rankings/                  # Multi-factor composite screener & scoring
│   ├── portfolio/                 # Multi-format parser, stress testing, super-portfolios
│   ├── ipo/                       # Mainboard & SME pipeline, DRHP metrics, GMP tracker
│   ├── backtesting/               # Quantitative point-in-time backtesting
│   ├── daytrading/                # Day Trading & Intraday Intelligence workstation
│   └── api/                       # REST API v1 endpoints
├── src/                           # Quantitative Core Engines (Deterministic Math)
│   ├── valuation/                 # 2-Stage DCF engine, Piotroski, Altman Z-Score
│   ├── portfolio/                 # Statement parsers (CSV, Excel, PDF, Word), 9 investor styles
│   ├── daytrading/                # The 11 Day Trading quantitative skills
│   └── analysis/                  # Fundamental, technical, and risk surveillance engines
├── templates/                     # Dark-Theme Institutional UI (Bootstrap 5 + fintech.css)
│   ├── base.html                  # Master shell with unified navigation and ticker bar
│   ├── market/                    # Dashboard templates
│   ├── research/                  # Research workstation templates
│   ├── rankings/                  # Screener templates
│   ├── portfolio/                 # Portfolio analysis and super-investor templates
│   ├── ipo/                       # IPO workstation templates
│   └── daytrading/                # Day Trading workstation templates with Chart.js
├── static/                        # CSS, JavaScript visualizers, and brand assets
│   ├── css/fintech.css            # Bloomberg-inspired dark design system
│   └── js/                        # Interactive components and charts
├── data/                          # Persistent storage (auto-created if missing)
│   ├── stock_research.db          # SQLite database (WAL mode enabled)
│   ├── chroma_db/                 # ChromaDB local vector embeddings
│   ├── reports/                   # Exported institutional Markdown & CSV dossiers
│   └── logs/                      # Application and background job logs
├── tests/                         # Pytest test suite & concurrency harness
│   ├── test_daytrading.py         # 12 day trading unit & integration tests
│   ├── stress_test_concurrency.py # 1,000-request multi-threaded stress harness
│   └── ...                        # Total 82 automated test cases
├── config/                        # Django project configuration & WSGI/ASGI
├── manage.py                      # Django CLI management script
├── requirements.txt               # Locked project dependencies
├── setup.bat / setup.sh           # Automated one-click environment setup
└── run.bat / run.sh               # Automated one-click server launchers
```

---

## 🏆 The 9 Legendary Investor Frameworks

Every stock and uploaded portfolio is continuously evaluated against Dalal Street and Wall Street's most celebrated quantitative frameworks:

1. **Warren Buffett**: Sustainable economic moats, predictable free cash flows, ROE > 15%, low debt.
2. **Charlie Munger**: Capital efficiency, pricing power, high ROCE, and rational management.
3. **Peter Lynch**: Growth at a Reasonable Price (GARP), PEG ratio < 1.0, fast growers in niche sectors.
4. **Benjamin Graham**: Deep value, Net-Net margin of safety, low P/B, and conservative current ratios.
5. **Joel Greenblatt (Magic Formula)**: High Return on Capital Employed (ROCE) paired with high Earnings Yield.
6. **Rakesh Jhunjhunwala**: High-conviction structural India growth themes, demographic consumption, and operating leverage.
7. **Radhakishan Damani**: High-velocity retail moat, strong cash conversion cycle, debt aversion.
8. **Vijay Kedia (SMILE Principle)**: Small in size, Medium in experience, Large in aspiration, Extra-Large in market potential.
9. **Ashish Kacholia**: High-alpha emerging SME and midcap niche manufacturing leaders.

---

## 🛡️ Engineering Rigor & Concurrency Benchmark

This platform was built to meet the rigorous reliability standards of production financial systems:

### 1. Concurrency & High-Throughput Verification
- **Test Harness**: [`tests/stress_test_concurrency.py`](tests/stress_test_concurrency.py)
- **Workload**: **1,000 requests** dispatched across **50 concurrent worker threads** simultaneously hitting market pulse, screener rankings, search autocompletion, IPO pipelines, and direct database write bursts.
- **Outcome**:
  - **100% HTTP 200 OK (1,000 / 1,000 successes, 0 failures)**.
  - **Zero Database Lock Errors**: Solved via SQLite WAL (`Write-Ahead Logging`), `PRAGMA synchronous=NORMAL`, and `PRAGMA busy_timeout=30000` applied to both Django ORM and SQLAlchemy connections.
  - **Zero Race Conditions**: Auto-provisioning queries use atomic `get_or_create` blocks.

### 2. Comprehensive Test Coverage
- **Status**: **82 passed, 0 failed** across all test suites in ~17 seconds.
- Fully automated test suite covering DCF valuation, portfolio statement parsers, IPO pipelines, Day Trading skills, risk limits, and paper brokerage execution.

---

## 💻 Cross-Platform Portability & System Requirements

This project is fully engineered to be **100% portable** across operating systems with zero modifications required:
- **Operating Systems**: Windows 10/11, macOS (Intel & Apple Silicon), Linux (Ubuntu, Debian, Fedora, Arch), WSL2.
- **Python Compatibility**: Python **3.10**, **3.11**, or **3.12**.
- **Memory**: 4 GB RAM minimum (8 GB recommended).
- **Disk Space**: ~3 MB download from GitHub (~500 MB after local `.venv` creation).

### Portability Safeguards Implemented:
1. **Dynamic Path Resolution**: All paths use Python `pathlib.Path` relative to `settings.BASE_DIR`. No hardcoded drive letters (`C:\`, `D:\`) or OS-specific separators.
2. **Directory Self-Healing**: Database directories (`data/`), report outputs (`data/reports/`), and log directories (`data/logs/`) are auto-created on startup if absent.
3. **Multi-Platform Launchers**: Native batch scripts (`.bat`) for Windows and shell scripts (`.sh`) for macOS/Linux.

---

## ⚡ Quick Start (One-Click Setup)

### 1. Clone the Repository
```bash
git clone https://github.com/ravingalaxy/Stock-AI-Agent.git
cd Stock-AI-Agent
```

### 2. Run Automated Setup

#### On Windows:
Double-click `setup.bat` or run:
```cmd
setup.bat
```
To launch the server, double-click `run.bat` or run:
```cmd
run.bat
```

#### On Linux / macOS / WSL:
```bash
chmod +x setup.sh run.sh
./setup.sh
./run.sh
```

Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser!

---

## 🔧 Manual Step-by-Step Installation

If you prefer to configure manually:

```bash
# 1. Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Setup environment configuration
cp .env.example .env
cp config/.env.example config/.env

# 4. Run database migrations
python manage.py migrate --noinput

# 5. Seed benchmark NSE/BSE universe and IPO data
python manage.py seed_universe

# 6. Start the server
python manage.py runserver 127.0.0.1:8000
```

---

## ⚙️ Environment Configuration (.env)

The application runs fully out-of-the-box in deterministic quantitative mode using free public exchange data. If you wish to enable advanced external LLM commentary, configure `.env`:

```ini
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,*

# Optional: LLM Providers (OpenAI, FreeLLM, or local Ollama)
FREELLM_API_KEY=your_freellmapi_key_here
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_NAME=gpt-4o-mini

# Database & Storage
DATABASE_URL=sqlite:///data/stock_research.db
VECTOR_DB_DIR=data/chroma_db
LOG_LEVEL=INFO
```

---

## 🔌 REST API & Programmatic Endpoints

The platform provides a complete RESTful API for algorithmic access:

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/market/pulse/` | `GET` | Returns live Nifty 50 and Sensex ticker quotes and market breadth metrics. |
| `/api/v1/research/<symbol>/` | `GET` | Comprehensive stock fundamentals, DCF valuation, and 9 investor scores. |
| `/api/v1/rankings/` | `GET` | Filtered and weighted ranking list across all screened Indian equities. |
| `/api/v1/ipo/` | `GET` | Mainboard & SME IPO pipeline, GMP data, and institutional subscription rates. |
| `/daytrading/api/scan/` | `GET` | Real-time momentum, ORB, and volume spike scan candidates. |
| `/daytrading/api/signals/<symbol>/` | `GET` | Intraday entry signals, ATR stop-loss, Target 1, Target 2, and risk metrics. |
| `/daytrading/api/advisor/<symbol>/` | `GET` | AI-generated trading thesis and catalyst commentary. |
| `/daytrading/api/execute/` | `POST` | Executes simulated paper trade with Indian friction charges. |

---

## 🧪 Running Automated Tests & Quality Assurance

To execute the test suite:

```bash
# Windows
.\.venv\Scripts\pytest -v

# macOS / Linux
pytest -v
```

Expected result:
```
======================= 82 passed, 0 failed in ~17s =======================
```

To run the 1,000-request high-concurrency stress test:
```bash
python tests/stress_test_concurrency.py
```

---

## 🔍 Troubleshooting & FAQ

### Q1: `activate.ps1 cannot be loaded because running scripts is disabled` on Windows PowerShell
**Solution**: Run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Or simply use `run.bat` or `setup.bat`.

### Q2: Port 8000 is already in use
**Solution**: Specify a custom port:
```bash
python manage.py runserver 127.0.0.1:8080
```

### Q3: `sqlite3.OperationalError: database is locked`
**Solution**: This repository comes pre-configured with SQLite WAL mode and a 30-second busy timeout. If running custom scripts, ensure your connections use WAL mode:
```sql
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=30000;
```

### Q4: Are real brokerage accounts or API keys required?
**Solution**: **No.** All day trading execution is strictly simulated (paper trading) with zero real money risk. All market data is retrieved from public exchange feeds via `yfinance`. No paid subscriptions or brokerage credentials are required.

---

## 📜 Compliance, Disclaimer & License

### Regulatory Disclaimer
This software complies with standard automated quantitative research guidelines:
1. **Source Transparency**: All financial metrics, price histories, and ratios are calculated using verifiable formulas or sourced directly from verified public market exchanges via `yfinance`.
2. **Skeptical Risk Architecture**: Every stock profile enforces a minimum of 3 mandatory thesis invalidation conditions and multi-dimensional risk disclosures.
3. **No Advisory Services**: The application does not solicit investments, execute automated broker trades, or promise returns.

### MIT License
This project is licensed under the [MIT License](LICENSE) — free to use, modify, and distribute for personal, educational, and commercial research purposes.

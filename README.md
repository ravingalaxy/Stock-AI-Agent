# AI Stock Market Research & Ranking Agent for NSE and BSE

[![Python 3.10 | 3.11 | 3.12](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Django 5.0+](https://img.shields.io/badge/django-5.0+-green.svg)](https://www.djangoproject.com/)
[![Tests Passing](https://img.shields.io/badge/pytest-70%20passed%2C%201%20skipped-brightgreen.svg)](tests/)
[![Stress Tested](https://img.shields.io/badge/concurrency-1000%20reqs%20%7C%200%20locks-brightgreen.svg)](tests/stress_test_concurrency.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](README.md)
[![Regulatory Compliance](https://img.shields.io/badge/compliance-SEBI%20Research%20Guidelines-orange.svg)](README.md#compliance--disclaimer)

> **⚠️ REGULATORY DISCLAIMER & SEBI COMPLIANCE NOTICE**:
> This software is an AI-assisted personal research, educational analysis, and quantitative decision-support tool only. It does **NOT** constitute personalized investment advice, portfolio management services (PMS), or financial recommendations under SEBI (Investment Advisers) Regulations, 2013 or SEBI (Research Analysts) Regulations, 2014. Stock market investments are subject to market risks. Read all related scheme and statutory documents carefully before investing. Past performance is not an indicator or guarantee of future returns. No assured or guaranteed returns are claimed or implied.

---

## 📌 Table of Contents
1. [Executive Vision: Bridging the Institutional Divide](#-executive-vision-bridging-the-institutional-divide)
2. [Architectural Philosophy: Deterministic Math First, AI Second](#-architectural-philosophy-deterministic-math-first-ai-second)
3. [Key Capabilities & Modules](#-key-capabilities--modules)
4. [System Architecture](#-system-architecture)
5. [The 9 Legendary Investor Frameworks](#-the-9-legendary-investor-frameworks)
6. [Engineering Rigor & Concurrency Benchmark](#-engineering-rigor--concurrency-benchmark)
7. [Cross-Platform Portability & System Requirements](#-cross-platform-portability--system-requirements)
8. [Quick Start (One-Click Setup)](#-quick-start-one-click-setup)
9. [Manual Step-by-Step Installation](#-manual-step-by-step-installation)
10. [Environment Configuration (.env)](#-environment-configuration-env)
11. [Running Automated Tests](#-running-automated-tests)
12. [Troubleshooting & FAQ](#-troubleshooting--faq)
13. [License & Ethical Compliance](#-license--ethical-compliance)

---

## 💡 Executive Vision: Bridging the Institutional Divide

In the Indian equity markets (NSE & BSE), there is an extreme information asymmetry:
- **Institutions (FIIs, DIIs, Mutual Funds, Family Offices)** utilize \$25,000–\$30,000/year Bloomberg and FactSet terminals, proprietary quantitative models, and dedicated research analysts.
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
│    • Portfolio Forensic Math: Concentration, Cluster Risk, Sharpe Ratio│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. Multi-Agent Qualitative Synthesis & Invalidation                    │
│    • Fundamental Agent  • Technical Agent  • Risk Surveillance Agent   │
│    • 3 Mandatory Falsifiable Thesis Invalidation Kill-Switches         │
│    • 9 Legendary Super-Investor Philosophy Scoring                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. Institutional Presentation Layer (Django 5 Dark Theme + REST API)   │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Deterministic Financial Math**: Key metrics (DCF intrinsic valuation, WACC, debt-to-equity, Piotroski scores) are computed with strict mathematical algorithms—eliminating LLM hallucinations where numbers matter.
2. **Multi-Agent Cross-Validation**: Multiple specialized agents inspect fundamentals, technical trendlines, regulatory filings, and macroeconomic tailwinds independently before generating a composite score.
3. **Falsifiable Invalidation Rules**: Every stock report includes **3 explicit exit conditions** that tell the investor exactly when the fundamental thesis has broken.

---

## 🌟 Key Capabilities & Modules

| Module | URL Route | Core Capabilities |
|---|---|---|
| **Market Intelligence Dashboard** | `/` | Real-time market summary, live Nifty/Sensex ticker bar, top composite ranking list, market breadth visualizer, and active surveillance alerts. |
| **Stock Research Workstation** | `/research/<symbol>/` | Deep fundamental ratios (ROE, ROCE, P/E, Debt/Equity, FCF), responsive Chart.js technical graphs with moving averages (SMA 50/200, Bollinger Bands), interactive 2-stage DCF valuation model with live slider sensitivity, 3 falsifiable thesis invalidation rules, and 9 legendary investor strategy evaluations. |
| **Rankings Screener** | `/rankings/` | Multi-factor weighted composite scoring (Quality 30%, Growth 20%, Valuation 15%, Momentum 15%, Catalysts 10%, Risk -10%), dynamic sorting, sector filtering, and downloadable Top-20 institutional research reports in Markdown & CSV. |
| **Portfolio Diagnostic & Upload** | `/portfolio/analysis/` | Upload statements in **CSV, Excel (.xlsx, .xls), PDF, or Word (.docx)** formats (e.g., FYERS, Zerodha, Groww). Automatically extracts holdings, parses buy prices and live prices, generates Large/Mid/Small cap and Sector allocation breakdowns, runs stress testing, and scores alignment with 9 legendary investor styles. |
| **Top 10 Super-Portfolios** | `/portfolio/top-portfolios/` | Deep tracking of India's most celebrated super-investors (Radhakishan Damani, Rakesh Jhunjhunwala / Rare Enterprises, Vijay Kedia, Ashish Kacholia, Nemish Shah, Porinju Veliyath, Dolly Khanna, Sunil Singhania, Mukul Agrawal, Hemendra Kothari). Synchronize live market prices with one click, explore sector allocations, and discover co-investment overlaps with your personal portfolio. |
| **IPO Intelligence Engine** | `/ipo/` | Tracks ongoing, upcoming, and recently listed Mainboard & SME offerings. Analyzes DRHP/RHP metrics, Fresh Issue vs. OFS capital split, live Grey Market Premium (GMP), expected listing gains, institutional subscription rates (QIB, NII, Retail), and 9 legendary investor match ratings. |
| **Algorithmic Backtesting** | `/backtest/` | Point-in-time quantitative backtesting without look-ahead bias, periodic rebalancing (monthly/quarterly), cumulative equity curve vs. Nifty 50 benchmark, CAGR, Sharpe ratio, volatility, and maximum drawdown calculations. |
| **CLI & Automation Hub** | `/cli-analysis/` | Browser-based interactive terminal window executing background analysis workflows (`python -m src.main analyze --index bse500 --top 60`) with real-time log streaming. |
| **REST API v1** | `/api/v1/` | Full Django REST Framework API providing programmatic JSON feeds for market tickers, stock research, rankings, and IPO records. |

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Web & Browser Presentation                     │
│  Institutional Dark Design System (Bloomberg/FactSet Aesthetic) │
│  Chart.js Technicals  •  Real-time Modals  •  SVG Favicon Suite │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Django 5 Application Layer                  │
│  apps.market    • apps.research   • apps.rankings               │
│  apps.portfolio • apps.ipo        • apps.backtesting • apps.api │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Quantitative & Analytics Engine                │
│  • Multi-Agent Forensic Screener (Fundamentals, Technicals)     │
│  • 2-Stage Discounted Cash Flow (DCF) Valuation Engine          │
│  • 9 Legendary Investor Strategy Classifiers                    │
│  • Multi-Format Statement Parsers (openpyxl, python-docx, pypdf)│
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Data Persistence & Feeds                    │
│  • SQLite Database (WAL Mode + 30s Timeout)                     │
│  • yfinance Live NSE (.NS) & BSE (.BO) Market Feeds             │
│  • ChromaDB Local Vector Store + Report Cache                   │
└─────────────────────────────────────────────────────────────────┘
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
- **Status**: **70 passed, 1 skipped (live API guard)** in ~10 seconds.
- Fully automated test suite covering DCF valuation, portfolio statement parsers, IPO pipelines, and CLI commands.

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

## 🧪 Running Automated Tests

To execute the test suite:

```bash
# Windows
.\.venv\Scripts\pytest -v

# macOS / Linux
pytest -v
```

Expected result:
```
======================= 70 passed, 1 skipped in ~10s =======================
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

---

## 📜 Compliance & Disclaimer

This software complies with standard automated quantitative research guidelines:
1. **Source Transparency**: All financial metrics, price histories, and ratios are calculated using verifiable formulas or sourced directly from verified public market exchanges via `yfinance`.
2. **Skeptical Risk Architecture**: Every stock profile enforces a minimum of 3 mandatory thesis invalidation conditions and multi-dimensional risk disclosures.
3. **No Advisory Services**: The application does not solicit investments, execute automated broker trades, or promise returns.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) — free to use, modify, and distribute for personal, educational, and commercial research purposes.

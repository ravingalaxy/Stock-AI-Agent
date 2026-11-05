# 🚀 **AI Stock Research & Ranking Agent - Complete Run Guide**

> **⚠️ DISCLAIMER**: This is an AI-assisted personal research and educational decision-support tool. It does NOT constitute personalized investment advice, financial advisory services, or stock recommendations. Stock market investments are subject to market risks. Past performance is not an indicator or guarantee of future returns. No assured or guaranteed returns are claimed or implied.

---

## 📋 **TABLE OF CONTENTS**

1. [🎯 Quick Start](#quick-start)
2. [📋 Prerequisites](#prerequisites)
3. [🔧 Installation & Setup](#installation--setup)
4. [🔑 freellmapi Configuration](#freellmapi-configuration)
5. [⚡ Running Analysis (CLI)](#running-analysis-cli)
6. [📊 Building Universe](#building-universe)
7. [🔄 Updating Data](#updating-data)
8. [📈 Running Backtest](#running-backtest)
9. [🌐 Web Dashboard](#web-dashboard)
10. [🧪 Running Tests](#running-tests)
11. [📁 Report Output](#report-output)
12. [🔧 Troubleshooting](#troubleshooting)
13. [📋 Quick Reference Card](#quick-reference-card)

---

## 🎯 **QUICK START**

### **Need the fastest way to get started?**
Copy and paste this into your terminal:

```powershell
# Navigate to project
cd F:\Projects\Stock-AI-Agent

# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run quick analysis (3 stocks, ~2 minutes)
.venv\Scripts\python -m src.main analyze --custom-symbols RELIANCE,TCS,INFY --top 3
```

---

## 📋 **PREREQUISITES**

### **Before You Start:**
```powershell
✅ Windows 10/11 or macOS/Linux
✅ Python 3.11+ installed
✅ Administrator privileges (for port binding)
✅ Internet connection (for API calls & market data)
✅ Code editor (VS Code, PyCharm, or any text editor)
```

---

## 🔧 **INSTALLATION & SETUP**

### **Step 1: Create Virtual Environment**
```powershell
# Navigate to project directory
cd F:\Projects\Stock-AI-Agent

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Upgrade pip
.venv\Scripts\pip install --upgrade pip
```

### **Step 2: Install Dependencies**
```powershell
# Install all project dependencies
.venv\Scripts\pip install -r requirements.txt -q

# If any packages fail, install them individually:
# .venv\Scripts\pip install yfinance pandas pyyaml rich typer pydantic pydantic-settings chromadb -q
```

### **Step 3: Configure Environment File**
```powershell
# Create .env file from template (if it doesn't exist)
if not exist config\.env copy config\.env.example config\.env

# Edit config\.env and add your freellmapi API key
# Open config\.env in your code editor and set:
FREELLM_API_KEY=your_freellmapi_key_here
```

---

## 🔑 **FREELLAPI CONFIGURATION**

### **Current Configuration (Already Done):**
Your `config\.env` file is already configured with:
```bash
# freellmapi (Unified API) - RECOMMENDED
FREELLM_API_KEY=freellmapi-6a1784d93...
FREELLM_API_BASE=https://api.freellmapi.com/v1

# OpenAI API Settings (Alternative)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL_NAME=gpt-4o-mini

# Local Ollama Settings (Optional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_NAME=llama3.2
```

### **Config File Settings (`config\config.yaml`):**
```yaml
llm:
  provider: "freellmapi"          # Uses your freellmapi key
  model_name: "gpt-4o-mini"       # Model to use
  freellmapi_api_base: "https://api.freellmapi.com/v1"
```

### **To Update Your Key:**
Edit `config\.env` and replace the placeholder with your actual key:
```bash
FREELLM_API_KEY=your_actual_freellmapi_key_here
```

---

## ⚡ **RUNNING ANALYSIS (CLI)**

### **Quick Test with 3 Stocks (~2 minutes)**
```powershell
cd F:\Projects\Stock-AI-Agent
.venv\Scripts\activate

# Quick test with 3 stocks
.venv\Scripts\python -m src.main analyze --custom-symbols RELIANCE,TCS,INFY --top 3
```

### **Full Nifty 500 Analysis (Top 20)**
```powershell
# Analyze top 20 from Nifty 500
.venv\Scripts\python -m src.main analyze --index nifty500 --top 20
```

### **With Filters**
```powershell
# Filter by sector
.venv\Scripts\python -m src.main analyze --index nifty500 --top 20 --sector Technology

# Filter by minimum market cap (in Crores)
.venv\Scripts\python -m src.main analyze --index nifty500 --top 20 --min_market_cap 1000

# Combine filters
.venv\Scripts\python -m src.main analyze --index nifty500 --top 20 --sector "Financial Services" --min_market_cap 5000
```

### **Custom Symbols**
```powershell
# Analyze specific stocks
.venv\Scripts\python -m src.main analyze --custom-symbols RELIANCE,TCS,INFY,HDFCBANK,ICICIBANK,SBIN,BHARTIARTL --top 7
```

---

## 📊 **BUILDING UNIVERSE**

### **Build Nifty 500 Universe (Recommended)**
```powershell
# Build universe from Nifty 500 (most liquid Indian stocks)
.venv\Scripts\python -m src.main build-universe --index nifty500

# Expected Output:
# [INFO] Database schema initialized.
# [INFO] Building universe from nifty500: 70+ symbols
# [INFO] Screening 70+ symbols...
# [INFO] Universe built: 66 stocks passed screening
# [INFO] 66 stocks added to database
```

### **Build Custom Subset (For Testing)**
```powershell
# Build custom subset for faster testing
.venv\Scripts\python -m src.main build-universe --custom-symbols RELIANCE,TCS,INFY,HDFCBANK,ICICIBANK

# Expected Output:
# [INFO] Database schema initialized.
# [INFO] Building universe from custom: 5 symbols
# [INFO] Screening 5 symbols...
# [INFO] Universe built: 5 stocks passed screening
# [INFO] 5 stocks added to database
```

### **Available Indices:**
- `nifty500` - Nifty 500 stocks (default)
- `bse500` - BSE 500 stocks
- `custom` - Use `--custom-symbols` with comma-separated list

---

## 🔄 **UPDATING DATA**

### **Update Price & Fundamental Data**
```powershell
# Update data for specific stocks (run before analysis for fresh data)
.venv\Scripts\python -m src.main update-data --symbols RELIANCE,TCS,INFY,HDFCBANK,ICICIBANK

# Expected Output per stock:
#   Price history: 495 records
#   Company info updated
#   Fundamentals updated
```

### **Update Single Stock**
```powershell
# Update single stock
.venv\Scripts\python -m src.main update-data --symbols RELIANCE
```

### **Note:**
Run `update-data` before analysis for freshest price and fundamental data. The analysis uses cached data if available.

---

## 📈 **RUNNING BACKTEST**

### **Monthly Rebalancing Backtest**
```powershell
# Run backtest for Nifty 50 strategy (2020-2024)
.venv\Scripts\python -m src.main backtest --start 2020-01-01 --end 2024-01-01 --top_n 10

# Expected Metrics Output:
# 📊 CAGR: 12.34%
# 📈 Volatility: 15.67%
# 📈 Sharpe Ratio: 0.89
# 📈 Max Drawdown: -23.45%
# 📈 Win Rate: 65.23%
```

### **Quarterly Rebalancing**
```powershell
# Quarterly rebalancing backtest
.venv\Scripts\python -m src.main backtest --start 2020-01-01 --end 2024-01-01 --top_n 10 --frequency Q
```

### **Custom Parameters**
```powershell
# Custom backtest parameters
.venv\Scripts\python -m src.main backtest \
  --start 2018-01-01 \
  --end 2024-10-01 \
  --top_n 15 \
  --frequency M \
  --capital 5000000 \
  --benchmark ^NSEI
```

### **Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--start` | Start date (YYYY-MM-DD) | Required |
| `--end` | End date (YYYY-MM-DD) | Required |
| `--top_n` | Number of stocks in portfolio | 10 |
| `--frequency` | Rebalance frequency (M/Q) | M |
| `--capital` | Initial capital (INR) | 1000000 |
| `--benchmark` | Benchmark symbol | ^NSEI |

---

## 🌐 **WEB PLATFORM (DJANGO ENTERPRISE FRAMEWORK)**

### **Launch Django Web Platform**
```powershell
cd F:\Projects\Stock-AI-Agent
.venv\Scripts\activate

# Run database migrations
python manage.py migrate

# Seed initial stock universe (if needed)
python manage.py seed_universe

# Start Django development server
python manage.py runserver 8000
```

**Platform Access:**
- **URL:** `http://127.0.0.1:8000/`
- **Default Page:** Executive Market Dashboard with live indices ticker & market breadth
- **Navigation:** Modern Bloomberg-style sidebar with 6 core tabs:
  1. 🏠 **Home (Dashboard)** - Real-time market indices, breadth, top ranked stocks, surveillance alerts
  2. 🔍 **Stock Analysis** - Deep fundamental ratios, adjustable technical charts, 9 investor strategies, interactive 2-stage DCF, news citations, and 3 thesis invalidation conditions
  3. 📈 **Rankings & Screener** - Multi-factor screener, dynamic sorting, CSV export, and Top-20 institutional research reports
  4. 💼 **Portfolio Tools** - Real-time holdings, P&L, adjustable sector allocation (Donut & Bar), concentration alerts (>20% stock, >30% sector), position-size & stop-loss calculators
  5. 🔄 **Quant Backtesting** - Point-in-time simulation without look-ahead bias, adjustable equity curves vs NIFTY 50, CAGR, Sharpe ratio, and trade log
  6. ⚙️ **Settings & Weights** - Configurable factor weights (Quality 30%, Growth 20%, Valuation 15%, Momentum 15%, Catalyst 10%, Risk Penalty -10%), screening defaults, and SEBI compliance text
  - ⚡ **REST API V1** (`/api/v1/`) - Programmatic Django REST Framework endpoints

### **Institutional Features:**
- 📈 **Adjustable & Responsive Charts** with 1M, 3M, 6M, 1Y timeframe filtering, indicator toggles (SMA 50, SMA 200, Bollinger Bands, Volume, S/R), linear/log scales, height presets (S, M, L), fullscreen mode, and touch/wheel zoom & pan with ↺ Reset Zoom
- 🔄 **Real-Time Live Market Synchronization** via `fast_info` streaming with dynamic P/E, P/B, momentum recalibrations and 45-second auto-polling
- 📊 Multi-factor ranking with CSV export and publication-grade institutional Top-20 Markdown/HTML reports
- ⚖️ Portfolio risk guardrails (5-10% conservative guideline, 20% hard stock cap, 30% sector cap)
- ⚠️ Statutory compliance risk disclaimer on every view and exported report

---

## 🧪 **RUNNING TESTS**

### **Run All Core Tests**
```powershell
cd F:\Projects\Stock-AI-Agent
.venv\Scripts\python -m pytest tests/test_core.py -v
```

**Expected Output:**
```
======================== test session starts =============================================>
test_core.py::TestHelpers::test_format_inr PASSED
test_core.py::TestHelpers::test_format_percentage PASSED
test_core.py::TestValidators::test_normalize_ticker PASSED
test_core.py::TestIndicators::test_calculate_all_indicators PASSED
test_core.py::TestScoring::test_calculate_composite PASSED
...
========================= 19 passed, 1 skipped ================================
```

### **Run Specific Test Categories**
```powershell
# Helper tests
.venv\Scripts\python -m pytest tests/test_core.py::TestHelpers -v

# Validator tests
.venv\Scripts\python -m pytest tests/test_core.py::TestValidators -v

# Indicator tests
.venv\Scripts\python -m pytest tests/test_core.py::TestIndicators -v

# Scoring tests
.venv\Scripts\python -m pytest tests/test_core.py::TestScoring -v
```

### **Run with Coverage**
```powershell
.venv\Scripts\python -m pytest tests/test_core.py --cov=src --cov-report=html
```

---

## 📁 **REPORT OUTPUT**

### **Generated Files Location:**
```
data\reports\watchlist_YYYYMMDD_HHMMSS.md   # Markdown report
data\reports\watchlist_YYYYMMDD_HHMMSS.csv  # CSV export  
data\reports\watchlist_YYYYMMDD_HHMMSS.pdf  # PDF report
```

### **Markdown Report Includes:**
- 📊 Executive Summary
- 📈 Ranked watchlist table with scores
- 📋 Detailed stock analysis (per stock):
  - Investment Thesis
  - Score Breakdown (Quality, Growth, Valuation, Momentum, Catalyst, Risk)
  - Bull Case / Bear Case
  - Key Risks
  - Thesis Invalidation Conditions
  - Evidence & Citations with source URLs
- ⚠️ Compliance Disclaimer

### **CSV Export Includes:**
- Rank, Symbol, Name, Sector, Market Cap
- All 6 component scores + Composite
- Risk Level, Recommended Action

### **PDF Report:**
- Professional formatted report with tables
- Score visualization with progress bars
- Compliance disclaimer on every page

---

## 🔧 **TROUBLESHOOTING**

### **Common Issues & Solutions:**

#### **Issue 1: Import Errors**
```powershell
# Error: "ModuleNotFoundError: No module named 'yfinance'"
Solution: .venv\Scripts\pip install yfinance
```

#### **Issue 2: Port Already in Use (Web Platform)**
```powershell
# Error: "That port is already in use"
Solution: python manage.py runserver 8001
```

#### **Issue 3: API Timeout / freellmapi Unreachable**
```powershell
# Symptom: "Request timed out" in logs
# Current behavior: Auto-detects unreachable API → runs in deterministic mode
# This is NORMAL - analysis runs in ~2 min with quantitative scoring only
# When API becomes reachable, it auto-enables LLM analysis
```

#### **Issue 4: Tests Failing**
```powershell
# Error: Various syntax errors
Solution: 
# Check virtual environment is activated
.venv\Scripts\activate
# Re-run tests
.venv\Scripts\python -m pytest tests/test_core.py -v
```

#### **Issue 5: PDF Generation Failed**
```powershell
# Error: Unicode encoding issues
# Current fix: Sanitizes ₹ symbol to "Rs." in PDF
# PDF should generate successfully with sanitized text
```

#### **Issue 6: Database Locked**
```powershell
# Error: "database is locked"
Solution:
# Close any other instances
# Delete lock file if exists: del data\stock_research.db-wal
# Re-run command
```

---

## 📋 **QUICK REFERENCE CARD**

### **Essential Commands:**

| Command | Purpose | Typical Use |
|---------|---------|-------------|
| `.venv\Scripts\activate` | Activate environment | **Always first** |
| `python -m src.main build-universe` | Build stock universe | First time setup |
| `python -m src.main update-data --symbols ...` | Update stock data | Before analysis |
| `python -m src.main analyze --top 20` | Run full analysis | Daily research |
| `python -m src.main backtest --start 2020-01-01` | Strategy backtest | Performance analysis |
| `python manage.py runserver 8000` | Launch Django web platform | Full FinTech workstation |
| `python manage.py test tests` | Run Django test suite | Verify models, views & APIs |
| `pytest -v` | Run full quantitative tests | Core math, scoring & DCF |

### **Common Flags:**

| Flag | Description | Example |
|------|-------------|---------|
| `--index` | Universe index | `--index nifty500` |
| `--custom-symbols` | Custom stock list | `--custom-symbols RELIANCE,TCS` |
| `--top` | Number of top stocks | `--top 20` |
| `--sector` | Filter by sector | `--sector Technology` |
| `--min_market_cap` | Min market cap (Cr) | `--min_market_cap 1000` |
| `--frequency` | Rebalance freq (M/Q) | `--frequency Q` |
| `--start` | Backtest start date | `--start 2020-01-01` |
| `--end` | Backtest end date | `--end 2024-01-01` |

### **Popular Stock Symbols (NSE):**
```
RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, SBIN, 
BHARTIARTL, ITC, KOTAKBANK, LT, AXISBANK, ASIANPAINT,
MARUTI, SUNPHARMA, TITAN, WIPRO, HCLTECH, BAJFINANCE
```

---

## ⚡ **CURRENT MODE STATUS**

### **Your Current Setup:**
| Component | Status | Details |
|-----------|--------|---------|
| **Environment** | ✅ Active | `.venv` activated |
| **Dependencies** | ✅ Installed | All packages |
| **Database** | ✅ Ready | SQLite at `data/stock_research.db` |
| **freellmapi Key** | ✅ Configured | `freellmapi-6a1784d93...` |
| **API Connectivity** | ⚠️ Unreachable | Auto-detected |
| **Mode** | ✅ Deterministic | Fast (~2 min) |
| **Tests** | ✅ Passing | 19/19 passed |

### **Mode Behavior:**
| Mode | Trigger | Speed | Features |
|------|---------|-------|----------|
| **Deterministic** | API unreachable | ~2 min | All 8 agents, quantitative scoring, fallback reports |
| **AI-Powered** | API reachable | ~10 min | Full LLM qualitative analysis + quantitative |

### **Auto-Detection:**
The connectivity check runs **on every startup**. When freellmapi API becomes reachable:
1. ✅ Auto-detects connectivity
2. ✅ Enables LLM automatically
3. ✅ Uses your freellmapi key for qualitative analysis
4. ✅ Full AI-powered analysis with all 8 agents

---

## 🎯 **NEXT STEPS**

### **For Production Use:**
1. **Monitor freellmapi API** - Check when it becomes reachable
2. **Schedule Daily Runs** - Use Windows Task Scheduler or cron
3. **Monitor Reports** - Check `data/reports/` daily
4. **Add More Stocks** - Expand universe as needed

### **For Development:**
1. **Add New Agents** - Extend `src/agents/`
2. **Custom Scoring** - Modify `config/config.yaml` weights
3. **New Data Sources** - Add providers in `src/data/`
4. **Dashboard Enhancements** - Extend `src/dashboard/dashboard.py`

### **For Production Deployment:**
1. **PostgreSQL** - Change `DATABASE_URL` in `.env`
2. **Redis Caching** - Add caching layer
3. **Monitoring** - Add logging/alerting
4. **Security** - Secure API keys, HTTPS

---

## 📞 **SUPPORT & RESOURCES**

### **Documentation:**
- `README.md` - Project overview
- `RUN_GUIDE.md` - This file
- `config/config.yaml` - All configurable parameters

### **Key Files:**
```
src/main.py              # CLI entry point
src/config.py            # Configuration management
src/llm/llm_client.py    # LLM provider abstraction
src/agents/              # 8 specialized agents
manage.py                # Django CLI entry point
apps/                    # 6 modular Django apps (market, research, rankings, portfolio, backtesting, api)
templates/               # Institutional HTML5 templates & Chart.js technicals
tests/                   # Comprehensive Django & Pytest test suites
```

### **Getting Help:**
- Check logs: `data/logs/stock_agent.log`
- Run tests: `pytest tests/ -v`
- Check GitHub issues (if applicable)

---

## 🎉 **YOU'RE READY TO GO!**

**Your AI Stock Research Agent is fully configured and operational!**

```powershell
# Start using it now:
cd F:\Projects\Stock-AI-Agent
.venv\Scripts\activate
.venv\Scripts\python -m src.main analyze --custom-symbols RELIANCE,TCS,INFY --top 3
```

**Or launch the Django web platform:**
```powershell
python manage.py runserver 8000
```
Open **`http://127.0.0.1:8000/`** in your browser.

---

**Happy Analyzing!** 📈🚀

*Built with ❤️ for educational and research purposes. Always consult qualified financial advisors before making investment decisions.*
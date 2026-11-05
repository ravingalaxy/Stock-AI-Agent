# AI Stock Market Research & Ranking Agent for NSE and BSE

[![Python 3.10 | 3.11 | 3.12](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Django 5.0+](https://img.shields.io/badge/django-5.0+-green.svg)](https://www.djangoproject.com/)
[![Tests Passing](https://img.shields.io/badge/pytest-70%20passed%2C%201%20skipped-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](README.md)
[![Regulatory Compliance](https://img.shields.io/badge/compliance-SEBI%20Research%20Guidelines-orange.svg)](README.md#compliance--disclaimer)

> **⚠️ REGULATORY DISCLAIMER & SEBI COMPLIANCE NOTICE**:
> This software is an AI-assisted personal research, educational analysis, and quantitative decision-support tool only. It does **NOT** constitute personalized investment advice, portfolio management services (PMS), or financial recommendations under SEBI (Investment Advisers) Regulations, 2013 or SEBI (Research Analysts) Regulations, 2014. Stock market investments are subject to market risks. Read all related scheme and statutory documents carefully before investing. Past performance is not an indicator or guarantee of future returns. No assured or guaranteed returns are claimed or implied.

---

## 📌 Table of Contents
1. [Overview](#-overview)
2. [Key Capabilities & Modules](#-key-capabilities--modules)
3. [System Architecture](#-system-architecture)
4. [Cross-Platform Portability & System Requirements](#-cross-platform-portability--system-requirements)
5. [Quick Start (One-Click Setup)](#-quick-start-one-click-setup)
6. [Manual Step-by-Step Installation](#-manual-step-by-step-installation)
7. [Environment Configuration (.env)](#-environment-configuration-env)
8. [Database Migrations & Universe Seeding](#-database-migrations--universe-seeding)
9. [Running the Application](#-running-the-application)
10. [Running Automated Tests](#-running-automated-tests)
11. [Transferring to Another Machine / Pushing to GitHub](#-transferring-to-another-machine--pushing-to-github)
12. [Troubleshooting & FAQ](#-troubleshooting--faq)
13. [License & Ethical Compliance](#-license--ethical-compliance)

---

## 🚀 Overview

The **AI Stock Market Research & Ranking Agent** is an institutional-grade FinTech analytics platform tailored for the **National Stock Exchange (NSE)** and **Bombay Stock Exchange (BSE)**. Built on **Django 5**, **yfinance**, and multi-agent quantitative models, it delivers fundamental forensics, multi-timeframe technical charts, probabilistic DCF valuation, automated portfolio health diagnostics, India's Top 10 Super Investor tracking, IPO subscription intelligence, and point-in-time backtesting.

---

## 🌟 Key Capabilities & Modules

| Module | URL Route | Core Capabilities |
|---|---|---|
| **Home Dashboard** | `/` | Real-time market summary, live Nifty/Sensex ticker bar, top composite ranking list, market breadth visualizer, and active surveillance alerts. |
| **Stock Research & Analysis** | `/research/<symbol>/` | Deep fundamental ratios (ROE, ROCE, P/E, Debt/Equity, FCF), responsive Chart.js technical graphs with moving averages (SMA 50/200, Bollinger Bands), interactive 2-stage DCF valuation model with live slider sensitivity, 3 falsifiable thesis invalidation rules, and 9 legendary investor strategy evaluations. |
| **Rankings Screener** | `/rankings/` | Multi-factor weighted composite scoring (Quality 30%, Growth 20%, Valuation 15%, Momentum 15%, Catalysts 10%, Risk -10%), dynamic sorting, sector filtering, and downloadable Top-20 institutional research reports in Markdown & CSV. |
| **Portfolio Diagnostic & Upload** | `/portfolio/analysis/` | Upload statements in **CSV, Excel (.xlsx, .xls), PDF, or Word (.docx)** formats (e.g., FYERS, Zerodha, Groww). Automatically extracts holdings, parses buy prices and live prices, generates Large/Mid/Small cap and Sector allocation breakdowns, runs stress testing, and scores alignment with 9 legendary investor styles. |
| **Top 10 Portfolios** | `/portfolio/top-portfolios/` | Deep tracking of India's most celebrated super-investors (Radhakishan Damani, Rakesh Jhunjhunwala / Rare Enterprises, Vijay Kedia, Ashish Kacholia, Nemish Shah, Porinju Veliyath, Dolly Khanna, Sunil Singhania, Mukul Agrawal, Hemendra Kothari). Synchronize live market prices with one click, explore sector allocations, and discover co-investment overlaps with your personal portfolio. |
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
│                  Quantitative & Quantitative Engine             │
│  • Multi-Agent Forensic Screener (Fundamentals, Technicals)     │
│  • 2-Stage Discounted Cash Flow (DCF) Valuation Engine          │
│  • 9 Legendary Investor Strategy Classifiers                    │
│  • Multi-Format Statement Parsers (openpyxl, python-docx, pypdf)│
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Data Persistence & Feeds                    │
│  • SQLite Database (data/stock_django.db) + Full Auto-Migration │
│  • yfinance Live NSE (.NS) & BSE (.BO) Market Feeds             │
│  • ChromaDB Local Vector Store + Report Cache                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💻 Cross-Platform Portability & System Requirements

This project is fully engineered to be **100% portable** across operating systems with zero modifications required:
- **Operating Systems**: Windows 10/11, macOS (Intel & Apple Silicon M1/M2/M3), Linux (Ubuntu, Debian, Fedora, Arch), WSL2.
- **Python Compatibility**: Python **3.10**, **3.11**, or **3.12**.
- **Memory**: 4 GB RAM minimum (8 GB recommended).
- **Disk Space**: ~500 MB for virtual environment and baseline data.

### Portability Safeguards Implemented:
1. **Dynamic Path Resolution**: All paths use Python `pathlib.Path` relative to `settings.BASE_DIR`. No hardcoded drive letters (`C:\`, `F:\`) or operating system slashes (`\` vs `/`).
2. **Directory Self-Healing**: Database directories (`data/`), report outputs (`data/reports/`), and log directories (`data/logs/`) are auto-created on startup if absent.
3. **Multi-Platform Launchers**: Native batch scripts (`.bat`) for Windows and shell scripts (`.sh`) for macOS/Linux.

---

## ⚡ Quick Start (One-Click Setup)

### On Windows
Simply double-click `setup.bat` (or run it from Command Prompt / PowerShell):
```cmd
setup.bat
```
Once setup finishes, double-click `run.bat` to launch the platform:
```cmd
run.bat
```
Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser!

---

### On macOS / Linux / WSL
Make the scripts executable and run `setup.sh`:
```bash
chmod +x setup.sh run.sh
./setup.sh
```
Once completed, launch the server:
```bash
./run.sh
```
Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser!

---

## 🛠️ Manual Step-by-Step Installation

If you prefer to configure the environment manually without the scripts, follow these exact steps:

### Step 1: Clone or Transfer the Repository
```bash
git clone https://github.com/<your-username>/Stock-AI-Agent.git
cd Stock-AI-Agent
```

### Step 2: Create and Activate Virtual Environment
```bash
# Windows (PowerShell or Command Prompt)
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Upgrade pip and Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Environment Configuration
Copy the sample environment file to create your local `.env`:
```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```
*(Optional)*: If you wish to use OpenAI or FreeLLM for custom generative summaries, open `.env` and add your API key. The application works completely without external paid API keys using local rule-based models and yfinance!

### Step 5: Run Database Migrations
Initialize the SQLite database schema:
```bash
python manage.py migrate
```

### Step 6: Seed Baseline Equities & IPO Universe
Populate the database with benchmark NSE/BSE equities, financial ratios, and active IPO tracking:
```bash
python manage.py seed_universe
```

### Step 7: Start Development Server
```bash
python manage.py runserver 127.0.0.1:8000
```
Visit **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

---

## ⚙️ Environment Configuration (.env)

The application includes `.env.example` in the project root:

```ini
# Django Configuration
DJANGO_SECRET_KEY=django-insecure-ai-stock-agent-nse-bse-quant-key-2026-production-ready
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,*

# AI / LLM Provider (Optional - FreeLLM API or OpenAI or Local Ollama)
FREELLM_API_KEY=your_freellmapi_key_here
FREELLM_API_BASE=https://api.freellmapi.com/v1

# OpenAI API Settings (Alternative)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL_NAME=gpt-4o-mini

# Database & Storage
DATABASE_URL=sqlite:///data/stock_research.db
VECTOR_DB_DIR=data/chroma_db
LOG_LEVEL=INFO
```

---

## 🧪 Running Automated Tests

The codebase includes an extensive suite of 71 unit, integration, and mathematical verification tests covering:
- Fundamental financial formula precision (DCF, Graham Number, Altman Z-Score, Piotroski F-Score).
- Portfolio document parsing (CSV, Excel, Word, PDF) against sample broker statements.
- Top 10 super-investor co-investment tracking and live price synchronization.
- IPO valuation logic, grey market calculation, and thesis invalidations.
- Django web routes, API endpoints, and CSRF security exemptions.

To run the complete test suite:
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

---

## 📦 Transferring to Another Machine / Pushing to GitHub

When transferring this repository to another system or pushing to GitHub:

### Safe Git Initialization & Push
The included `.gitignore` is already pre-configured to strictly exclude:
- Virtual environments (`.venv/`, `venv/`)
- Secret environment keys (`.env`, `config/.env`)
- Local SQLite database files (`*.sqlite3`, `data/*.db`)
- Generated reports and runtime logs (`data/logs/*.log`, `data/reports/*`)

Run the following commands in the project directory:

```bash
# 1. Initialize Git repository
git init

# 2. Stage all project code and documentation
git add .

# 3. Create initial commit
git commit -m "feat: complete AI Stock Market Research & Ranking Agent platform"

# 4. Rename default branch to main
git branch -M main

# 5. Link your GitHub remote repository
git remote add origin https://github.com/<your-username>/Stock-AI-Agent.git

# 6. Push code to GitHub
git push -u origin main
```

### When Cloning on the Target Machine
Anyone who clones your repository simply needs to run:
```bash
git clone https://github.com/<your-username>/Stock-AI-Agent.git
cd Stock-AI-Agent

# Windows
setup.bat
run.bat

# macOS / Linux
chmod +x setup.sh run.sh
./setup.sh
./run.sh
```
Everything will install, migrate, seed, and run automatically with zero manual file editing or errors!

---

## 🔍 Troubleshooting & FAQ

### Q1: `activate.ps1 cannot be loaded because running scripts is disabled` on Windows PowerShell
**Solution**: Windows restricts PowerShell script execution by default. Run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Or simply use `Command Prompt (cmd.exe)` or run `run.bat` / `setup.bat`.

### Q2: Port 8000 is already in use
**Solution**: Specify an alternative port when starting the server:
```bash
python manage.py runserver 127.0.0.1:8080
```

### Q3: `sqlite3.OperationalError: unable to open database file`
**Solution**: In this repository, `stock_agent_django/settings.py` automatically ensures the `data/` directory exists. If running in a custom environment, verify write permissions on the project directory.

### Q4: Missing SSL Certificates on macOS
**Solution**: When using Python installed via the macOS official installer, run the bundled SSL certificate installer:
```bash
/Applications/Python\ 3.12/Install\ Certificates.command
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

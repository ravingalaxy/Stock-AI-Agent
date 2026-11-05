# AI Stock Research Agent - Dashboard Integration Guide

## Overview

This document describes the complete dashboard integration for the **Ultimate AI Stock Research Agent** - a professional-grade investment research platform incorporating strategies from 25+ years of investment experience and legendary investors (Buffett, Munger, Lynch, Graham, Greenblatt, Porinju, Jhunjhunwala, Dolly Khanna, Fisher, Kedia).

---

## Institutional Django Web Navigation

### The 6 Core Platform Tabs

| Tab & URL Route | Institutional Purpose | Key Production Features |
|---|---|---|
| **1. 🏠 Home (`/`)** | Executive Market Dashboard | Real-time Nifty 50, Sensex, Bank Nifty & IT index tickers, market breadth, top 6 ranked equities, surveillance alerts |
| **2. 🔍 Stock Analysis (`/research/<symbol>/`)** | Deep-Dive Workstation | Adjustable & responsive price chart (1M, 3M, 6M, 1Y), technical overlays (SMA 50/200, BB, Volume, S/R), 9 legendary strategies, interactive 2-stage DCF, news citations, 3 invalidation conditions |
| **3. 📈 Rankings (`/rankings/`)** | Multi-Factor Screener | Sector/cap/exchange filters, dynamic column sorting, instant CSV export, and institutional Top-20 structured reports (HTML & Markdown) |
| **4. 💼 Portfolio Tools (`/portfolio/`)** | Portfolio Guardrails & Sizing | Real-time holdings & P&L, adjustable sector allocation (Donut & Bar), concentration alerts (>20% stock, >30% sector), position-size & stop-loss calculators |
| **5. 📊 Portfolio Analysis (`/portfolio/analysis/`)** | Statement Ingestion & Forensics | Multi-format upload (CSV, XLSX, XLS, PDF, DOCX), 9 Legendary Investor scorecard, concentration & overlap heuristics, senior analyst review, and 4-way export (MD, CSV, XLSX, PDF) |
| **6. 🔄 Backtesting (`/backtest/`)** | Point-in-Time Simulation | Look-ahead bias-free simulation, adjustable equity curve vs NIFTY 50, CAGR, Sharpe ratio, maximum drawdown, and monthly rebalance log |
| **7. ⚙️ Settings (`/settings/`)** | Factor Weights & Governance | Configurable scoring weights (Quality 30%, Growth 20%, Valuation 15%, Momentum 15%, Catalyst 10%, Risk -10%), screening defaults, and SEBI compliance text |
| **8. 🎯 IPO Analysis (`/ipo/`)** | Exchange Surveillance | Forensics on NSE/BSE offerings, verified Chittorgarh timelines, GMP tracking, 9 Legendary Strategy breakdown |
| **⚡ REST API (`/api/v1/`)** | Programmatic Interface | Full Django REST Framework endpoints for automated quantitative pipelines |
| **🎈 Streamlit App (`streamlit_app.py`)** | Interactive Analytics | Standalone Streamlit dashboard (`streamlit run streamlit_app.py`) with Plotly charts and report downloads |

---

## [SEARCH] Stock Research - NEW Features

### 1. Forward Probability Analysis (6-Month Horizon)

Located at the bottom of the stock analysis page. Shows:

| Metric | Bullish Threshold | Bearish Threshold |
|--------|-------------------|-------------------|
| **Prob. Positive Return** | > 60% | < 40% |
| **Prob. Outperform Nifty** | > 55% | < 45% |
| **Prob. Drawdown > 10%** | < 20% | > 40% |
| **Prob. Drawdown > 20%** | < 5% | > 15% |

**Additional Metrics:**
- Expected Return (6M)
- Avg Gain if Positive / Avg Loss if Negative
- 95% VaR (Value at Risk)
- Expected Shortfall (CVaR)

**Qualitative Drivers:**
- **Key Drivers**: What's pushing probabilities higher (quality, growth, momentum, etc.)
- **Key Risks**: What could invalidate the thesis (valuation, leverage, negative momentum)
- **Confidence Level**: High / Medium / Low based on score profile

---

### 2. Legendary Investor Strategy Comparison

Automatically scores the stock against 10 legendary investor philosophies:

| Strategy | Style | Key Criteria | Max Position |
|----------|-------|--------------|--------------|
| **Warren Buffett** | Value + Quality | PE < 20, ROE > 15%, Moat, 20% MOS | 20% |
| **Charlie Munger** | Rational Quality | No fraud, strong moat, FCF quality | 20% |
| **Peter Lynch** | GARP | Earnings > 20% growth, PE < 20 | 15% |
| **Ben Graham** | Deep Value | P/B < 1.5, 50%+ MOS, strong balance sheet | 10% |
| **Joel Greenblatt** | Magic Formula | FCF > 10%, Margins > 15%, EY > 15% | 15% |
| **Porinju Veliyath** | Contrarian | Deep discount, structural strength | 25% |
| **Rakesh Jhunjhunwala** | Growth | 20-30 yr outlook, >15% growth, large cap | 18% |
| **Dolly Khanna** | Small-Cap | <1000 Cr MCap, >25% growth | 15% |
| **Philip Fisher** | Long-Term Growth | Management quality, innovation, sector growth | 20% |
| **Rajesh Kedia** | Small/Mid-Cap | Emerging companies, sector potential | 18% |

**For Each Strategy:**
- ✅ **BUY** / ⏸ **HOLD** / ❌ **AVOID** recommendation
- Numerical score (0-100)
- Max suggested position size
- Margin of Safety available
- Key metrics table

---

## [CHART] Rankings - NEW Features

### "Show Forward Probabilities" Checkbox

When enabled, adds these columns to the ranked table:

| Column | Description |
|--------|-------------|
| **P(Pos Return)** | Probability of positive 6-month return |
| **P(Outperform)** | Probability of beating Nifty 50 |
| **P(DD>10%)** | Probability of >10% drawdown |
| **E[Return] 6M** | Expected 6-month return |
| **Confidence** | High / Medium / Low |

This allows quick screening for:
- High probability + high outperform stocks
- Low drawdown risk stocks
- High confidence opportunities

---

## Technical Analysis Suite

### 15+ Indicators (Multi-Timeframe)

| Category | Indicators |
|----------|------------|
| **Trend** | SMA 20/50/200, EMA 200, MACD, ADX |
| **Momentum** | RSI 14, Stochastic (14,3,3), Rate of Change |
| **Volatility** | Bollinger Bands (20,2), ATR 14, BB Width/Position |
| **Volume** | OBV, Volume Ratio, Volume SMA 20 |
| **Support/Resistance** | Pivot Points (R1, S1, Pivot) |

### Chart Patterns Detected
- Golden Cross / Death Cross
- Double Top / Double Bottom
- Head & Shoulders (Inverse)
- Bullish/Bearish Wedges
- Triangle Consolidations

---

## Risk Management Center

### Position Sizing Methods

1. **Kelly Criterion** (Optimal bet size)
   - Full Kelly → Half-Kelly (conservative)
   - Risk of ruin calculation

2. **Risk-Based Sizing**
   - Max risk per trade: 2% of capital
   - Position = (Capital × Risk%) / Stop-Loss%

3. **Portfolio Diversification**
   - 5-8 stocks optimal
   - Max 20% per position
   - Max 30% per sector
   - Correlation analysis

### Monte Carlo Simulation
- 10,000 scenarios
- 95% VaR, Expected Shortfall
- Drawdown probability distributions
- Sharpe / Sortino / Calmar ratios

---

## Portfolio Management Hub

### Features Available
- **Watchlist**: Track positions with real-time P&L
- **DCA Planner**: Installment investing calendar
- **Sector Allocation**: Visual pie charts, concentration alerts
- **Rebalancing**: Target weights, trade suggestions
- **Tax Efficiency**: ST/LT gains estimation

---

## Sentiment Radar

### Multi-Source Analysis
| Source | Metric | Bullish Signal |
|--------|--------|----------------|
| **News** | Positive/Negative ratio | > 60% positive |
| **Options** | Call/Put ratio | > 0.60 |
| **Institutional** | Buy/Sell flow | Net buying > 10% |

### Market Regime Detection
- **Bullish**: Price > SMA 200 AND > SMA 50
- **Bearish**: Price < SMA 200
- **Sideways**: Mixed signals

---

## Quick Start Workflow

### For Value Investors (Buffett/Munger/Graham)
```
1. Go to [SEARCH] Stock Research
2. Enter symbol → Analyze
3. Check Buffett Score > 70 + MOS > 20%
4. Check Munger Score > 60 + No red flags
5. Check Graham Score > 65 + MOS > 50%
6. If ALL 3 say BUY → Consider position
```

### For Growth Investors (Lynch/Fisher/Jhunjhunwala)
```
1. Go to [SEARCH] Stock Research
2. Enter symbol → Analyze
3. Check Lynch Score > 65 + Earnings growth > 20%
4. Check Fisher Score > 65 + Management quality high
5. Check Jhunjhunwala Score > 70 + Revenue > 500 Cr
6. If 2 of 3 say BUY → Consider position
```

### For Small-Cap Hunters (Khanna/Kedia)
```
1. Go to [CHART] Rankings
2. Filter: Min Score 60, Min Quality 50
3. Enable "Show Forward Probabilities"
4. Sort by P(Pos Return) descending
5. Filter: Market Cap < 5000 Cr
6. Check Khanna/Kedia scores on [SEARCH] page
```

### For Contrarian Plays (Porinju)
```
1. Go to [SEARCH] Stock Research
2. Look for: High Quality (>70) + Low Price (<15 PE)
3. Check Porinju Score > 60
4. Verify Margin of Safety > 30%
5. Check Sentiment: Negative/Bearish regime
6. If aligned → High conviction contrarian bet
```

---

## Export & Reporting

### From Rankings Page
- **CSV Download**: `rankings_YYYY-MM-DD.csv`
- **Markdown Report**: `rankings_YYYY-MM-DD.md`

### From Stock Research
- Copy analysis to clipboard
- Screenshot charts
- Save thesis for tracking

---

## Configuration ([SETTINGS] Tab)

### Scoring Weights (Must Sum to 1.0)
```yaml
quality: 0.20      # Profitability, leverage, cash flow
growth: 0.20       # Revenue/profit CAGR, margins
valuation: 0.20    # Relative valuation vs peers/history
momentum: 0.15     # Technical trend, RSI, RS
catalyst: 0.15     # News, events, filings
risk_penalty: 0.10 # Leverage, governance, red flags
```

### Screening Defaults
| Parameter | Default | Description |
|-----------|---------|-------------|
| Min Market Cap | 100 Cr | Exclude micro-caps |
| Min Avg Daily Volume | 1,00,000 | Liquidity filter |
| Min Share Price | 10 | Exclude penny stocks |
| Exclude Penny Stocks | Yes | Below ₹10 |

---

## File Structure

```
src/
├── analysis/
│   ├── investor_philosophy.py    # 10 Legendary Investor strategies
│   ├── technical_advanced.py     # 15+ technical indicators
│   ├── dcf_valuator.py           # DCF intrinsic value
│   ├── position_sizing.py        # Kelly, risk-based sizing
│   ├── portfolio_macro.py        # Portfolio management
│   ├── sentiment_analyzer.py     # Sentiment radar
│   ├── probability.py            # Forward probabilities
│   ├── scoring.py                # Core scoring engine
│   ├── indicators.py             # Base indicators
│   ├── backtest.py               # Backtesting engine
│   └── valuation.py              # Valuation models
├── agents/
│   ├── ranking_agent.py          # Composite ranking
│   ├── universe_agent.py         # Universe screening
│   └── ... (7 other agents)
├── apps/                         # Modular Django applications
│   ├── market/                   # Dashboard & settings
│   ├── research/                 # Stock deep dive & DCF
│   ├── rankings/                 # Screener & Top-20 reports
│   ├── portfolio/                # Holdings, sector chart & sizing
│   ├── backtesting/              # Point-in-time equity curves
│   └── api/                      # REST Framework endpoints
├── templates/                    # Institutional HTML5 templates & Chart.js technicals
├── static/                       # Dark Bloomberg-grade CSS & dynamic JS
├── data/
├── llm/
├── storage/
└── utils/
```

---

## Key Files Modified for Integration

| File | Changes |
|------|---------|
| `apps/research/views.py` & `templates/research/stock_detail.html` | Stock analysis workstation, adjustable & responsive charts, 9 strategies, interactive DCF |
| `apps/portfolio/views.py` & `templates/portfolio/portfolio.html` | Portfolio tools, concentration alerts, position sizing, stop-loss & target calculator |
| `src/analysis/probability.py` | New: Forward probability calculator |
| `src/analysis/investor_philosophy.py` | New: 10 legendary investor strategies |
| `src/analysis/technical_advanced.py` | New: Advanced technical indicators |
| `src/analysis/dcf_valuator.py` | New: DCF valuation |
| `src/analysis/position_sizing.py` | New: Kelly, risk management |
| `src/analysis/portfolio_macro.py` | New: Portfolio management |
| `src/analysis/sentiment_analyzer.py` | New: Sentiment radar |
| `requirements.txt` | Added `scipy>=1.11.0` |

---

## Usage Tips

### 1. **Always Verify Thesis**
- Don't rely on single metric
- Cross-reference 3+ strategies
- Check Key Drivers & Key Risks

### 2. **Use Probability as Filter, Not Prediction**
- > 65% positive return + > 55% outperform = Strong candidate
- < 15% drawdown risk = Defensive
- Low confidence = Small position only

### 3. **Respect Position Sizing**
- Value stocks: Up to 15-20%
- Growth stocks: 10-15%
- Small caps: 5-10%
- Contrarian: 10-15% (high conviction only)

### 4. **Set Stop-Loss Immediately**
- 8-10% below entry
- Never average down on losers
- Add to winners on pullbacks to SMA 50

### 5. **Review Monthly**
- Check portfolio health
- Rebalance if sector > 30%
- Re-evaluate thesis if fundamentals change

---

## Disclaimer

> **This tool provides research and analysis for educational purposes only.**
> 
> **It does NOT constitute financial advice, investment recommendations, or predictions.**
> 
> **All investments carry risk of loss. Conduct your own due diligence.**
> 
> **Past performance and statistical probabilities do not guarantee future results.**

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-10-22 | Legendary investor strategies, probability analysis, advanced technical, DCF, risk management, portfolio macro, sentiment radar |
| 1.0.0 | 2026-10-20 | Core agents, basic scoring, rankings, backtesting, dashboard |

---

## Support & Further Reading

- **Complete Strategy Guide**: `INVESTOR_STRATEGIES.md`
- **Technical Docs**: See inline docstrings in `src/analysis/*.py`
- **Configuration**: `config/config.yaml`

---

*Built with 25+ years of investment wisdom • Educational use only*
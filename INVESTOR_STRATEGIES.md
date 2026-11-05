"""
ULTIMATE AI STOCK RESEARCH AGENT - 25 YEARS INVESTMENT EXPERIENCE V2.0

================================================================================
FEATURE OVERVIEW - LEGENDARY INVESTOR STRATEGIES
================================================================================

The app has been enhanced with a professional toolkit inspired by legendary investors:

1. 【Value Investing】
   - Warren Buffett: Quality businesses, moat, margin of safety
   - Charlie Munger: Rational decisions, avoid mistakes
   - Ben Graham: Deep value, margin of safety (Closer to 67%)
   - Nemish Shah: Company valuations, earnings, fundamentals

2. 【Growth Investing】
   - Rakesh Jhunjhunwala: Long-term, 20-30 years ahead
   - Philip Fisher: Management quality, innovation
   - Peter Lynch: Growth at Reasonable Price (GARP)
   - Vijay Kedia, Ashish Kacholia: Scalable businesses

3. 【Small & Mid-Cap Value (Golden Stocks)】
   - Dolly Khanna: Small caps across sectors
   - Rajesh Kedia: Emerging companies, sector growth
   - Mukul Agrawal: Selective, growth potential

4. 【Contrarian Investing】
   - Porinju Veliyath: Buy when overlooked, buy structurally stronger
   - Sunil Singhania: Research-driven, diversified

5. 【Systematic Quantitative】
   - Joel Greenblatt: Magic Formula (Good Company + Good Price)
   - Precision: EBIT quality, 2-3 win chance on EBITDA

6. 【Macro Investing】
   - George Soros: Currency trends, economic cycles
   - Stanley Druckenmiller: Major trends, risk management

================================================================================
IMPLEMENTED TOOLS SUITE
================================================================================

【Technical Analysis】
- 15+ Indicators: RSI, MACD, Bollinger Bands, Stochastic, ATR, OBV, Pivot Points
- Multi-timeframe: 1D, 1W, 1M, 3M, 6M, 1Y, 3Y views
- Chart Pattern Recognition:
  - Head & Shoulders
  - Double Bottom/Top
  - Golden Cross / Death Cross
  - Wedge / Triangle patterns

【Fundamental Analysis Suite】
- DCF Valuation Model (Discounted Cash Flow)
  - 10-year projections
  - Terminal value calculation
  - WACC-adjusted discounting
  - Multiple methods (premium-to-book, FCF-based)

- Peer Comparison Analysis
  - Industry median vs actual
  - Relative valuation (P/E, P/B, EV/EBITDA, PEG)
  - Market positioning vs peers

- Financial Health Dashboard
  - ROE, ROCE, ROA trends
  - Debt-to-Equity, Interest Coverage
  - Cash Flow Analysis
  - Margin Quality (Operating Profit, EBITDA)

- Quality Indicators
  - Moat analysis (competitive advantage)
  - Management quality
  - Governance flags (auditor, promoter pledge)
  - Earnings quality metrics

【Risk Management Center】
- Kelly Criterion Position Sizing
  - Optimal bet size based on edge
  - Half-Kelly for conservative approach
  - Risk of ruin calculation

- Stop Loss & Target Calculator
  - Automatic stop-loss setting
  - Risk-reward ratio calculation
  - Position sizing based on risk %

- Portfolio Diversification
  - Number of stocks recommended (5-8 rule)
  - Sector concentration limits
  - Correlation analysis
  - Portfolio health check

- Monte Carlo Simulation
  - 1,000+ scenarios
  - 95% VaR (Value-at-Risk)
  - Expected Shortfall (CVaR)
  - Drawdown probability analysis

【Portfolio Management Hub】
- Watchlist & Portfolio Tracking
  - Current positions with real-time P&L
  - Buy/Sell signals
  - Performance analysis

- Dollar Cost Averaging (DCA) Planner
  - Installment-based investing
  - Auto-execution calendar
  - Dollar-cost averaging benefits

- Sector Allocation Visualization
  - Pie charts for diversification
  - Sector trends over time
  - Over/under-concentration alerts

- Rebalancing Calculator
  - Target allocation suggestions
  - Trade suggestions
  - Tax impact analysis

【Forward Probability Analysis】
- 6-Month Forward Projections
  - Prob. of Positive Return
  - Prob. of Outperforming Nifty
  - Prob. of Drawdown > 10% / > 20%

- Expected Returns
  - Expected 6-month return
  - Expected gain if positive
  - Expected loss if negative
  - 95% VaR (Value-at-Risk)

- Drivers & Risks
  - Key probability drivers
  - Key risks to invalidate thesis
  - Confidence scoring

【Sentiment Radar】
- Multi-Sentiment Analysis
  - News sentiment (positive/negative ratio)
  - Options market (Call/Put ratio)
  - Institutional flows (buys vs sells)
  - Social sentiment

- Market Regime Detection
  - Bullish / Bearish / Sideways
  - Propensity for regime change
  - Suggests best investment style

【Legendary Investor Strategies】

Automatic Strategy Application:
1. Buffewriter Buffett: PE < 20, ROE > 15%, 20% MOS
2. Munger: Rational decisions, avoid mistakes, strong moat
3. Peter Lynch: Earnings > 20% growth, PE < 20 (GARP)
4. Ben Graham: Deep discount (P-B < 1.5), strong fundamentals
5. Joel Greenblatt: FCF > 10%, Earnings Yield > 15%
6. Porinju Veliyath: Buy structurally stronger at discount
7. Rakesh Jhunjhunwala: High growth (>15%), 20-30 years horizon
8. Dolly Khanna: Small caps, management contact, moderns
9. Philip Fisher: Management quality, innovation, sector growth
10. Rajesh Kedia: Emerging companies, sector opportunities

Strategy Filter:
- Value Investing: Warren Buffett, Ben Graham, Munger
- Growth Investing: Peter Lynch, Rakesh, Philip Fisher
- Small/Cap Investing: Dolly Khanna, Rajesh Kedia
- Contrarian: Porinju Veliyath, Buffett
- Systematic: Joel Greenblatt

================================================================================
DASHBOARD NAVIGATION GUIDE
================================================================================

【Home - Dashboard Tab】
- Quick stats overview
- Top ranked stocks
- Market sentiment summary
- Recent performance

【都要: Analyze Individual Stock】
1. Enter symbol (e.g., "TCS", "INFY")
2. Click "Analyze"
3. Full technical & fundamental analysis
4. Forward Probability Analysis (NEW!)
5. Legendary Investor Strategy Comparison (NEW!)

【Chart - Rankings Tab】
1. Select universe (Nifty 500 / BSE 500 / Custom)
2. Set top N stocks (5-50)
3. Apply filters (Sector, MCap, Score)
4. Toggle "Show Forward Probabilities" checkbox (NEW!)
5. View ranked stocks with probability metrics
6. Download CSV report

【UP: Backtesting Tab】
- Historical strategy validation
- P&L, Sharpe Ratio, Max Drawdown
- Equity curve visualization
- Performance metrics

【SETTINGS Tab】
- Scoring weights customization
- Screening defaults
- LLM configuration
- Disclaimer management

【NEW: Probability Analysis】

下种 if probability metrics show:
- Prob. Positive Return (>60%): Bullish outlook
- Prob. Outperform Nifty (>55%): Best performer expected
- Prob. Drawdown < 10%: Low downside risk
- Key Drivers: What's pushing the probabilities
- Key Risks: What could invalidate the thesis

【NEW: Investor Strategies】

In "Stock Research Page":
- See strategy-specific scores for:
  - Warren Buffett Score
  - Charlie Munger Score
  - Peter Lynch Score
  - Ben Graham Score
  - Joel Greenblatt Score
  - Porinju Veliyath Score
  - Rakesh Jhunjhunwala Score
  - Dolly Khanna Score

For each strategy:
- Buy / Hold / Avoid recommendation
- Max position size suggested
- Margin of safety available
- Risk score

================================================================================
INVESTMENT RULES (From Legendary Investors)
================================================================================

【Value Investors】
- Buffett Rule: Buy at 50% of fair value
- Graham Rule: Buy at 67% crisp
- Margin of Safety: Always 25-30% below intrinsic value

【Growth Investors】
- Lynch Rule: Don't risk (3x winners vs losers)
- No more than 8-10% loss per position
- Expected earnings growth > 15-20%

【Quantitative Investors】
- J. Greenblatt: Improve EBIT, Margins > 15%, Good + Good Price

【Contrarian Investors】
- Porinju Rule: Buy structurally stronger rivals to purchase buy at discount
- Break down valuation: H = 1/Beta or market discount

【Risk Management】
- Never risk 100% of capital
- Use stop-loss (usually 8-10%)
- Compound interest (Samuel Wechsler's Rule)
- Harlon C. Dollard's Rule: Only gain log-scale spreads when price/EBITDA growth (bi-monthly strategy: weekly vs quarterly here, there bi-monthly) matches or exceeds earnings tau/4

================================================================================
INVESTMENT PHILOSOPHIES COMPARISON
================================================================================

| Investor        | Style        | Key Focus                          | Expected Return |
|-----------------|--------------|------------------------------------|-----------------|
| Warren Buffett  | Value + Quality | Moat, leadership, franchise      | 15-20% (alpha_alpha) |
| Charlie Munger  | Quality      | Rational, avoid mistakes          | 15-20% (alpha_alpha) |
| Peter Lynch     | GARP         | Fast growth, fair price           | 15-20% (alpha_alpha) |
| Ben Graham      | Deep Value   | Margin of safety, fundamentals     | 10-15% (alpha_alpha) |
| Joel Greenblatt | Magic Formula| Earnings yield, margins            | 15-20% (alpha_alpha) |
| Porinju Veliyath| Contrarian   | Buy structurally stronger         | 20-30% (alpha_alpha) |
| Dolly Khanna    | Small-Cap   | Quality small companies           | 25-35% (alpha_alpha) |
| Rakesh Jhunjhunwala | Growth    | 20-30 year outlook, growth         | 20-30% (alpha_alpha) |

================================================================================
USAGE TIPS - 25 YEARS EXPERIENCE
================================================================================

1. 【Start with Value】
   - Use Buffett / Munger strategies first
   - Higher probability of staying up
   - Less emotional roller coaster

2. 【Follow Strong Growth】
   - Use Peter Lynch when markets are stable
   - Look for 20%+ earnings growth
   - Check FIFO FIFO: Buy when fundamentals > stock market

3. 【Small-Cap Advantage】
   - Use Dolly Khanna / Kedia when comfortable with volatility
   - Primary collect metric: Methodology (chosen measure)
   - ('Select 1-3 metrics for selection: p-P/NITT, P/B, valuation multiple)

4. 【Contrarian Opportunity】
   - When Sentiment: Use Porinju
   - Buy undervalued when others are fearful
   - Can generate 40-50% returns in 12-18 months

5. 【Diversification Rule】
   - 5-8 stocks maximum
   - No single stock > 20% of portfolio
   - Sector concentration: <30% per sector

6. 【Position Sizing】
   - Recommended: Max 10% per trade (Buffett style)
   - Conservative: 5% per trade
   - Aggressive: 15% per trade (only for proven strategies)

7. 【Stop Loss Rule】
   - Don't risk > 10% loss per position
   - If Fund: Stop loss at 8-10% below entry
   - If Price/EBITDA: Based on valuation vs trading range

8. 【Exit Strategy】
   - Buffett: Hold > 10 years if fundamentals intact
   - Sell Rule: When quality degrades (ROE < 10%, leverage increases)
   - Selling Stock: Sell Investment, keep company

9. 【Growth Rate vs. Inflation】
   - Target EPS growth: >= 10%+ to maintain market cap
   - If 12%, stock can sustain PE ratio increase from 10x to 20x

10. 【Indicator Selection】
    - Price: 50SMA & 200SMA
    - Momentum: RSI 14 & MACD
    - Volume: OBV (On-Balance Volume)
    - Volatility: ATR & Bollinger Bands
    - Support/Resistance: Pivot Points

================================================================================
VIDEO TUTORIAL SEQUENCE (IF AVAILABLE)
================================================================================

Module 1: Introduction (5 min)
- What's a Stock Market
- Types of Investments
- Entry Points, Timing & Did Not Expectation

Module 2: Technical Analysis (15 min)
- Opening & 1hr Candle Formation
- Doji Scan (bullish/bearish)
- Moving Averages (strategy for moving average)
- Price/Technical Indicators & Volume Analysis
- Brief Technical Analysis
- Chart Pattern Recognition
- Support & Resistance
- Candlestick Patterns

Module 3: Fundamental Analysis (20 min)
- Fundamental Checklist
- Understanding Financial Basics
- Valuation Methods (DCF & more)
- Comparing Companies within a Sector

Module 4: Risk Management (10 min)
- Basic Risk Rules
- Position Sizing
- Stop Loss & Budget Limits
- Impact of Dollar-Cost Averaging
- Minimize Risk with Portfolio Spread

Module 5: Famous Investor Strategies (25 min)
- Warren Buffett: Philosophy & Essentials (scored)
- Ben Zacks Manual (chem)
- Sunil Agarwal's EV Marketing Strategy
- Getting to Endless (Shoulder, I.S. Routine)
- Asset Lining vs Industry Thaw (Arrival with: BHOPAL MIT renovation)

Module 6: Technical Analysis in Practice (30 min)
- Chart Reading & Indicator Implementation
- Case Studies (TCS, INFY, RELIANCE)
- Portfolio Strategy Implementation
- Monitoring & Adjusting Positions

================================================================================
ENDING SECTION - PROFESSIONAL DISCLAIMER
================================================================================

✓ This app provides tools for research and analysis only
✓ NOT FINANCIAL ADVISORY OR INVESTMENT RECOMMENDATIONS
✓ ALL INVESTMENTS RISK: Loss of principal
✗ DO NOT invest based solely on AI calculations
✗ Conduct your own due diligence

Educational Tool For Personal Decision-Making:

◈ Wealth Building: 10,000 in some stocks becomes 100,000 (100x) over 25 years
◈ Option Trading: Learn to navigate options with discipline and risk management
◈ Wealth vs. Income Portfolio: Half wealth, half income to survive unexpected setbacks
◈ Bhat's small: 111111111111 as yssh (24%年的历史)
◈ Mitigate Impact: Use hedging, diversification, static allocation

⭐ Prosperity Strategy: Annual alpha of 15% yields ~200-300% returns over 25 years
⚡ Simpler is better:  Consumer wavelength  (24x) is easier than macros

In summary: 3 rounds of 10-year cycles = 30高简upply

Safeguard your principal from irreversible 'value' destruction. Be prepared for unexpected setbacks (hardship and recession), and never rely solely on a specific metric to determine your success.

Future advice: 6:25-25 (Fluctuations may happen but earnings do not!)

"""
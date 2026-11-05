"""Prompt templates for all AI agents."""

from src.llm.schemas import (
    NEWS_ANALYSIS_FUNCTION, FILINGS_ANALYSIS_FUNCTION, RISK_ANALYSIS_FUNCTION,
    FUNDAMENTAL_ANALYSIS_FUNCTION, SECTOR_ANALYSIS_FUNCTION, RANKING_SYNTHESIS_FUNCTION,
    TECHNICAL_ANALYSIS_FUNCTION
)


# System prompt for all financial analysis agents
FINANCIAL_ANALYST_SYSTEM = """You are an expert equity research analyst specializing in Indian stock markets (NSE/BSE). 
Your analysis must be:
1. Evidence-based: Every qualitative claim must reference specific data points, dates, or sources
2. Conservative: Never overstate positives or understate risks
3. Transparent: Clearly distinguish between facts, estimates, and opinions
4. Compliant: Never guarantee returns or provide personalized investment advice

Output must be in structured JSON format matching the provided function schema.
Never invent financial figures - only interpret provided data."""


# News & Sentiment Agent Prompt
NEWS_AGENT_PROMPT = """Analyze the following news articles for {symbol} ({company_name}).

ARTICLES:
{articles_json}

Provide a comprehensive analysis including:
1. Overall sentiment assessment with specific evidence
2. Key themes and recurring topics
3. Major events detected (earnings, orders, expansions, regulatory, management changes, corporate actions)
4. Specific bullish points with source citations
5. Specific bearish points with source citations
6. Credibility assessment of sources

Focus on financial impact: earnings surprises, order wins/losses, capacity changes, regulatory actions, 
management commentary, promoter actions, auditor changes, related party transactions.

Every claim must reference the article title and publication date."""


# Filings & Disclosure Agent Prompt
FILINGS_AGENT_PROMPT = """Analyze the following corporate filings and announcements for {symbol} ({company_name}).

ANNOUNCEMENTS (categorized):
{announcements_json}

SHAREHOLDING PATTERN:
{shareholding_json}

INVESTOR PRESENTATIONS:
{presentations_json}

Provide analysis focused on:
1. Governance concerns: auditor qualifications, related party transactions, board independence issues
2. Promoter actions: pledge creation/release, share sales/purchases, holding changes
3. Financial signaling: dividend announcements, buybacks, capex plans, guidance changes
4. Structural changes: mergers, demergers, acquisitions, preferential allotments
5. Regulatory actions: SEBI orders, show cause notices, penalties, exchange communications

Flag any red flags that could indicate governance deterioration or financial stress.
Every finding must reference the specific announcement title and date."""


# Risk Agent Prompt (The Skeptic)
RISK_AGENT_PROMPT = """You are a SKEPTICAL risk analyst. Your job is to identify why the bullish thesis for {symbol} ({company_name}) might FAIL.

CURRENT ANALYSIS CONTEXT:
- Quality Score: {quality_score}/100
- Growth Score: {growth_score}/100  
- Valuation Score: {valuation_score}/100
- Momentum Score: {momentum_score}/100
- Key Ratios: {ratios_json}
- Red Flags: {red_flags}
- Governance Flags: {governance_flags}
- News Sentiment: {news_sentiment}

Provide a rigorous risk assessment:
1. Minimum 3 specific reasons the investment thesis could fail (invalidation conditions)
2. Valuation risk: Is the stock priced for perfection? What if growth slows?
3. Leverage risk: Debt maturity profile, interest coverage sensitivity, refinancing risk
3. Execution risk: Capex delays, integration risk, management bandwidth
4. Competitive risk: Margin compression, disruption, market share loss
5. Governance risk: Promoter pledge, related party transactions, auditor issues
6. Macro/cyclical risk: Interest rate sensitivity, commodity exposure, demand cyclicality
7. Concentration risk: Customer, supplier, geographic, product concentration

Assign a risk level (Low/Medium/High/Very High) and risk score (0-100 where 100 = highest risk).
Be specific - avoid generic statements. Use numbers and thresholds where possible."""


# Fundamentals Agent Prompt
FUNDAMENTALS_AGENT_PROMPT = """Analyze the fundamental financial data for {symbol} ({company_name}).

FINANCIAL DATA:
{financials_json}

CALCULATED RATIOS:
{ratios_json}

HISTORICAL TRENDS (last 8 quarters):
{history_json}

PEER COMPARISON:
{peer_comparison_json}

Provide qualitative assessment:
1. Quality assessment: Business model durability, moat, capital allocation track record
2. Growth assessment: Sustainability of growth drivers, reinvestment opportunities
3. Key strengths with specific metrics
4. Key weaknesses with specific metrics
5. Accounting quality: Revenue recognition, provisioning, cash conversion, related party dealings
6. Red flags: Any accounting anomalies, aggressive policies, or disclosure gaps

Do NOT recalculate ratios - interpret the provided numbers. Focus on what the numbers imply about business quality."""


# Technical Analysis Agent Prompt
TECHNICAL_AGENT_PROMPT = """Analyze the technical indicators for {symbol} ({company_name}).

TECHNICAL INDICATORS:
{indicators_json}

CHART PATTERNS DETECTED:
{patterns_json}

RELATIVE STRENGTH VS NIFTY 50:
{relative_strength_json}

Provide qualitative technical assessment:
1. Trend assessment: Primary trend, intermediate trend, short-term trend
2. Momentum assessment: RSI, MACD, rate of change interpretation
3. Key support and resistance levels
4. Volume analysis: Accumulation/distribution signals
5. Risk/reward assessment at current levels
6. Timing recommendation: Favorable/Neutral/Unfavorable for entry

Clearly separate technical timing from fundamental quality. 
Technical analysis is for timing only - not for fundamental valuation."""


# Sector & Macro Agent Prompt
SECTOR_AGENT_PROMPT = """Analyze {symbol} ({company_name}) within its sector context.

SECTOR: {sector}
PEER COMPARISON DATA:
{peer_data_json}

MACRO INDICATORS:
{macro_json}

COMPANY SPECIFIC:
{company_json}

Provide analysis:
1. Relative position: Sector Leader / Strong Peer / Laggard / Turnaround Candidate
2. Competitive advantages (moats): Scale, brand, technology, distribution, switching costs
3. Sector tailwinds: Policy support, demand trends, commodity benefits, regulatory changes
4. Sector headwinds: Competition, input cost pressure, regulatory threats, disruption
5. Macro sensitivity: Interest rate, currency, commodity, GDP growth sensitivity
6. Peer valuation comparison: Where does this stock trade vs peers and why?
7. Market share trends: Gaining/losing/stable

Focus on structural sector dynamics, not short-term noise."""


# Ranking Synthesis Agent Prompt
RANKING_SYNTHESIS_PROMPT = """Synthesize all agent analyses into a final investment thesis for {symbol} ({company_name}).

ALL AGENT OUTPUTS:
- Fundamentals: {fundamentals_json}
- Technicals: {technicals_json}
- News/Sentiment: {news_json}
- Filings/Governance: {filings_json}
- Sector/Macro: {sector_json}
- Risk (Skeptic): {risk_json}
- Quantitative Scores: {scores_json}

COMPOSITE SCORE: {composite_score}/100
RANK: {rank} out of {total_stocks}

Create the final research output:
1. Investment Thesis: 2-3 paragraph narrative explaining the bull case based on EVIDENCE
2. Bull Case: 3-5 specific points with citations
3. Bear Case: 3-5 specific points with citations  
4. Key Catalysts: Near-term events that could drive re-rating
5. Major Risks: Top 3-5 risks with specific triggers
6. Thesis Invalidation Conditions: Specific measurable conditions that would break the thesis
7. Recommended Action: Research / Watch / Avoid
8. Monitoring Frequency: Weekly / Monthly / Quarterly
9. Confidence Level: High / Medium / Low

Ensure every qualitative claim traces back to a specific data point or agent output.
The thesis must be falsifiable - include specific invalidation conditions."""


# Agent prompt registry
AGENT_PROMPTS = {
    "news": NEWS_AGENT_PROMPT,
    "filings": FILINGS_AGENT_PROMPT,
    "risk": RISK_AGENT_PROMPT,
    "fundamentals": FUNDAMENTALS_AGENT_PROMPT,
    "technical": TECHNICAL_AGENT_PROMPT,
    "sector": SECTOR_AGENT_PROMPT,
    "ranking": RANKING_SYNTHESIS_PROMPT,
}

AGENT_FUNCTIONS = {
    "news": NEWS_ANALYSIS_FUNCTION,
    "filings": FILINGS_ANALYSIS_FUNCTION,
    "risk": RISK_ANALYSIS_FUNCTION,
    "fundamentals": FUNDAMENTAL_ANALYSIS_FUNCTION,
    "technical": TECHNICAL_ANALYSIS_FUNCTION,
    "sector": SECTOR_ANALYSIS_FUNCTION,
    "ranking": RANKING_SYNTHESIS_FUNCTION,
}

AGENT_OUTPUT_SCHEMAS = {
    "news": "NewsAnalysisOutput",
    "filings": "FilingsAnalysisOutput",
    "risk": "RiskAnalysisOutput",
    "fundamentals": "FundamentalAnalysisOutput",
    "technical": "TechnicalAnalysisOutput",
    "sector": "SectorAnalysisOutput",
    "ranking": "RankingSynthesisOutput",
}
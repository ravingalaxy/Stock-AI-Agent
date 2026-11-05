"""Pydantic schemas for structured LLM outputs."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class NewsSummary(BaseModel):
    """Single news article analysis."""
    title: str
    url: str
    publisher: str
    published_at: str
    summary: str
    sentiment: str = Field(description="Positive, Negative, or Neutral")
    sentiment_score: float = Field(ge=-1, le=1)
    events: List[str] = Field(default_factory=list)
    relevance_score: float = Field(ge=0, le=1)
    credibility: str = Field(description="High, Medium, Low")


class NewsAnalysisOutput(BaseModel):
    """Aggregated news analysis for a company."""
    company_symbol: str
    overall_sentiment: str
    avg_sentiment_score: float
    article_count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    key_themes: List[str]
    major_events: List[str]
    bullish_points: List[str]
    bearish_points: List[str]
    summaries: List[NewsSummary]
    latest_news_days_ago: int


class FilingsAnalysisOutput(BaseModel):
    """Corporate filings analysis."""
    company_symbol: str
    governance_concerns: List[str]
    promoter_pledge_change: Optional[str]
    promoter_holding_change: Optional[str]
    related_party_transactions: List[str]
    auditor_issues: List[str]
    key_events: List[str]
    risk_flags: List[str]


class RiskAnalysisOutput(BaseModel):
    """Risk Agent output - skeptical analysis."""
    company_symbol: str
    risk_level: str = Field(description="Low, Medium, High, Very High")
    risk_score: int = Field(ge=0, le=100)
    risk_factors: List[str]
    invalidation_conditions: List[str]
    bear_case: List[str]
    valuation_risk: str
    leverage_risk: str
    execution_risk: str
    governance_risk: str
    macro_risk: str


class FundamentalAnalysisOutput(BaseModel):
    """Fundamentals Agent qualitative output."""
    company_symbol: str
    quality_assessment: str
    growth_assessment: str
    key_strengths: List[str]
    key_weaknesses: List[str]
    accounting_quality: str
    red_flags: List[str]


class SectorAnalysisOutput(BaseModel):
    """Sector & Macro Agent output."""
    company_symbol: str
    sector: str
    relative_position: str = Field(description="Leader, Laggard, Turnaround, Peer")
    competitive_advantage: List[str]
    sector_tailwinds: List[str]
    sector_headwinds: List[str]
    macro_sensitivity: str
    peer_comparison: Dict[str, Any]


class RankingSynthesisOutput(BaseModel):
    """Final Ranking Agent synthesis."""
    company_symbol: str
    investment_thesis: str
    bull_case: List[str]
    bear_case: List[str]
    key_catalysts: List[str]
    major_risks: List[str]
    invalidation_conditions: List[str]
    recommended_action: str = Field(description="Research, Watch, Avoid")
    monitoring_frequency: str = Field(description="Weekly, Monthly, Quarterly")
    confidence_level: str = Field(description="High, Medium, Low")


class TechnicalAnalysisOutput(BaseModel):
    """Technical Agent qualitative output."""
    company_symbol: str
    trend_assessment: str
    momentum_assessment: str
    support_levels: List[float]
    resistance_levels: List[float]
    risk_reward: str
    timing_recommendation: str


# Function calling schemas for agents
NEWS_ANALYSIS_FUNCTION = {
    "name": "analyze_news",
    "description": "Analyze collected news articles for a company and extract structured insights",
    "parameters": NewsAnalysisOutput.model_json_schema()
}

FILINGS_ANALYSIS_FUNCTION = {
    "name": "analyze_filings",
    "description": "Analyze corporate filings and disclosures for governance and event signals",
    "parameters": FilingsAnalysisOutput.model_json_schema()
}

RISK_ANALYSIS_FUNCTION = {
    "name": "analyze_risk",
    "description": "Perform skeptical risk analysis identifying thesis invalidation conditions",
    "parameters": RiskAnalysisOutput.model_json_schema()
}

FUNDAMENTAL_ANALYSIS_FUNCTION = {
    "name": "analyze_fundamentals",
    "description": "Provide qualitative fundamental assessment",
    "parameters": FundamentalAnalysisOutput.model_json_schema()
}

SECTOR_ANALYSIS_FUNCTION = {
    "name": "analyze_sector",
    "description": "Analyze sector positioning and macro sensitivity",
    "parameters": SectorAnalysisOutput.model_json_schema()
}

RANKING_SYNTHESIS_FUNCTION = {
    "name": "synthesize_ranking",
    "description": "Synthesize all analyses into final investment thesis and ranking",
    "parameters": RankingSynthesisOutput.model_json_schema()
}

TECHNICAL_ANALYSIS_FUNCTION = {
    "name": "analyze_technicals",
    "description": "Provide qualitative technical analysis and timing assessment",
    "parameters": TechnicalAnalysisOutput.model_json_schema()
}
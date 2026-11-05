"""Deterministic Scoring Engine for Quality, Growth, Valuation, Momentum, Catalyst, and Risk."""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from src.utils.logger import logger
from src.utils.helpers import safe_divide
from src.config import get_config


@dataclass
class ScoreBreakdown:
    """Structured score breakdown."""
    quality: float = 0.0
    growth: float = 0.0
    valuation: float = 0.0
    momentum: float = 0.0
    catalyst: float = 0.0
    risk_penalty: float = 0.0
    composite: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "quality_score": round(self.quality, 1),
            "growth_score": round(self.growth, 1),
            "valuation_score": round(self.valuation, 1),
            "momentum_score": round(self.momentum, 1),
            "catalyst_score": round(self.catalyst, 1),
            "risk_score": round(self.risk_penalty, 1),
            "composite_score": round(self.composite, 1),
        }


class ScoringEngine:
    """Calculates all component scores deterministically from quantitative data."""
    
    def __init__(self):
        self.config = get_config()
        self.weights = self.config.scoring_weights
        
    def score_quality(self, ratios: Dict, red_flags: List[str]) -> float:
        """Score Quality 0-100 based on profitability, leverage, cash flow, governance."""
        score = 50  # Base
        
        # ROCE (25 pts max)
        roce = ratios.get("roce", 0)
        if roce > 25: score += 25
        elif roce > 20: score += 20
        elif roce > 15: score += 15
        elif roce > 10: score += 10
        elif roce > 5: score += 5
        
        # ROE (15 pts max)
        roe = ratios.get("roe", 0)
        if roe > 20: score += 15
        elif roe > 15: score += 12
        elif roe > 10: score += 8
        elif roe > 5: score += 4
        
        # Operating Margin (10 pts max)
        opm = ratios.get("operating_margin", 0)
        if opm > 20: score += 10
        elif opm > 15: score += 8
        elif opm > 10: score += 5
        elif opm > 5: score += 2
        
        # Debt-to-Equity (15 pts max) - Lower is better
        de = ratios.get("debt_to_equity", 99)
        if de < 0.3: score += 15
        elif de < 0.5: score += 12
        elif de < 1.0: score += 8
        elif de < 1.5: score += 4
        elif de < 2.0: score += 1
        
        # Interest Coverage (10 pts max)
        ic = ratios.get("interest_coverage", 0)
        if ic > 10: score += 10
        elif ic > 5: score += 7
        elif ic > 3: score += 4
        elif ic > 1.5: score += 1
        
        # FCF Quality (10 pts max)
        fcf_margin = ratios.get("fcf_margin", 0)
        cfo_ni = ratios.get("cfo_to_net_income", 0)
        if fcf_margin > 10 and cfo_ni > 1: score += 10
        elif fcf_margin > 5 and cfo_ni > 0.8: score += 7
        elif fcf_margin > 0 and cfo_ni > 0.5: score += 4
        elif fcf_margin > 0: score += 1
        
        # Promoter Holding Quality (10 pts max)
        promoter = ratios.get("promoter_holding_pct", 0)
        pledged = ratios.get("promoter_pledged_pct", 0)
        if promoter > 50 and pledged < 5: score += 10
        elif promoter > 40 and pledged < 10: score += 7
        elif promoter > 30 and pledged < 20: score += 4
        elif promoter > 20: score += 1
        
        # Red Flag Penalties
        penalty = min(len(red_flags) * 5, 25)  # Max 25 points penalty
        score -= penalty
        
        return max(0, min(100, score))
    
    def score_growth(self, growth_metrics: Dict, fundamental_history: List[Dict]) -> float:
        """Score Growth 0-100 based on revenue/profit CAGR and margin trends."""
        score = 30  # Base
        
        # Revenue CAGR (30 pts max)
        rev_cagr = growth_metrics.get("revenue_cagr", 0)
        if rev_cagr > 0.20: score += 30
        elif rev_cagr > 0.15: score += 25
        elif rev_cagr > 0.10: score += 18
        elif rev_cagr > 0.05: score += 10
        elif rev_cagr > 0: score += 5
        elif rev_cagr > -0.05: score += 0
        else: score -= 10
        
        # Profit CAGR (25 pts max)
        prof_cagr = growth_metrics.get("profit_cagr", 0)
        if prof_cagr > 0.25: score += 25
        elif prof_cagr > 0.15: score += 20
        elif prof_cagr > 0.10: score += 15
        elif prof_cagr > 0.05: score += 8
        elif prof_cagr > 0: score += 3
        else: score -= 5
        
        # Margin Expansion (15 pts max)
        latest_opm = growth_metrics.get("latest_operating_margin", 0)
        if len(fundamental_history) >= 3:
            old_opm = fundamental_history[-1].get("operating_margin", 0) if fundamental_history else 0
            margin_change = latest_opm - old_opm
            if margin_change > 5: score += 15
            elif margin_change > 2: score += 10
            elif margin_change > 0: score += 5
            elif margin_change < -3: score -= 5
            
        # ROE/ROCE Trend (15 pts max)
        latest_roe = growth_metrics.get("latest_roe", 0)
        if latest_roe > 20: score += 15
        elif latest_roe > 15: score += 10
        elif latest_roe > 10: score += 5
        
        # Consistency Bonus (10 pts max)
        if fundamental_history and len(fundamental_history) >= 4:
            profits = [f.get("net_profit", 0) for f in fundamental_history[:4] if f.get("net_profit")]
            if len(profits) == 4 and all(p > 0 for p in profits):
                # Check if growing
                if profits[0] > profits[3]:
                    score += 10
                else:
                    score += 5
                    
        return max(0, min(100, score))
    
    def score_momentum(self, tech_indicators: Dict, relative_strength: Dict) -> float:
        """Score Momentum 0-100 based on price action, RSI, MACD, relative strength."""
        score = 40  # Base
        
        # Trend Alignment (25 pts max)
        trend = tech_indicators.get("trend_sma", "Bearish")
        price_vs_50 = tech_indicators.get("price_vs_sma50", "Below")
        price_vs_200 = tech_indicators.get("price_vs_sma200", "Below")
        macd_sig = tech_indicators.get("macd_signal", "Bearish")
        
        trend_points = 0
        if trend == "Bullish": trend_points += 10
        if price_vs_50 == "Above": trend_points += 8
        if price_vs_200 == "Above": trend_points += 7
        if macd_sig == "Bullish": trend_points += 5
        score += trend_points
        
        # RSI (15 pts max) - Prefer 50-70 range for uptrend
        rsi = tech_indicators.get("RSI_14", 50)
        if 50 <= rsi <= 70: score += 15
        elif 40 <= rsi < 50: score += 10
        elif 70 < rsi <= 80: score += 8
        elif 30 <= rsi < 40: score += 3
        elif rsi > 80: score += 0  # Overbought
        else: score -= 5  # Oversold
        
        # Price Momentum (20 pts max)
        mom_20 = tech_indicators.get("momentum_20d", 0)
        mom_60 = tech_indicators.get("momentum_60d", 0)
        mom_252 = tech_indicators.get("momentum_252d", 0)
        
        mom_score = 0
        if mom_20 > 5: mom_score += 8
        elif mom_20 > 0: mom_score += 4
        elif mom_20 < -5: mom_score -= 5
        
        if mom_60 > 15: mom_score += 7
        elif mom_60 > 5: mom_score += 4
        elif mom_60 < -10: mom_score -= 5
        
        if mom_252 > 20: mom_score += 5
        elif mom_252 < 0: mom_score -= 3
        
        score += mom_score
        
        # Relative Strength vs Benchmark (20 pts max)
        rs_60 = relative_strength.get("RS_60d", 0)
        rs_120 = relative_strength.get("RS_120d", 0)
        rs_252 = relative_strength.get("RS_252d", 0)
        
        rs_score = 0
        if rs_60 > 0.05: rs_score += 8
        elif rs_60 > 0: rs_score += 4
        elif rs_60 < -0.05: rs_score -= 5
        
        if rs_120 > 0.10: rs_score += 7
        elif rs_120 > 0: rs_score += 3
        
        if rs_252 > 0.15: rs_score += 5
        elif rs_252 > 0: rs_score += 2
        
        score += rs_score
        
        # Volume Confirmation (10 pts max)
        vol_ratio = tech_indicators.get("Volume_Ratio", 1)
        if vol_ratio > 1.5: score += 10
        elif vol_ratio > 1.2: score += 6
        elif vol_ratio > 1.0: score += 3
        elif vol_ratio < 0.7: score -= 3
        
        return max(0, min(100, score))
    
    def score_catalyst(self, news_analysis: Dict, filings_analysis: Dict) -> float:
        """Score Catalyst 0-100 based on news sentiment, events, and corporate actions."""
        score = 30  # Base
        
        # News Sentiment (40 pts max)
        sentiment = news_analysis.get("avg_sentiment", 0)
        article_count = news_analysis.get("article_count", 0)
        positive_count = news_analysis.get("positive_count", 0)
        negative_count = news_analysis.get("negative_count", 0)
        
        if article_count > 0:
            pos_ratio = positive_count / article_count
            neg_ratio = negative_count / article_count
            
            if sentiment > 0.3 and pos_ratio > 0.6: score += 40
            elif sentiment > 0.1 and pos_ratio > 0.5: score += 25
            elif sentiment > 0: score += 15
            elif sentiment < -0.2: score -= 10
            elif sentiment < -0.4: score -= 20
            
        # Event Types (30 pts max)
        events = news_analysis.get("events_detected", [])
        event_scores = {
            "earnings": 5,
            "order": 10,
            "expansion": 8,
            "acquisition": 5,
            "dividend": 5,
            "buyback": 5,
            "management_change": 3,
        }
        for ev in events:
            score += event_scores.get(ev, 0)
            
        # Filings Catalysts (20 pts max)
        filing_events = filings_analysis.get("key_events", [])
        if "strong_results" in filing_events: score += 15
        elif "results" in filing_events: score += 8
        if "dividend_announced" in filing_events: score += 10
        if "buyback_announced" in filing_events: score += 8
        if "capex_announced" in filing_events: score += 10
        if "promoter_buying" in filing_events: score += 10
        if "pledge_reduction" in filing_events: score += 8
        if "promoter_pledge_increase" in filing_events: score -= 10
        if "auditor_qualification" in filing_events: score -= 15
        if "related_party_concern" in filing_events: score -= 10
        
        # Recency Bonus (10 pts max)
        latest_news_days = news_analysis.get("latest_news_days_ago", 999)
        if latest_news_days <= 3: score += 10
        elif latest_news_days <= 7: score += 6
        elif latest_news_days <= 14: score += 3
        
        return max(0, min(100, score))
    
    def calculate_risk_penalty(
        self, 
        ratios: Dict, 
        red_flags: List[str], 
        risk_agent_output: Dict,
        governance_flags: List[str]
    ) -> Tuple[float, str]:
        """Calculate Risk Penalty 0-100 (higher = riskier) and Risk Level."""
        penalty = 0
        
        # Leverage Risk
        de = ratios.get("debt_to_equity", 0)
        if de > 2.0: penalty += 25
        elif de > 1.5: penalty += 15
        elif de > 1.0: penalty += 8
        elif de > 0.5: penalty += 3
        
        ic = ratios.get("interest_coverage", 99)
        if ic < 1.5: penalty += 20
        elif ic < 3: penalty += 12
        elif ic < 5: penalty += 5
        
        # Promoter Pledge Risk
        pledged = ratios.get("promoter_pledged_pct", 0)
        if pledged > 30: penalty += 25
        elif pledged > 20: penalty += 15
        elif pledged > 10: penalty += 8
        elif pledged > 5: penalty += 3
        
        # Profitability Risk
        roce = ratios.get("roce", 0)
        if roce < 5: penalty += 15
        elif roce < 10: penalty += 8
        elif roce < 15: penalty += 3
        
        # Cash Flow Risk
        fcf = ratios.get("fcf", 0)
        cfo_ni = ratios.get("cfo_to_net_income", 1)
        if fcf < 0 and cfo_ni < 0.5: penalty += 15
        elif fcf < 0: penalty += 8
        elif cfo_ni < 0.5: penalty += 5
        
        # Red Flags from Fundamentals
        penalty += min(len(red_flags) * 4, 20)
        
        # Governance Flags from Filings
        penalty += min(len(governance_flags) * 6, 25)
        
        # Risk Agent Qualitative Assessment
        risk_level = risk_agent_output.get("risk_level", "Medium")
        risk_factors = risk_agent_output.get("risk_factors", [])
        risk_score = risk_agent_output.get("risk_score", 50)
        
        # Incorporate AI risk score (scaled)
        penalty += (risk_score / 100) * 20
        
        penalty = max(0, min(100, penalty))
        
        # Determine Risk Level Label
        if penalty >= 70: level = "Very High"
        elif penalty >= 50: level = "High"
        elif penalty >= 30: level = "Medium"
        else: level = "Low"
        
        return penalty, level
    
    def calculate_composite(self, components: Dict[str, float]) -> ScoreBreakdown:
        """Calculate final composite score from components."""
        breakdown = ScoreBreakdown(
            quality=components.get("quality", 0),
            growth=components.get("growth", 0),
            valuation=components.get("valuation", 0),
            momentum=components.get("momentum", 0),
            catalyst=components.get("catalyst", 0),
            risk_penalty=components.get("risk_penalty", 0)
        )
        
        # Apply weights
        w = self.weights
        breakdown.composite = (
            breakdown.quality * w.quality +
            breakdown.growth * w.growth +
            breakdown.valuation * w.valuation +
            breakdown.momentum * w.momentum +
            breakdown.catalyst * w.catalyst -
            breakdown.risk_penalty * w.risk_penalty
        )
        
        breakdown.composite = max(0, min(100, breakdown.composite))
        return breakdown


# Convenience function
def score_stock(
    ratios: Dict,
    growth_metrics: Dict,
    fundamental_history: List,
    tech_indicators: Dict,
    relative_strength: Dict,
    news_analysis: Dict,
    filings_analysis: Dict,
    risk_agent_output: Dict,
    governance_flags: List[str]
) -> ScoreBreakdown:
    """One-call scoring function."""
    engine = ScoringEngine()
    
    quality = engine.score_quality(ratios, [])
    growth = engine.score_growth(growth_metrics, fundamental_history)
    valuation = 50  # Will be overridden by valuation engine
    momentum = engine.score_momentum(tech_indicators, relative_strength)
    catalyst = engine.score_catalyst(news_analysis, filings_analysis)
    risk_penalty, risk_level = engine.calculate_risk_penalty(ratios, [], risk_agent_output, governance_flags)
    
    components = {
        "quality": quality,
        "growth": growth,
        "valuation": valuation,
        "momentum": momentum,
        "catalyst": catalyst,
        "risk_penalty": risk_penalty
    }
    
    return engine.calculate_composite(components)
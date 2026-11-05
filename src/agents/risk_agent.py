"""Risk Agent - The Skeptical Analyst identifying thesis failure conditions."""

import json
from typing import Dict, Any, List
from datetime import date

from src.utils.logger import logger
from src.llm.llm_client import get_llm_client
from src.llm.prompts import FINANCIAL_ANALYST_SYSTEM, RISK_AGENT_PROMPT
from src.llm.schemas import RiskAnalysisOutput
from src.storage.database import StockRepository


class RiskAgent:
    """Plays devil's advocate - identifies why the bullish thesis might fail."""
    
    def __init__(self, repo: StockRepository):
        self.repo = repo
        self.llm = get_llm_client()
        
    def analyze(
        self, 
        symbol: str,
        quality_score: float,
        growth_score: float,
        valuation_score: float,
        momentum_score: float,
        ratios: Dict[str, Any],
        red_flags: List[str],
        governance_flags: List[str],
        news_sentiment: float
    ) -> Dict[str, Any]:
        """Run skeptical risk analysis."""
        logger.info(f"Running risk analysis for {symbol}")
        
        stock = self.repo.get_stock(symbol)
        company_name = stock.name if stock else symbol
        
        try:
            prompt = RISK_AGENT_PROMPT.format(
                symbol=symbol,
                company_name=company_name,
                quality_score=quality_score,
                growth_score=growth_score,
                valuation_score=valuation_score,
                momentum_score=momentum_score,
                ratios_json=json.dumps(ratios, indent=2, default=str),
                red_flags=json.dumps(red_flags, indent=2),
                governance_flags=json.dumps(governance_flags, indent=2),
                news_sentiment=f"{news_sentiment:.2f}"
            )
            
            messages = [
                {"role": "system", "content": FINANCIAL_ANALYST_SYSTEM},
                {"role": "user", "content": prompt}
            ]
            
            result = self.llm.chat_structured(
                messages=messages,
                response_model=RiskAnalysisOutput
            )
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"LLM risk analysis failed for {symbol}: {e}")
            return self._fallback_risk_analysis(symbol, ratios, red_flags, governance_flags)
    
    def _fallback_risk_analysis(
        self, 
        symbol: str, 
        ratios: Dict, 
        red_flags: List[str], 
        governance_flags: List[str]
    ) -> Dict[str, Any]:
        """Deterministic fallback risk analysis when LLM fails."""
        risk_factors = []
        invalidation = []
        bear_case = []
        
        # Valuation Risk
        pe = ratios.get("pe_ratio", 0)
        if pe > 40:
            risk_factors.append(f"Very high P/E ({pe:.1f}x) - priced for perfection")
            invalidation.append(f"P/E compresses below 30x without earnings catch-up")
            bear_case.append("Valuation multiple contraction risk")
        elif pe > 25:
            risk_factors.append(f"Elevated P/E ({pe:.1f}x) limits upside")
            
        # Leverage Risk
        de = ratios.get("debt_to_equity", 0)
        if de > 1.5:
            risk_factors.append(f"High leverage (D/E: {de:.2f}) - refinancing and interest rate risk")
            invalidation.append(f"Interest coverage falls below 2x or debt maturity wall hits")
            bear_case.append("Balance sheet stress in rising rate environment")
        elif de > 1.0:
            risk_factors.append(f"Moderate leverage (D/E: {de:.2f})")
            
        ic = ratios.get("interest_coverage", 0)
        if ic < 3:
            risk_factors.append(f"Low interest coverage ({ic:.1f}x) - cash flow vulnerability")
            invalidation.append("Operating profit declines 20%+ leading to coverage < 1.5x")
            
        # Promoter Pledge Risk
        pledged = ratios.get("promoter_pledged_pct", 0)
        if pledged > 20:
            risk_factors.append(f"Very high promoter pledge ({pledged:.1f}%) - margin call risk")
            invalidation.append("Promoter pledge increases further or margin calls trigger forced selling")
            bear_case.append("Promoter share pledge risk")
        elif pledged > 10:
            risk_factors.append(f"Elevated promoter pledge ({pledged:.1f}%)")
            
        # Profitability Risk
        roce = ratios.get("roce", 0)
        if roce < 10:
            risk_factors.append(f"Low ROCE ({roce:.1f}%) - capital allocation concerns")
            bear_case.append("Sub-par capital efficiency")
            
        # Cash Flow Risk
        fcf = ratios.get("fcf", 0)
        cfo_ni = ratios.get("cfo_to_net_income", 1)
        if fcf < 0:
            risk_factors.append("Negative free cash flow - funding gap risk")
            invalidation.append("FCF remains negative for 2+ consecutive quarters")
        if cfo_ni < 0.5:
            risk_factors.append(f"Poor cash conversion (CFO/Net Income: {cfo_ni:.2f})")
            
        # Red flags
        for flag in red_flags:
            risk_factors.append(f"Accounting flag: {flag}")
            
        # Governance flags
        for flag in governance_flags:
            risk_factors.append(f"Governance concern: {flag}")
            
        # Determine risk level
        risk_score = min(len(risk_factors) * 8 + len(governance_flags) * 10, 100)
        if risk_score >= 70: level = "Very High"
        elif risk_score >= 50: level = "High"
        elif risk_score >= 30: level = "Medium"
        else: level = "Low"
        
        # Ensure minimum 3 invalidation conditions
        if len(invalidation) < 3:
            invalidation.extend([
                "Revenue growth decelerates below 5% for 2+ quarters",
                "Operating margins contract by >300bps YoY",
                "Promoter holding falls below 30% or pledge increases >5%"
            ])
            
        return {
            "company_symbol": symbol,
            "risk_level": level,
            "risk_score": risk_score,
            "risk_factors": risk_factors[:10],  # Top 10
            "invalidation_conditions": invalidation[:5],
            "bear_case": bear_case[:5],
            "valuation_risk": "High" if pe > 30 else "Medium" if pe > 20 else "Low",
            "leverage_risk": "High" if de > 1.5 else "Medium" if de > 1.0 else "Low",
            "execution_risk": "Medium",
            "governance_risk": "High" if governance_flags else "Low",
            "macro_risk": "Medium"
        }
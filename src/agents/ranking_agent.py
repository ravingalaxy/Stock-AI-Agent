"""Comparison & Ranking Agent - Synthesizes all analyses into final ranked watchlist."""

import json
from typing import Dict, Any, List, Optional
from datetime import date

from src.utils.logger import logger
from src.analysis.scoring import ScoringEngine, ScoreBreakdown
from src.llm.llm_client import get_llm_client
from src.llm.prompts import FINANCIAL_ANALYST_SYSTEM, RANKING_SYNTHESIS_PROMPT
from src.llm.schemas import RankingSynthesisOutput
from src.storage.database import StockRepository, AgentEvaluation


class RankingAgent:
    """Combines all agent outputs into transparent composite scores and ranked watchlist."""
    
    def __init__(self, repo: StockRepository):
        self.repo = repo
        self.scoring_engine = ScoringEngine()
        self.llm = get_llm_client()
        
    def rank_universe(
        self, 
        symbols: List[str],
        agent_outputs: Dict[str, Dict[str, Any]],
        top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """Rank a universe of stocks based on all agent analyses."""
        logger.info(f"Ranking {len(symbols)} stocks...")
        
        ranked = []
        
        for symbol in symbols:
            try:
                outputs = agent_outputs.get(symbol, {})
                if not outputs:
                    logger.warning(f"No agent outputs for {symbol}")
                    continue
                    
                # Calculate deterministic scores
                score_breakdown = self._calculate_scores(symbol, outputs)
                
                # Skip if composite too low or critical flags
                if score_breakdown.composite < 30:
                    logger.debug(f"{symbol} below threshold: {score_breakdown.composite:.1f}")
                    continue
                    
                # Check for hard rejection criteria
                if self._should_reject(symbol, outputs, score_breakdown):
                    logger.debug(f"{symbol} rejected due to hard criteria")
                    continue
                    
                # LLM Synthesis for top candidates
                synthesis = self._run_synthesis(symbol, outputs, score_breakdown)
                
                # Build final result
                result = self._build_result(symbol, outputs, score_breakdown, synthesis)
                ranked.append(result)
                
            except Exception as e:
                logger.error(f"Ranking failed for {symbol}: {e}")
                continue
                
        # Sort by composite score descending
        ranked.sort(key=lambda x: x["composite_score"], reverse=True)
        
        # Assign ranks
        for i, r in enumerate(ranked):
            r["rank"] = i + 1
            
        # Save to database
        self._save_evaluations(ranked)
        
        return ranked[:top_n]
    
    def _calculate_scores(self, symbol: str, outputs: Dict) -> ScoreBreakdown:
        """Calculate all component scores deterministically."""
        
        # Extract data from agent outputs
        fund_out = outputs.get("fundamentals", {})
        tech_out = outputs.get("technical", {})
        news_out = outputs.get("news", {})
        filings_out = outputs.get("filings", {})
        risk_out = outputs.get("risk", {})
        
        ratios = fund_out.get("ratios", {})
        growth_metrics = fund_out.get("growth_metrics", {})
        fund_history = [fund_out.get("fundamental_data", {})]  # Simplified
        tech_indicators = tech_out.get("indicators", {})
        relative_strength = tech_out.get("relative_strength", {})
        news_agg = news_out.get("aggregate_metrics", {})
        filings_flags = filings_out.get("structured_flags", {})
        governance_flags = filings_flags.get("governance_red_flags", [])
        red_flags = fund_out.get("red_flags", [])
        
        # Valuation score (from valuation engine or simplified)
        val_score = 50
        peer_comp = fund_out.get("peer_comparison", {})
        if peer_comp and "error" not in peer_comp:
            # Score based on relative valuation
            discounts = [v.get("discount_to_median_pct", 0) for v in peer_comp.values() if isinstance(v, dict)]
            if discounts:
                avg_discount = sum(discounts) / len(discounts)
                val_score = max(0, min(100, 50 + avg_discount))  # Discount = good
        
        # Calculate components
        quality = self.scoring_engine.score_quality(ratios, red_flags)
        growth = self.scoring_engine.score_growth(growth_metrics, fund_history)
        valuation = val_score
        momentum = self.scoring_engine.score_momentum(tech_indicators, relative_strength)
        catalyst = self.scoring_engine.score_catalyst(news_agg, filings_flags)
        risk_penalty, risk_level = self.scoring_engine.calculate_risk_penalty(
            ratios, red_flags, risk_out, governance_flags
        )
        
        components = {
            "quality": quality,
            "growth": growth,
            "valuation": valuation,
            "momentum": momentum,
            "catalyst": catalyst,
            "risk_penalty": risk_penalty
        }
        
        return self.scoring_engine.calculate_composite(components)
    
    def _should_reject(self, symbol: str, outputs: Dict, scores: ScoreBreakdown) -> bool:
        """Check hard rejection criteria."""
        fund_out = outputs.get("fundamentals", {})
        filings_out = outputs.get("filings", {})
        risk_out = outputs.get("risk", {})
        
        # Reject if governance very high risk
        if risk_out.get("risk_level") == "Very High":
            return True
            
        # Reject if promoter pledge > 50%
        filings_flags = filings_out.get("structured_flags", {})
        pledged = filings_flags.get("promoter_pledged_pct")
        if pledged and pledged > 50:
            return True
            
        # Reject if negative equity
        ratios = fund_out.get("ratios", {})
        # Would need total_equity from fundamentals
        
        # Reject if auditor qualification
        gov_flags = filings_flags.get("governance_red_flags", [])
        if any("auditor" in f.lower() for f in gov_flags):
            return True
            
        # Reject if composite too low
        if scores.composite < 25:
            return True
            
        return False
    
    def _run_synthesis(
        self, 
        symbol: str, 
        outputs: Dict, 
        scores: ScoreBreakdown
    ) -> Dict[str, Any]:
        """Run LLM synthesis for final thesis."""
        try:
            stock = self.repo.get_stock(symbol)
            company_name = stock.name if stock else symbol
            
            prompt = RANKING_SYNTHESIS_PROMPT.format(
                symbol=symbol,
                company_name=company_name,
                fundamentals_json=json.dumps(outputs.get("fundamentals", {}).get("qualitative_analysis", {}), indent=2, default=str),
                technicals_json=json.dumps(outputs.get("technical", {}).get("qualitative_analysis", {}), indent=2, default=str),
                news_json=json.dumps(outputs.get("news", {}).get("qualitative_analysis", {}), indent=2, default=str),
                filings_json=json.dumps(outputs.get("filings", {}).get("qualitative_analysis", {}), indent=2, default=str),
                sector_json=json.dumps(outputs.get("sector", {}).get("qualitative_analysis", {}), indent=2, default=str),
                risk_json=json.dumps(outputs.get("risk", {}), indent=2, default=str),
                scores_json=json.dumps(scores.to_dict(), indent=2),
                composite_score=scores.composite,
                rank=0,  # Will be assigned after sorting
                total_stocks=0
            )
            
            messages = [
                {"role": "system", "content": FINANCIAL_ANALYST_SYSTEM},
                {"role": "user", "content": prompt}
            ]
            
            result = self.llm.chat_structured(
                messages=messages,
                response_model=RankingSynthesisOutput
            )
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"LLM synthesis failed for {symbol}: {e}")
            return self._fallback_synthesis(symbol, scores)
    
    def _fallback_synthesis(self, symbol: str, scores: ScoreBreakdown) -> Dict[str, Any]:
        """Deterministic fallback synthesis based on quantitative scores."""
        action = "Research" if scores.composite > 60 else "Watch" if scores.composite > 40 else "Avoid"
        
        # Generate contextual bull/bear cases based on component scores
        bull_points = []
        if scores.quality >= 70:
            bull_points.append(f"High quality business (Quality: {scores.quality:.0f}/100) with strong profitability and clean financials")
        elif scores.quality >= 50:
            bull_points.append(f"Decent quality metrics (Quality: {scores.quality:.0f}/100)")
        if scores.growth >= 60:
            bull_points.append(f"Growth momentum present (Growth: {scores.growth:.0f}/100)")
        if scores.valuation >= 60:
            bull_points.append(f"Attractive valuation (Valuation: {scores.valuation:.0f}/100) - potential margin of safety")
        if scores.momentum >= 60:
            bull_points.append(f"Positive price momentum (Momentum: {scores.momentum:.0f}/100)")
        if scores.catalyst >= 55:
            bull_points.append(f"Positive catalysts emerging (Catalyst: {scores.catalyst:.0f}/100)")
        if scores.risk_penalty <= 30:
            bull_points.append("Low risk profile with minimal leverage and governance concerns")
        if not bull_points:
            bull_points.append("Moderate quantitative profile - suitable for further research")
        
        bear_points = []
        if scores.quality < 40:
            bear_points.append(f"Quality concerns (Quality: {scores.quality:.0f}/100) - weak profitability or leverage")
        if scores.growth < 35:
            bear_points.append(f"Growth stagnation (Growth: {scores.growth:.0f}/100)")
        if scores.valuation < 40:
            bear_points.append(f"Rich valuation (Valuation: {scores.valuation:.0f}/100) - limited margin of safety")
        if scores.momentum < 40:
            bear_points.append(f"Negative price momentum (Momentum: {scores.momentum:.0f}/100)")
        if scores.risk_penalty > 50:
            bear_points.append(f"Elevated risk (Risk Penalty: {scores.risk_penalty:.0f}/100) - leverage, governance, or red flags")
        if scores.catalyst < 35:
            bear_points.append("Lack of near-term catalysts for re-rating")
        if not bear_points:
            bear_points.append("Standard market risks apply")
        
        # Contextual catalysts
        catalysts = []
        if scores.growth >= 55:
            catalysts.append("Earnings growth momentum could drive re-rating")
        if scores.catalyst >= 50:
            catalysts.append("Positive news flow or corporate actions")
        if scores.momentum >= 55:
            catalysts.append("Technical breakout potential")
        if scores.quality >= 65 and scores.valuation >= 55:
            catalysts.append("Quality compounder at reasonable valuation")
        catalysts.extend(["Sector tailwinds", "Operational leverage on revenue growth"])
        
        # Contextual risks
        risks = []
        if scores.quality < 50:
            risks.append("Deteriorating fundamentals could trigger de-rating")
        if scores.valuation < 45:
            risks.append("Valuation leaves no room for execution slip-ups")
        if scores.momentum < 45:
            risks.append("Downtrend could persist without catalyst")
        if scores.risk_penalty > 40:
            risks.append("Balance sheet or governance concerns")
        risks.extend(["Macro economic slowdown", "Sector rotation risk", "Regulatory/policy changes"])
        
        # Contextual invalidation
        invalidation = []
        if scores.growth >= 50:
            invalidation.append(f"Revenue growth deceleration below {scores.growth * 0.5:.0f}% YoY")
        if scores.quality >= 60:
            invalidation.append("ROE/ROCE declining below 15%")
        if scores.risk_penalty > 30:
            invalidation.append("Debt/equity rising above 1.0 or promoter pledge increasing")
        invalidation.extend(["Earnings miss > 15%", "Margin compression > 300bps", "Key personnel departure"])
        
        thesis = (
            f"Quantitative Analysis: {symbol} scores {scores.composite:.1f}/100 composite. "
            f"Strengths: {', '.join([b for b in bull_points[:2]])}. "
            f"Concerns: {', '.join([b for b in bear_points[:2]])}. "
            f"Recommended: {action}. "
            f"Note: Generated via deterministic fallback (LLM unavailable)."
        )
        
        return {
            "investment_thesis": thesis,
            "bull_case": bull_points,
            "bear_case": bear_points,
            "key_catalysts": catalysts[:4],
            "major_risks": risks[:4],
            "invalidation_conditions": invalidation[:4],
            "recommended_action": action,
            "monitoring_frequency": "Monthly",
            "confidence_level": "Low (Fallback Mode)"
        }
    
    def _build_result(
        self, 
        symbol: str, 
        outputs: Dict, 
        scores: ScoreBreakdown,
        synthesis: Dict
    ) -> Dict[str, Any]:
        """Build final result dictionary."""
        stock = self.repo.get_stock(symbol)
        
        # Format market cap
        mcap = stock.market_cap if stock and stock.market_cap else 0
        if mcap >= 10_000_000_000:  # 1000 Cr
            mcap_str = f"₹{mcap / 10_000_000:.0f} Cr"
        elif mcap >= 10_000_000:
            mcap_str = f"₹{mcap / 10_000_000:.1f} Cr"
        else:
            mcap_str = f"₹{mcap / 10_000_000:.2f} Cr"
            
        # Liquidity assessment
        fund_out = outputs.get("fundamentals", {})
        ratios = fund_out.get("ratios", {})
        
        # Extract current price from technical indicators
        tech_indicators = outputs.get("technical", {}).get("indicators", {})
        current_price = tech_indicators.get("current_price", 0.0)
        
        return {
            "symbol": symbol,
            "name": stock.name if stock else symbol,
            "sector": stock.sector if stock else "Unknown",
            "market_cap": mcap,
            "market_cap_str": mcap_str,
            "current_price": current_price,
            "liquidity": "High",  # Simplified
            "composite_score": round(scores.composite, 1),
            "quality_score": round(scores.quality, 1),
            "growth_score": round(scores.growth, 1),
            "valuation_score": round(scores.valuation, 1),
            "momentum_score": round(scores.momentum, 1),
            "catalyst_score": round(scores.catalyst, 1),
            "risk_score": round(scores.risk_penalty, 1),
            "thesis": synthesis.get("investment_thesis", ""),
            "bull_case": synthesis.get("bull_case", []),
            "bear_case": synthesis.get("bear_case", []),
            "catalysts": synthesis.get("key_catalysts", []),
            "risks": synthesis.get("major_risks", []),
            "invalidation_conditions": synthesis.get("invalidation_conditions", []),
            "recommended_action": synthesis.get("recommended_action", "Research"),
            "monitoring_frequency": synthesis.get("monitoring_frequency", "Monthly"),
            "confidence_level": synthesis.get("confidence_level", "Medium"),
            "risk_level": outputs.get("risk", {}).get("risk_level", "Medium"),
            "citations": self._extract_citations(outputs),
            "analyzed_at": date.today().isoformat()
        }
    
    def _extract_citations(self, outputs: Dict) -> List[Dict]:
        """Extract source citations from agent outputs."""
        citations = []
        
        # News citations
        news_articles = outputs.get("news", {}).get("articles", [])
        for art in news_articles[:5]:
            citations.append({
                "title": art.get("title", ""),
                "url": art.get("url", ""),
                "date": art.get("published_at", "").isoformat() if hasattr(art.get("published_at"), "isoformat") else str(art.get("published_at", "")),
                "source_type": "news"
            })
            
        # Filings citations
        filings_ann = outputs.get("filings", {}).get("categorized", {})
        for cat, anns in filings_ann.items():
            for ann in anns[:2]:
                citations.append({
                    "title": ann.get("subject", ""),
                    "url": ann.get("attachment_url", ""),
                    "date": ann.get("published_at", "").isoformat() if hasattr(ann.get("published_at"), "isoformat") else str(ann.get("published_at", "")),
                    "source_type": "filing"
                })
                
        return citations[:10]
    
    def _save_evaluations(self, ranked: List[Dict]):
        """Save evaluations to database."""
        eval_date = date.today()
        for r in ranked:
            try:
                self.repo.save_evaluation({
                    "symbol": r["symbol"],
                    "evaluation_date": eval_date,
                    "composite_score": r["composite_score"],
                    "quality_score": r["quality_score"],
                    "growth_score": r["growth_score"],
                    "valuation_score": r["valuation_score"],
                    "momentum_score": r["momentum_score"],
                    "catalyst_score": r["catalyst_score"],
                    "risk_score": r["risk_score"],
                    "rank": r["rank"],
                    "thesis": r["thesis"],
                    "bull_case": json.dumps(r["bull_case"]),
                    "bear_case": json.dumps(r["bear_case"]),
                    "catalysts": json.dumps(r["catalysts"]),
                    "risks": json.dumps(r["risks"]),
                    "invalidation_conditions": json.dumps(r["invalidation_conditions"]),
                    "citations": json.dumps(r["citations"]),
                })
            except Exception as e:
                logger.error(f"Failed to save evaluation for {r['symbol']}: {e}")

        # Synchronize automatically with Django database if available
        try:
            import os
            import django
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_agent_django.settings')
            django.setup()
            from apps.market.services import sync_evaluations_to_django_from_data
            sync_evaluations_to_django_from_data(ranked, eval_date)
        except Exception as e:
            logger.debug(f"Direct Django sync during ranking: {e}")
"""Sector & Macro Agent - Peer comparison and macro sensitivity analysis."""

import json
from typing import Dict, Any, List, Optional
from datetime import date

from src.utils.logger import logger
from src.storage.database import StockRepository
from src.analysis.valuation import ValuationEngine
from src.llm.llm_client import get_llm_client
from src.llm.prompts import FINANCIAL_ANALYST_SYSTEM, SECTOR_AGENT_PROMPT
from src.llm.schemas import SectorAnalysisOutput


class SectorAgent:
    """Analyzes sector positioning, peer comparison, and macro sensitivity."""
    
    def __init__(self, repo: StockRepository):
        self.repo = repo
        self.val_engine = ValuationEngine(repo)
        self.llm = get_llm_client()
        
    def analyze(self, symbol: str) -> Dict[str, Any]:
        """Run complete sector analysis."""
        logger.info(f"Running sector analysis for {symbol}")
        
        # 1. Get company info
        stock = self.repo.get_stock(symbol)
        if not stock or not stock.sector:
            return self._empty_result(symbol, "No sector info")
            
        company_name = stock.name
        sector = stock.sector
        
        # 2. Get peer valuation stats
        peer_stats = self.val_engine.get_peer_valuation_stats(symbol, sector)
        
        # 3. Get peer fundamentals for comparison
        peers = self.val_engine.get_sector_peers(symbol, sector)
        peer_fundamentals = []
        for peer in peers[:10]:
            fund = self.repo.get_latest_fundamentals(peer)
            peer_stock = self.repo.get_stock(peer)
            if fund and peer_stock:
                peer_fundamentals.append({
                    "symbol": peer,
                    "name": peer_stock.name if peer_stock else peer,
                    "market_cap": peer_stock.market_cap,
                    "pe_ratio": fund.pe_ratio,
                    "pb_ratio": fund.pb_ratio,
                    "ev_ebitda": fund.ev_ebitda,
                    "roe": fund.roe,
                    "roce": fund.roce,
                    "debt_to_equity": fund.debt_to_equity,
                    "revenue_growth": fund.revenue,  # Would need history for growth
                })
                
        # 4. Company fundamentals
        fund = self.repo.get_latest_fundamentals(symbol)
        company_stock = self.repo.get_stock(symbol)
        company_data = {}
        if fund and company_stock:
            company_data = {
                "symbol": symbol,
                "name": company_name,
                "market_cap": company_stock.market_cap,
                "pe_ratio": fund.pe_ratio,
                "pb_ratio": fund.pb_ratio,
                "ev_ebitda": fund.ev_ebitda,
                "roe": fund.roe,
                "roce": fund.roce,
                "debt_to_equity": fund.debt_to_equity,
                "operating_margin": fund.operating_margin,
                "net_margin": fund.net_margin,
            }
            
        # 5. Macro indicators (simplified)
        macro_data = self._get_macro_context(sector)
        
        # 6. LLM Qualitative Analysis
        qualitative = self._run_llm_analysis(
            symbol, company_name, sector, peer_fundamentals, 
            macro_data, company_data, peer_stats
        )
        
        return {
            "symbol": symbol,
            "sector": sector,
            "peer_count": len(peer_fundamentals),
            "peer_valuation_stats": peer_stats,
            "company_valuation": company_data,
            "macro_context": macro_data,
            "qualitative_analysis": qualitative,
            "analyzed_at": date.today().isoformat()
        }
    
    def _get_macro_context(self, sector: str) -> Dict[str, Any]:
        """Get relevant macro indicators for sector."""
        # In production, fetch from economic data APIs
        # This is a placeholder structure
        sector_macro_map = {
            "Financial Services": ["Interest Rates", "Credit Growth", "NPA Cycle", "GDP Growth"],
            "Information Technology": ["USD/INR", "US Tech Spending", "Global GDP", "Visa Policy"],
            "Consumer Goods": ["Rural Income", "CPI Inflation", "Commodity Prices", "Monsoon"],
            "Automobile": ["Interest Rates", "Fuel Prices", "Income Growth", "EV Policy"],
            "Pharmaceuticals": ["USD/INR", "FDA Inspections", "Drug Pricing Policy", "R&D Spend"],
            "Metals & Mining": ["Global Commodity Prices", "China Demand", "USD/INR", "Infrastructure Spend"],
            "Energy": ["Crude Oil Price", "Gas Price", "Government Policy", "Green Energy Transition"],
        }
        
        return {
            "sector": sector,
            "key_macro_drivers": sector_macro_map.get(sector, ["GDP Growth", "Interest Rates", "Inflation", "Currency"]),
            "current_cycle": "Expansion",  # Would be determined from actual data
        }
    
    def _run_llm_analysis(
        self, 
        symbol: str, 
        company_name: str,
        sector: str,
        peer_data: List[Dict],
        macro_data: Dict,
        company_data: Dict,
        peer_stats: Dict
    ) -> Dict[str, Any]:
        """Run LLM qualitative sector analysis."""
        try:
            prompt = SECTOR_AGENT_PROMPT.format(
                symbol=symbol,
                company_name=company_name,
                sector=sector,
                peer_data_json=json.dumps(peer_data, indent=2, default=str),
                macro_json=json.dumps(macro_data, indent=2, default=str),
                company_json=json.dumps(company_data, indent=2, default=str)
            )
            
            messages = [
                {"role": "system", "content": FINANCIAL_ANALYST_SYSTEM},
                {"role": "user", "content": prompt}
            ]
            
            result = self.llm.chat_structured(
                messages=messages,
                response_model=SectorAnalysisOutput
            )
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"LLM sector analysis failed for {symbol}: {e}")
            return {"error": str(e), "relative_position": "Unknown"}
    
    def _empty_result(self, symbol: str, reason: str) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "sector": "Unknown",
            "peer_count": 0,
            "peer_valuation_stats": {},
            "company_valuation": {},
            "macro_context": {},
            "qualitative_analysis": {"error": reason},
            "analyzed_at": date.today().isoformat()
        }
"""Technical Analysis Agent - Price action, momentum, and timing analysis."""

import json
from typing import Dict, Any, List, Optional
from datetime import date, timedelta

from src.utils.logger import logger
from src.data.market_data import get_market_data_provider
from src.analysis.indicators import (
    calculate_all_indicators, get_latest_indicators, 
    calculate_relative_strength, detect_chart_patterns
)
from src.llm.llm_client import get_llm_client
from src.llm.prompts import FINANCIAL_ANALYST_SYSTEM, TECHNICAL_AGENT_PROMPT
from src.llm.schemas import TechnicalAnalysisOutput
from src.storage.database import StockRepository


class TechnicalAgent:
    """Performs technical analysis and momentum assessment."""
    
    def __init__(self, repo: StockRepository):
        self.repo = repo
        self.md_provider = get_market_data_provider()
        self.llm = get_llm_client()
        
    def analyze(self, symbol: str, benchmark_symbol: str = "^NSEI") -> Dict[str, Any]:
        """Run complete technical analysis."""
        logger.info(f"Running technical analysis for {symbol}")
        
        # 1. Get price history
        stock_df = self.md_provider.get_price_history(symbol, period="2y")
        if stock_df is None or stock_df.empty:
            return self._empty_result(symbol)
            
        # 2. Get benchmark for relative strength (cached)
        if not hasattr(self, "_bench_cache"):
            self._bench_cache = {}
        if benchmark_symbol not in self._bench_cache:
            b_df = self.md_provider.get_price_history(benchmark_symbol, period="2y")
            self._bench_cache[benchmark_symbol] = b_df if (b_df is not None and not b_df.empty) else None
        bench_df = self._bench_cache.get(benchmark_symbol)
            
        # 3. Calculate indicators
        stock_df = calculate_all_indicators(stock_df)
        if bench_df is not None:
            bench_df = calculate_all_indicators(bench_df)
            
        # 4. Extract latest indicators
        indicators = get_latest_indicators(stock_df)
        
        # 5. Relative strength
        relative_strength = {}
        if bench_df is not None:
            relative_strength = calculate_relative_strength(stock_df, bench_df)
            
        # 6. Chart patterns
        patterns = detect_chart_patterns(stock_df)
        
        # 7. LLM Qualitative Analysis
        qualitative = self._run_llm_analysis(symbol, indicators, patterns, relative_strength)
        
        return {
            "symbol": symbol,
            "indicators": indicators,
            "relative_strength": relative_strength,
            "patterns": patterns,
            "qualitative_analysis": qualitative,
            "analyzed_at": date.today().isoformat()
        }
    
    def _run_llm_analysis(
        self, 
        symbol: str, 
        indicators: Dict, 
        patterns: List[str],
        relative_strength: Dict
    ) -> Dict[str, Any]:
        """Run LLM qualitative technical analysis."""
        try:
            stock = self.repo.get_stock(symbol)
            company_name = stock.name if stock else symbol
            
            prompt = TECHNICAL_AGENT_PROMPT.format(
                symbol=symbol,
                company_name=company_name,
                indicators_json=json.dumps(indicators, indent=2, default=str),
                patterns_json=json.dumps(patterns, indent=2),
                relative_strength_json=json.dumps(relative_strength, indent=2, default=str)
            )
            
            messages = [
                {"role": "system", "content": FINANCIAL_ANALYST_SYSTEM},
                {"role": "user", "content": prompt}
            ]
            
            result = self.llm.chat_structured(
                messages=messages,
                response_model=TechnicalAnalysisOutput
            )
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"LLM technical analysis failed for {symbol}: {e}")
            return {"error": str(e), "trend_assessment": "Unavailable", "timing_recommendation": "Unavailable"}
    
    def _empty_result(self, symbol: str) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "indicators": {},
            "relative_strength": {},
            "patterns": [],
            "qualitative_analysis": {"error": "No price data available"},
            "analyzed_at": date.today().isoformat()
        }
"""Valuation Analysis and Peer Comparison Engine."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import date

from src.utils.logger import logger
from src.utils.helpers import safe_divide
from src.storage.database import StockRepository


class ValuationEngine:
    """Handles valuation metrics calculation and peer comparison."""
    
    def __init__(self, repo: StockRepository):
        self.repo = repo
        
    def calculate_valuation_metrics(
        self, 
        fundamentals: Dict[str, Any], 
        current_price: float,
        shares_outstanding: Optional[float] = None
    ) -> Dict[str, float]:
        """Calculate comprehensive valuation metrics."""
        metrics = {}
        
        revenue = fundamentals.get("revenue") or 0
        net_profit = fundamentals.get("net_profit") or 0
        ebitda = fundamentals.get("ebitda") or 0
        equity = fundamentals.get("total_equity") or 0
        debt = fundamentals.get("total_debt") or 0
        fcf = fundamentals.get("fcf") or 0
        
        if shares_outstanding is None:
            shares_outstanding = fundamentals.get("shares_outstanding")
            
        if shares_outstanding and shares_outstanding > 0:
            mcap = current_price * shares_outstanding
            metrics["market_cap"] = mcap
            
            # Price Ratios
            metrics["pe_ratio"] = safe_divide(mcap, net_profit)
            metrics["ps_ratio"] = safe_divide(mcap, revenue)
            metrics["pb_ratio"] = safe_divide(mcap, equity)
            
            # Enterprise Value Ratios
            ev = mcap + debt - fundamentals.get("cash", 0)
            metrics["ev"] = ev
            metrics["ev_ebitda"] = safe_divide(ev, ebitda)
            metrics["ev_revenue"] = safe_divide(ev, revenue)
            metrics["ev_fcf"] = safe_divide(ev, fcf)
            
            # Per Share
            metrics["eps"] = safe_divide(net_profit, shares_outstanding)
            metrics["bvps"] = safe_divide(equity, shares_outstanding)
            metrics["fcfps"] = safe_divide(fcf, shares_outstanding)
            
        # Yield metrics
        metrics["dividend_yield"] = fundamentals.get("dividend_yield", 0)
        metrics["fcf_yield"] = safe_divide(fcf, metrics.get("market_cap", 1)) * 100
        
        return metrics
    
    def get_sector_peers(self, symbol: str, sector: str, min_mcap: float = 0) -> List[str]:
        """Get peer symbols in the same sector."""
        all_stocks = self.repo.get_all_active_stocks()
        peers = []
        for stock in all_stocks:
            if stock.symbol == symbol:
                continue
            if stock.sector and sector and stock.sector.lower() == sector.lower():
                if stock.market_cap and stock.market_cap >= min_mcap:
                    peers.append(stock.symbol)
        return peers
    
    def get_peer_valuation_stats(self, symbol: str, sector: str) -> Dict[str, Dict[str, float]]:
        """Calculate sector median, min, max for key valuation metrics."""
        peers = self.get_sector_peers(symbol, sector)
        if not peers:
            return {}
            
        peer_metrics = {
            "pe_ratio": [], "pb_ratio": [], "ev_ebitda": [], 
            "ps_ratio": [], "dividend_yield": [], "roe": [], "roce": []
        }
        
        for peer_sym in peers[:30]:  # Limit to top 30 peers by market cap
            fund = self.repo.get_latest_fundamentals(peer_sym)
            if fund:
                peer_metrics["pe_ratio"].append(fund.pe_ratio or 0)
                peer_metrics["pb_ratio"].append(fund.pb_ratio or 0)
                peer_metrics["ev_ebitda"].append(fund.ev_ebitda or 0)
                peer_metrics["ps_ratio"].append(fund.ps_ratio or 0)
                peer_metrics["dividend_yield"].append(fund.dividend_yield or 0)
                peer_metrics["roe"].append(fund.roe or 0)
                peer_metrics["roce"].append(fund.roce or 0)
                
        stats = {}
        for metric, values in peer_metrics.items():
            valid = [v for v in values if v and v > 0]
            if valid:
                stats[metric] = {
                    "median": float(np.median(valid)),
                    "mean": float(np.mean(valid)),
                    "min": float(np.min(valid)),
                    "max": float(np.max(valid)),
                    "p25": float(np.percentile(valid, 25)),
                    "p75": float(np.percentile(valid, 75)),
                    "count": len(valid)
                }
                
        return stats
    
    def calculate_relative_valuation(self, symbol: str, sector: str, stock_metrics: Dict) -> Dict[str, Any]:
        """Compare stock valuation vs sector peers."""
        peer_stats = self.get_peer_valuation_stats(symbol, sector)
        if not peer_stats:
            return {"error": "Insufficient peer data"}
            
        comparison = {}
        key_metrics = ["pe_ratio", "pb_ratio", "ev_ebitda", "ps_ratio"]
        
        for metric in key_metrics:
            stock_val = stock_metrics.get(metric, 0)
            if stock_val and metric in peer_stats:
                median = peer_stats[metric]["median"]
                p25 = peer_stats[metric]["p25"]
                p75 = peer_stats[metric]["p75"]
                
                # Percentile rank
                percentile = self._percentile_rank(stock_val, peer_stats[metric])
                
                # Discount/Premium to median
                discount = safe_divide(median - stock_val, median) * 100 if median else 0
                
                comparison[metric] = {
                    "stock_value": stock_val,
                    "sector_median": median,
                    "sector_p25": p25,
                    "sector_p75": p75,
                    "percentile": percentile,
                    "discount_to_median_pct": discount,
                    "assessment": self._assess_valuation(metric, percentile)
                }
                
        return comparison
    
    def _percentile_rank(self, value: float, stats: Dict) -> float:
        """Estimate percentile rank assuming normal distribution."""
        # Simplified: use p25/p75 to estimate
        p25 = stats.get("p25", 0)
        p75 = stats.get("p75", 0)
        median = stats.get("median", 0)
        
        if value <= p25:
            return 10.0
        elif value >= p75:
            return 90.0
        elif value <= median:
            return 25.0 + 25.0 * (value - p25) / (median - p25) if median != p25 else 25.0
        else:
            return 50.0 + 40.0 * (value - median) / (p75 - median) if p75 != median else 50.0
            
    def _assess_valuation(self, metric: str, percentile: float) -> str:
        """Assess if valuation is cheap/fair/expensive."""
        # For most metrics, lower is better (cheaper)
        if metric in ["dividend_yield", "roe", "roce"]:
            # Higher is better
            if percentile > 75: return "Attractive"
            elif percentile > 50: return "Fair"
            elif percentile > 25: return "Rich"
            else: return "Expensive"
        else:
            # Lower is better (PE, PB, EV/EBITDA, PS)
            if percentile < 25: return "Attractive"
            elif percentile < 50: return "Fair"
            elif percentile < 75: return "Rich"
            else: return "Expensive"
    
    def historical_valuation_percentile(self, symbol: str, metric: str, years: int = 5) -> Optional[float]:
        """Calculate current valuation percentile vs own history."""
        history = self.repo.get_fundamentals_history(symbol, limit=years * 4)
        if len(history) < 8:
            return None
            
        values = []
        for f in history:
            val = getattr(f, metric, None)
            if val and val > 0:
                values.append(val)
                
        if len(values) < 5:
            return None
            
        current = values[0]  # Most recent
        percentile = (sum(1 for v in values if v >= current) / len(values)) * 100
        return percentile


def score_valuation(metrics: Dict, peer_comparison: Dict, historical_pct: Optional[float]) -> float:
    """Score valuation 0-100 based on multiple factors."""
    scores = []
    
    # 1. Peer Relative (40% weight)
    if peer_comparison and "error" not in peer_comparison:
        peer_scores = []
        for m, data in peer_comparison.items():
            assessment = data.get("assessment", "Fair")
            if assessment == "Attractive": peer_scores.append(90)
            elif assessment == "Fair": peer_scores.append(60)
            elif assessment == "Rich": peer_scores.append(30)
            else: peer_scores.append(10)
        if peer_scores:
            scores.append(("peer", np.mean(peer_scores), 0.4))
            
    # 2. Historical Percentile (30% weight)
    if historical_pct is not None:
        # Lower percentile = cheaper = better score
        hist_score = 100 - historical_pct
        scores.append(("historical", hist_score, 0.3))
        
    # 3. Absolute Levels (30% weight)
    pe = metrics.get("pe_ratio", 0)
    pb = metrics.get("pb_ratio", 0)
    ev_ebitda = metrics.get("ev_ebitda", 0)
    
    abs_score = 50  # Base
    if pe > 0:
        if pe < 15: abs_score += 20
        elif pe < 25: abs_score += 10
        elif pe > 50: abs_score -= 20
    if pb > 0:
        if pb < 2: abs_score += 10
        elif pb > 5: abs_score -= 10
    if ev_ebitda > 0:
        if ev_ebitda < 10: abs_score += 15
        elif ev_ebitda > 20: abs_score -= 15
        
    abs_score = max(0, min(100, abs_score))
    scores.append(("absolute", abs_score, 0.3))
    
    # Weighted average
    total_weight = sum(w for _, _, w in scores)
    if total_weight == 0:
        return 50
        
    weighted = sum(s * w for _, s, w in scores) / total_weight
    return max(0, min(100, weighted))
"""Fundamental Data Processing and Ratio Calculation Engine."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import date, datetime

from src.utils.logger import logger
from src.utils.helpers import safe_divide
from src.utils.validators import validate_financial_ratio
from src.storage.database import FundamentalData, StockRepository


class FundamentalsProcessor:
    """Processes raw financial statements into standardized ratios and metrics."""
    
    def __init__(self, repo: StockRepository):
        self.repo = repo
        
    def calculate_ratios(self, fund: FundamentalData, current_price: Optional[float] = None) -> Dict[str, float]:
        """Calculates all fundamental ratios from stored fundamental data."""
        ratios = {}
        
        # Profitability
        ratios["operating_margin"] = validate_financial_ratio(fund.operating_margin)
        ratios["net_margin"] = validate_financial_ratio(fund.net_margin)
        ratios["roe"] = validate_financial_ratio(fund.roe)
        ratios["roce"] = validate_financial_ratio(fund.roce)
        
        # Leverage
        ratios["debt_to_equity"] = validate_financial_ratio(fund.debt_to_equity, min_val=0, max_val=50)
        ratios["interest_coverage"] = validate_financial_ratio(fund.interest_coverage, min_val=-100, max_val=100)
        
        # Cash Flow Quality
        ratios["fcf"] = fund.fcf if fund.fcf else 0
        ratios["fcf_margin"] = safe_divide(fund.fcf, fund.revenue) * 100 if fund.fcf and fund.revenue else 0
        ratios["cfo_to_net_income"] = safe_divide(fund.cfo, fund.net_profit) if fund.cfo and fund.net_profit else 0
        
        # Valuation (requires current price)
        if current_price and fund.shares_outstanding and fund.shares_outstanding > 0:
            mcap = current_price * fund.shares_outstanding
            ratios["pe_ratio"] = safe_divide(mcap, fund.net_profit) if fund.net_profit else 0
            ratios["ps_ratio"] = safe_divide(mcap, fund.revenue) if fund.revenue else 0
            ratios["ev_ebitda"] = safe_divide(mcap + (fund.total_debt or 0) - (fund.cfo or 0), fund.ebitda) if fund.ebitda else 0
        else:
            # Use stored valuation ratios
            ratios["pe_ratio"] = validate_financial_ratio(fund.pe_ratio, min_val=0, max_val=500)
            ratios["pb_ratio"] = validate_financial_ratio(fund.pb_ratio, min_val=0, max_val=100)
            ratios["ev_ebitda"] = validate_financial_ratio(fund.ev_ebitda, min_val=0, max_val=200)
            ratios["ps_ratio"] = validate_financial_ratio(fund.ps_ratio, min_val=0, max_val=100)
            ratios["dividend_yield"] = validate_financial_ratio(fund.dividend_yield, min_val=0, max_val=20)
            
        # Shareholding Quality
        ratios["promoter_holding_pct"] = validate_financial_ratio(fund.promoter_holding_pct, min_val=0, max_val=100)
        ratios["promoter_pledged_pct"] = validate_financial_ratio(fund.promoter_pledged_pct, min_val=0, max_val=100)
        
        return ratios
    
    def compute_growth_metrics(self, symbol: str, years: int = 3) -> Dict[str, float]:
        """Computes CAGR growth metrics from historical fundamentals."""
        history = self.repo.get_fundamentals_history(symbol, limit=years * 2)  # Get extra for safety
        if len(history) < 2:
            return {}
            
        # Sort by date ascending (oldest first)
        history_sorted = sorted(history, key=lambda x: x.period_date)
        
        metrics = {}
        # Revenue CAGR
        if history_sorted[-1].revenue and history_sorted[0].revenue and history_sorted[0].revenue > 0:
            n_years = (history_sorted[-1].period_date - history_sorted[0].period_date).days / 365.25
            if n_years > 0:
                metrics["revenue_cagr"] = (history_sorted[-1].revenue / history_sorted[0].revenue) ** (1/n_years) - 1
                
        # Net Profit CAGR
        if history_sorted[-1].net_profit and history_sorted[0].net_profit and history_sorted[0].net_profit > 0:
            n_years = (history_sorted[-1].period_date - history_sorted[0].period_date).days / 365.25
            if n_years > 0:
                metrics["profit_cagr"] = (history_sorted[-1].net_profit / history_sorted[0].net_profit) ** (1/n_years) - 1
                
        # Latest margins
        latest = history_sorted[-1]
        metrics["latest_operating_margin"] = latest.operating_margin or 0
        metrics["latest_net_margin"] = latest.net_margin or 0
        metrics["latest_roe"] = latest.roe or 0
        metrics["latest_roce"] = latest.roce or 0
        
        return metrics
    
    def detect_accounting_red_flags(self, fund: FundamentalData, history: List[FundamentalData]) -> List[str]:
        """Detects potential accounting quality issues."""
        flags = []
        
        # 1. Cash Flow vs Net Income divergence
        if fund.cfo and fund.net_profit:
            if fund.cfo < 0 and fund.net_profit > 0:
                flags.append("Positive Net Income but Negative Operating Cash Flow (Aggressive Accruals)")
            elif fund.cfo < fund.net_profit * 0.5:
                flags.append("Operating Cash Flow significantly lower than Net Income (Low Quality Earnings)")
                
        # 2. Receivables growing faster than Revenue (if we had detailed BS)
        # Simplified check: CFO/Net Income trend
        if len(history) >= 3:
            cfo_ni_ratios = [safe_divide(f.cfo, f.net_profit) for f in history[:3] if f.cfo and f.net_profit]
            if len(cfo_ni_ratios) >= 3 and all(r < 0.8 for r in cfo_ni_ratios):
                flags.append("Consistently low Cash Conversion (CFO/Net Income < 0.8 for 3+ periods)")
                
        # 3. High Promoter Pledge
        if fund.promoter_pledged_pct and fund.promoter_pledged_pct > 20:
            flags.append(f"High Promoter Pledge: {fund.promoter_pledged_pct:.1f}%")
        elif fund.promoter_pledged_pct and fund.promoter_pledged_pct > 5:
            flags.append(f"Moderate Promoter Pledge: {fund.promoter_pledged_pct:.1f}%")
            
        # 4. Declining Promoter Holding
        if len(history) >= 2:
            latest_holding = history[0].promoter_holding_pct or 0
            prev_holding = history[1].promoter_holding_pct or 0
            if latest_holding < prev_holding - 2:  # >2% drop
                flags.append(f"Promoter Holding decreased from {prev_holding:.1f}% to {latest_holding:.1f}%")
                
        # 5. Rising Debt without Asset Growth
        if len(history) >= 2:
            latest_debt = history[0].debt_to_equity or 0
            prev_debt = history[1].debt_to_equity or 0
            if latest_debt > prev_debt * 1.5 and latest_debt > 1.0:
                flags.append(f"Debt-to-Equity increased sharply from {prev_debt:.2f} to {latest_debt:.2f}")
                
        # 6. Negative Net Worth / Equity
        # Use getattr to safely handle missing attributes (e.g., older DB schema)
        total_equity = getattr(fund, 'total_equity', None)
        if total_equity is not None and total_equity < 0:
            flags.append("Negative Shareholders' Equity (Balance Sheet Insolvency Risk)")
            
        return flags


def enrich_fundamental_data(raw_data: Dict[str, Any], current_price: Optional[float] = None) -> Dict[str, Any]:
    """Enriches raw fundamental data with calculated ratios and derived metrics."""
    enriched = raw_data.copy()
    
    # Basic Ratios
    rev = raw_data.get("revenue") or 0
    ni = raw_data.get("net_profit") or 0
    ebitda = raw_data.get("ebitda") or 0
    op = raw_data.get("operating_profit") or 0
    debt = raw_data.get("total_debt") or 0
    equity = raw_data.get("total_equity") or 0
    fcf = raw_data.get("fcf") or 0
    cfo = raw_data.get("cfo") or 0
    
    enriched["operating_margin"] = safe_divide(op, rev) * 100
    enriched["net_margin"] = safe_divide(ni, rev) * 100
    enriched["debt_to_equity"] = safe_divide(debt, equity)
    enriched["interest_coverage"] = safe_divide(ebitda, raw_data.get("interest_expense") or 1) if raw_data.get("interest_expense") else 0
    
    # Valuation
    if current_price and raw_data.get("shares_outstanding"):
        mcap = current_price * raw_data["shares_outstanding"]
        enriched["pe_ratio"] = safe_divide(mcap, ni)
        enriched["ps_ratio"] = safe_divide(mcap, rev)
        enriched["ev_ebitda"] = safe_divide(mcap + debt - (raw_data.get("cash") or 0), ebitda)
        enriched["pb_ratio"] = safe_divide(mcap, equity)
        
    return enriched
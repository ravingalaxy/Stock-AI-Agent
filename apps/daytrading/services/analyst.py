"""Skill 9: Trader Analyst — Earnings, financial statements, quarterly results, company analysis.

Uses existing FundamentalData model from apps.market. Never fabricates financial metrics.
"""

import logging
from typing import Dict, Any, Optional, List

from apps.market.models import Stock, FundamentalData, PriceHistory
from .market_data import get_quote, get_daily_history, normalize_symbol, clean_symbol

logger = logging.getLogger(__name__)


def get_company_overview(symbol, exchange="NSE"):
    """Get comprehensive company overview from existing DB."""
    sym = normalize_symbol(symbol, exchange)
    try:
        stock = Stock.objects.get(symbol=sym)
    except Stock.DoesNotExist:
        # Try clean symbol match
        clean = clean_symbol(sym)
        stocks = Stock.objects.filter(symbol__icontains=clean)
        if not stocks.exists():
            return {"error": f"Stock {sym} not found in database"}
        stock = stocks.first()

    # Get latest fundamentals
    fundamentals = FundamentalData.objects.filter(stock=stock).order_by("-period_date")
    latest_annual = fundamentals.filter(period_type="A").first()
    latest_quarterly = fundamentals.filter(period_type="Q").first()

    # Get current quote
    quote = get_quote(symbol, exchange)

    result = {
        "symbol": stock.symbol,
        "name": stock.name,
        "exchange": stock.exchange,
        "sector": stock.sector,
        "industry": stock.industry,
        "market_cap": stock.market_cap,
        "market_cap_formatted": stock.formatted_mcap,
        "current_price": float(stock.current_price) if stock.current_price else None,
        "pe_ratio": stock.pe_ratio,
        "pb_ratio": stock.pb_ratio,
        "dividend_yield": stock.dividend_yield,
    }

    if latest_annual:
        result["annual"] = {
            "period": str(latest_annual.period_date),
            "revenue": latest_annual.revenue,
            "net_profit": latest_annual.net_profit,
            "operating_margin": latest_annual.operating_margin,
            "net_margin": latest_annual.net_margin,
            "roe": latest_annual.roe,
            "roce": latest_annual.roce,
            "debt_to_equity": latest_annual.debt_to_equity,
            "promoter_holding": latest_annual.promoter_holding_pct,
        }

    if latest_quarterly:
        result["quarterly"] = {
            "period": str(latest_quarterly.period_date),
            "revenue": latest_quarterly.revenue,
            "net_profit": latest_quarterly.net_profit,
            "operating_margin": latest_quarterly.operating_margin,
            "net_margin": latest_quarterly.net_margin,
        }

    if quote:
        result["live_quote"] = quote

    return result


def get_earnings_history(symbol, exchange="NSE", periods=8):
    """Get quarterly earnings history."""
    sym = normalize_symbol(symbol, exchange)
    try:
        stock = Stock.objects.get(symbol=sym)
    except Stock.DoesNotExist:
        clean = clean_symbol(sym)
        stocks = Stock.objects.filter(symbol__icontains=clean)
        if not stocks.exists():
            return []
        stock = stocks.first()

    return list(
        FundamentalData.objects.filter(stock=stock, period_type="Q")
        .order_by("-period_date")[:periods]
        .values("period_date", "revenue", "net_profit", "ebitda",
                "operating_margin", "net_margin", "roe")
    )


def get_financial_ratios(symbol, exchange="NSE"):
    """Get key financial ratios for intraday analysis context."""
    overview = get_company_overview(symbol, exchange)
    if "error" in overview:
        return overview

    ratios = {
        "symbol": overview["symbol"],
        "pe_ratio": overview.get("pe_ratio"),
        "pb_ratio": overview.get("pb_ratio"),
        "dividend_yield": overview.get("dividend_yield"),
        "market_cap": overview.get("market_cap_formatted"),
    }

    if "annual" in overview:
        a = overview["annual"]
        ratios.update({
            "roe": a.get("roe"),
            "roce": a.get("roce"),
            "debt_to_equity": a.get("debt_to_equity"),
            "operating_margin": a.get("operating_margin"),
            "net_margin": a.get("net_margin"),
            "promoter_holding": a.get("promoter_holding"),
        })

    return ratios


def compare_stocks(symbols, exchange="NSE"):
    """Compare multiple stocks on key metrics."""
    results = []
    for sym in symbols:
        overview = get_company_overview(sym, exchange)
        if "error" not in overview:
            results.append({
                "symbol": overview["symbol"],
                "name": overview.get("name"),
                "market_cap": overview.get("market_cap_formatted"),
                "pe_ratio": overview.get("pe_ratio"),
                "pb_ratio": overview.get("pb_ratio"),
                "roe": overview.get("annual", {}).get("roe"),
                "roce": overview.get("annual", {}).get("roce"),
                "net_margin": overview.get("annual", {}).get("net_margin"),
            })
    return results

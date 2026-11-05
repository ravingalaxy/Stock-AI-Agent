"""Data and financial validation helper functions."""

import re
from typing import Any, Dict, List, Optional, Tuple


# Ticker aliases dictionary for renamed, demerged, or legacy tickers on NSE/BSE
# (e.g. Tata Motors demerged into TMCV and TMPV effective Nov 2026; TATAMOTORS -> TMCV on Yahoo Finance)
TICKER_ALIASES: Dict[str, str] = {
    "TATAMOTORS": "TMCV",
    "TATAMOTORS.NS": "TMCV.NS",
    "TATAMOTORS.BO": "TMCV.BO",
    "TATAMTRDVR": "TMCV",
    "TATAMTRDVR.NS": "TMCV.NS",
    "TATAMTRDVR.BO": "TMCV.BO",
}


def normalize_ticker(ticker: str) -> str:
    """Standardizes ticker symbol for NSE/BSE Indian stocks for yfinance compatibility.
    
    Examples:
        RELIANCE -> RELIANCE.NS
        500325 -> 500325.BO
        TCS.NS -> TCS.NS
        TATAMOTORS -> TMCV.NS (via demerger alias)
        ^NSEI -> ^NSEI (index symbols unchanged)
    """
    ticker = ticker.strip().upper()
    
    # Check direct alias
    if ticker in TICKER_ALIASES:
        ticker = TICKER_ALIASES[ticker]
    
    # Check base alias if suffix is attached
    base = ticker.replace(".NS", "").replace(".BO", "")
    if base in TICKER_ALIASES:
        target_base = TICKER_ALIASES[base].replace(".NS", "").replace(".BO", "")
        suffix = ".BO" if ticker.endswith(".BO") else ".NS"
        ticker = f"{target_base}{suffix}"

    if ticker.endswith(".NS") or ticker.endswith(".BO"):
        return ticker
    # Index symbols (starting with ^) should not be modified
    if ticker.startswith("^"):
        return ticker
    # If ticker is purely numeric, it's a BSE code
    if ticker.isdigit():
        return f"{ticker}.BO"
    return f"{ticker}.NS"


def clean_ticker_display(ticker: str) -> str:
    """Returns clean symbol for display (e.g. RELIANCE.NS -> RELIANCE)."""
    clean = ticker.replace(".NS", "").replace(".BO", "").strip().upper()
    return TICKER_ALIASES.get(clean, clean)


def validate_financial_ratio(val: Any, default: float = 0.0, min_val: Optional[float] = None, max_val: Optional[float] = None) -> float:
    """Validates and clips financial ratio values safely against NaN or extreme outliers."""
    if val is None:
        return default
    try:
        fval = float(val)
        if fval != fval:  # Check NaN
            return default
        if min_val is not None and fval < min_val:
            return min_val
        if max_val is not None and fval > max_val:
            return max_val
        return fval
    except (ValueError, TypeError):
        return default


def validate_ticker_list(symbols: List[str]) -> List[str]:
    """Cleans and validates a list of raw ticker inputs."""
    valid_symbols = []
    for sym in symbols:
        cleaned = normalize_ticker(sym)
        if re.match(r"^[A-Z0-9\.\&\-]+$", cleaned):
            valid_symbols.append(cleaned)
    return list(dict.fromkeys(valid_symbols))  # Deduplicate preserving order

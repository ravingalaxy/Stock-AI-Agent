"""General helper utilities for data formatting, math, and date handling."""

from datetime import datetime, date
import math
from typing import Any, Union

try:
    import numpy as np
    import pandas as pd
except ImportError:
    np = None
    pd = None


def format_inr(value: Union[int, float, None]) -> str:
    """Formats numeric values into Indian Crore (Cr) or Lakh (L) representations.
    
    Examples:
        10000000 -> ₹1.00 Cr
        500000 -> ₹5.00 L
    """
    if value is None or math.isnan(value):
        return "N/A"
    
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    
    if abs_val >= 10_000_000:  # 1 Crore = 10 Million
        return f"{sign}₹{abs_val / 10_000_000:,.2f} Cr"
    elif abs_val >= 100_000:   # 1 Lakh = 100 Thousand
        return f"{sign}₹{abs_val / 100_000:,.2f} L"
    else:
        return f"{sign}₹{abs_val:,.2f}"


def format_percentage(value: Union[int, float, None], decimals: int = 2) -> str:
    """Formats float value to percentage string. Input is decimal (0.1234 = 12.34%)."""
    if value is None or math.isnan(value):
        return "N/A"
    return f"{value * 100:.{decimals}f}%"


def safe_divide(numerator: Union[float, "pd.Series"], denominator: Union[float, "pd.Series"], default: float = 0.0) -> Union[float, "pd.Series"]:
    """Safely divides two numbers or Series avoiding ZeroDivisionError and NaN."""
    try:
        import pandas as pd
        if isinstance(numerator, pd.Series) or isinstance(denominator, pd.Series):
            # Handle pandas Series division
            with np.errstate(divide='ignore', invalid='ignore'):
                result = numerator / denominator
                result = result.replace([np.inf, -np.inf], np.nan)
                return result.fillna(default)
    except ImportError:
        pass
    
    # Scalar division
    if denominator is None or denominator == 0 or (isinstance(denominator, float) and math.isnan(denominator)) or (isinstance(numerator, float) and math.isnan(numerator)):
        return default
    return numerator / denominator


def parse_date(date_str: Any) -> datetime:
    """Parses various date string formats safely into datetime."""
    if isinstance(date_str, datetime):
        return date_str
    if isinstance(date_str, date):
        return datetime.combine(date_str, datetime.min.time())
    
    formats = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d", "%d-%m-%Y", "%b %d, %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except ValueError:
            continue
    return datetime.now()

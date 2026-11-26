"""NSE / BSE market calendar — holidays, trading sessions, Muhurat trading.

Timezone: Asia/Kolkata (IST, UTC+05:30, no DST).
Pre-open: 09:00 - 09:15 IST.
Normal session: 09:15 - 15:30 IST.
"""

from datetime import datetime, date, time, timedelta
from typing import Optional, Tuple
import pytz

IST = pytz.timezone("Asia/Kolkata")

NSE_HOLIDAYS: set = {
    # 2025
    date(2025, 1, 26), date(2025, 2, 26), date(2025, 3, 14),
    date(2025, 3, 31), date(2025, 4, 10), date(2025, 4, 14),
    date(2025, 4, 18), date(2025, 5, 1), date(2025, 6, 27),
    date(2025, 8, 15), date(2025, 8, 16), date(2025, 8, 27),
    date(2025, 10, 2), date(2025, 10, 21), date(2025, 10, 22),
    date(2025, 11, 5), date(2025, 11, 26), date(2025, 12, 25),
    # 2026
    date(2026, 1, 26), date(2026, 2, 17), date(2026, 3, 3),
    date(2026, 3, 19), date(2026, 3, 25), date(2026, 3, 30),
    date(2026, 4, 3), date(2026, 4, 14), date(2026, 5, 1),
    date(2026, 6, 17), date(2026, 7, 7), date(2026, 8, 15),
    date(2026, 8, 17), date(2026, 10, 2), date(2026, 10, 10),
    date(2026, 10, 20), date(2026, 10, 25), date(2026, 11, 4),
    date(2026, 12, 25),
    # 2027
    date(2027, 1, 26), date(2027, 2, 5), date(2027, 3, 11),
    date(2027, 3, 18), date(2027, 3, 22), date(2027, 4, 1),
    date(2027, 4, 14), date(2027, 5, 1), date(2027, 5, 14),
    date(2027, 6, 7), date(2027, 7, 27), date(2027, 8, 15),
    date(2027, 10, 2), date(2027, 10, 9), date(2027, 10, 29),
    date(2027, 11, 15), date(2027, 11, 24), date(2027, 12, 25),
}

MARKET_OPEN_TIME = time(9, 15)
MARKET_CLOSE_TIME = time(15, 30)
PRE_OPEN_START = time(9, 0)


def now_ist():
    """Current datetime in IST."""
    return datetime.now(IST)


def is_trading_day(d=None):
    """Check if a date is a trading day (weekday & not a holiday)."""
    d = d or now_ist().date()
    if d.weekday() >= 5:
        return False
    return d not in NSE_HOLIDAYS


def is_market_open(dt=None):
    """Check if market is currently open for normal trading."""
    dt = dt or now_ist()
    if not is_trading_day(dt.date()):
        return False
    t = dt.time()
    return MARKET_OPEN_TIME <= t < MARKET_CLOSE_TIME


def is_pre_open(dt=None):
    """Check if we are in pre-open session."""
    dt = dt or now_ist()
    if not is_trading_day(dt.date()):
        return False
    t = dt.time()
    return PRE_OPEN_START <= t < MARKET_OPEN_TIME


def session_boundaries(d=None):
    """Return (open_dt, close_dt) in IST for a given date."""
    d = d or now_ist().date()
    open_dt = IST.localize(datetime.combine(d, MARKET_OPEN_TIME))
    close_dt = IST.localize(datetime.combine(d, MARKET_CLOSE_TIME))
    return open_dt, close_dt


def next_trading_day(d=None):
    """Return the next trading day after d."""
    d = d or now_ist().date()
    d += timedelta(days=1)
    while not is_trading_day(d):
        d += timedelta(days=1)
    return d


def prev_trading_day(d=None):
    """Return the previous trading day before d."""
    d = d or now_ist().date()
    d -= timedelta(days=1)
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


def trading_days_between(start, end):
    """Return list of trading days in [start, end]."""
    days = []
    d = start
    while d <= end:
        if is_trading_day(d):
            days.append(d)
        d += timedelta(days=1)
    return days


def minutes_to_close(dt=None):
    """Minutes remaining until market close. Returns 0 if closed."""
    dt = dt or now_ist()
    if not is_market_open(dt):
        return 0
    close_dt = IST.localize(datetime.combine(dt.date(), MARKET_CLOSE_TIME))
    return max(0, int((close_dt - dt).total_seconds() / 60))


def market_status():
    """Return current market status summary."""
    dt = now_ist()
    return {
        "is_trading_day": is_trading_day(dt.date()),
        "is_market_open": is_market_open(dt),
        "is_pre_open": is_pre_open(dt),
        "current_time_ist": dt.strftime("%Y-%m-%d %H:%M:%S IST"),
        "minutes_to_close": minutes_to_close(dt),
        "next_trading_day": str(next_trading_day(dt.date())) if not is_market_open(dt) else str(dt.date()),
    }

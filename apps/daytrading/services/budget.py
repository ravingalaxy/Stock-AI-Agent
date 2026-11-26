"""Skill 6: Trader Budget — INR capital allocation, available balance, per-trade limits."""

import logging
from decimal import Decimal
from typing import Dict, Any

from apps.daytrading.models import PaperAccount, PaperPosition
from .risk import get_or_create_account, calculate_position_size
from .charges import round_trip_charges

logger = logging.getLogger(__name__)


def get_budget_summary():
    """Get complete budget/capital summary."""
    account = get_or_create_account()
    positions = PaperPosition.objects.filter(is_open=True)
    used_capital = sum(
        float(p.avg_entry_price * abs(p.quantity)) for p in positions
    )
    unrealized = sum(float(p.unrealized_pnl) for p in positions)

    return {
        "initial_capital": float(account.initial_capital),
        "available_cash": float(account.available_cash),
        "used_margin": float(account.used_margin),
        "used_capital": round(used_capital, 2),
        "unrealized_pnl": round(unrealized, 2),
        "realized_pnl": float(account.realized_pnl),
        "total_charges": float(account.total_charges),
        "net_equity": round(float(account.available_cash) + used_capital + unrealized, 2),
        "open_positions": positions.count(),
        "max_open_positions": account.max_open_positions,
        "daily_loss_limit": float(account.daily_loss_limit),
        "max_position_pct": float(account.max_position_pct),
        "per_trade_max": round(float(account.initial_capital) * float(account.max_position_pct) / 100, 2),
    }


def allocate_for_trade(entry_price, stop_loss, risk_pct=1.0, exchange="NSE"):
    """Calculate position sizing and capital allocation for a trade."""
    account = get_or_create_account()
    sizing = calculate_position_size(
        capital=float(account.available_cash),
        risk_pct=risk_pct,
        entry_price=entry_price,
        stop_loss=stop_loss,
        max_position_pct=float(account.max_position_pct),
    )

    if sizing["quantity"] <= 0:
        return {**sizing, "can_trade": False, "reason": "Cannot size position"}

    charges = round_trip_charges(
        Decimal(str(entry_price)), Decimal(str(stop_loss)),
        sizing["quantity"], "MIS", exchange,
    )

    return {
        **sizing,
        "can_trade": True,
        "available_cash": float(account.available_cash),
        "remaining_after": round(float(account.available_cash) - sizing["position_value"], 2),
        "estimated_charges": {k: float(v) for k, v in charges.items()},
    }


def update_account_after_fill(fill_value, charges_total, is_buy=True):
    """Update account balances after a fill."""
    account = get_or_create_account()
    charges = Decimal(str(charges_total))
    value = Decimal(str(fill_value))

    if is_buy:
        account.available_cash -= (value + charges)
        account.used_margin += value
    else:
        account.available_cash += (value - charges)
        account.used_margin -= value
        account.used_margin = max(Decimal("0"), account.used_margin)

    account.total_charges += charges
    account.save()
    return float(account.available_cash)


def reset_paper_account(initial_capital=1000000):
    """Reset paper account to starting capital."""
    account = get_or_create_account()
    account.initial_capital = Decimal(str(initial_capital))
    account.available_cash = Decimal(str(initial_capital))
    account.used_margin = Decimal("0")
    account.realized_pnl = Decimal("0")
    account.total_charges = Decimal("0")
    account.save()

    # Close all positions
    PaperPosition.objects.filter(is_open=True).update(is_open=False)
    return {"status": "reset", "initial_capital": initial_capital}

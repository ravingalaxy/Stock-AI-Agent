"""Skill 5: Trader Risk — Position sizing, risk/reward, exposure, drawdown, daily loss limits.

All calculations deterministic. Server-side enforced.
"""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional

from apps.daytrading.models import PaperAccount, PaperPosition, PaperOrder, DayTradePlan
from .market_calendar import now_ist
from .charges import round_trip_charges

logger = logging.getLogger(__name__)


def get_or_create_account():
    """Get the default paper account, creating if needed."""
    account, _ = PaperAccount.objects.get_or_create(
        name="Default Paper Account",
        defaults={"initial_capital": Decimal("1000000"), "available_cash": Decimal("1000000")}
    )
    return account


def pre_trade_risk_check(symbol, side, quantity, price, stop_loss=None,
                          product="MIS", exchange="NSE"):
    """Comprehensive pre-trade risk checks. Returns pass/fail with reasons."""
    account = get_or_create_account()
    issues = []
    warnings = []

    # 1. Basic validation
    if quantity <= 0:
        issues.append("Quantity must be positive")
    if price and Decimal(str(price)) <= 0:
        issues.append("Price must be positive")

    position_value = Decimal(str(price or 0)) * quantity

    # 2. Cash check
    if position_value > account.available_cash:
        issues.append(f"Insufficient cash: need {position_value:.2f}, have {account.available_cash:.2f}")

    # 3. Max position size check (% of capital)
    max_position = account.initial_capital * account.max_position_pct / Decimal("100")
    if position_value > max_position:
        issues.append(f"Position {position_value:.2f} exceeds max {max_position:.2f} ({account.max_position_pct}% of capital)")

    # 4. Max open positions
    open_count = PaperPosition.objects.filter(is_open=True).count()
    if open_count >= account.max_open_positions:
        issues.append(f"Max open positions reached ({account.max_open_positions})")

    # 5. Daily loss limit: only triggered if NET REALIZED P&L is negative and exceeds limit
    today = now_ist().date()
    daily_realized = sum(
        float(pos.realized_pnl)
        for pos in PaperPosition.objects.filter(closed_at__date=today, is_open=False)
    )
    if daily_realized <= -float(account.daily_loss_limit):
        issues.append(f"Daily loss limit hit: ₹{abs(daily_realized):.2f} loss vs limit ₹{account.daily_loss_limit}")

    # 6. Stop-loss required
    if not stop_loss:
        warnings.append("No stop-loss set — high risk trade")
    else:
        # Risk per trade
        risk_per_share = abs(Decimal(str(price)) - Decimal(str(stop_loss)))
        total_risk = risk_per_share * quantity
        max_risk = account.initial_capital * Decimal("0.02")  # 2% max risk per trade
        if total_risk > max_risk:
            issues.append(f"Risk ₹{total_risk:.2f} exceeds 2% max (₹{max_risk:.2f})")

    # 7. Reward/risk ratio
    if stop_loss and price:
        risk = abs(Decimal(str(price)) - Decimal(str(stop_loss)))
        if risk > 0:
            rr = risk  # just the risk component; reward needs target
        else:
            warnings.append("Risk is zero — check stop-loss")

    # 8. Charges estimate
    charges = round_trip_charges(
        Decimal(str(price)), Decimal(str(price)) * Decimal("1.01"),
        quantity, product, exchange
    )

    passed = len(issues) == 0
    return {
        "passed": passed,
        "issues": issues,
        "warnings": warnings,
        "position_value": float(position_value),
        "available_cash": float(account.available_cash),
        "open_positions": open_count,
        "max_positions": account.max_open_positions,
        "estimated_charges": {k: float(v) for k, v in charges.items()},
        "daily_realized_pnl": round(daily_realized, 2),
        "daily_loss_limit": float(account.daily_loss_limit),
    }


def calculate_position_size(capital, risk_pct, entry_price, stop_loss,
                             max_position_pct=20):
    """Calculate optimal position size based on risk."""
    capital = Decimal(str(capital))
    entry = Decimal(str(entry_price))
    stop = Decimal(str(stop_loss))
    risk_pct_d = Decimal(str(risk_pct)) / Decimal("100")

    risk_amount = capital * risk_pct_d
    risk_per_share = abs(entry - stop)

    if risk_per_share <= 0:
        return {"quantity": 0, "reason": "Invalid stop-loss (zero risk)"}

    max_qty_risk = int(risk_amount / risk_per_share)

    max_position_value = capital * Decimal(str(max_position_pct)) / Decimal("100")
    max_qty_position = int(max_position_value / entry) if entry > 0 else 0

    quantity = min(max_qty_risk, max_qty_position)

    return {
        "quantity": max(0, quantity),
        "risk_amount": float(risk_amount.quantize(Decimal("0.01"))),
        "risk_per_share": float(risk_per_share.quantize(Decimal("0.01"))),
        "position_value": float((entry * quantity).quantize(Decimal("0.01"))),
        "position_pct": float((entry * quantity / capital * 100).quantize(Decimal("0.01"))) if capital > 0 else 0,
    }


def portfolio_exposure():
    """Calculate current portfolio exposure."""
    account = get_or_create_account()
    positions = PaperPosition.objects.filter(is_open=True)

    total_long = sum(float(p.avg_entry_price * p.quantity) for p in positions if p.quantity > 0)
    total_short = sum(float(abs(p.avg_entry_price * p.quantity)) for p in positions if p.quantity < 0)
    total_exposure = total_long + total_short
    unrealized = sum(float(p.unrealized_pnl) for p in positions)

    return {
        "total_exposure": round(total_exposure, 2),
        "long_exposure": round(total_long, 2),
        "short_exposure": round(total_short, 2),
        "exposure_pct": round(total_exposure / float(account.initial_capital) * 100, 2) if account.initial_capital else 0,
        "unrealized_pnl": round(unrealized, 2),
        "available_cash": float(account.available_cash),
        "initial_capital": float(account.initial_capital),
        "open_positions": positions.count(),
    }

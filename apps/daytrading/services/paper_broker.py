"""Skill 11: Trader Broker — Simulated paper brokerage engine.

PAPER TRADING ONLY. Live trading is TECHNICALLY IMPOSSIBLE.
No real broker endpoints, no real credentials, no real-money transactions.
Server-side enforced: is_paper=True is non-editable, hardcoded in save().
"""

import logging
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional, List

from apps.daytrading.models import (
    PaperOrder, PaperFill, PaperPosition, PaperAccount,
    DayTradePlan, TradeJournalEntry,
)
from .risk import get_or_create_account, pre_trade_risk_check
from .budget import update_account_after_fill
from .charges import calculate_charges
from .market_data import get_quote
from .market_calendar import now_ist, is_market_open

logger = logging.getLogger(__name__)

# ==========================================================================
# PAPER-ONLY SAFETY: These constants make live trading impossible
# ==========================================================================
_PAPER_MODE = True  # Hardcoded, no env override, no config override
_PAPER_LABEL = "[PAPER TRADE - SIMULATED]"


def _enforce_paper():
    """Runtime assertion that we are in paper mode. Called before every order."""
    assert _PAPER_MODE is True, "FATAL: Paper mode disabled — this should never happen"
    return True


def submit_order(symbol, side, quantity, order_type="MARKET", price=None,
                  trigger_price=None, product="MIS", exchange="NSE",
                  plan_id=None):
    """Submit a simulated paper order.

    Returns order dict or error. NEVER sends to a real broker.
    """
    _enforce_paper()

    # Risk check
    check_price = float(price or 0)
    if not check_price:
        quote = get_quote(symbol, exchange)
        if quote:
            check_price = quote["price"]
        else:
            return {"status": "REJECTED", "reason": "Cannot determine price"}

    risk_check = pre_trade_risk_check(
        symbol=symbol, side=side, quantity=quantity,
        price=check_price, product=product, exchange=exchange,
    )

    if not risk_check["passed"]:
        order = PaperOrder.objects.create(
            symbol=symbol, exchange=exchange, side=side,
            order_type=order_type, product=product, quantity=quantity,
            price=Decimal(str(check_price)) if price else None,
            trigger_price=Decimal(str(trigger_price)) if trigger_price else None,
            status="REJECTED",
            rejection_reason="; ".join(risk_check["issues"]),
            plan_id=plan_id,
        )
        return {
            "status": "REJECTED", "order_id": str(order.order_id),
            "reasons": risk_check["issues"], "label": _PAPER_LABEL,
        }

    # Create order
    order = PaperOrder.objects.create(
        symbol=symbol, exchange=exchange, side=side,
        order_type=order_type, product=product, quantity=quantity,
        price=Decimal(str(check_price)),
        trigger_price=Decimal(str(trigger_price)) if trigger_price else None,
        status="OPEN", plan_id=plan_id,
    )

    # For MARKET orders, simulate immediate fill
    if order_type == "MARKET":
        result = _simulate_fill(order, Decimal(str(check_price)))
        return result

    return {
        "status": "OPEN", "order_id": str(order.order_id),
        "symbol": symbol, "side": side, "quantity": quantity,
        "price": check_price, "label": _PAPER_LABEL,
    }


def _simulate_fill(order, fill_price):
    """Simulate order fill with realistic slippage and charges."""
    _enforce_paper()

    # Add simulated slippage (0.01-0.05%)
    import random
    slippage_pct = Decimal(str(random.uniform(0.0001, 0.0005)))
    if order.side == "BUY":
        actual_price = fill_price * (Decimal("1") + slippage_pct)
    else:
        actual_price = fill_price * (Decimal("1") - slippage_pct)
    actual_price = actual_price.quantize(Decimal("0.05"), ROUND_HALF_UP)

    # Calculate charges
    turnover = actual_price * order.quantity
    charges = calculate_charges(turnover, order.side, order.product, order.exchange)

    # Create fill
    fill = PaperFill.objects.create(
        order=order,
        fill_price=actual_price,
        filled_qty=order.quantity,
        filled_at=now_ist(),
        brokerage=charges["brokerage"],
        stt=charges["stt"],
        exchange_charges=charges["exchange_charges"],
        gst=charges["gst"],
        sebi_fee=charges["sebi_fee"],
        stamp_duty=charges["stamp_duty"],
        total_charges=charges["total"],
    )

    # Update order
    order.status = "FILLED"
    order.filled_qty = order.quantity
    order.avg_fill_price = actual_price
    order.save()

    # Update position
    _update_position(order.symbol, order.exchange, order.side,
                     order.quantity, actual_price, charges["total"])

    # Update account
    is_buy = order.side == "BUY"
    update_account_after_fill(float(turnover), float(charges["total"]), is_buy)

    return {
        "status": "FILLED", "order_id": str(order.order_id),
        "symbol": order.symbol, "side": order.side,
        "quantity": order.quantity, "fill_price": float(actual_price),
        "slippage_pct": float(slippage_pct * 100),
        "charges": {k: float(v) for k, v in charges.items()},
        "label": _PAPER_LABEL,
    }


def _update_position(symbol, exchange, side, quantity, price, charges):
    """Update or create paper position."""
    _enforce_paper()

    existing = PaperPosition.objects.filter(symbol=symbol, is_open=True).first()

    if existing:
        if side == "BUY":
            new_qty = existing.quantity + quantity
            if existing.quantity > 0:
                total_cost = (existing.avg_entry_price * existing.quantity) + (price * quantity)
                existing.avg_entry_price = total_cost / new_qty if new_qty > 0 else price
            else:
                # Closing short
                realized = (existing.avg_entry_price - price) * min(quantity, abs(existing.quantity))
                existing.realized_pnl += realized
                new_qty = existing.quantity + quantity

            existing.quantity = new_qty
        else:  # SELL
            new_qty = existing.quantity - quantity
            if existing.quantity > 0:
                # Closing long
                realized = (price - existing.avg_entry_price) * min(quantity, existing.quantity)
                existing.realized_pnl += realized
                new_qty = existing.quantity - quantity
            else:
                total_cost = (abs(existing.avg_entry_price * existing.quantity)) + (price * quantity)
                existing.avg_entry_price = total_cost / abs(new_qty) if new_qty != 0 else price

            existing.quantity = new_qty

        existing.total_charges += Decimal(str(charges))
        existing.current_price = price

        if existing.quantity == 0:
            existing.is_open = False
            existing.closed_at = now_ist()

        existing.save()
    else:
        qty = quantity if side == "BUY" else -quantity
        PaperPosition.objects.create(
            symbol=symbol, exchange=exchange,
            quantity=qty, avg_entry_price=price,
            current_price=price, total_charges=Decimal(str(charges)),
        )


def cancel_order(order_id):
    """Cancel an open paper order."""
    try:
        order = PaperOrder.objects.get(order_id=order_id)
        if order.status in ("PENDING", "OPEN"):
            order.status = "CANCELLED"
            order.save()
            return {"status": "CANCELLED", "order_id": order_id, "label": _PAPER_LABEL}
        return {"status": "ERROR", "reason": f"Cannot cancel {order.status} order"}
    except PaperOrder.DoesNotExist:
        return {"status": "ERROR", "reason": "Order not found"}


def flatten_all():
    """Close all open positions (end-of-day square-off)."""
    _enforce_paper()
    positions = PaperPosition.objects.filter(is_open=True)
    results = []
    for pos in positions:
        side = "SELL" if pos.quantity > 0 else "BUY"
        qty = abs(pos.quantity)
        result = submit_order(pos.symbol, side, qty, "MARKET",
                              exchange=pos.exchange, product="MIS")
        results.append(result)
    return {"flattened": len(results), "results": results, "label": _PAPER_LABEL}


def get_open_positions():
    """Get all open paper positions."""
    positions = PaperPosition.objects.filter(is_open=True)
    result = []
    for pos in positions:
        quote = get_quote(pos.symbol, pos.exchange)
        if quote:
            pos.current_price = Decimal(str(quote["price"]))
            pos.save()
        result.append({
            "symbol": pos.symbol, "exchange": pos.exchange,
            "quantity": pos.quantity,
            "avg_entry": float(pos.avg_entry_price),
            "current_price": float(pos.current_price),
            "unrealized_pnl": float(pos.unrealized_pnl),
            "realized_pnl": float(pos.realized_pnl),
            "total_charges": float(pos.total_charges),
            "label": _PAPER_LABEL,
        })
    return result


def get_order_history(limit=50):
    """Get paper order history."""
    return list(
        PaperOrder.objects.order_by("-created_at")[:limit].values(
            "order_id", "symbol", "side", "order_type", "quantity",
            "price", "status", "avg_fill_price", "filled_qty",
            "rejection_reason", "created_at", "is_paper",
        )
    )


def get_trade_pnl_summary():
    """Get P&L summary across all paper trades."""
    _enforce_paper()
    account = get_or_create_account()
    closed = PaperPosition.objects.filter(is_open=False)
    open_pos = PaperPosition.objects.filter(is_open=True)

    total_realized = sum(float(p.realized_pnl) for p in closed)
    total_unrealized = sum(float(p.unrealized_pnl) for p in open_pos)
    total_charges = float(account.total_charges)

    return {
        "realized_pnl": round(total_realized, 2),
        "unrealized_pnl": round(total_unrealized, 2),
        "total_charges": round(total_charges, 2),
        "net_pnl": round(total_realized + total_unrealized - total_charges, 2),
        "initial_capital": float(account.initial_capital),
        "current_equity": round(float(account.available_cash) + sum(
            float(p.current_price * abs(p.quantity)) for p in open_pos
        ), 2),
        "total_trades": closed.count(),
        "open_positions": open_pos.count(),
        "winners": closed.filter(realized_pnl__gt=0).count(),
        "losers": closed.filter(realized_pnl__lt=0).count(),
        "label": _PAPER_LABEL,
    }

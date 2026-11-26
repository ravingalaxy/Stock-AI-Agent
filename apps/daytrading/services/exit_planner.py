"""Skill 4: Trader Exit — Stop-loss, targets, trailing stops, exit signals.

Deterministic exit logic using Decimal math for precision.
"""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional

from apps.daytrading.models import DayTradePlan, PaperPosition
from .market_data import get_quote
from .market_calendar import is_market_open, minutes_to_close, now_ist

logger = logging.getLogger(__name__)


def calculate_exit_levels(entry_price, direction="LONG", stop_type="ATR",
                          atr=None, risk_pct=1.5, rr_target=2.0):
    """Calculate stop-loss and target levels.

    Stop types: ATR, PERCENT, PRICE, OR_LOW, OR_HIGH
    """
    entry = Decimal(str(entry_price))
    atr_val = Decimal(str(atr or entry * Decimal("0.01")))

    if stop_type == "ATR":
        risk = atr_val * Decimal(str(risk_pct))
    elif stop_type == "PERCENT":
        risk = entry * Decimal(str(risk_pct)) / Decimal("100")
    else:
        risk = atr_val * Decimal("1.5")

    if direction == "LONG":
        stop_loss = entry - risk
        target_1 = entry + (risk * Decimal(str(rr_target)))
        target_2 = entry + (risk * Decimal(str(rr_target * 1.5)))
        target_3 = entry + (risk * Decimal(str(rr_target * 2)))
    else:
        stop_loss = entry + risk
        target_1 = entry - (risk * Decimal(str(rr_target)))
        target_2 = entry - (risk * Decimal(str(rr_target * 1.5)))
        target_3 = entry - (risk * Decimal(str(rr_target * 2)))

    return {
        "entry_price": float(entry),
        "stop_loss": float(stop_loss.quantize(Decimal("0.01"))),
        "target_1": float(target_1.quantize(Decimal("0.01"))),
        "target_2": float(target_2.quantize(Decimal("0.01"))),
        "target_3": float(target_3.quantize(Decimal("0.01"))),
        "risk_per_share": float(risk.quantize(Decimal("0.01"))),
        "risk_reward_1": float(rr_target),
        "risk_reward_2": float(rr_target * 1.5),
        "direction": direction,
        "stop_type": stop_type,
    }


def check_trailing_stop(current_price, entry_price, highest_since_entry,
                         trail_pct=1.0, direction="LONG"):
    """Check if trailing stop has been hit."""
    current = Decimal(str(current_price))
    entry = Decimal(str(entry_price))
    highest = Decimal(str(highest_since_entry))
    trail = Decimal(str(trail_pct)) / Decimal("100")

    if direction == "LONG":
        trail_stop = highest * (Decimal("1") - trail)
        hit = current <= trail_stop
        return {
            "trail_stop": float(trail_stop.quantize(Decimal("0.01"))),
            "hit": hit,
            "current_price": float(current),
            "highest_since_entry": float(highest),
            "unrealized_pnl_pct": float((current - entry) / entry * 100),
        }
    else:
        lowest = Decimal(str(highest_since_entry))  # lowest for shorts
        trail_stop = lowest * (Decimal("1") + trail)
        hit = current >= trail_stop
        return {
            "trail_stop": float(trail_stop.quantize(Decimal("0.01"))),
            "hit": hit,
            "current_price": float(current),
        }


def evaluate_exit(plan_id):
    """Evaluate whether an active plan should exit."""
    try:
        plan = DayTradePlan.objects.get(plan_id=plan_id)
    except DayTradePlan.DoesNotExist:
        return {"action": "NONE", "reason": "Plan not found"}

    if plan.status not in ("ACTIVE", "FILLED"):
        return {"action": "NONE", "reason": f"Plan status is {plan.status}"}

    quote = get_quote(plan.symbol, plan.exchange)
    if not quote:
        return {"action": "NONE", "reason": "Cannot fetch current price"}

    current = Decimal(str(quote["price"]))
    entry = plan.entry_price or Decimal("0")
    stop = plan.stop_loss or Decimal("0")
    t1 = plan.target_1
    t2 = plan.target_2

    if plan.direction == "LONG":
        if stop and current <= stop:
            return {"action": "EXIT", "reason": "Stop-loss hit", "exit_price": float(current), "type": "STOP_LOSS"}
        if t2 and current >= t2:
            return {"action": "EXIT", "reason": "Target 2 hit", "exit_price": float(current), "type": "TARGET_2"}
        if t1 and current >= t1:
            return {"action": "PARTIAL_EXIT", "reason": "Target 1 hit", "exit_price": float(current), "type": "TARGET_1"}
    else:
        if stop and current >= stop:
            return {"action": "EXIT", "reason": "Stop-loss hit", "exit_price": float(current), "type": "STOP_LOSS"}
        if t2 and current <= t2:
            return {"action": "EXIT", "reason": "Target 2 hit", "exit_price": float(current), "type": "TARGET_2"}
        if t1 and current <= t1:
            return {"action": "PARTIAL_EXIT", "reason": "Target 1 hit", "exit_price": float(current), "type": "TARGET_1"}

    # Time-based exit — close all MIS positions before 15:15
    mtc = minutes_to_close()
    if 0 < mtc <= 15:
        return {"action": "EXIT", "reason": "Market closing soon (MIS square-off)", "exit_price": float(current), "type": "TIME_EXIT"}

    pnl_pct = float((current - entry) / entry * 100) if entry else 0
    return {
        "action": "HOLD", "reason": "Within targets",
        "current_price": float(current), "entry_price": float(entry),
        "unrealized_pnl_pct": round(pnl_pct, 2),
        "minutes_to_close": mtc,
    }

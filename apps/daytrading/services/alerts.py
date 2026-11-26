"""Skill 7: Trader Alerts — Price, volume, breakout, entry, exit, stop-loss, news notifications."""

import logging
from decimal import Decimal
from typing import List, Dict, Any, Optional

from apps.daytrading.models import TradingAlert
from .market_data import get_quote
from .market_calendar import now_ist, is_market_open

logger = logging.getLogger(__name__)


def create_alert(symbol, alert_type, condition, threshold=None):
    """Create a new trading alert."""
    alert = TradingAlert.objects.create(
        symbol=symbol,
        alert_type=alert_type,
        condition=condition,
        threshold=Decimal(str(threshold)) if threshold else None,
        is_active=True,
    )
    return {
        "alert_id": str(alert.alert_id),
        "symbol": symbol,
        "alert_type": alert_type,
        "condition": condition,
        "threshold": float(threshold) if threshold else None,
        "status": "ACTIVE",
    }


def check_alerts():
    """Check all active alerts against current prices. Returns triggered alerts."""
    active = TradingAlert.objects.filter(is_active=True, is_triggered=False)
    triggered = []

    for alert in active:
        if not alert.symbol:
            continue

        quote = get_quote(alert.symbol)
        if not quote:
            continue

        current = Decimal(str(quote["price"]))
        should_trigger = False

        if alert.alert_type == "PRICE_ABOVE" and alert.threshold:
            should_trigger = current >= alert.threshold
        elif alert.alert_type == "PRICE_BELOW" and alert.threshold:
            should_trigger = current <= alert.threshold
        elif alert.alert_type == "VOLUME_SPIKE":
            cur_volume = quote.get("volume", 0)
            target_vol = float(alert.threshold) if alert.threshold else 500000
            should_trigger = cur_volume >= target_vol

        if should_trigger:
            alert.is_triggered = True
            alert.triggered_at = now_ist()
            alert.triggered_value = current
            alert.message = f"{alert.symbol} {alert.alert_type}: current ₹{current:.2f}"
            alert.save()
            triggered.append({
                "alert_id": str(alert.alert_id),
                "symbol": alert.symbol,
                "alert_type": alert.alert_type,
                "condition": alert.condition,
                "triggered_value": float(current),
                "message": alert.message,
            })

    return triggered


def get_active_alerts(symbol=None):
    """Get all active alerts."""
    qs = TradingAlert.objects.filter(is_active=True)
    if symbol:
        qs = qs.filter(symbol__icontains=symbol)
    return list(qs.values())


def get_triggered_alerts(limit=50):
    """Get recently triggered alerts."""
    return list(
        TradingAlert.objects.filter(is_triggered=True)
        .order_by("-triggered_at")[:limit]
        .values()
    )


def cancel_alert(alert_id):
    """Cancel an active alert."""
    try:
        alert = TradingAlert.objects.get(alert_id=alert_id)
        alert.is_active = False
        alert.save()
        return {"status": "cancelled", "alert_id": alert_id}
    except TradingAlert.DoesNotExist:
        return {"status": "not_found", "alert_id": alert_id}

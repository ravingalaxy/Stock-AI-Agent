"""Skill 10: Trader Pelosi (Indian) — SEBI insider / promoter trading disclosures.

Adapted for India: uses publicly available SEBI insider-trading disclosures,
NSE/BSE bulk/block deal data. NEVER fabricates transactions.
Only uses legally accessible, public-domain data.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import requests

from apps.daytrading.models import PublicDisclosure
from .market_calendar import now_ist, IST
from .market_data import normalize_symbol

logger = logging.getLogger(__name__)


def fetch_nse_insider_trading(symbol=None, days=30):
    """Fetch NSE insider trading disclosures (SAST/PIT regulations).

    Data source: NSE public corporate governance disclosures.
    These are legally mandated public filings under SEBI regulations.
    """
    items = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        # NSE insider trading data endpoint (public)
        url = "https://www.nseindia.com/api/corporates-pit"
        params = {
            "index": "equities",
            "from_date": (now_ist() - timedelta(days=days)).strftime("%d-%m-%Y"),
            "to_date": now_ist().strftime("%d-%m-%Y"),
        }
        if symbol:
            params["symbol"] = symbol.replace(".NS", "").replace(".BO", "")

        # Note: NSE API requires session cookies — may need a session-based approach
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        resp = session.get(url, params=params, headers=headers, timeout=15)

        if resp.status_code == 200:
            data = resp.json()
            records = data if isinstance(data, list) else data.get("data", [])
            for rec in records[:50]:
                tx_type = "BUY" if "buy" in str(rec.get("acqMode", "")).lower() or \
                          "purchase" in str(rec.get("acqMode", "")).lower() else "SELL"

                items.append({
                    "symbol": normalize_symbol(rec.get("symbol", ""), "NSE"),
                    "filer_name": rec.get("acqName", rec.get("personName", "Unknown")),
                    "filer_category": _map_category(rec.get("tkdAcquirerName", "")),
                    "transaction_type": tx_type,
                    "transaction_date": rec.get("date", rec.get("intimDt", "")),
                    "quantity": int(rec.get("secAcq", 0) or 0),
                    "value_inr": float(rec.get("secVal", 0) or 0),
                    "holding_post_pct": float(rec.get("shareholdingAfter", 0) or 0),
                    "source_url": "https://www.nseindia.com/companies-listing/corporate-filings-insider-trading",
                    "raw_data": rec,
                })
    except Exception as e:
        logger.warning(f"NSE insider trading fetch failed: {e}")

    return items


def fetch_bse_bulk_deals(days=7):
    """Fetch BSE bulk/block deal data (publicly available)."""
    items = []
    try:
        url = "https://api.bseindia.com/BseIndiaAPI/api/DefaultData/w"
        params = {"Type": "bulk_deals"}
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bseindia.com/"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and "Table" in data:
                for deal in data["Table"][:30]:
                    items.append({
                        "symbol": deal.get("SCRIP_CD", ""),
                        "filer_name": deal.get("CLIENTNAME", "Unknown"),
                        "filer_category": "OTHER",
                        "transaction_type": "BUY" if "buy" in deal.get("BUYSELL", "").lower() else "SELL",
                        "transaction_date": deal.get("DT", ""),
                        "quantity": int(deal.get("QTY", 0) or 0),
                        "price": float(deal.get("RATE", 0) or 0),
                        "source_url": "https://www.bseindia.com/markets/MarketInfo/BulkDeals.aspx",
                    })
    except Exception as e:
        logger.warning(f"BSE bulk deals fetch failed: {e}")

    return items


def _map_category(text):
    """Map filer description to category."""
    text = text.lower()
    if "promoter" in text:
        return "PROMOTER"
    elif "director" in text or "kmp" in text:
        return "DIRECTOR"
    elif "designated" in text:
        return "INSIDER"
    return "OTHER"


def fetch_and_store_disclosures(symbol=None, days=30):
    """Fetch disclosures from all sources and persist."""
    all_disclosures = fetch_nse_insider_trading(symbol, days)
    all_disclosures.extend(fetch_bse_bulk_deals())

    stored = []
    for item in all_disclosures:
        try:
            tx_date = None
            date_str = item.get("transaction_date", "")
            if date_str:
                for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
                    try:
                        tx_date = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue

            if not tx_date:
                continue

            obj, created = PublicDisclosure.objects.update_or_create(
                symbol=item.get("symbol", ""),
                filer_name=item.get("filer_name", "")[:255],
                transaction_date=tx_date,
                defaults={
                    "filer_category": item.get("filer_category", "OTHER"),
                    "transaction_type": item.get("transaction_type", "OTHER"),
                    "quantity": item.get("quantity", 0),
                    "price": item.get("price") or item.get("value_inr"),
                    "value_inr": item.get("value_inr"),
                    "holding_post_pct": item.get("holding_post_pct"),
                    "source_url": item.get("source_url", ""),
                    "raw_data": item.get("raw_data", {}),
                }
            )
            stored.append({
                "symbol": item["symbol"], "filer": item["filer_name"],
                "type": item["transaction_type"], "date": str(tx_date), "created": created,
            })
        except Exception as e:
            logger.warning(f"Failed to store disclosure: {e}")

    return stored


def get_recent_disclosures(symbol=None, limit=50):
    """Get recent disclosures from DB."""
    qs = PublicDisclosure.objects.all()
    if symbol:
        clean = symbol.replace(".NS", "").replace(".BO", "")
        qs = qs.filter(symbol__icontains=clean)
    return list(qs[:limit].values())


def get_disclosure_summary(symbol, days=90):
    """Summarize insider activity for a stock."""
    clean = symbol.replace(".NS", "").replace(".BO", "")
    cutoff = now_ist().date() - timedelta(days=days)
    disclosures = PublicDisclosure.objects.filter(
        symbol__icontains=clean, transaction_date__gte=cutoff
    )

    buys = disclosures.filter(transaction_type="BUY")
    sells = disclosures.filter(transaction_type="SELL")

    return {
        "symbol": symbol,
        "period_days": days,
        "total_disclosures": disclosures.count(),
        "total_buys": buys.count(),
        "total_sells": sells.count(),
        "buy_value": sum(float(d.value_inr or 0) for d in buys),
        "sell_value": sum(float(d.value_inr or 0) for d in sells),
        "net_sentiment": "BULLISH" if buys.count() > sells.count() else (
            "BEARISH" if sells.count() > buys.count() else "NEUTRAL"
        ),
        "recent": list(disclosures[:10].values(
            "filer_name", "transaction_type", "transaction_date", "quantity", "value_inr"
        )),
    }

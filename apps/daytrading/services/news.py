"""Skill 2: Trader News — Indian market news, sentiment, catalysts.

Sources: Yahoo Finance RSS, BSE announcements (public).
Never fabricates news. Always includes source URL references.
"""

import logging
import hashlib
import time as time_mod
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import feedparser
import requests

from apps.daytrading.models import NewsItem
from .market_calendar import now_ist, IST

logger = logging.getLogger(__name__)


def _hash_headline(headline):
    return hashlib.md5(headline.strip().lower().encode()).hexdigest()[:16]


def fetch_yahoo_india_news(symbol=None, limit=20):
    """Fetch news from Yahoo Finance RSS for Indian market."""
    items = []
    try:
        if symbol:
            clean = symbol.replace(".NS", "").replace(".BO", "")
            url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={clean}.NS&region=IN&lang=en-IN"
        else:
            url = "https://feeds.finance.yahoo.com/rss/2.0/headline?region=IN&lang=en-IN"
        feed = feedparser.parse(url)
        for entry in feed.entries[:limit]:
            pub_dt = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_dt = datetime.fromtimestamp(time_mod.mktime(entry.published_parsed), tz=IST)
            items.append({
                "headline": entry.get("title", ""), "summary": entry.get("summary", ""),
                "url": entry.get("link", ""), "source": "YAHOO",
                "published_at": pub_dt, "symbols": [symbol] if symbol else [],
            })
    except Exception as e:
        logger.error(f"Yahoo news fetch failed: {e}")
    return items


def fetch_bse_announcements(scrip_code=None, limit=20):
    """Fetch recent BSE corporate announcements (publicly available)."""
    items = []
    try:
        url = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"
        params = {
            "pageno": "1", "strCat": "-1",
            "strPrevDate": (now_ist() - timedelta(days=7)).strftime("%Y%m%d"),
            "strScrip": scrip_code or "", "strSearch": "P",
            "strToDate": now_ist().strftime("%Y%m%d"), "strType": "C",
        }
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bseindia.com/"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and "Table" in data:
                for ann in data["Table"][:limit]:
                    items.append({
                        "headline": ann.get("HEADLINE", ann.get("NEWSSUB", "")),
                        "summary": ann.get("NEWS_DT", ""),
                        "url": f"https://www.bseindia.com/xml-data/corpfiling/AttachHis/{ann.get('ATTACHMENTNAME', '')}",
                        "source": "BSE", "published_at": None,
                        "symbols": [scrip_code] if scrip_code else [],
                        "is_catalyst": "result" in ann.get("HEADLINE", "").lower() or "dividend" in ann.get("HEADLINE", "").lower(),
                    })
    except Exception as e:
        logger.warning(f"BSE announcements fetch failed: {e}")
    return items


def simple_sentiment(text):
    """Rule-based sentiment scoring (no LLM). Returns (label, score)."""
    text_lower = text.lower()
    pos_words = ["surge", "rally", "gains", "profit", "growth", "bullish", "upgrade",
                 "beat", "outperform", "record", "high", "strong", "positive",
                 "dividend", "buyback", "bonus", "approval", "cleared"]
    neg_words = ["fall", "drop", "loss", "decline", "bearish", "downgrade",
                 "miss", "underperform", "low", "weak", "negative", "fraud",
                 "penalty", "default", "crash", "sell-off"]
    pos_count = sum(1 for w in pos_words if w in text_lower)
    neg_count = sum(1 for w in neg_words if w in text_lower)
    total = pos_count + neg_count
    if total == 0:
        return ("NEUTRAL", 0.0)
    score = (pos_count - neg_count) / total
    if score > 0.2:
        return ("POSITIVE", round(score, 2))
    elif score < -0.2:
        return ("NEGATIVE", round(score, 2))
    return ("NEUTRAL", round(score, 2))


def fetch_and_store_news(symbol=None):
    """Fetch news from all sources and persist to DB."""
    all_news = fetch_yahoo_india_news(symbol) + fetch_bse_announcements()
    stored = []
    for item in all_news:
        headline = item.get("headline", "")
        if not headline:
            continue
        news_id = _hash_headline(headline)
        sentiment_label, sentiment_score = simple_sentiment(headline + " " + item.get("summary", ""))
        try:
            obj, created = NewsItem.objects.update_or_create(
                news_id=news_id,
                defaults={
                    "headline": headline[:500], "summary": item.get("summary", "")[:2000],
                    "url": item.get("url", ""), "source": item.get("source", "OTHER"),
                    "symbols": item.get("symbols", []), "sentiment": sentiment_label,
                    "sentiment_score": sentiment_score, "is_catalyst": item.get("is_catalyst", False),
                    "published_at": item.get("published_at"),
                }
            )
            stored.append({"news_id": news_id, "headline": headline, "sentiment": sentiment_label, "created": created})
        except Exception as e:
            logger.warning(f"Failed to store news: {e}")
    return stored


def get_recent_news(symbol=None, limit=20):
    """Get recent news from DB, optionally filtered by symbol."""
    qs = NewsItem.objects.all()
    if symbol:
        qs = qs.filter(symbols__contains=[symbol])
    return list(qs[:limit].values())

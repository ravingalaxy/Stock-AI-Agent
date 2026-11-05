import os
import time
import requests
import feedparser
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

from src.utils.logger import logger
from src.utils.validators import clean_ticker_display
from src.utils.helpers import parse_date


# RSS Feed Sources for Indian Markets (verified 200 OK endpoints)
RSS_FEEDS = {
    "moneycontrol": "https://www.moneycontrol.com/rss/latestnews.xml",
    "economic_times": "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
    "business_standard": "https://www.business-standard.com/rss/latest.rss",
    "livemint": "https://www.livemint.com/rss/markets",
    "financial_express": "https://www.financialexpress.com/market/rss",
}

# Sector/General feeds
SECTOR_FEEDS = {
    "banking": "https://www.moneycontrol.com/rss/banking.xml",
    "technology": "https://www.moneycontrol.com/rss/technology.xml",
    "pharma": "https://www.moneycontrol.com/rss/pharma.xml",
    "auto": "https://www.moneycontrol.com/rss/auto.xml",
    "fmcg": "https://www.moneycontrol.com/rss/fmcg.xml",
}

# Module-level high-performance in-memory RSS cache
_rss_feed_cache: Dict[str, Any] = {
    "articles": [],
    "last_fetched": 0.0,
}


class NewsCollector:
    """Collects and processes financial news from multiple sources with high-speed caching."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        self.config = None
        self._news_offline = False
        
    def _get_config(self):
        if self.config is None:
            from src.config import get_config
            self.config = get_config()
        return self.config
    
    def fetch_rss_feed(self, url: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Parse RSS feed safely with strict timeout."""
        if getattr(self, "_news_offline", False):
            return []
        articles = []
        try:
            # Use requests with strict timeout instead of un-timeouted feedparser
            resp = self.session.get(url, timeout=3.5)
            if resp.status_code != 200:
                return []
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:limit]:
                pub_date = datetime.utcnow()
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])
                    
                summary = entry.get("summary", "")
                if summary:
                    soup = BeautifulSoup(summary, "html.parser")
                    summary = soup.get_text()[:500]
                    
                articles.append({
                    "title": entry.get("title", "").strip(),
                    "url": entry.get("link", "").strip(),
                    "publisher": feed.feed.get("title", "Unknown"),
                    "published_at": pub_date,
                    "summary": summary,
                })
        except Exception as e:
            logger.debug(f"Failed to parse RSS {url}: {e}")
        return articles

    def _get_cached_general_news(self, ttl: int = 900) -> List[Dict[str, Any]]:
        """Fetches or reuses cached general market RSS feeds (15-min TTL).
        
        Uses parallel concurrent fetching to download all feeds in < 2.5 seconds total.
        """
        now = time.time()
        if _rss_feed_cache["articles"] and (now - _rss_feed_cache["last_fetched"] < ttl):
            return _rss_feed_cache["articles"]

        all_articles = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_name = {
                executor.submit(self.fetch_rss_feed, feed_url, 40): name
                for name, feed_url in RSS_FEEDS.items()
            }
            for future in as_completed(future_to_name, timeout=6.0):
                try:
                    res = future.result()
                    if res:
                        all_articles.extend(res)
                except Exception:
                    pass

        # Deduplicate
        seen = set()
        unique = []
        for a in all_articles:
            if a["url"] and a["url"] not in seen:
                seen.add(a["url"])
                unique.append(a)

        if unique:
            _rss_feed_cache["articles"] = unique
            _rss_feed_cache["last_fetched"] = now
            logger.info(f"Cached {len(unique)} market news articles across {len(RSS_FEEDS)} RSS feeds.")

        return _rss_feed_cache["articles"]
    
    def fetch_google_news(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        """Fetch news from Google News RSS for a specific query."""
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
        return self.fetch_rss_feed(url, limit)
    
    def fetch_company_news(self, symbol: str, company_name: str, days: int = 30, limit: int = 15) -> List[Dict[str, Any]]:
        """Fetch news specific to a company using fast cache and targeted fallback."""
        all_articles = []
        clean_name = clean_ticker_display(symbol)
        
        # 1. Filter fast cached general RSS articles in-memory (0ms)
        cached_articles = self._get_cached_general_news()
        c_clean = clean_name.lower()
        c_comp = company_name.lower().replace(" limited", "").replace(" ltd", "").strip()
        
        for art in cached_articles:
            text = (art["title"] + " " + art.get("summary", "")).lower()
            if c_clean in text or (len(c_comp) >= 4 and c_comp in text):
                all_articles.append(art)
                
        # 2. Targeted Google News search only if needed
        if len(all_articles) < 5:
            q = f"{clean_name} {c_comp} stock"
            articles = self.fetch_google_news(q, limit=6)
            all_articles.extend(articles)
            
        # Deduplicate by URL
        seen = set()
        unique = []
        for art in all_articles:
            if art["url"] not in seen:
                seen.add(art["url"])
                unique.append(art)
                
        # Sort by date descending
        unique.sort(key=lambda x: x["published_at"], reverse=True)
        
        # Filter by date
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [a for a in unique if a["published_at"] >= cutoff]
        
        return recent[:limit]
    
    def fetch_sector_news(self, sector: str, days: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch sector-specific news."""
        all_articles = []
        
        sector_key = sector.lower().replace(" ", "_").replace("&", "")
        if sector_key in SECTOR_FEEDS:
            all_articles.extend(self.fetch_rss_feed(SECTOR_FEEDS[sector_key], limit=30))
            
        all_articles.extend(self.fetch_google_news(f"{sector} sector India stocks", limit=10))
        
        seen = set()
        unique = []
        for art in all_articles:
            if art["url"] not in seen:
                seen.add(art["url"])
                unique.append(art)
                
        unique.sort(key=lambda x: x["published_at"], reverse=True)
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [a for a in unique if a["published_at"] >= cutoff][:limit]


# Simple sentiment dictionary for financial text
POSITIVE_WORDS = {
    "growth", "profit", "surge", "gain", "rise", "jump", "record", "strong", 
    "bullish", "upgrade", "outperform", "buy", "expansion", "positive", "dividend",
    "rally", "beat", "exceed", "high", "order", "contract", "breakthrough"
}

NEGATIVE_WORDS = {
    "loss", "fall", "drop", "plunge", "decline", "weak", "bearish", "downgrade",
    "underperform", "sell", "debt", "risk", "warning", "probe", "investigation",
    "penalty", "fraud", "default", "crisis", "cut", "slump", "miss"
}

EVENT_KEYWORDS = {
    "earnings": ["earnings", "q1", "q2", "q3", "q4", "quarterly", "results", "financial results"],
    "management": ["ceo", "cfo", "director", "board", "management", "leadership", "resigns", "appoints"],
    "regulatory": ["sebi", "rbi", "government", "policy", "fine", "penalty", "investigation", "compliance"],
    "deal": ["acquisition", "merger", "joint venture", "order", "contract", "partnership", "expansion"],
    "macro": ["inflation", "interest rate", "gdp", "budget", "crude", "rupee", "fed", "monetary policy"],
    "corporate_action": ["bonus", "dividend", "split", "buyback", "rights issue"],
}


def score_text_sentiment(text: str) -> float:
    """Simple dictionary-based sentiment scoring [-1.0, 1.0]."""
    text_lower = text.lower()
    words = set(re.findall(r'\b[a-z]+\b', text_lower))
    
    pos_count = len(words.intersection(POSITIVE_WORDS))
    neg_count = len(words.intersection(NEGATIVE_WORDS))
    
    total = pos_count + neg_count
    if total == 0:
        return 0.0
        
    return round((pos_count - neg_count) / total, 3)


def detect_events(text: str) -> List[str]:
    """Detect event types mentioned in text."""
    text_lower = text.lower()
    detected = []
    
    for event_type, keywords in EVENT_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            detected.append(event_type)
            
    return detected


def score_relevance(text: str, symbol: str, company_name: str) -> float:
    """Score article relevance to the target company [0.0, 1.0]."""
    text_lower = text.lower()
    clean_sym = clean_ticker_display(symbol).lower()
    comp_lower = company_name.lower()
    
    # Check title vs body
    relevance = 0.0
    
    # Direct symbol match
    if re.search(rf'\b{clean_sym}\b', text_lower):
        relevance += 0.5
        
    # Company name match
    if comp_lower in text_lower:
        relevance += 0.5
    else:
        # Partial company name (first word if significant)
        first_word = comp_lower.split()[0]
        if len(first_word) > 3 and first_word in text_lower:
            relevance += 0.25
            
    return min(relevance, 1.0)


def process_raw_articles(
    articles: List[Dict[str, Any]], 
    symbol: str, 
    company_name: str
) -> List[Dict[str, Any]]:
    """Enrich raw articles with sentiment, events, and relevance scores."""
    processed = []
    
    for art in articles:
        combined_text = f"{art.get('title', '')} {art.get('summary', '')}"
        
        sentiment = score_text_sentiment(combined_text)
        events = detect_events(combined_text)
        relevance = score_relevance(combined_text, symbol, company_name)
        
        enriched = {
            **art,
            "sentiment_score": sentiment,
            "events": events,
            "relevance_score": relevance,
            "processed_at": datetime.utcnow(),
        }
        processed.append(enriched)
        
    return processed


def collect_news_for_symbol(
    symbol: str, 
    company_name: str, 
    days: int = 30, 
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Main entry point to collect and process news for a symbol."""
    collector = NewsCollector()
    raw = collector.fetch_company_news(symbol, company_name, days=days, limit=limit)
    return process_raw_articles(raw, symbol, company_name)

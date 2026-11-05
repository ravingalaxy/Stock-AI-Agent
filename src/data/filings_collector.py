"""Corporate Filings and Disclosures Collector for NSE/BSE announcements."""

import requests
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from src.utils.logger import logger
from src.utils.validators import normalize_ticker, clean_ticker_display
from src.utils.helpers import parse_date


# NSE/BSE Corporate Announcements endpoints
NSE_ANNOUNCEMENTS_API = "https://www.nseindia.com/api/corporate-announcements"
BSE_ANNOUNCEMENTS_URL = "https://www.bseindia.com/corporates/ann.html"


class FilingsCollector:
    """Collects corporate announcements, shareholding patterns, and investor presentations."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "en-US,en;q=0.9",
        })
        self._nse_offline = False
        self._init_nse_session()
        
    def _init_nse_session(self):
        """Initialize NSE session with required cookies."""
        try:
            self.session.get("https://www.nseindia.com", timeout=2)
        except Exception as e:
            self._nse_offline = True
            logger.debug(f"NSE session init failed: {e}")
            
    def fetch_nse_announcements(self, symbol: str, days: int = 90, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch corporate announcements from NSE."""
        if getattr(self, "_nse_offline", False):
            return []
        clean_sym = clean_ticker_display(symbol)
        params = {
            "index": "equities",
            "symbol": clean_sym,
            "from_date": (datetime.now() - timedelta(days=days)).strftime("%d-%m-%Y"),
            "to_date": datetime.now().strftime("%d-%m-%Y"),
        }
        
        try:
            resp = self.session.get(NSE_ANNOUNCEMENTS_API, params=params, timeout=2)
            if resp.status_code != 200:
                logger.warning(f"NSE announcements API returned {resp.status_code}")
                return []
                
            data = resp.json()
            announcements = []
            
            # Handle different response formats
            items = []
            if isinstance(data, dict) and "data" in data:
                items = data["data"]
            elif isinstance(data, list):
                items = data
            else:
                logger.warning(f"Unexpected NSE announcements response format: {type(data)}")
                return []
            
            for item in items[:limit]:
                # Handle case where item might be a list or dict
                if not isinstance(item, dict):
                    continue
                    
                # Parse NSE announcement format
                ann = {
                    "symbol": symbol,
                    "source": "NSE",
                    "subject": item.get("subject", ""),
                    "description": item.get("desc", ""),
                    "attachment_url": item.get("attachmntFile", ""),
                    "published_at": parse_date(item.get("dt", "")),
                    "category": item.get("category", ""),
                }
                announcements.append(ann)
                
            return announcements
            
        except Exception as e:
            logger.warning(f"NSE announcements fetch failed for {symbol}: {e}")
            return []
    
    def fetch_bse_announcements(self, symbol: str, days: int = 90, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch corporate announcements from BSE (HTML scraping)."""
        # BSE uses scrip code, not symbol. This is a simplified approach.
        # In production, maintain a symbol->scrip_code mapping.
        clean_sym = clean_ticker_display(symbol)
        
        params = {
            "scrip_cd": "",  # Would need mapping
            "strDate": (datetime.now() - timedelta(days=days)).strftime("%d/%m/%Y"),
            "endDate": datetime.now().strftime("%d/%m/%Y"),
        }
        
        # Note: BSE scraping is more complex due to scrip codes.
        # This is a placeholder for the interface.
        logger.info(f"BSE announcements fetch not fully implemented for {symbol} (requires scrip code mapping)")
        return []
    
    def fetch_shareholding_pattern(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch latest shareholding pattern from NSE."""
        if getattr(self, "_nse_offline", False):
            return None
        clean_sym = clean_ticker_display(symbol)
        url = f"https://www.nseindia.com/api/shareholding-pattern?symbol={clean_sym}"
        try:
            resp = self.session.get(url, timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                return self._parse_shareholding(data)
        except Exception as e:
            self._nse_offline = True
            logger.debug(f"Shareholding fetch failed for {symbol}: {e}")
        return None
    
    def _parse_shareholding(self, data: Dict) -> Dict[str, Any]:
        """Parse NSE shareholding pattern response."""
        try:
            # NSE returns data in specific format
            # This is a simplified parser
            result = {
                "promoter_holding_pct": 0,
                "promoter_pledged_pct": 0,
                "fii_holding_pct": 0,
                "dii_holding_pct": 0,
                "public_holding_pct": 0,
                "raw_data": data
            }
            
            # Extract from typical NSE response structure
            if "data" in data:
                for cat in data["data"]:
                    cat_name = cat.get("category", "").lower()
                    if "promoter" in cat_name and "pledge" not in cat_name:
                        result["promoter_holding_pct"] = float(cat.get("percentage", 0))
                    elif "pledge" in cat_name:
                        result["promoter_pledged_pct"] = float(cat.get("percentage", 0))
                    elif "fii" in cat_name or "foreign" in cat_name:
                        result["fii_holding_pct"] = float(cat.get("percentage", 0))
                    elif "dii" in cat_name or "domestic" in cat_name:
                        result["dii_holding_pct"] = float(cat.get("percentage", 0))
                    elif "public" in cat_name:
                        result["public_holding_pct"] = float(cat.get("percentage", 0))
                        
            return result
        except Exception as e:
            logger.warning(f"Shareholding parse error: {e}")
            return {}
    
    def fetch_investor_presentations(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch investor presentations/transcripts."""
        # Search NSE announcements for presentations
        announcements = self.fetch_nse_announcements(symbol, days=180, limit=100)
        
        presentations = []
        keywords = ["presentation", "transcript", "investor meet", "analyst meet", "concall"]
        
        for ann in announcements:
            text = (ann.get("subject", "") + " " + ann.get("description", "")).lower()
            if any(kw in text for kw in keywords):
                presentations.append({
                    "symbol": symbol,
                    "title": ann.get("subject"),
                    "url": ann.get("attachment_url"),
                    "date": ann.get("published_at"),
                    "type": "presentation" if "presentation" in text else "transcript",
                })
                
        return presentations[:limit]
    
    def fetch_all_filings(self, symbol: str, days: int = 90) -> Dict[str, Any]:
        """Fetch all available filings for a symbol."""
        logger.info(f"Fetching filings for {symbol}...")
        
        nse_anns = self.fetch_nse_announcements(symbol, days=days)
        shareholding = self.fetch_shareholding_pattern(symbol)
        presentations = self.fetch_investor_presentations(symbol)
        
        # Categorize announcements
        categorized = self._categorize_announcements(nse_anns)
        
        return {
            "symbol": symbol,
            "announcements": nse_anns,
            "categorized": categorized,
            "shareholding": shareholding,
            "presentations": presentations,
            "fetched_at": datetime.utcnow(),
        }
    
    def _categorize_announcements(self, announcements: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize announcements by type."""
        categories = {
            "financial_results": [],
            "board_meeting": [],
            "dividend": [],
            "corporate_action": [],
            "management_change": [],
            "regulatory": [],
            "related_party": [],
            "other": [],
        }
        
        for ann in announcements:
            text = (ann.get("subject", "") + " " + ann.get("description", "")).lower()
            
            if any(kw in text for kw in ["result", "financial", "quarterly", "audited", "unaudited"]):
                categories["financial_results"].append(ann)
            elif any(kw in text for kw in ["board meeting", "board of director"]):
                categories["board_meeting"].append(ann)
            elif any(kw in text for kw in ["dividend", "interim dividend", "final dividend"]):
                categories["dividend"].append(ann)
            elif any(kw in text for kw in ["bonus", "split", "buyback", "rights issue", "preferential"]):
                categories["corporate_action"].append(ann)
            elif any(kw in text for kw in ["ceo", "cfo", "director", "chairman", "resignation", "appointment", "key managerial"]):
                categories["management_change"].append(ann)
            elif any(kw in text for kw in ["sebi", "stock exchange", "compliance", "regulation", "penalty", "show cause"]):
                categories["regulatory"].append(ann)
            elif any(kw in text for kw in ["related party", "rp transaction", "rpt"]):
                categories["related_party"].append(ann)
            else:
                categories["other"].append(ann)
                
        return categories


_filings_collector_instance: Optional["FilingsCollector"] = None

def get_filings_collector() -> "FilingsCollector":
    """Singleton instance for filings collector to preserve session and avoid repeated timeouts."""
    global _filings_collector_instance
    if _filings_collector_instance is None:
        _filings_collector_instance = FilingsCollector()
    return _filings_collector_instance


def collect_filings_for_symbol(symbol: str, days: int = 90) -> Dict[str, Any]:
    """Main entry point to collect all filings for a symbol."""
    collector = get_filings_collector()
    return collector.fetch_all_filings(symbol, days=days)
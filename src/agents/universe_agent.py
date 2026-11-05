"""Universe Screener Agent - Filters liquid, tradeable stocks."""

from typing import List, Dict, Any, Optional
from datetime import date

from src.utils.logger import logger
from src.utils.validators import normalize_ticker, validate_ticker_list
from src.data.market_data import get_market_data_provider, screen_symbols
from src.storage.database import StockRepository
from src.config import get_config


# Nifty 500 and BSE 500 symbol lists (subset for demo - in production load from CSV/API)
NIFTY_500_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "HINDUNILVR", "ITC", "SBIN",
    "BHARTIARTL", "BAJFINANCE", "KOTAKBANK", "LT", "AXISBANK", "ASIANPAINT", "MARUTI",
    "SUNPHARMA", "TITAN", "ULTRACEMCO", "WIPRO", "NESTLEIND", "POWERGRID", "NTPC",
    "ONGC", "COALINDIA", "TMCV", "TMPV", "TATASTEEL", "JSWSTEEL", "HINDALCO", "ADANIENT",
    "ADANIPORTS", "BAJAJFINSV", "HCLTECH", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP",
    "TECHM", "BPCL", "GRASIM", "BRITANNIA", "EICHERMOT", "HEROMOTOCO", "BAJAJ-AUTO",
    "M&M", "TATACONSUM", "INDUSINDBK", "SBILIFE", "HDFCLIFE", "SHREECEM", "UPL",
    "GODREJCP", "PIDILITIND", "DABUR", "MARICO", "COLPAL", "BERGEPAINT", "HAVELLS",
    "VOLTAS", "WHIRLPOOL", "BLUEDART", "CONCOR", "IRCTC", "NAUKRI", "ZOMATO",
    "PAYTM", "NYKAA", "POLICYBZR", "CARTRADE", "EASEMYTRIP", "MAPMYINDIA"
]

BSE_500_SYMBOLS = NIFTY_500_SYMBOLS  # Overlap significantly; in production load actual BSE 500


class UniverseAgent:
    """Screens and builds the investable universe of stocks."""
    
    def __init__(self, repo: StockRepository):
        self.repo = repo
        self.md_provider = get_market_data_provider()
        self.config = get_config()
        
    def build_universe(
        self, 
        index: str = "nifty500", 
        custom_symbols: Optional[List[str]] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Build filtered universe from index or custom list."""
        
        # Get base symbol list
        if custom_symbols:
            base_symbols = validate_ticker_list(custom_symbols)
            source = "custom"
        elif index.lower() == "nifty500":
            base_symbols = [normalize_ticker(s) for s in NIFTY_500_SYMBOLS]
            source = "nifty500"
        elif index.lower() == "bse500":
            base_symbols = [normalize_ticker(s) for s in BSE_500_SYMBOLS]
            source = "bse500"
        else:
            raise ValueError(f"Unknown index: {index}")
            
        logger.info(f"Building universe from {source}: {len(base_symbols)} symbols")
        
        # Apply screening criteria
        criteria = {
            "min_market_cap_cr": self.config.screening_defaults.min_market_cap_cr,
            "min_avg_daily_volume": self.config.screening_defaults.min_avg_daily_volume,
            "min_share_price": self.config.screening_defaults.min_share_price,
        }
        
        # Screen for liquidity and size
        passed_symbols = screen_symbols(base_symbols, criteria)
        
        # Get/update stock metadata in database
        universe_stocks = []
        excluded = []
        
        for sym in passed_symbols:
            try:
                info = self.md_provider.get_company_info(sym)
                if not info:
                    stock_rec = self.repo.get_stock(sym)
                    if stock_rec:
                        info = {
                            "name": stock_rec.name,
                            "sector": stock_rec.sector,
                            "industry": stock_rec.industry,
                            "market_cap": stock_rec.market_cap,
                            "exchange": stock_rec.exchange
                        }
                    else:
                        clean = sym.replace(".NS", "").replace(".BO", "")
                        info = {
                            "name": clean,
                            "sector": "Diversified",
                            "industry": "General",
                            "market_cap": 50000000000.0,
                            "exchange": "NSE" if sym.endswith(".NS") else "BSE"
                        }
                stock = self.repo.upsert_stock(
                    symbol=sym,
                    name=info.get("name"),
                    sector=info.get("sector"),
                    industry=info.get("industry"),
                    market_cap=info.get("market_cap"),
                    exchange="NSE" if sym.endswith(".NS") else "BSE",
                    is_active=True
                )
                universe_stocks.append({
                    "symbol": sym,
                    "name": stock.name,
                    "sector": stock.sector,
                    "market_cap": stock.market_cap,
                    "exchange": stock.exchange
                })
            except Exception as e:
                excluded.append({"symbol": sym, "reason": str(e)})
                
        result = {
            "source": source,
            "total_input": len(base_symbols),
            "passed_screening": len(passed_symbols),
            "final_universe": len(universe_stocks),
            "excluded": excluded,
            "stocks": universe_stocks,
            "screening_criteria": criteria,
            "generated_at": date.today().isoformat()
        }
        
        logger.info(f"Universe built: {result['final_universe']} stocks passed screening")
        return result
    
    def get_universe_symbols(self, index: str = "nifty500") -> List[str]:
        """Get just the symbols for the current universe."""
        result = self.build_universe(index)
        symbols = [s["symbol"] for s in result["stocks"]]
        if not symbols:
            if index.lower() == "bse500":
                return [normalize_ticker(s) for s in BSE_500_SYMBOLS]
            return [normalize_ticker(s) for s in NIFTY_500_SYMBOLS]
        return symbols
    
    def filter_universe(
        self, 
        symbols: List[str], 
        sector: Optional[str] = None,
        min_market_cap_cr: Optional[float] = None,
        max_market_cap_cr: Optional[float] = None,
        min_liquidity_score: Optional[float] = None
    ) -> List[str]:
        """Apply additional filters to an existing universe."""
        filtered = []
        
        for sym in symbols:
            stock = self.repo.get_stock(sym)
            if not stock or not stock.is_active:
                continue
                
            if sector and stock.sector and sector.lower() not in stock.sector.lower():
                continue
                
            if min_market_cap_cr and stock.market_cap:
                if stock.market_cap < min_market_cap_cr * 10_000_000:
                    continue
                    
            if max_market_cap_cr and stock.market_cap:
                if stock.market_cap > max_market_cap_cr * 10_000_000:
                    continue
                    
            filtered.append(sym)
            
        return filtered
"""SQLite Database Models and Repository using SQLAlchemy 2.0."""

from datetime import datetime, date
from typing import List, Optional, Any
from decimal import Decimal

from sqlalchemy import (
    create_engine, Column, String, Float, Integer, DateTime, Date, Text, ForeignKey, 
    UniqueConstraint, Index, func, select, delete, event
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column, relationship, Session

from src.utils.logger import logger
from src.utils.validators import normalize_ticker


class Base(DeclarativeBase):
    pass


# --- ORM Models ---

class Stock(Base):
    __tablename__ = "stocks"
    
    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)  # e.g., RELIANCE.NS
    name: Mapped[Optional[str]] = mapped_column(String(200))
    isin: Mapped[Optional[str]] = mapped_column(String(12))
    exchange: Mapped[str] = mapped_column(String(5))  # NSE / BSE
    sector: Mapped[Optional[str]] = mapped_column(String(100))
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    market_cap: Mapped[Optional[float]] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prices: Mapped[List["PriceHistory"]] = relationship(back_populates="stock", lazy="dynamic")
    fundamentals: Mapped[List["FundamentalData"]] = relationship(back_populates="stock", lazy="dynamic")
    news: Mapped[List["NewsArticle"]] = relationship(back_populates="stock", lazy="dynamic")
    evaluations: Mapped[List["AgentEvaluation"]] = relationship(back_populates="stock", lazy="dynamic")


class PriceHistory(Base):
    __tablename__ = "price_history"
    
    symbol: Mapped[str] = mapped_column(String(20), ForeignKey("stocks.symbol"), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    open: Mapped[Optional[float]] = mapped_column(Float)
    high: Mapped[Optional[float]] = mapped_column(Float)
    low: Mapped[Optional[float]] = mapped_column(Float)
    close: Mapped[Optional[float]] = mapped_column(Float)
    adj_close: Mapped[Optional[float]] = mapped_column(Float)
    volume: Mapped[Optional[int]] = mapped_column(Integer)
    
    stock: Mapped["Stock"] = relationship(back_populates="prices")


class FundamentalData(Base):
    __tablename__ = "fundamentals"
    
    symbol: Mapped[str] = mapped_column(String(20), ForeignKey("stocks.symbol"), primary_key=True)
    period_date: Mapped[date] = mapped_column(Date, primary_key=True)  # Quarter/Year end date
    period_type: Mapped[str] = mapped_column(String(10), primary_key=True, default="Q")  # Q / A
    
    # Income Statement
    revenue: Mapped[Optional[float]] = mapped_column(Float)
    net_profit: Mapped[Optional[float]] = mapped_column(Float)
    ebitda: Mapped[Optional[float]] = mapped_column(Float)
    operating_profit: Mapped[Optional[float]] = mapped_column(Float)
    
    # Margins
    operating_margin: Mapped[Optional[float]] = mapped_column(Float)
    net_margin: Mapped[Optional[float]] = mapped_column(Float)
    
    # Returns
    roe: Mapped[Optional[float]] = mapped_column(Float)
    roce: Mapped[Optional[float]] = mapped_column(Float)
    
    # Leverage & Solvency
    debt_to_equity: Mapped[Optional[float]] = mapped_column(Float)
    interest_coverage: Mapped[Optional[float]] = mapped_column(Float)
    
    # Cash Flow
    fcf: Mapped[Optional[float]] = mapped_column(Float)
    cfo: Mapped[Optional[float]] = mapped_column(Float)
    
    # Shareholding
    promoter_holding_pct: Mapped[Optional[float]] = mapped_column(Float)
    promoter_pledged_pct: Mapped[Optional[float]] = mapped_column(Float)
    
    # Valuation (Point in Time)
    pe_ratio: Mapped[Optional[float]] = mapped_column(Float)
    pb_ratio: Mapped[Optional[float]] = mapped_column(Float)
    ev_ebitda: Mapped[Optional[float]] = mapped_column(Float)
    ps_ratio: Mapped[Optional[float]] = mapped_column(Float)
    dividend_yield: Mapped[Optional[float]] = mapped_column(Float)
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    stock: Mapped["Stock"] = relationship(back_populates="fundamentals")


class NewsArticle(Base):
    __tablename__ = "news_articles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), ForeignKey("stocks.symbol"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(500))
    publisher: Mapped[Optional[str]] = mapped_column(String(100))
    published_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float)  # -1 to 1
    relevance_score: Mapped[Optional[float]] = mapped_column(Float)  # 0 to 1
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    stock: Mapped["Stock"] = relationship(back_populates="news")


class AgentEvaluation(Base):
    __tablename__ = "agent_evaluations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), ForeignKey("stocks.symbol"), index=True)
    evaluation_date: Mapped[date] = mapped_column(Date, index=True)
    
    composite_score: Mapped[float] = mapped_column(Float)
    quality_score: Mapped[float] = mapped_column(Float)
    growth_score: Mapped[float] = mapped_column(Float)
    valuation_score: Mapped[float] = mapped_column(Float)
    momentum_score: Mapped[float] = mapped_column(Float)
    catalyst_score: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[float] = mapped_column(Float)
    rank: Mapped[Optional[int]] = mapped_column(Integer)
    
    thesis: Mapped[Optional[str]] = mapped_column(Text)
    bull_case: Mapped[Optional[str]] = mapped_column(Text)  # JSON array
    bear_case: Mapped[Optional[str]] = mapped_column(Text)  # JSON array
    catalysts: Mapped[Optional[str]] = mapped_column(Text)  # JSON array
    risks: Mapped[Optional[str]] = mapped_column(Text)      # JSON array
    invalidation_conditions: Mapped[Optional[str]] = mapped_column(Text)  # JSON array
    citations: Mapped[Optional[str]] = mapped_column(Text)  # JSON array
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    stock: Mapped["Stock"] = relationship(back_populates="evaluations")
    
    # Unique constraint to prevent duplicate evaluations for same symbol on same date
    __table_args__ = (
        UniqueConstraint("symbol", "evaluation_date", name="uq_symbol_eval_date"),
    )


class BacktestRun(Base):
    __tablename__ = "backtest_runs"
    
    run_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    strategy_name: Mapped[str] = mapped_column(String(100))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    rebalance_frequency: Mapped[str] = mapped_column(String(2))
    initial_capital: Mapped[float] = mapped_column(Float)
    
    # Results
    cagr: Mapped[Optional[float]] = mapped_column(Float)
    volatility: Mapped[Optional[float]] = mapped_column(Float)
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(Float)
    max_drawdown: Mapped[Optional[float]] = mapped_column(Float)
    win_rate: Mapped[Optional[float]] = mapped_column(Float)
    benchmark_cagr: Mapped[Optional[float]] = mapped_column(Float)
    
    metrics_json: Mapped[Optional[str]] = mapped_column(Text)
    equity_curve_json: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


# --- Database Manager ---

class DatabaseManager:
    """Manages database connection, schema creation, and session handling."""
    
    def __init__(self, db_url: str = "sqlite:///data/stock_research.db"):
        connect_args = {}
        if "sqlite" in db_url:
            connect_args["timeout"] = 30
        self.engine = create_engine(db_url, echo=False, future=True, connect_args=connect_args)
        if "sqlite" in db_url:
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA busy_timeout=30000")
                cursor.close()
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        
    def init_db(self):
        """Creates all tables."""
        Base.metadata.create_all(self.engine)
        logger.info("Database schema initialized.")
        
    def get_session(self) -> Session:
        """Returns a new database session."""
        return self.SessionLocal()


# --- Repository Layer ---

class StockRepository:
    """CRUD operations for Stocks and related data."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
    def upsert_stock(self, symbol: str, **kwargs) -> Stock:
        """Insert or update a stock record."""
        symbol = normalize_ticker(symbol)
        with self.db.get_session() as session:
            stock = session.get(Stock, symbol)
            if not stock:
                stock = Stock(symbol=symbol)
                session.add(stock)
            
            for key, val in kwargs.items():
                if hasattr(stock, key) and val is not None:
                    setattr(stock, key, val)
            stock.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(stock)
            return stock
            
    def get_stock(self, symbol: str) -> Optional[Stock]:
        symbol = normalize_ticker(symbol)
        with self.db.get_session() as session:
            return session.get(Stock, symbol)
            
    def get_all_active_stocks(self, exchange: Optional[str] = None) -> List[Stock]:
        with self.db.get_session() as session:
            stmt = select(Stock).where(Stock.is_active == True)
            if exchange:
                stmt = stmt.where(Stock.exchange == exchange.upper())
            return list(session.scalars(stmt))
            
    def get_symbols_only(self, exchange: Optional[str] = None) -> List[str]:
        with self.db.get_session() as session:
            stmt = select(Stock.symbol).where(Stock.is_active == True)
            if exchange:
                stmt = stmt.where(Stock.exchange == exchange.upper())
            return list(session.scalars(stmt))

    def bulk_upsert_prices(self, symbol: str, df) -> int:
        """Bulk insert price history from pandas DataFrame."""
        symbol = normalize_ticker(symbol)
        if df is None or df.empty:
            return 0
            
        records = []
        for idx, row in df.iterrows():
            records.append({
                "symbol": symbol,
                "date": idx.date() if hasattr(idx, 'date') else idx,
                "open": float(row.get("Open", 0)) if row.get("Open") else None,
                "high": float(row.get("High", 0)) if row.get("High") else None,
                "low": float(row.get("Low", 0)) if row.get("Low") else None,
                "close": float(row.get("Close", 0)) if row.get("Close") else None,
                "adj_close": float(row.get("Adj Close", 0)) if row.get("Adj Close") else None,
                "volume": int(row.get("Volume", 0)) if row.get("Volume") else None,
            })
        
        if not records:
            return 0
            
        with self.db.get_session() as session:
            # Use upsert logic for SQLite (INSERT OR REPLACE)
            from sqlalchemy.dialects.sqlite import insert as sqlite_insert
            stmt = sqlite_insert(PriceHistory).values(records)
            # Define conflict resolution on PK (symbol, date)
            update_dict = {c.name: getattr(stmt.excluded, c.name) for c in PriceHistory.__table__.columns if c.name not in ("symbol", "date")}
            stmt = stmt.on_conflict_do_update(index_elements=["symbol", "date"], set_=update_dict)
            session.execute(stmt)
            session.commit()
            return len(records)

    def get_price_history(self, symbol: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[PriceHistory]:
        symbol = normalize_ticker(symbol)
        with self.db.get_session() as session:
            stmt = select(PriceHistory).where(PriceHistory.symbol == symbol)
            if start_date:
                stmt = stmt.where(PriceHistory.date >= start_date)
            if end_date:
                stmt = stmt.where(PriceHistory.date <= end_date)
            stmt = stmt.order_by(PriceHistory.date)
            return list(session.scalars(stmt))

    def upsert_fundamentals(self, symbol: str, data: dict) -> FundamentalData:
        symbol = normalize_ticker(symbol)
        period_date = data.get("period_date") or date.today()
        data["period_date"] = period_date
        period_type = data.get("period_type", "Q")
        
        with self.db.get_session() as session:
            stmt = select(FundamentalData).where(
                FundamentalData.symbol == symbol,
                FundamentalData.period_date == period_date,
                FundamentalData.period_type == period_type
            )
            fund = session.scalar(stmt)
            if not fund:
                fund = FundamentalData(symbol=symbol, period_date=period_date, period_type=period_type)
                session.add(fund)
            
            for key, val in data.items():
                if hasattr(fund, key) and val is not None:
                    setattr(fund, key, val)
            session.commit()
            session.refresh(fund)
            return fund

    def get_latest_fundamentals(self, symbol: str) -> Optional[FundamentalData]:
        symbol = normalize_ticker(symbol)
        with self.db.get_session() as session:
            stmt = (
                select(FundamentalData)
                .where(FundamentalData.symbol == symbol)
                .order_by(FundamentalData.period_date.desc())
                .limit(1)
            )
            return session.scalar(stmt)

    def get_fundamentals_history(self, symbol: str, limit: int = 12) -> List[FundamentalData]:
        symbol = normalize_ticker(symbol)
        with self.db.get_session() as session:
            stmt = (
                select(FundamentalData)
                .where(FundamentalData.symbol == symbol)
                .order_by(FundamentalData.period_date.desc())
                .limit(limit)
            )
            return list(session.scalars(stmt))

    def upsert_news(self, articles: List[dict]) -> int:
        if not articles:
            return 0
        count = 0
        with self.db.get_session() as session:
            for art in articles:
                # Check if URL exists to avoid duplicates
                existing = session.scalar(
                    select(NewsArticle).where(NewsArticle.url == art["url"])
                )
                if existing:
                    continue
                news = NewsArticle(**art)
                session.add(news)
                count += 1
            session.commit()
        return count

    def get_news_for_symbol(self, symbol: str, days: int = 30, limit: int = 50) -> List[NewsArticle]:
        symbol = normalize_ticker(symbol)
        cutoff = datetime.utcnow().date()  # we filter by datetime in python for simplicity
        with self.db.get_session() as session:
            stmt = (
                select(NewsArticle)
                .where(NewsArticle.symbol == symbol)
                .order_by(NewsArticle.published_at.desc())
                .limit(limit)
            )
            return list(session.scalars(stmt))

    def save_evaluation(self, eval_data: dict) -> AgentEvaluation:
        """Insert or update evaluation (upsert) for a symbol on a specific date."""
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        from sqlalchemy import select
        
        with self.db.get_session() as session:
            # Use SQLite upsert (INSERT OR REPLACE on unique constraint)
            stmt = sqlite_insert(AgentEvaluation).values(eval_data)
            # Define conflict resolution on unique constraint (symbol, evaluation_date)
            update_dict = {c.name: getattr(stmt.excluded, c.name) for c in AgentEvaluation.__table__.columns 
                          if c.name not in ("symbol", "evaluation_date", "id", "created_at")}
            # Always update the updated_at timestamp
            update_dict["updated_at"] = datetime.utcnow()
            stmt = stmt.on_conflict_do_update(
                index_elements=["symbol", "evaluation_date"],
                set_=update_dict
            )
            session.execute(stmt)
            session.commit()
            
            # Return the upserted object by querying
            eval_date = eval_data["evaluation_date"]
            symbol = eval_data["symbol"]
            stmt = select(AgentEvaluation).where(
                AgentEvaluation.symbol == symbol,
                AgentEvaluation.evaluation_date == eval_date
            )
            return session.scalar(stmt)

    def get_latest_evaluation(self, symbol: str) -> Optional[AgentEvaluation]:
        symbol = normalize_ticker(symbol)
        with self.db.get_session() as session:
            stmt = (
                select(AgentEvaluation)
                .where(AgentEvaluation.symbol == symbol)
                .order_by(AgentEvaluation.evaluation_date.desc())
                .limit(1)
            )
            return session.scalar(stmt)

    def get_evaluations_by_date(self, eval_date: date) -> List[AgentEvaluation]:
        with self.db.get_session() as session:
            stmt = select(AgentEvaluation).where(AgentEvaluation.evaluation_date == eval_date).order_by(AgentEvaluation.rank)
            return list(session.scalars(stmt))
            
    def save_backtest_run(self, run_data: dict) -> BacktestRun:
        with self.db.get_session() as session:
            run = BacktestRun(**run_data)
            session.add(run)
            session.commit()
            session.refresh(run)
            return run
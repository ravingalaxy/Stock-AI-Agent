"""Sync data from stock_django.db to stock_research.db."""
import sqlite3
import pathlib

django_path = pathlib.Path("data/stock_django.db")
research_path = pathlib.Path("data/stock_research.db")

c_dj = sqlite3.connect(django_path)
c_rs = sqlite3.connect(research_path)

c_dj_cur = c_dj.cursor()
c_rs_cur = c_rs.cursor()

# 1. Sync stocks
c_dj_cur.execute("SELECT symbol, name, isin, exchange, sector, industry, market_cap, is_active, created_at, updated_at FROM market_stock")
stocks = c_dj_cur.fetchall()
for s in stocks:
    c_rs_cur.execute("""
        INSERT INTO stocks (symbol, name, isin, exchange, sector, industry, market_cap, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol) DO UPDATE SET
            name=excluded.name,
            sector=excluded.sector,
            industry=excluded.industry,
            market_cap=excluded.market_cap,
            is_active=excluded.is_active,
            updated_at=excluded.updated_at
    """, s)

print(f"Synced {len(stocks)} stocks.")

# 2. Sync price history
c_dj_cur.execute("SELECT stock_id, date, open, high, low, close, adj_close, volume FROM market_pricehistory")
prices = c_dj_cur.fetchall()
for p in prices:
    c_rs_cur.execute("""
        INSERT INTO price_history (symbol, date, open, high, low, close, adj_close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol, date) DO UPDATE SET
            open=excluded.open,
            high=excluded.high,
            low=excluded.low,
            close=excluded.close,
            adj_close=excluded.adj_close,
            volume=excluded.volume
    """, p)

print(f"Synced {len(prices)} price history records.")

# 3. Clear and re-populate fundamentals
c_rs_cur.execute("DELETE FROM fundamentals")
c_dj_cur.execute("""
    SELECT s.symbol, f.period_date, f.period_type, f.revenue, f.net_profit, f.ebitda, 
           f.operating_profit, f.operating_margin, f.net_margin, f.roe, f.roce, 
           f.debt_to_equity, f.interest_coverage, f.fcf, f.cfo, 
           f.promoter_holding_pct, f.promoter_pledged_pct,
           s.pe_ratio, s.pb_ratio, 15.0, 3.5, s.dividend_yield, f.created_at
    FROM market_fundamentaldata f
    JOIN market_stock s ON f.stock_id = s.symbol
""")
funds = c_dj_cur.fetchall()
for f in funds:
    c_rs_cur.execute("""
        INSERT INTO fundamentals (
            symbol, period_date, period_type, revenue, net_profit, ebitda,
            operating_profit, operating_margin, net_margin, roe, roce,
            debt_to_equity, interest_coverage, fcf, cfo,
            promoter_holding_pct, promoter_pledged_pct,
            pe_ratio, pb_ratio, ev_ebitda, ps_ratio, dividend_yield, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, f)

print(f"Synced {len(funds)} fundamentals records.")

c_rs.commit()
c_dj.close()
c_rs.close()
print("Database sync complete.")

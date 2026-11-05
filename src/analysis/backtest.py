"""Point-in-Time Backtesting Engine for Ranking Strategy."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass, asdict
import json

from src.utils.logger import logger
from src.utils.helpers import safe_divide
from src.storage.database import StockRepository, DatabaseManager
from src.data.market_data import get_market_data_provider
from src.analysis.indicators import calculate_all_indicators, get_latest_indicators, calculate_relative_strength
from src.analysis.valuation import ValuationEngine
from src.analysis.scoring import ScoringEngine, ScoreBreakdown
from src.config import get_config


@dataclass
class BacktestResult:
    run_id: str
    strategy_name: str
    start_date: date
    end_date: date
    rebalance_frequency: str
    initial_capital: float
    final_capital: float
    cagr: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    benchmark_cagr: float
    alpha: float
    beta: float
    equity_curve: List[Dict]
    trades: List[Dict]


class PointInTimeBacktester:
    """Backtester that strictly uses only data available at each decision point."""
    
    def __init__(self, repo: StockRepository):
        self.repo = repo
        self.md_provider = get_market_data_provider()
        self.val_engine = ValuationEngine(repo)
        self.scoring_engine = ScoringEngine()
        self.config = get_config()
        
    def run_backtest(
        self,
        universe_symbols: List[str],
        start_date: date,
        end_date: date,
        rebalance_freq: str = "M",
        top_n: int = 10,
        initial_capital: float = 1_000_000,
        transaction_cost: float = 0.001,
        benchmark_symbol: str = "^NSEI"
    ) -> BacktestResult:
        """Run point-in-time backtest."""
        
        run_id = f"bt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting backtest {run_id}: {start_date} to {end_date}, freq={rebalance_freq}")
        
        # Get benchmark data
        bench_df = self.md_provider.get_price_history(benchmark_symbol, period="max")
        if bench_df is None:
            raise ValueError("Failed to fetch benchmark data")
        bench_df = calculate_all_indicators(bench_df)
        
        # Generate rebalance dates
        rebalance_dates = self._generate_rebalance_dates(start_date, end_date, rebalance_freq)
        
        # Portfolio state
        cash = initial_capital
        positions = {}  # symbol -> shares
        equity_curve = []
        trades = []
        
        # Track portfolio value daily for metrics
        portfolio_values = []
        
        # For each rebalance period
        for i, rebal_date in enumerate(rebalance_dates):
            logger.info(f"Rebalance {i+1}/{len(rebalance_dates)}: {rebal_date}")
            
            # 1. Get universe available at this date (simplified: use full universe)
            # In production, filter by listing date, suspension status at rebal_date
            available_symbols = universe_symbols
            
            # 2. Calculate scores using ONLY data available up to rebal_date
            scores = self._calculate_point_in_time_scores(available_symbols, rebal_date, bench_df)
            
            # 3. Select top N
            ranked = sorted(scores, key=lambda x: x["composite_score"], reverse=True)
            selected = ranked[:top_n]
            
            # 4. Execute rebalancing
            cash, positions, period_trades = self._rebalance_portfolio(
                cash, positions, selected, rebal_date, transaction_cost
            )
            trades.extend(period_trades)
            
            # 5. Track equity curve until next rebalance (or end)
            next_rebal = rebalance_dates[i + 1] if i + 1 < len(rebalance_dates) else end_date
            period_equity = self._track_period_equity(
                positions, cash, rebal_date, next_rebal, bench_df
            )
            equity_curve.extend(period_equity)
            portfolio_values.extend([e["portfolio_value"] for e in period_equity])
            
        # Calculate final metrics
        final_value = portfolio_values[-1] if portfolio_values else initial_capital
        metrics = self._calculate_metrics(
            portfolio_values, equity_curve, bench_df, start_date, end_date, initial_capital
        )
        
        result = BacktestResult(
            run_id=run_id,
            strategy_name="AI_Ranking_Strategy",
            start_date=start_date,
            end_date=end_date,
            rebalance_frequency=rebalance_freq,
            initial_capital=initial_capital,
            final_capital=final_value,
            cagr=metrics["cagr"],
            volatility=metrics["volatility"],
            sharpe_ratio=metrics["sharpe"],
            max_drawdown=metrics["max_dd"],
            win_rate=metrics["win_rate"],
            benchmark_cagr=metrics["bench_cagr"],
            alpha=metrics["alpha"],
            beta=metrics["beta"],
            equity_curve=equity_curve,
            trades=trades
        )
        
        logger.info(f"Backtest complete. CAGR: {result.cagr:.2%}, Sharpe: {result.sharpe_ratio:.2f}")
        return result
    
    def _generate_rebalance_dates(self, start: date, end: date, freq: str) -> List[date]:
        """Generate month-end or quarter-end rebalance dates."""
        dates = []
        current = start
        
        # Move to first month/quarter end after start
        if freq == "M":
            # Month end
            if current.day != 1:
                # Next month 1st, then -1 day
                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)
            current = current - timedelta(days=1)
        elif freq == "Q":
            # Quarter end (Mar, Jun, Sep, Dec)
            quarter_ends = [3, 6, 9, 12]
            next_q = next((q for q in quarter_ends if q > current.month or (q == current.month and current.day <= 1)), quarter_ends[0])
            year = current.year if next_q >= current.month else current.year + 1
            if next_q == 3:
                current = date(year, 3, 31)
            elif next_q == 6:
                current = date(year, 6, 30)
            elif next_q == 9:
                current = date(year, 9, 30)
            else:
                current = date(year, 12, 31)
                
        while current <= end:
            dates.append(current)
            if freq == "M":
                # Next month end
                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)
                current = current - timedelta(days=1)
            else:
                # Next quarter
                q_ends = [3, 6, 9, 12]
                curr_q = q_ends.index(current.month) if current.month in q_ends else 0
                next_q_idx = (curr_q + 1) % 4
                year = current.year + (1 if next_q_idx == 0 else 0)
                next_q = q_ends[next_q_idx]
                if next_q == 3:
                    current = date(year, 3, 31)
                elif next_q == 6:
                    current = date(year, 6, 30)
                elif next_q == 9:
                    current = date(year, 9, 30)
                else:
                    current = date(year, 12, 31)
                    
        return dates
    
    def _calculate_point_in_time_scores(
        self, symbols: List[str], as_of_date: date, bench_df: pd.DataFrame
    ) -> List[Dict]:
        """Calculate scores using only data available on or before as_of_date."""
        scores = []
        
        for sym in symbols:
            try:
                # Get price history up to as_of_date
                price_df = self.md_provider.get_price_history(sym, period="max")
                if price_df is None or price_df.empty:
                    continue
                    
                # Filter to data available at decision date
                price_df = price_df[price_df.index.date <= as_of_date]
                if len(price_df) < 100:
                    continue
                    
                # Calculate indicators
                price_df = calculate_all_indicators(price_df)
                tech = get_latest_indicators(price_df)
                
                # Relative strength
                rs = calculate_relative_strength(price_df, bench_df[bench_df.index.date <= as_of_date])
                
                # Fundamentals available at this date (with filing lag)
                # Simplified: get latest fundamental where period_date <= as_of_date - 45 days
                cutoff = as_of_date - timedelta(days=45)
                fund = self.repo.get_latest_fundamentals(sym)
                if not fund or fund.period_date > cutoff:
                    # Need historical lookup - simplified
                    pass
                    
                # Get stored evaluation if exists for this date
                evals = self.repo.get_evaluations_by_date(as_of_date)
                existing = next((e for e in evals if e.symbol == sym), None)
                
                if existing:
                    # Use stored scores
                    score_data = {
                        "symbol": sym,
                        "composite_score": existing.composite_score,
                        "quality_score": existing.quality_score,
                        "growth_score": existing.growth_score,
                        "valuation_score": existing.valuation_score,
                        "momentum_score": existing.momentum_score,
                        "catalyst_score": existing.catalyst_score,
                        "risk_score": existing.risk_score,
                    }
                else:
                    # Simplified scoring without full pipeline
                    score_data = self._quick_score(sym, tech, rs, fund)
                    
                scores.append(score_data)
                
            except Exception as e:
                logger.debug(f"Scoring failed for {sym} at {as_of_date}: {e}")
                continue
                
        return scores
    
    def _quick_score(self, sym: str, tech: Dict, rs: Dict, fund) -> Dict:
        """Quick scoring for backtest when full pipeline not available."""
        # Simplified momentum-based score for backtest
        score = 50
        
        trend = tech.get("trend_sma", "Bearish")
        rsi = tech.get("RSI_14", 50)
        mom_60 = tech.get("momentum_60d", 0)
        rs_60 = rs.get("RS_60d", 0)
        
        if trend == "Bullish": score += 15
        if 50 <= rsi <= 70: score += 10
        if mom_60 > 10: score += 15
        elif mom_60 > 0: score += 8
        if rs_60 > 0: score += 10
        elif rs_60 > -0.05: score += 5
        
        return {
            "symbol": sym,
            "composite_score": max(0, min(100, score)),
            "quality_score": 50,
            "growth_score": 50,
            "valuation_score": 50,
            "momentum_score": max(0, min(100, score)),
            "catalyst_score": 50,
            "risk_score": 30
        }
    
    def _rebalance_portfolio(
        self, cash: float, positions: Dict, selected: List[Dict], 
        rebal_date: date, cost: float
    ) -> Tuple[float, Dict, List[Dict]]:
        """Equal-weight rebalancing."""
        if not selected:
            return cash, positions, []
            
        # Target weight per stock
        total_value = cash + sum(
            positions.get(s, 0) * self._get_price_on_date(s, rebal_date) 
            for s in positions
        )
        target_per_stock = total_value / len(selected)
        target_symbols = {s["symbol"] for s in selected}
        
        trades = []
        
        # Sell positions not in target
        to_sell = [s for s in positions if s not in target_symbols]
        for sym in to_sell:
            shares = positions[sym]
            price = self._get_price_on_date(sym, rebal_date)
            if price and shares > 0:
                proceeds = shares * price * (1 - cost)
                cash += proceeds
                trades.append({
                    "date": rebal_date.isoformat(),
                    "symbol": sym,
                    "action": "SELL",
                    "shares": shares,
                    "price": price,
                    "value": shares * price
                })
            del positions[sym]
            
        # Buy/Adjust target positions
        for sdata in selected:
            sym = sdata["symbol"]
            price = self._get_price_on_date(sym, rebal_date)
            if not price:
                continue
                
            current_shares = positions.get(sym, 0)
            current_value = current_shares * price
            target_shares = int(target_per_stock / price)
            
            if target_shares > current_shares:
                # Buy
                buy_shares = target_shares - current_shares
                cost_amount = buy_shares * price * (1 + cost)
                if cost_amount <= cash:
                    cash -= cost_amount
                    positions[sym] = target_shares
                    trades.append({
                        "date": rebal_date.isoformat(),
                        "symbol": sym,
                        "action": "BUY",
                        "shares": buy_shares,
                        "price": price,
                        "value": buy_shares * price
                    })
            elif target_shares < current_shares:
                # Sell excess
                sell_shares = current_shares - target_shares
                proceeds = sell_shares * price * (1 - cost)
                cash += proceeds
                positions[sym] = target_shares
                trades.append({
                    "date": rebal_date.isoformat(),
                    "symbol": sym,
                    "action": "SELL",
                    "shares": sell_shares,
                    "price": price,
                    "value": sell_shares * price
                })
                
        return cash, positions, trades
    
    def _get_price_on_date(self, symbol: str, target_date: date) -> Optional[float]:
        """Get close price on or before target date."""
        df = self.md_provider.get_price_history(symbol, period="max")
        if df is None or df.empty:
            return None
        df = df[df.index.date <= target_date]
        if df.empty:
            return None
        return float(df["Close"].iloc[-1])
    
    def _track_period_equity(
        self, positions: Dict, cash: float, start: date, end: date, bench_df: pd.DataFrame
    ) -> List[Dict]:
        """Track daily portfolio value during period."""
        equity_points = []
        
        # Get all trading days in period from benchmark
        bench_period = bench_df[(bench_df.index.date >= start) & (bench_df.index.date <= end)]
        
        for dt in bench_period.index:
            d = dt.date()
            portfolio_val = cash
            for sym, shares in positions.items():
                price = self._get_price_on_date(sym, d)
                if price:
                    portfolio_val += shares * price
                    
            bench_price = float(bench_period.loc[dt, "Close"])
            equity_points.append({
                "date": d.isoformat(),
                "portfolio_value": portfolio_val,
                "benchmark_price": bench_price
            })
            
        return equity_points
    
    def _calculate_metrics(
        self, portfolio_values: List[float], equity_curve: List[Dict], 
        bench_df: pd.DataFrame, start: date, end: date, initial: float
    ) -> Dict:
        """Calculate performance metrics."""
        if len(portfolio_values) < 2:
            return {"cagr": 0, "volatility": 0, "sharpe": 0, "max_dd": 0, "win_rate": 0, "bench_cagr": 0, "alpha": 0, "beta": 0}
            
        pv = np.array(portfolio_values)
        returns = np.diff(pv) / pv[:-1]
        
        # CAGR
        years = (end - start).days / 365.25
        cagr = (pv[-1] / initial) ** (1/years) - 1 if years > 0 else 0
        
        # Volatility (annualized)
        vol = np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0
        
        # Sharpe (assume 6% risk-free)
        rf = 0.06
        sharpe = (cagr - rf) / vol if vol > 0 else 0
        
        # Max Drawdown
        peak = np.maximum.accumulate(pv)
        dd = (pv - peak) / peak
        max_dd = float(np.min(dd))
        
        # Win Rate
        win_rate = np.sum(returns > 0) / len(returns) if len(returns) > 0 else 0
        
        # Benchmark
        bench_period = bench_df[(bench_df.index.date >= start) & (bench_df.index.date <= end)]
        if len(bench_period) > 1:
            bench_ret = (bench_period["Close"].iloc[-1] / bench_period["Close"].iloc[0]) - 1
            bench_cagr = (1 + bench_ret) ** (1/years) - 1
            bench_returns = bench_period["Close"].pct_change().dropna().values
            
            # Alpha, Beta
            if len(returns) == len(bench_returns):
                beta = np.cov(returns, bench_returns)[0,1] / np.var(bench_returns) if np.var(bench_returns) > 0 else 1
                alpha = cagr - (rf + beta * (bench_cagr - rf))
            else:
                beta, alpha = 1, 0
        else:
            bench_cagr, beta, alpha = 0, 1, 0
            
        return {
            "cagr": float(cagr),
            "volatility": float(vol),
            "sharpe": float(sharpe),
            "max_dd": float(max_dd),
            "win_rate": float(win_rate),
            "bench_cagr": float(bench_cagr),
            "alpha": float(alpha),
            "beta": float(beta)
        }
    
    def save_results(self, result: BacktestResult) -> str:
        """Save backtest results to database and JSON."""
        db = DatabaseManager()
        db.init_db()
        
        db.save_backtest_run({
            "run_id": result.run_id,
            "strategy_name": result.strategy_name,
            "start_date": result.start_date,
            "end_date": result.end_date,
            "rebalance_frequency": result.rebalance_frequency,
            "initial_capital": result.initial_capital,
            "cagr": result.cagr,
            "volatility": result.volatility,
            "sharpe_ratio": result.sharpe_ratio,
            "max_drawdown": result.max_drawdown,
            "win_rate": result.win_rate,
            "benchmark_cagr": result.benchmark_cagr,
            "metrics_json": json.dumps({
                "alpha": result.alpha,
                "beta": result.beta,
                "final_capital": result.final_capital
            }),
            "equity_curve_json": json.dumps(result.equity_curve)
        })
        
        # Save JSON report
        import os
        os.makedirs("data/reports", exist_ok=True)
        report_path = f"data/reports/backtest_{result.run_id}.json"
        with open(report_path, "w") as f:
            json.dump(asdict(result), f, default=str, indent=2)
            
        return report_path
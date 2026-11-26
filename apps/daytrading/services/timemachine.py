"""Skill 8: Trader Time Machine — Historical candle replay, backtesting, Monte Carlo.

Deterministic Python for all simulations. No LLM for calculations.
Prevents look-ahead bias and data leakage.
"""

import logging
import random
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List

import pandas as pd
import numpy as np

from apps.daytrading.models import BacktestScenario
from .market_data import get_intraday_candles, get_daily_history
from .indicators import calculate_intraday_indicators, calculate_opening_range
from .market_calendar import trading_days_between, now_ist
from .charges import round_trip_charges

logger = logging.getLogger(__name__)


def replay_orb_strategy(symbol, lookback_days=60, or_minutes=15, exchange="NSE",
                         risk_pct=1.0, rr_target=2.0):
    """Replay Opening Range Breakout strategy on historical data.

    No look-ahead bias: at each bar only data up to that bar is used.
    """
    df = get_intraday_candles(symbol, interval="5m", period=f"{lookback_days}d", exchange=exchange)
    if df is None or len(df) < 50:
        return {"error": "Insufficient data for replay"}

    df = calculate_intraday_indicators(df)

    # Group by date
    df["trade_date"] = df.index.date
    dates = sorted(df["trade_date"].unique())

    trades = []
    for d in dates:
        day_df = df[df["trade_date"] == d].copy()
        if len(day_df) < or_minutes // 5 + 2:
            continue

        or_data = calculate_opening_range(day_df, minutes=or_minutes)
        if not or_data or or_data["or_range"] <= 0:
            continue

        # Only look at bars AFTER opening range (no look-ahead)
        cutoff_idx = or_minutes // 5
        if cutoff_idx >= len(day_df):
            continue

        entry = None
        direction = None
        entry_price = None
        for i in range(cutoff_idx, len(day_df)):
            bar = day_df.iloc[i]
            if bar["Close"] > or_data["or_high"] and not entry:
                entry = bar
                direction = "LONG"
                entry_price = or_data["or_high"]
                break
            elif bar["Close"] < or_data["or_low"] and not entry:
                entry = bar
                direction = "SHORT"
                entry_price = or_data["or_low"]
                break

        if not entry_price:
            continue

        # Calculate stop and target
        risk = or_data["or_range"]
        if direction == "LONG":
            stop = entry_price - risk
            target = entry_price + (risk * rr_target)
        else:
            stop = entry_price + risk
            target = entry_price - (risk * rr_target)

        # Simulate trade outcome (bars after entry, no look-ahead)
        entry_idx = day_df.index.get_loc(entry.name)
        exit_price = None
        exit_reason = "EOD"

        for j in range(entry_idx + 1, len(day_df)):
            bar = day_df.iloc[j]
            if direction == "LONG":
                if bar["Low"] <= stop:
                    exit_price = stop
                    exit_reason = "STOP_LOSS"
                    break
                if bar["High"] >= target:
                    exit_price = target
                    exit_reason = "TARGET"
                    break
            else:
                if bar["High"] >= stop:
                    exit_price = stop
                    exit_reason = "STOP_LOSS"
                    break
                if bar["Low"] <= target:
                    exit_price = target
                    exit_reason = "TARGET"
                    break

        if not exit_price:
            exit_price = float(day_df.iloc[-1]["Close"])

        # Position sizing based on capital and risk
        capital = 100000.0  # standard baseline paper capital ₹1,00,000
        risk_amount = capital * (risk_pct / 100.0)
        risk_per_share = abs(entry_price - stop)
        qty = max(1, int(risk_amount / risk_per_share)) if risk_per_share > 0 else 1

        gross_diff = (exit_price - entry_price) if direction == "LONG" else (entry_price - exit_price)
        gross_pnl = gross_diff * qty

        # Indian transaction costs (Brokerage, STT, Exchange, GST, Stamp Duty)
        charges_dict = round_trip_charges(
            Decimal(str(entry_price)), Decimal(str(exit_price)),
            qty, "MIS", exchange
        )
        total_charges = float(charges_dict["total"])
        net_pnl = round(gross_pnl - total_charges, 2)

        trades.append({
            "date": str(d),
            "direction": direction,
            "quantity": qty,
            "entry": round(entry_price, 2),
            "exit": round(exit_price, 2),
            "stop": round(stop, 2),
            "target": round(target, 2),
            "gross_pnl": round(gross_pnl, 2),
            "charges": total_charges,
            "pnl": net_pnl,  # Net PnL after Indian charges
            "pnl_pct": round(net_pnl / (entry_price * qty) * 100, 2) if entry_price and qty else 0,
            "exit_reason": exit_reason,
        })

    # Summary statistics
    if not trades:
        return {"trades": [], "summary": {"error": "No trades generated"}}

    winners = [t for t in trades if t["pnl"] > 0]
    losers = [t for t in trades if t["pnl"] <= 0]
    total_pnl = sum(t["pnl"] for t in trades)
    total_charges_sum = sum(t["charges"] for t in trades)
    gross_profit = sum(t["pnl"] for t in winners) if winners else 0
    gross_loss = abs(sum(t["pnl"] for t in losers)) if losers else 0

    return {
        "symbol": symbol,
        "strategy": "ORB",
        "lookback_days": lookback_days,
        "trades": trades,
        "summary": {
            "total_trades": len(trades),
            "winners": len(winners),
            "losers": len(losers),
            "win_rate": round(len(winners) / len(trades) * 100, 1),
            "total_pnl": round(total_pnl, 2),
            "total_charges": round(total_charges_sum, 2),
            "avg_win": round(sum(t["pnl"] for t in winners) / len(winners), 2) if winners else 0,
            "avg_loss": round(sum(t["pnl"] for t in losers) / len(losers), 2) if losers else 0,
            "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss > 0 else float("inf"),
            "max_win": round(max(t["pnl"] for t in trades), 2),
            "max_loss": round(min(t["pnl"] for t in trades), 2),
        },
    }


def monte_carlo_simulation(trades, num_simulations=1000, initial_capital=100000):
    """Run Monte Carlo simulation on trade results.

    Shuffles trade order to see distribution of outcomes.
    """
    if not trades:
        return {"error": "No trades for simulation"}

    pnls = [t["pnl"] for t in trades]
    results = []

    for _ in range(num_simulations):
        shuffled = pnls.copy()
        random.shuffle(shuffled)

        equity = initial_capital
        peak = equity
        max_dd = 0
        curve = [equity]

        for pnl in shuffled:
            equity += pnl
            curve.append(equity)
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak * 100 if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

        results.append({
            "final_equity": round(equity, 2),
            "total_return_pct": round((equity - initial_capital) / initial_capital * 100, 2),
            "max_drawdown_pct": round(max_dd, 2),
        })

    final_equities = [r["final_equity"] for r in results]
    max_dds = [r["max_drawdown_pct"] for r in results]

    return {
        "num_simulations": num_simulations,
        "initial_capital": initial_capital,
        "percentiles": {
            "p5": round(np.percentile(final_equities, 5), 2),
            "p25": round(np.percentile(final_equities, 25), 2),
            "p50": round(np.percentile(final_equities, 50), 2),
            "p75": round(np.percentile(final_equities, 75), 2),
            "p95": round(np.percentile(final_equities, 95), 2),
        },
        "avg_return_pct": round(np.mean([r["total_return_pct"] for r in results]), 2),
        "avg_max_drawdown": round(np.mean(max_dds), 2),
        "worst_case": round(min(final_equities), 2),
        "best_case": round(max(final_equities), 2),
        "probability_profit": round(sum(1 for r in results if r["final_equity"] > initial_capital) / num_simulations * 100, 1),
    }


def run_backtest_and_save(symbol, strategy="ORB", lookback_days=60, exchange="NSE"):
    """Run backtest, Monte Carlo, and save results."""
    result = replay_orb_strategy(symbol, lookback_days=lookback_days, exchange=exchange)

    if "error" in result.get("summary", {}):
        return result

    mc = monte_carlo_simulation(result["trades"])

    scenario = BacktestScenario.objects.create(
        name=f"{symbol} {strategy} {lookback_days}d backtest",
        symbol=symbol,
        strategy=strategy,
        timeframe="5m",
        start_date=now_ist().date() - timedelta(days=lookback_days),
        end_date=now_ist().date(),
        num_trades=result["summary"]["total_trades"],
        winners=result["summary"]["winners"],
        losers=result["summary"]["losers"],
        win_rate=result["summary"]["win_rate"],
        total_return_pct=round((result["summary"].get("total_pnl", 0) / 100000.0) * 100, 2),
        avg_win_pct=round((result["summary"].get("avg_win", 0) / 100000.0) * 100, 2),
        avg_loss_pct=round((result["summary"].get("avg_loss", 0) / 100000.0) * 100, 2),
        profit_factor=result["summary"].get("profit_factor", 0),
        trades_json=result["trades"],
        monte_carlo=mc,
    )

    result["scenario_id"] = str(scenario.scenario_id)
    result["monte_carlo"] = mc
    return result

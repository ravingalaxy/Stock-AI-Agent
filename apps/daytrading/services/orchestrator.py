"""Day Trading Orchestrator — coordinates all 11 skills into a unified pipeline.

Flow: Scanner → Entry → Risk Check → Budget → Order → Exit Monitor → Journal
"""

import logging
from typing import Dict, Any, Optional, List

from . import scanner, news, entry, exit_planner, risk, budget, alerts
from . import timemachine, analyst, disclosure, paper_broker
from .market_calendar import market_status, is_market_open, now_ist

logger = logging.getLogger(__name__)


def get_dashboard_data():
    """Aggregate data for the day trading dashboard."""
    status = market_status()

    # Get recent scan results
    from apps.daytrading.models import ScanResult, NewsItem, PaperPosition, DayTradePlan, TradingAlert
    recent_scans = list(
        ScanResult.objects.order_by("-score")[:10].values(
            "symbol", "scan_type", "score", "price", "volume_ratio", "change_pct", "scanned_at"
        )
    )

    # Active plans
    active_plans = list(
        DayTradePlan.objects.filter(status__in=["PENDING", "ACTIVE"]).values()
    )

    # Open positions
    positions = paper_broker.get_open_positions()

    # P&L summary
    pnl = paper_broker.get_trade_pnl_summary()

    # Recent news
    recent_news = list(
        NewsItem.objects.order_by("-fetched_at")[:10].values(
            "headline", "source", "sentiment", "url", "published_at"
        )
    )

    # Active alerts
    active_alerts = list(
        TradingAlert.objects.filter(is_active=True)[:5].values(
            "symbol", "alert_type", "condition", "threshold"
        )
    )

    # Budget
    budget_data = budget.get_budget_summary()

    return {
        "market_status": status,
        "scanner_results": recent_scans,
        "active_plans": active_plans,
        "open_positions": positions,
        "pnl_summary": pnl,
        "recent_news": recent_news,
        "active_alerts": active_alerts,
        "budget": budget_data,
    }


def execute_scan_to_plan(symbol=None, universe=None, exchange="NSE", strategy="ORB"):
    """Full pipeline: scan → generate entry → risk check → create plan."""
    results = {"steps": []}

    # Step 1: Scan
    if symbol:
        scan_results = scanner.scan_momentum([symbol], exchange)
    else:
        scan_results = scanner.run_full_scan(universe, exchange)
        scan_results = scan_results.get("momentum", [])

    results["steps"].append({"step": "scan", "count": len(scan_results)})

    if not scan_results:
        results["outcome"] = "No scan hits"
        return results

    # Step 2: Generate entry for top hits
    plans = []
    for hit in scan_results[:3]:
        sym = hit.get("clean_symbol", hit["symbol"])
        signal = entry.generate_entry_signal(sym, exchange, strategy)
        results["steps"].append({"step": "entry_signal", "symbol": sym, "signal": signal.get("signal", False)})

        if signal.get("signal"):
            # Step 3: Risk check
            rcheck = risk.pre_trade_risk_check(
                symbol=signal["symbol"], side="BUY",
                quantity=1, price=signal["entry_price"],
                stop_loss=signal["stop_loss"], exchange=exchange,
            )
            results["steps"].append({"step": "risk_check", "symbol": sym, "passed": rcheck["passed"]})

            if rcheck["passed"]:
                # Step 4: Position sizing
                sizing = budget.allocate_for_trade(
                    entry_price=signal["entry_price"],
                    stop_loss=signal["stop_loss"],
                    exchange=exchange,
                )
                signal["quantity"] = sizing.get("quantity", 0)

                # Step 5: Create plan
                plan = entry.create_trade_plan(signal)
                if plan:
                    plan.quantity = sizing.get("quantity", 0)
                    plan.risk_amount = sizing.get("risk_amount", 0)
                    plan.position_value = sizing.get("position_value", 0)
                    plan.save()
                    plans.append(str(plan.plan_id))
                    results["steps"].append({"step": "plan_created", "plan_id": str(plan.plan_id)})

    results["plans_created"] = plans
    results["outcome"] = f"{len(plans)} trade plan(s) created"
    return results


def execute_paper_trade(plan_id):
    """Execute a pending plan as a paper trade."""
    try:
        plan = entry.DayTradePlan.objects.get(plan_id=plan_id)
    except entry.DayTradePlan.DoesNotExist:
        return {"error": "Plan not found"}

    if plan.status != "PENDING":
        return {"error": f"Plan status is {plan.status}, expected PENDING"}

    result = paper_broker.submit_order(
        symbol=plan.symbol,
        side="BUY" if plan.direction == "LONG" else "SELL",
        quantity=plan.quantity,
        order_type="MARKET",
        exchange=plan.exchange,
        product="MIS",
        plan_id=plan.plan_id,
    )

    if result.get("status") == "FILLED":
        plan.status = "FILLED"
        plan.entry_time = now_ist()
        plan.save()

    return result


def check_all_exits():
    """Check exit conditions for all active plans."""
    active_plans = entry.DayTradePlan.objects.filter(status__in=["ACTIVE", "FILLED"])
    results = []
    for plan in active_plans:
        exit_eval = exit_planner.evaluate_exit(plan.plan_id)
        if exit_eval.get("action") in ("EXIT", "PARTIAL_EXIT"):
            # Execute exit
            side = "SELL" if plan.direction == "LONG" else "BUY"
            exit_result = paper_broker.submit_order(
                symbol=plan.symbol, side=side,
                quantity=plan.quantity, order_type="MARKET",
                exchange=plan.exchange, product="MIS",
            )
            if exit_result.get("status") == "FILLED":
                plan.status = "EXITED"
                plan.save()
                # Create journal entry
                _create_journal_entry(plan, exit_result)
            results.append({"plan": str(plan.plan_id), "exit": exit_eval, "result": exit_result})
        else:
            results.append({"plan": str(plan.plan_id), "exit": exit_eval})
    return results


def _create_journal_entry(plan, exit_result):
    """Create a trade journal entry after exit."""
    try:
        exit_price = exit_result.get("fill_price", 0)
        entry_price = float(plan.entry_price or 0)
        qty = plan.quantity
        pnl = (exit_price - entry_price) * qty if plan.direction == "LONG" else (entry_price - exit_price) * qty

        TradeJournalEntry.objects.create(
            symbol=plan.symbol,
            trade_date=now_ist().date(),
            strategy=plan.strategy,
            direction=plan.direction,
            entry_price=plan.entry_price,
            exit_price=exit_price,
            quantity=qty,
            pnl_amount=pnl,
            pnl_pct=(pnl / (entry_price * qty) * 100) if entry_price * qty > 0 else 0,
            charges=exit_result.get("charges", {}).get("total", 0),
            outcome="WIN" if pnl > 0 else ("LOSS" if pnl < 0 else "BREAKEVEN"),
            plan=plan,
        )
    except Exception as e:
        logger.error(f"Failed to create journal entry: {e}")

"""Day Trading views — dashboard and API endpoints."""

import json
import logging

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .services import (
    orchestrator, scanner, news, entry, exit_planner,
    risk, budget, alerts, timemachine, analyst,
    disclosure, paper_broker, market_calendar,
)
from .serializers import (
    SubmitOrderSerializer, CreateAlertSerializer, BacktestRequestSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dashboard View
# ---------------------------------------------------------------------------
def dashboard(request):
    """Main Day Trading dashboard."""
    context = {
        "market_status": market_calendar.market_status(),
        "page_title": "Day Trading Dashboard",
    }
    return render(request, "daytrading/dashboard.html", context)


# ---------------------------------------------------------------------------
# API: Dashboard Data
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def api_dashboard_data(request):
    """Get aggregated dashboard data."""
    try:
        data = orchestrator.get_dashboard_data()
        return Response(data)
    except Exception as e:
        logger.error(f"Dashboard data error: {e}")
        return Response({"error": str(e)}, status=500)


# ---------------------------------------------------------------------------
# API: Scanner
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def api_scan(request):
    """Run stock scanner."""
    scan_type = request.GET.get("type", "momentum")
    exchange = request.GET.get("exchange", "NSE")
    try:
        if scan_type == "full":
            results = scanner.run_full_scan(exchange=exchange)
        elif scan_type == "breakout":
            results = scanner.scan_breakouts(exchange=exchange)
        elif scan_type == "volume":
            results = scanner.scan_volume_spikes(exchange=exchange)
        else:
            results = scanner.scan_momentum(exchange=exchange)
        return Response({"scan_type": scan_type, "results": results})
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ---------------------------------------------------------------------------
# API: News
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def api_news(request):
    """Get market news."""
    symbol = request.GET.get("symbol")
    refresh = request.GET.get("refresh", "false").lower() == "true"
    try:
        if refresh:
            news.fetch_and_store_news(symbol)
        items = news.get_recent_news(symbol)
        return Response({"news": items})
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ---------------------------------------------------------------------------
# API: Entry Signal
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def api_entry_signal(request):
    """Generate entry signal for a symbol."""
    symbol = request.GET.get("symbol")
    strategy = request.GET.get("strategy", "ORB")
    exchange = request.GET.get("exchange", "NSE")
    if not symbol:
        return Response({"error": "symbol required"}, status=400)
    try:
        signal = entry.generate_entry_signal(symbol, exchange, strategy)
        return Response(signal)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ---------------------------------------------------------------------------
# API: Exit Evaluation
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def api_exit_check(request, plan_id):
    """Check exit conditions for a plan."""
    try:
        result = exit_planner.evaluate_exit(plan_id)
        return Response(result)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ---------------------------------------------------------------------------
# API: Risk Check
# ---------------------------------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def api_risk_check(request):
    """Pre-trade risk check."""
    try:
        data = request.data
        result = risk.pre_trade_risk_check(
            symbol=data.get("symbol", ""),
            side=data.get("side", "BUY"),
            quantity=int(data.get("quantity", 1)),
            price=float(data.get("price", 0)),
            stop_loss=float(data.get("stop_loss", 0)) if data.get("stop_loss") else None,
            product=data.get("product", "MIS"),
            exchange=data.get("exchange", "NSE"),
        )
        return Response(result)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ---------------------------------------------------------------------------
# API: Budget
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def api_budget(request):
    """Get budget summary."""
    try:
        return Response(budget.get_budget_summary())
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ---------------------------------------------------------------------------
# API: Paper Orders
# ---------------------------------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def api_submit_order(request):
    """Submit a paper order."""
    serializer = SubmitOrderSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    try:
        d = serializer.validated_data
        result = paper_broker.submit_order(
            symbol=d["symbol"], side=d["side"], quantity=d["quantity"],
            order_type=d["order_type"],
            price=float(d["price"]) if d.get("price") else None,
            product=d["product"], exchange=d["exchange"],
        )
        return Response(result)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_positions(request):
    """Get open positions."""
    try:
        return Response({"positions": paper_broker.get_open_positions()})
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_order_history(request):
    """Get order history."""
    try:
        return Response({"orders": paper_broker.get_order_history()})
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_pnl(request):
    """Get P&L summary."""
    try:
        return Response(paper_broker.get_trade_pnl_summary())
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([AllowAny])
def api_flatten(request):
    """Flatten all open positions."""
    try:
        return Response(paper_broker.flatten_all())
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ---------------------------------------------------------------------------
# API: Alerts
# ---------------------------------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def api_create_alert(request):
    """Create a trading alert."""
    serializer = CreateAlertSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    try:
        d = serializer.validated_data
        result = alerts.create_alert(d["symbol"], d["alert_type"], d["condition"],
                                     float(d["threshold"]) if d.get("threshold") else None)
        return Response(result)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_alerts_list(request):
    """Get active alerts."""
    try:
        return Response({"alerts": alerts.get_active_alerts()})
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ---------------------------------------------------------------------------
# API: Backtest / Time Machine
# ---------------------------------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def api_backtest(request):
    """Run backtest."""
    serializer = BacktestRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    try:
        d = serializer.validated_data
        result = timemachine.run_backtest_and_save(
            symbol=d["symbol"], strategy=d["strategy"],
            lookback_days=d["lookback_days"], exchange=d["exchange"],
        )
        return Response(result)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ---------------------------------------------------------------------------
# API: Analyst
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def api_analyst(request):
    """Get company analysis."""
    symbol = request.GET.get("symbol")
    if not symbol:
        return Response({"error": "symbol required"}, status=400)
    try:
        overview = analyst.get_company_overview(symbol)
        earnings = analyst.get_earnings_history(symbol)
        ratios = analyst.get_financial_ratios(symbol)
        return Response({"overview": overview, "earnings": earnings, "ratios": ratios})
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ---------------------------------------------------------------------------
# API: Disclosures
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def api_disclosures(request):
    """Get public disclosures."""
    symbol = request.GET.get("symbol")
    refresh = request.GET.get("refresh", "false").lower() == "true"
    try:
        if refresh:
            disclosure.fetch_and_store_disclosures(symbol)
        result = disclosure.get_recent_disclosures(symbol)
        summary = disclosure.get_disclosure_summary(symbol) if symbol else {}
        return Response({"disclosures": result, "summary": summary})
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ---------------------------------------------------------------------------
# API: Orchestrator Pipeline
# ---------------------------------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def api_scan_to_plan(request):
    """Run full scan-to-plan pipeline."""
    try:
        symbol = request.data.get("symbol")
        strategy = request.data.get("strategy", "ORB")
        exchange = request.data.get("exchange", "NSE")
        result = orchestrator.execute_scan_to_plan(symbol=symbol, strategy=strategy, exchange=exchange)
        return Response(result)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([AllowAny])
def api_execute_plan(request, plan_id):
    """Execute a pending trade plan."""
    try:
        result = orchestrator.execute_paper_trade(plan_id)
        return Response(result)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([AllowAny])
def api_check_exits(request):
    """Check exit conditions for all active plans."""
    try:
        return Response({"results": orchestrator.check_all_exits()})
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ---------------------------------------------------------------------------
# API: Market Status
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def api_market_status(request):
    """Get current market status."""
    return Response(market_calendar.market_status())


# ---------------------------------------------------------------------------
# API: Account Reset
# ---------------------------------------------------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def api_reset_account(request):
    """Reset paper trading account."""
    try:
        capital = float(request.data.get("initial_capital", 1000000))
        result = budget.reset_paper_account(capital)
        return Response(result)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

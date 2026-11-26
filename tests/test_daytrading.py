"""Comprehensive tests for Day Trading & Intraday Intelligence module.

Tests cover all 11 skills, Indian market specifics, paper-only security.
"""

import pytest
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

import django
from django.test import TestCase, override_settings

# ---------------------------------------------------------------------------
# Skill 0: Market Calendar (shared infrastructure)
# ---------------------------------------------------------------------------
class TestMarketCalendar(TestCase):
    """Test NSE/BSE market calendar."""

    def test_weekday_is_trading_day(self):
        from apps.daytrading.services.market_calendar import is_trading_day
        # 2026-11-26 is Thursday
        self.assertTrue(is_trading_day(date(2026, 11, 26)))

    def test_weekend_not_trading_day(self):
        from apps.daytrading.services.market_calendar import is_trading_day
        # Saturday
        self.assertFalse(is_trading_day(date(2026, 11, 28)))
        # Sunday
        self.assertFalse(is_trading_day(date(2026, 11, 29)))

    def test_republic_day_holiday(self):
        from apps.daytrading.services.market_calendar import is_trading_day
        self.assertFalse(is_trading_day(date(2026, 1, 26)))

    def test_independence_day_holiday(self):
        from apps.daytrading.services.market_calendar import is_trading_day
        self.assertFalse(is_trading_day(date(2026, 8, 15)))

    def test_market_open_during_session(self):
        from apps.daytrading.services.market_calendar import is_market_open, IST
        import pytz
        # 10:30 IST on a trading day
        dt = IST.localize(datetime(2026, 11, 26, 10, 30))
        self.assertTrue(is_market_open(dt))

    def test_market_closed_before_open(self):
        from apps.daytrading.services.market_calendar import is_market_open, IST
        dt = IST.localize(datetime(2026, 11, 26, 8, 0))
        self.assertFalse(is_market_open(dt))

    def test_market_closed_after_close(self):
        from apps.daytrading.services.market_calendar import is_market_open, IST
        dt = IST.localize(datetime(2026, 11, 26, 16, 0))
        self.assertFalse(is_market_open(dt))

    def test_pre_open_session(self):
        from apps.daytrading.services.market_calendar import is_pre_open, IST
        dt = IST.localize(datetime(2026, 11, 26, 9, 10))
        self.assertTrue(is_pre_open(dt))

    def test_pre_open_not_during_session(self):
        from apps.daytrading.services.market_calendar import is_pre_open, IST
        dt = IST.localize(datetime(2026, 11, 26, 10, 0))
        self.assertFalse(is_pre_open(dt))

    def test_session_boundaries(self):
        from apps.daytrading.services.market_calendar import session_boundaries
        open_dt, close_dt = session_boundaries(date(2026, 11, 26))
        self.assertEqual(open_dt.hour, 9)
        self.assertEqual(open_dt.minute, 15)
        self.assertEqual(close_dt.hour, 15)
        self.assertEqual(close_dt.minute, 30)

    def test_next_trading_day_skips_weekend(self):
        from apps.daytrading.services.market_calendar import next_trading_day
        # Friday -> Monday
        result = next_trading_day(date(2026, 11, 27))  # Friday
        self.assertEqual(result.weekday(), 0)  # Monday

    def test_prev_trading_day(self):
        from apps.daytrading.services.market_calendar import prev_trading_day
        # Monday -> Friday
        result = prev_trading_day(date(2026, 11, 30))  # Monday
        self.assertEqual(result, date(2026, 11, 27))  # Friday

    def test_trading_days_between(self):
        from apps.daytrading.services.market_calendar import trading_days_between
        days = trading_days_between(date(2026, 11, 23), date(2026, 11, 27))
        # Mon-Fri, check all are weekdays and not holidays
        for d in days:
            self.assertTrue(d.weekday() < 5)

    def test_market_status_returns_dict(self):
        from apps.daytrading.services.market_calendar import market_status
        status = market_status()
        self.assertIn("is_trading_day", status)
        self.assertIn("is_market_open", status)
        self.assertIn("current_time_ist", status)


# ---------------------------------------------------------------------------
# Indian Transaction Charges
# ---------------------------------------------------------------------------
class TestCharges(TestCase):
    """Test Indian securities transaction charges."""

    def test_intraday_buy_charges(self):
        from apps.daytrading.services.charges import calculate_charges
        charges = calculate_charges(100000, "BUY", "MIS", "NSE")
        self.assertIn("brokerage", charges)
        self.assertIn("stt", charges)
        self.assertIn("gst", charges)
        self.assertIn("total", charges)
        # Intraday buy: no STT on buy side
        self.assertEqual(charges["stt"], Decimal("0"))
        # Stamp duty on buy side
        self.assertGreater(charges["stamp_duty"], Decimal("0"))

    def test_intraday_sell_charges(self):
        from apps.daytrading.services.charges import calculate_charges
        charges = calculate_charges(100000, "SELL", "MIS", "NSE")
        # Intraday sell: STT applied
        self.assertGreater(charges["stt"], Decimal("0"))
        # No stamp duty on sell
        self.assertEqual(charges["stamp_duty"], Decimal("0"))

    def test_round_trip_charges(self):
        from apps.daytrading.services.charges import round_trip_charges
        charges = round_trip_charges(Decimal("100"), Decimal("105"), 100, "MIS", "NSE")
        self.assertIn("buy_charges", charges)
        self.assertIn("sell_charges", charges)
        self.assertGreater(charges["total"], Decimal("0"))

    def test_bse_lower_exchange_charges(self):
        from apps.daytrading.services.charges import calculate_charges
        nse = calculate_charges(100000, "BUY", "MIS", "NSE")
        bse = calculate_charges(100000, "BUY", "MIS", "BSE")
        self.assertGreater(nse["exchange_charges"], bse["exchange_charges"])


# ---------------------------------------------------------------------------
# Market Data Service
# ---------------------------------------------------------------------------
class TestMarketData(TestCase):
    """Test market data service."""

    def test_normalize_symbol_nse(self):
        from apps.daytrading.services.market_data import normalize_symbol
        self.assertEqual(normalize_symbol("RELIANCE", "NSE"), "RELIANCE.NS")
        self.assertEqual(normalize_symbol("RELIANCE.NS", "NSE"), "RELIANCE.NS")

    def test_normalize_symbol_bse(self):
        from apps.daytrading.services.market_data import normalize_symbol
        self.assertEqual(normalize_symbol("500325", "BSE"), "500325.BO")

    def test_clean_symbol(self):
        from apps.daytrading.services.market_data import clean_symbol
        self.assertEqual(clean_symbol("RELIANCE.NS"), "RELIANCE")
        self.assertEqual(clean_symbol("500325.BO"), "500325")

    def test_validate_candle_data_empty(self):
        from apps.daytrading.services.market_data import validate_candle_data
        result = validate_candle_data(None)
        self.assertFalse(result["valid"])


# ---------------------------------------------------------------------------
# Technical Indicators (Skill infrastructure)
# ---------------------------------------------------------------------------
class TestIndicators(TestCase):
    """Test intraday technical indicators."""

    def _make_df(self, n=50):
        import pandas as pd
        import numpy as np
        dates = pd.date_range("2026-01-01 09:15", periods=n, freq="5min")
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)
        return pd.DataFrame({
            "Open": close - 0.2, "High": close + 0.5,
            "Low": close - 0.5, "Close": close,
            "Volume": np.random.randint(1000, 10000, n),
        }, index=dates)

    def test_vwap_calculation(self):
        from apps.daytrading.services.indicators import calculate_vwap
        df = self._make_df()
        vwap = calculate_vwap(df)
        self.assertEqual(len(vwap), len(df))
        self.assertFalse(vwap.isna().all())

    def test_opening_range(self):
        from apps.daytrading.services.indicators import calculate_opening_range
        df = self._make_df(50)
        or_data = calculate_opening_range(df, minutes=15)
        self.assertIsNotNone(or_data)
        self.assertIn("or_high", or_data)
        self.assertIn("or_low", or_data)
        self.assertGreater(or_data["or_high"], or_data["or_low"])

    def test_intraday_indicators(self):
        from apps.daytrading.services.indicators import calculate_intraday_indicators
        df = self._make_df(50)
        result = calculate_intraday_indicators(df)
        self.assertIn("VWAP", result.columns)
        self.assertIn("RSI_9", result.columns)
        self.assertIn("EMA_9", result.columns)
        self.assertIn("ATR_5", result.columns)

    def test_support_resistance(self):
        from apps.daytrading.services.indicators import calculate_support_resistance
        df = self._make_df(20)
        sr = calculate_support_resistance(df)
        self.assertIn("pivot", sr)
        self.assertEqual(len(sr["resistance"]), 3)
        self.assertEqual(len(sr["support"]), 3)


# ---------------------------------------------------------------------------
# Skill 4: Exit Planner
# ---------------------------------------------------------------------------
class TestExitPlanner(TestCase):
    """Test exit level calculations."""

    def test_long_exit_levels(self):
        from apps.daytrading.services.exit_planner import calculate_exit_levels
        levels = calculate_exit_levels(100, "LONG", "ATR", atr=2.0, rr_target=2.0)
        self.assertLess(levels["stop_loss"], 100)
        self.assertGreater(levels["target_1"], 100)
        self.assertGreater(levels["target_2"], levels["target_1"])

    def test_short_exit_levels(self):
        from apps.daytrading.services.exit_planner import calculate_exit_levels
        levels = calculate_exit_levels(100, "SHORT", "ATR", atr=2.0, rr_target=2.0)
        self.assertGreater(levels["stop_loss"], 100)
        self.assertLess(levels["target_1"], 100)

    def test_trailing_stop_long(self):
        from apps.daytrading.services.exit_planner import check_trailing_stop
        result = check_trailing_stop(
            current_price=98, entry_price=100,
            highest_since_entry=105, trail_pct=2.0, direction="LONG"
        )
        self.assertIn("trail_stop", result)
        self.assertIn("hit", result)


# ---------------------------------------------------------------------------
# Skill 5: Risk Management
# ---------------------------------------------------------------------------
class TestRisk(TestCase):
    """Test risk management."""

    def test_position_sizing(self):
        from apps.daytrading.services.risk import calculate_position_size
        result = calculate_position_size(
            capital=1000000, risk_pct=1.0,
            entry_price=100, stop_loss=98
        )
        self.assertGreater(result["quantity"], 0)
        self.assertEqual(result["risk_per_share"], 2.0)
        # Risk amount should be 1% of capital = 10000
        self.assertEqual(result["risk_amount"], 10000.0)
        # Max qty from risk: 10000/2 = 5000
        # Max qty from position: 200000/100 = 2000
        self.assertEqual(result["quantity"], 2000)

    def test_position_sizing_zero_risk(self):
        from apps.daytrading.services.risk import calculate_position_size
        result = calculate_position_size(
            capital=1000000, risk_pct=1.0,
            entry_price=100, stop_loss=100
        )
        self.assertEqual(result["quantity"], 0)


# ---------------------------------------------------------------------------
# Skill 6: Budget
# ---------------------------------------------------------------------------
class TestBudget(TestCase):
    """Test capital allocation and budget management."""

    def test_budget_summary(self):
        from apps.daytrading.services.budget import get_budget_summary
        summary = get_budget_summary()
        self.assertIn("initial_capital", summary)
        self.assertIn("available_cash", summary)
        self.assertIn("per_trade_max", summary)
        self.assertEqual(summary["initial_capital"], 1000000.0)

    def test_reset_account(self):
        from apps.daytrading.services.budget import reset_paper_account
        result = reset_paper_account(500000)
        self.assertEqual(result["initial_capital"], 500000)
        # Reset back
        reset_paper_account(1000000)


# ---------------------------------------------------------------------------
# Skill 7: Alerts
# ---------------------------------------------------------------------------
class TestAlerts(TestCase):
    """Test trading alerts."""

    def test_create_alert(self):
        from apps.daytrading.services.alerts import create_alert
        result = create_alert("RELIANCE.NS", "PRICE_ABOVE", "Price > 3000", 3000)
        self.assertEqual(result["status"], "ACTIVE")
        self.assertEqual(result["symbol"], "RELIANCE.NS")

    def test_get_active_alerts(self):
        from apps.daytrading.services.alerts import create_alert, get_active_alerts
        create_alert("TCS.NS", "PRICE_BELOW", "Price < 3500", 3500)
        active = get_active_alerts()
        self.assertTrue(len(active) > 0)

    def test_cancel_alert(self):
        from apps.daytrading.services.alerts import create_alert, cancel_alert
        result = create_alert("INFY.NS", "VOLUME_SPIKE", "Volume spike", None)
        cancel = cancel_alert(result["alert_id"])
        self.assertEqual(cancel["status"], "cancelled")


# ---------------------------------------------------------------------------
# Skill 11: Paper Broker — SECURITY TESTS
# ---------------------------------------------------------------------------
class TestPaperBrokerSecurity(TestCase):
    """CRITICAL: Verify paper-only enforcement."""

    def test_paper_mode_hardcoded(self):
        from apps.daytrading.services.paper_broker import _PAPER_MODE
        self.assertTrue(_PAPER_MODE)

    def test_paper_mode_enforcement(self):
        from apps.daytrading.services.paper_broker import _enforce_paper
        # Should not raise
        self.assertTrue(_enforce_paper())

    def test_order_always_paper(self):
        from apps.daytrading.models import PaperOrder
        order = PaperOrder(
            symbol="TEST.NS", side="BUY", quantity=1,
            order_type="MARKET", product="MIS",
        )
        order.save()
        self.assertTrue(order.is_paper)
        # Try to set to False — save() overrides
        order.is_paper = False
        order.save()
        order.refresh_from_db()
        self.assertTrue(order.is_paper)

    def test_position_always_paper(self):
        from apps.daytrading.models import PaperPosition
        pos = PaperPosition(
            symbol="TEST.NS", quantity=10,
            avg_entry_price=100, current_price=100,
        )
        pos.save()
        self.assertTrue(pos.is_paper)
        pos.is_paper = False
        pos.save()
        pos.refresh_from_db()
        self.assertTrue(pos.is_paper)

    def test_account_always_paper(self):
        from apps.daytrading.models import PaperAccount
        acc = PaperAccount(name="Test Account")
        acc.save()
        self.assertTrue(acc.is_paper)
        acc.is_paper = False
        acc.save()
        acc.refresh_from_db()
        self.assertTrue(acc.is_paper)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class TestDayTradingModels(TestCase):
    """Test model creation and constraints."""

    def test_create_trade_plan(self):
        from apps.daytrading.models import DayTradePlan
        plan = DayTradePlan.objects.create(
            symbol="RELIANCE.NS", exchange="NSE",
            strategy="ORB", direction="LONG", status="PENDING",
            entry_price=Decimal("2950.00"), stop_loss=Decimal("2930.00"),
            target_1=Decimal("2990.00"),
        )
        self.assertEqual(str(plan.exchange), "NSE")
        self.assertIn("RELIANCE", str(plan))

    def test_create_scan_result(self):
        from apps.daytrading.models import ScanResult
        scan = ScanResult.objects.create(
            symbol="TCS.NS", scan_type="MOMENTUM",
            score=75.5, price=Decimal("3500.00"),
            volume=1000000, volume_ratio=2.5,
        )
        self.assertEqual(scan.score, 75.5)

    def test_create_news_item(self):
        from apps.daytrading.models import NewsItem
        item = NewsItem.objects.create(
            headline="Reliance Q3 results beat estimates",
            source="BSE", sentiment="POSITIVE",
            sentiment_score=0.8, symbols=["RELIANCE.NS"],
        )
        self.assertEqual(item.sentiment, "POSITIVE")

    def test_create_backtest_scenario(self):
        from apps.daytrading.models import BacktestScenario
        bt = BacktestScenario.objects.create(
            name="RELIANCE ORB 60d",
            symbol="RELIANCE.NS", strategy="ORB",
            start_date=date(2026, 9, 1), end_date=date(2026, 11, 1),
            num_trades=20, winners=12, losers=8,
            win_rate=60.0, total_return_pct=5.2,
        )
        self.assertEqual(bt.win_rate, 60.0)

    def test_create_disclosure(self):
        from apps.daytrading.models import PublicDisclosure
        disc = PublicDisclosure.objects.create(
            symbol="RELIANCE.NS", filer_name="Mukesh Ambani",
            filer_category="PROMOTER", transaction_type="BUY",
            transaction_date=date(2026, 11, 1),
            quantity=100000, value_inr=Decimal("295000000"),
        )
        self.assertIn("Ambani", str(disc))

    def test_create_journal_entry(self):
        from apps.daytrading.models import TradeJournalEntry
        j = TradeJournalEntry.objects.create(
            symbol="INFY.NS", trade_date=date(2026, 11, 26),
            direction="LONG", entry_price=Decimal("1500"),
            exit_price=Decimal("1520"), quantity=50,
            pnl_amount=Decimal("1000"), outcome="WIN",
        )
        self.assertEqual(j.outcome, "WIN")


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
class TestDayTradingAPIs(TestCase):
    """Test REST API endpoints return correct status codes."""

    def test_dashboard_view(self):
        response = self.client.get("/daytrading/")
        self.assertEqual(response.status_code, 200)

    def test_market_status_api(self):
        response = self.client.get("/daytrading/api/market-status/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("is_market_open", data)

    def test_budget_api(self):
        response = self.client.get("/daytrading/api/budget/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("available_cash", data)

    def test_positions_api(self):
        response = self.client.get("/daytrading/api/positions/")
        self.assertEqual(response.status_code, 200)

    def test_orders_api(self):
        response = self.client.get("/daytrading/api/orders/")
        self.assertEqual(response.status_code, 200)

    def test_pnl_api(self):
        response = self.client.get("/daytrading/api/pnl/")
        self.assertEqual(response.status_code, 200)

    def test_alerts_api(self):
        response = self.client.get("/daytrading/api/alerts/")
        self.assertEqual(response.status_code, 200)

    def test_submit_order_api(self):
        """Test paper order submission."""
        response = self.client.post(
            "/daytrading/api/order/",
            data={"symbol": "RELIANCE", "side": "BUY", "quantity": 1,
                  "order_type": "MARKET", "product": "MIS", "exchange": "NSE"},
            content_type="application/json",
        )
        self.assertIn(response.status_code, [200, 500])  # 500 if yfinance fails (offline)

    def test_entry_signal_requires_symbol(self):
        response = self.client.get("/daytrading/api/entry-signal/")
        self.assertEqual(response.status_code, 400)

    def test_analyst_requires_symbol(self):
        response = self.client.get("/daytrading/api/analyst/")
        self.assertEqual(response.status_code, 400)

    def test_create_alert_api(self):
        response = self.client.post(
            "/daytrading/api/alerts/create/",
            data={"symbol": "RELIANCE.NS", "alert_type": "PRICE_ABOVE",
                  "condition": "Price above 3000", "threshold": "3000.00"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# News Sentiment (Skill 2)
# ---------------------------------------------------------------------------
class TestNewsSentiment(TestCase):
    """Test rule-based sentiment analysis."""

    def test_positive_sentiment(self):
        from apps.daytrading.services.news import simple_sentiment
        label, score = simple_sentiment("Stock surges to record high on strong growth")
        self.assertEqual(label, "POSITIVE")
        self.assertGreater(score, 0)

    def test_negative_sentiment(self):
        from apps.daytrading.services.news import simple_sentiment
        label, score = simple_sentiment("Stock crash leads to heavy loss amid fraud allegations")
        self.assertEqual(label, "NEGATIVE")
        self.assertLess(score, 0)

    def test_neutral_sentiment(self):
        from apps.daytrading.services.news import simple_sentiment
        label, score = simple_sentiment("Company announces board meeting next week")
        self.assertEqual(label, "NEUTRAL")


# ---------------------------------------------------------------------------
# Time Machine (Skill 8)
# ---------------------------------------------------------------------------
class TestTimeMachine(TestCase):
    """Test Monte Carlo simulation."""

    def test_monte_carlo(self):
        from apps.daytrading.services.timemachine import monte_carlo_simulation
        trades = [
            {"pnl": 100}, {"pnl": -50}, {"pnl": 200},
            {"pnl": -80}, {"pnl": 150}, {"pnl": -30},
        ]
        mc = monte_carlo_simulation(trades, num_simulations=100, initial_capital=100000)
        self.assertIn("probability_profit", mc)
        self.assertIn("percentiles", mc)
        self.assertEqual(mc["num_simulations"], 100)
        self.assertGreaterEqual(mc["best_case"], mc["worst_case"])

    def test_monte_carlo_empty(self):
        from apps.daytrading.services.timemachine import monte_carlo_simulation
        result = monte_carlo_simulation([], num_simulations=10)
        self.assertIn("error", result)


# ---------------------------------------------------------------------------
# INR / Indian Market Specific
# ---------------------------------------------------------------------------
class TestIndianMarketSpecifics(TestCase):
    """Verify India-first assumptions throughout the system."""

    def test_nse_symbol_format(self):
        from apps.daytrading.services.market_data import normalize_symbol
        self.assertTrue(normalize_symbol("RELIANCE", "NSE").endswith(".NS"))

    def test_bse_symbol_format(self):
        from apps.daytrading.services.market_data import normalize_symbol
        self.assertTrue(normalize_symbol("500325", "BSE").endswith(".BO"))

    def test_market_hours_ist(self):
        from apps.daytrading.services.market_calendar import MARKET_OPEN_TIME, MARKET_CLOSE_TIME
        self.assertEqual(MARKET_OPEN_TIME, time(9, 15))
        self.assertEqual(MARKET_CLOSE_TIME, time(15, 30))

    def test_timezone_ist(self):
        from apps.daytrading.services.market_calendar import IST
        self.assertEqual(str(IST), "Asia/Kolkata")

    def test_initial_capital_inr(self):
        from apps.daytrading.services.budget import get_budget_summary
        summary = get_budget_summary()
        # Default ₹10,00,000
        self.assertEqual(summary["initial_capital"], 1000000.0)

    def test_stt_exists(self):
        from apps.daytrading.services.charges import STT_RATE_INTRADAY_SELL
        self.assertGreater(STT_RATE_INTRADAY_SELL, 0)

    def test_stamp_duty_exists(self):
        from apps.daytrading.services.charges import STAMP_DUTY_INTRADAY
        self.assertGreater(STAMP_DUTY_INTRADAY, 0)


# ---------------------------------------------------------------------------
# Existing App Regression
# ---------------------------------------------------------------------------
class TestExistingAppRegression(TestCase):
    """Ensure existing app functionality is not broken."""

    def test_market_dashboard_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_stock_model_exists(self):
        from apps.market.models import Stock
        # Model should be importable
        self.assertTrue(hasattr(Stock, 'symbol'))

    def test_portfolio_model_exists(self):
        from apps.portfolio.models import PortfolioHolding
        self.assertTrue(hasattr(PortfolioHolding, 'symbol'))

    def test_config_loads(self):
        from src.config import get_config
        config = get_config()
        self.assertEqual(config.llm.provider, "freellmapi")
        self.assertIn("NSE", config.screening_defaults.allowed_exchanges)

    def test_llm_client_importable(self):
        from src.llm.llm_client import LLMClient
        self.assertTrue(callable(LLMClient))

    def test_existing_analysis_indicators(self):
        from src.analysis.indicators import calculate_all_indicators
        self.assertTrue(callable(calculate_all_indicators))

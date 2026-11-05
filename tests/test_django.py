"""Comprehensive test suite for Django application, models, views, and APIs."""

import os
import json
from datetime import date
import pytest
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_agent_django.settings')
django.setup()

try:
    from django.test.utils import setup_test_environment
    setup_test_environment()
except RuntimeError:
    pass

from django.test import TestCase, Client
from django.urls import reverse

from apps.market.models import Stock, PriceHistory, FundamentalData, AgentEvaluation, BacktestRunRecord
from apps.market.services import seed_universe_if_empty, get_market_indices_summary
from src.analysis.dcf_valuator import DCFValuator, DCFParameters


class TestDjangoModels(TestCase):
    """Test Django ORM models, methods, and properties."""

    def setUp(self):
        self.stock, _ = Stock.objects.get_or_create(
            symbol="TEST_CORP.NS",
            defaults={
                "name": "Test Corporation Limited",
                "exchange": "NSE",
                "sector": "Information Technology",
                "industry": "IT Services",
                "market_cap": 6200000000000.0,
                "current_price": 1500.0,
                "day_change": 15.0,
                "day_change_pct": 1.01,
                "pe_ratio": 24.0,
                "pb_ratio": 7.5,
                "is_active": True
            }
        )

    def test_stock_properties(self):
        self.assertEqual(self.stock.clean_symbol, "TEST_CORP")
        self.assertAlmostEqual(self.stock.market_cap_crores, 620000.0, places=1)
        self.assertIn("Cr", self.stock.formatted_mcap)
        self.assertIn("TEST_CORP", str(self.stock))

    def test_price_history_creation(self):
        ph, _ = PriceHistory.objects.get_or_create(
            stock=self.stock,
            date=date(2026, 10, 20),
            defaults={
                "open": 1490.0,
                "high": 1510.0,
                "low": 1485.0,
                "close": 1500.0,
                "volume": 500000
            }
        )
        self.assertEqual(ph.stock.symbol, "TEST_CORP.NS")
        self.assertEqual(ph.close, 1500.0)

    def test_fundamental_data_creation(self):
        fund, _ = FundamentalData.objects.get_or_create(
            stock=self.stock,
            period_date=date(2026, 3, 31),
            period_type="A",
            defaults={
                "revenue": 150000000000.0,
                "net_profit": 25000000000.0,
                "roe": 31.5,
                "roce": 39.0,
                "debt_to_equity": 0.08
            }
        )
        self.assertEqual(fund.roe, 31.5)
        self.assertEqual(fund.period_type, "A")

    def test_agent_evaluation_creation(self):
        ev, _ = AgentEvaluation.objects.get_or_create(
            stock=self.stock,
            evaluation_date=date(2026, 10, 20),
            defaults={
                "composite_score": 78.5,
                "quality_score": 85.0,
                "valuation_score": 60.0,
                "rank": 1,
                "action": "Strong Buy"
            }
        )
        self.assertEqual(ev.rank, 1)
        self.assertEqual(ev.action, "Strong Buy")


class TestMarketViews(TestCase):
    """Test Market and Dashboard views."""

    def setUp(self):
        self.client = Client()
        seed_universe_if_empty()

    def test_dashboard_view(self):
        response = self.client.get(reverse('market:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Executive Market Dashboard", response.content)
        if response.context:
            self.assertIn('indices', response.context)
            self.assertIn('top_rankings', response.context)

    def test_settings_view(self):
        response = self.client.get(reverse('market:settings'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"System Settings", response.content)
        if response.context:
            self.assertIn('weights', response.context)
            self.assertIn('screening', response.context)

    def test_search_stocks_api(self):
        response = self.client.get(reverse('market:search_stocks') + '?q=RELIANCE')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertTrue(len(data['results']) > 0)
        symbols = [r['clean_symbol'] for r in data['results']]
        self.assertTrue('RELIANCE' in symbols or '500325' in symbols)

    def test_market_pulse_api(self):
        response = self.client.get(reverse('market:market_pulse_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('indices', data)
        self.assertIn('breadth', data)
        self.assertEqual(len(data['indices']), 4)

    def test_sync_market_api(self):
        response = self.client.get(reverse('market:sync_market_api') + '?symbols=RELIANCE.NS')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))

    def test_cli_analysis_view(self):
        response = self.client.get(reverse('market:cli_analysis'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CLI &amp; Batch Analysis Engine")
        self.assertContains(response, "Analyze BSE 500 (Top 60)")
        self.assertContains(response, "Live Execution Console")
        self.assertContains(response, "downwardOutputWindow")

    def test_api_run_and_status_cli(self):
        # 1. Test POST run CLI analyze
        payload = {
            "command": "analyze",
            "index": "bse500",
            "top": 2,
            "sector": "",
            "min_market_cap": "",
            "output_dir": "data/reports"
        }
        res_run = self.client.post(
            reverse('market:api_run_cli'),
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res_run.status_code, 200)
        data_run = res_run.json()
        self.assertEqual(data_run["status"], "started")
        self.assertIn("job_", data_run["job_id"])
        self.assertIn("bse500", data_run["command"])
        job_id = data_run["job_id"]

        # 2. Test status polling
        res_status = self.client.get(reverse('market:api_cli_status', args=[job_id]))
        self.assertEqual(res_status.status_code, 200)
        data_status = res_status.json()
        self.assertIn(data_status["status"], ["running", "completed"])

        # 3. Test stop endpoint
        res_stop = self.client.post(reverse('market:api_cli_stop', args=[job_id]))
        self.assertEqual(res_stop.status_code, 200)
        self.assertIn(res_stop.json()["status"], ["stopped", "already_finished"])

    def test_cli_report_view_security(self):
        # Test non-existent file
        res = self.client.get(reverse('market:cli_report_view', args=['non_existent_file.md']))
        self.assertEqual(res.status_code, 404)

        # Test path traversal prevention
        res_trav = self.client.get('/cli-analysis/report/../../manage.py')
        self.assertEqual(res_trav.status_code, 404)


class TestResearchViews(TestCase):
    """Test Stock Research Workstation and Interactive DCF API."""

    def setUp(self):
        self.client = Client()
        seed_universe_if_empty()

    def test_stock_research_view(self):
        response = self.client.get(reverse('research:stock_detail', args=['RELIANCE.NS']))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Research & Analysis", response.content)
        if response.context:
            self.assertEqual(response.context['stock'].clean_symbol, 'RELIANCE')
            self.assertIn('dcf', response.context)

    def test_calculate_dcf_api(self):
        payload = {
            'fcf_per_share': 80.0,
            'fcf_cagr': 14.0,
            'wacc': 11.0,
            'terminal_growth': 3.0,
            'cash_per_share': 50.0,
            'debt_per_share': 10.0
        }
        response = self.client.post(
            reverse('research:calculate_dcf_api', args=['RELIANCE.NS']),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('intrinsic_value_per_share', data)
        self.assertIn('margin_of_safety_pct', data)
        self.assertTrue(data['intrinsic_value_per_share'] > 0)

    def test_sync_stock_quote_api(self):
        response = self.client.get(reverse('research:sync_stock_quote_api', args=['RELIANCE.NS']))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('clean_symbol'), 'RELIANCE')
        self.assertIsNotNone(data.get('current_price'))


class TestRankingsViews(TestCase):
    """Test Screener, Ranking, and Export views."""

    def setUp(self):
        self.client = Client()
        seed_universe_if_empty()

    def test_screener_view(self):
        response = self.client.get(reverse('rankings:screener'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Screened Watchlist", response.content)

    def test_screener_filtering(self):
        response = self.client.get(reverse('rankings:screener') + '?exchange=NSE&action=Strong+Buy')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Screened Watchlist", response.content)
        if response.context and 'rankings' in response.context:
            for r in response.context['rankings']:
                self.assertEqual(r.stock.exchange, 'NSE')
                self.assertEqual(r.action, 'Strong Buy')

    def test_export_rankings_csv(self):
        response = self.client.get(reverse('rankings:export_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])


class TestBacktestingViews(TestCase):
    """Test Quantitative Backtester Workstation."""

    def setUp(self):
        self.client = Client()
        seed_universe_if_empty()

    def test_backtest_view(self):
        response = self.client.get(reverse('backtesting:backtest_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Quantitative Backtest Workstation", response.content)
        if response.context and 'record' in response.context:
            self.assertTrue(response.context['record'].cagr > 0)


class TestRESTAPI(TestCase):
    """Test Django REST Framework endpoints."""

    def setUp(self):
        self.client = Client()
        seed_universe_if_empty()

    def test_api_stocks_list(self):
        response = self.client.get('/api/v1/stocks/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertTrue(len(data['results']) > 0)

    def test_api_rankings_list(self):
        response = self.client.get('/api/v1/rankings/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertTrue(len(data['results']) > 0)

    def test_api_market_summary(self):
        response = self.client.get('/api/v1/market/summary/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('indices', data)
        self.assertIn('breadth', data)

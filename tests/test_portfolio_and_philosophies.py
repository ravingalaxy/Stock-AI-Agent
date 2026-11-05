"""Tests for Portfolio Management, Risk Rules, and Legendary Investor Strategies."""

import pytest
from src.analysis.portfolio_manager import PortfolioManager, HoldingItem, get_sample_holdings
from src.analysis.investor_philosophy import LegendaryInvestorStrategies
from src.analysis.dcf_valuator import DCFValuator, DCFParameters


class TestPortfolioManager:
    """Tests for PortfolioManager calculations and guardrails."""

    def test_sample_holdings_evaluation(self):
        manager = PortfolioManager(max_single_stock_pct=20.0, max_sector_pct=30.0)
        holdings = get_sample_holdings()
        assert len(holdings) > 0
        
        report = manager.evaluate_portfolio(holdings)
        assert report['total_invested'] > 0
        assert report['total_current'] > 0
        assert report['holdings_count'] == len(holdings)
        assert 'sector_allocation' in report
        assert 'alerts' in report
        assert 'rebalancing_suggestions' in report

    def test_concentration_alerts_single_stock(self):
        manager = PortfolioManager(max_single_stock_pct=20.0, max_sector_pct=30.0)
        # Create an overweight holding (>20% of portfolio)
        holdings = [
            HoldingItem("OVERWEIGHT.NS", "Overweight Corp", "Tech", 1000, 100.0, 100.0),  # 100,000
            HoldingItem("DIVERSE.NS", "Diverse Corp", "FMCG", 100, 100.0, 100.0),          # 10,000
        ]
        report = manager.evaluate_portfolio(holdings)
        alerts = report['alerts']
        single_stock_alerts = [a for a in alerts if a['category'] == 'single_stock']
        assert len(single_stock_alerts) > 0
        assert "OVERWEIGHT.NS" in single_stock_alerts[0]['message']

    def test_concentration_alerts_sector(self):
        manager = PortfolioManager(max_single_stock_pct=20.0, max_sector_pct=30.0)
        # Overweight sector (>30%)
        holdings = [
            HoldingItem("TECH1.NS", "Tech One", "Technology", 100, 100.0, 100.0),  # 10k
            HoldingItem("TECH2.NS", "Tech Two", "Technology", 100, 100.0, 100.0),  # 10k
            HoldingItem("TECH3.NS", "Tech Three", "Technology", 100, 100.0, 100.0),# 10k (30k Tech)
            HoldingItem("AUTO1.NS", "Auto One", "Automobile", 100, 100.0, 100.0),  # 10k (10k Auto)
        ]
        # Tech is 75% > 30%
        report = manager.evaluate_portfolio(holdings)
        sector_alerts = [a for a in report['alerts'] if a['category'] == 'sector']
        assert len(sector_alerts) > 0
        assert "Technology" in sector_alerts[0]['message']

    def test_position_size_calculator(self):
        manager = PortfolioManager()
        # 1,000,000 capital, 1% risk (10,000 INR), entry 1000, stop 950 (50 risk/share) -> 200 shares
        res = manager.calculate_position_size(
            portfolio_capital=1000000.0,
            risk_pct=1.0,
            entry_price=1000.0,
            stop_loss_price=950.0
        )
        assert res['recommended_shares'] == 200
        assert res['position_capital'] == 200000.0
        assert res['max_loss_inr'] == 10000.0
        assert res['position_weight_pct'] == 20.0

    def test_stop_target_calculator(self):
        manager = PortfolioManager()
        res = manager.calculate_stop_target(entry_price=1000.0, risk_pct=5.0, target_ratio=2.0)
        assert res['stop_loss_price'] == 950.0
        assert res['target_price_1'] == 1075.0
        assert res['target_price_2'] == 1100.0


class TestLegendaryInvestorStrategies:
    """Tests for all 9 legendary investor strategies."""

    @pytest.fixture
    def sample_agent_outputs(self):
        return {
            'fundamentals': {
                'ratios': {
                    'pe_ratio': 18.5,
                    'pb_ratio': 2.8,
                    'roe': 22.0,
                    'roce': 24.5,
                    'debt_to_equity': 0.25,
                    'interest_coverage': 12.0,
                    'fcf_margin': 0.16,
                    'net_margin': 0.18,
                    'promoter_holding': 58.0,
                    'promoter_pledge': 0.0,
                    'dividend_yield': 1.8,
                },
                'growth_metrics': {
                    'profit_cagr': 0.18,
                    'revenue_cagr': 0.15,
                },
                'red_flags': [],
            },
            'technical_indicators': {},
            'governance_issues': [],
            'risk_score': 20.0,
            'quality_imprint': [],
            'imprint_plan': [],
            'innovation_score': 70,
            'research_thrusts': [],
            'sector_analysis': {'sector': 'Technology'},
            'current_price': 1500.0,
        }

    def test_all_nine_strategies(self, sample_agent_outputs):
        engine = LegendaryInvestorStrategies()
        expected_keys = [
            'buffett', 'munger', 'peter_lynch', 'ben_graham', 'joel_greenblatt',
            'jhunjhunwala', 'philip_fisher', 'dolly_khanna', 'porinju_veliyath'
        ]
        assert set(engine.strategies.keys()) == set(expected_keys)

        for key in expected_keys:
            res = engine.apply_strategy("TEST.NS", sample_agent_outputs, key)
            assert 'score' in res
            assert 0 <= res['score'] <= 100
            assert 'label' in res
            assert res['label'] in ["BUY", "HOLD", "AVOID"]
            assert 'reason' in res
            assert 'key_risks' in res
            assert isinstance(res['key_risks'], list)


class TestDCFValuationEngine:
    """Tests for DCF Institutional Valuation."""

    def test_dcf_fade_model(self):
        params = DCFParameters(
            forecast_years=5,
            transition_years=5,
            fcf_cagr=0.15,
            terminal_growth_rate=0.045,
            wacc=0.115,
            current_fcf_per_share=50.0,
            net_debt_per_share=0.0
        )
        valuator = DCFValuator("Test Company")
        res = valuator.calculate_dcf(params)
        assert res['intrinsic_value'] > 0
        assert res['pv_forecast_sum'] > 0
        assert res['terminal_value'] > 0
        assert 'sensitivity_matrix' in res

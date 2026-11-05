"""Test suite for AI Stock Research Agent."""

import pytest
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta

from src.utils.helpers import format_inr, format_percentage, safe_divide, parse_date
from src.utils.validators import normalize_ticker, clean_ticker_display, validate_financial_ratio, validate_ticker_list
from src.analysis.indicators import calculate_all_indicators, get_latest_indicators, detect_chart_patterns
from src.analysis.scoring import ScoringEngine, ScoreBreakdown
from src.analysis.valuation import ValuationEngine, score_valuation
from src.storage.database import Base, Stock, PriceHistory, FundamentalData, NewsArticle, AgentEvaluation


class TestHelpers:
    """Tests for utility helpers."""
    
    def test_format_inr(self):
        assert format_inr(10_000_000) == "₹1.00 Cr"
        assert format_inr(5_000_000) == "₹50.00 L"
        assert format_inr(100_000) == "₹1.00 L"
        assert format_inr(50_000) == "₹50,000.00"
        assert format_inr(-10_000_000) == "-₹1.00 Cr"
        assert format_inr(None) == "N/A"
        assert format_inr(float('nan')) == "N/A"
        
    def test_format_percentage(self):
        assert format_percentage(0.1234) == "12.34%"
        assert format_percentage(0.05) == "5.00%"
        assert format_percentage(None) == "N/A"
        
    def test_safe_divide(self):
        assert safe_divide(10, 2) == 5.0
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(10, 0, default=-1) == -1
        assert safe_divide(float('nan'), 2) == 0.0
        assert safe_divide(10, float('nan')) == 0.0
        
    def test_parse_date(self):
        dt = parse_date("2024-01-15")
        assert dt.year == 2024 and dt.month == 1 and dt.day == 15
        dt = parse_date("2024-01-15T10:30:00")
        assert dt.hour == 10
        dt = parse_date(date(2024, 1, 15))
        assert dt.date() == date(2024, 1, 15)


class TestValidators:
    """Tests for validation functions."""
    
    def test_normalize_ticker(self):
        assert normalize_ticker("RELIANCE") == "RELIANCE.NS"
        assert normalize_ticker("reliance") == "RELIANCE.NS"
        assert normalize_ticker("RELIANCE.NS") == "RELIANCE.NS"
        assert normalize_ticker("500325") == "500325.BO"
        assert normalize_ticker("500325.BO") == "500325.BO"
        
    def test_clean_ticker_display(self):
        assert clean_ticker_display("RELIANCE.NS") == "RELIANCE"
        assert clean_ticker_display("500325.BO") == "500325"
        
    def test_validate_financial_ratio(self):
        assert validate_financial_ratio(15.5) == 15.5
        assert validate_financial_ratio(None) == 0.0
        assert validate_financial_ratio("20.3") == 20.3
        assert validate_financial_ratio(float('nan')) == 0.0
        assert validate_financial_ratio(100, max_val=50) == 50
        assert validate_financial_ratio(-5, min_val=0) == 0
        
    def test_validate_ticker_list(self):
        symbols = ["RELIANCE", "TCS.NS", "500325", "INVALID!"]
        result = validate_ticker_list(symbols)
        assert "RELIANCE.NS" in result
        assert "TCS.NS" in result
        assert "500325.BO" in result
        assert "INVALID!" not in result


class TestIndicators:
    """Tests for technical indicators."""
    
    @pytest.fixture
    def sample_price_data(self):
        """Create sample OHLCV data."""
        dates = pd.date_range(start='2023-01-01', periods=300, freq='D')
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.randn(300) * 0.5)
        high = close + np.abs(np.random.randn(300) * 0.3)
        low = close - np.abs(np.random.randn(300) * 0.3)
        open_ = close + np.random.randn(300) * 0.2
        volume = np.abs(np.random.randn(300) * 1000000) + 500000
        
        df = pd.DataFrame({
            'Open': open_, 'High': high, 'Low': low, 'Close': close, 'Volume': volume
        }, index=dates)
        return df
    
    def test_calculate_all_indicators(self, sample_price_data):
        result = calculate_all_indicators(sample_price_data)
        
        # Check key columns exist
        expected_cols = ['SMA_20', 'SMA_50', 'SMA_200', 'RSI_14', 'MACD', 'BB_Upper', 'BB_Lower', 'ATR_14']
        for col in expected_cols:
            assert col in result.columns
            
        # Check values are reasonable
        assert result['RSI_14'].dropna().between(0, 100).all()
        assert result['SMA_20'].dropna().notna().all()
        assert result['MACD'].dropna().notna().all()
        
    def test_get_latest_indicators(self, sample_price_data):
        df = calculate_all_indicators(sample_price_data)
        indicators = get_latest_indicators(df)
        
        assert 'RSI_14' in indicators
        assert 'trend_sma' in indicators
        assert 'macd_signal' in indicators
        assert indicators['trend_sma'] in ['Bullish', 'Bearish']
        
    def test_detect_chart_patterns(self, sample_price_data):
        df = calculate_all_indicators(sample_price_data)
        patterns = detect_chart_patterns(df)
        # Just verify it runs without error
        assert isinstance(patterns, list)


class TestScoring:
    """Tests for scoring engine."""
    
    @pytest.fixture
    def scoring_engine(self):
        return ScoringEngine()
    
    def test_score_quality_high(self, scoring_engine):
        ratios = {
            'roce': 25, 'roe': 22, 'operating_margin': 18,
            'debt_to_equity': 0.2, 'interest_coverage': 10,
            'fcf_margin': 12, 'cfo_to_net_income': 1.2,
            'promoter_holding_pct': 55, 'promoter_pledged_pct': 2
        }
        score = scoring_engine.score_quality(ratios, [])
        assert score > 80
        
    def test_score_quality_low(self, scoring_engine):
        ratios = {
            'roce': 5, 'roe': 6, 'operating_margin': 3,
            'debt_to_equity': 2.5, 'interest_coverage': 1.2,
            'fcf_margin': -5, 'cfo_to_net_income': 0.3,
            'promoter_holding_pct': 20, 'promoter_pledged_pct': 40
        }
        score = scoring_engine.score_quality(ratios, ['Red flag 1', 'Red flag 2', 'Red flag 3'])
        # With 3 red flags = 15 penalty, base 50 + small positives - 15 = ~44
        assert score < 50
        
    def test_score_growth(self, scoring_engine):
        growth = {'revenue_cagr': 0.15, 'profit_cagr': 0.20, 'latest_operating_margin': 18, 'latest_roe': 22}
        history = [{'operating_margin': 15, 'net_profit': 100}, {'operating_margin': 14, 'net_profit': 90}, 
                   {'operating_margin': 13, 'net_profit': 80}, {'operating_margin': 12, 'net_profit': 70}]
        score = scoring_engine.score_growth(growth, history)
        assert score > 60
        
    def test_score_momentum(self, scoring_engine):
        tech = {
            'trend_sma': 'Bullish', 'price_vs_sma50': 'Above', 'price_vs_sma200': 'Above',
            'macd_signal': 'Bullish', 'RSI_14': 60, 'momentum_20d': 5, 'momentum_60d': 15,
            'Volume_Ratio': 1.5
        }
        rs = {'RS_60d': 0.08, 'RS_120d': 0.12}
        score = scoring_engine.score_momentum(tech, rs)
        assert score > 70
        
    def test_calculate_composite(self, scoring_engine):
        components = {
            'quality': 80, 'growth': 70, 'valuation': 60,
            'momentum': 75, 'catalyst': 65, 'risk_penalty': 20
        }
        breakdown = scoring_engine.calculate_composite(components)
        
        # Verify calculation: 0.3*80 + 0.2*70 + 0.15*60 + 0.15*75 + 0.1*65 - 0.1*20
        expected = 24 + 14 + 9 + 11.25 + 6.5 - 2
        assert abs(breakdown.composite - expected) < 0.1
        assert 0 <= breakdown.composite <= 100


class TestValuation:
    """Tests for valuation engine."""
    
    def test_calculate_valuation_metrics(self):
        from src.storage.database import StockRepository
        from unittest.mock import Mock
        
        repo = Mock(spec=StockRepository)
        engine = ValuationEngine(repo)
        
        # Values: shares = 10M, price = 200 => mcap = 2,000,000,000
        # Net profit = 1,500,000,000
        # PE = 2,000,000,000 / 1,500,000,000 = 1.33
        fundamentals = {
            'revenue': 10_000_000_000, 'net_profit': 1_500_000_000, 'ebitda': 2_000_000_000,
            'total_equity': 8_000_000_000, 'total_debt': 1_000_000_000, 'fcf': 1_200_000_000,
            'shares_outstanding': 10_000_000, 'cash': 500_000_000
        }
        
        metrics = engine.calculate_valuation_metrics(fundamentals, 200, 10_000_000)
        
        assert metrics['pe_ratio'] == pytest.approx(1.33, rel=0.01)
        assert metrics['pb_ratio'] == pytest.approx(0.25, rel=0.01)
        assert metrics['ev_ebitda'] == pytest.approx(1.25, rel=0.01)


class TestDatabaseModels:
    """Tests for database model creation."""
    
    def test_stock_model(self):
        stock = Stock(
            symbol="RELIANCE.NS", name="Reliance Industries", 
            exchange="NSE", sector="Energy", market_cap=1500000000000
        )
        assert stock.symbol == "RELIANCE.NS"
        assert stock.exchange == "NSE"
        
    def test_price_history_model(self):
        ph = PriceHistory(
            symbol="RELIANCE.NS", date=date.today(),
            open=2500, high=2550, low=2480, close=2530, volume=1000000
        )
        assert ph.symbol == "RELIANCE.NS"
        assert ph.close == 2530


# Integration tests - marked to be skipped by default
@pytest.mark.skip(reason="Requires external API dependencies")
class TestIntegration:
    """Integration tests (require API access)."""
    
    def test_market_data_provider(self):
        from src.data.market_data import get_market_data_provider
        provider = get_market_data_provider()
        # This would need actual API - skip in CI
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
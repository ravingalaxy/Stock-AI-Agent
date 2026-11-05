from rest_framework import serializers
from apps.market.models import Stock, PriceHistory, FundamentalData, AgentEvaluation, BacktestRunRecord


class StockSerializer(serializers.ModelSerializer):
    market_cap_crores = serializers.FloatField(read_only=True)
    formatted_mcap = serializers.CharField(read_only=True)
    clean_symbol = serializers.CharField(read_only=True)

    class Meta:
        model = Stock
        fields = [
            'symbol', 'clean_symbol', 'name', 'isin', 'exchange', 'sector', 'industry',
            'market_cap', 'market_cap_crores', 'formatted_mcap', 'current_price',
            'day_change', 'day_change_pct', 'pe_ratio', 'pb_ratio', 'dividend_yield',
            'description', 'website', 'is_active', 'updated_at'
        ]


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume', 'sma_20', 'sma_50', 'rsi_14']


class FundamentalDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundamentalData
        fields = [
            'period_date', 'period_type', 'revenue', 'net_profit', 'ebitda',
            'operating_margin', 'net_margin', 'roe', 'roce', 'debt_to_equity',
            'interest_coverage', 'fcf', 'cfo', 'promoter_holding_pct'
        ]


class AgentEvaluationSerializer(serializers.ModelSerializer):
    stock = StockSerializer(read_only=True)

    class Meta:
        model = AgentEvaluation
        fields = [
            'rank', 'stock', 'evaluation_date', 'composite_score', 'quality_score',
            'growth_score', 'valuation_score', 'momentum_score', 'catalyst_score',
            'risk_score', 'action', 'confidence', 'bull_case', 'bear_case',
            'key_catalysts', 'risk_flags', 'investor_scores', 'probability_metrics',
            'dcf_valuation'
        ]


class BacktestRunRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BacktestRunRecord
        fields = [
            'run_id', 'strategy_name', 'start_date', 'end_date', 'rebalance_frequency',
            'initial_capital', 'final_capital', 'cagr', 'volatility', 'sharpe_ratio',
            'max_drawdown', 'win_rate', 'benchmark_cagr', 'alpha', 'beta',
            'equity_curve', 'trades'
        ]

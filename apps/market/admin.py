from django.contrib import admin
from .models import Stock, PriceHistory, FundamentalData, AgentEvaluation, BacktestRunRecord


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'exchange', 'sector', 'current_price', 'day_change_pct', 'market_cap_crores', 'is_active')
    list_filter = ('exchange', 'sector', 'is_active')
    search_fields = ('symbol', 'name', 'isin')
    ordering = ('symbol',)


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('stock', 'date', 'close', 'open', 'high', 'low', 'volume')
    list_filter = ('date',)
    search_fields = ('stock__symbol', 'stock__name')


@admin.register(FundamentalData)
class FundamentalDataAdmin(admin.ModelAdmin):
    list_display = ('stock', 'period_date', 'period_type', 'revenue', 'net_profit', 'roe', 'roce')
    list_filter = ('period_type', 'period_date')
    search_fields = ('stock__symbol',)


@admin.register(AgentEvaluation)
class AgentEvaluationAdmin(admin.ModelAdmin):
    list_display = ('rank', 'stock', 'composite_score', 'quality_score', 'valuation_score', 'action', 'evaluation_date')
    list_filter = ('action', 'evaluation_date')
    search_fields = ('stock__symbol', 'stock__name')


@admin.register(BacktestRunRecord)
class BacktestRunRecordAdmin(admin.ModelAdmin):
    list_display = ('run_id', 'strategy_name', 'start_date', 'end_date', 'cagr', 'sharpe_ratio', 'max_drawdown')
    list_filter = ('rebalance_frequency',)
    search_fields = ('run_id', 'strategy_name')

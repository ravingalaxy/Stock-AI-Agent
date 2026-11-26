"""Django admin registration for Day Trading models."""

from django.contrib import admin
from .models import (
    DayTradePlan, PaperOrder, PaperPosition, PaperFill,
    TradingAlert, ScanResult, NewsItem, BacktestScenario,
    PublicDisclosure, TradeJournalEntry,
)


@admin.register(DayTradePlan)
class DayTradePlanAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'strategy', 'direction', 'status', 'created_at')
    list_filter = ('status', 'strategy', 'direction')
    search_fields = ('symbol',)


@admin.register(PaperOrder)
class PaperOrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'symbol', 'side', 'order_type', 'quantity', 'status', 'created_at')
    list_filter = ('status', 'side', 'order_type')
    search_fields = ('symbol', 'order_id')


@admin.register(PaperPosition)
class PaperPositionAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'quantity', 'avg_entry_price', 'unrealized_pnl', 'is_open')
    list_filter = ('is_open',)
    search_fields = ('symbol',)


@admin.register(PaperFill)
class PaperFillAdmin(admin.ModelAdmin):
    list_display = ('order', 'fill_price', 'filled_qty', 'filled_at')


@admin.register(TradingAlert)
class TradingAlertAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'alert_type', 'condition', 'is_active', 'created_at')
    list_filter = ('alert_type', 'is_active')


@admin.register(ScanResult)
class ScanResultAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'scan_type', 'score', 'scanned_at')
    list_filter = ('scan_type',)


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ('headline', 'source', 'sentiment', 'published_at')
    list_filter = ('sentiment', 'source')


@admin.register(BacktestScenario)
class BacktestScenarioAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'strategy', 'total_return_pct', 'created_at')


@admin.register(PublicDisclosure)
class PublicDisclosureAdmin(admin.ModelAdmin):
    list_display = ('filer_name', 'symbol', 'transaction_type', 'transaction_date')
    list_filter = ('transaction_type',)


@admin.register(TradeJournalEntry)
class TradeJournalEntryAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'trade_date', 'direction', 'pnl_amount')
    list_filter = ('direction',)

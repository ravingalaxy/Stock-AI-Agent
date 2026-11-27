"""Day Trading URL configuration."""

from django.urls import path
from . import views

app_name = 'daytrading'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # API: Dashboard
    path('api/dashboard/', views.api_dashboard_data, name='api_dashboard'),

    # API: Market Status
    path('api/market-status/', views.api_market_status, name='api_market_status'),

    # API: Scanner (Skill 1)
    path('api/scan/', views.api_scan, name='api_scan'),

    # API: News (Skill 2)
    path('api/news/', views.api_news, name='api_news'),

    # API: Intraday Chart Data
    path('api/chart/', views.api_intraday_chart, name='api_intraday_chart'),

    # API: Entry Signals (Skill 3)
    path('api/entry-signal/', views.api_entry_signal, name='api_entry_signal'),

    # API: Exit Check (Skill 4)
    path('api/exit-check/<str:plan_id>/', views.api_exit_check, name='api_exit_check'),

    # API: Risk Check (Skill 5)
    path('api/risk-check/', views.api_risk_check, name='api_risk_check'),

    # API: Budget (Skill 6)
    path('api/budget/', views.api_budget, name='api_budget'),

    # API: Alerts (Skill 7)
    path('api/alerts/', views.api_alerts_list, name='api_alerts_list'),
    path('api/alerts/create/', views.api_create_alert, name='api_create_alert'),

    # API: Backtest / Time Machine (Skill 8)
    path('api/backtest/', views.api_backtest, name='api_backtest'),

    # API: Analyst (Skill 9)
    path('api/analyst/', views.api_analyst, name='api_analyst'),

    # API: Disclosures (Skill 10)
    path('api/disclosures/', views.api_disclosures, name='api_disclosures'),

    # API: Paper Broker (Skill 11)
    path('api/order/', views.api_submit_order, name='api_submit_order'),
    path('api/positions/', views.api_positions, name='api_positions'),
    path('api/orders/', views.api_order_history, name='api_order_history'),
    path('api/pnl/', views.api_pnl, name='api_pnl'),
    path('api/flatten/', views.api_flatten, name='api_flatten'),

    # API: Orchestrator
    path('api/scan-to-plan/', views.api_scan_to_plan, name='api_scan_to_plan'),
    path('api/execute-plan/<str:plan_id>/', views.api_execute_plan, name='api_execute_plan'),
    path('api/check-exits/', views.api_check_exits, name='api_check_exits'),

    # API: Account
    path('api/reset-account/', views.api_reset_account, name='api_reset_account'),

    # API: Trade Journal
    path('api/journal/', views.api_trade_journal, name='api_trade_journal'),

    # API: FreeLLMAPI AI Advisor
    path('api/ai-explain/', views.api_ai_explain, name='api_ai_explain'),
]

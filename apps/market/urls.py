from django.urls import path
from . import views

app_name = 'market'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('settings/', views.settings_view, name='settings'),
    path('api/search/', views.search_stocks, name='search_stocks'),
    path('api/market/pulse/', views.market_pulse_api, name='market_pulse_api'),
    path('api/market/sync/', views.sync_market_api, name='sync_market_api'),
    
    # CLI & Batch Analysis Runner
    path('cli-analysis/', views.cli_analysis_view, name='cli_analysis'),
    path('cli-analysis/api/run/', views.api_run_cli, name='api_run_cli'),
    path('cli-analysis/api/status/<str:job_id>/', views.api_cli_status, name='api_cli_status'),
    path('cli-analysis/api/stop/<str:job_id>/', views.api_cli_stop, name='api_cli_stop'),
    path('cli-analysis/report/<str:filename>/', views.cli_report_view, name='cli_report_view'),
]

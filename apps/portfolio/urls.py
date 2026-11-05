from django.urls import path
from . import views

app_name = 'portfolio'

urlpatterns = [
    path('', views.portfolio_dashboard, name='dashboard'),
    path('top-portfolios/', views.top_portfolios_view, name='top_portfolios'),
    path('top-portfolios/<str:portfolio_id>/', views.top_portfolios_view, name='top_portfolio_detail'),
    path('top-portfolios/<str:portfolio_id>/analyze/', views.load_top_portfolio_into_analysis, name='analyze_top_portfolio'),
    path('top-portfolios/<str:portfolio_id>/sync-prices/', views.sync_top_portfolio_prices_api, name='sync_top_portfolio_prices'),
    path('analysis/', views.portfolio_analysis_view, name='analysis'),
    path('analysis/reset/', views.portfolio_reset_view, name='reset'),
    path('analysis/preview/', views.portfolio_preview_api, name='preview_api'),
    path('analysis/export/<str:fmt>/', views.portfolio_export_report_view, name='export_report'),
    path('api/position-size/', views.calculate_position_size_api, name='position_size_api'),
    path('api/stop-loss/', views.calculate_stop_loss_api, name='stop_loss_api'),
    path('api/sync-prices/', views.sync_portfolio_prices_api, name='sync_portfolio_prices_api'),
]

from django.urls import path
from . import views

app_name = 'backtesting'

urlpatterns = [
    path('', views.backtest_view, name='backtest_dashboard'),
    path('api/run/', views.run_custom_backtest, name='run_custom_backtest'),
]

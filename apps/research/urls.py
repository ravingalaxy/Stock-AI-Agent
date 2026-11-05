from django.urls import path
from . import views

app_name = 'research'

urlpatterns = [
    path('', views.stock_research, {'symbol': 'RELIANCE.NS'}, name='research_default'),
    path('<str:symbol>/', views.stock_research, name='stock_detail'),
    path('<str:symbol>/api/dcf/', views.calculate_dcf_api, name='calculate_dcf_api'),
    path('<str:symbol>/api/sync/', views.sync_stock_quote_api, name='sync_stock_quote_api'),
]

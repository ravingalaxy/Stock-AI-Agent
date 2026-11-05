from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

router = DefaultRouter()
router.register(r'stocks', views.StockViewSet, basename='stock')

urlpatterns = [
    path('', include(router.urls)),
    path('stocks/<str:symbol>/prices/', views.StockPriceHistoryAPIView.as_view(), name='stock_prices'),
    path('rankings/', views.RankingsListAPIView.as_view(), name='rankings_list'),
    path('market/summary/', views.MarketSummaryAPIView.as_view(), name='market_summary'),
    path('ipos/', views.IPOListAPIView.as_view(), name='ipo_list'),
]

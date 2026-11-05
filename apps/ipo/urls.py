from django.urls import path
from . import views

app_name = 'ipo'

urlpatterns = [
    path('', views.ipo_dashboard, name='dashboard'),
    path('api/sync/', views.api_sync_ipo_data, name='api_sync'),
    path('api/list/', views.api_ipo_list, name='api_list'),
    path('api/<str:symbol>/', views.api_ipo_detail, name='api_detail'),
    path('<str:symbol>/', views.ipo_detail, name='detail'),
]

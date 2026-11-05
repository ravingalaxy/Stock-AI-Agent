from django.urls import path
from . import views

app_name = 'rankings'

urlpatterns = [
    path('', views.screener_and_rankings, name='screener'),
    path('export/csv/', views.export_rankings_csv, name='export_csv'),
    path('report/top20/', views.view_top20_report, name='view_top20_report'),
    path('report/top20/download/', views.download_top20_report_markdown, name='download_top20_report'),
]

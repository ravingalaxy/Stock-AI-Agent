"""
URL configuration for stock_agent_django project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/images/favicon.ico', permanent=True)),
    path('admin/', admin.site.urls),
    path('', include('apps.market.urls')),
    path('research/', include('apps.research.urls')),
    path('rankings/', include('apps.rankings.urls')),
    path('portfolio/', include('apps.portfolio.urls')),
    path('backtest/', include('apps.backtesting.urls')),
    path('backtesting/', RedirectView.as_view(url='/backtest/', permanent=True)),
    path('ipo/', include('apps.ipo.urls')),
    path('api/v1/', include('apps.api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

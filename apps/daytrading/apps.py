"""Day Trading app configuration."""

from django.apps import AppConfig


class DaytradingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.daytrading'
    verbose_name = 'Day Trading & Intraday Intelligence'

"""Pytest global configuration and fixtures.
Ensures Django settings and applications are loaded before any test collection.
"""
import os
import django

# Configure Django settings environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stock_agent_django.settings")

# Setup Django application registry
django.setup()

try:
    from django.test.utils import setup_test_environment
    setup_test_environment()
except RuntimeError:
    pass

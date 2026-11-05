"""
ASGI config for stock_agent_django project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_agent_django.settings')

application = get_asgi_application()

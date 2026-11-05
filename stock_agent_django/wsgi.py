"""
WSGI config for stock_agent_django project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_agent_django.settings')

application = get_wsgi_application()

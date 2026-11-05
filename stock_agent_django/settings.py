"""
Django settings for stock_agent_django project.
Production-ready configuration for AI Stock Market Research & Ranking Agent (NSE & BSE).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Ensure essential runtime data directories exist automatically on any new system
(BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "data" / "reports").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "data" / "logs").mkdir(parents=True, exist_ok=True)

# Load environment configuration
env_file = BASE_DIR / "config" / ".env"
if env_file.exists():
    load_dotenv(env_file, override=False)
else:
    load_dotenv(override=False)

# Security Settings
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY", 
    "django-insecure-ai-stock-agent-nse-bse-quant-key-2026-production-ready"
)

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0,*").split(",")

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    
    # Custom apps
    'apps.market',
    'apps.research',
    'apps.rankings',
    'apps.backtesting',
    'apps.portfolio',
    'apps.ipo',
    'apps.api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'stock_agent_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.market.context_processors.market_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'stock_agent_django.wsgi.application'
ASGI_APPLICATION = 'stock_agent_django.asgi.application'

# Database Configuration
# Using SQLite with WAL mode for concurrent read/write support
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'data' / 'stock_django.db',
        'OPTIONS': {
            'timeout': 30,
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization - Configured for Indian Standard Time (IST)
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'data' / 'reports'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# Compliance Disclaimer
DISCLAIMER = (
    "DISCLAIMER: This report and ranking system is an AI-assisted personal research "
    "and educational decision-support tool only. It does NOT constitute personalized "
    "investment advice, financial advisory services, or stock recommendations. "
    "Stock market investments are subject to market risks. Read all related documents "
    "carefully before investing. Past performance is not an indicator or guarantee of "
    "future returns. No assured or guaranteed returns are claimed or implied."
)

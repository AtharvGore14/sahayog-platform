# sahayog_marketplace/settings.py

import os
from pathlib import Path
from decouple import config
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/
SECRET_KEY = config('SECRET_KEY', default='django-insecure-a-very-secret-key-replace-this')
DEBUG = config('DEBUG', default=True, cast=bool)

# ALLOWED_HOSTS - handle comma-separated list and strip whitespace
_allowed_hosts = config('ALLOWED_HOSTS', default='*')
if _allowed_hosts == '*':
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(',') if host.strip()]

# Always add Render domain if not already present
if '*' not in ALLOWED_HOSTS:
    render_hosts = [
        'sahayog-platform.onrender.com',
        'sahayog-platform-1.onrender.com',
        '*.onrender.com'
    ]
    for host in render_hosts:
        if host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)

# Application definition
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 3rd Party Apps
    'rest_framework',
    'rest_framework.authtoken',
    'channels',
    'corsheaders',
    # Your Local Apps
    'marketplace',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# This line points to your main URL configuration. It is now correct.
ROOT_URLCONF = 'sahayog_marketplace.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# This line points to your real-time application handler. It is now correct.
ASGI_APPLICATION = 'sahayog_marketplace.asgi.application'

# Database
# Use PostgreSQL if DATABASE_URL is set (for production/Render), otherwise use SQLite (for local dev)
if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# --- Celery Configuration ---
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TIMEZONE = 'UTC'

# --- Celery Beat Periodic Task Schedule ---
CELERY_BEAT_SCHEDULE = {
    # 'scan-for-opportunities-every-2-hours': {
    #     'task': 'marketplace.tasks.scan_for_market_opportunities',
    #     'schedule': 60,
    # },
    'update-prices-daily': {
        'task': 'marketplace.tasks.update_commodity_prices',
        'schedule': 86400.0,
    },
    # 🧠 AI-POWERED TASKS
    'generate-market-analytics': {
        'task': 'marketplace.tasks.generate_market_analytics',
        'schedule': 3600.0,  # Every hour
    },
    'generate-ai-recommendations': {
        'task': 'marketplace.tasks.generate_ai_recommendations',
        'schedule': 1800.0,  # Every 30 minutes
    },
    'send-auction-alerts': {
        'task': 'marketplace.tasks.send_auction_ending_alerts',
        'schedule': 300.0,  # Every 5 minutes
    },
}

# --- Channels (WebSocket) Configuration ---
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
# Parse Redis URL for Channels
if REDIS_URL.startswith('redis://'):
    # Extract host and port from redis://host:port/db
    redis_parts = REDIS_URL.replace('redis://', '').split('/')
    host_port = redis_parts[0].split(':')
    redis_host = host_port[0] if len(host_port) > 0 else '127.0.0.1'
    redis_port = int(host_port[1]) if len(host_port) > 1 else 6379
    redis_db = int(redis_parts[1]) if len(redis_parts) > 1 else 0
else:
    redis_host = '127.0.0.1'
    redis_port = 6379
    redis_db = 0

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(redis_host, redis_port)],
        },
    },
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
FORCE_SCRIPT_NAME = config('FORCE_SCRIPT_NAME', default='/marketplace') or None
if FORCE_SCRIPT_NAME:
    STATIC_URL = f"{FORCE_SCRIPT_NAME}/static/"
else:
    STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# In sahayog_marketplace/settings.py

# ... (all your other settings above) ...

# --- DRF Settings ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}
CORS_ALLOWED_ORIGINS = [
    "null",
]
CORS_ALLOW_ALL_ORIGINS = True

# Media files
if FORCE_SCRIPT_NAME:
    MEDIA_URL = f"{FORCE_SCRIPT_NAME}/media/"
else:
    MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Proxy settings for Render deployment
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CSRF settings for Render deployment
CSRF_TRUSTED_ORIGINS = [
    'https://sahayog-platform.onrender.com',
    'https://sahayog-platform-1.onrender.com',
    'https://*.onrender.com',
]
# Add any additional trusted origins from environment
_csrf_env = config('CSRF_TRUSTED_ORIGINS', default='')
if _csrf_env:
    CSRF_TRUSTED_ORIGINS.extend([origin.strip() for origin in _csrf_env.split(',') if origin.strip()])

# Cookie settings for production (HTTPS)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
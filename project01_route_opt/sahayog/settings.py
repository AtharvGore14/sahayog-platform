"""
Django settings for Sahayog project.
"""

import os
from pathlib import Path
from decouple import config
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
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
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    
    # Third party apps
    'rest_framework',
    'corsheaders',
    
    # Local apps
    'route_optimizer',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Proxy settings for Render deployment
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookie settings for subdirectory mounting
SESSION_COOKIE_PATH = '/django/'
CSRF_COOKIE_PATH = '/django/'
SESSION_COOKIE_SECURE = True  # Use secure cookies in production (HTTPS)
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

ROOT_URLCONF = 'sahayog.urls'

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
                'route_optimizer.context_processors.unread_notifications_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'sahayog.wsgi.application'
ASGI_APPLICATION = 'sahayog.asgi.application'

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

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
FORCE_SCRIPT_NAME = config('FORCE_SCRIPT_NAME', default='/django') or None

if FORCE_SCRIPT_NAME:
    STATIC_URL = f"{FORCE_SCRIPT_NAME}/static/"
else:
    STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

# Media files
if FORCE_SCRIPT_NAME:
    MEDIA_URL = f"{FORCE_SCRIPT_NAME}/media/"
else:
    MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
# AUTH_USER_MODEL = 'users.User'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True
_cors_env = config('CORS_ALLOWED_ORIGINS', default='')
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_env.split(',') if o.strip().startswith(('http://', 'https://'))]

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

## Channels/Celery disabled for this focused app

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'sahayog.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

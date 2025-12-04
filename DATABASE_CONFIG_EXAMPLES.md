# Database Configuration Examples

Copy these configurations into your settings files to enable PostgreSQL on Render.

## 1. project01_route_opt/sahayog/settings.py

Replace the DATABASES section (around line 72-77) with:

```python
import dj_database_url
import os

# Database configuration
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
```

## 2. project03_market_place/sahayog_marketplace/settings.py

Replace the DATABASES section (around line 68-73) with the same code as above.

Also update Redis configuration (around line 76-113):

```python
import os
import redis

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Celery Configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TIMEZONE = 'UTC'

# Channels Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_URL],
        },
    },
}
```

## 3. project04/backend/database.py

Replace the entire file content with:

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL from environment or default to SQLite
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./waste_ledger.db')

# Convert Render PostgreSQL URL to SQLAlchemy format if needed
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

if DATABASE_URL.startswith('postgresql://'):
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

## 4. Update SECRET_KEY in project03_market_place

In `project03_market_place/sahayog_marketplace/settings.py`, replace the hardcoded SECRET_KEY (line 11) with:

```python
import os
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-a-very-secret-key-replace-this')
```

## 5. Update ALLOWED_HOSTS

Make sure ALLOWED_HOSTS uses environment variables:

```python
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')
```


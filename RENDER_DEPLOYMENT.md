# Render Deployment Guide for Sahayog Platform

This guide will help you deploy your multi-app Sahayog platform to Render.

## Prerequisites

1. A GitHub account
2. Your code pushed to a GitHub repository
3. A Render account (sign up at https://render.com)

## Step-by-Step Deployment

### Step 1: Prepare Your Repository

1. **Push your code to GitHub** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Ensure these files are in your root directory**:
   - `render.yaml` (or use manual setup)
   - `Procfile`
   - `build.sh`
   - `requirements.txt`
   - `master_server.py`

### Step 2: Update Database Configurations

You need to update your Django and FastAPI projects to use PostgreSQL instead of SQLite.

#### For project01_route_opt/sahayog/settings.py:

Add this at the top of the file (after imports):
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

#### For project03_market_place/sahayog_marketplace/settings.py:

Add the same database configuration as above.

#### For project04/backend/database.py:

Update to support PostgreSQL:
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

### Step 3: Update Redis Configuration

#### For project03_market_place/sahayog_marketplace/settings.py:

Update Celery and Channels configuration:
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

### Step 4: Update Requirements

Add `dj-database-url` and `psycopg2-binary` to your `requirements.txt` (if not already present):
```
dj-database-url==2.1.0
psycopg2-binary==2.9.7
```

### Step 5: Deploy on Render

#### Option A: Using render.yaml (Recommended)

1. Go to https://dashboard.render.com
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml` and create all services
5. Review and apply the blueprint

#### Option B: Manual Setup

1. **Create PostgreSQL Database**:
   - Go to Dashboard → "New +" → "PostgreSQL"
   - Name: `sahayog-db`
   - Plan: Starter (Free tier available)
   - Note the connection string

2. **Create Redis Instance**:
   - Go to Dashboard → "New +" → "Redis"
   - Name: `sahayog-redis`
   - Plan: Starter (Free tier available)
   - Note the connection string

3. **Create Web Service**:
   - Go to Dashboard → "New +" → "Web Service"
   - Connect your GitHub repository
   - Settings:
     - **Name**: `sahayog-platform`
     - **Environment**: `Python 3`
     - **Build Command**: `chmod +x build.sh && ./build.sh`
     - **Start Command**: `gunicorn master_server:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
     - **Plan**: Starter (Free tier available)

4. **Add Environment Variables**:
   ```
   PYTHON_VERSION=3.11.0
   PORT=10000
   DEBUG=False
   DJANGO_SETTINGS_MODULE=sahayog.settings
   FASTAPI_ROOT_PATH=/ledger
   DATABASE_URL=<from PostgreSQL service>
   REDIS_URL=<from Redis service>
   SECRET_KEY=<generate a secure random key>
   ALLOWED_HOSTS=*.onrender.com,your-app-name.onrender.com
   ```

5. **Create Celery Worker** (Optional):
   - Go to Dashboard → "New +" → "Background Worker"
   - Connect same repository
   - Build Command: `chmod +x build.sh && ./build.sh`
   - Start Command: `celery -A sahayog_marketplace.celery worker --loglevel=info`
   - Add same environment variables

6. **Create Celery Beat** (Optional):
   - Go to Dashboard → "New +" → "Background Worker"
   - Build Command: `chmod +x build.sh && ./build.sh`
   - Start Command: `celery -A sahayog_marketplace.celery beat --loglevel=info`
   - Add same environment variables

### Step 6: Post-Deployment Setup

1. **Create Superuser** (for Django admin):
   - Go to your Render service → "Shell"
   - Run:
     ```bash
     cd project01_route_opt
     python manage.py createsuperuser
     ```
   - Repeat for project03:
     ```bash
     cd project03_market_place
     python manage.py createsuperuser
     ```

2. **Verify Services**:
   - Check that all services are running
   - Visit your app URL: `https://your-app-name.onrender.com`
   - Test each sub-application:
     - `/django` - Route Optimizer
     - `/auditing` - Auditing App
     - `/marketplace` - Marketplace
     - `/ledger` - Waste Ledger

### Step 7: Important Notes

#### Static Files
- Static files are collected during build
- For production, consider using WhiteNoise or AWS S3
- Update `STATIC_ROOT` in Django settings if needed

#### Media Files
- SQLite files won't persist on Render (ephemeral filesystem)
- Use PostgreSQL for all databases
- For file uploads, use AWS S3 or Render's disk storage

#### Subprocess Management
- The marketplace subprocess should work, but monitor logs
- If issues occur, consider running marketplace as a separate service

#### Environment Variables
- Never commit secrets to Git
- Use Render's environment variable management
- Generate strong SECRET_KEY values

#### Scaling
- Free tier has limitations (spins down after inactivity)
- Upgrade to paid plan for 24/7 uptime
- Consider using Render's auto-sleep feature

### Troubleshooting

1. **Build Fails**:
   - Check build logs in Render dashboard
   - Ensure all dependencies are in `requirements.txt`
   - Verify Python version compatibility

2. **Database Connection Errors**:
   - Verify `DATABASE_URL` is set correctly
   - Check PostgreSQL service is running
   - Ensure `dj-database-url` is installed

3. **Redis Connection Errors**:
   - Verify `REDIS_URL` is set correctly
   - Check Redis service is running
   - Update connection string format if needed

4. **Static Files Not Loading**:
   - Run `collectstatic` manually in shell
   - Check `STATIC_ROOT` and `STATIC_URL` settings
   - Verify WhiteNoise is configured

5. **App Crashes**:
   - Check logs in Render dashboard
   - Verify all environment variables are set
   - Check database migrations ran successfully

### Cost Estimation

**Free Tier** (for testing):
- Web Service: Free (spins down after inactivity)
- PostgreSQL: Free (90 days, then $7/month)
- Redis: Free (limited)
- Workers: Free (spins down)

**Paid Tier** (for production):
- Web Service: $7/month (always on)
- PostgreSQL: $7/month
- Redis: $10/month
- Workers: $7/month each

### Security Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Use HTTPS (automatic on Render)
- [ ] Secure database credentials
- [ ] Enable CORS only for needed domains
- [ ] Review and update security settings

### Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- Django Deployment: https://docs.djangoproject.com/en/stable/howto/deployment/

---

**Good luck with your deployment! 🚀**


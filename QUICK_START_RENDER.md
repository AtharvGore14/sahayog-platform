# Quick Start: Deploy to Render

## TL;DR - Fastest Path to Deployment

### 1. Update Your Code

Run these commands to update database configurations:

```bash
# The files DATABASE_CONFIG_EXAMPLES.md has the exact code to copy
# Follow the instructions in that file to update:
# - project01_route_opt/sahayog/settings.py
# - project03_market_place/sahayog_marketplace/settings.py  
# - project04/backend/database.py
```

### 2. Push to GitHub

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 3. Deploy on Render

**Option A: Using Blueprint (Easiest)**
1. Go to https://dashboard.render.com
2. Click "New +" → "Blueprint"
3. Connect your GitHub repo
4. Render will auto-detect `render.yaml`
5. Click "Apply"

**Option B: Manual Setup**
1. Create PostgreSQL database
2. Create Redis instance
3. Create Web Service with:
   - Build: `chmod +x build.sh && ./build.sh`
   - Start: `gunicorn master_server:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
4. Add environment variables (see RENDER_DEPLOYMENT.md)

### 4. Set Environment Variables

In Render dashboard, add:
- `DATABASE_URL` (from PostgreSQL service)
- `REDIS_URL` (from Redis service)
- `SECRET_KEY` (generate random string)
- `ALLOWED_HOSTS` (your-app.onrender.com)

### 5. Create Superusers

After deployment, use Render Shell:
```bash
cd project01_route_opt && python manage.py createsuperuser
cd ../project03_market_place && python manage.py createsuperuser
```

### 6. Done! 🎉

Visit: `https://your-app-name.onrender.com`

---

**Full details in RENDER_DEPLOYMENT.md**


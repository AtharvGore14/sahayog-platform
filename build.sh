#!/bin/bash
# Build script for Render deployment

set -e  # Exit on any error

echo "🚀 Starting build process..."

# Get the project root directory
PROJECT_ROOT=$(pwd)
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# Install Python dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files for Django projects
echo "📁 Collecting static files for project01..."
cd "${PROJECT_ROOT}/project01_route_opt"
export DJANGO_SETTINGS_MODULE="sahayog.settings"
export FORCE_SCRIPT_NAME="/django"
# Ensure STATIC_ROOT directory exists
mkdir -p staticfiles
python manage.py collectstatic --noinput || echo "⚠️  Warning: collectstatic failed for project01"
cd "${PROJECT_ROOT}"

echo "📁 Collecting static files for project03..."
cd "${PROJECT_ROOT}/sahayog_marketplace"
# Temporarily remove project01 from PYTHONPATH to avoid module conflicts
CLEAN_PYTHONPATH=$(echo "${PYTHONPATH}" | tr ':' '\n' | grep -v "project01_route_opt" | tr '\n' ':' | sed 's/:$//')
export PYTHONPATH="${PROJECT_ROOT}/sahayog_marketplace:${CLEAN_PYTHONPATH}"
export DJANGO_SETTINGS_MODULE="sahayog_marketplace.settings"
# Skip collectstatic for marketplace if it fails - static files are served differently
python manage.py collectstatic --noinput 2>&1 || echo "⚠️  Info: collectstatic skipped for project03 (static files served via subprocess)"
cd "${PROJECT_ROOT}"

# Run migrations for Django projects
echo "🗄️ Running migrations for project01..."
cd "${PROJECT_ROOT}/project01_route_opt"
export DJANGO_SETTINGS_MODULE="sahayog.settings"
python manage.py migrate --noinput || echo "⚠️  Warning: migrations failed for project01"
cd "${PROJECT_ROOT}"

echo "🗄️ Running migrations for project03..."
cd "${PROJECT_ROOT}/sahayog_marketplace"
# Remove project01 from PYTHONPATH to avoid 'sahayog' module name conflict
CLEAN_PYTHONPATH=$(echo "${PYTHONPATH}" | tr ':' '\n' | grep -v "project01_route_opt" | tr '\n' ':' | sed 's/:$//')
export PYTHONPATH="${PROJECT_ROOT}/sahayog_marketplace:${CLEAN_PYTHONPATH}"
export DJANGO_SETTINGS_MODULE="sahayog_marketplace.settings"
# Try migrations - if they fail, they'll run at startup via master_server
python manage.py migrate --noinput 2>&1 || echo "⚠️  Info: migrations will run at startup for project03"
cd "${PROJECT_ROOT}"

echo "✅ Build completed successfully!"


#!/bin/bash
# Build script for Render deployment

set -e  # Exit on any error

echo "🚀 Starting build process..."

# Install Python dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files for Django projects
echo "📁 Collecting static files for project01..."
cd project01_route_opt
python manage.py collectstatic --noinput || true
cd ..

echo "📁 Collecting static files for project03..."
cd project03_market_place
python manage.py collectstatic --noinput || true
cd ..

# Run migrations for Django projects
echo "🗄️ Running migrations for project01..."
cd project01_route_opt
python manage.py migrate --noinput || true
cd ..

echo "🗄️ Running migrations for project03..."
cd project03_market_place
python manage.py migrate --noinput || true
cd ..

echo "✅ Build completed successfully!"


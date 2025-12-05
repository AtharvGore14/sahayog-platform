web: gunicorn master_server:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
worker: celery -A sahayog_marketplace.celery worker --loglevel=info
beat: celery -A sahayog_marketplace.celery beat --loglevel=info


"""WSGI entrypoint for the marketplace Django project."""

import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sahayog_marketplace.settings')

application = get_wsgi_application()



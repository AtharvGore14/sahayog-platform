"""
ASGI config for Sahayog project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sahayog.settings')

# Import the routing after Django is configured
application = get_asgi_application()

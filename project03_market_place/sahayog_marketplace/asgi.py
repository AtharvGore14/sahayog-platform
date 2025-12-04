import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

# Set the Django settings module environment variable.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sahayog_marketplace.settings')

# This is the crucial line that initializes the Django app registry.
django.setup()

# We must import the routing *after* django.setup() has been called.
import marketplace.routing

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests.
    "http": get_asgi_application(),

    # WebSocket chat handler
    "websocket": AuthMiddlewareStack(
        URLRouter(
            marketplace.routing.websocket_urlpatterns
        )
    ),
})
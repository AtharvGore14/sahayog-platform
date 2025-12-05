from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.utils.timezone import now
from rest_framework.authtoken import views
from django.conf import settings
from django.conf.urls.static import static


def health_check(_request):
    """Lightweight health endpoint used by the master orchestrator."""
    return JsonResponse(
        {
            "status": "healthy",
            "service": "marketplace",
            "timestamp": now().isoformat(),
        }
    )

urlpatterns = [
    path('api/health', health_check, name='marketplace-health'),
    path('admin/', admin.site.urls),
    path('api/marketplace/', include('marketplace.urls')),
    path('api-token-auth/', views.obtain_auth_token)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
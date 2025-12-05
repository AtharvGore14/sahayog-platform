from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken import views
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
import os

def serve_frontend(request):
    """Serve the main frontend HTML file"""
    frontend_path = os.path.join(settings.BASE_DIR, 'ai_enhanced_frontend.html')
    try:
        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html; charset=utf-8')
    except FileNotFoundError:
        return HttpResponse('Frontend file not found. Please open ai_enhanced_frontend.html directly.', status=404)

urlpatterns = [
    path('', serve_frontend, name='frontend'),
    path('admin/', admin.site.urls),
    path('api/health', lambda r: HttpResponse('{"status":"ok"}', content_type='application/json'), name='health'),
    path('api/marketplace/', include('marketplace.urls')),
    path('api-token-auth/', views.obtain_auth_token)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
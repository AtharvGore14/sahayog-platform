"""
URL configuration for the route optimizer app.
"""
from django.urls import path
from . import views

app_name = 'route_optimizer'

urlpatterns = [
    # Main views
    path('logout/', views.logout_view, name='logout'),
    path('', views.index, name='index'),
    path('locations/', views.locations, name='locations'),
    path('vehicles/', views.vehicles, name='vehicles'),
    path('optimize/', views.optimize_route, name='optimize_route'),
    path('routes/', views.routes_list, name='routes_list'),
    path('routes/import/', views.import_route_json, name='import_route_json'),
    path('route/<int:route_id>/', views.route_details, name='route_details'),
    path('history/', views.optimization_history, name='optimization_history'),
    path('performance/', views.performance_dashboard, name='performance_dashboard'),
    path('tracking/', views.real_time_tracking, name='real_time_tracking'),
    path('notifications/', views.notifications, name='notifications'),
    path('api/notifications/<int:notification_id>/read/', views.api_notification_mark_read, name='api_notification_mark_read'),
    path('api/notifications/read-all/', views.api_notification_mark_all_read, name='api_notification_mark_all_read'),
    path('api/notifications/<int:notification_id>/unread/', views.api_notification_mark_unread, name='api_notification_mark_unread'),
    path('api/notifications/clear-all/', views.api_notification_clear_all, name='api_notification_clear_all'),
    
    # Management views
    path('add-location/', views.add_location, name='add_location'),
    path('import-locations/', views.import_locations, name='import_locations'),
    path('add-vehicle/', views.add_vehicle, name='add_vehicle'),
    
    # API endpoints
    path('api/locations/', views.api_locations, name='api_locations'),
    path('api/vehicles/', views.api_vehicles, name='api_vehicles'),
    path('api/route/<int:route_id>/stats/', views.api_route_statistics, name='api_route_statistics'),
    path('api/route/<int:route_id>/tracking/start/', views.api_route_tracking_start, name='api_route_tracking_start'),
    path('api/route/<int:route_id>/tracking/stop/', views.api_route_tracking_stop, name='api_route_tracking_stop'),
    path('api/route/<int:route_id>/tracking/status/', views.api_route_tracking_status, name='api_route_tracking_status'),
    path('api/history/', views.api_optimization_history, name='api_optimization_history'),
    path('api/recommend/', views.api_recommend_route, name='api_recommend_route'),
    path('api/route/<int:route_id>/delete/', views.api_delete_route, name='api_delete_route'),
]

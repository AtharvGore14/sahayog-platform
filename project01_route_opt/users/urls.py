"""
URL configuration for the users app.
"""
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/login/', views.UserLoginView.as_view(), name='login'),
    path('auth/logout/', views.UserLogoutView.as_view(), name='logout'),
    path('auth/password-change/', views.PasswordChangeView.as_view(), name='password-change'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/company/', views.CompanyProfileView.as_view(), name='company-profile'),
    path('profile/driver/', views.DriverProfileView.as_view(), name='driver-profile'),
    path('profile/admin/', views.MunicipalAdminProfileView.as_view(), name='admin-profile'),
    path('devices/', views.UserDeviceView.as_view(), name='device-register'),
    path('stats/', views.user_stats, name='user-stats'),
]

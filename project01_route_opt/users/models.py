"""
User models for Sahayog project.
"""
from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.core.validators import RegexValidator
from django.utils import timezone


class User(AbstractUser):
    """
    Custom user model with extended fields for different user types.
    """
    USER_TYPE_CHOICES = [
        ('citizen', 'Citizen'),
        ('company', 'Company'),
        ('driver', 'Collection Driver'),
        ('corporate', 'Corporate User'),
        ('admin', 'Municipal Admin'),
    ]
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='citizen')
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')],
        blank=True,
        null=True
    )
    address = models.TextField(blank=True)
    location = models.PointField(blank=True, null=True, srid=4326)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class CompanyProfile(models.Model):
    """
    Extended profile for company users.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_profile')
    company_name = models.CharField(max_length=200)
    business_type = models.CharField(max_length=100)
    registration_number = models.CharField(max_length=100, unique=True)
    tax_id = models.CharField(max_length=100, blank=True)
    employee_count = models.PositiveIntegerField(default=1)
    annual_waste_volume = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sustainability_goals = models.TextField(blank=True)
    
    class Meta:
        db_table = 'company_profiles'
    
    def __str__(self):
        return self.company_name


class DriverProfile(models.Model):
    """
    Extended profile for collection drivers.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    vehicle_number = models.CharField(max_length=20)
    vehicle_type = models.CharField(max_length=50)
    license_number = models.CharField(max_length=50)
    experience_years = models.PositiveIntegerField(default=0)
    assigned_zone = models.CharField(max_length=100, blank=True)
    is_available = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'driver_profiles'
    
    def __str__(self):
        return f"{self.user.username} - {self.employee_id}"


class MunicipalAdminProfile(models.Model):
    """
    Extended profile for municipal administrators.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    jurisdiction_area = models.CharField(max_length=200)
    emergency_contact = models.CharField(max_length=15)
    permissions_level = models.CharField(max_length=50, default='standard')
    
    class Meta:
        db_table = 'municipal_admin_profiles'
    
    def __str__(self):
        return f"{self.user.username} - {self.department}"


class UserDevice(models.Model):
    """
    Track user devices for push notifications.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_token = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(max_length=20, choices=[
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ])
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_devices'
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type}"

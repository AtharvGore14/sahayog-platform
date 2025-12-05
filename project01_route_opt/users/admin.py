"""
Admin configuration for the users app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, CompanyProfile, DriverProfile, MunicipalAdminProfile, UserDevice


class CompanyProfileInline(admin.StackedInline):
    model = CompanyProfile
    can_delete = False
    verbose_name_plural = 'Company Profile'


class DriverProfileInline(admin.StackedInline):
    model = DriverProfile
    can_delete = False
    verbose_name_plural = 'Driver Profile'


class MunicipalAdminProfileInline(admin.StackedInline):
    model = MunicipalAdminProfile
    can_delete = False
    verbose_name_plural = 'Municipal Admin Profile'


class UserAdmin(BaseUserAdmin):
    inlines = (CompanyProfileInline, DriverProfileInline, MunicipalAdminProfileInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_verified', 'is_staff')
    list_filter = ('user_type', 'is_verified', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Sahayog Profile', {
            'fields': ('user_type', 'phone_number', 'address', 'location', 'profile_picture', 'is_verified')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Sahayog Profile', {
            'fields': ('user_type', 'phone_number', 'address', 'location', 'profile_picture', 'is_verified')
        }),
    )


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'business_type', 'registration_number', 'employee_count')
    list_filter = ('business_type', 'employee_count')
    search_fields = ('company_name', 'registration_number', 'tax_id')
    ordering = ('company_name',)


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'vehicle_number', 'vehicle_type', 'assigned_zone', 'is_available')
    list_filter = ('vehicle_type', 'assigned_zone', 'is_available')
    search_fields = ('employee_id', 'vehicle_number', 'license_number')
    ordering = ('employee_id',)


@admin.register(MunicipalAdminProfile)
class MunicipalAdminProfileAdmin(admin.ModelAdmin):
    list_display = ('department', 'designation', 'jurisdiction_area', 'permissions_level')
    list_filter = ('department', 'permissions_level')
    search_fields = ('department', 'designation', 'jurisdiction_area')
    ordering = ('department',)


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'is_active', 'last_used')
    list_filter = ('device_type', 'is_active')
    search_fields = ('user__username', 'device_token')
    ordering = ('-last_used',)


# Register the custom User model
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

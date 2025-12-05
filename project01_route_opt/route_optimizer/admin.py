"""
Admin configuration for the route optimizer app.
"""
from django.contrib import admin
from .models import Location, Vehicle, OptimizedRoute, RouteLocation, RouteOptimizationSession


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'location_type', 'priority', 'address', 'is_active', 'created_at')
    list_filter = ('location_type', 'priority', 'is_active', 'created_at')
    search_fields = ('name', 'address')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'address', 'location_type', 'priority')
        }),
        ('Location Details', {
            'fields': ('location', 'estimated_waste_volume', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('name', 'vehicle_type', 'capacity', 'fuel_efficiency', 'is_available', 'created_at')
    list_filter = ('vehicle_type', 'is_available', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'vehicle_type', 'capacity', 'fuel_efficiency')
        }),
        ('Location & Status', {
            'fields': ('current_location', 'is_available')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class RouteLocationInline(admin.TabularInline):
    model = RouteLocation
    extra = 0
    readonly_fields = ('visit_order', 'estimated_arrival_time', 'estimated_departure_time')
    ordering = ('visit_order',)


@admin.register(OptimizedRoute)
class OptimizedRouteAdmin(admin.ModelAdmin):
    list_display = ('route_name', 'vehicle', 'total_distance', 'total_duration', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'vehicle__vehicle_type')
    search_fields = ('route_name', 'vehicle__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [RouteLocationInline]
    
    fieldsets = (
        ('Route Information', {
            'fields': ('route_name', 'vehicle', 'status')
        }),
        ('Optimization Results', {
            'fields': ('total_distance', 'total_duration', 'estimated_fuel_consumption', 'total_waste_volume')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RouteLocation)
class RouteLocationAdmin(admin.ModelAdmin):
    list_display = ('route', 'location', 'visit_order', 'estimated_waste_collected')
    list_filter = ('route__status', 'visit_order')
    search_fields = ('route__route_name', 'location__name')
    ordering = ('route', 'visit_order')
    readonly_fields = ('route', 'location', 'visit_order')


@admin.register(RouteOptimizationSession)
class RouteOptimizationSessionAdmin(admin.ModelAdmin):
    list_display = ('session_name', 'algorithm_used', 'execution_time', 'optimization_score', 'created_at')
    list_filter = ('algorithm_used', 'created_at')
    search_fields = ('session_name',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Session Information', {
            'fields': ('session_name', 'algorithm_used', 'parameters')
        }),
        ('Performance Metrics', {
            'fields': ('execution_time', 'optimization_score')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

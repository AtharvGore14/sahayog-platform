"""
Models for the route optimization system.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Location(models.Model):
    """
    Model representing locations (bins, collection points, etc.)
    """
    name = models.CharField(max_length=200)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    location_type = models.CharField(max_length=50, choices=[
        ('bin', 'Waste Bin'),
        ('collection_point', 'Collection Point'),
        ('depot', 'Depot'),
        ('landfill', 'Landfill'),
    ])
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium')
    estimated_waste_volume = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0,
        help_text="Estimated waste volume in liters"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'locations'
        indexes = [
            models.Index(fields=['location_type', 'is_active']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_location_type_display()})"


class Vehicle(models.Model):
    """
    Model representing collection vehicles.
    """
    name = models.CharField(max_length=200)
    vehicle_type = models.CharField(max_length=50, choices=[
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('tractor', 'Tractor'),
        ('compactor', 'Compactor'),
    ])
    capacity = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        help_text="Capacity in liters"
    )
    fuel_efficiency = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Fuel efficiency in km/l"
    )
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vehicles'
        indexes = [
            models.Index(fields=['vehicle_type', 'is_available']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_vehicle_type_display()})"


class OptimizedRoute(models.Model):
    """
    Model representing optimized collection routes.
    """
    route_name = models.CharField(max_length=200)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='routes')
    locations = models.ManyToManyField(Location, through='RouteLocation')
    total_distance = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        help_text="Total distance in kilometers"
    )
    total_duration = models.IntegerField(
        help_text="Total duration in minutes"
    )
    estimated_fuel_consumption = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        help_text="Estimated fuel consumption in liters"
    )
    total_waste_volume = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        help_text="Total waste volume in liters"
    )
    status = models.CharField(max_length=20, choices=[
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='planned')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'optimized_routes'
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.route_name} - {self.vehicle.name}"


class RouteLocation(models.Model):
    """
    Intermediate model for route-location relationships with visit order.
    """
    route = models.ForeignKey(OptimizedRoute, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    visit_order = models.PositiveIntegerField()
    estimated_arrival_time = models.TimeField()
    estimated_departure_time = models.TimeField()
    estimated_waste_collected = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        default=0
    )
    
    class Meta:
        db_table = 'route_locations'
        unique_together = ('route', 'location')
        ordering = ['visit_order']
    
    def __str__(self):
        return f"{self.route.route_name} - {self.location.name} (Order: {self.visit_order})"


class RouteOptimizationSession(models.Model):
    """
    Model to track route optimization sessions and parameters.
    """
    session_name = models.CharField(max_length=200)
    algorithm_used = models.CharField(max_length=100)
    parameters = models.JSONField(default=dict)  # Store optimization parameters
    execution_time = models.DecimalField(
        max_digits=8, 
        decimal_places=3,
        help_text="Execution time in seconds"
    )
    optimization_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Optimization quality score (0-100)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'route_optimization_sessions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.session_name} - {self.algorithm_used}"


class Notification(models.Model):
    """System notifications shown in the Notifications page."""
    NOTIFICATION_TYPES = [
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('danger', 'Alert'),
        ('info', 'Information'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.notification_type})"
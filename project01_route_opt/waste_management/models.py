"""
Waste management models for Sahayog project.
"""
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from users.models import User


class WasteBin(models.Model):
    """
    Model representing waste bins in the city.
    """
    BIN_TYPE_CHOICES = [
        ('general', 'General Waste'),
        ('recyclable', 'Recyclable'),
        ('organic', 'Organic'),
        ('hazardous', 'Hazardous'),
        ('e-waste', 'E-Waste'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
        ('decommissioned', 'Decommissioned'),
    ]
    
    bin_id = models.CharField(max_length=50, unique=True)
    bin_type = models.CharField(max_length=20, choices=BIN_TYPE_CHOICES)
    location = models.PointField(srid=4326)
    address = models.TextField()
    zone = models.CharField(max_length=100)
    capacity = models.DecimalField(max_digits=8, decimal_places=2)  # in liters
    current_fill_level = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    last_collection = models.DateTimeField(blank=True, null=True)
    next_collection = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'waste_bins'
        indexes = [
            models.Index(fields=['bin_type', 'status']),
            models.Index(fields=['zone', 'status']),
            models.Index(fields=['current_fill_level']),
        ]
    
    def __str__(self):
        return f"{self.bin_id} - {self.get_bin_type_display()} ({self.zone})"


class WasteReport(models.Model):
    """
    Model representing waste reports submitted by users.
    """
    REPORT_TYPE_CHOICES = [
        ('fill_level', 'Bin Fill Level'),
        ('overflow', 'Bin Overflow'),
        ('damage', 'Bin Damage'),
        ('illegal_dumping', 'Illegal Dumping'),
        ('segregation_audit', 'Segregation Audit'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='waste_reports')
    bin = models.ForeignKey(WasteBin, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    description = models.TextField()
    location = models.PointField(srid=4326)
    photo = models.ImageField(upload_to='waste_reports/', blank=True, null=True)
    fill_level = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium')
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'waste_reports'
        indexes = [
            models.Index(fields=['report_type', 'status']),
            models.Index(fields=['priority', 'status']),
            models.Index(fields=['reported_at']),
        ]
    
    def __str__(self):
        return f"{self.report_type} - {self.bin.bin_id} ({self.status})"


class SegregationAudit(models.Model):
    """
    Model representing waste segregation audits.
    """
    AUDIT_RESULT_CHOICES = [
        ('approved', 'Approved'),
        ('contaminated', 'Contaminated'),
        ('rejected', 'Rejected'),
    ]
    
    waste_report = models.OneToOneField(WasteReport, on_delete=models.CASCADE, related_name='segregation_audit')
    audit_result = models.CharField(max_length=20, choices=AUDIT_RESULT_CHOICES)
    contamination_details = models.TextField(blank=True)
    ai_confidence_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    detected_materials = models.JSONField(default=dict)  # Store AI-detected materials
    audit_notes = models.TextField(blank=True)
    audited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audits_conducted')
    audited_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'segregation_audits'
    
    def __str__(self):
        return f"Audit {self.id} - {self.audit_result}"


class CollectionRoute(models.Model):
    """
    Model representing optimized collection routes.
    """
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    route_id = models.CharField(max_length=50, unique=True)
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_routes')
    bins = models.ManyToManyField(WasteBin, through='RouteBin')
    estimated_distance = models.DecimalField(max_digits=8, decimal_places=2)  # in kilometers
    estimated_duration = models.IntegerField()  # in minutes
    fuel_consumption = models.DecimalField(max_digits=6, decimal_places=2)  # in liters
    total_waste_volume = models.DecimalField(max_digits=8, decimal_places=2)  # in liters
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    planned_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'collection_routes'
        indexes = [
            models.Index(fields=['status', 'planned_date']),
            models.Index(fields=['driver', 'status']),
        ]
    
    def __str__(self):
        return f"Route {self.route_id} - {self.driver.username} ({self.status})"


class RouteBin(models.Model):
    """
    Intermediate model for route-bin relationships with order.
    """
    route = models.ForeignKey(CollectionRoute, on_delete=models.CASCADE)
    bin = models.ForeignKey(WasteBin, on_delete=models.CASCADE)
    visit_order = models.PositiveIntegerField()
    estimated_arrival_time = models.TimeField()
    actual_arrival_time = models.TimeField(blank=True, null=True)
    collection_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('collected', 'Collected'),
        ('skipped', 'Skipped'),
        ('failed', 'Failed'),
    ], default='pending')
    
    class Meta:
        db_table = 'route_bins'
        unique_together = ('route', 'bin')
        ordering = ['visit_order']
    
    def __str__(self):
        return f"{self.route.route_id} - {self.bin.bin_id} (Order: {self.visit_order})"


class CollectionVehicle(models.Model):
    """
    Model representing collection vehicles.
    """
    VEHICLE_TYPE_CHOICES = [
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('tractor', 'Tractor'),
        ('compactor', 'Compactor'),
    ]
    
    vehicle_id = models.CharField(max_length=50, unique=True)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES)
    license_plate = models.CharField(max_length=20, unique=True)
    capacity = models.DecimalField(max_digits=8, decimal_places=2)  # in liters
    fuel_type = models.CharField(max_length=20)
    fuel_efficiency = models.DecimalField(max_digits=5, decimal_places=2)  # km/l
    current_location = models.PointField(srid=4326, blank=True, null=True)
    is_available = models.BooleanField(default=True)
    last_maintenance = models.DateField(blank=True, null=True)
    next_maintenance = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'collection_vehicles'
        indexes = [
            models.Index(fields=['vehicle_type', 'is_available']),
            models.Index(fields=['license_plate']),
        ]
    
    def __str__(self):
        return f"{self.vehicle_id} - {self.license_plate} ({self.get_vehicle_type_display()})"

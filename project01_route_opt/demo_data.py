#!/usr/bin/env python3
"""
Demo data script for Sahayog Route Optimizer
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sahayog.settings')
django.setup()

from route_optimizer.models import Location, Vehicle

def create_demo_locations():
    """Create demo locations for testing."""
    print("📍 Creating demo locations...")
    
    locations_data = [
        {
            'name': 'Central Market Bin',
            'address': '123 Main Street, Downtown',
            'latitude': 20.5937,
            'longitude': 78.9629,
            'location_type': 'bin',
            'priority': 'high',
            'estimated_waste_volume': 150.0
        },
        {
            'name': 'Shopping Mall Collection Point',
            'address': '456 Mall Road, Shopping District',
            'latitude': 20.6037,
            'longitude': 78.9729,
            'location_type': 'collection_point',
            'priority': 'medium',
            'estimated_waste_volume': 200.0
        },
        {
            'name': 'Residential Area Bin',
            'address': '789 Residential Lane, Suburbs',
            'latitude': 20.5837,
            'longitude': 78.9529,
            'location_type': 'bin',
            'priority': 'low',
            'estimated_waste_volume': 75.0
        },
        {
            'name': 'Industrial Zone Bin',
            'address': '321 Industrial Park, Factory Area',
            'latitude': 20.6137,
            'longitude': 78.9829,
            'location_type': 'bin',
            'priority': 'urgent',
            'estimated_waste_volume': 300.0
        },
        {
            'name': 'University Campus Bin',
            'address': '654 University Road, Campus Area',
            'latitude': 20.5737,
            'longitude': 78.9429,
            'location_type': 'bin',
            'priority': 'medium',
            'estimated_waste_volume': 120.0
        },
        {
            'name': 'Hospital Collection Point',
            'address': '987 Medical Center, Healthcare District',
            'latitude': 20.6237,
            'longitude': 78.9929,
            'location_type': 'collection_point',
            'priority': 'urgent',
            'estimated_waste_volume': 250.0
        },
        {
            'name': 'Park Area Bin',
            'address': '147 Park Street, Recreation Area',
            'latitude': 20.5637,
            'longitude': 78.9329,
            'location_type': 'bin',
            'priority': 'low',
            'estimated_waste_volume': 50.0
        },
        {
            'name': 'Business District Bin',
            'address': '258 Business Avenue, Corporate Area',
            'latitude': 20.6337,
            'longitude': 79.0029,
            'location_type': 'bin',
            'priority': 'high',
            'estimated_waste_volume': 180.0
        },
        {
            'name': 'Airport Collection Point',
            'address': '369 Airport Road, Transportation Hub',
            'latitude': 20.5537,
            'longitude': 78.9229,
            'location_type': 'collection_point',
            'priority': 'high',
            'estimated_waste_volume': 400.0
        },
        {
            'name': 'Stadium Bin',
            'address': '741 Stadium Boulevard, Sports Complex',
            'latitude': 20.6437,
            'longitude': 79.0129,
            'location_type': 'bin',
            'priority': 'medium',
            'estimated_waste_volume': 220.0
        }
    ]
    
    created_count = 0
    for data in locations_data:
        location, created = Location.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        if created:
            created_count += 1
            print(f"  ✅ Created: {data['name']}")
        else:
            print(f"  ⚠️  Exists: {data['name']}")
    
    print(f"📍 Created {created_count} new locations")
    return created_count

def create_demo_vehicles():
    """Create demo vehicles for testing."""
    print("\n🚛 Creating demo vehicles...")
    
    vehicles_data = [
        {
            'name': 'Waste Collection Truck Alpha',
            'vehicle_type': 'truck',
            'capacity': 5000.0,
            'fuel_efficiency': 8.5,
            'current_latitude': 20.5937,
            'current_longitude': 78.9629
        },
        {
            'name': 'Compact Collection Van Beta',
            'vehicle_type': 'van',
            'capacity': 2000.0,
            'fuel_efficiency': 12.0,
            'current_latitude': 20.6037,
            'current_longitude': 78.9729
        },
        {
            'name': 'Heavy Duty Compactor Gamma',
            'vehicle_type': 'compactor',
            'capacity': 8000.0,
            'fuel_efficiency': 6.5,
            'current_latitude': 20.5837,
            'current_longitude': 78.9529
        },
        {
            'name': 'Agricultural Tractor Delta',
            'vehicle_type': 'tractor',
            'capacity': 3000.0,
            'fuel_efficiency': 15.0,
            'current_latitude': 20.6137,
            'current_longitude': 78.9829
        }
    ]
    
    created_count = 0
    for data in vehicles_data:
        vehicle, created = Vehicle.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        if created:
            created_count += 1
            print(f"  ✅ Created: {data['name']}")
        else:
            print(f"  ⚠️  Exists: {data['name']}")
    
    print(f"🚛 Created {created_count} new vehicles")
    return created_count

def main():
    """Main function to create demo data."""
    print("🎯 Sahayog Route Optimizer - Demo Data Creator")
    print("=" * 50)
    
    # Create demo locations
    locations_created = create_demo_locations()
    
    # Create demo vehicles
    vehicles_created = create_demo_vehicles()
    
    print("\n" + "=" * 50)
    print("🎉 Demo data creation completed!")
    print(f"📍 Locations: {locations_created} new")
    print(f"🚛 Vehicles: {vehicles_created} new")
    print("\nYou can now:")
    print("1. Start the server: python start.py")
    print("2. Access the app: http://localhost:8000/route-optimizer/")
    print("3. Test route optimization with the demo data")
    print("4. Login to admin: http://localhost:8000/admin/")

if __name__ == "__main__":
    main()

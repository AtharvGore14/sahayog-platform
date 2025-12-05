"""
Script to update vehicle capacities and add fuel tank capacities.
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sahayog.settings')
django.setup()

from route_optimizer.models import Vehicle

# Vehicle updates: increased capacities and fuel tank capacities
VEHICLE_UPDATES = {
    'Waste Collection Truck Alpha': {
        'capacity': 15000.0,  # Increased from 5000
        'fuel_tank_capacity': 150.0,  # Typical truck fuel tank
        'fuel_efficiency': 8.5
    },
    'Compact Collection Van Beta': {
        'capacity': 6000.0,  # Increased from 2000
        'fuel_tank_capacity': 60.0,  # Van fuel tank
        'fuel_efficiency': 12.0
    },
    'Heavy Duty Compactor Gamma': {
        'capacity': 25000.0,  # Increased from 8000
        'fuel_tank_capacity': 200.0,  # Large truck fuel tank
        'fuel_efficiency': 6.5
    },
    'Agricultural Tractor Delta': {
        'capacity': 8000.0,  # Increased from 3000
        'fuel_tank_capacity': 80.0,  # Tractor fuel tank
        'fuel_efficiency': 15.0
    },
    'Recycling Truck Echo': {
        'capacity': 12000.0,  # Increased from 4500
        'fuel_tank_capacity': 120.0,
        'fuel_efficiency': 9.0
    },
    'Mini Collection Van Foxtrot': {
        'capacity': 4000.0,  # Increased from 1500
        'fuel_tank_capacity': 50.0,
        'fuel_efficiency': 14.0
    },
    'Large Capacity Truck Golf': {
        'capacity': 18000.0,  # Increased from 6000
        'fuel_tank_capacity': 180.0,
        'fuel_efficiency': 7.5
    },
    'Eco-Friendly Electric Van Hotel': {
        'capacity': 5000.0,  # Increased from 1800
        'fuel_tank_capacity': 0.0,  # Electric vehicle
        'fuel_efficiency': 20.0  # Equivalent efficiency
    },
    'hrea': {
        'capacity': 5000.0,  # Increased from 100
        'fuel_tank_capacity': 80.0,
        'fuel_efficiency': 5.0
    }
}

def update_vehicles():
    """Update vehicle capacities and fuel tank capacities."""
    updated_count = 0
    created_count = 0
    
    for vehicle_name, updates in VEHICLE_UPDATES.items():
        try:
            vehicle = Vehicle.objects.get(name=vehicle_name)
            vehicle.capacity = updates['capacity']
            vehicle.fuel_tank_capacity = updates['fuel_tank_capacity']
            vehicle.fuel_efficiency = updates['fuel_efficiency']
            vehicle.save()
            updated_count += 1
            print(f"Updated: {vehicle_name}")
            print(f"  - Capacity: {vehicle.capacity}L")
            print(f"  - Fuel Tank: {vehicle.fuel_tank_capacity}L")
            print(f"  - Fuel Efficiency: {vehicle.fuel_efficiency} km/L")
            print()
        except Vehicle.DoesNotExist:
            print(f"Vehicle '{vehicle_name}' not found, skipping...")
    
    # Update any other vehicles with default values
    other_vehicles = Vehicle.objects.exclude(name__in=VEHICLE_UPDATES.keys())
    for vehicle in other_vehicles:
        if not vehicle.fuel_tank_capacity or vehicle.fuel_tank_capacity == 0:
            # Set default fuel tank capacity based on vehicle type
            default_fuel_tank = {
                'truck': 150.0,
                'van': 60.0,
                'tractor': 80.0,
                'compactor': 200.0
            }.get(vehicle.vehicle_type, 100.0)
            
            vehicle.fuel_tank_capacity = default_fuel_tank
            # Increase capacity if it's too low
            if vehicle.capacity < 5000:
                vehicle.capacity = 5000.0
            vehicle.save()
            updated_count += 1
            print(f"Updated: {vehicle.name} (defaults applied)")
            print(f"  - Capacity: {vehicle.capacity}L")
            print(f"  - Fuel Tank: {vehicle.fuel_tank_capacity}L")
            print()
    
    print(f"Update completed!")
    print(f"  - Updated vehicles: {updated_count}")
    print(f"  - Created vehicles: {created_count}")

if __name__ == '__main__':
    update_vehicles()


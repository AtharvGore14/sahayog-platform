"""
Script to restore routes from backup database to current database.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sahayog.settings')
django.setup()

from route_optimizer.models import OptimizedRoute, RouteLocation, Vehicle, Location
import sqlite3

# Paths
BACKUP_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'project01_route_opt_backup', 'db.sqlite3')
CURRENT_DB = os.path.join(os.path.dirname(__file__), 'db.sqlite3')

print(f"Backup DB: {BACKUP_DB}")
print(f"Current DB: {CURRENT_DB}")

# Connect to backup database
backup_conn = sqlite3.connect(BACKUP_DB)
backup_conn.row_factory = sqlite3.Row
backup_cursor = backup_conn.cursor()

# Connect to current database
current_conn = sqlite3.connect(CURRENT_DB)
current_conn.row_factory = sqlite3.Row
current_cursor = current_conn.cursor()

try:
    # First, copy vehicles if they don't exist
    print("\n1. Copying vehicles...")
    backup_cursor.execute("SELECT * FROM vehicles")
    backup_vehicles = backup_cursor.fetchall()
    
    vehicle_map = {}  # Map old vehicle ID to new vehicle ID
    
    for veh in backup_vehicles:
        # Check if vehicle exists by name
        current_cursor.execute("SELECT id FROM vehicles WHERE name = ?", (veh['name'],))
        existing = current_cursor.fetchone()
        
        if existing:
            vehicle_map[veh['id']] = existing['id']
            print(f"  Vehicle '{veh['name']}' already exists (ID: {existing['id']})")
        else:
            # Insert vehicle
            current_cursor.execute("""
                INSERT INTO vehicles (name, vehicle_type, capacity, fuel_efficiency, 
                    current_latitude, current_longitude, is_available, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                veh['name'], veh['vehicle_type'], veh['capacity'], veh['fuel_efficiency'],
                veh['current_latitude'], veh['current_longitude'], veh['is_available'],
                veh['created_at'], veh['updated_at']
            ))
            new_id = current_cursor.lastrowid
            vehicle_map[veh['id']] = new_id
            print(f"  Copied vehicle '{veh['name']}' (Old ID: {veh['id']} -> New ID: {new_id})")
    
    current_conn.commit()
    
    # Second, copy locations if they don't exist
    print("\n2. Copying locations...")
    backup_cursor.execute("SELECT * FROM locations")
    backup_locations = backup_cursor.fetchall()
    
    location_map = {}  # Map old location ID to new location ID
    
    for loc in backup_locations:
        # Check if location exists by name and coordinates
        current_cursor.execute("""
            SELECT id FROM locations 
            WHERE name = ? AND latitude = ? AND longitude = ?
        """, (loc['name'], loc['latitude'], loc['longitude']))
        existing = current_cursor.fetchone()
        
        if existing:
            location_map[loc['id']] = existing['id']
            print(f"  Location '{loc['name']}' already exists (ID: {existing['id']})")
        else:
            # Insert location
            current_cursor.execute("""
                INSERT INTO locations (name, address, latitude, longitude, location_type,
                    priority, estimated_waste_volume, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                loc['name'], loc['address'], loc['latitude'], loc['longitude'],
                loc['location_type'], loc['priority'], loc['estimated_waste_volume'],
                loc['is_active'], loc['created_at'], loc['updated_at']
            ))
            new_id = current_cursor.lastrowid
            location_map[loc['id']] = new_id
            print(f"  Copied location '{loc['name']}' (Old ID: {loc['id']} -> New ID: {new_id})")
    
    current_conn.commit()
    
    # Third, copy routes
    print("\n3. Copying routes...")
    backup_cursor.execute("SELECT * FROM optimized_routes ORDER BY id")
    backup_routes = backup_cursor.fetchall()
    
    route_map = {}  # Map old route ID to new route ID
    routes_copied = 0
    
    for route in backup_routes:
        old_vehicle_id = route['vehicle_id']
        new_vehicle_id = vehicle_map.get(old_vehicle_id)
        
        if not new_vehicle_id:
            print(f"  WARNING: Route '{route['route_name']}' references vehicle ID {old_vehicle_id} which doesn't exist. Skipping.")
            continue
        
        # Insert route
        current_cursor.execute("""
            INSERT INTO optimized_routes (route_name, vehicle_id, total_distance, total_duration,
                estimated_fuel_consumption, total_waste_volume, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            route['route_name'], new_vehicle_id, route['total_distance'], route['total_duration'],
            route['estimated_fuel_consumption'], route['total_waste_volume'],
            route['status'], route['created_at'], route['updated_at']
        ))
        new_route_id = current_cursor.lastrowid
        route_map[route['id']] = new_route_id
        routes_copied += 1
        print(f"  Copied route '{route['route_name']}' (Old ID: {route['id']} -> New ID: {new_route_id})")
    
    current_conn.commit()
    
    # Fourth, copy route-location relationships
    print("\n4. Copying route-location relationships...")
    # Try different possible table names
    table_names = ['route_locations', 'route_optimizer_routelocation']
    backup_route_locations = []
    
    for table_name in table_names:
        try:
            backup_cursor.execute(f"SELECT * FROM {table_name} ORDER BY id")
            backup_route_locations = backup_cursor.fetchall()
            print(f"  Found table: {table_name} ({len(backup_route_locations)} relationships)")
            break
        except sqlite3.OperationalError:
            continue
    
    if not backup_route_locations:
        print("  WARNING: Could not find route-location relationships table")
        relationships_copied = 0
    else:
        relationships_copied = 0
        
        for rl in backup_route_locations:
            old_route_id = rl['route_id']
            old_location_id = rl['location_id']
            
            new_route_id = route_map.get(old_route_id)
            new_location_id = location_map.get(old_location_id)
            
            if not new_route_id or not new_location_id:
                print(f"  WARNING: RouteLocation references missing route or location. Skipping.")
                continue
            
            # Check if relationship already exists
            current_cursor.execute("""
                SELECT id FROM route_locations 
                WHERE route_id = ? AND location_id = ?
            """, (new_route_id, new_location_id))
            existing = current_cursor.fetchone()
            
            if existing:
                continue
            
            # Insert relationship (handle all possible columns)
            # sqlite3.Row objects use dictionary-style access, not .get()
            visit_order = rl['visit_order'] if 'visit_order' in rl.keys() else 0
            estimated_arrival_time = rl.get('estimated_arrival_time', '00:00:00') if hasattr(rl, 'get') else (rl['estimated_arrival_time'] if 'estimated_arrival_time' in rl.keys() else '00:00:00')
            estimated_departure_time = rl.get('estimated_departure_time', '00:00:00') if hasattr(rl, 'get') else (rl['estimated_departure_time'] if 'estimated_departure_time' in rl.keys() else '00:00:00')
            estimated_waste_collected = rl.get('estimated_waste_collected', 0) if hasattr(rl, 'get') else (rl['estimated_waste_collected'] if 'estimated_waste_collected' in rl.keys() else 0)
            
            try:
                current_cursor.execute("""
                    INSERT INTO route_locations (route_id, location_id, visit_order, 
                        estimated_arrival_time, estimated_departure_time, estimated_waste_collected)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    new_route_id, new_location_id, visit_order,
                    estimated_arrival_time, estimated_departure_time, estimated_waste_collected
                ))
                relationships_copied += 1
            except Exception as e:
                # Try simpler insert if columns don't match
                try:
                    current_cursor.execute("""
                        INSERT INTO route_locations (route_id, location_id, visit_order)
                        VALUES (?, ?, ?)
                    """, (new_route_id, new_location_id, visit_order))
                    relationships_copied += 1
                except Exception as e2:
                    print(f"  WARNING: Could not insert relationship: {e2}")
    
    current_conn.commit()
    
    print(f"\nRestore completed!")
    print(f"   - Vehicles: {len(vehicle_map)}")
    print(f"   - Locations: {len(location_map)}")
    print(f"   - Routes: {routes_copied}")
    print(f"   - Route-Location relationships: {relationships_copied}")
    
except Exception as e:
    print(f"\nError during restore: {e}")
    import traceback
    traceback.print_exc()
    current_conn.rollback()
finally:
    backup_conn.close()
    current_conn.close()


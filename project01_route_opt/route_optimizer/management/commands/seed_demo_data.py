"""
Management command to seed demo data for Route Optimizer.
Run with: python manage.py seed_demo_data
"""

from django.core.management.base import BaseCommand
from route_optimizer.models import Location, Vehicle


class Command(BaseCommand):
    help = 'Seed demo data for Route Optimizer (locations and vehicles)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-seeding even if data exists',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # Demo locations
        demo_locations = [
            # Downtown/Central Area
            {'name': 'Central Market Bin', 'address': '123 Main Street, Downtown', 'latitude': 20.5937, 'longitude': 78.9629, 'location_type': 'bin', 'priority': 'high', 'estimated_waste_volume': 150.0, 'is_active': True},
            {'name': 'City Hall Collection Point', 'address': '456 Government Square, Downtown', 'latitude': 20.5987, 'longitude': 78.9679, 'location_type': 'collection_point', 'priority': 'high', 'estimated_waste_volume': 180.0, 'is_active': True},
            {'name': 'Downtown Plaza Bin', 'address': '789 Commerce Street, Central', 'latitude': 20.5887, 'longitude': 78.9579, 'location_type': 'bin', 'priority': 'medium', 'estimated_waste_volume': 120.0, 'is_active': True},
            
            # Shopping District
            {'name': 'Shopping Mall Collection Point', 'address': '456 Mall Road, Shopping District', 'latitude': 20.6037, 'longitude': 78.9729, 'location_type': 'collection_point', 'priority': 'medium', 'estimated_waste_volume': 200.0, 'is_active': True},
            {'name': 'Retail Complex Bin', 'address': '321 Retail Avenue, Shopping District', 'latitude': 20.6087, 'longitude': 78.9779, 'location_type': 'bin', 'priority': 'medium', 'estimated_waste_volume': 140.0, 'is_active': True},
            {'name': 'Market Square Bin', 'address': '654 Market Street, Shopping Area', 'latitude': 20.5987, 'longitude': 78.9779, 'location_type': 'bin', 'priority': 'high', 'estimated_waste_volume': 160.0, 'is_active': True},
            
            # Residential Areas
            {'name': 'Residential Area Bin', 'address': '789 Residential Lane, Suburbs', 'latitude': 20.5837, 'longitude': 78.9529, 'location_type': 'bin', 'priority': 'low', 'estimated_waste_volume': 75.0, 'is_active': True},
            {'name': 'Housing Society Collection Point', 'address': '147 Housing Complex, Suburbs', 'latitude': 20.5787, 'longitude': 78.9479, 'location_type': 'collection_point', 'priority': 'low', 'estimated_waste_volume': 90.0, 'is_active': True},
            {'name': 'Apartment Complex Bin', 'address': '258 Apartment Road, Residential', 'latitude': 20.5737, 'longitude': 78.9529, 'location_type': 'bin', 'priority': 'medium', 'estimated_waste_volume': 110.0, 'is_active': True},
            
            # Industrial Zone
            {'name': 'Industrial Zone Bin', 'address': '321 Industrial Park, Factory Area', 'latitude': 20.6137, 'longitude': 78.9829, 'location_type': 'bin', 'priority': 'urgent', 'estimated_waste_volume': 300.0, 'is_active': True},
            {'name': 'Warehouse Collection Point', 'address': '654 Warehouse Road, Industrial', 'latitude': 20.6187, 'longitude': 78.9879, 'location_type': 'collection_point', 'priority': 'urgent', 'estimated_waste_volume': 350.0, 'is_active': True},
            {'name': 'Factory Area Bin', 'address': '987 Factory Street, Industrial Zone', 'latitude': 20.6237, 'longitude': 78.9929, 'location_type': 'bin', 'priority': 'high', 'estimated_waste_volume': 280.0, 'is_active': True},
            
            # Educational Institutions
            {'name': 'University Campus Bin', 'address': '654 University Road, Campus Area', 'latitude': 20.5737, 'longitude': 78.9429, 'location_type': 'bin', 'priority': 'medium', 'estimated_waste_volume': 120.0, 'is_active': True},
            {'name': 'School Collection Point', 'address': '321 School Lane, Education District', 'latitude': 20.5687, 'longitude': 78.9379, 'location_type': 'collection_point', 'priority': 'medium', 'estimated_waste_volume': 95.0, 'is_active': True},
            {'name': 'College Campus Bin', 'address': '147 College Avenue, Academic Area', 'latitude': 20.5637, 'longitude': 78.9429, 'location_type': 'bin', 'priority': 'medium', 'estimated_waste_volume': 105.0, 'is_active': True},
            
            # Healthcare Facilities
            {'name': 'Hospital Collection Point', 'address': '987 Medical Center, Healthcare District', 'latitude': 20.6237, 'longitude': 78.9929, 'location_type': 'collection_point', 'priority': 'urgent', 'estimated_waste_volume': 250.0, 'is_active': True},
            {'name': 'Clinic Bin', 'address': '456 Health Street, Medical Area', 'latitude': 20.6187, 'longitude': 78.9879, 'location_type': 'bin', 'priority': 'high', 'estimated_waste_volume': 130.0, 'is_active': True},
            
            # Parks and Recreation
            {'name': 'Park Area Bin', 'address': '147 Park Street, Recreation Area', 'latitude': 20.5637, 'longitude': 78.9329, 'location_type': 'bin', 'priority': 'low', 'estimated_waste_volume': 50.0, 'is_active': True},
            {'name': 'Stadium Collection Point', 'address': '741 Stadium Boulevard, Sports Complex', 'latitude': 20.6437, 'longitude': 79.0129, 'location_type': 'collection_point', 'priority': 'medium', 'estimated_waste_volume': 220.0, 'is_active': True},
            {'name': 'Recreation Center Bin', 'address': '852 Recreation Road, Leisure Area', 'latitude': 20.5537, 'longitude': 78.9229, 'location_type': 'bin', 'priority': 'low', 'estimated_waste_volume': 65.0, 'is_active': True},
            
            # Transportation Hubs
            {'name': 'Airport Collection Point', 'address': '369 Airport Road, Transportation Hub', 'latitude': 20.5537, 'longitude': 78.9229, 'location_type': 'collection_point', 'priority': 'high', 'estimated_waste_volume': 400.0, 'is_active': True},
            {'name': 'Bus Station Bin', 'address': '159 Transit Street, Transport Hub', 'latitude': 20.5487, 'longitude': 78.9179, 'location_type': 'bin', 'priority': 'medium', 'estimated_waste_volume': 170.0, 'is_active': True},
            {'name': 'Railway Station Collection Point', 'address': '357 Railway Road, Transport Area', 'latitude': 20.5437, 'longitude': 78.9129, 'location_type': 'collection_point', 'priority': 'high', 'estimated_waste_volume': 380.0, 'is_active': True},
            
            # Business District
            {'name': 'Business District Bin', 'address': '258 Business Avenue, Corporate Area', 'latitude': 20.6337, 'longitude': 79.0029, 'location_type': 'bin', 'priority': 'high', 'estimated_waste_volume': 180.0, 'is_active': True},
            {'name': 'Office Complex Collection Point', 'address': '741 Corporate Tower, Business District', 'latitude': 20.6387, 'longitude': 79.0079, 'location_type': 'collection_point', 'priority': 'high', 'estimated_waste_volume': 210.0, 'is_active': True},
            
            # Outskirts/Extended Areas
            {'name': 'Suburban Collection Point', 'address': '852 Suburban Road, Outskirts', 'latitude': 20.5287, 'longitude': 78.9029, 'location_type': 'collection_point', 'priority': 'low', 'estimated_waste_volume': 85.0, 'is_active': True},
            {'name': 'Rural Area Bin', 'address': '963 Country Lane, Rural Zone', 'latitude': 20.5137, 'longitude': 78.8929, 'location_type': 'bin', 'priority': 'low', 'estimated_waste_volume': 60.0, 'is_active': True},
        ]
        
        # Demo vehicles
        demo_vehicles = [
            {'name': 'Waste Collection Truck Alpha', 'vehicle_type': 'truck', 'capacity': 5000.0, 'fuel_efficiency': 8.5, 'current_latitude': 20.5937, 'current_longitude': 78.9629, 'is_available': True},
            {'name': 'Compact Collection Van Beta', 'vehicle_type': 'van', 'capacity': 2000.0, 'fuel_efficiency': 12.0, 'current_latitude': 20.6037, 'current_longitude': 78.9729, 'is_available': True},
            {'name': 'Heavy Duty Compactor Gamma', 'vehicle_type': 'compactor', 'capacity': 8000.0, 'fuel_efficiency': 6.5, 'current_latitude': 20.5837, 'current_longitude': 78.9529, 'is_available': True},
            {'name': 'Agricultural Tractor Delta', 'vehicle_type': 'tractor', 'capacity': 3000.0, 'fuel_efficiency': 15.0, 'current_latitude': 20.6137, 'current_longitude': 78.9829, 'is_available': True},
            {'name': 'Recycling Truck Echo', 'vehicle_type': 'truck', 'capacity': 4500.0, 'fuel_efficiency': 9.0, 'current_latitude': 20.5737, 'current_longitude': 78.9429, 'is_available': True},
            {'name': 'Mini Collection Van Foxtrot', 'vehicle_type': 'van', 'capacity': 1500.0, 'fuel_efficiency': 14.0, 'current_latitude': 20.5637, 'current_longitude': 78.9329, 'is_available': True},
            {'name': 'Large Capacity Truck Golf', 'vehicle_type': 'truck', 'capacity': 6000.0, 'fuel_efficiency': 7.5, 'current_latitude': 20.6237, 'current_longitude': 78.9929, 'is_available': True},
            {'name': 'Eco-Friendly Electric Van Hotel', 'vehicle_type': 'van', 'capacity': 1800.0, 'fuel_efficiency': 20.0, 'current_latitude': 20.5537, 'current_longitude': 78.9229, 'is_available': True},
        ]
        
        # Seed locations
        locations_count = Location.objects.count()
        if locations_count == 0 or force:
            created_locations = 0
            for loc_data in demo_locations:
                loc, created = Location.objects.get_or_create(name=loc_data['name'], defaults=loc_data)
                if created:
                    created_locations += 1
            self.stdout.write(
                self.style.SUCCESS(f'Successfully seeded {created_locations} locations (total: {Location.objects.count()})')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Locations already exist ({locations_count}). Use --force to re-seed.')
            )
        
        # Seed vehicles
        vehicles_count = Vehicle.objects.count()
        if vehicles_count == 0 or force:
            created_vehicles = 0
            for veh_data in demo_vehicles:
                veh, created = Vehicle.objects.get_or_create(name=veh_data['name'], defaults=veh_data)
                if created:
                    created_vehicles += 1
            self.stdout.write(
                self.style.SUCCESS(f'Successfully seeded {created_vehicles} vehicles (total: {Vehicle.objects.count()})')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Vehicles already exist ({vehicles_count}). Use --force to re-seed.')
            )


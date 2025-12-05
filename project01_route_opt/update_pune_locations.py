"""
Script to update locations to real Pune locations scattered across the city.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sahayog.settings')
django.setup()

from route_optimizer.models import Location

# Real Pune locations with coordinates (scattered across Pune)
PUNE_LOCATIONS = [
    # Central Pune / Camp Area
    {
        'name': 'Camp Area Collection Point',
        'address': 'MG Road, Camp, Pune - 411001',
        'latitude': 18.5204,
        'longitude': 73.8567,
        'location_type': 'collection_point',
        'priority': 'high',
        'estimated_waste_volume': 2500.0
    },
    {
        'name': 'Shivajinagar Waste Bin',
        'address': 'Shivajinagar, Pune - 411005',
        'latitude': 18.5314,
        'longitude': 73.8446,
        'location_type': 'bin',
        'priority': 'high',
        'estimated_waste_volume': 1800.0
    },
    
    # Koregaon Park / Kalyani Nagar
    {
        'name': 'Koregaon Park Collection Point',
        'address': 'Koregaon Park, Pune - 411001',
        'latitude': 18.5450,
        'longitude': 73.8972,
        'location_type': 'collection_point',
        'priority': 'medium',
        'estimated_waste_volume': 2200.0
    },
    {
        'name': 'Kalyani Nagar Bin',
        'address': 'Kalyani Nagar, Pune - 411014',
        'latitude': 18.5500,
        'longitude': 73.9050,
        'location_type': 'bin',
        'priority': 'medium',
        'estimated_waste_volume': 1500.0
    },
    
    # Viman Nagar / Airport Area
    {
        'name': 'Viman Nagar Collection Point',
        'address': 'Viman Nagar, Pune - 411014',
        'latitude': 18.5680,
        'longitude': 73.9190,
        'location_type': 'collection_point',
        'priority': 'high',
        'estimated_waste_volume': 2800.0
    },
    {
        'name': 'Lohegaon Airport Bin',
        'address': 'Near Pune Airport, Lohegaon, Pune - 411032',
        'latitude': 18.5822,
        'longitude': 73.9197,
        'location_type': 'bin',
        'priority': 'high',
        'estimated_waste_volume': 3200.0
    },
    
    # Hinjewadi / IT Hub
    {
        'name': 'Hinjewadi IT Park Collection Point',
        'address': 'Hinjewadi IT Park, Pune - 411057',
        'latitude': 18.5917,
        'longitude': 73.7306,
        'location_type': 'collection_point',
        'priority': 'high',
        'estimated_waste_volume': 3500.0
    },
    {
        'name': 'Wakad Waste Bin',
        'address': 'Wakad, Pune - 411057',
        'latitude': 18.5990,
        'longitude': 73.7500,
        'location_type': 'bin',
        'priority': 'medium',
        'estimated_waste_volume': 2000.0
    },
    
    # Baner / Balewadi
    {
        'name': 'Baner Collection Point',
        'address': 'Baner, Pune - 411045',
        'latitude': 18.5600,
        'longitude': 73.7800,
        'location_type': 'collection_point',
        'priority': 'medium',
        'estimated_waste_volume': 2400.0
    },
    {
        'name': 'Balewadi Stadium Bin',
        'address': 'Near Balewadi Stadium, Pune - 411045',
        'latitude': 18.5700,
        'longitude': 73.7900,
        'location_type': 'bin',
        'priority': 'medium',
        'estimated_waste_volume': 1900.0
    },
    
    # Aundh / Pashan
    {
        'name': 'Aundh Collection Point',
        'address': 'Aundh, Pune - 411007',
        'latitude': 18.5500,
        'longitude': 73.8200,
        'location_type': 'collection_point',
        'priority': 'medium',
        'estimated_waste_volume': 2100.0
    },
    {
        'name': 'Pashan Waste Bin',
        'address': 'Pashan, Pune - 411008',
        'latitude': 18.5400,
        'longitude': 73.8000,
        'location_type': 'bin',
        'priority': 'low',
        'estimated_waste_volume': 1200.0
    },
    
    # Hadapsar / Magarpatta
    {
        'name': 'Magarpatta Collection Point',
        'address': 'Magarpatta City, Hadapsar, Pune - 411013',
        'latitude': 18.5100,
        'longitude': 73.9200,
        'location_type': 'collection_point',
        'priority': 'high',
        'estimated_waste_volume': 3000.0
    },
    {
        'name': 'Hadapsar Waste Bin',
        'address': 'Hadapsar, Pune - 411028',
        'latitude': 18.5000,
        'longitude': 73.9100,
        'location_type': 'bin',
        'priority': 'medium',
        'estimated_waste_volume': 1700.0
    },
    
    # Kothrud / Karve Nagar
    {
        'name': 'Kothrud Collection Point',
        'address': 'Kothrud, Pune - 411038',
        'latitude': 18.5100,
        'longitude': 73.8100,
        'location_type': 'collection_point',
        'priority': 'high',
        'estimated_waste_volume': 2600.0
    },
    {
        'name': 'Karve Nagar Waste Bin',
        'address': 'Karve Nagar, Pune - 411052',
        'latitude': 18.5000,
        'longitude': 73.8200,
        'location_type': 'bin',
        'priority': 'medium',
        'estimated_waste_volume': 1600.0
    },
    
    # Deccan / FC Road
    {
        'name': 'FC Road Collection Point',
        'address': 'Fergusson College Road, Deccan, Pune - 411004',
        'latitude': 18.5150,
        'longitude': 73.8400,
        'location_type': 'collection_point',
        'priority': 'high',
        'estimated_waste_volume': 2700.0
    },
    {
        'name': 'JM Road Waste Bin',
        'address': 'Jangli Maharaj Road, Deccan, Pune - 411004',
        'latitude': 18.5200,
        'longitude': 73.8450,
        'location_type': 'bin',
        'priority': 'high',
        'estimated_waste_volume': 2300.0
    },
    
    # Katraj / Satara Road
    {
        'name': 'Katraj Collection Point',
        'address': 'Katraj, Pune - 411046',
        'latitude': 18.4500,
        'longitude': 73.8500,
        'location_type': 'collection_point',
        'priority': 'medium',
        'estimated_waste_volume': 2000.0
    },
    {
        'name': 'Bibwewadi Waste Bin',
        'address': 'Bibwewadi, Pune - 411037',
        'latitude': 18.4800,
        'longitude': 73.8600,
        'location_type': 'bin',
        'priority': 'medium',
        'estimated_waste_volume': 1400.0
    },
    
    # Pimpri-Chinchwad
    {
        'name': 'Pimpri Collection Point',
        'address': 'Pimpri, Pune - 411018',
        'latitude': 18.6200,
        'longitude': 73.8000,
        'location_type': 'collection_point',
        'priority': 'high',
        'estimated_waste_volume': 3100.0
    },
    {
        'name': 'Chinchwad Waste Bin',
        'address': 'Chinchwad, Pune - 411019',
        'latitude': 18.6300,
        'longitude': 73.8100,
        'location_type': 'bin',
        'priority': 'medium',
        'estimated_waste_volume': 1800.0
    },
    
    # Depots and Landfills
    {
        'name': 'Uruli Kanchan Depot',
        'address': 'Uruli Kanchan, Pune - 412202',
        'latitude': 18.4500,
        'longitude': 74.0000,
        'location_type': 'depot',
        'priority': 'urgent',
        'estimated_waste_volume': 50000.0
    },
    {
        'name': 'Phursungi Landfill',
        'address': 'Phursungi Landfill Site, Pune - 412308',
        'latitude': 18.4000,
        'longitude': 73.9500,
        'location_type': 'landfill',
        'priority': 'urgent',
        'estimated_waste_volume': 100000.0
    },
    
    # Additional scattered locations
    {
        'name': 'Warje Collection Point',
        'address': 'Warje, Pune - 411052',
        'latitude': 18.4900,
        'longitude': 73.7800,
        'location_type': 'collection_point',
        'priority': 'medium',
        'estimated_waste_volume': 1900.0
    },
    {
        'name': 'Sinhagad Road Waste Bin',
        'address': 'Sinhagad Road, Pune - 411030',
        'latitude': 18.4700,
        'longitude': 73.7700,
        'location_type': 'bin',
        'priority': 'low',
        'estimated_waste_volume': 1100.0
    },
    {
        'name': 'Kondhwa Collection Point',
        'address': 'Kondhwa, Pune - 411048',
        'latitude': 18.4600,
        'longitude': 73.9000,
        'location_type': 'collection_point',
        'priority': 'medium',
        'estimated_waste_volume': 2100.0
    },
    {
        'name': 'Wanowrie Waste Bin',
        'address': 'Wanowrie, Pune - 411040',
        'latitude': 18.5000,
        'longitude': 73.8800,
        'location_type': 'bin',
        'priority': 'medium',
        'estimated_waste_volume': 1500.0
    },
    {
        'name': 'Bund Garden Collection Point',
        'address': 'Bund Garden Road, Pune - 411001',
        'latitude': 18.5300,
        'longitude': 73.8700,
        'location_type': 'collection_point',
        'priority': 'high',
        'estimated_waste_volume': 2400.0
    },
    {
        'name': 'Senapati Bapat Road Waste Bin',
        'address': 'Senapati Bapat Road, Pune - 411016',
        'latitude': 18.5400,
        'longitude': 73.8300,
        'location_type': 'bin',
        'priority': 'medium',
        'estimated_waste_volume': 1600.0
    },
]

def update_locations():
    """Update existing locations with Pune locations."""
    existing_locations = Location.objects.all().order_by('id')
    total_locations = existing_locations.count()
    pune_locations_count = len(PUNE_LOCATIONS)
    
    print(f"Found {total_locations} existing locations")
    print(f"Will update with {pune_locations_count} Pune locations\n")
    
    # Update existing locations
    updated_count = 0
    for i, location in enumerate(existing_locations):
        if i < pune_locations_count:
            pune_loc = PUNE_LOCATIONS[i]
            location.name = pune_loc['name']
            location.address = pune_loc['address']
            location.latitude = pune_loc['latitude']
            location.longitude = pune_loc['longitude']
            location.location_type = pune_loc['location_type']
            location.priority = pune_loc['priority']
            location.estimated_waste_volume = pune_loc['estimated_waste_volume']
            location.is_active = True
            location.save()
            updated_count += 1
            print(f"Updated: {location.name} ({location.latitude}, {location.longitude})")
    
    # Create new locations if we have more Pune locations than existing
    if pune_locations_count > total_locations:
        for i in range(total_locations, pune_locations_count):
            pune_loc = PUNE_LOCATIONS[i]
            Location.objects.create(
                name=pune_loc['name'],
                address=pune_loc['address'],
                latitude=pune_loc['latitude'],
                longitude=pune_loc['longitude'],
                location_type=pune_loc['location_type'],
                priority=pune_loc['priority'],
                estimated_waste_volume=pune_loc['estimated_waste_volume'],
                is_active=True
            )
            updated_count += 1
            print(f"Created: {pune_loc['name']} ({pune_loc['latitude']}, {pune_loc['longitude']})")
    
    print(f"\nSuccessfully updated/created {updated_count} Pune locations!")
    print(f"\nLocation distribution:")
    print(f"  - Collection Points: {Location.objects.filter(location_type='collection_point').count()}")
    print(f"  - Waste Bins: {Location.objects.filter(location_type='bin').count()}")
    print(f"  - Depots: {Location.objects.filter(location_type='depot').count()}")
    print(f"  - Landfills: {Location.objects.filter(location_type='landfill').count()}")

if __name__ == '__main__':
    update_locations()


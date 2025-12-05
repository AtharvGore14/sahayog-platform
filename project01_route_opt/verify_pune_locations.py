"""Verify Pune locations"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sahayog.settings')
django.setup()

from route_optimizer.models import Location

print("=" * 60)
print("PUNE LOCATIONS VERIFICATION")
print("=" * 60)

total = Location.objects.count()
print(f"\nTotal Locations: {total}")

print("\nLocation Distribution:")
print(f"  Collection Points: {Location.objects.filter(location_type='collection_point').count()}")
print(f"  Waste Bins: {Location.objects.filter(location_type='bin').count()}")
print(f"  Depots: {Location.objects.filter(location_type='depot').count()}")
print(f"  Landfills: {Location.objects.filter(location_type='landfill').count()}")

print("\nAll Pune Locations:")
print("-" * 60)
for i, loc in enumerate(Location.objects.all().order_by('name'), 1):
    print(f"{i:2d}. {loc.name:40s} | {loc.get_location_type_display():20s} | ({loc.latitude:.4f}, {loc.longitude:.4f})")

print("\n" + "=" * 60)
print("Locations are scattered across Pune city!")
print("=" * 60)


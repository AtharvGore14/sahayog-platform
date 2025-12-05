"""
Views for the route optimization web interface.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Avg, Count, F
from django.utils import timezone
from datetime import datetime, timedelta
import json
import sys
import traceback
from .models import Location, Vehicle, OptimizedRoute, RouteLocation, RouteOptimizationSession
from .optimization_engine import RouteOptimizationService
from django.contrib.auth import logout


def logout_view(request):
    """Log the user out (if authenticated) and return to the master landing page."""

    logout(request)
    return redirect('/')


def index(request):
    """Main dashboard view."""
    # Seed demo data if database is empty (for initial setup/demo)
    # Check locations and vehicles separately to ensure both are seeded
    locations_count = Location.objects.count()
    vehicles_count = Vehicle.objects.count()
    
    if locations_count == 0 or vehicles_count == 0:
        # Create demo locations - scattered across a wider geographic area
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
        # Only create locations if they don't exist
        if locations_count == 0:
            for loc_data in demo_locations:
                Location.objects.get_or_create(name=loc_data['name'], defaults=loc_data)
        
        # Create demo vehicles - more variety
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
        # Only create vehicles if they don't exist
        if vehicles_count == 0:
            for veh_data in demo_vehicles:
                Vehicle.objects.get_or_create(name=veh_data['name'], defaults=veh_data)
    
    # Get recent routes
    recent_routes = OptimizedRoute.objects.all().order_by('-created_at')[:5]
    
    # Get statistics
    total_routes = OptimizedRoute.objects.count()
    total_locations = Location.objects.filter(is_active=True).count()
    total_vehicles = Vehicle.objects.filter(is_available=True).count()
    
    # Get optimization history (use ORM objects so template date filter works)
    optimization_history = RouteOptimizationSession.objects.all().order_by('-created_at')[:5]
    
    context = {
        'recent_routes': recent_routes,
        'total_routes': total_routes,
        'total_locations': total_locations,
        'total_vehicles': total_vehicles,
        'optimization_history': optimization_history,
    }
    
    return render(request, 'route_optimizer/index.html', context)


def locations(request):
    """Locations management view."""
    search_query = request.GET.get('search', '')
    location_type = request.GET.get('type', '')
    
    locations_list = Location.objects.filter(is_active=True)
    
    if search_query:
        locations_list = locations_list.filter(
            Q(name__icontains=search_query) | 
            Q(address__icontains=search_query)
        )
    
    if location_type:
        locations_list = locations_list.filter(location_type=location_type)
    
    # Pagination
    paginator = Paginator(locations_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'location_type': location_type,
        'location_types': Location._meta.get_field('location_type').choices,
    }
    
    return render(request, 'route_optimizer/locations.html', context)


def vehicles(request):
    """Vehicles management view."""
    search_query = request.GET.get('search', '')
    vehicle_type = request.GET.get('type', '')
    
    vehicles_list = Vehicle.objects.all()
    
    if search_query:
        vehicles_list = vehicles_list.filter(
            Q(name__icontains=search_query) | 
            Q(vehicle_type__icontains=search_query)
        )
    
    if vehicle_type:
        vehicles_list = vehicles_list.filter(vehicle_type=vehicle_type)
    
    # Pagination
    paginator = Paginator(vehicles_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'vehicle_type': vehicle_type,
        'vehicle_types': Vehicle._meta.get_field('vehicle_type').choices,
    }
    
    return render(request, 'route_optimizer/vehicles.html', context)


@ensure_csrf_cookie
def optimize_route(request):
    """Route optimization form view."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            location_ids = data.get('location_ids', [])
            vehicle_id = data.get('vehicle_id')
            route_name = data.get('route_name', '')
            depot_location_id = data.get('depot_location_id')
            
            if not location_ids or not vehicle_id or not route_name:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required parameters'
                })
            
            # Create optimized route
            optimization_service = RouteOptimizationService()
            result = optimization_service.create_optimized_route(
                location_ids=location_ids,
                vehicle_id=vehicle_id,
                route_name=route_name,
                depot_location_id=depot_location_id
            )
            
            if result['success']:
                # Create a notification for new optimized route
                try:
                    from .models import Notification
                    route_name_safe = route_name or 'New Route'
                    Notification.objects.create(
                        title='Route Optimized',
                        message=f'Route "{route_name_safe}" has been created and is ready to start.',
                        notification_type='success',
                        is_read=False,
                    )
                    # Fuel capacity warnings
                    est_fuel = result.get('estimated_fuel_consumption')
                    fuel_tank_capacity = result.get('fuel_tank_capacity')
                    fuel_sufficient = result.get('fuel_sufficient', True)
                    fuel_warning = result.get('fuel_warning')
                    
                    if est_fuel is not None and fuel_tank_capacity:
                        try:
                            est_fuel_float = float(est_fuel)
                            fuel_tank_float = float(fuel_tank_capacity)
                            
                            if not fuel_sufficient:
                                # Critical: Fuel insufficient
                                Notification.objects.create(
                                    title='Fuel Capacity Exceeded',
                                    message=f'Route "{route_name_safe}" requires {est_fuel_float:.1f}L fuel, but vehicle fuel tank capacity is only {fuel_tank_float:.1f}L. Vehicle needs refueling during route.',
                                    notification_type='danger',
                                    is_read=False,
                                )
                            elif est_fuel_float > fuel_tank_float * 0.8:
                                # Warning: High fuel usage (>80% of tank)
                                Notification.objects.create(
                                    title='High Fuel Consumption Warning',
                                    message=f'Route "{route_name_safe}" will use {est_fuel_float:.1f}L fuel ({round((est_fuel_float/fuel_tank_float)*100, 1)}% of tank capacity). Consider refueling before starting.',
                                    notification_type='warning',
                                    is_read=False,
                                )
                        except Exception:
                            pass
                except Exception:
                    # Best-effort notifications; do not block route creation
                    pass
                messages.success(request, f'Route "{route_name}" optimized successfully!')
                return JsonResponse({
                    'success': True,
                    'route_id': result['route_id'],
                    'message': 'Route optimized successfully',
                    'total_distance': result.get('total_distance'),
                    'total_time': result.get('total_time'),
                    'estimated_fuel_consumption': result.get('estimated_fuel_consumption'),
                    'fuel_tank_capacity': result.get('fuel_tank_capacity'),
                    'fuel_sufficient': result.get('fuel_sufficient', True),
                    'fuel_warning': result.get('fuel_warning'),
                    'route_path_coords': result.get('route_path_coords', []),
                    'route_segments': result.get('route_segments', []),
                    'start': result.get('route_path_coords', [None])[0] if result.get('route_path_coords') else None,
                    'end': result.get('route_path_coords', [None])[-1] if result.get('route_path_coords') else None
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            # Log error for debugging
            print(f"Route optimization error: {e}", file=sys.stderr)
            print(error_trace, file=sys.stderr)
            return JsonResponse({
                'success': False,
                'error': f'Route optimization failed: {str(e)}'
            })
    
    # GET request - show form
    locations_list = Location.objects.filter(is_active=True)
    vehicles_list = Vehicle.objects.filter(is_available=True)
    
    context = {
        'locations': locations_list,
        'vehicles': vehicles_list,
    }
    
    return render(request, 'route_optimizer/optimize_route.html', context)


def route_details(request, route_id):
    """Route details view."""
    route = get_object_or_404(OptimizedRoute, id=route_id)
    route_locations = RouteLocation.objects.filter(route=route).order_by('visit_order')
    
    # Get route statistics
    optimization_service = RouteOptimizationService()
    stats_result = optimization_service.get_route_statistics(route_id)
    route_stats = stats_result.get('data', {}) if stats_result['success'] else {}
    
    # Prepare coordinates for map (from stored locations order)
    path_coords = []
    for rl in route_locations:
        if rl.location.latitude and rl.location.longitude:
            try:
                path_coords.append([float(rl.location.latitude), float(rl.location.longitude)])
            except Exception:
                pass
    context = {
        'route': route,
        'route_locations': route_locations,
        'route_stats': route_stats,
        'route_path_coords': path_coords,
    }
    
    return render(request, 'route_optimizer/route_details.html', context)


def routes_list(request):
    """Routes list view."""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    routes_list = OptimizedRoute.objects.all().order_by('-created_at')
    
    if search_query:
        routes_list = routes_list.filter(
            Q(route_name__icontains=search_query) | 
            Q(vehicle__name__icontains=search_query)
        )
    
    if status_filter:
        routes_list = routes_list.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(routes_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': OptimizedRoute._meta.get_field('status').choices,
    }
    
    return render(request, 'route_optimizer/routes_list.html', context)


def import_route_json(request):
    """Import a complete route from an exported JSON file and make it appear in recent/routes list."""
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            data = json.load(request.FILES['file'])
            if not isinstance(data, dict):
                messages.error(request, 'Invalid file. Expected a single route JSON object.')
                return redirect('route_optimizer:routes_list')

            # Create or find a vehicle
            vehicle = Vehicle.objects.filter(is_available=True, name=data.get('vehicle')).first()
            if not vehicle:
                vehicle = Vehicle.objects.filter(is_available=True).first()
            if not vehicle:
                messages.error(request, 'No available vehicle to assign for the imported route.')
                return redirect('route_optimizer:routes_list')

            # Build locations from stops (preferred) or path
            locations = []
            if isinstance(data.get('stops'), list) and data['stops']:
                for s in data['stops']:
                    lat, lng = s.get('latitude'), s.get('longitude')
                    if lat is None or lng is None:
                        continue
                    loc = Location.objects.create(
                        name=s.get('name') or 'Imported Stop',
                        address=s.get('address') or '',
                        latitude=lat,
                        longitude=lng,
                        location_type='collection_point',
                        priority='medium',
                        estimated_waste_volume=0,
                        is_active=True,
                    )
                    locations.append(loc)
            elif isinstance(data.get('path'), list):
                for idx, coord in enumerate(data['path']):
                    if isinstance(coord, (list, tuple)) and len(coord) >= 2:
                        loc = Location.objects.create(
                            name=f"Imported Point {idx+1}",
                            address='',
                            latitude=coord[0],
                            longitude=coord[1],
                            location_type='collection_point',
                            priority='medium',
                            estimated_waste_volume=0,
                            is_active=True,
                        )
                        locations.append(loc)
            else:
                messages.error(request, 'Route JSON missing stops or path array.')
                return redirect('route_optimizer:routes_list')

            if len(locations) < 2:
                messages.error(request, 'Need at least 2 locations to form a route.')
                return redirect('route_optimizer:routes_list')

            route_name = data.get('name') or 'Imported Route'

            # Use optimization service to create an OptimizedRoute so it shows up everywhere
            service = RouteOptimizationService()
            result = service.create_optimized_route(
                location_ids=[l.id for l in locations],
                vehicle_id=vehicle.id,
                route_name=route_name,
                depot_location_id=locations[0].id,
            )
            if not result.get('success'):
                messages.error(request, f"Failed to create route: {result.get('error')}")
                return redirect('route_optimizer:routes_list')

            messages.success(request, f'Route "{route_name}" imported successfully!')
            return redirect('route_optimizer:route_details', route_id=result['route_id'])
        except Exception as e:
            messages.error(request, f'Failed to import route: {str(e)}')
            return redirect('route_optimizer:routes_list')

    # GET: show simple upload page
    return render(request, 'route_optimizer/import_route_json.html')

def optimization_history(request):
    """Optimization history view."""
    sessions_list = RouteOptimizationSession.objects.all().order_by('-created_at')

    # Filters
    search = request.GET.get('search', '').strip()
    start_date = request.GET.get('start', '').strip()
    end_date = request.GET.get('end', '').strip()

    if search:
        sessions_list = sessions_list.filter(Q(session_name__icontains=search) | Q(algorithm_used__icontains=search))
    if start_date:
        sessions_list = sessions_list.filter(created_at__date__gte=start_date)
    if end_date:
        sessions_list = sessions_list.filter(created_at__date__lte=end_date)
    
    # Pagination
    paginator = Paginator(sessions_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'start': start_date,
        'end': end_date,
    }
    
    return render(request, 'route_optimizer/optimization_history.html', context)


# Live tracking controls (polling-based MVP)
@csrf_exempt
def api_route_tracking_start(request, route_id):
    """Start live tracking for a specific route by setting status to in_progress.
    Returns JSON with current status.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    try:
        route = get_object_or_404(OptimizedRoute, id=route_id)
        if route.status == 'completed':
            return JsonResponse({'success': False, 'error': 'Cannot start tracking on a completed route'})
        route.status = 'in_progress'
        route.save(update_fields=['status', 'updated_at'])
        # Notification: live tracking started
        try:
            from .models import Notification
            Notification.objects.create(
                title='Live Tracking Started',
                message=f'Live tracking started for route "{route.route_name}" (vehicle {route.vehicle.name}).',
                notification_type='info',
                is_read=False,
            )
        except Exception:
            pass
        return JsonResponse({'success': True, 'status': route.status})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def api_route_tracking_stop(request, route_id):
    """Stop live tracking for a specific route by setting status to completed.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    try:
        route = get_object_or_404(OptimizedRoute, id=route_id)
        route.status = 'completed'
        route.save(update_fields=['status', 'updated_at'])
        # Notification: trip finished
        try:
            from .models import Notification
            Notification.objects.create(
                title='Route Completed',
                message=f'Route "{route.route_name}" has been completed successfully.',
                notification_type='success',
                is_read=False,
            )
        except Exception:
            pass
        return JsonResponse({'success': True, 'status': route.status})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def api_route_tracking_status(request, route_id):
    """Return current tracking status for a route and a simulated position for MVP."""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    try:
        route = get_object_or_404(OptimizedRoute, id=route_id)
        progress = 0
        position = None
        try:
            rl = route.routelocation_set.all().order_by('visit_order').first()
            if rl and rl.location.latitude and rl.location.longitude:
                base_lat = float(rl.location.latitude)
                base_lng = float(rl.location.longitude)
                # simple jitter
                progress = (hash(route.id) % 100)
                position = {
                    'latitude': base_lat + (progress/1000.0),
                    'longitude': base_lng + (progress/1000.0),
                    'progress': progress,
                }
        except Exception:
            pass
        return JsonResponse({'success': True, 'status': route.status, 'position': position})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# API endpoints for AJAX requests
@csrf_exempt
def api_locations(request):
    """API endpoint to get locations for route optimization."""
    if request.method == 'GET':
        locations_list = Location.objects.filter(is_active=True).values(
            'id', 'name', 'address', 'location_type', 'priority', 'estimated_waste_volume'
        )
        return JsonResponse({'success': True, 'data': list(locations_list)})
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})


@csrf_exempt
def api_vehicles(request):
    """API endpoint to get vehicles for route optimization."""
    if request.method == 'GET':
        vehicles_list = Vehicle.objects.filter(is_available=True).values(
            'id', 'name', 'vehicle_type', 'capacity', 'fuel_efficiency'
        )
        return JsonResponse({'success': True, 'data': list(vehicles_list)})
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})


@csrf_exempt
def api_route_statistics(request, route_id):
    """API endpoint to get route statistics."""
    if request.method == 'GET':
        optimization_service = RouteOptimizationService()
        result = optimization_service.get_route_statistics(route_id)
        return JsonResponse(result)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})


@csrf_exempt
def api_optimization_history(request):
    """API endpoint to get optimization history."""
    if request.method == 'GET':
        optimization_service = RouteOptimizationService()
        result = optimization_service.get_optimization_history()
        return JsonResponse(result)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})


@csrf_exempt
def api_recommend_route(request):
    """Given selected locations and optional vehicle/depot, return recommended path preview."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            location_ids = data.get('location_ids', [])
            vehicle_id = data.get('vehicle_id')
            depot_location_id = data.get('depot_location_id')

            if not location_ids:
                return JsonResponse({'success': False, 'error': 'No locations provided'})

            # If no vehicle yet, fake a lightweight capacity using the first available vehicle or default params
            vehicle = None
            if vehicle_id:
                try:
                    vehicle = Vehicle.objects.get(id=vehicle_id)
                except Vehicle.DoesNotExist:
                    vehicle = None
            if not vehicle:
                # Create an in-memory lightweight vehicle substitute
                class _V: pass
                vehicle = _V()
                vehicle.capacity = 10_000

            # Optimize without saving
            optimizer = RouteOptimizationService().optimizer
            locations = list(Location.objects.filter(id__in=location_ids, is_active=True))
            if not locations:
                return JsonResponse({'success': False, 'error': 'Invalid locations'})

            depot_index = 0
            if depot_location_id:
                try:
                    depot_index = next(i for i, loc in enumerate(locations) if loc.id == depot_location_id)
                except StopIteration:
                    depot_index = 0

            # Use short solve for preview
            result = optimizer.optimize_route(locations, vehicle, depot_index, solve_seconds=5)
            if not result.get('success'):
                return JsonResponse(result)

            return JsonResponse({
                'success': True,
                'route_path_coords': result.get('route_path_coords', []),
                'route_segments': result.get('route_segments', []),
                'total_distance': result.get('total_distance'),
                'total_time': result.get('total_time'),
                'estimated_fuel_consumption': result.get('estimated_fuel_consumption'),
                'fuel_tank_capacity': result.get('fuel_tank_capacity'),
                'fuel_sufficient': result.get('fuel_sufficient', True),
                'fuel_warning': result.get('fuel_warning'),
                'start': result.get('route_path_coords', [None])[0] if result.get('route_path_coords') else None,
                'end': result.get('route_path_coords', [None])[-1] if result.get('route_path_coords') else None,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Method not allowed'})


@csrf_exempt
def api_delete_route(request, route_id):
    """Delete an optimized route and its associated waypoints."""
    if request.method == 'POST':
        try:
            route = get_object_or_404(OptimizedRoute, id=route_id)
            # Cascade will remove related RouteLocation because of FK through, but ensure delete
            route.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Method not allowed'})


# Management views
def add_location(request):
    """Add new location view."""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            address = request.POST.get('address')
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            location_type = request.POST.get('location_type')
            priority = request.POST.get('priority')
            estimated_waste_volume = request.POST.get('estimated_waste_volume', 0)
            
            if not all([name, address, latitude, longitude, location_type]):
                messages.error(request, 'Please fill all required fields')
                return redirect('add_location')
            
            Location.objects.create(
                name=name,
                address=address,
                latitude=latitude,
                longitude=longitude,
                location_type=location_type,
                priority=priority,
                estimated_waste_volume=estimated_waste_volume
            )
            
            messages.success(request, 'Location added successfully!')
            return redirect('locations')
            
        except Exception as e:
            messages.error(request, f'Error adding location: {str(e)}')
    
    context = {
        'location_types': Location._meta.get_field('location_type').choices,
        'priority_choices': Location._meta.get_field('priority').choices,
    }
    
    return render(request, 'route_optimizer/add_location.html', context)


def import_locations(request):
    """Bulk import locations from a JSON file uploaded via form.
    Expected JSON format: list of objects with keys
    [name, address, latitude, longitude, location_type, priority, estimated_waste_volume].
    If importing route data (with stops or path), also creates an OptimizedRoute.
    """
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            uploaded = request.FILES['file']
            data = json.load(uploaded)
            is_route_data = False
            route_name = None
            vehicle = None
            
            # Accept multiple formats: array of locations, exported route JSON with stops, or path coords
            if not isinstance(data, list):
                # Try exported route JSON shape
                if isinstance(data, dict):
                    is_route_data = True
                    route_name = data.get('name') or 'Imported Route'
                    
                    # Create or find a vehicle for route data
                    vehicle = Vehicle.objects.filter(is_available=True, name=data.get('vehicle')).first()
                    if not vehicle:
                        vehicle = Vehicle.objects.filter(is_available=True).first()
                    if not vehicle:
                        messages.error(request, 'No available vehicle to assign for the imported route.')
                        return redirect('route_optimizer:import_locations')
                    
                    if isinstance(data.get('stops'), list):
                        converted = []
                        for s in data['stops']:
                            converted.append({
                                'name': s.get('name') or f"Imported Stop {s.get('order') or ''}".strip(),
                                'address': s.get('address') or '',
                                'latitude': s.get('latitude'),
                                'longitude': s.get('longitude'),
                                'location_type': 'collection_point',
                                'priority': 'medium',
                                'estimated_waste_volume': 0,
                            })
                        data = converted
                    elif isinstance(data.get('path'), list):
                        converted = []
                        for idx, coord in enumerate(data['path']):
                            if isinstance(coord, (list, tuple)) and len(coord) >= 2:
                                converted.append({
                                    'name': f"Imported Point {idx+1}",
                                    'address': '',
                                    'latitude': coord[0],
                                    'longitude': coord[1],
                                    'location_type': 'collection_point',
                                    'priority': 'medium',
                                    'estimated_waste_volume': 0,
                                })
                        data = converted
                    else:
                        raise ValueError('JSON must be an array of locations')
                else:
                    raise ValueError('JSON must be an array of locations')

            total_items = len(data) if isinstance(data, list) else 0
            created_locations = []
            
            # For route data, create locations individually to get IDs
            if is_route_data:
                for item in data:
                    try:
                        name = item.get('name') or 'Imported Location'
                        address = item.get('address') or ''
                        lat = item.get('latitude')
                        lng = item.get('longitude')
                        loc_type = item.get('location_type') or 'waste_bin'
                        priority = item.get('priority') or 'medium'
                        waste = item.get('estimated_waste_volume') or 0
                        if lat is None or lng is None:
                            continue
                        location = Location.objects.create(
                            name=name,
                            address=address,
                            latitude=lat,
                            longitude=lng,
                            location_type=loc_type,
                            priority=priority,
                            estimated_waste_volume=waste,
                            is_active=True,
                        )
                        created_locations.append(location)
                    except Exception:
                        continue
            else:
                # For regular location arrays, use bulk_create for speed
                to_create = []
                for item in data:
                    try:
                        name = item.get('name') or 'Imported Location'
                        address = item.get('address') or ''
                        lat = item.get('latitude')
                        lng = item.get('longitude')
                        loc_type = item.get('location_type') or 'waste_bin'
                        priority = item.get('priority') or 'medium'
                        waste = item.get('estimated_waste_volume') or 0
                        if lat is None or lng is None:
                            continue
                        to_create.append(Location(
                            name=name,
                            address=address,
                            latitude=lat,
                            longitude=lng,
                            location_type=loc_type,
                            priority=priority,
                            estimated_waste_volume=waste,
                            is_active=True,
                        ))
                    except Exception:
                        continue
                
                if to_create:
                    Location.objects.bulk_create(to_create, batch_size=500)
                    created_locations = to_create

            created_count = len(created_locations)
            
            # If this was route data and we have enough locations, create an OptimizedRoute
            if is_route_data and len(created_locations) >= 2 and vehicle:
                try:
                    service = RouteOptimizationService()
                    result = service.create_optimized_route(
                        location_ids=[l.id for l in created_locations],
                        vehicle_id=vehicle.id,
                        route_name=route_name,
                        depot_location_id=created_locations[0].id,
                    )
                    if result.get('success'):
                        messages.success(request, f'Route "{route_name}" imported successfully with {created_count} stops!')
                        return redirect('route_optimizer:route_details', route_id=result['route_id'])
                    else:
                        messages.warning(request, f'Imported {created_count} locations but failed to create route: {result.get("error")}')
                except Exception as e:
                    messages.warning(request, f'Imported {created_count} locations but failed to create route: {str(e)}')
            else:
                if created_count < total_items:
                    skipped = total_items - created_count
                    messages.warning(request, f'Imported {created_count} of {total_items} locations. Skipped {skipped} without coordinates.')
                else:
                    messages.success(request, f'Imported {created_count} locations successfully.')
            
            return redirect('route_optimizer:locations')
        except Exception as e:
            messages.error(request, f'Failed to import locations: {str(e)}')
            return redirect('route_optimizer:import_locations')

    return render(request, 'route_optimizer/import_locations.html')

def add_vehicle(request):
    """Add new vehicle view."""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            vehicle_type = request.POST.get('vehicle_type')
            capacity = request.POST.get('capacity')
            fuel_efficiency = request.POST.get('fuel_efficiency')
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            
            if not all([name, vehicle_type, capacity, fuel_efficiency]):
                messages.error(request, 'Please fill all required fields')
                return redirect('add_vehicle')
            
            Vehicle.objects.create(
                name=name,
                vehicle_type=vehicle_type,
                capacity=capacity,
                fuel_efficiency=fuel_efficiency,
                current_latitude=latitude if latitude else None,
                current_longitude=longitude if longitude else None
            )
            
            messages.success(request, 'Vehicle added successfully!')
            return redirect('vehicles')
            
        except Exception as e:
            messages.error(request, f'Error adding vehicle: {str(e)}')
    
    context = {
        'vehicle_types': Vehicle._meta.get_field('vehicle_type').choices,
    }
    
    return render(request, 'route_optimizer/add_vehicle.html', context)


def performance_dashboard(request):
    """Performance dashboard with analytics and KPIs."""
    try:
        # Calculate key metrics
        total_routes = OptimizedRoute.objects.count()
        
        # Calculate total distance and average efficiency
        route_stats = OptimizedRoute.objects.aggregate(
            total_distance=Sum('total_distance'),
            avg_fuel_consumption=Avg('estimated_fuel_consumption')
        )
        
        total_distance = float(route_stats['total_distance'] or 0)
        avg_fuel_consumption = float(route_stats['avg_fuel_consumption'] or 0)
        
        # Calculate average efficiency based on optimization sessions
        optimization_sessions = RouteOptimizationSession.objects.aggregate(
            avg_efficiency=Avg('optimization_score')
        )
        avg_efficiency = float(optimization_sessions['avg_efficiency'] or 85)  # Default to 85%
        
        # Calculate fuel saved (estimated)
        fuel_saved = total_distance * 0.1  # Assuming 0.1L saved per km due to optimization
    except Exception as e:
        # Fallback values if there's an error
        total_routes = 0
        total_distance = 0.0
        avg_efficiency = 85.0
        fuel_saved = 0.0
    
    # Fleet status simulation
    vehicles = Vehicle.objects.all()
    fleet_status = []
    for vehicle in vehicles:
        status = ['active', 'maintenance', 'idle'][hash(vehicle.id) % 3]
        efficiency = 85 + (hash(vehicle.id) % 15)
        current_route = f"Route {hash(vehicle.id) % 10 + 1}" if status == 'active' else None
        
        fleet_status.append({
            'name': vehicle.name,
            'status': status,
            'current_route': current_route,
            'efficiency': efficiency
        })
    
    # If no vehicles exist, create sample data
    if not fleet_status:
        fleet_status = [
            {'name': 'Truck Alpha', 'status': 'active', 'current_route': 'Route 1', 'efficiency': 92},
            {'name': 'Van Beta', 'status': 'maintenance', 'current_route': None, 'efficiency': 88},
            {'name': 'Truck Gamma', 'status': 'idle', 'current_route': None, 'efficiency': 85}
        ]
    
    # Recent activities simulation
    recent_activities = [
        {
            'title': 'Route Optimization Completed',
            'description': 'Route "Morning Collection" optimized successfully',
            'timestamp': '2 minutes ago'
        },
        {
            'title': 'Vehicle Maintenance',
            'description': 'Truck Alpha scheduled for routine maintenance',
            'timestamp': '1 hour ago'
        },
        {
            'title': 'New Location Added',
            'description': 'Central Market Bin added to system',
            'timestamp': '3 hours ago'
        },
        {
            'title': 'Route Completed',
            'description': 'Evening Collection route completed successfully',
            'timestamp': '5 hours ago'
        },
        {
            'title': 'Weather Alert',
            'description': 'Heavy rain expected - routes may be delayed',
            'timestamp': '1 day ago'
        }
    ]
    
    context = {
        'total_routes': total_routes,
        'total_distance': total_distance,
        'avg_efficiency': avg_efficiency,
        'fuel_saved': fuel_saved,
        'fleet_status': fleet_status,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'route_optimizer/performance_dashboard.html', context)


def real_time_tracking(request):
    """Real-time vehicle tracking view using actual route optimization data."""
    import json
    from datetime import datetime, timedelta
    
    try:
        # Get active routes (using 'in_progress' status from the model)
        active_routes = OptimizedRoute.objects.filter(status='in_progress').select_related('vehicle').prefetch_related('routelocation_set__location')[:10]
        
        vehicle_positions = []
        for route in active_routes:
            # Get route locations in visit order
            route_locations = route.routelocation_set.all().order_by('visit_order')
            
            if not route_locations.exists():
                continue
            
            # Calculate progress based on time elapsed since route started
            # Use updated_at when status changed to 'in_progress' as start time
            # If route was just updated (status changed), use updated_at; otherwise use created_at
            route_start_time = route.updated_at if route.status == 'in_progress' else route.created_at
            elapsed_minutes = (timezone.now() - route_start_time).total_seconds() / 60
            
            # Calculate progress ratio (0.0 to 1.0)
            # Cap progress at 100% even if time exceeds duration
            if route.total_duration > 0:
                progress_ratio = min(1.0, max(0.0, elapsed_minutes / route.total_duration))
            else:
                progress_ratio = 0.0
            
            # Calculate which location segment the vehicle is in
            total_locations = route_locations.count()
            if total_locations == 0:
                continue
            
            # Calculate current segment (between two locations)
            current_segment = int(progress_ratio * (total_locations - 1)) if total_locations > 1 else 0
            current_segment = min(current_segment, total_locations - 2) if total_locations > 1 else 0
            
            # Get current and next location
            locations_list = list(route_locations)
            current_location_obj = locations_list[current_segment].location
            next_location_obj = locations_list[min(current_segment + 1, total_locations - 1)].location if total_locations > 1 else current_location_obj
            
            # Calculate position between current and next location
            segment_progress = (progress_ratio * (total_locations - 1)) - current_segment if total_locations > 1 else 0
            segment_progress = max(0, min(1, segment_progress))
            
            # Interpolate position between current and next location
            current_lat = float(current_location_obj.latitude)
            current_lng = float(current_location_obj.longitude)
            next_lat = float(next_location_obj.latitude)
            next_lng = float(next_location_obj.longitude)
            
            # Linear interpolation
            vehicle_lat = current_lat + (next_lat - current_lat) * segment_progress
            vehicle_lng = current_lng + (next_lng - current_lng) * segment_progress
            
            # Calculate remaining time
            remaining_minutes = max(0, int((1 - progress_ratio) * route.total_duration))
            estimated_completion = f"{remaining_minutes} min remaining" if remaining_minutes > 0 else "Completed"
            
            # Get current and next stop names
            current_location_name = current_location_obj.name
            next_location_name = next_location_obj.name if total_locations > 1 and current_segment < total_locations - 1 else "Route Complete"
            
            vehicle_positions.append({
                'route_id': route.id,
                'route_name': route.route_name,
                'vehicle': route.vehicle.name if route.vehicle else 'Unknown',
                'latitude': vehicle_lat,
                'longitude': vehicle_lng,
                'progress': int(progress_ratio * 100),
                'status': 'in_progress',
                'estimated_completion': estimated_completion,
                'current_location': current_location_name,
                'next_stop': next_location_name,
                'route_locations': [
                    {
                        'id': rl.location.id,
                        'name': rl.location.name,
                        'latitude': float(rl.location.latitude),
                        'longitude': float(rl.location.longitude),
                        'visit_order': rl.visit_order,
                        'location_type': rl.location.location_type
                    }
                    for rl in route_locations
                ]
            })
            
    except Exception as e:
        import traceback
        print(f"Error in real_time_tracking: {e}")
        traceback.print_exc()
        active_routes = []
        vehicle_positions = []
    
    # Use sample data if no active routes exist (for demo purposes)
    use_sample_data = len(vehicle_positions) == 0
    
    context = {
        'active_routes': active_routes,
        'vehicle_positions': vehicle_positions,  # Pass as list for template iteration
        'vehicle_positions_json': json.dumps(vehicle_positions),  # Pass as JSON string for JavaScript
        'use_sample_data': use_sample_data,
    }
    
    return render(request, 'route_optimizer/real_time_tracking.html', context)


def notifications(request):
    """Notifications and alerts management view backed by DB."""
    from django.utils.timesince import timesince
    from .models import Notification

    # Seed demo data once if empty
    if Notification.objects.count() == 0:
        demo = [
            dict(title='Route Optimization Completed', message='Route "Morning Collection" has been optimized successfully. 15% efficiency improvement achieved.', notification_type='success', is_read=False),
            dict(title='Vehicle Maintenance Due', message='Truck Alpha is due for routine maintenance in 2 days. Please schedule service.', notification_type='warning', is_read=False),
            dict(title='Weather Alert', message='Heavy rain expected tomorrow. Consider adjusting routes for safety.', notification_type='info', is_read=True),
            dict(title='Route Delay', message='Route "Evening Collection" is running 30 minutes behind schedule due to traffic.', notification_type='danger', is_read=True),
            dict(title='New Location Added', message='Central Market Bin has been successfully added to the system.', notification_type='success', is_read=True),
        ]
        Notification.objects.bulk_create([Notification(**d) for d in demo])

    # Order: unread first, then by created_at descending
    qs = Notification.objects.all().order_by('is_read', '-created_at')

    # Precompute counts by type and unread
    total_count = qs.count()
    unread_count = qs.filter(is_read=False).count()
    type_counts = {
        'success': qs.filter(notification_type='success').count(),
        'warning': qs.filter(notification_type='warning').count(),
        'danger': qs.filter(notification_type='danger').count(),
        'info': qs.filter(notification_type='info').count(),
    }

    # Filter by type if requested
    notification_type = request.GET.get('type', '')
    if notification_type:
        qs = qs.filter(notification_type=notification_type).order_by('is_read', '-created_at')

    notifications_data = [
        {
            'id': n.id,
            'type': n.notification_type,
            'title': n.title,
            'message': n.message,
            'timestamp': (timesince(n.created_at) + ' ago') if n.created_at else '',
            'read': n.is_read,
        }
        for n in qs
    ]

    context = {
        'notifications': notifications_data,
        'unread_count': unread_count,
        'total_count': total_count,
        'type_counts': type_counts,
    }

    return render(request, 'route_optimizer/notifications.html', context)


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_POST
def api_notification_mark_read(request, notification_id: int):
    from .models import Notification
    try:
        n = Notification.objects.get(id=notification_id)
        n.is_read = True
        n.save(update_fields=['is_read', 'updated_at'])
        return JsonResponse({'ok': True})
    except Notification.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'not_found'}, status=404)


@csrf_exempt
@require_POST
def api_notification_mark_all_read(request):
    from .models import Notification
    Notification.objects.filter(is_read=False).update(is_read=True)
    return JsonResponse({'ok': True})


@csrf_exempt
@require_POST
def api_notification_mark_unread(request, notification_id: int):
    from .models import Notification
    try:
        n = Notification.objects.get(id=notification_id)
        n.is_read = False
        n.save(update_fields=['is_read', 'updated_at'])
        return JsonResponse({'ok': True})
    except Notification.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'not_found'}, status=404)


@csrf_exempt
@require_POST
def api_notification_clear_all(request):
    from .models import Notification
    Notification.objects.all().delete()
    return JsonResponse({'ok': True})

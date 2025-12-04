"""
Route optimization engine using Google OR-Tools.
"""
import time
import math
from typing import List, Dict, Tuple, Optional
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from geopy.distance import geodesic
from .models import Location, Vehicle, OptimizedRoute, RouteLocation
from django.utils import timezone
from .models import RouteOptimizationSession


class RouteOptimizer:
    """
    Main route optimization engine using Google OR-Tools.
    """
    
    def __init__(self):
        self.manager = None
        self.routing = None
        self.solution = None
        
    def calculate_distance_matrix(self, locations: List[Location], depot_index: int = 0) -> List[List[int]]:
        """
        Calculate distance matrix between all locations.
        Returns matrix in meters.
        """
        n = len(locations)
        distance_matrix = [[0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Calculate distance using geopy
                    coord1 = (float(locations[i].latitude), float(locations[i].longitude))
                    coord2 = (float(locations[j].latitude), float(locations[j].longitude))
                    distance = geodesic(coord1, coord2).meters
                    distance_matrix[i][j] = int(distance)
                else:
                    distance_matrix[i][j] = 0
                    
        return distance_matrix
    
    def calculate_time_matrix(self, distance_matrix: List[List[int]], 
                            avg_speed_kmh: float = 30) -> List[List[int]]:
        """
        Calculate time matrix based on distance matrix.
        Returns time in minutes.
        """
        n = len(distance_matrix)
        time_matrix = [[0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Convert distance from meters to km, then calculate time
                    distance_km = distance_matrix[i][j] / 1000
                    time_hours = distance_km / avg_speed_kmh
                    time_minutes = int(time_hours * 60)
                    time_matrix[i][j] = time_minutes
                else:
                    time_matrix[i][j] = 0
                    
        return time_matrix
    
    def optimize_route(self, 
                      locations: List[Location],
                      vehicle: Vehicle,
                      depot_index: int = 0,
                      max_time_per_route: int = 24 * 60,  # minutes
                      time_windows: Optional[List[Tuple[int, int]]] = None,
                      solve_seconds: int = 5) -> Dict:
        """
        Optimize route using Google OR-Tools.
        
        Args:
            locations: List of locations to visit
            vehicle: Vehicle to use for the route
            depot_index: Index of depot/starting location
            max_time_per_route: Maximum time per route in minutes
            time_windows: Optional time windows for locations [(start_time, end_time), ...]
        
        Returns:
            Dictionary containing optimization results
        """
        start_time = time.time()
        
        # Calculate matrices
        distance_matrix = self.calculate_distance_matrix(locations, depot_index)
        time_matrix = self.calculate_time_matrix(distance_matrix)
        
        # Create routing model
        self.manager = pywrapcp.RoutingIndexManager(
            len(locations), 1, depot_index
        )
        self.routing = pywrapcp.RoutingModel(self.manager)
        
        # Define cost function (distance)
        def distance_callback(from_index, to_index):
            from_node = self.manager.IndexToNode(from_index)
            to_node = self.manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]
        
        transit_callback_index = self.routing.RegisterTransitCallback(distance_callback)
        self.routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Add time dimension
        time_callback_index = self.routing.RegisterTransitCallback(
            lambda from_index, to_index: time_matrix[
                self.manager.IndexToNode(from_index)
            ][self.manager.IndexToNode(to_index)]
        )
        
        self.routing.AddDimension(
            time_callback_index,
            max_time_per_route,  # Maximum time per route
            max_time_per_route,  # Maximum time per route
            False,  # Don't start cumul to zero
            "Time"
        )
        
        time_dimension = self.routing.GetDimensionOrDie("Time")
        
        # Add time window constraints if provided
        if time_windows:
            for location_idx, (start_time, end_time) in enumerate(time_windows):
                if location_idx != depot_index:
                    index = self.manager.NodeToIndex(location_idx)
                    time_dimension.CumulVar(index).SetRange(start_time, end_time)
        
        # Add capacity constraint
        def demand_callback(from_index):
            from_node = self.manager.IndexToNode(from_index)
            return int(locations[from_node].estimated_waste_volume)
        
        demand_callback_index = self.routing.RegisterUnaryTransitCallback(demand_callback)
        self.routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # Null capacity slack
            [int(vehicle.capacity)],  # Vehicle maximum capacities
            True,  # Start cumul to zero
            "Capacity"
        )
        
        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = max(1, int(solve_seconds))
        
        # Solve the problem
        self.solution = self.routing.SolveWithParameters(search_parameters)
        
        # Process results
        execution_time = time.time() - start_time
        
        if self.solution:
            return self._process_solution(
                locations, vehicle, depot_index, 
                distance_matrix, time_matrix, execution_time
            )
        else:
            return {
                'success': False,
                'error': 'No solution found',
                'execution_time': execution_time
            }
    
    def _process_solution(self, locations: List[Location], vehicle: Vehicle,
                         depot_index: int, distance_matrix: List[List[int]],
                         time_matrix: List[List[int]], execution_time: float) -> Dict:
        """
        Process the optimization solution and return structured results.
        """
        route_locations = []
        route_path_coords = []  # list of (lat, lng)
        route_segments = []  # list of per-segment dicts
        total_distance = 0
        total_time = 0
        total_waste_volume = 0
        
        # Build route by walking successor variables (single vehicle: 0)
        index = self.routing.Start(0)
        current_node = self.manager.IndexToNode(index)
        visit_order = 0
        if locations:
            route_path_coords.append((float(locations[current_node].latitude), float(locations[current_node].longitude)))
        while not self.routing.IsEnd(index):
            next_index = self.solution.Value(self.routing.NextVar(index))
            next_node = self.manager.IndexToNode(next_index)
            if self.routing.IsEnd(next_index):
                break

            # Calculate distance and time to next node
            distance = distance_matrix[current_node][next_node]
            travel_time = time_matrix[current_node][next_node]

            total_distance += distance
            total_time += travel_time
            total_waste_volume += float(locations[next_node].estimated_waste_volume)

            route_location = {
                'location': locations[next_node],
                'visit_order': visit_order,
                'distance_from_previous': distance,
                'travel_time_from_previous': travel_time,
                'estimated_waste_collected': locations[next_node].estimated_waste_volume,
                'cumulative_distance': total_distance,
                'cumulative_time': total_time
            }
            route_locations.append(route_location)

            route_path_coords.append((float(locations[next_node].latitude), float(locations[next_node].longitude)))
            route_segments.append({
                'from_index': current_node,
                'to_index': next_node,
                'from_name': locations[current_node].name,
                'to_name': locations[next_node].name,
                'distance_m': distance,
                'time_min': travel_time
            })

            current_node = next_node
            index = next_index
            visit_order += 1
        
        # Calculate fuel consumption (assuming 0.1 L/km for trucks)
        fuel_consumption = (total_distance / 1000) * 0.1  # Convert to km and calculate fuel
        
        return {
            'success': True,
            'route_locations': route_locations,
            'route_path_coords': route_path_coords,
            'route_segments': route_segments,
            'total_distance': total_distance / 1000,  # Convert to km
            'total_time': total_time,
            'total_waste_volume': total_waste_volume,
            'estimated_fuel_consumption': fuel_consumption,
            'execution_time': execution_time,
            'optimization_score': self._calculate_optimization_score(route_locations)
        }
    
    def _calculate_optimization_score(self, route_locations: List[Dict]) -> float:
        """
        Calculate optimization quality score (0-100).
        Higher score means better optimization.
        """
        if not route_locations:
            return 0.0
        
        # Calculate various metrics
        total_locations = len(route_locations)
        total_distance = sum(loc['distance_from_previous'] for loc in route_locations)
        
        # Score based on number of locations visited efficiently
        efficiency_score = min(100, (total_locations / max(1, total_distance / 1000)) * 10)
        
        # Score based on route balance (avoiding very long segments)
        max_segment = max(loc['distance_from_previous'] for loc in route_locations)
        avg_segment = total_distance / total_locations
        balance_score = max(0, 100 - ((max_segment - avg_segment) / avg_segment) * 50)
        
        # Combined score
        final_score = (efficiency_score + balance_score) / 2
        return round(final_score, 2)


class RouteOptimizationService:
    """
    Service class for managing route optimization operations.
    """
    
    def __init__(self):
        self.optimizer = RouteOptimizer()
    
    def create_optimized_route(self, 
                              location_ids: List[int],
                              vehicle_id: int,
                              route_name: str,
                              depot_location_id: Optional[int] = None) -> Dict:
        """
        Create an optimized route and save it to the database.
        """
        try:
            # Get locations and vehicle
            locations = list(Location.objects.filter(id__in=location_ids, is_active=True))
            vehicle = Vehicle.objects.get(id=vehicle_id, is_available=True)
            
            if not locations:
                return {'success': False, 'error': 'No valid locations provided'}
            
            if not vehicle:
                return {'success': False, 'error': 'Vehicle not found or unavailable'}
            
            # Determine depot index and optionally add a virtual depot so all provided
            # locations are treated as stops and appear in the final route.
            depot_index = 0
            locations_for_optimization = locations
            if depot_location_id:
                try:
                    depot_obj = next(loc for loc in locations if loc.id == depot_location_id)
                    non_depot_locations = [loc for loc in locations if loc.id != depot_location_id]
                    locations_for_optimization = [depot_obj] + non_depot_locations
                    depot_index = 0
                except StopIteration:
                    depot_index = 0
            else:
                # No explicit depot: add a virtual start so every provided location is a visit
                class _Depot:
                    pass
                virtual_depot = _Depot()
                first = locations[0]
                virtual_depot.latitude = float(first.latitude)
                virtual_depot.longitude = float(first.longitude)
                virtual_depot.estimated_waste_volume = 0
                virtual_depot.name = "Start"
                locations_for_optimization = [virtual_depot] + locations
                depot_index = 0
            
            # Optimize route
            # Give more time for the final solve
            # Final solve with longer time; also relax capacity if needed
            # If total estimated waste exceeds capacity, temporarily scale capacity to allow a route
            try:
                total_estimated = sum(float(l.estimated_waste_volume) for l in locations)
                vehicle_capacity = float(getattr(vehicle, 'capacity', 0) or 0)
                solve_cap_vehicle = vehicle
                if vehicle_capacity and total_estimated > vehicle_capacity:
                    class _V: pass
                    solve_cap_vehicle = _V()
                    solve_cap_vehicle.capacity = max(total_estimated, vehicle_capacity)
                result = self.optimizer.optimize_route(
                    locations_for_optimization,
                    solve_cap_vehicle,
                    depot_index,
                    max_time_per_route=24*60,
                    solve_seconds=20
                )
            except Exception:
                result = self.optimizer.optimize_route(
                    locations_for_optimization,
                    vehicle,
                    depot_index,
                    max_time_per_route=24*60,
                    solve_seconds=20
                )
            
            if not result['success']:
                return result
            
            # Save optimized route to database
            optimized_route = OptimizedRoute.objects.create(
                route_name=route_name,
                vehicle=vehicle,
                total_distance=result['total_distance'],
                total_duration=result['total_time'],
                estimated_fuel_consumption=result['estimated_fuel_consumption'],
                total_waste_volume=result['total_waste_volume']
            )
            
            # Create route location entries
            for route_loc_data in result['route_locations']:
                RouteLocation.objects.create(
                    route=optimized_route,
                    location=route_loc_data['location'],
                    visit_order=route_loc_data['visit_order'],
                    estimated_arrival_time=timezone.now().time(),  # Placeholder
                    estimated_departure_time=timezone.now().time(),  # Placeholder
                    estimated_waste_collected=route_loc_data['estimated_waste_collected']
                )
            
            # Save optimization session
            RouteOptimizationSession.objects.create(
                session_name=f"Route optimization for {route_name}",
                algorithm_used="Google OR-Tools VRP",
                parameters={
                    'locations_count': len(locations),
                    'vehicle_id': vehicle_id,
                    'depot_index': depot_index
                },
                execution_time=result['execution_time'],
                optimization_score=result['optimization_score']
            )
            
            result['route_id'] = optimized_route.id
            result['route_name'] = route_name
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_route_statistics(self, route_id: int) -> Dict:
        """
        Get detailed statistics for a specific route.
        """
        try:
            route = OptimizedRoute.objects.get(id=route_id)
            route_locations = RouteLocation.objects.filter(route=route).order_by('visit_order')
            
            stats = {
                'route_name': route.route_name,
                'vehicle': route.vehicle.name,
                'total_distance': float(route.total_distance),
                'total_duration': route.total_duration,
                'estimated_fuel_consumption': float(route.estimated_fuel_consumption),
                'total_waste_volume': float(route.total_waste_volume),
                'status': route.status,
                'locations_count': route_locations.count(),
                'route_details': [],
                'route_path_coords': []
            }
            
            for route_loc in route_locations:
                stats['route_details'].append({
                    'location_name': route_loc.location.name,
                    'visit_order': route_loc.visit_order,
                    'address': route_loc.location.address,
                    'waste_volume': float(route_loc.estimated_waste_collected),
                    'priority': route_loc.location.priority
                })
                # Build path coordinates for map preview
                try:
                    lat = float(route_loc.location.latitude)
                    lng = float(route_loc.location.longitude)
                    stats['route_path_coords'].append([lat, lng])
                except Exception:
                    pass
            
            return {'success': True, 'data': stats}
            
        except OptimizedRoute.DoesNotExist:
            return {'success': False, 'error': 'Route not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_optimization_history(self) -> Dict:
        """
        Get optimization session history.
        """
        try:
            sessions = RouteOptimizationSession.objects.all()[:20]  # Last 20 sessions
            
            history = []
            for session in sessions:
                history.append({
                    'session_name': session.session_name,
                    'algorithm_used': session.algorithm_used,
                    'execution_time': float(session.execution_time),
                    'optimization_score': float(session.optimization_score),
                    'created_at': session.created_at.isoformat(),
                    'parameters': session.parameters
                })
            
            return {'success': True, 'data': history}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

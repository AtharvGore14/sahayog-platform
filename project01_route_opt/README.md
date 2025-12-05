# Sahayog Route Optimizer

A focused route optimization system for waste management collection routes using Google OR-Tools and Django.

## Features

- **Route Optimization**: Uses Google OR-Tools to solve the Vehicle Routing Problem (VRP)
- **Interactive Web Interface**: Modern, responsive web interface for route planning
- **Location Management**: Add and manage collection points, bins, and depots
- **Vehicle Management**: Track collection vehicles with capacity and efficiency data
- **Real-time Optimization**: Instant route optimization with distance and time calculations
- **Visual Results**: Interactive maps and detailed route statistics

## Technology Stack

- **Backend**: Django 4.2.7
- **Optimization Engine**: Google OR-Tools
- **Distance Calculation**: Geopy for geographic calculations
- **Frontend**: Bootstrap 5, jQuery, Leaflet Maps
- **Database**: SQLite (can be upgraded to PostgreSQL)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sahayog
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements_simple.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Main application: http://localhost:8000/route-optimizer/
   - Admin panel: http://localhost:8000/admin/

## Usage

### 1. Add Locations

1. Navigate to "Add Location" from the sidebar
2. Fill in location details:
   - Name and address
   - Latitude and longitude coordinates
   - Location type (bin, collection point, depot, landfill)
   - Priority level
   - Estimated waste volume

### 2. Add Vehicles

1. Navigate to "Add Vehicle" from the sidebar
2. Fill in vehicle details:
   - Name and type
   - Capacity in liters
   - Fuel efficiency (km/L)
   - Current location coordinates (optional)

### 3. Optimize Routes

1. Navigate to "Optimize Route"
2. Select locations to visit
3. Choose a vehicle
4. Enter route name
5. Optionally select a starting point (depot)
6. Click "Optimize Route"

### 4. View Results

- **Dashboard**: Overview of all routes and statistics
- **Route Details**: Detailed view of optimized routes with visit order
- **Optimization History**: Track all optimization sessions and performance

## API Endpoints

The system provides REST API endpoints for integration:

- `GET /route-optimizer/api/locations/` - Get all locations
- `GET /route-optimizer/api/vehicles/` - Get all vehicles
- `GET /route-optimizer/api/route/{id}/stats/` - Get route statistics
- `GET /route-optimizer/api/history/` - Get optimization history

## Optimization Algorithm

The route optimizer uses Google OR-Tools to solve the Vehicle Routing Problem with the following constraints:

- **Distance Minimization**: Find the shortest total route distance
- **Time Constraints**: Respect maximum route duration limits
- **Capacity Constraints**: Ensure vehicle capacity is not exceeded
- **Visit Order**: Optimize the sequence of location visits

### Algorithm Features

- **Guided Local Search**: Advanced local search with guided exploration
- **Time Limits**: Configurable optimization time limits (default: 30 seconds)
- **Multiple Constraints**: Handles distance, time, and capacity simultaneously
- **Quality Scoring**: Provides optimization quality scores (0-100%)

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Database Configuration

By default, the system uses SQLite. To upgrade to PostgreSQL:

1. Install PostgreSQL and psycopg2
2. Update `DATABASES` in `sahayog/settings.py`
3. Run migrations

## Customization

### Adding New Location Types

1. Update `LOCATION_TYPE_CHOICES` in `route_optimizer/models.py`
2. Run migrations
3. Update admin interface if needed

### Adding New Vehicle Types

1. Update `VEHICLE_TYPE_CHOICES` in `route_optimizer/models.py`
2. Run migrations
3. Update admin interface if needed

### Custom Optimization Parameters

Modify the optimization parameters in `route_optimizer/optimization_engine.py`:

- Time limits
- Search strategies
- Constraint weights
- Optimization objectives

## Performance Considerations

- **Large Datasets**: For routes with 100+ locations, consider increasing time limits
- **Real-time Optimization**: The system is designed for interactive use with sub-minute response times
- **Memory Usage**: Each optimization session creates temporary matrices in memory

## Troubleshooting

### Common Issues

1. **Optimization Fails**
   - Check that locations have valid coordinates
   - Ensure vehicle capacity is sufficient for selected locations
   - Verify that at least 2 locations are selected

2. **Map Not Loading**
   - Check internet connection (Leaflet requires external tile servers)
   - Verify that coordinates are within valid ranges (-90 to 90 for latitude, -180 to 180 for longitude)

3. **Database Errors**
   - Run `python manage.py migrate` to ensure database schema is up to date
   - Check that all required fields are provided when creating objects

### Debug Mode

Enable debug mode in settings to see detailed error messages:

```python
DEBUG = True
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation and troubleshooting sections

## Roadmap

- [ ] Multi-vehicle route optimization
- [ ] Time window constraints
- [ ] Real-time traffic integration
- [ ] Mobile app support
- [ ] Advanced analytics dashboard
- [ ] Integration with GPS tracking systems

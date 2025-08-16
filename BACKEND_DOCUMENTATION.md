# Weather247 Backend - Detailed Documentation

## 🏗️ Backend Architecture Overview

The Weather247 backend is built using Django 4.2.10 with Django REST Framework, providing a robust, scalable foundation for weather data management, user authentication, and advanced weather services.

## 📁 Directory Structure

```
backend/
├── weather247_backend/          # Django project core
├── weather_data/               # Core weather application
├── accounts/                   # User management system
├── route_planner/             # Route planning with weather
├── templates/                  # Admin templates
├── requirements.txt            # Python dependencies
├── manage.py                   # Django management script
├── Dockerfile                  # Container configuration
└── start_celery.py            # Celery worker startup
```

## 🔧 Core Configuration

### `weather247_backend/` - Django Project Core

#### `settings.py`
**Purpose**: Main Django configuration file with environment-based settings

**Key Configurations**:
- **Database**: SQLite for development, PostgreSQL for production
- **Cache**: Redis configuration with fallback options
- **Installed Apps**: Custom apps + Django built-ins
- **Middleware**: Performance monitoring, CORS, compression
- **Authentication**: DRF token authentication
- **CORS**: Cross-origin resource sharing configuration

**Environment Variables**:
```python
SECRET_KEY = config('SECRET_KEY', default='django-insecure-...')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')
OPENWEATHERMAP_API_KEY = config('OPENWEATHERMAP_API_KEY', default='demo-key')
```

#### `urls.py`
**Purpose**: Root URL configuration and API routing

**URL Patterns**:
```python
urlpatterns = [
    path('admin/', admin_site.urls),           # Custom admin site
    path('django-admin/', admin.site.urls),    # Default admin backup
    path('api/auth/', include('accounts.urls')),
    path('api/weather/', include('weather_data.urls')),
    path('api/routes/', include('route_planner.urls')),
]
```

#### `wsgi.py` & `asgi.py`
**Purpose**: Application entry points for WSGI and ASGI servers

## 🌤️ Weather Data Application (`weather_data/`)

### Core Models (`models.py`)

#### `City` Model
**Purpose**: Geographic and timezone information for weather data

**Fields**:
- `name`: City name (max 100 chars)
- `country`: Country code/name (max 100 chars)
- `latitude` & `longitude`: Geographic coordinates
- `timezone`: Timezone information (default UTC)
- `is_active`: City status flag
- `created_at` & `updated_at`: Timestamps

**Features**:
- Unique constraint on name + country
- Geographic coordinate validation
- Active city filtering

#### `WeatherData` Model
**Purpose**: Current weather data storage

**Fields**:
- `city`: Foreign key to City model
- `temperature`: Current temperature in Celsius
- `feels_like`: Apparent temperature
- `humidity`: Humidity percentage
- `pressure`: Atmospheric pressure in hPa
- `wind_speed` & `wind_direction`: Wind information
- `weather_condition` & `description`: Weather state
- `data_source`: API source identifier
- `timestamp`: Data collection time

**Features**:
- Automatic timestamp management
- Data source tracking
- Recent data filtering (30-minute freshness)

#### `AirQualityData` Model
**Purpose**: Air quality and pollutant measurements

**Fields**:
- `city`: Foreign key to City model
- `aqi`: Air Quality Index
- `co`, `no`, `no2`: Carbon and nitrogen compounds
- `o3`: Ozone levels
- `so2`: Sulphur dioxide
- `pm2_5`, `pm10`: Particulate matter
- `nh3`: Ammonia levels

**Features**:
- Comprehensive pollutant tracking
- AQI calculation and categorization
- Health impact assessment

#### `WeatherForecast` Model
**Purpose**: Multi-day weather predictions

**Fields**:
- `city`: Foreign key to City model
- `forecast_date`: Prediction date
- `temperature_min/max/avg`: Temperature ranges
- `precipitation_probability`: Rain/snow chance
- `precipitation_amount`: Expected precipitation
- `weather_condition`: Predicted weather state

**Features**:
- 5-day forecast support
- Precipitation probability modeling
- Temperature range predictions

#### `HistoricalWeatherData` Model
**Purpose**: Long-term weather trend analysis

**Fields**:
- `city`: Foreign key to City model
- `date`: Historical date
- `temperature_min/max/avg`: Daily temperature ranges
- `humidity_avg`: Average humidity
- `precipitation_total`: Daily precipitation

**Features**:
- 5-year historical data
- Trend analysis support
- Seasonal pattern recognition

#### `WeatherPrediction` Model
**Purpose**: AI-generated weather forecasts

**Fields**:
- `city`: Foreign key to City model
- `prediction_date`: Forecast date
- `predicted_temperature`: AI temperature prediction
- `confidence_score`: Prediction reliability (0-1)
- `model_version`: AI model version
- `features_used`: ML feature information

**Features**:
- Machine learning predictions
- Confidence scoring
- Model version tracking

#### `UserWeatherPreference` Model
**Purpose**: Personalized user weather settings

**Fields**:
- `user`: Foreign key to User model
- `city`: Favorite city
- `is_favorite`: Favorite city flag
- `alert_enabled`: Weather alert preferences
- `order`: Display order preference

**Features**:
- User customization
- Alert preferences
- Display ordering

#### `PushSubscription` Model
**Purpose**: Web push notification management

**Fields**:
- `user`: Foreign key to User model
- `endpoint`: Push service endpoint
- `p256dh_key` & `auth_key`: Encryption keys
- `notification_preferences`: Alert type preferences
- `is_active`: Subscription status

**Features**:
- Web push notifications
- User preference management
- Subscription lifecycle management

### API Views (`views.py`)

#### City Management Views
- **`CityListCreateView`**: List all cities or create new ones
- **`CityDetailView`**: Retrieve, update, or delete cities

#### Weather Data Views
- **`get_current_weather`**: Current weather for specific city
- **`get_weather_by_city_name`**: Weather lookup by city name
- **`get_forecast`**: Multi-day weather forecast
- **`get_air_quality`**: Air quality data retrieval
- **`get_historical_data`**: Historical weather trends
- **`get_ai_predictions`**: AI weather predictions

#### Analytics Views
- **`get_weather_analytics`**: Weather trend analysis
- **`get_city_comparison`**: Multi-city weather comparison
- **`get_weather_alerts`**: Weather alert management

### Weather Service (`real_weather_service.py`)

#### `OpenWeatherMapService` Class
**Purpose**: Primary weather API integration

**Methods**:
- `get_coordinates()`: City geocoding
- `get_current_weather()`: Current weather data
- `get_forecast()`: Weather predictions
- `get_air_quality()`: Air quality data
- `_get_demo_weather()`: Demo data fallback

**Features**:
- API key management
- Request caching
- Error handling
- Demo mode support

#### `WeatherManager` Class
**Purpose**: Main weather service orchestrator

**Methods**:
- `get_current_weather_with_fallback()`: Primary with fallback
- `get_comprehensive_weather()`: Full weather data
- `update_weather_for_all_cities()`: Bulk updates

**Features**:
- Service fallback strategies
- Retry logic with exponential backoff
- Cache management
- Error recovery

### Cache Management (`cache_manager.py`)

#### `WeatherCacheManager` Class
**Purpose**: Redis-based weather data caching

**Methods**:
- `get_cache()`: Retrieve cached data
- `set_cache()`: Store data in cache
- `invalidate_cache()`: Remove cached data
- `get_weather_cache_key()`: Generate cache keys

**Features**:
- TTL-based expiration
- Automatic invalidation
- Cache key generation
- Performance monitoring

### Data Validation (`validators.py`)

#### `WeatherDataValidator` Class
**Purpose**: Weather data validation

**Validation Rules**:
- Temperature range validation
- Humidity percentage validation
- Pressure range validation
- Wind speed validation
- Coordinate validation

#### `CityValidator` Class
**Purpose**: City data validation

**Validation Rules**:
- Name format validation
- Country code validation
- Coordinate range validation
- Timezone validation

### Admin Interface (`admin.py`)

#### Custom Admin Site
**Features**:
- Enhanced city management
- Weather data monitoring
- User preference management
- System health dashboard

## 👥 User Management (`accounts/`)

### Extended User Model (`models.py`)

#### `User` Model (Custom)
**Extensions**:
- `phone_number`: Contact information
- `is_verified`: Account verification status
- `last_activity`: User activity tracking
- `login_count`: Authentication tracking
- `preferred_units`: Measurement preferences
- `timezone`: User timezone
- `language`: Language preference
- `api_requests_count`: API usage tracking
- `api_rate_limit`: Rate limiting configuration

#### `UserProfile` Model
**Purpose**: Extended user profile information

**Fields**:
- `user`: One-to-one relationship with User
- `bio`: User biography
- `location`: User location
- `preferences`: JSON field for custom preferences
- `notification_settings`: Alert preferences

#### `UserRole` Model
**Purpose**: Role-based access control

**Fields**:
- `name`: Role name
- `permissions`: Many-to-many with permissions
- `description`: Role description
- `is_active`: Role status

#### `UserActivity` Model
**Purpose**: User activity tracking

**Fields**:
- `user`: Foreign key to User
- `activity_type`: Type of activity
- `description`: Activity description
- `metadata`: Additional activity data
- `timestamp`: Activity time

#### `UserSession` Model
**Purpose**: User session management

**Fields**:
- `user`: Foreign key to User
- `session_key`: Django session key
- `ip_address`: User IP address
- `user_agent`: Browser information
- `created_at` & `expires_at`: Session timing

### Authentication Views (`views.py`)

#### User Registration
- **`register`**: User account creation
- **`login_view`**: User authentication
- **`logout_view`**: User logout
- **`change_password`**: Password updates

#### User Management
- **`UserProfileView`**: Profile management
- **`UserDetailView`**: User information
- **`user_preferences`**: Preference management
- **`user_dashboard_data`**: Dashboard data

#### Admin Functions
- **`admin_users_list`**: User administration
- **`admin_user_detail`**: User details
- **`admin_bulk_user_operations`**: Bulk operations
- **`admin_user_analytics`**: User analytics

### User Serializers (`serializers.py`)

#### `UserRegistrationSerializer`
**Purpose**: User registration data validation

**Fields**:
- `username`: Unique username
- `email`: Valid email address
- `password`: Secure password
- `password_confirm`: Password confirmation

#### `UserLoginSerializer`
**Purpose**: Login data validation

**Fields**:
- `email`: User email
- `password`: User password

#### `UserSerializer`
**Purpose**: User data serialization

**Features**:
- Profile data inclusion
- Permission summary
- Read-only field protection

## 🗺️ Route Planning (`route_planner/`)

### Route Models (`models.py`)

#### `Route` Model
**Purpose**: Route definition and metadata

**Fields**:
- `user`: Route owner
- `name`: Route name
- `start_location` & `end_location`: Route endpoints
- `waypoints`: Intermediate points
- `total_distance`: Route length
- `estimated_duration`: Travel time
- `created_at` & `updated_at`: Timestamps

#### `RouteWeatherPoint` Model
**Purpose**: Weather data along routes

**Fields**:
- `route`: Foreign key to Route
- `location`: Geographic point
- `weather_data`: Associated weather
- `timestamp`: Weather time

#### `RouteAlert` Model
**Purpose**: Weather alerts for routes

**Fields**:
- `route`: Foreign key to Route
- `alert_type`: Alert category
- `severity`: Alert level
- `description`: Alert details
- `is_active`: Alert status

#### `TravelPlan` Model
**Purpose**: Comprehensive travel planning

**Fields**:
- `user`: Plan owner
- `route`: Associated route
- `departure_time`: Travel start
- `weather_conditions`: Expected weather
- `hazard_score`: Risk assessment
- `recommendations`: Travel advice

### Route Views (`views.py`)

#### Route Management
- **`RouteListCreateView`**: Route CRUD operations
- **`RouteDetailView`**: Route details
- **`create_route_with_weather`**: Weather-integrated routes

#### Weather Integration
- **`get_route_weather`**: Weather along routes
- **`calculate_hazard_score`**: Risk assessment
- **`generate_travel_recommendations`**: Travel advice

### Route Serializers (`serializers.py`)

#### `RouteSerializer`
**Purpose**: Route data serialization

**Features**:
- Weather data inclusion
- Hazard scoring
- User permission validation

## 🚀 Performance & Monitoring

### Middleware (`weather_data/middleware/`)

#### `PerformanceMonitoringMiddleware`
**Purpose**: Request performance tracking

**Features**:
- Response time monitoring
- Database query counting
- Memory usage tracking
- Performance metrics logging

#### `CacheControlMiddleware`
**Purpose**: HTTP cache control

**Features**:
- Cache header management
- ETag generation
- Conditional requests
- Cache optimization

#### `ResponseCompressionMiddleware`
**Purpose**: Response compression

**Features**:
- Gzip compression
- Content type detection
- Compression level optimization

#### `DatabaseQueryOptimizationMiddleware`
**Purpose**: Database optimization

**Features**:
- Query analysis
- N+1 query detection
- Database connection management
- Query optimization suggestions

### System Monitoring (`weather_data/system_monitoring/`)

#### `SystemHealthMonitor`
**Purpose**: System health tracking

**Features**:
- Service availability monitoring
- Resource usage tracking
- Error rate monitoring
- Performance alerts

#### `WeatherAPIMonitor`
**Purpose**: External API monitoring

**Features**:
- API response time tracking
- Error rate monitoring
- Rate limit tracking
- Service health alerts

## 🔒 Security Features

### Authentication & Authorization
- **Token-based Authentication**: DRF token authentication
- **Role-based Access Control**: User role management
- **Permission System**: Granular permission control
- **Session Management**: Secure session handling

### Data Validation
- **Input Sanitization**: XSS prevention
- **SQL Injection Protection**: Parameterized queries
- **CSRF Protection**: Cross-site request forgery prevention
- **Rate Limiting**: API abuse prevention

### Security Headers
- **CORS Configuration**: Cross-origin resource sharing
- **Security Headers**: XSS, clickjacking protection
- **HTTPS Enforcement**: Secure communication
- **Content Security Policy**: Resource loading control

## 📊 Database Design

### Database Schema
- **Normalized Design**: Efficient data storage
- **Indexing Strategy**: Query performance optimization
- **Foreign Key Relationships**: Data integrity
- **Transaction Management**: ACID compliance

### Database Operations
- **ORM Usage**: Django ORM for database operations
- **Query Optimization**: Efficient database queries
- **Connection Pooling**: Database connection management
- **Migration Management**: Schema evolution

## 🧪 Testing Strategy

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Performance Tests**: Load and stress testing
- **Security Tests**: Vulnerability assessment

### Test Files
- **`test_api.py`**: API endpoint testing
- **`test_auth.py`**: Authentication testing
- **`test_caching.py`**: Cache system testing
- **`test_validation.py`**: Data validation testing
- **`test_weather_manager.py`**: Weather service testing

## 🚀 Deployment & DevOps

### Docker Configuration
- **`Dockerfile`**: Container image definition
- **`docker-compose.yml`**: Multi-service orchestration
- **Environment Configuration**: Container environment setup

### Background Services
- **Celery Worker**: Asynchronous task processing
- **Celery Beat**: Scheduled task management
- **Redis**: Cache and message broker
- **Flower**: Celery monitoring interface

### Environment Management
- **Environment Variables**: Configuration management
- **Settings Override**: Environment-specific settings
- **Secret Management**: Secure credential handling

## 📈 Performance Optimization

### Caching Strategy
- **Redis Caching**: High-performance data storage
- **Cache Invalidation**: Automatic cache management
- **Cache Warming**: Proactive data loading
- **Cache Statistics**: Performance monitoring

### Database Optimization
- **Query Optimization**: Efficient database queries
- **Indexing Strategy**: Fast data retrieval
- **Connection Pooling**: Resource management
- **Query Analysis**: Performance monitoring

### API Optimization
- **Response Compression**: Reduced bandwidth usage
- **Pagination**: Large dataset handling
- **Field Selection**: Optimized data transfer
- **Rate Limiting**: Resource protection

---

*This documentation provides a comprehensive overview of the Weather247 backend architecture, components, and implementation details. For specific implementation questions, refer to the individual module documentation or source code.*
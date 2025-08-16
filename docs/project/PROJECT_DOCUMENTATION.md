# Weather247 - Comprehensive Project Documentation

## 🚀 Project Overview

Weather247 is a sophisticated, AI-powered weather application that provides real-time, historical, and predictive weather insights through an interactive web platform. Built with modern technologies and best practices, it offers enterprise-grade weather services with advanced features like route planning, weather alerts, and machine learning predictions.

## 🎯 Key Features

### Core Weather Services
- **Real-time Weather Data**: Current weather conditions for multiple cities
- **Weather Comparison**: Side-by-side comparison across cities
- **Historical Trends**: 5-year historical weather analysis with interactive charts
- **AI Predictions**: Machine learning-powered 24-hour weather forecasts
- **Weather Alerts**: SMS/email notifications for severe weather conditions
- **Route Planning**: Weather-aware route planning with hazard assessment
- **User Accounts**: Personalized location preferences and settings
- **Admin Panel**: Comprehensive user and data management

### Advanced Capabilities
- **Multi-API Integration**: OpenWeatherMap (primary), Open-Meteo.com (secondary), Weatherstack (backup)
- **Intelligent Caching**: Redis-based caching with automatic invalidation
- **Real-time Updates**: 30-minute data freshness with automatic API calls
- **Performance Monitoring**: Comprehensive system health and performance metrics
- **Push Notifications**: Web push notifications with user preference management
- **Background Processing**: Celery-based asynchronous task processing

## 🏗️ Architecture

### Backend Architecture (Django + DRF)
```
weather247/
├── backend/                    # Django backend application
│   ├── weather247_backend/     # Django project settings and URLs
│   ├── weather_data/          # Core weather functionality
│   ├── accounts/              # User management and authentication
│   ├── route_planner/         # Route planning with weather integration
│   └── templates/             # Admin templates
├── frontend/                  # React frontend application
└── docs/                      # Project documentation
```

### Technology Stack

#### Backend
- **Framework**: Django 4.2.10 with Django REST Framework 3.16.1
- **Database**: PostgreSQL with SQLite for development
- **Cache/Message Broker**: Redis 6.4.0
- **Task Queue**: Celery 5.5.3 with django-celery-beat
- **AI/ML**: Scikit-learn, NumPy, Pandas, Matplotlib, Seaborn
- **Authentication**: Django REST Framework Token Authentication
- **API Documentation**: Built-in DRF browsable API

#### Frontend
- **Framework**: React 19.1.0 with Vite 6.3.5
- **Styling**: Tailwind CSS 4.1.7 with Radix UI components
- **Charts**: Recharts for data visualization
- **Maps**: Leaflet.js for geographic features
- **State Management**: React Hook Form with Zod validation
- **Routing**: React Router DOM 7.6.1
- **PWA**: Progressive Web App support

#### DevOps & Deployment
- **Containerization**: Docker with Docker Compose
- **Process Management**: Background services for web, worker, and beat
- **Monitoring**: Flower for Celery monitoring
- **Tunneling**: ngrok for local development sharing

## 📁 Detailed Directory Structure

### Backend Directory (`backend/`)

#### `weather247_backend/` - Django Project Core
- **`settings.py`**: Main Django configuration with environment-based settings
- **`urls.py`**: Root URL configuration and API routing
- **`wsgi.py`**: WSGI application entry point
- **`asgi.py`**: ASGI application entry point (for async support)

#### `weather_data/` - Core Weather Application
- **`models.py`**: Comprehensive data models for weather, cities, and user preferences
- **`views.py`**: API endpoints for weather data, forecasts, and analytics
- **`serializers.py`**: DRF serializers for data transformation
- **`real_weather_service.py`**: Weather API integration with fallback strategies
- **`cache_manager.py`**: Redis-based caching system
- **`validators.py`**: Data validation utilities
- **`admin.py`**: Custom Django admin interface
- **`urls.py`**: Weather API routing

#### `accounts/` - User Management System
- **`models.py`**: Extended user model with profiles, roles, and permissions
- **`views.py`**: Authentication, registration, and user management endpoints
- **`serializers.py`**: User data serialization and validation
- **`admin.py`**: User administration interface
- **`urls.py`**: Authentication and user management routing

#### `route_planner/` - Route Planning with Weather
- **`models.py`**: Route, weather points, and travel plan models
- **`views.py`**: Route creation, weather integration, and hazard assessment
- **`serializers.py`**: Route data serialization
- **`urls.py`**: Route planning API endpoints

### Frontend Directory (`frontend/`)

#### `src/` - React Application Source
- **`App.jsx`**: Main application component with routing
- **`main.jsx`**: Application entry point
- **`pages/`**: Route-based page components
- **`components/`**: Reusable UI components
- **`services/`**: API integration and external services
- **`hooks/`**: Custom React hooks
- **`lib/`**: Utility functions and configurations
- **`assets/`**: Static assets and images

#### Configuration Files
- **`package.json`**: Node.js dependencies and scripts
- **`vite.config.js`**: Vite build configuration
- **`tailwind.config.js`**: Tailwind CSS configuration
- **`eslint.config.js`**: Code linting configuration

## 🔧 API Endpoints

### Weather API (`/api/weather/`)
- `GET /cities/` - List all cities
- `GET /cities/{id}/` - Get city details
- `GET /current/{city_id}/` - Get current weather for a city
- `GET /forecast/{city_id}/` - Get weather forecast
- `GET /air-quality/{city_id}/` - Get air quality data
- `GET /historical/{city_id}/` - Get historical weather data
- `GET /predictions/{city_id}/` - Get AI weather predictions

### Authentication API (`/api/auth/`)
- `POST /register/` - User registration
- `POST /login/` - User authentication
- `POST /logout/` - User logout
- `GET /profile/` - Get user profile
- `PUT /profile/` - Update user profile
- `POST /change-password/` - Change user password

### Route Planning API (`/api/routes/`)
- `GET /routes/` - List user routes (authenticated)
- `POST /routes/` - Create new route
- `GET /routes/{id}/` - Get route details
- `POST /create_with_weather/` - Create route with weather integration
- `GET /routes/{id}/weather/` - Get weather along route

## 🚀 Getting Started

### Prerequisites
- Python 3.13+
- Node.js 18+
- Redis server
- PostgreSQL (optional, SQLite for development)

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DJANGO_SETTINGS_MODULE=weather247_backend.settings
export PYTHONPATH=$(pwd)
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

### Frontend Setup
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

### Docker Setup
```bash
docker-compose up --build -d
```

## 🧪 Testing

### Backend Testing
- **Unit Tests**: Django test framework with comprehensive coverage
- **Integration Tests**: API endpoint testing with real data
- **Performance Tests**: Cache performance and response time benchmarks
- **Test Runner**: Automated test execution with detailed reporting

### Test Files
- `test_api.py` - API endpoint testing
- `test_auth.py` - Authentication system testing
- `test_caching.py` - Cache system testing
- `test_validation.py` - Data validation testing
- `test_weather_manager.py` - Weather service testing
- `comprehensive_test.py` - End-to-end testing

## 📊 Data Models

### Core Models
- **`City`**: Geographic and timezone information
- **`WeatherData`**: Current weather metrics
- **`AirQualityData`**: AQI and pollutant measurements
- **`WeatherForecast`**: Multi-day weather predictions
- **`HistoricalWeatherData`**: Long-term weather trends
- **`WeatherPrediction`**: AI-generated forecasts
- **`UserWeatherPreference`**: Personalized user settings
- **`PushSubscription`**: Web push notification management

### User Management Models
- **`User`**: Extended user model with additional fields
- **`UserProfile`**: User profile information
- **`UserRole`**: Role-based access control
- **`UserActivity`**: User activity tracking
- **`UserSession`**: Session management

### Route Planning Models
- **`Route`**: Route definition and metadata
- **`RouteWeatherPoint`**: Weather data along routes
- **`RouteAlert`**: Weather alerts for routes
- **`TravelPlan`**: Comprehensive travel planning

## 🔒 Security Features

- **Authentication**: Token-based authentication with DRF
- **Authorization**: Role-based access control
- **Input Validation**: Comprehensive data validation
- **Rate Limiting**: API request rate limiting
- **CORS**: Cross-origin resource sharing configuration
- **HTTPS**: Secure communication (in production)

## 📈 Performance Features

- **Caching**: Redis-based caching with automatic invalidation
- **Database Optimization**: Query optimization and indexing
- **Background Processing**: Celery-based asynchronous tasks
- **Response Compression**: Gzip compression for API responses
- **Connection Pooling**: Database connection optimization

## 🚀 Deployment

### Production Considerations
- **Environment Variables**: Secure configuration management
- **Database**: PostgreSQL for production use
- **Caching**: Redis cluster for high availability
- **Monitoring**: Application performance monitoring
- **Logging**: Structured logging with rotation
- **Backup**: Automated database and file backups

### Hosting Options
- **Container Platforms**: Docker, Kubernetes
- **Cloud Providers**: AWS, Google Cloud, Azure
- **PaaS**: Heroku, Render, Fly.io
- **VPS**: DigitalOcean, Linode, Vultr

## 🔧 Configuration

### Environment Variables
```bash
DJANGO_SETTINGS_MODULE=weather247_backend.settings
OPENWEATHER_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:pass@localhost:5432/weather247
```

### Django Settings
- **Database**: Configurable database backends
- **Cache**: Redis configuration with fallbacks
- **Static Files**: CDN and local serving options
- **Media Files**: File storage configuration
- **Logging**: Configurable logging levels and handlers

## 📚 API Documentation

### Interactive API
- **DRF Browsable API**: Built-in API browser at `/api/`
- **Swagger/OpenAPI**: API documentation generation
- **Postman Collections**: Pre-configured API testing

### Authentication
```bash
# Get authentication token
curl -X POST https://yourdomain.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Use token in requests
curl -H "Authorization: Token your_token_here" \
  https://yourdomain.com/api/weather/cities/
```

## 🎯 Future Enhancements

### Planned Features
- **Mobile App**: React Native mobile application
- **Advanced Analytics**: Machine learning insights
- **Weather Alerts**: Real-time notification system
- **Social Features**: User sharing and collaboration
- **API Marketplace**: Third-party integrations

### Technical Improvements
- **GraphQL**: Alternative to REST API
- **WebSockets**: Real-time updates
- **Microservices**: Service decomposition
- **Kubernetes**: Container orchestration
- **CI/CD**: Automated deployment pipelines

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Standards
- **Python**: PEP 8 compliance
- **JavaScript**: ESLint configuration
- **Testing**: Minimum 80% code coverage
- **Documentation**: Comprehensive docstrings and comments

## 📄 License

This project is developed as part of an academic project at Government Post Graduate College (Boys), Satellite Town Gujranwala.

## 👥 Contributors

- **Muhammad Zaheer Ul Din Babar** (Group Leader)
- **Waqas Ahmad**

## 📞 Support

For technical support or questions:
- **Issues**: GitHub issue tracker
- **Documentation**: Project documentation
- **Email**: Contact project maintainers

---

*This documentation is maintained as part of the Weather247 project and should be updated as the project evolves.*
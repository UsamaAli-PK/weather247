# Weather247

Weather247 is an AI-powered weather application that provides real-time, historical, and predictive weather insights through an interactive web platform.

## Project Overview

**Goal:** To provide real-time, historical, and predictive weather insights through an interactive web platform.

**Target Users:** General public, meteorologists, agriculture/aviation industries.

## Key Features

1. **Real-time Weather Data:** Display current weather data (temperature, humidity, AQI) for 3+ cities
2. **Weather Comparison:** Side-by-side comparison of weather metrics across cities
3. **Historical Trends:** Visualize historical weather trends (last 5 years) using interactive charts
4. **AI Predictions:** Generate AI-powered 24-hour weather predictions
5. **Weather Alerts:** SMS/email alerts for severe weather conditions
6. **Route Planning:** Weather-aware route planning with Google Maps-like interface
7. **User Accounts:** Personalized location preferences for authenticated users
8. **Admin Panel:** Manage data sources, users, and API integrations

## Technology Stack

### Backend
- **Framework:** Django with Django REST Framework
- **Database:** PostgreSQL
- **Cache/Message Broker:** Redis
- **Task Queue:** Celery
- **AI/ML:** Scikit-learn, NumPy, Pandas, Matplotlib, Seaborn

### Frontend
- **Framework:** React
- **Styling:** HTML5, CSS3, Bootstrap 5, Tailwind CSS
- **Charts:** Chart.js/Plotly, Recharts
- **Maps:** Leaflet.js
- **Icons:** Lucide React

### APIs
- **Primary Weather API:** OpenWeatherMap
- **Secondary Weather API:** Open-Meteo.com
- **Backup Weather API:** Weatherstack

## Project Structure

```
weather247/
├── backend/                # Django backend application
├── frontend/               # React frontend application
├── docs/                   # Project documentation
├── README.md
└── .gitignore
```

## Getting Started

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

4. Start the Django development server:
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Start the React development server:
   ```bash
   pnpm run dev
   ```

## Documentation

Detailed documentation can be found in the `docs/` directory:

- [API Documentation](docs/api_documentation.md)
- [Database Schema](docs/database_schema.md)
- [Frontend Components](docs/frontend_components.md)
- [Weather APIs](docs/weather_apis.md)

## License

This project is developed as part of an academic project at Government Post Graduate College (Boys), Satellite Town Gujranwala.

## Contributors

- Muhammad Zaheer Ul Din Babar (Group Leader)
- Waqas Ahmad

## Deployment (Docker)

### Quick start

1. Create an `.env` file with at least:
```
DJANGO_SETTINGS_MODULE=weather247_backend.settings
OPENWEATHER_API_KEY=demo-key
SECRET_KEY=change-me
DEBUG=False
ALLOWED_HOSTS=*
```

2. Build and run:
```
docker compose up --build -d
```

3. Run migrations and create superuser:
```
docker compose exec web python manage.py migrate
```

### File/Folder Overview

- `backend/`: Django backend
  - `accounts/`: custom user model, auth endpoints
  - `weather_data/`: weather models, views, serializers, caching, alerts, system monitoring
    - `views.py`: API endpoints (current, forecast, AI predictions, analytics, health)
    - `models.py`: `City`, `WeatherData`, `AirQualityData`, `WeatherForecast`, `HistoricalWeatherData`, `WeatherPrediction`, alert/push/system models
    - `real_weather_service.py`: weather manager with API integration and fallback
    - `validators.py`: validation utilities
    - `cache_manager.py`: cache helpers
    - `alert_system.py`: persisted alert engine and delivery
    - `system_monitoring*.py`: monitoring services and core
    - `urls.py`: routes for weather API
  - `route_planner/`: routing with weather, alerts, hazard scoring
    - `models.py`: `Route`, `RouteWeatherPoint`, `RouteAlert`, `TravelPlan` (+ hazard fields)
    - `views.py`: create routes, fetch route weather, compute alerts/hazard
    - `serializers.py`: serializers including hazard fields
  - `weather247_backend/`: Django project settings and URLs
- `frontend/`: static/demo frontend resources
- `.kiro/specs/`: specification tasks
- `run_tests.py`: comprehensive test runner

### Local run

```
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
export DJANGO_SETTINGS_MODULE=weather247_backend.settings
export PYTHONPATH=$(pwd)/backend
python backend/manage.py migrate
python backend/manage.py runserver 0.0.0.0:8000
```

### Hosting

- Containerize with Docker Compose (web + optional redis/celery) and deploy to any container host (Render, Fly.io, AWS ECS). Configure `OPENWEATHER_API_KEY`, email/Twilio only if needed. Optional deps (`celery`, `psutil`, `pywebpush`, `numpy`) are guarded.


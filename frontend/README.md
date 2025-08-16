# Frontend Application
## React Progressive Web App for Weather247

**Framework:** React 19.1.0 + Vite 6.3.5  
**Styling:** Tailwind CSS 4.1.7 + Radix UI  
**Build Tool:** Vite 6.3.5  
**Status:** Production Ready  

---

## 🎯 **Overview**

The Frontend application is a modern, responsive Progressive Web App (PWA) built with React that provides an intuitive user interface for weather information, route planning, and user management. It features a mobile-first design, offline functionality, and seamless integration with the backend API.

---

## 📁 **Directory Structure**

```
frontend/
├── 📁 public/                # Static assets and PWA files
│   ├── 📄 index.html         # Main HTML template
│   ├── 📄 favicon.ico        # Application icon
│   ├── 📄 manifest.json      # PWA manifest
│   ├── 📄 robots.txt         # Search engine configuration
│   └── 📄 icons/             # PWA icons (various sizes)
├── 📁 src/                   # Source code
│   ├── 📁 components/        # Reusable React components
│   │   ├── 📁 ui/            # Base UI components
│   │   ├── 📁 weather/       # Weather-specific components
│   │   ├── 📁 routes/        # Route planning components
│   │   ├── 📁 forms/         # Form components
│   │   └── 📁 layout/        # Layout components
│   ├── 📁 pages/             # Page components
│   │   ├── 📄 Home.jsx       # Home page
│   │   ├── 📄 Weather.jsx    # Weather details page
│   │   ├── 📄 Forecast.jsx   # Weather forecast page
│   │   ├── 📄 Routes.jsx     # Route planning page
│   │   ├── 📄 Profile.jsx    # User profile page
│   │   └── 📄 Login.jsx      # Authentication page
│   ├── 📁 hooks/             # Custom React hooks
│   │   ├── 📄 useWeather.js  # Weather data hook
│   │   ├── 📄 useAuth.js     # Authentication hook
│   │   ├── 📄 useRoutes.js   # Route planning hook
│   │   └── 📄 useLocalStorage.js # Local storage hook
│   ├── 📁 services/          # API services
│   │   ├── 📄 api.js         # Base API configuration
│   │   ├── 📄 weatherService.js # Weather API calls
│   │   ├── 📄 authService.js # Authentication API calls
│   │   └── 📄 routeService.js # Route planning API calls
│   ├── 📁 utils/             # Utility functions
│   │   ├── 📄 constants.js   # Application constants
│   │   ├── 📄 helpers.js     # Helper functions
│   │   ├── 📄 validation.js  # Form validation
│   │   └── 📄 formatters.js  # Data formatting
│   ├── 📁 styles/            # Global styles
│   │   ├── 📄 globals.css    # Global CSS
│   │   ├── 📄 components.css # Component styles
│   │   └── 📄 utilities.css  # Utility classes
│   ├── 📁 context/           # React context providers
│   │   ├── 📄 AuthContext.js # Authentication context
│   │   ├── 📄 WeatherContext.js # Weather data context
│   │   └── 📄 ThemeContext.js # Theme context
│   ├── 📄 App.jsx            # Main application component
│   ├── 📄 main.jsx           # Application entry point
│   └── 📄 index.css          # Root styles
├── 📄 package.json           # Node.js dependencies
├── 📄 vite.config.js         # Vite configuration
├── 📄 tailwind.config.js     # Tailwind CSS configuration
├── 📄 postcss.config.js      # PostCSS configuration
├── 📄 .eslintrc.js           # ESLint configuration
├── 📄 .prettierrc            # Prettier configuration
└── 📄 README.md              # This file
```

---

## 🏗️ **Architecture**

### **Component Architecture**
```
App (Root)
├── Router
│   ├── Layout
│   │   ├── Header
│   │   ├── Navigation
│   │   └── Footer
│   ├── Pages
│   │   ├── Home
│   │   ├── Weather
│   │   ├── Forecast
│   │   ├── Routes
│   │   └── Profile
│   └── Auth Pages
│       ├── Login
│       └── Register
└── Context Providers
    ├── AuthContext
    ├── WeatherContext
    └── ThemeContext
```

### **Data Flow Architecture**
```
User Interaction → Component → Hook → Service → API → Backend
       ↓              ↓         ↓        ↓       ↓
   State Update → Re-render → UI Update → Response → Data
```

---

## 🚀 **Quick Start**

### **Prerequisites**
- Node.js 18+
- npm or yarn package manager

### **1. Installation**
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### **2. Build for Production**
```bash
# Build the application
npm run build

# Preview production build
npm run preview
```

### **3. Development Commands**
```bash
# Start development server
npm run dev

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Lint code
npm run lint

# Format code
npm run format

# Type check (if using TypeScript)
npm run type-check
```

---

## 🎨 **UI Components**

### **1. Base UI Components** 🧩
**Location:** `src/components/ui/`

**Components:**
- **Button**: Primary, secondary, and ghost button variants
- **Input**: Text, email, password, and search inputs
- **Card**: Content containers with various styles
- **Modal**: Overlay dialogs and popups
- **Dropdown**: Select menus and dropdowns
- **Toast**: Notification messages
- **Spinner**: Loading indicators
- **Badge**: Status and label indicators

**Usage:**
```jsx
import { Button, Input, Card } from '@/components/ui';

function ExampleComponent() {
  return (
    <Card>
      <Input placeholder="Enter city name" />
      <Button variant="primary">Search Weather</Button>
    </Card>
  );
}
```

### **2. Weather Components** 🌤️
**Location:** `src/components/weather/`

**Components:**
- **WeatherCard**: Current weather display
- **ForecastCard**: Weather forecast display
- **WeatherIcon**: Weather condition icons
- **TemperatureDisplay**: Temperature with unit conversion
- **WeatherDetails**: Detailed weather information
- **AirQualityCard**: Air quality information
- **WeatherChart**: Historical weather charts
- **WeatherAlert**: Weather warning display

**Usage:**
```jsx
import { WeatherCard, ForecastCard } from '@/components/weather';

function WeatherPage() {
  return (
    <div>
      <WeatherCard city="New York" />
      <ForecastCard city="New York" days={7} />
    </div>
  );
}
```

### **3. Route Planning Components** 🗺️
**Location:** `src/components/routes/`

**Components:**
- **RouteMap**: Interactive map display
- **RouteForm**: Route creation form
- **RouteCard**: Route information display
- **WaypointList**: Route waypoints
- **WeatherOverlay**: Weather on route
- **HazardIndicator**: Route hazard warnings
- **RouteOptimizer**: Route optimization tools

**Usage:**
```jsx
import { RouteMap, RouteForm } from '@/components/routes';

function RoutePage() {
  return (
    <div>
      <RouteForm />
      <RouteMap />
    </div>
  );
}
```

### **4. Layout Components** 🏗️
**Location:** `src/components/layout/`

**Components:**
- **Header**: Application header with navigation
- **Sidebar**: Side navigation menu
- **Footer**: Application footer
- **Navigation**: Main navigation menu
- **Breadcrumb**: Page navigation breadcrumbs
- **Container**: Content wrapper with responsive behavior

**Usage:**
```jsx
import { Header, Sidebar, Footer } from '@/components/layout';

function Layout({ children }) {
  return (
    <div>
      <Header />
      <Sidebar />
      <main>{children}</main>
      <Footer />
    </div>
  );
}
```

---

## 📱 **Pages**

### **1. Home Page** 🏠
**File:** `src/pages/Home.jsx`

**Purpose:** Main landing page with weather overview

**Features:**
- Current weather for user's location
- Quick weather search
- Weather alerts and warnings
- Recent searches
- Quick actions (forecast, routes)

**Components Used:**
- WeatherCard
- SearchBar
- AlertBanner
- QuickActions

### **2. Weather Page** 🌤️
**File:** `src/pages/Weather.jsx`

**Purpose:** Detailed weather information

**Features:**
- Current weather conditions
- Hourly and daily forecasts
- Weather maps and radar
- Air quality information
- Historical weather data

**Components Used:**
- WeatherCard
- ForecastCard
- WeatherMap
- AirQualityCard
- WeatherChart

### **3. Forecast Page** 📅
**File:** `src/pages/Forecast.jsx`

**Purpose:** Extended weather predictions

**Features:**
- 7-day weather forecast
- Hourly breakdowns
- Precipitation probability
- Wind and pressure forecasts
- UV index information

**Components Used:**
- ForecastCard
- WeatherChart
- WeatherIcon
- TemperatureDisplay

### **4. Routes Page** 🗺️
**File:** `src/pages/Routes.jsx`

**Purpose:** Weather-integrated route planning

**Features:**
- Route creation and editing
- Weather overlay on routes
- Hazard assessment
- Route optimization
- Multi-waypoint support

**Components Used:**
- RouteMap
- RouteForm
- RouteCard
- WeatherOverlay
- HazardIndicator

### **5. Profile Page** 👤
**File:** `src/pages/Profile.jsx`

**Purpose:** User account management

**Features:**
- User profile information
- Weather preferences
- Notification settings
- Account security
- Usage statistics

**Components Used:**
- ProfileForm
- PreferencesForm
- SecuritySettings
- UsageStats

---

## 🔌 **Custom Hooks**

### **1. useWeather Hook** 🌤️
**File:** `src/hooks/useWeather.js`

**Purpose:** Weather data management

**Features:**
- Fetch current weather
- Get weather forecasts
- Historical weather data
- Air quality information
- Weather alerts

**Usage:**
```jsx
import { useWeather } from '@/hooks/useWeather';

function WeatherComponent() {
  const { 
    currentWeather, 
    forecast, 
    loading, 
    error,
    fetchWeather 
  } = useWeather();

  useEffect(() => {
    fetchWeather('New York');
  }, []);

  if (loading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;

  return <WeatherCard weather={currentWeather} />;
}
```

### **2. useAuth Hook** 🔐
**File:** `src/hooks/useAuth.js`

**Purpose:** Authentication management

**Features:**
- User login/logout
- Registration
- Password reset
- Profile management
- Token management

**Usage:**
```jsx
import { useAuth } from '@/hooks/useAuth';

function LoginForm() {
  const { login, loading, error } = useAuth();

  const handleSubmit = async (credentials) => {
    await login(credentials);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
    </form>
  );
}
```

### **3. useRoutes Hook** 🗺️
**File:** `src/hooks/useRoutes.js`

**Purpose:** Route planning management

**Features:**
- Create routes
- Fetch route weather
- Optimize routes
- Manage waypoints
- Route history

**Usage:**
```jsx
import { useRoutes } from '@/hooks/useRoutes';

function RouteComponent() {
  const { 
    routes, 
    createRoute, 
    loading, 
    error 
  } = useRoutes();

  const handleCreateRoute = async (routeData) => {
    await createRoute(routeData);
  };

  return (
    <div>
      <RouteForm onSubmit={handleCreateRoute} />
      <RouteList routes={routes} />
    </div>
  );
}
```

---

## 🌐 **API Services**

### **1. Base API Configuration** ⚙️
**File:** `src/services/api.js`

**Purpose:** Centralized API configuration

**Features:**
- Base URL configuration
- Request/response interceptors
- Error handling
- Authentication headers
- Request timeout

**Usage:**
```jsx
import api from '@/services/api';

// GET request
const weather = await api.get('/weather/current/New York');

// POST request
const route = await api.post('/routes/', routeData);

// PUT request
const profile = await api.put('/auth/profile/', profileData);
```

### **2. Weather Service** 🌤️
**File:** `src/services/weatherService.js`

**Purpose:** Weather-related API calls

**Endpoints:**
- Current weather
- Weather forecasts
- Historical data
- Air quality
- Weather alerts

**Usage:**
```jsx
import { weatherService } from '@/services/weatherService';

// Get current weather
const weather = await weatherService.getCurrentWeather('New York');

// Get forecast
const forecast = await weatherService.getForecast('New York', 7);

// Get air quality
const airQuality = await weatherService.getAirQuality('New York');
```

### **3. Authentication Service** 🔐
**File:** `src/services/authService.js`

**Purpose:** Authentication API calls

**Endpoints:**
- User registration
- User login
- Password reset
- Profile management
- Token refresh

**Usage:**
```jsx
import { authService } from '@/services/authService';

// User login
const user = await authService.login(credentials);

// User registration
const newUser = await authService.register(userData);

// Get profile
const profile = await authService.getProfile();
```

---

## 🎨 **Styling & Design**

### **1. Tailwind CSS** 🎨
**Configuration:** `tailwind.config.js`

**Features:**
- Utility-first CSS framework
- Responsive design utilities
- Custom color palette
- Component variants
- Dark mode support

**Usage:**
```jsx
function WeatherCard() {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
        Current Weather
      </h2>
      <div className="mt-4 text-gray-600 dark:text-gray-300">
        {/* Weather content */}
      </div>
    </div>
  );
}
```

### **2. Radix UI** 🧩
**Purpose:** Accessible UI primitives

**Components:**
- Dialog
- Dropdown Menu
- Select
- Tabs
- Toast
- Tooltip

**Usage:**
```jsx
import { Dialog, DialogContent, DialogTrigger } from '@radix-ui/react-dialog';

function WeatherModal() {
  return (
    <Dialog>
      <DialogTrigger>Open Weather</DialogTrigger>
      <DialogContent>
        <WeatherCard />
      </DialogContent>
    </Dialog>
  );
}
```

### **3. Custom CSS** 🎯
**Location:** `src/styles/`

**Files:**
- `globals.css`: Global styles and CSS variables
- `components.css`: Component-specific styles
- `utilities.css`: Custom utility classes

**Usage:**
```css
/* globals.css */
:root {
  --primary-color: #3b82f6;
  --secondary-color: #64748b;
  --accent-color: #f59e0b;
}

/* components.css */
.weather-card {
  @apply bg-white rounded-lg shadow-md p-6;
  border: 1px solid var(--border-color);
}
```

---

## 📱 **Progressive Web App Features**

### **1. PWA Configuration** ⚙️
**File:** `public/manifest.json`

**Features:**
- App name and description
- Icons for various sizes
- Theme colors
- Display mode
- Orientation preferences

### **2. Service Worker** 🔄
**Purpose:** Offline functionality and caching

**Features:**
- Offline weather data
- Route caching
- Background sync
- Push notifications
- App updates

### **3. Offline Support** 📴
**Features:**
- Cached weather data
- Offline route planning
- Local storage
- Background sync
- Progressive enhancement

---

## 🧪 **Testing**

### **1. Testing Framework** 🧪
**Tools:**
- Jest for unit testing
- React Testing Library for component testing
- MSW for API mocking
- Testing Library for user interactions

### **2. Test Structure** 📁
```
__tests__/
├── components/        # Component tests
├── hooks/            # Hook tests
├── services/         # Service tests
├── utils/            # Utility tests
└── setup/            # Test setup files
```

### **3. Running Tests** 🚀
```bash
# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch

# Run specific test file
npm test WeatherCard.test.jsx
```

---

## 🚀 **Build & Deployment**

### **1. Development Build** 🔧
```bash
# Start development server
npm run dev

# Build for development
npm run build:dev
```

### **2. Production Build** 🚀
```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Analyze bundle
npm run analyze
```

### **3. Environment Configuration** ⚙️
**Files:**
- `.env.development`: Development environment variables
- `.env.production`: Production environment variables
- `.env.local`: Local environment variables

**Variables:**
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WEATHER_API_KEY=your-api-key
VITE_APP_NAME=Weather247
VITE_APP_VERSION=1.0.0
```

---

## 🔧 **Configuration Files**

### **1. Vite Configuration** ⚡
**File:** `vite.config.js`

**Features:**
- React plugin
- Path aliases
- Environment variables
- Build optimization
- Development server

### **2. Tailwind Configuration** 🎨
**File:** `tailwind.config.js`

**Features:**
- Custom color palette
- Component variants
- Responsive breakpoints
- Dark mode support
- Custom utilities

### **3. ESLint Configuration** 📝
**File:** `.eslintrc.js`

**Features:**
- React rules
- JavaScript standards
- Import organization
- Code quality
- Accessibility rules

---

## 🔒 **Security Features**

### **1. Input Validation** ✅
- Form validation
- XSS prevention
- CSRF protection
- Input sanitization

### **2. Authentication** 🔐
- JWT token management
- Secure storage
- Token refresh
- Logout handling

### **3. API Security** 🛡️
- HTTPS enforcement
- CORS configuration
- Rate limiting
- Error handling

---

## 📊 **Performance Optimization**

### **1. Code Splitting** 📦
- Route-based splitting
- Component lazy loading
- Dynamic imports
- Bundle optimization

### **2. Caching Strategies** 💾
- Service worker caching
- Local storage
- Memory caching
- API response caching

### **3. Image Optimization** 🖼️
- WebP format support
- Responsive images
- Lazy loading
- Compression

---

## 🔧 **Troubleshooting**

### **1. Common Issues**

#### **Build Errors**
```bash
# Clear node modules
rm -rf node_modules package-lock.json
npm install

# Clear cache
npm run clean
```

#### **Development Server Issues**
```bash
# Check port availability
lsof -i :5173

# Kill process
kill -9 <PID>
```

#### **Dependency Issues**
```bash
# Update dependencies
npm update

# Check for conflicts
npm ls
```

### **2. Debug Mode**
```bash
# Enable debug logging
DEBUG=* npm run dev

# Check browser console
# Check network tab
# Check application tab
```

---

## 📚 **Additional Resources**

### **Documentation**
- **React Documentation**: https://react.dev/
- **Vite Documentation**: https://vitejs.dev/
- **Tailwind CSS**: https://tailwindcss.com/
- **Radix UI**: https://www.radix-ui.com/

### **Development Tools**
- **React Developer Tools**: Browser extension
- **Vite DevTools**: Development utilities
- **ESLint**: Code quality
- **Prettier**: Code formatting

---

## 🤝 **Contributing**

### **Development Workflow**
1. **Fork Repository**: Create your fork
2. **Create Branch**: `git checkout -b feature/frontend-feature`
3. **Make Changes**: Implement your feature
4. **Run Tests**: Ensure all tests pass
5. **Submit PR**: Create pull request with description

### **Code Standards**
- **JavaScript**: ES6+ standards
- **React**: Functional components with hooks
- **CSS**: Tailwind CSS utilities
- **Testing**: Comprehensive test coverage
- **Accessibility**: WCAG 2.1 compliance

---

## 📞 **Support & Contact**

### **Technical Support**
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: Project documentation
- **Wiki**: Project wiki pages

### **Contact Information**
- **Student**: [Your Name]
- **Email**: [Your Email]
- **Supervisor**: [Supervisor Name]
- **Department**: Computer Science
- **University**: [University Name]

---

**Frontend Application - Weather247** 🎨

**Modern React PWA with beautiful, responsive design**
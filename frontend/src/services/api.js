// API service for Weather247 frontend
const API_BASE_URL = 'http://localhost:8000/api';

class ApiService {
  constructor() {
    this.token = localStorage.getItem('authToken');
  }

  // Helper method to get headers
  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (this.token) {
      headers['Authorization'] = `Token ${this.token}`;
    }
    
    return headers;
  }

  // Helper method to handle responses
  async handleResponse(response) {
    if (!response.ok) {
      let errorMessage = 'API request failed';
      try {
        const errorData = await response.json();
        console.log('Error response data:', errorData); // Debug logging
        
        // Handle different error formats
        if (errorData.error) {
          errorMessage = errorData.error;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.non_field_errors) {
          errorMessage = errorData.non_field_errors.join(', ');
        } else if (typeof errorData === 'object') {
          // Handle field-specific errors
          const fieldErrors = [];
          for (const [field, errors] of Object.entries(errorData)) {
            if (Array.isArray(errors)) {
              fieldErrors.push(`${field}: ${errors.join(', ')}`);
            } else {
              fieldErrors.push(`${field}: ${errors}`);
            }
          }
          if (fieldErrors.length > 0) {
            errorMessage = fieldErrors.join('; ');
          }
        }
      } catch (parseError) {
        console.error('Error parsing error response:', parseError);
        if (response.status === 0) {
          errorMessage = 'Cannot connect to server. Please check if the backend is running.';
        } else {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
      }
      
      throw new Error(errorMessage);
    }
    return response.json();
  }

  // Authentication methods
  async register(userData) {
    try {
      console.log('Sending registration data:', userData); // Debug logging
      const response = await fetch(`${API_BASE_URL}/auth/register/`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(userData),
      });
      
      console.log('Registration response status:', response.status); // Debug logging
      
      const data = await this.handleResponse(response);
      
      if (data.token) {
        this.token = data.token;
        localStorage.setItem('authToken', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
      }
      
      return data;
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  }

  async login(credentials) {
    try {
      console.log('Sending login data:', credentials); // Debug logging
      const response = await fetch(`${API_BASE_URL}/auth/login/`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(credentials),
      });
      
      console.log('Login response status:', response.status); // Debug logging
      
      const data = await this.handleResponse(response);
      
      if (data.token) {
        this.token = data.token;
        localStorage.setItem('authToken', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
      }
      
      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async logout() {
    try {
      await fetch(`${API_BASE_URL}/auth/logout/`, {
        method: 'POST',
        headers: this.getHeaders(),
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.token = null;
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
    }
  }

  // Weather data methods
  async getWeatherByCity(cityName, country = '') {
    try {
      const params = new URLSearchParams({ city: cityName });
      if (country) params.append('country', country);
      
      const response = await fetch(`${API_BASE_URL}/weather/current/?${params}`, {
        headers: this.getHeaders(),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('Weather fetch error:', error);
      throw error;
    }
  }

  async getMultipleCitiesWeather(cities) {
    try {
      const params = new URLSearchParams({ cities: cities.join(',') });
      
      const response = await fetch(`${API_BASE_URL}/weather/multiple/?${params}`, {
        headers: this.getHeaders(),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('Multiple cities weather fetch error:', error);
      throw error;
    }
  }

  async getForecast(cityId, days = 5) {
    try {
      const params = new URLSearchParams({ days: days.toString() });
      
      const response = await fetch(`${API_BASE_URL}/weather/forecast/${cityId}/?${params}`, {
        headers: this.getHeaders(),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('Forecast fetch error:', error);
      throw error;
    }
  }

  async getAirQuality(cityId) {
    try {
      const response = await fetch(`${API_BASE_URL}/weather/air-quality/${cityId}/`, {
        headers: this.getHeaders(),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('Air quality fetch error:', error);
      throw error;
    }
  }

  // City management
  async getCities() {
    try {
      const response = await fetch(`${API_BASE_URL}/weather/cities/`, {
        headers: this.getHeaders(),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('Cities fetch error:', error);
      throw error;
    }
  }

  async createCity(cityData) {
    try {
      const response = await fetch(`${API_BASE_URL}/weather/cities/`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(cityData),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('City creation error:', error);
      throw error;
    }
  }

  // User profile methods
  async getUserProfile() {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/profile/`, {
        headers: this.getHeaders(),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('Profile fetch error:', error);
      throw error;
    }
  }

  async updateUserProfile(profileData) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/profile/`, {
        method: 'PATCH',
        headers: this.getHeaders(),
        body: JSON.stringify(profileData),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('Profile update error:', error);
      throw error;
    }
  }

  // AI and Analytics methods
  async getAIPredictions(cityName) {
    try {
      const params = new URLSearchParams({ city: cityName });
      
      const response = await fetch(`${API_BASE_URL}/weather/ai-predictions/?${params}`, {
        headers: this.getHeaders(),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('AI predictions fetch error:', error);
      throw error;
    }
  }

  async getHistoricalData(cityName, days = 30) {
    try {
      const params = new URLSearchParams({ city: cityName, days: days.toString() });
      
      const response = await fetch(`${API_BASE_URL}/weather/historical/?${params}`, {
        headers: this.getHeaders(),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('Historical data fetch error:', error);
      throw error;
    }
  }

  async compareCities(cityNames) {
    try {
      const params = new URLSearchParams({ cities: cityNames.join(',') });
      
      const response = await fetch(`${API_BASE_URL}/weather/compare/?${params}`, {
        headers: this.getHeaders(),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('City comparison fetch error:', error);
      throw error;
    }
  }

  // Enhanced weather analytics
  async getWeatherAnalytics(cityName, days = 7) {
    try {
      const params = new URLSearchParams({ city: cityName, days: days.toString() });
      
      const response = await fetch(`${API_BASE_URL}/weather/analytics/?${params}`, {
        headers: this.getHeaders(),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('Weather analytics fetch error:', error);
      throw error;
    }
  }

  async getWeatherMapData(cities = []) {
    try {
      const params = cities.length > 0 ? new URLSearchParams({ cities: cities.join(',') }) : '';
      
      const response = await fetch(`${API_BASE_URL}/weather/map-data/?${params}`, {
        headers: this.getHeaders(),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('Weather map data fetch error:', error);
      throw error;
    }
  }

  async triggerWeatherAlerts(cityName) {
    try {
      const response = await fetch(`${API_BASE_URL}/weather/alerts/trigger/`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ city: cityName }),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('Alert trigger error:', error);
      throw error;
    }
  }

  // Route planning methods
  async createRoute(routeData) {
    try {
      const response = await fetch(`${API_BASE_URL}/routes/routes/`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(routeData),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('Route creation error:', error);
      throw error;
    }
  }

  async getRouteWeather(routeId) {
    try {
      const response = await fetch(`${API_BASE_URL}/routes/routes/${routeId}/weather/`, {
        headers: this.getHeaders(),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('Route weather fetch error:', error);
      throw error;
    }
  }

  // City management methods
  async searchCities(query) {
    try {
      const params = new URLSearchParams({ q: query });
      
      const response = await fetch(`${API_BASE_URL}/weather/cities/search/?${params}`, {
        headers: this.getHeaders(),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('City search error:', error);
      throw error;
    }
  }

  async addCity(cityData) {
    try {
      const response = await fetch(`${API_BASE_URL}/weather/cities/add/`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(cityData),
      });
      
      return await this.handleResponse(response);
    } catch (error) {
      console.error('Add city error:', error);
      throw error;
    }
  }

  // Utility methods
  isAuthenticated() {
    return !!this.token;
  }

  getCurrentUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  }

  setToken(token) {
    this.token = token;
    localStorage.setItem('authToken', token);
  }

  clearAuth() {
    this.token = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
  }
}

// Create and export a singleton instance
const apiService = new ApiService();
export default apiService;


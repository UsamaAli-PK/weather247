import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CloudRain, MapPin, Thermometer, Droplet, Wind, Gauge, Eye, Sun, 
  LogOut, Route, TrendingUp, Brain, Bell, BarChart3, Zap, 
  RefreshCw, Calendar, Clock, AlertTriangle, CheckCircle,
  ArrowUp, ArrowDown, Activity, Globe, Layers
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import WeatherCard from '../components/WeatherCard';
import WeatherChart from '../components/WeatherChart';
import apiService from '../services/api';

const ModernDashboard = () => {
  const [user, setUser] = useState(null);
  const [cities, setCities] = useState([]);
  const [selectedCity, setSelectedCity] = useState('New York');
  const [weatherData, setWeatherData] = useState(null);
  const [aiPredictions, setAiPredictions] = useState(null);
  const [historicalData, setHistoricalData] = useState(null);
  const [comparisonData, setComparisonData] = useState(null);
  const [weatherAnalytics, setWeatherAnalytics] = useState(null);
  const [mapData, setMapData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [lastUpdated, setLastUpdated] = useState(null);

  const defaultCities = ['New York', 'London', 'Tokyo', 'Paris', 'Sydney', 'Dubai'];

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (!token) {
      window.location.href = '/signin';
      return;
    }
    
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (selectedCity) {
      fetchWeatherData(selectedCity);
    }
  }, [selectedCity]);

  const fetchInitialData = async () => {
    try {
      const userData = apiService.getCurrentUser();
      setUser(userData);
      setCities(defaultCities);
      setSelectedCity(defaultCities[0]);
    } catch (err) {
      console.error('Failed to fetch initial data:', err);
    }
  };

  const fetchWeatherData = async (cityName) => {
    setLoading(true);
    setError('');
    
    try {
      // Fetch current weather
      const weather = await apiService.getWeatherByCity(cityName);
      setWeatherData(weather);
      
      // Fetch AI predictions
      const predictions = await apiService.getAIPredictions(cityName);
      setAiPredictions(predictions);
      
      // Fetch historical data
      const historical = await apiService.getHistoricalData(cityName, 7);
      setHistoricalData(historical);
      
      // Fetch weather analytics
      const analytics = await apiService.getWeatherAnalytics(cityName, 7);
      setWeatherAnalytics(analytics);
      
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to fetch weather data:', err);
      setError('Failed to fetch weather data');
    } finally {
      setLoading(false);
    }
  };

  const fetchComparisonData = async () => {
    try {
      const comparison = await apiService.compareCities(cities.slice(0, 4));
      setComparisonData(comparison);
    } catch (err) {
      console.error('Failed to fetch comparison data:', err);
    }
  };

  const handleLogout = () => {
    apiService.logout();
    window.location.href = '/signin';
  };

  const refreshData = () => {
    fetchWeatherData(selectedCity);
    if (activeTab === 'comparison') {
      fetchComparisonData();
    }
  };

  const getWeatherIcon = (condition) => {
    const icons = {
      'Clear': <Sun className="h-8 w-8 text-yellow-500" />,
      'Clouds': <CloudRain className="h-8 w-8 text-gray-500" />,
      'Rain': <CloudRain className="h-8 w-8 text-blue-500" />,
      'Snow': <CloudRain className="h-8 w-8 text-blue-200" />,
    };
    return icons[condition] || <Sun className="h-8 w-8 text-yellow-500" />;
  };

  const getAQIColor = (aqi) => {
    if (aqi <= 2) return 'bg-green-500';
    if (aqi <= 3) return 'bg-yellow-500';
    if (aqi <= 4) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getAQILabel = (aqi) => {
    const labels = {
      1: 'Good',
      2: 'Fair',
      3: 'Moderate',
      4: 'Poor',
      5: 'Very Poor'
    };
    return labels[aqi] || 'Unknown';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <CloudRain className="h-8 w-8 text-blue-600" />
                <span className="text-2xl font-bold text-gray-800">Weather247</span>
              </div>
              
              {lastUpdated && (
                <Badge variant="outline" className="text-xs">
                  <Clock className="h-3 w-3 mr-1" />
                  Updated {lastUpdated.toLocaleTimeString()}
                </Badge>
              )}
            </div>
            
            <div className="flex items-center space-x-4">
              <Button 
                onClick={refreshData} 
                variant="outline" 
                size="sm"
                disabled={loading}
                className="flex items-center space-x-2"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </Button>
              
              <Button 
                onClick={() => window.location.href = '/route-planner'} 
                variant="outline" 
                className="flex items-center space-x-2"
              >
                <Route className="h-4 w-4" />
                <span>Route Planner</span>
              </Button>
              
              <Button onClick={handleLogout} variant="outline" className="flex items-center space-x-2">
                <LogOut className="h-4 w-4" />
                <span>Logout</span>
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md mb-6 flex items-center space-x-2"
          >
            <AlertTriangle className="h-5 w-5" />
            <span>{error}</span>
          </motion.div>
        )}

        {/* City Selection */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Globe className="h-5 w-5" />
              <span>Select City</span>
            </CardTitle>
            <CardDescription>Choose a city to view comprehensive weather data</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {cities.map((city) => (
                <Button
                  key={city}
                  onClick={() => setSelectedCity(city)}
                  variant={selectedCity === city ? "default" : "outline"}
                  className="justify-start"
                  size="sm"
                >
                  <MapPin className="h-4 w-4 mr-2" />
                  {city}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Main Dashboard Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview" className="flex items-center space-x-2">
              <Activity className="h-4 w-4" />
              <span>Overview</span>
            </TabsTrigger>
            <TabsTrigger value="predictions" className="flex items-center space-x-2">
              <Brain className="h-4 w-4" />
              <span>AI Predictions</span>
            </TabsTrigger>
            <TabsTrigger value="trends" className="flex items-center space-x-2">
              <TrendingUp className="h-4 w-4" />
              <span>Historical Trends</span>
            </TabsTrigger>
            <TabsTrigger value="comparison" className="flex items-center space-x-2" onClick={fetchComparisonData}>
              <BarChart3 className="h-4 w-4" />
              <span>City Comparison</span>
            </TabsTrigger>
            <TabsTrigger value="alerts" className="flex items-center space-x-2">
              <Bell className="h-4 w-4" />
              <span>Alerts</span>
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {weatherData && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                {/* Current Weather Hero Card */}
                <Card className="bg-gradient-to-br from-blue-500 to-cyan-500 text-white">
                  <CardContent className="p-8">
                    <div className="flex items-center justify-between">
                      <div>
                        <h2 className="text-3xl font-bold mb-2">{selectedCity}</h2>
                        <div className="flex items-center space-x-4 mb-4">
                          {weatherData.current && getWeatherIcon(weatherData.current.weather_condition)}
                          <div>
                            <div className="text-5xl font-bold">
                              {weatherData.current?.temperature}°C
                            </div>
                            <div className="text-lg opacity-90">
                              Feels like {weatherData.current?.feels_like}°C
                            </div>
                          </div>
                        </div>
                        <div className="text-lg capitalize opacity-90">
                          {weatherData.current?.weather_description}
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className="text-sm opacity-75 mb-2">Last Updated</div>
                        <div className="text-lg">
                          {new Date().toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Weather Metrics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <Card>
                    <CardContent className="p-6">
                      <div className="flex items-center space-x-4">
                        <div className="p-3 bg-blue-100 rounded-lg">
                          <Droplet className="h-6 w-6 text-blue-600" />
                        </div>
                        <div>
                          <div className="text-2xl font-bold">
                            {weatherData.current?.humidity}%
                          </div>
                          <div className="text-sm text-gray-600">Humidity</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-6">
                      <div className="flex items-center space-x-4">
                        <div className="p-3 bg-green-100 rounded-lg">
                          <Wind className="h-6 w-6 text-green-600" />
                        </div>
                        <div>
                          <div className="text-2xl font-bold">
                            {weatherData.current?.wind_speed} km/h
                          </div>
                          <div className="text-sm text-gray-600">Wind Speed</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-6">
                      <div className="flex items-center space-x-4">
                        <div className="p-3 bg-purple-100 rounded-lg">
                          <Gauge className="h-6 w-6 text-purple-600" />
                        </div>
                        <div>
                          <div className="text-2xl font-bold">
                            {weatherData.current?.pressure} hPa
                          </div>
                          <div className="text-sm text-gray-600">Pressure</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-6">
                      <div className="flex items-center space-x-4">
                        <div className="p-3 bg-orange-100 rounded-lg">
                          <Eye className="h-6 w-6 text-orange-600" />
                        </div>
                        <div>
                          <div className="text-2xl font-bold">
                            {weatherData.current?.visibility} km
                          </div>
                          <div className="text-sm text-gray-600">Visibility</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Air Quality and Forecast */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Air Quality */}
                  {weatherData.air_quality && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center space-x-2">
                          <Layers className="h-5 w-5" />
                          <span>Air Quality</span>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div className="flex items-center space-x-4">
                            <div className={`w-4 h-4 rounded-full ${getAQIColor(weatherData.air_quality.aqi)}`}></div>
                            <div>
                              <div className="text-2xl font-bold">AQI {weatherData.air_quality.aqi}</div>
                              <div className="text-sm text-gray-600">{getAQILabel(weatherData.air_quality.aqi)}</div>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>PM2.5: {weatherData.air_quality.pm2_5} μg/m³</div>
                            <div>PM10: {weatherData.air_quality.pm10} μg/m³</div>
                            <div>CO: {weatherData.air_quality.co} μg/m³</div>
                            <div>NO2: {weatherData.air_quality.no2} μg/m³</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* 5-Day Forecast */}
                  {weatherData.forecast && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center space-x-2">
                          <Calendar className="h-5 w-5" />
                          <span>5-Day Forecast</span>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {weatherData.forecast.slice(0, 5).map((day, index) => (
                            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                              <div className="flex items-center space-x-3">
                                {getWeatherIcon(day.weather_condition)}
                                <div>
                                  <div className="font-medium">
                                    {new Date(day.forecast_date).toLocaleDateString('en-US', { 
                                      weekday: 'short', 
                                      month: 'short', 
                                      day: 'numeric' 
                                    })}
                                  </div>
                                  <div className="text-sm text-gray-600 capitalize">
                                    {day.weather_description}
                                  </div>
                                </div>
                              </div>
                              <div className="text-right">
                                <div className="font-bold">
                                  {Math.round(day.temperature_max)}°/{Math.round(day.temperature_min)}°
                                </div>
                                <div className="text-sm text-gray-600">
                                  {day.precipitation_probability}% rain
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </motion.div>
            )}
          </TabsContent>

          {/* AI Predictions Tab */}
          <TabsContent value="predictions" className="space-y-6">
            {aiPredictions && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Brain className="h-5 w-5" />
                      <span>AI-Powered 24-Hour Predictions</span>
                    </CardTitle>
                    <CardDescription>
                      Advanced neural networks provide accurate weather forecasts with confidence intervals
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={aiPredictions.predictions?.slice(0, 12)}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="hour" />
                          <YAxis />
                          <Tooltip 
                            formatter={(value, name) => [
                              name === 'temperature' ? `${value}°C` : `${value}%`,
                              name === 'temperature' ? 'Temperature' : 'Confidence'
                            ]}
                          />
                          <Line 
                            type="monotone" 
                            dataKey="temperature" 
                            stroke="#3b82f6" 
                            strokeWidth={3}
                            dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                          />
                          <Line 
                            type="monotone" 
                            dataKey="confidence" 
                            stroke="#10b981" 
                            strokeWidth={2}
                            strokeDasharray="5 5"
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                    
                    <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      {aiPredictions.predictions?.slice(0, 4).map((prediction, index) => (
                        <div key={index} className="p-4 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg">
                          <div className="text-sm text-gray-600">+{prediction.hour}h</div>
                          <div className="text-2xl font-bold">{prediction.temperature}°C</div>
                          <div className="text-sm text-gray-600 capitalize">{prediction.condition}</div>
                          <div className="flex items-center space-x-1 mt-2">
                            <CheckCircle className="h-4 w-4 text-green-500" />
                            <span className="text-sm">{prediction.confidence}% confidence</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </TabsContent>

          {/* Historical Trends Tab */}
          <TabsContent value="trends" className="space-y-6">
            {historicalData && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <TrendingUp className="h-5 w-5" />
                      <span>Historical Weather Trends</span>
                    </CardTitle>
                    <CardDescription>
                      Analyze weather patterns over the past {historicalData.period}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80 mb-6">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={historicalData.data?.slice(-20)}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis 
                            dataKey="timestamp" 
                            tickFormatter={(value) => new Date(value).toLocaleDateString()}
                          />
                          <YAxis />
                          <Tooltip 
                            labelFormatter={(value) => new Date(value).toLocaleString()}
                            formatter={(value, name) => [
                              name === 'temperature' ? `${value}°C` : 
                              name === 'humidity' ? `${value}%` : `${value}`,
                              name.charAt(0).toUpperCase() + name.slice(1)
                            ]}
                          />
                          <Line 
                            type="monotone" 
                            dataKey="temperature" 
                            stroke="#ef4444" 
                            strokeWidth={2}
                            name="temperature"
                          />
                          <Line 
                            type="monotone" 
                            dataKey="humidity" 
                            stroke="#3b82f6" 
                            strokeWidth={2}
                            name="humidity"
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold">Temperature Trends</h3>
                        <div className="grid grid-cols-3 gap-4">
                          <div className="text-center p-3 bg-red-50 rounded-lg">
                            <div className="text-2xl font-bold text-red-600">
                              {historicalData.trends?.temperature.max}°C
                            </div>
                            <div className="text-sm text-gray-600">Max</div>
                          </div>
                          <div className="text-center p-3 bg-blue-50 rounded-lg">
                            <div className="text-2xl font-bold text-blue-600">
                              {historicalData.trends?.temperature.avg}°C
                            </div>
                            <div className="text-sm text-gray-600">Avg</div>
                          </div>
                          <div className="text-center p-3 bg-cyan-50 rounded-lg">
                            <div className="text-2xl font-bold text-cyan-600">
                              {historicalData.trends?.temperature.min}°C
                            </div>
                            <div className="text-sm text-gray-600">Min</div>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold">Humidity Trends</h3>
                        <div className="grid grid-cols-3 gap-4">
                          <div className="text-center p-3 bg-green-50 rounded-lg">
                            <div className="text-2xl font-bold text-green-600">
                              {historicalData.trends?.humidity.max}%
                            </div>
                            <div className="text-sm text-gray-600">Max</div>
                          </div>
                          <div className="text-center p-3 bg-yellow-50 rounded-lg">
                            <div className="text-2xl font-bold text-yellow-600">
                              {historicalData.trends?.humidity.avg}%
                            </div>
                            <div className="text-sm text-gray-600">Avg</div>
                          </div>
                          <div className="text-center p-3 bg-orange-50 rounded-lg">
                            <div className="text-2xl font-bold text-orange-600">
                              {historicalData.trends?.humidity.min}%
                            </div>
                            <div className="text-sm text-gray-600">Min</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </TabsContent>

          {/* City Comparison Tab */}
          <TabsContent value="comparison" className="space-y-6">
            {comparisonData && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <BarChart3 className="h-5 w-5" />
                      <span>Multi-City Weather Comparison</span>
                    </CardTitle>
                    <CardDescription>
                      Compare weather metrics across multiple cities side-by-side
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {/* Comparison Insights */}
                    {comparisonData.insights && (
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                        <div className="p-4 bg-red-50 rounded-lg text-center">
                          <div className="text-lg font-bold text-red-600">
                            {comparisonData.insights.warmest_city}
                          </div>
                          <div className="text-sm text-gray-600">Warmest City</div>
                        </div>
                        <div className="p-4 bg-blue-50 rounded-lg text-center">
                          <div className="text-lg font-bold text-blue-600">
                            {comparisonData.insights.coolest_city}
                          </div>
                          <div className="text-sm text-gray-600">Coolest City</div>
                        </div>
                        <div className="p-4 bg-green-50 rounded-lg text-center">
                          <div className="text-lg font-bold text-green-600">
                            {comparisonData.insights.temperature_range}°C
                          </div>
                          <div className="text-sm text-gray-600">Temperature Range</div>
                        </div>
                        <div className="p-4 bg-purple-50 rounded-lg text-center">
                          <div className="text-lg font-bold text-purple-600">
                            {comparisonData.insights.average_temperature}°C
                          </div>
                          <div className="text-sm text-gray-600">Average Temperature</div>
                        </div>
                      </div>
                    )}

                    {/* City Comparison Chart */}
                    <div className="h-80 mb-6">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={comparisonData.cities?.map(city => ({
                          city: city.city,
                          temperature: parseFloat(city.current.temperature),
                          humidity: parseFloat(city.current.humidity),
                          windSpeed: parseFloat(city.current.wind_speed)
                        }))}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="city" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="temperature" fill="#ef4444" name="Temperature (°C)" />
                          <Bar dataKey="humidity" fill="#3b82f6" name="Humidity (%)" />
                          <Bar dataKey="windSpeed" fill="#10b981" name="Wind Speed (km/h)" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>

                    {/* City Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      {comparisonData.cities?.map((city, index) => (
                        <Card key={index} className="relative overflow-hidden">
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between mb-3">
                              <h3 className="font-bold text-lg">{city.city}</h3>
                              {getWeatherIcon(city.current.weather_condition)}
                            </div>
                            
                            <div className="space-y-2">
                              <div className="flex justify-between">
                                <span className="text-sm text-gray-600">Temperature</span>
                                <span className="font-semibold">{city.current.temperature}°C</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-sm text-gray-600">Humidity</span>
                                <span className="font-semibold">{city.current.humidity}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-sm text-gray-600">Wind</span>
                                <span className="font-semibold">{city.current.wind_speed} km/h</span>
                              </div>
                              {city.air_quality && (
                                <div className="flex justify-between">
                                  <span className="text-sm text-gray-600">AQI</span>
                                  <Badge className={getAQIColor(city.air_quality.aqi)}>
                                    {city.air_quality.aqi}
                                  </Badge>
                                </div>
                              )}
                            </div>
                            
                            <div className="mt-3 text-xs text-gray-500 capitalize">
                              {city.current.weather_description}
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </TabsContent>

          {/* Alerts Tab */}
          <TabsContent value="alerts" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Bell className="h-5 w-5" />
                  <span>Weather Alerts & Notifications</span>
                </CardTitle>
                <CardDescription>
                  Configure intelligent alerts for severe weather conditions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <AlertTriangle className="h-5 w-5 text-yellow-600" />
                      <div>
                        <div className="font-semibold text-yellow-800">High Wind Alert</div>
                        <div className="text-sm text-yellow-700">
                          Wind speeds expected to reach 35 km/h in {selectedCity}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <CloudRain className="h-5 w-5 text-blue-600" />
                      <div>
                        <div className="font-semibold text-blue-800">Rain Forecast</div>
                        <div className="text-sm text-blue-700">
                          Light rain expected tomorrow afternoon
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6">
                    <h3 className="text-lg font-semibold mb-4">Alert Settings</h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <span>Temperature Alerts</span>
                        <Button variant="outline" size="sm">Configure</Button>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <span>Precipitation Alerts</span>
                        <Button variant="outline" size="sm">Configure</Button>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <span>Air Quality Alerts</span>
                        <Button variant="outline" size="sm">Configure</Button>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default ModernDashboard;
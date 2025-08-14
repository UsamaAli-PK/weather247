import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { CloudRain, MapPin, Thermometer, Droplet, Wind, Gauge, LogOut, Route, Plus } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import CitySearch from '../components/CitySearch';
import apiService from '../services/api';

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('authToken'));
  const [cities, setCities] = useState([]);
  const [selectedCity, setSelectedCity] = useState(null);
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (token) {
      fetchUserProfile();
      fetchCities();
    } else {
      // Redirect to sign-in if no token
      window.location.href = '/signin';
    }
  }, [token]);

  useEffect(() => {
    if (selectedCity) {
      fetchWeatherData(selectedCity.name);
    }
  }, [selectedCity]);

  const fetchUserProfile = async () => {
    try {
      const data = await apiService.getUserProfile();
      setUser(data);
    } catch (err) {
      console.error('Failed to fetch user profile:', err);
      setError('Failed to fetch user profile');
    }
  };

  const fetchCities = async () => {
    try {
      const data = await apiService.getCities();
      const cityList = data.results || data;
      setCities(cityList);
      if (cityList.length > 0) {
        setSelectedCity(cityList[0]);
      }
    } catch (err) {
      console.error('Failed to fetch cities:', err);
      setError('Failed to fetch cities');
    }
  };

  const fetchWeatherData = async (cityName) => {
    setLoading(true);
    try {
      const data = await apiService.getWeatherByCity(cityName);
      setWeatherData(data);
      setError('');
    } catch (err) {
      console.error('Failed to fetch weather data:', err);
      setError('Failed to fetch weather data');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    apiService.logout();
    window.location.href = '/signin';
  };

  const handleCityChange = (city) => {
    setSelectedCity(city);
  };

  const handleCityAdded = (newCity) => {
    setCities(prev => [...prev, newCity]);
    setSelectedCity(newCity);
  };

  const handleCitySelected = (city) => {
    if (city.exists) {
      const existingCity = cities.find(c => c.id === city.id);
      if (existingCity) {
        setSelectedCity(existingCity);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-2">
              <CloudRain className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-800">Weather247 Dashboard</span>
            </div>
            <div className="flex items-center space-x-4">
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
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        {/* City Selection and Search */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <MapPin className="h-5 w-5" />
                  <span>Select City</span>
                </CardTitle>
                <CardDescription>Choose a city to view weather information</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {cities.map((city) => (
                    <Button
                      key={city.id}
                      onClick={() => handleCityChange(city)}
                      variant={selectedCity?.id === city.id ? "default" : "outline"}
                      className="justify-start"
                    >
                      <MapPin className="h-4 w-4 mr-2" />
                      {city.name}, {city.country}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
          
          <div>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Plus className="h-5 w-5" />
                  <span>Add City</span>
                </CardTitle>
                <CardDescription>Search and add new cities</CardDescription>
              </CardHeader>
              <CardContent>
                <CitySearch 
                  onCityAdded={handleCityAdded}
                  onCitySelected={handleCitySelected}
                />
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Weather Information */}
        {selectedCity && (
          <div className="space-y-6">
            {loading ? (
              <Card>
                <CardContent className="p-8">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-2 text-gray-600">Loading weather data...</p>
                  </div>
                </CardContent>
              </Card>
            ) : weatherData ? (
              <>
                {/* Current Weather Card */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-2">
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center space-x-2">
                          <CloudRain className="h-5 w-5" />
                          <span>Current Weather in {selectedCity.name}</span>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        {weatherData.current && (
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg">
                              <div className="flex items-center space-x-2">
                                <Thermometer className="h-5 w-5 text-blue-600" />
                                <span className="font-medium text-blue-800">Temperature</span>
                              </div>
                              <p className="text-3xl font-bold text-blue-600 mt-2">
                                {Math.round(weatherData.current.temperature)}°C
                              </p>
                              <p className="text-sm text-blue-700">
                                Feels like {Math.round(weatherData.current.feels_like)}°C
                              </p>
                            </div>

                            <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg">
                              <div className="flex items-center space-x-2">
                                <Droplet className="h-5 w-5 text-green-600" />
                                <span className="font-medium text-green-800">Humidity</span>
                              </div>
                              <p className="text-3xl font-bold text-green-600 mt-2">
                                {weatherData.current.humidity}%
                              </p>
                            </div>

                            <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg">
                              <div className="flex items-center space-x-2">
                                <Wind className="h-5 w-5 text-purple-600" />
                                <span className="font-medium text-purple-800">Wind</span>
                              </div>
                              <p className="text-3xl font-bold text-purple-600 mt-2">
                                {Math.round(weatherData.current.wind_speed)}
                              </p>
                              <p className="text-sm text-purple-700">km/h</p>
                            </div>

                            <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-lg">
                              <div className="flex items-center space-x-2">
                                <Gauge className="h-5 w-5 text-orange-600" />
                                <span className="font-medium text-orange-800">Pressure</span>
                              </div>
                              <p className="text-3xl font-bold text-orange-600 mt-2">
                                {Math.round(weatherData.current.pressure)}
                              </p>
                              <p className="text-sm text-orange-700">hPa</p>
                            </div>
                          </div>
                        )}

                        {weatherData.current && (
                          <div className="mt-6 p-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-xl font-semibold text-gray-800 capitalize">
                                  {weatherData.current.weather_description}
                                </p>
                                <p className="text-gray-600">
                                  Visibility: {weatherData.current.visibility} km
                                </p>
                              </div>
                              <div className="text-right">
                                <p className="text-sm text-gray-600">Wind Direction</p>
                                <p className="text-lg font-semibold">{weatherData.current.wind_direction}°</p>
                              </div>
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>

                  {/* Air Quality Card */}
                  <div>
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Air Quality</CardTitle>
                      </CardHeader>
                      <CardContent>
                        {weatherData.air_quality ? (
                          <div className="space-y-4">
                            <div className="text-center">
                              <div className="text-3xl font-bold text-yellow-600">
                                {weatherData.air_quality.aqi}
                              </div>
                              <div className="text-sm text-gray-600">AQI Index</div>
                            </div>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span>PM2.5:</span>
                                <span>{weatherData.air_quality.pm2_5} μg/m³</span>
                              </div>
                              <div className="flex justify-between">
                                <span>PM10:</span>
                                <span>{weatherData.air_quality.pm10} μg/m³</span>
                              </div>
                              <div className="flex justify-between">
                                <span>CO:</span>
                                <span>{weatherData.air_quality.co} μg/m³</span>
                              </div>
                              <div className="flex justify-between">
                                <span>NO2:</span>
                                <span>{weatherData.air_quality.no2} μg/m³</span>
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="text-center text-gray-500 py-8">
                            <p>Air quality data</p>
                            <p>temporarily unavailable</p>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                </div>

                {/* Forecast Section */}
                {weatherData.forecast && weatherData.forecast.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>5-Day Forecast</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                        {weatherData.forecast.slice(0, 5).map((day, index) => (
                          <div key={index} className="bg-gradient-to-br from-blue-50 to-blue-100 border rounded-lg p-4 text-center hover:shadow-md transition-shadow">
                            <p className="font-medium text-sm text-blue-800 mb-2">
                              {new Date(day.forecast_date).toLocaleDateString('en-US', { 
                                weekday: 'short', 
                                month: 'short', 
                                day: 'numeric' 
                              })}
                            </p>
                            <p className="text-lg font-bold text-blue-900">
                              {Math.round(day.temperature_max)}°/{Math.round(day.temperature_min)}°
                            </p>
                            <p className="text-sm text-blue-700 mt-1 capitalize">{day.weather_condition}</p>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </>
            ) : (
              <div className="text-center py-8 text-gray-600">
                Select a city to view weather information
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;


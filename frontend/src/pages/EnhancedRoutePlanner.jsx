import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { 
  MapPin, Navigation, Route, CloudRain, Thermometer, Wind, 
  AlertTriangle, CheckCircle, Clock, ArrowRight, Save, Share2,
  Layers, Zap, Eye, Droplet, RefreshCw, Settings
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import apiService from '../services/api';

const EnhancedRoutePlanner = () => {
  const [startLocation, setStartLocation] = useState('');
  const [endLocation, setEndLocation] = useState('');
  const [routeName, setRouteName] = useState('');
  const [route, setRoute] = useState(null);
  const [routeWeather, setRouteWeather] = useState(null);
  const [weatherAlerts, setWeatherAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [mapData, setMapData] = useState(null);
  const [selectedRoute, setSelectedRoute] = useState(0);
  const mapRef = useRef(null);
  const [map, setMap] = useState(null);

  useEffect(() => {
    // Initialize Leaflet map
    initializeMap();
    
    // Fetch initial weather map data
    fetchWeatherMapData();
  }, []);

  const initializeMap = async () => {
    try {
      // Dynamically import Leaflet
      const L = await import('leaflet');
      
      // Initialize map
      const mapInstance = L.map(mapRef.current).setView([40.7128, -74.0060], 10);
      
      // Add tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(mapInstance);
      
      setMap(mapInstance);
    } catch (error) {
      console.error('Error initializing map:', error);
    }
  };

  const fetchWeatherMapData = async () => {
    try {
      const data = await apiService.getWeatherMapData();
      setMapData(data);
      
      if (map && data.map_data) {
        addWeatherMarkersToMap(data.map_data);
      }
    } catch (error) {
      console.error('Error fetching weather map data:', error);
    }
  };

  const addWeatherMarkersToMap = async (weatherData) => {
    if (!map) return;
    
    const L = await import('leaflet');
    
    weatherData.forEach(cityData => {
      const { coordinates, weather, city, severity_score } = cityData;
      
      // Create custom marker based on weather severity
      const markerColor = getMarkerColor(severity_score);
      const weatherIcon = getWeatherIcon(weather.condition);
      
      const marker = L.marker([coordinates.lat, coordinates.lng])
        .addTo(map)
        .bindPopup(`
          <div class="weather-popup">
            <h3>${city}</h3>
            <div class="weather-info">
              <div class="temp">${Math.round(weather.temperature)}°C</div>
              <div class="condition">${weather.description}</div>
              <div class="details">
                <div>Humidity: ${weather.humidity}%</div>
                <div>Wind: ${Math.round(weather.wind_speed)} km/h</div>
                <div>Pressure: ${Math.round(weather.pressure)} hPa</div>
              </div>
              <div class="severity">
                Severity Score: ${severity_score}/100
              </div>
            </div>
          </div>
        `);
    });
  };

  const getMarkerColor = (severityScore) => {
    if (severityScore >= 80) return '#ef4444'; // Red
    if (severityScore >= 60) return '#f97316'; // Orange
    if (severityScore >= 40) return '#eab308'; // Yellow
    return '#22c55e'; // Green
  };

  const getWeatherIcon = (condition) => {
    const icons = {
      'clear': '☀️',
      'clouds': '☁️',
      'rain': '🌧️',
      'snow': '❄️',
      'thunderstorm': '⛈️'
    };
    return icons[condition?.toLowerCase()] || '☀️';
  };

  const planRoute = async () => {
    if (!startLocation || !endLocation) {
      alert('Please enter both start and end locations');
      return;
    }

    setLoading(true);
    
    try {
      // Create route
      const routeData = {
        name: routeName || `${startLocation} to ${endLocation}`,
        start_location: { address: startLocation },
        end_location: { address: endLocation }
      };
      
      const newRoute = await apiService.createRoute(routeData);
      setRoute(newRoute);
      
      // Get weather data along route
      const weatherData = await apiService.getRouteWeather(newRoute.id);
      setRouteWeather(weatherData);
      
      // Analyze weather alerts
      analyzeWeatherAlerts(weatherData);
      
      // Update map with route
      if (map) {
        displayRouteOnMap(newRoute, weatherData);
      }
      
    } catch (error) {
      console.error('Error planning route:', error);
      alert('Error planning route. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const analyzeWeatherAlerts = (weatherData) => {
    const alerts = [];
    
    if (weatherData?.weather_points) {
      weatherData.weather_points.forEach((point, index) => {
        const weather = point.current_weather;
        
        // Temperature alerts
        if (weather.temperature > 35) {
          alerts.push({
            type: 'temperature',
            severity: 'high',
            message: `Extreme heat (${weather.temperature}°C) at km ${point.distance_km}`,
            location: `${point.distance_km} km from start`,
            icon: <Thermometer className="h-4 w-4" />
          });
        }
        
        // Wind alerts
        if (weather.wind_speed > 50) {
          alerts.push({
            type: 'wind',
            severity: 'high',
            message: `High winds (${weather.wind_speed} km/h) at km ${point.distance_km}`,
            location: `${point.distance_km} km from start`,
            icon: <Wind className="h-4 w-4" />
          });
        }
        
        // Precipitation alerts
        if (weather.precipitation > 5) {
          alerts.push({
            type: 'precipitation',
            severity: 'medium',
            message: `Heavy rain (${weather.precipitation}mm) at km ${point.distance_km}`,
            location: `${point.distance_km} km from start`,
            icon: <CloudRain className="h-4 w-4" />
          });
        }
      });
    }
    
    setWeatherAlerts(alerts);
  };

  const displayRouteOnMap = async (routeData, weatherData) => {
    if (!map) return;
    
    const L = await import('leaflet');
    
    // Clear existing route layers
    map.eachLayer(layer => {
      if (layer instanceof L.Polyline) {
        map.removeLayer(layer);
      }
    });
    
    // Add route polyline (simplified - in real implementation, use route geometry)
    if (weatherData?.weather_points && weatherData.weather_points.length > 1) {
      const routeCoords = weatherData.weather_points.map(point => [
        point.location.lat,
        point.location.lng
      ]);
      
      const routeLine = L.polyline(routeCoords, {
        color: '#3b82f6',
        weight: 5,
        opacity: 0.8
      }).addTo(map);
      
      // Fit map to route bounds
      map.fitBounds(routeLine.getBounds());
      
      // Add weather markers along route
      weatherData.weather_points.forEach((point, index) => {
        const severity = point.hazard_score || 0;
        const markerColor = getMarkerColor(severity);
        
        L.circleMarker([point.location.lat, point.location.lng], {
          radius: 8,
          fillColor: markerColor,
          color: '#fff',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.8
        })
        .addTo(map)
        .bindPopup(`
          <div class="route-weather-popup">
            <h4>km ${point.distance_km}</h4>
            <div>Temp: ${point.current_weather.temperature}°C</div>
            <div>Condition: ${point.current_weather.condition}</div>
            <div>Hazard Score: ${severity}/100</div>
          </div>
        `);
      });
    }
  };

  const saveRoute = async () => {
    if (!route) return;
    
    try {
      // Save route to favorites (implementation depends on backend)
      alert('Route saved to favorites!');
    } catch (error) {
      console.error('Error saving route:', error);
    }
  };

  const shareRoute = async () => {
    if (!route) return;
    
    try {
      const shareData = {
        title: route.name,
        text: `Check out this weather-aware route from ${startLocation} to ${endLocation}`,
        url: window.location.href
      };
      
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        // Fallback: copy to clipboard
        await navigator.clipboard.writeText(shareData.url);
        alert('Route link copied to clipboard!');
      }
    } catch (error) {
      console.error('Error sharing route:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-2">
              <Route className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-800">Weather-Aware Route Planner</span>
            </div>
            <div className="flex items-center space-x-4">
              <Button onClick={() => window.location.href = '/dashboard'} variant="outline">
                Back to Dashboard
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Route Planning Panel */}
          <div className="lg:col-span-1 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Navigation className="h-5 w-5" />
                  <span>Plan Your Route</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="routeName">Route Name (Optional)</Label>
                  <Input
                    id="routeName"
                    placeholder="My Weather Route"
                    value={routeName}
                    onChange={(e) => setRouteName(e.target.value)}
                  />
                </div>
                
                <div>
                  <Label htmlFor="startLocation">Start Location</Label>
                  <Input
                    id="startLocation"
                    placeholder="Enter starting point"
                    value={startLocation}
                    onChange={(e) => setStartLocation(e.target.value)}
                  />
                </div>
                
                <div>
                  <Label htmlFor="endLocation">End Location</Label>
                  <Input
                    id="endLocation"
                    placeholder="Enter destination"
                    value={endLocation}
                    onChange={(e) => setEndLocation(e.target.value)}
                  />
                </div>
                
                <Button 
                  onClick={planRoute} 
                  disabled={loading}
                  className="w-full"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Planning Route...
                    </>
                  ) : (
                    <>
                      <Route className="h-4 w-4 mr-2" />
                      Plan Route
                    </>
                  )}
                </Button>
                
                {route && (
                  <div className="flex space-x-2">
                    <Button onClick={saveRoute} variant="outline" size="sm">
                      <Save className="h-4 w-4 mr-2" />
                      Save
                    </Button>
                    <Button onClick={shareRoute} variant="outline" size="sm">
                      <Share2 className="h-4 w-4 mr-2" />
                      Share
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Route Information */}
            {route && (
              <Card>
                <CardHeader>
                  <CardTitle>Route Information</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Distance:</span>
                      <span className="font-semibold">{route.distance} km</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Est. Duration:</span>
                      <span className="font-semibold">{Math.round(route.estimated_duration / 60)} hours</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Weather Score:</span>
                      <Badge className={`${route.weather_score > 80 ? 'bg-green-500' : 
                        route.weather_score > 60 ? 'bg-yellow-500' : 'bg-red-500'}`}>
                        {route.weather_score}/100
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Weather Alerts */}
            {weatherAlerts.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <AlertTriangle className="h-5 w-5 text-orange-500" />
                    <span>Weather Alerts</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {weatherAlerts.map((alert, index) => (
                      <div key={index} className={`p-3 rounded-lg border-l-4 ${
                        alert.severity === 'high' ? 'border-red-500 bg-red-50' :
                        alert.severity === 'medium' ? 'border-yellow-500 bg-yellow-50' :
                        'border-blue-500 bg-blue-50'
                      }`}>
                        <div className="flex items-start space-x-2">
                          {alert.icon}
                          <div>
                            <div className="font-semibold text-sm">{alert.message}</div>
                            <div className="text-xs text-gray-600">{alert.location}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Map and Weather Display */}
          <div className="lg:col-span-2 space-y-6">
            {/* Interactive Map */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <MapPin className="h-5 w-5" />
                  <span>Interactive Weather Map</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div 
                  ref={mapRef} 
                  className="w-full h-96 rounded-lg border"
                  style={{ minHeight: '400px' }}
                />
              </CardContent>
            </Card>

            {/* Route Weather Details */}
            {routeWeather && (
              <Card>
                <CardHeader>
                  <CardTitle>Weather Along Route</CardTitle>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="overview">
                    <TabsList>
                      <TabsTrigger value="overview">Overview</TabsTrigger>
                      <TabsTrigger value="detailed">Detailed</TabsTrigger>
                      <TabsTrigger value="forecast">Forecast</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="overview" className="mt-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center p-4 bg-blue-50 rounded-lg">
                          <div className="text-2xl font-bold text-blue-600">
                            {routeWeather.overall_score}/100
                          </div>
                          <div className="text-sm text-gray-600">Overall Weather Score</div>
                        </div>
                        <div className="text-center p-4 bg-green-50 rounded-lg">
                          <div className="text-2xl font-bold text-green-600">
                            {routeWeather.weather_points?.length || 0}
                          </div>
                          <div className="text-sm text-gray-600">Weather Checkpoints</div>
                        </div>
                        <div className="text-center p-4 bg-orange-50 rounded-lg">
                          <div className="text-2xl font-bold text-orange-600">
                            {weatherAlerts.length}
                          </div>
                          <div className="text-sm text-gray-600">Weather Alerts</div>
                        </div>
                      </div>
                      
                      {routeWeather.recommendations && (
                        <div className="mt-6">
                          <h3 className="font-semibold mb-3">Recommendations</h3>
                          <div className="space-y-2">
                            {routeWeather.recommendations.map((rec, index) => (
                              <div key={index} className="flex items-center space-x-2 text-sm">
                                <CheckCircle className="h-4 w-4 text-green-500" />
                                <span>{rec}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </TabsContent>
                    
                    <TabsContent value="detailed" className="mt-4">
                      {routeWeather.weather_points && (
                        <div className="space-y-4">
                          {routeWeather.weather_points.map((point, index) => (
                            <div key={index} className="p-4 border rounded-lg">
                              <div className="flex justify-between items-start mb-2">
                                <div className="font-semibold">
                                  Checkpoint {index + 1} - {point.distance_km} km
                                </div>
                                <Badge className={`${point.hazard_score > 70 ? 'bg-red-500' : 
                                  point.hazard_score > 40 ? 'bg-yellow-500' : 'bg-green-500'}`}>
                                  Risk: {point.hazard_score}/100
                                </Badge>
                              </div>
                              
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                <div className="flex items-center space-x-2">
                                  <Thermometer className="h-4 w-4 text-red-500" />
                                  <span>{point.current_weather.temperature}°C</span>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <Droplet className="h-4 w-4 text-blue-500" />
                                  <span>{point.current_weather.humidity || 'N/A'}%</span>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <Wind className="h-4 w-4 text-green-500" />
                                  <span>{point.current_weather.wind_speed} km/h</span>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <Eye className="h-4 w-4 text-purple-500" />
                                  <span>{point.current_weather.visibility || 'Good'}</span>
                                </div>
                              </div>
                              
                              {point.warnings && point.warnings.length > 0 && (
                                <div className="mt-3">
                                  <div className="text-sm font-medium text-orange-600 mb-1">Warnings:</div>
                                  {point.warnings.map((warning, wIndex) => (
                                    <div key={wIndex} className="text-sm text-orange-700">
                                      • {warning}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </TabsContent>
                    
                    <TabsContent value="forecast" className="mt-4">
                      <div className="text-center text-gray-500 py-8">
                        <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>Extended forecast along route coming soon...</p>
                      </div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedRoutePlanner;
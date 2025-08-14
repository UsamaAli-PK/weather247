import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { MapPin, Navigation, Route, AlertTriangle, Clock, Thermometer, Droplet, Wind, Eye, Save, Trash2, RefreshCw } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const RoutePlanner = () => {
  const [token, setToken] = useState(localStorage.getItem('authToken'));
  const [startLocation, setStartLocation] = useState('');
  const [endLocation, setEndLocation] = useState('');
  const [startCoords, setStartCoords] = useState(null);
  const [endCoords, setEndCoords] = useState(null);
  const [currentRoute, setCurrentRoute] = useState(null);
  const [savedRoutes, setSavedRoutes] = useState([]);
  const [weatherPoints, setWeatherPoints] = useState([]);
  const [routeAlerts, setRouteAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [routeName, setRouteName] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const routeLayerRef = useRef(null);
  const markersRef = useRef([]);

  const API_BASE_URL = 'http://localhost:8000/api'; // Replace with your Django backend URL

  useEffect(() => {
    if (!token) {
      window.location.href = '/signin';
      return;
    }

    // Initialize map
    if (mapRef.current && !mapInstanceRef.current) {
      mapInstanceRef.current = L.map(mapRef.current).setView([40.7128, -74.0060], 10); // Default to NYC
      
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(mapInstanceRef.current);

      // Add click event to map for setting waypoints
      mapInstanceRef.current.on('click', handleMapClick);
    }

    fetchSavedRoutes();

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [token]);

  const fetchSavedRoutes = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/routes/routes/`, {
        headers: {
          'Authorization': `Token ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSavedRoutes(data);
      } else {
        setError('Failed to fetch saved routes');
      }
    } catch (err) {
      setError('Network error fetching routes');
    }
  };

  const handleMapClick = (e) => {
    const { lat, lng } = e.latlng;
    
    if (!startCoords) {
      setStartCoords({ latitude: lat, longitude: lng });
      setStartLocation(`${lat.toFixed(4)}, ${lng.toFixed(4)}`);
      
      // Add start marker
      const marker = L.marker([lat, lng])
        .addTo(mapInstanceRef.current)
        .bindPopup('Start Location')
        .openPopup();
      markersRef.current.push(marker);
    } else if (!endCoords) {
      setEndCoords({ latitude: lat, longitude: lng });
      setEndLocation(`${lat.toFixed(4)}, ${lng.toFixed(4)}`);
      
      // Add end marker
      const marker = L.marker([lat, lng])
        .addTo(mapInstanceRef.current)
        .bindPopup('End Location')
        .openPopup();
      markersRef.current.push(marker);
    }
  };

  const geocodeLocation = async (location) => {
    try {
      const response = await fetch(`${API_BASE_URL}/routes/geocode/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`
        },
        body: JSON.stringify({ location })
      });
      
      if (response.ok) {
        const data = await response.json();
        return { latitude: data.latitude, longitude: data.longitude };
      } else {
        throw new Error('Location not found');
      }
    } catch (err) {
      throw new Error(`Geocoding failed: ${err.message}`);
    }
  };

  const handleLocationSearch = async (locationType) => {
    const location = locationType === 'start' ? startLocation : endLocation;
    if (!location) return;

    setLoading(true);
    setError('');

    try {
      const coords = await geocodeLocation(location);
      
      if (locationType === 'start') {
        setStartCoords(coords);
        // Add start marker
        clearMarkers();
        const marker = L.marker([coords.latitude, coords.longitude])
          .addTo(mapInstanceRef.current)
          .bindPopup(`Start: ${location}`)
          .openPopup();
        markersRef.current.push(marker);
        mapInstanceRef.current.setView([coords.latitude, coords.longitude], 12);
      } else {
        setEndCoords(coords);
        // Add end marker
        const marker = L.marker([coords.latitude, coords.longitude])
          .addTo(mapInstanceRef.current)
          .bindPopup(`End: ${location}`)
          .openPopup();
        markersRef.current.push(marker);
        
        // Fit map to show both markers
        if (startCoords) {
          const group = new L.featureGroup(markersRef.current);
          mapInstanceRef.current.fitBounds(group.getBounds().pad(0.1));
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const clearMarkers = () => {
    markersRef.current.forEach(marker => {
      mapInstanceRef.current.removeLayer(marker);
    });
    markersRef.current = [];
  };

  const clearRoute = () => {
    if (routeLayerRef.current) {
      mapInstanceRef.current.removeLayer(routeLayerRef.current);
      routeLayerRef.current = null;
    }
  };

  const createRouteWithWeather = async () => {
    if (!startCoords || !endCoords) {
      setError('Please set both start and end locations');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/routes/routes/create_with_weather/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`
        },
        body: JSON.stringify({
          name: routeName || `${startLocation} to ${endLocation}`,
          start_location: startLocation,
          end_location: endLocation,
          start_latitude: startCoords.latitude,
          start_longitude: startCoords.longitude,
          end_latitude: endCoords.latitude,
          end_longitude: endCoords.longitude
        })
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentRoute(data);
        setWeatherPoints(data.weather_points || []);
        setRouteAlerts(data.alerts || []);
        
        // Draw route on map
        drawRouteOnMap(data.waypoints);
        
        // Add weather markers
        addWeatherMarkersToMap(data.weather_points || []);
        
        await fetchSavedRoutes(); // Refresh saved routes
      } else {
        const errData = await response.json();
        setError(errData.error || 'Failed to create route');
      }
    } catch (err) {
      setError('Network error creating route');
    } finally {
      setLoading(false);
    }
  };

  const drawRouteOnMap = (waypoints) => {
    if (!waypoints || waypoints.length === 0) return;

    clearRoute();
    
    const latLngs = waypoints.map(point => [point[0], point[1]]);
    routeLayerRef.current = L.polyline(latLngs, { color: 'blue', weight: 4 }).addTo(mapInstanceRef.current);
    
    // Fit map to route
    mapInstanceRef.current.fitBounds(routeLayerRef.current.getBounds().pad(0.1));
  };

  const addWeatherMarkersToMap = (weatherPoints) => {
    weatherPoints.forEach((point, index) => {
      const weatherIcon = getWeatherIcon(point.weather_condition);
      const marker = L.marker([point.latitude, point.longitude], {
        icon: L.divIcon({
          html: `<div style="background: white; border-radius: 50%; padding: 4px; border: 2px solid #3b82f6;">${weatherIcon}</div>`,
          className: 'weather-marker',
          iconSize: [30, 30]
        })
      })
      .addTo(mapInstanceRef.current)
      .bindPopup(`
        <div>
          <strong>Weather at ${point.distance_from_start_km.toFixed(1)}km</strong><br/>
          Temperature: ${point.temperature}°C<br/>
          Humidity: ${point.humidity}%<br/>
          Wind: ${point.wind_speed} km/h<br/>
          Condition: ${point.weather_description}
        </div>
      `);
      
      markersRef.current.push(marker);
    });
  };

  const getWeatherIcon = (condition) => {
    const iconMap = {
      'Clear': '☀️',
      'Clouds': '☁️',
      'Rain': '🌧️',
      'Drizzle': '🌦️',
      'Thunderstorm': '⛈️',
      'Snow': '❄️',
      'Mist': '🌫️',
      'Fog': '🌫️'
    };
    return iconMap[condition] || '🌤️';
  };

  const loadSavedRoute = async (routeId) => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/routes/routes/${routeId}/`, {
        headers: {
          'Authorization': `Token ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentRoute(data);
        setWeatherPoints(data.weather_points || []);
        setRouteAlerts(data.alerts || []);
        setStartLocation(data.start_location);
        setEndLocation(data.end_location);
        setStartCoords({ latitude: data.start_latitude, longitude: data.start_longitude });
        setEndCoords({ latitude: data.end_latitude, longitude: data.end_longitude });
        
        // Clear existing markers and route
        clearMarkers();
        clearRoute();
        
        // Add start and end markers
        const startMarker = L.marker([data.start_latitude, data.start_longitude])
          .addTo(mapInstanceRef.current)
          .bindPopup(`Start: ${data.start_location}`);
        const endMarker = L.marker([data.end_latitude, data.end_longitude])
          .addTo(mapInstanceRef.current)
          .bindPopup(`End: ${data.end_location}`);
        markersRef.current.push(startMarker, endMarker);
        
        // Draw route and weather markers
        drawRouteOnMap(data.waypoints);
        addWeatherMarkersToMap(data.weather_points || []);
      } else {
        setError('Failed to load route');
      }
    } catch (err) {
      setError('Network error loading route');
    } finally {
      setLoading(false);
    }
  };

  const refreshRouteWeather = async () => {
    if (!currentRoute) return;

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/routes/routes/${currentRoute.id}/weather/`, {
        headers: {
          'Authorization': `Token ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setWeatherPoints(data.weather_points || []);
        setRouteAlerts(data.alerts || []);
        
        // Update weather markers
        clearMarkers();
        const startMarker = L.marker([data.start_latitude, data.start_longitude])
          .addTo(mapInstanceRef.current)
          .bindPopup(`Start: ${data.start_location}`);
        const endMarker = L.marker([data.end_latitude, data.end_longitude])
          .addTo(mapInstanceRef.current)
          .bindPopup(`End: ${data.end_location}`);
        markersRef.current.push(startMarker, endMarker);
        addWeatherMarkersToMap(data.weather_points || []);
      } else {
        setError('Failed to refresh weather data');
      }
    } catch (err) {
      setError('Network error refreshing weather');
    } finally {
      setLoading(false);
    }
  };

  const deleteRoute = async (routeId) => {
    if (!confirm('Are you sure you want to delete this route?')) return;

    try {
      const response = await fetch(`${API_BASE_URL}/routes/routes/${routeId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Token ${token}`
        }
      });

      if (response.ok) {
        await fetchSavedRoutes();
        if (currentRoute && currentRoute.id === routeId) {
          setCurrentRoute(null);
          setWeatherPoints([]);
          setRouteAlerts([]);
          clearMarkers();
          clearRoute();
        }
      } else {
        setError('Failed to delete route');
      }
    } catch (err) {
      setError('Network error deleting route');
    }
  };

  const resetForm = () => {
    setStartLocation('');
    setEndLocation('');
    setStartCoords(null);
    setEndCoords(null);
    setCurrentRoute(null);
    setWeatherPoints([]);
    setRouteAlerts([]);
    setRouteName('');
    clearMarkers();
    clearRoute();
  };

  const getSeverityColor = (severity) => {
    const colors = {
      'low': 'text-yellow-600 bg-yellow-50 border-yellow-200',
      'medium': 'text-orange-600 bg-orange-50 border-orange-200',
      'high': 'text-red-600 bg-red-50 border-red-200',
      'severe': 'text-red-800 bg-red-100 border-red-300'
    };
    return colors[severity] || colors['medium'];
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <motion.div 
          className="flex items-center space-x-2"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Route className="h-8 w-8 text-blue-600" />
          <span className="text-2xl font-bold text-gray-800">Route Planner</span>
        </motion.div>
        <Button onClick={() => window.location.href = '/dashboard'} variant="outline">Back to Dashboard</Button>
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm mb-6"
        >
          {error}
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Route Planning Panel */}
        <Card className="lg:col-span-1 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center"><Navigation className="mr-2" /> Plan Route</CardTitle>
            <CardDescription>Create a new route with weather information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="start">Start Location</Label>
              <div className="flex space-x-2">
                <Input 
                  id="start"
                  placeholder="Enter start location"
                  value={startLocation}
                  onChange={(e) => setStartLocation(e.target.value)}
                />
                <Button onClick={() => handleLocationSearch('start')} disabled={loading}>
                  <MapPin className="h-4 w-4" />
                </Button>
              </div>
            </div>
            
            <div>
              <Label htmlFor="end">End Location</Label>
              <div className="flex space-x-2">
                <Input 
                  id="end"
                  placeholder="Enter end location"
                  value={endLocation}
                  onChange={(e) => setEndLocation(e.target.value)}
                />
                <Button onClick={() => handleLocationSearch('end')} disabled={loading}>
                  <MapPin className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div>
              <Label htmlFor="routeName">Route Name (Optional)</Label>
              <Input 
                id="routeName"
                placeholder="My Route"
                value={routeName}
                onChange={(e) => setRouteName(e.target.value)}
              />
            </div>

            <div className="flex space-x-2">
              <Button onClick={createRouteWithWeather} disabled={loading || !startCoords || !endCoords} className="flex-1">
                {loading ? 'Creating...' : 'Create Route'}
              </Button>
              <Button onClick={resetForm} variant="outline">Reset</Button>
            </div>

            {currentRoute && (
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <h3 className="font-semibold text-blue-800">{currentRoute.name}</h3>
                <p className="text-sm text-blue-600">Distance: {currentRoute.distance_km?.toFixed(1)} km</p>
                <p className="text-sm text-blue-600">Duration: {currentRoute.estimated_duration_minutes?.toFixed(0)} minutes</p>
                <Button onClick={refreshRouteWeather} disabled={loading} className="mt-2" size="sm">
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Refresh Weather
                </Button>
              </div>
            )}

            <div className="text-xs text-gray-500 mt-4">
              <p>💡 Tip: Click on the map to set start and end points, or use the search boxes above.</p>
            </div>
          </CardContent>
        </Card>

        {/* Map */}
        <Card className="lg:col-span-2 shadow-lg">
          <CardHeader>
            <CardTitle>Interactive Map</CardTitle>
            <CardDescription>View your route with weather information</CardDescription>
          </CardHeader>
          <CardContent>
            <div ref={mapRef} style={{ height: '500px', width: '100%' }} className="rounded-lg"></div>
          </CardContent>
        </Card>

        {/* Weather Information */}
        {weatherPoints.length > 0 && (
          <Card className="lg:col-span-3 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center"><Thermometer className="mr-2" /> Weather Along Route</CardTitle>
              <CardDescription>Current weather conditions at key points</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {weatherPoints.map((point, index) => (
                  <Card key={index} className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">
                        {point.distance_from_start_km.toFixed(1)} km
                      </span>
                      <span className="text-2xl">{getWeatherIcon(point.weather_condition)}</span>
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex items-center">
                        <Thermometer className="h-4 w-4 mr-1 text-red-500" />
                        {point.temperature}°C
                      </div>
                      <div className="flex items-center">
                        <Droplet className="h-4 w-4 mr-1 text-blue-500" />
                        {point.humidity}%
                      </div>
                      <div className="flex items-center">
                        <Wind className="h-4 w-4 mr-1 text-green-500" />
                        {point.wind_speed} km/h
                      </div>
                      {point.visibility && (
                        <div className="flex items-center">
                          <Eye className="h-4 w-4 mr-1 text-gray-500" />
                          {point.visibility} km
                        </div>
                      )}
                      <p className="text-xs text-gray-600 mt-1">{point.weather_description}</p>
                    </div>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Route Alerts */}
        {routeAlerts.length > 0 && (
          <Card className="lg:col-span-3 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center"><AlertTriangle className="mr-2" /> Weather Alerts</CardTitle>
              <CardDescription>Important weather conditions that may affect your journey</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {routeAlerts.map((alert, index) => (
                  <div key={index} className={`p-4 rounded-lg border ${getSeverityColor(alert.severity)}`}>
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-semibold capitalize">{alert.alert_type} Alert</h4>
                        <p className="text-sm mt-1">{alert.message}</p>
                        <p className="text-xs mt-2">
                          Location: {alert.distance_from_start_km.toFixed(1)} km from start
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                        {alert.severity.toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Saved Routes */}
        <Card className="lg:col-span-3 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center"><Save className="mr-2" /> Saved Routes</CardTitle>
            <CardDescription>Your previously saved routes</CardDescription>
          </CardHeader>
          <CardContent>
            {savedRoutes.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {savedRoutes.map((route) => (
                  <Card key={route.id} className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-semibold">{route.name}</h4>
                        <p className="text-sm text-gray-600">{route.start_location} → {route.end_location}</p>
                        <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                          <span className="flex items-center">
                            <Route className="h-3 w-3 mr-1" />
                            {route.distance_km?.toFixed(1)} km
                          </span>
                          <span className="flex items-center">
                            <Clock className="h-3 w-3 mr-1" />
                            {route.estimated_duration_minutes?.toFixed(0)} min
                          </span>
                        </div>
                      </div>
                      <div className="flex space-x-1">
                        <Button onClick={() => loadSavedRoute(route.id)} size="sm" variant="outline">
                          Load
                        </Button>
                        <Button onClick={() => deleteRoute(route.id)} size="sm" variant="outline">
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No saved routes yet. Create your first route above!</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default RoutePlanner;


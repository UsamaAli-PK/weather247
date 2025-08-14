import React from 'react';
import { motion } from 'framer-motion';
import { 
  Thermometer, Droplet, Wind, Gauge, Eye, Sun, Cloud, CloudRain, 
  CloudSnow, Zap, AlertTriangle, TrendingUp, TrendingDown 
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';

const WeatherCard = ({ weatherData, city, isSelected, onClick, showDetails = false }) => {
  const getWeatherIcon = (condition, size = 'h-8 w-8') => {
    const iconClass = `${size} ${getWeatherColor(condition)}`;
    
    switch (condition?.toLowerCase()) {
      case 'clear':
        return <Sun className={iconClass} />;
      case 'clouds':
        return <Cloud className={iconClass} />;
      case 'rain':
      case 'drizzle':
        return <CloudRain className={iconClass} />;
      case 'snow':
        return <CloudSnow className={iconClass} />;
      case 'thunderstorm':
        return <Zap className={iconClass} />;
      default:
        return <Sun className={iconClass} />;
    }
  };

  const getWeatherColor = (condition) => {
    switch (condition?.toLowerCase()) {
      case 'clear':
        return 'text-yellow-500';
      case 'clouds':
        return 'text-gray-500';
      case 'rain':
      case 'drizzle':
        return 'text-blue-500';
      case 'snow':
        return 'text-blue-200';
      case 'thunderstorm':
        return 'text-purple-500';
      default:
        return 'text-yellow-500';
    }
  };

  const getTemperatureColor = (temp) => {
    if (temp >= 30) return 'text-red-500';
    if (temp >= 20) return 'text-orange-500';
    if (temp >= 10) return 'text-green-500';
    if (temp >= 0) return 'text-blue-500';
    return 'text-blue-700';
  };

  const getAQIColor = (aqi) => {
    if (aqi <= 2) return 'bg-green-500';
    if (aqi <= 3) return 'bg-yellow-500';
    if (aqi <= 4) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getAQILabel = (aqi) => {
    const labels = { 1: 'Good', 2: 'Fair', 3: 'Moderate', 4: 'Poor', 5: 'Very Poor' };
    return labels[aqi] || 'Unknown';
  };

  if (!weatherData?.current) {
    return (
      <Card className={`cursor-pointer transition-all duration-300 ${isSelected ? 'ring-2 ring-blue-500' : ''}`} onClick={onClick}>
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
          <div className="text-center mt-4">
            <h3 className="font-bold text-lg">{city}</h3>
            <p className="text-gray-500">Loading...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const current = weatherData.current;
  const airQuality = weatherData.air_quality;

  return (
    <motion.div
      whileHover={{ y: -5 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.2 }}
    >
      <Card 
        className={`cursor-pointer transition-all duration-300 hover:shadow-lg ${
          isSelected ? 'ring-2 ring-blue-500 shadow-lg' : ''
        }`} 
        onClick={onClick}
      >
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-bold">{city}</CardTitle>
            {getWeatherIcon(current.weather_condition)}
          </div>
        </CardHeader>
        
        <CardContent className="pt-0">
          {/* Temperature Display */}
          <div className="mb-4">
            <div className={`text-4xl font-bold ${getTemperatureColor(current.temperature)}`}>
              {Math.round(current.temperature)}°C
            </div>
            <div className="text-sm text-gray-600">
              Feels like {Math.round(current.feels_like)}°C
            </div>
            <div className="text-sm text-gray-500 capitalize mt-1">
              {current.weather_description}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="flex items-center space-x-2">
              <Droplet className="h-4 w-4 text-blue-500" />
              <span className="text-sm">{current.humidity}%</span>
            </div>
            <div className="flex items-center space-x-2">
              <Wind className="h-4 w-4 text-green-500" />
              <span className="text-sm">{Math.round(current.wind_speed)} km/h</span>
            </div>
            <div className="flex items-center space-x-2">
              <Gauge className="h-4 w-4 text-purple-500" />
              <span className="text-sm">{Math.round(current.pressure)} hPa</span>
            </div>
            <div className="flex items-center space-x-2">
              <Eye className="h-4 w-4 text-orange-500" />
              <span className="text-sm">{current.visibility} km</span>
            </div>
          </div>

          {/* Air Quality */}
          {airQuality && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Air Quality</span>
              <Badge className={`${getAQIColor(airQuality.aqi)} text-white`}>
                AQI {airQuality.aqi} - {getAQILabel(airQuality.aqi)}
              </Badge>
            </div>
          )}

          {/* Detailed View */}
          {showDetails && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mt-4 pt-4 border-t border-gray-200"
            >
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>UV Index: {current.uv_index || 'N/A'}</div>
                <div>Wind Dir: {current.wind_direction}°</div>
                {airQuality && (
                  <>
                    <div>PM2.5: {airQuality.pm2_5} μg/m³</div>
                    <div>PM10: {airQuality.pm10} μg/m³</div>
                  </>
                )}
              </div>
            </motion.div>
          )}

          {/* Weather Alerts */}
          {current.temperature > 35 && (
            <div className="mt-3 flex items-center space-x-2 text-red-600">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-xs">Extreme Heat Warning</span>
            </div>
          )}
          
          {current.wind_speed > 50 && (
            <div className="mt-2 flex items-center space-x-2 text-orange-600">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-xs">High Wind Alert</span>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default WeatherCard;
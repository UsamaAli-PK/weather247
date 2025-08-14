import React, { useState, useMemo } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, AreaChart, Area, PieChart, Pie, Cell, Legend
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  TrendingUp, TrendingDown, BarChart3, LineChart as LineChartIcon,
  PieChart as PieChartIcon, Download, Maximize2
} from 'lucide-react';

const WeatherChart = ({ 
  data, 
  title, 
  type = 'line', 
  metrics = ['temperature'], 
  timeRange = '24h',
  showControls = true,
  height = 300 
}) => {
  const [chartType, setChartType] = useState(type);
  const [selectedMetrics, setSelectedMetrics] = useState(metrics);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const colors = {
    temperature: '#ef4444',
    humidity: '#3b82f6',
    pressure: '#8b5cf6',
    wind_speed: '#10b981',
    precipitation: '#06b6d4',
    aqi: '#f59e0b'
  };

  const formatData = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];
    
    return data.map(item => ({
      ...item,
      time: new Date(item.timestamp || item.time || item.datetime).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
      }),
      date: new Date(item.timestamp || item.time || item.datetime).toLocaleDateString(),
      temperature: parseFloat(item.temperature || 0),
      humidity: parseFloat(item.humidity || 0),
      pressure: parseFloat(item.pressure || 0),
      wind_speed: parseFloat(item.wind_speed || 0),
      precipitation: parseFloat(item.precipitation || 0),
      aqi: parseInt(item.aqi || 0)
    }));
  }, [data]);

  const calculateTrend = (metric) => {
    if (formatData.length < 2) return 0;
    const first = formatData[0][metric] || 0;
    const last = formatData[formatData.length - 1][metric] || 0;
    return ((last - first) / first * 100).toFixed(1);
  };

  const getMetricUnit = (metric) => {
    const units = {
      temperature: '°C',
      humidity: '%',
      pressure: 'hPa',
      wind_speed: 'km/h',
      precipitation: 'mm',
      aqi: ''
    };
    return units[metric] || '';
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {entry.value}{getMetricUnit(entry.dataKey)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const renderChart = () => {
    const commonProps = {
      data: formatData,
      margin: { top: 5, right: 30, left: 20, bottom: 5 }
    };

    switch (chartType) {
      case 'line':
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="time" stroke="#666" fontSize={12} />
            <YAxis stroke="#666" fontSize={12} />
            <Tooltip content={<CustomTooltip />} />
            {selectedMetrics.map(metric => (
              <Line
                key={metric}
                type="monotone"
                dataKey={metric}
                stroke={colors[metric]}
                strokeWidth={2}
                dot={{ fill: colors[metric], strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, stroke: colors[metric], strokeWidth: 2 }}
              />
            ))}
          </LineChart>
        );

      case 'area':
        return (
          <AreaChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="time" stroke="#666" fontSize={12} />
            <YAxis stroke="#666" fontSize={12} />
            <Tooltip content={<CustomTooltip />} />
            {selectedMetrics.map(metric => (
              <Area
                key={metric}
                type="monotone"
                dataKey={metric}
                stroke={colors[metric]}
                fill={colors[metric]}
                fillOpacity={0.3}
                strokeWidth={2}
              />
            ))}
          </AreaChart>
        );

      case 'bar':
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="time" stroke="#666" fontSize={12} />
            <YAxis stroke="#666" fontSize={12} />
            <Tooltip content={<CustomTooltip />} />
            {selectedMetrics.map(metric => (
              <Bar
                key={metric}
                dataKey={metric}
                fill={colors[metric]}
                radius={[2, 2, 0, 0]}
              />
            ))}
          </BarChart>
        );

      default:
        return null;
    }
  };

  const exportChart = () => {
    // Implementation for chart export
    const csvData = formatData.map(item => 
      selectedMetrics.reduce((acc, metric) => ({
        ...acc,
        time: item.time,
        [metric]: item[metric]
      }), {})
    );
    
    const csvContent = [
      Object.keys(csvData[0]).join(','),
      ...csvData.map(row => Object.values(row).join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `weather-data-${Date.now()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <Card className={`${isFullscreen ? 'fixed inset-4 z-50' : ''}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <span>{title}</span>
              {selectedMetrics.map(metric => {
                const trend = calculateTrend(metric);
                return (
                  <Badge key={metric} variant="outline" className="ml-2">
                    {trend > 0 ? (
                      <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
                    ) : (
                      <TrendingDown className="h-3 w-3 text-red-500 mr-1" />
                    )}
                    {Math.abs(trend)}%
                  </Badge>
                );
              })}
            </CardTitle>
          </div>
          
          {showControls && (
            <div className="flex items-center space-x-2">
              {/* Chart Type Controls */}
              <div className="flex space-x-1">
                <Button
                  variant={chartType === 'line' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setChartType('line')}
                >
                  <LineChartIcon className="h-4 w-4" />
                </Button>
                <Button
                  variant={chartType === 'bar' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setChartType('bar')}
                >
                  <BarChart3 className="h-4 w-4" />
                </Button>
                <Button
                  variant={chartType === 'area' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setChartType('area')}
                >
                  <PieChartIcon className="h-4 w-4" />
                </Button>
              </div>
              
              {/* Export Button */}
              <Button variant="outline" size="sm" onClick={exportChart}>
                <Download className="h-4 w-4" />
              </Button>
              
              {/* Fullscreen Button */}
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setIsFullscreen(!isFullscreen)}
              >
                <Maximize2 className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
        
        {/* Metric Selection */}
        {showControls && (
          <div className="flex flex-wrap gap-2 mt-3">
            {Object.keys(colors).map(metric => (
              <Button
                key={metric}
                variant={selectedMetrics.includes(metric) ? 'default' : 'outline'}
                size="sm"
                onClick={() => {
                  if (selectedMetrics.includes(metric)) {
                    setSelectedMetrics(selectedMetrics.filter(m => m !== metric));
                  } else {
                    setSelectedMetrics([...selectedMetrics, metric]);
                  }
                }}
                style={{
                  backgroundColor: selectedMetrics.includes(metric) ? colors[metric] : 'transparent',
                  borderColor: colors[metric],
                  color: selectedMetrics.includes(metric) ? 'white' : colors[metric]
                }}
              >
                {metric.replace('_', ' ').toUpperCase()}
              </Button>
            ))}
          </div>
        )}
      </CardHeader>
      
      <CardContent>
        <div style={{ height: isFullscreen ? 'calc(100vh - 200px)' : height }}>
          <ResponsiveContainer width="100%" height="100%">
            {renderChart()}
          </ResponsiveContainer>
        </div>
        
        {/* Chart Statistics */}
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          {selectedMetrics.map(metric => {
            const values = formatData.map(d => d[metric]).filter(v => v !== undefined);
            const avg = values.reduce((a, b) => a + b, 0) / values.length;
            const max = Math.max(...values);
            const min = Math.min(...values);
            
            return (
              <div key={metric} className="text-center p-2 bg-gray-50 rounded">
                <div className="font-semibold" style={{ color: colors[metric] }}>
                  {metric.replace('_', ' ').toUpperCase()}
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  Avg: {avg.toFixed(1)}{getMetricUnit(metric)}
                </div>
                <div className="text-xs text-gray-600">
                  Range: {min.toFixed(1)} - {max.toFixed(1)}{getMetricUnit(metric)}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

export default WeatherChart;
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const AnalyticsDashboard = () => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('/api/weather/analytics/dashboard/', {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch analytics data');
      }

      const data = await response.json();
      setAnalyticsData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getHealthStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'excellent': return 'bg-green-500';
      case 'good': return 'bg-blue-500';
      case 'fair': return 'bg-yellow-500';
      case 'poor': return 'bg-orange-500';
      case 'critical': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getCacheEfficiencyColor = (efficiency) => {
    switch (efficiency?.toLowerCase()) {
      case 'good': return 'text-green-600';
      case 'fair': return 'text-yellow-600';
      case 'poor': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2">Loading analytics...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="border-red-200 bg-red-50">
        <AlertDescription className="text-red-800">
          Error loading analytics: {error}
        </AlertDescription>
      </Alert>
    );
  }

  if (!analyticsData) {
    return (
      <Alert>
        <AlertDescription>No analytics data available</AlertDescription>
      </Alert>
    );
  }

  const { api_usage, cache_performance, data_freshness, weather_trends } = analyticsData;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Weather Analytics Dashboard</h2>
        <button
          onClick={fetchAnalyticsData}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Refresh Data
        </button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">API Requests (24h)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{api_usage?.total_requests || 0}</div>
            <p className="text-xs text-gray-500">
              {api_usage?.unique_cities || 0} unique cities
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Cache Hit Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{cache_performance?.estimated_hit_rate || 0}%</div>
            <p className={`text-xs ${getCacheEfficiencyColor(cache_performance?.cache_efficiency)}`}>
              {cache_performance?.cache_efficiency || 'Unknown'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Data Health Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data_freshness?.health_score || 0}%</div>
            <Badge className={getHealthStatusColor(data_freshness?.health_status)}>
              {data_freshness?.health_status || 'Unknown'}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Active Cities</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data_freshness?.total_cities || 0}</div>
            <p className="text-xs text-gray-500">
              {weather_trends?.total_data_points || 0} data points
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analytics */}
      <Tabs defaultValue="api-usage" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="api-usage">API Usage</TabsTrigger>
          <TabsTrigger value="cache">Cache Performance</TabsTrigger>
          <TabsTrigger value="freshness">Data Freshness</TabsTrigger>
          <TabsTrigger value="trends">Weather Trends</TabsTrigger>
        </TabsList>

        <TabsContent value="api-usage" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>API Usage Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              {api_usage?.hourly_breakdown && (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={api_usage.hourly_breakdown}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="hour" 
                      tick={{ fontSize: 12 }}
                      angle={-45}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="requests" stroke="#3b82f6" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Top Cities by Requests</CardTitle>
            </CardHeader>
            <CardContent>
              {api_usage?.top_cities && (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={api_usage.top_cities.slice(0, 10)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="city__name" 
                      tick={{ fontSize: 12 }}
                      angle={-45}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="request_count" fill="#10b981" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="cache" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Cache Performance Metrics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-600">Estimated Hit Rate</p>
                  <p className="text-2xl font-bold">{cache_performance?.estimated_hit_rate || 0}%</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">Cache Efficiency</p>
                  <p className={`text-lg font-semibold ${getCacheEfficiencyColor(cache_performance?.cache_efficiency)}`}>
                    {cache_performance?.cache_efficiency || 'Unknown'}
                  </p>
                </div>
              </div>

              {cache_performance?.recommendations && (
                <div>
                  <p className="text-sm font-medium text-gray-600 mb-2">Recommendations</p>
                  <ul className="space-y-1">
                    {cache_performance.recommendations.map((rec, index) => (
                      <li key={index} className="text-sm text-gray-700 flex items-start">
                        <span className="text-blue-500 mr-2">•</span>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="freshness" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Data Freshness Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              {data_freshness?.freshness_percentages && (
                <div className="space-y-3">
                  {Object.entries(data_freshness.freshness_percentages).map(([status, percentage]) => (
                    <div key={status} className="flex items-center justify-between">
                      <span className="text-sm font-medium capitalize">
                        {status.replace('_', ' ')}
                      </span>
                      <div className="flex items-center space-x-2">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              status === 'very_fresh' ? 'bg-green-500' :
                              status === 'fresh' ? 'bg-blue-500' :
                              status === 'stale' ? 'bg-yellow-500' :
                              status === 'very_stale' ? 'bg-orange-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium w-12 text-right">{percentage}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {data_freshness?.recommendations && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-gray-600 mb-2">Recommendations</p>
                  <ul className="space-y-1">
                    {data_freshness.recommendations.map((rec, index) => (
                      <li key={index} className="text-sm text-gray-700 flex items-start">
                        <span className="text-blue-500 mr-2">•</span>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Temperature Trends</CardTitle>
            </CardHeader>
            <CardContent>
              {weather_trends?.daily_trends && (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={weather_trends.daily_trends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="avg_temperature" stroke="#ef4444" strokeWidth={2} name="Avg Temp" />
                    <Line type="monotone" dataKey="max_temperature" stroke="#f97316" strokeWidth={1} name="Max Temp" />
                    <Line type="monotone" dataKey="min_temperature" stroke="#3b82f6" strokeWidth={1} name="Min Temp" />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {weather_trends?.overall_stats && (
            <Card>
              <CardHeader>
                <CardTitle>Overall Statistics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Avg Temperature</p>
                    <p className="text-xl font-bold">{weather_trends.overall_stats.avg_temperature}°C</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">Max Temperature</p>
                    <p className="text-xl font-bold">{weather_trends.overall_stats.max_temperature}°C</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">Min Temperature</p>
                    <p className="text-xl font-bold">{weather_trends.overall_stats.min_temperature}°C</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-600">Avg Humidity</p>
                    <p className="text-xl font-bold">{weather_trends.overall_stats.avg_humidity}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AnalyticsDashboard;
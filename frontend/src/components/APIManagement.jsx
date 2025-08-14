import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

const APIManagement = () => {
  const [providers, setProviders] = useState([]);
  const [usageAnalytics, setUsageAnalytics] = useState(null);
  const [failoverEvents, setFailoverEvents] = useState([]);
  const [dashboardSummary, setDashboardSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAPIData();
  }, []);

  const loadAPIData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json',
      };

      // Load all API management data
      const [providersRes, usageRes, failoversRes, summaryRes] = await Promise.all([
        fetch('/api/weather/api/providers/', { headers }),
        fetch('/api/weather/api/usage/?days=30', { headers }),
        fetch('/api/weather/api/failovers/?days=7', { headers }),
        fetch('/api/weather/api/dashboard/', { headers })
      ]);

      if (!providersRes.ok || !usageRes.ok || !failoversRes.ok || !summaryRes.ok) {
        throw new Error('Failed to fetch API data');
      }

      const [providersData, usageData, failoversData, summaryData] = await Promise.all([
        providersRes.json(),
        usageRes.json(),
        failoversRes.json(),
        summaryRes.json()
      ]);

      setProviders(providersData);
      setUsageAnalytics(usageData);
      setFailoverEvents(failoversData.failover_events || []);
      setDashboardSummary(summaryData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const performHealthCheck = async (providerId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/weather/api/providers/${providerId}/health/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Health check failed');
      }

      const result = await response.json();
      
      // Update provider status
      setProviders(prev => prev.map(p => 
        p.id === providerId 
          ? { ...p, is_healthy: result.healthy, last_health_check: result.timestamp }
          : p
      ));

      return result;
    } catch (err) {
      console.error('Health check error:', err);
      throw err;
    }
  };

  const getStatusColor = (isActive, isHealthy) => {
    if (!isActive) return 'bg-gray-500';
    return isHealthy ? 'bg-green-500' : 'bg-red-500';
  };

  const getUsageColor = (current, limit) => {
    const percentage = (current / limit) * 100;
    if (percentage < 70) return 'text-green-600';
    if (percentage < 90) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2">Loading API management data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="border-red-200 bg-red-50">
        <AlertDescription className="text-red-800">
          Error loading API management data: {error}
        </AlertDescription>
      </Alert>
    );
  }

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">API Integration Management</h2>
        <button
          onClick={loadAPIData}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Refresh Data
        </button>
      </div>

      {/* Dashboard Summary */}
      {dashboardSummary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Active Providers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardSummary.providers.active}</div>
              <p className="text-xs text-gray-500">
                {dashboardSummary.providers.healthy} healthy
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Requests Today</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardSummary.usage_today.total_requests}</div>
              <p className="text-xs text-gray-500">
                ${dashboardSummary.usage_today.total_cost.toFixed(4)} cost
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Error Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardSummary.usage_today.error_rate.toFixed(1)}%</div>
              <p className="text-xs text-gray-500">
                {dashboardSummary.usage_today.total_errors} errors
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Failovers (24h)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardSummary.failovers_24h}</div>
              <p className="text-xs text-gray-500">
                Automatic failovers
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="providers" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="providers">Providers</TabsTrigger>
          <TabsTrigger value="usage">Usage Analytics</TabsTrigger>
          <TabsTrigger value="failovers">Failover Events</TabsTrigger>
          <TabsTrigger value="costs">Cost Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="providers" className="space-y-4">
          <div className="grid gap-4">
            {providers.map((provider) => (
              <Card key={provider.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center space-x-2">
                      <span className={`w-3 h-3 rounded-full ${getStatusColor(provider.is_active, provider.is_healthy)}`}></span>
                      <span>{provider.display_name}</span>
                      {provider.is_primary && (
                        <Badge className="bg-blue-500">Primary</Badge>
                      )}
                    </CardTitle>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => performHealthCheck(provider.id)}
                        className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
                      >
                        Health Check
                      </button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Status</p>
                      <p className={`text-sm ${provider.is_active ? 'text-green-600' : 'text-red-600'}`}>
                        {provider.is_active ? 'Active' : 'Inactive'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Health</p>
                      <p className={`text-sm ${provider.is_healthy ? 'text-green-600' : 'text-red-600'}`}>
                        {provider.is_healthy ? 'Healthy' : 'Unhealthy'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Success Rate</p>
                      <p className="text-sm font-bold">{provider.success_rate.toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Priority</p>
                      <p className="text-sm font-bold">{provider.priority}</p>
                    </div>
                  </div>

                  <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Usage Today</p>
                      <p className={`text-sm font-bold ${getUsageColor(provider.usage_today, provider.requests_per_day)}`}>
                        {provider.usage_today} / {provider.requests_per_day}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Monthly Budget</p>
                      <p className="text-sm font-bold">${provider.monthly_budget}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Cost/Request</p>
                      <p className="text-sm font-bold">${provider.cost_per_request.toFixed(6)}</p>
                    </div>
                  </div>

                  <div className="mt-4">
                    <p className="text-sm font-medium text-gray-600 mb-2">Supported Endpoints</p>
                    <div className="flex flex-wrap gap-1">
                      {provider.supported_endpoints.map((endpoint, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {endpoint}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="usage" className="space-y-4">
          {usageAnalytics && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Daily Usage Trends</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={usageAnalytics.daily_costs}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="requests" stroke="#3b82f6" strokeWidth={2} name="Requests" />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Provider Usage Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={usageAnalytics.provider_breakdown}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ display_name, requests }) => `${display_name}: ${requests}`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="requests"
                      >
                        {usageAnalytics.provider_breakdown.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        <TabsContent value="failovers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Failover Events</CardTitle>
            </CardHeader>
            <CardContent>
              {failoverEvents.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No recent failover events</p>
              ) : (
                <div className="space-y-3">
                  {failoverEvents.map((event) => (
                    <div key={event.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline" className="text-red-600 border-red-200">
                            Failover
                          </Badge>
                          <span className="text-sm font-medium">
                            {event.primary_provider} → {event.fallback_provider}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {new Date(event.failed_at).toLocaleString()}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600">
                        <p><strong>Endpoint:</strong> {event.endpoint}</p>
                        <p><strong>Reason:</strong> {event.reason}</p>
                        {event.error_details && (
                          <p><strong>Details:</strong> {event.error_details}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="costs" className="space-y-4">
          {usageAnalytics && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Cost Overview</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Total Cost (30 days)</p>
                      <p className="text-2xl font-bold">${usageAnalytics.totals.total_cost.toFixed(4)}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Total Requests</p>
                      <p className="text-2xl font-bold">{usageAnalytics.totals.total_requests.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Avg Cost/Request</p>
                      <p className="text-2xl font-bold">${usageAnalytics.totals.avg_cost_per_request.toFixed(6)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Daily Cost Trends</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={usageAnalytics.daily_costs}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                      <YAxis />
                      <Tooltip formatter={(value) => [`$${value.toFixed(4)}`, 'Cost']} />
                      <Bar dataKey="cost" fill="#10b981" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Cost by Provider</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {usageAnalytics.provider_breakdown.map((provider, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded">
                        <div>
                          <p className="font-medium">{provider.display_name}</p>
                          <p className="text-sm text-gray-500">{provider.requests.toLocaleString()} requests</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold">${provider.cost.toFixed(4)}</p>
                          <p className="text-sm text-gray-500">${provider.avg_cost_per_request.toFixed(6)}/req</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default APIManagement;
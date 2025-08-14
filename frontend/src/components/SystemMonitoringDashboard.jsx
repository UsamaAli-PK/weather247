import React, { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Server, 
  Database, 
  Cpu, 
  HardDrive,
  Zap,
  TrendingUp,
  RefreshCw
} from 'lucide-react';

const SystemMonitoringDashboard = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [healthChecks, setHealthChecks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const intervalRef = useRef(null);

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('/api/weather/monitoring/status/');
      if (!response.ok) throw new Error('Failed to fetch system status');
      const data = await response.json();
      setSystemStatus(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await fetch('/api/weather/monitoring/alerts/?status=active&hours=24');
      if (!response.ok) throw new Error('Failed to fetch alerts');
      const data = await response.json();
      setAlerts(data.alerts || []);
    } catch (err) {
      console.error('Error fetching alerts:', err);
    }
  };

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/weather/monitoring/trends/?hours=1&metrics=cpu_usage,memory_usage,disk_usage');
      if (!response.ok) throw new Error('Failed to fetch metrics');
      const data = await response.json();
      setMetrics(data.trends || {});
    } catch (err) {
      console.error('Error fetching metrics:', err);
    }
  };

  const fetchHealthChecks = async () => {
    try {
      const response = await fetch('/api/weather/monitoring/health/?hours=1');
      if (!response.ok) throw new Error('Failed to fetch health checks');
      const data = await response.json();
      setHealthChecks(data.health_checks || []);
    } catch (err) {
      console.error('Error fetching health checks:', err);
    }
  };

  const acknowledgeAlert = async (alertId) => {
    try {
      const response = await fetch(`/api/weather/monitoring/alerts/${alertId}/acknowledge/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
      });
      if (!response.ok) throw new Error('Failed to acknowledge alert');
      await fetchAlerts(); // Refresh alerts
    } catch (err) {
      console.error('Error acknowledging alert:', err);
    }
  };

  const resolveAlert = async (alertId) => {
    try {
      const response = await fetch(`/api/weather/monitoring/alerts/${alertId}/resolve/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
      });
      if (!response.ok) throw new Error('Failed to resolve alert');
      await fetchAlerts(); // Refresh alerts
    } catch (err) {
      console.error('Error resolving alert:', err);
    }
  };

  const runHealthChecks = async () => {
    try {
      const response = await fetch('/api/weather/monitoring/health/run/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
      });
      if (!response.ok) throw new Error('Failed to run health checks');
      await fetchHealthChecks(); // Refresh health checks
    } catch (err) {
      console.error('Error running health checks:', err);
    }
  };

  const getCsrfToken = () => {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
  };

  const refreshData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchSystemStatus(),
        fetchAlerts(),
        fetchMetrics(),
        fetchHealthChecks()
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(refreshData, 30000); // Refresh every 30 seconds
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefresh]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'critical':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getSeverityBadge = (severity) => {
    const colors = {
      info: 'bg-blue-100 text-blue-800',
      warning: 'bg-yellow-100 text-yellow-800',
      error: 'bg-red-100 text-red-800',
      critical: 'bg-red-200 text-red-900',
      emergency: 'bg-purple-100 text-purple-800'
    };
    return (
      <Badge className={colors[severity] || 'bg-gray-100 text-gray-800'}>
        {severity.toUpperCase()}
      </Badge>
    );
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const getLatestMetricValue = (metricData) => {
    if (!metricData || metricData.length === 0) return 'N/A';
    return `${metricData[metricData.length - 1].value.toFixed(1)}${metricData[metricData.length - 1].unit}`;
  };

  if (loading && !systemStatus) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading system status...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="border-red-200 bg-red-50">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Error loading system monitoring data: {error}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Activity className="h-6 w-6" />
          <h1 className="text-2xl font-bold">System Monitoring</h1>
          {systemStatus && getStatusIcon(systemStatus.overall_status)}
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? 'Disable Auto-refresh' : 'Enable Auto-refresh'}
          </Button>
          <Button variant="outline" size="sm" onClick={refreshData}>
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </Button>
        </div>
      </div>

      {/* System Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Server className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-sm font-medium">System Status</p>
                <p className="text-lg font-bold">
                  {systemStatus?.overall_status?.toUpperCase() || 'UNKNOWN'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              <div>
                <p className="text-sm font-medium">Active Alerts</p>
                <p className="text-lg font-bold">
                  {systemStatus?.alerts?.active || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <XCircle className="h-5 w-5 text-red-500" />
              <div>
                <p className="text-sm font-medium">Critical Alerts</p>
                <p className="text-lg font-bold">
                  {systemStatus?.alerts?.critical || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-gray-500" />
              <div>
                <p className="text-sm font-medium">Last Updated</p>
                <p className="text-sm">
                  {systemStatus?.timestamp ? formatTimestamp(systemStatus.timestamp) : 'N/A'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="health">Health Checks</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* System Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center space-x-2">
                  <Cpu className="h-5 w-5" />
                  <span>CPU Usage</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {getLatestMetricValue(metrics.cpu_usage)}
                </p>
                <p className="text-sm text-gray-600">
                  {systemStatus?.metrics?.cpu?.core_count || 'N/A'} cores
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center space-x-2">
                  <Zap className="h-5 w-5" />
                  <span>Memory Usage</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {getLatestMetricValue(metrics.memory_usage)}
                </p>
                <p className="text-sm text-gray-600">
                  {systemStatus?.metrics?.memory?.total_gb || 'N/A'} GB total
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center space-x-2">
                  <HardDrive className="h-5 w-5" />
                  <span>Disk Usage</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {getLatestMetricValue(metrics.disk_usage)}
                </p>
                <p className="text-sm text-gray-600">
                  {systemStatus?.metrics?.disk?.total_gb || 'N/A'} GB total
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Recent Alerts */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              {alerts.length === 0 ? (
                <p className="text-gray-600">No active alerts</p>
              ) : (
                <div className="space-y-2">
                  {alerts.slice(0, 5).map((alert) => (
                    <div key={alert.id} className="flex items-center justify-between p-2 border rounded">
                      <div className="flex items-center space-x-2">
                        {getSeverityBadge(alert.severity)}
                        <span className="font-medium">{alert.title}</span>
                      </div>
                      <span className="text-sm text-gray-600">
                        {formatTimestamp(alert.created_at)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">System Alerts</h3>
            <Button variant="outline" size="sm" onClick={fetchAlerts}>
              <RefreshCw className="h-4 w-4 mr-1" />
              Refresh Alerts
            </Button>
          </div>

          {alerts.length === 0 ? (
            <Card>
              <CardContent className="p-6 text-center">
                <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-2" />
                <p className="text-lg font-medium">No Active Alerts</p>
                <p className="text-gray-600">System is running normally</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {alerts.map((alert) => (
                <Card key={alert.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          {getSeverityBadge(alert.severity)}
                          <Badge variant="outline">{alert.type}</Badge>
                          <span className="text-sm text-gray-600">{alert.component}</span>
                        </div>
                        <h4 className="font-semibold">{alert.title}</h4>
                        <p className="text-gray-700">{alert.message}</p>
                        <p className="text-sm text-gray-600">
                          Created: {formatTimestamp(alert.created_at)}
                        </p>
                      </div>
                      <div className="flex space-x-2">
                        {alert.status === 'active' && (
                          <>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => acknowledgeAlert(alert.id)}
                            >
                              Acknowledge
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => resolveAlert(alert.id)}
                            >
                              Resolve
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Performance Metrics</h3>
            <Button variant="outline" size="sm" onClick={fetchMetrics}>
              <TrendingUp className="h-4 w-4 mr-1" />
              Refresh Metrics
            </Button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {Object.entries(metrics).map(([metricType, data]) => (
              <Card key={metricType}>
                <CardHeader>
                  <CardTitle className="capitalize">
                    {metricType.replace('_', ' ')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {data.length > 0 ? (
                    <div className="space-y-2">
                      <p className="text-2xl font-bold">
                        {data[data.length - 1].value.toFixed(1)}{data[data.length - 1].unit}
                      </p>
                      <p className="text-sm text-gray-600">
                        Last updated: {formatTimestamp(data[data.length - 1].timestamp)}
                      </p>
                      <div className="text-xs text-gray-500">
                        {data.length} data points in the last hour
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-600">No data available</p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="health" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Health Checks</h3>
            <Button variant="outline" size="sm" onClick={runHealthChecks}>
              <RefreshCw className="h-4 w-4 mr-1" />
              Run Health Checks
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {healthChecks.map((check) => (
              <Card key={check.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(check.status)}
                        <span className="font-medium">{check.name}</span>
                      </div>
                      <p className="text-sm text-gray-600 capitalize">{check.type}</p>
                      {check.response_time && (
                        <p className="text-sm text-gray-600">
                          Response time: {check.response_time.toFixed(2)}ms
                        </p>
                      )}
                      {check.error_message && (
                        <p className="text-sm text-red-600">{check.error_message}</p>
                      )}
                    </div>
                    <div className="text-right">
                      <Badge 
                        className={
                          check.status === 'healthy' 
                            ? 'bg-green-100 text-green-800'
                            : check.status === 'warning'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }
                      >
                        {check.status.toUpperCase()}
                      </Badge>
                      <p className="text-xs text-gray-500 mt-1">
                        {formatTimestamp(check.timestamp)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {healthChecks.length === 0 && (
            <Card>
              <CardContent className="p-6 text-center">
                <Database className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                <p className="text-lg font-medium">No Health Check Data</p>
                <p className="text-gray-600">Run health checks to see system status</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SystemMonitoringDashboard;
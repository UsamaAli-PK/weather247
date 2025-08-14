"""
API views for API Integration Management
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Avg, Count
import json

from .api_management import APIProvider, APIUsage, APIFailover, api_manager
from .serializers import APIProviderSerializer, APIUsageSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_providers_list(request):
    """List all API providers with their status"""
    try:
        providers = APIProvider.objects.all().order_by('priority')
        serializer = APIProviderSerializer(providers, many=True)
        
        # Add usage statistics
        provider_data = []
        for provider_info in serializer.data:
            provider = APIProvider.objects.get(id=provider_info['id'])
            usage_today = provider.get_usage_today()
            usage_month = provider.get_usage_this_month()
            
            provider_info.update({
                'usage_today': usage_today,
                'usage_month': usage_month['total_requests'] or 0,
                'cost_month': float(usage_month['total_cost'] or 0),
                'can_make_request': provider.can_make_request()
            })
            provider_data.append(provider_info)
        
        return Response({
            'providers': provider_data,
            'total_count': len(provider_data)
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_provider_create(request):
    """Create a new API provider"""
    try:
        serializer = APIProviderSerializer(data=request.data)
        if serializer.is_valid():
            provider = serializer.save()
            return Response(
                APIProviderSerializer(provider).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_provider_detail(request, provider_id):
    """Get, update, or delete an API provider"""
    try:
        provider = APIProvider.objects.get(id=provider_id)
        
        if request.method == 'GET':
            serializer = APIProviderSerializer(provider)
            data = serializer.data
            
            # Add detailed statistics
            stats = api_manager.get_provider_statistics(provider_id, days=30)
            data['statistics'] = stats
            
            return Response(data)
            
        elif request.method == 'PUT':
            serializer = APIProviderSerializer(provider, data=request.data, partial=True)
            if serializer.is_valid():
                provider = serializer.save()
                return Response(APIProviderSerializer(provider).data)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
            
        elif request.method == 'DELETE':
            provider.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
            
    except APIProvider.DoesNotExist:
        return Response(
            {'error': 'Provider not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_provider_health_check(request, provider_id):
    """Perform health check on an API provider"""
    try:
        provider = APIProvider.objects.get(id=provider_id)
        health_result = api_manager.perform_health_check(provider)
        
        return Response(health_result)
        
    except APIProvider.DoesNotExist:
        return Response(
            {'error': 'Provider not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_usage_analytics(request):
    """Get API usage analytics"""
    try:
        days = int(request.GET.get('days', 30))
        provider_id = request.GET.get('provider_id')
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Base queryset
        usage_qs = APIUsage.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )
        
        if provider_id:
            usage_qs = usage_qs.filter(provider_id=provider_id)
        
        # Aggregate statistics
        total_stats = usage_qs.aggregate(
            total_requests=Sum('request_count'),
            total_success=Sum('success_count'),
            total_errors=Sum('error_count'),
            total_cost=Sum('cost'),
            avg_response_time=Avg('avg_response_time')
        )
        
        # Daily breakdown
        daily_usage = usage_qs.values('date').annotate(
            requests=Sum('request_count'),
            errors=Sum('error_count'),
            cost=Sum('cost'),
            avg_response_time=Avg('avg_response_time')
        ).order_by('date')
        
        # Provider breakdown
        provider_usage = usage_qs.values(
            'provider__name',
            'provider__display_name'
        ).annotate(
            requests=Sum('request_count'),
            errors=Sum('error_count'),
            cost=Sum('cost'),
            avg_response_time=Avg('avg_response_time')
        ).order_by('-requests')
        
        # Endpoint breakdown
        endpoint_usage = usage_qs.values('endpoint').annotate(
            requests=Sum('request_count'),
            errors=Sum('error_count'),
            cost=Sum('cost'),
            avg_response_time=Avg('avg_response_time')
        ).order_by('-requests')[:10]
        
        return Response({
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'totals': {
                'requests': total_stats['total_requests'] or 0,
                'success': total_stats['total_success'] or 0,
                'errors': total_stats['total_errors'] or 0,
                'cost': float(total_stats['total_cost'] or 0),
                'avg_response_time': float(total_stats['avg_response_time'] or 0),
                'success_rate': (
                    (total_stats['total_success'] or 0) / 
                    max(total_stats['total_requests'] or 1, 1)
                ) * 100
            },
            'daily_usage': [
                {
                    'date': item['date'].isoformat(),
                    'requests': item['requests'],
                    'errors': item['errors'],
                    'cost': float(item['cost']),
                    'avg_response_time': float(item['avg_response_time'] or 0)
                }
                for item in daily_usage
            ],
            'provider_breakdown': [
                {
                    'provider': item['provider__name'],
                    'display_name': item['provider__display_name'],
                    'requests': item['requests'],
                    'errors': item['errors'],
                    'cost': float(item['cost']),
                    'avg_response_time': float(item['avg_response_time'] or 0),
                    'success_rate': (
                        (item['requests'] - item['errors']) / 
                        max(item['requests'], 1)
                    ) * 100
                }
                for item in provider_usage
            ],
            'endpoint_breakdown': [
                {
                    'endpoint': item['endpoint'],
                    'requests': item['requests'],
                    'errors': item['errors'],
                    'cost': float(item['cost']),
                    'avg_response_time': float(item['avg_response_time'] or 0)
                }
                for item in endpoint_usage
            ]
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_cost_analysis(request):
    """Get detailed cost analysis"""
    try:
        days = int(request.GET.get('days', 30))
        cost_analysis = api_manager.get_cost_analysis(days)
        
        return Response(cost_analysis)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_failover_events(request):
    """Get API failover events"""
    try:
        days = int(request.GET.get('days', 30))
        provider_id = request.GET.get('provider_id')
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        failovers_qs = APIFailover.objects.filter(
            failed_at__gte=start_date,
            failed_at__lte=end_date
        )
        
        if provider_id:
            failovers_qs = failovers_qs.filter(primary_provider_id=provider_id)
        
        failovers = failovers_qs.select_related(
            'primary_provider',
            'fallback_provider'
        ).order_by('-failed_at')
        
        failover_data = []
        for failover in failovers:
            duration = None
            if failover.resolved_at:
                duration = (failover.resolved_at - failover.failed_at).total_seconds()
            
            failover_data.append({
                'id': failover.id,
                'primary_provider': failover.primary_provider.display_name,
                'fallback_provider': failover.fallback_provider.display_name,
                'endpoint': failover.endpoint,
                'reason': failover.reason,
                'error_details': failover.error_details,
                'failed_at': failover.failed_at.isoformat(),
                'resolved_at': failover.resolved_at.isoformat() if failover.resolved_at else None,
                'duration_seconds': duration,
                'is_resolved': failover.resolved_at is not None
            })
        
        # Summary statistics
        total_failovers = failovers.count()
        resolved_failovers = failovers.filter(resolved_at__isnull=False).count()
        avg_resolution_time = None
        
        if resolved_failovers > 0:
            resolved_events = failovers.filter(resolved_at__isnull=False)
            total_duration = sum([
                (f.resolved_at - f.failed_at).total_seconds()
                for f in resolved_events
            ])
            avg_resolution_time = total_duration / resolved_failovers
        
        return Response({
            'period': {
                'start_date': start_date.date().isoformat(),
                'end_date': end_date.date().isoformat(),
                'days': days
            },
            'summary': {
                'total_failovers': total_failovers,
                'resolved_failovers': resolved_failovers,
                'unresolved_failovers': total_failovers - resolved_failovers,
                'avg_resolution_time_seconds': avg_resolution_time
            },
            'events': failover_data
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_failover_resolve(request, failover_id):
    """Mark a failover event as resolved"""
    try:
        failover = APIFailover.objects.get(id=failover_id)
        
        if failover.resolved_at:
            return Response(
                {'error': 'Failover already resolved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        failover.resolved_at = timezone.now()
        failover.save()
        
        return Response({
            'message': 'Failover marked as resolved',
            'resolved_at': failover.resolved_at.isoformat()
        })
        
    except APIFailover.DoesNotExist:
        return Response(
            {'error': 'Failover event not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_system_health(request):
    """Get overall API system health status"""
    try:
        providers = APIProvider.objects.filter(is_active=True)
        
        total_providers = providers.count()
        healthy_providers = providers.filter(is_healthy=True).count()
        
        # Recent failovers (last 24 hours)
        recent_failovers = APIFailover.objects.filter(
            failed_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        # Usage statistics for today
        today = timezone.now().date()
        today_usage = APIUsage.objects.filter(date=today).aggregate(
            total_requests=Sum('request_count'),
            total_errors=Sum('error_count'),
            total_cost=Sum('cost')
        )
        
        # Calculate health score
        health_score = 100
        if total_providers > 0:
            provider_health = (healthy_providers / total_providers) * 100
            health_score = min(health_score, provider_health)
        
        if today_usage['total_requests'] and today_usage['total_requests'] > 0:
            error_rate = (today_usage['total_errors'] or 0) / today_usage['total_requests']
            error_health = max(0, (1 - error_rate) * 100)
            health_score = min(health_score, error_health)
        
        # Determine overall status
        if health_score >= 95:
            status_text = 'Excellent'
            status_color = 'green'
        elif health_score >= 80:
            status_text = 'Good'
            status_color = 'green'
        elif health_score >= 60:
            status_text = 'Warning'
            status_color = 'orange'
        else:
            status_text = 'Critical'
            status_color = 'red'
        
        return Response({
            'health_score': round(health_score, 1),
            'status': status_text,
            'status_color': status_color,
            'providers': {
                'total': total_providers,
                'healthy': healthy_providers,
                'unhealthy': total_providers - healthy_providers
            },
            'today_usage': {
                'requests': today_usage['total_requests'] or 0,
                'errors': today_usage['total_errors'] or 0,
                'cost': float(today_usage['total_cost'] or 0),
                'error_rate': (
                    (today_usage['total_errors'] or 0) / 
                    max(today_usage['total_requests'] or 1, 1)
                ) * 100
            },
            'recent_failovers': recent_failovers,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_real_time_status(request):
    """Get real-time status of all API providers"""
    try:
        from .api_monitoring_realtime import real_time_monitor
        
        status_data = real_time_monitor.get_real_time_status()
        return Response(status_data)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_latest_alerts(request):
    """Get latest system alerts"""
    try:
        from .api_monitoring_realtime import real_time_monitor
        
        limit = int(request.GET.get('limit', 10))
        alerts = real_time_monitor.get_latest_alerts(limit)
        
        return Response({
            'alerts': alerts,
            'count': len(alerts),
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_start_monitoring(request):
    """Start real-time API monitoring"""
    try:
        from .api_monitoring_realtime import real_time_monitor
        
        real_time_monitor.start_monitoring()
        
        return Response({
            'message': 'Real-time monitoring started',
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_bulk_health_check(request):
    """Perform health check on all active providers"""
    try:
        providers = APIProvider.objects.filter(is_active=True)
        results = []
        
        for provider in providers:
            try:
                health_result = api_manager.perform_health_check(provider)
                results.append({
                    'provider': provider.name,
                    'display_name': provider.display_name,
                    'healthy': health_result['healthy'],
                    'response_time': health_result.get('response_time', 0),
                    'error': health_result.get('error')
                })
            except Exception as e:
                results.append({
                    'provider': provider.name,
                    'display_name': provider.display_name,
                    'healthy': False,
                    'error': str(e)
                })
        
        return Response({
            'results': results,
            'total_checked': len(results),
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
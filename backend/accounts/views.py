from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from .models import User, UserProfile, UserActivity, UserSession, UserRole, UserAPIUsage
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    UserProfileSerializer, PasswordChangeSerializer, UserActivitySerializer,
    BulkUserOperationSerializer
)


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@csrf_exempt
def register(request):
    """User registration endpoint"""
    print(f"Registration request data: {request.data}")  # Debug logging
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)
    print(f"Registration errors: {serializer.errors}")  # Debug logging
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@csrf_exempt
def login_view(request):
    """User login endpoint"""
    print(f"Login request data: {request.data}")  # Debug logging
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        login(request, user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)
    print(f"Login errors: {serializer.errors}")  # Debug logging
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """User logout endpoint"""
    try:
        # Delete the user's token
        request.user.auth_token.delete()
        logout(request)
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except:
        return Response({'error': 'Error logging out'}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile view"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class UserDetailView(generics.RetrieveUpdateAPIView):
    """User detail view"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# WeatherAlert views will be moved to alerts app later


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """Change user password"""
    serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        # Update token
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        return Response({
            'message': 'Password changed successfully',
            'token': token.key
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """Get user statistics"""
    user = request.user
    
    return Response({
        'login_count': user.login_count,
        'api_requests_count': user.api_requests_count,
        'last_activity': user.last_activity,
        'member_since': user.date_joined.strftime('%Y-%m-%d'),
        'is_verified': user.is_verified,
        'preferred_units': user.preferred_units,
    }, status=status.HTTP_200_OK)

# Enhanced User Management Views

@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def user_preferences(request):
    """Get or update user preferences"""
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        if request.method == 'GET':
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                
                # Track activity
                from .utils import track_user_activity
                track_user_activity(
                    user=request.user,
                    activity_type='profile_update',
                    description='User preferences updated',
                    request=request
                )
                
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to handle user preferences'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_activity_history(request):
    """Get user activity history"""
    try:
        from .models import UserActivity
        activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')[:50]
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to retrieve activity history'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_sessions(request):
    """Get user active sessions"""
    try:
        from .models import UserSession
        sessions = UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-last_activity')
        
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                'session_key': session.session_key[:8] + '...',
                'ip_address': session.ip_address,
                'location': session.location,
                'user_agent': session.user_agent[:100] + '...' if len(session.user_agent) > 100 else session.user_agent,
                'created_at': session.created_at,
                'last_activity': session.last_activity,
                'is_current': session.session_key == request.session.session_key
            })
        
        return Response(sessions_data)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to retrieve sessions'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_dashboard_data(request):
    """Get user dashboard data"""
    try:
        from .utils import get_user_dashboard_data
        dashboard_data = get_user_dashboard_data(request.user)
        return Response(dashboard_data)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to retrieve dashboard data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Admin User Management Views

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_users_list(request):
    """Get list of all users for admin"""
    try:
        from django.db.models import Q
        
        users = User.objects.all().order_by('-date_joined')
        
        # Apply filters
        search = request.GET.get('search', '')
        if search:
            users = users.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        is_active = request.GET.get('is_active')
        if is_active is not None:
            users = users.filter(is_active=is_active.lower() == 'true')
        
        # Pagination
        page_size = int(request.GET.get('page_size', 20))
        page = int(request.GET.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_users = users.count()
        users_page = users[start:end]
        
        users_data = []
        for user in users_page:
            users_data.append({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'date_joined': user.date_joined,
                'last_login': user.last_login,
                'last_activity': user.last_activity,
                'login_count': user.login_count,
                'api_requests_count': user.api_requests_count,
                'is_verified': user.is_verified,
            })
        
        return Response({
            'users': users_data,
            'pagination': {
                'total': total_users,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_users + page_size - 1) // page_size
            }
        })
        
    except Exception as e:
        return Response(
            {'error': 'Failed to retrieve users list'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAdminUser])
def admin_user_detail(request, user_id):
    """Get, update, or delete user (admin only)"""
    try:
        user = User.objects.get(id=user_id)
        
        if request.method == 'GET':
            # Get detailed user information
            from .models import UserActivity
            recent_activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:10]
            api_usage_today = user.get_api_usage_today()
            
            user_data = {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined,
                'last_login': user.last_login,
                'last_activity': user.last_activity,
                'login_count': user.login_count,
                'api_requests_count': user.api_requests_count,
                'api_rate_limit': user.api_rate_limit,
                'is_verified': user.is_verified,
                'preferred_units': user.preferred_units,
                'timezone': user.timezone,
                'api_usage_today': api_usage_today,
                'recent_activities': UserActivitySerializer(recent_activities, many=True).data
            }
            
            return Response(user_data)
        
        elif request.method == 'PUT':
            # Update user
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            # Deactivate user instead of deleting
            user.is_active = False
            user.save()
            return Response({'message': 'User deactivated successfully'})
        
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Operation failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_bulk_user_operations(request):
    """Bulk operations on users (admin only)"""
    try:
        serializer = BulkUserOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        operation = serializer.validated_data['operation']
        user_ids = serializer.validated_data['user_ids']
        
        users = User.objects.filter(id__in=user_ids)
        
        if operation == 'activate':
            updated = users.update(is_active=True)
            message = f'{updated} users activated'
        elif operation == 'deactivate':
            updated = users.update(is_active=False)
            message = f'{updated} users deactivated'
        elif operation == 'delete':
            # Soft delete by deactivating
            updated = users.update(is_active=False)
            message = f'{updated} users deactivated'
        
        return Response({'message': message})
        
    except Exception as e:
        return Response(
            {'error': 'Bulk operation failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_user_analytics(request):
    """Get user analytics for admin dashboard"""
    try:
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        analytics = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'verified_users': User.objects.filter(is_verified=True).count(),
            'staff_users': User.objects.filter(is_staff=True).count(),
            'users_24h': User.objects.filter(last_activity__gte=last_24h).count(),
            'new_users_7d': User.objects.filter(date_joined__gte=last_7d).count(),
            'new_users_30d': User.objects.filter(date_joined__gte=last_30d).count(),
        }
        
        # User registration trends
        registration_trends = []
        for i in range(7):
            date = (now - timedelta(days=i)).date()
            count = User.objects.filter(date_joined__date=date).count()
            registration_trends.append({
                'date': date.isoformat(),
                'count': count
            })
        
        analytics['registration_trends'] = list(reversed(registration_trends))
        
        # Top active users
        top_users = User.objects.filter(
            is_active=True
        ).order_by('-login_count')[:10]
        
        analytics['top_active_users'] = [
            {
                'email': user.email,
                'login_count': user.login_count,
                'last_activity': user.last_activity
            }
            for user in top_users
        ]
        
        return Response(analytics)
        
    except Exception as e:
        return Response(
            {'error': 'Failed to retrieve analytics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Enhanced User Management System Views

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
import json
import csv
from datetime import timedelta

from .user_management import user_manager, role_manager


def is_admin_user(user):
    """Check if user is admin"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


class UserManagementViewSet(viewsets.ModelViewSet):
    """API ViewSet for comprehensive user management"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = User.objects.select_related('profile').prefetch_related('groups')
        
        # Filter by search query
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # Filter by status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        is_verified = self.request.query_params.get('is_verified')
        if is_verified is not None:
            queryset = queryset.filter(is_verified=is_verified.lower() == 'true')
        
        return queryset.order_by('-date_joined')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get comprehensive user statistics"""
        days = int(request.query_params.get('days', 30))
        stats = user_manager.get_user_statistics(days)
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update users"""
        user_ids = request.data.get('user_ids', [])
        updates = request.data.get('updates', {})
        
        if not user_ids:
            return Response(
                {'error': 'user_ids is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            count = user_manager.bulk_update_users(user_ids, updates)
            return Response({'updated_count': count})
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def assign_role(self, request):
        """Assign role to users"""
        user_ids = request.data.get('user_ids', [])
        role_name = request.data.get('role_name')
        
        if not user_ids or not role_name:
            return Response(
                {'error': 'user_ids and role_name are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            count = user_manager.assign_role_to_users(user_ids, role_name)
            return Response({'assigned_count': count})
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def activity_summary(self, request, pk=None):
        """Get user activity summary"""
        user = self.get_object()
        days = int(request.query_params.get('days', 30))
        summary = user_manager.get_user_activity_summary(user, days)
        return Response(summary)
    
    @action(detail=True, methods=['post'])
    def terminate_sessions(self, request, pk=None):
        """Terminate user sessions"""
        user = self.get_object()
        count = user_manager.manage_user_sessions(user, 'terminate_all')
        return Response({'terminated_sessions': count})
    
    @action(detail=False, methods=['post'])
    def send_notification(self, request):
        """Send bulk notification"""
        user_ids = request.data.get('user_ids', [])
        subject = request.data.get('subject')
        message = request.data.get('message')
        notification_type = request.data.get('notification_type', 'email')
        
        if not all([user_ids, subject, message]):
            return Response(
                {'error': 'user_ids, subject, and message are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            count = user_manager.send_bulk_notification(
                user_ids, subject, message, notification_type
            )
            return Response({'sent_count': count})
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export users data"""
        user_ids = request.query_params.getlist('user_ids')
        format_type = request.query_params.get('format', 'csv')
        
        if not user_ids:
            user_ids = list(self.get_queryset().values_list('id', flat=True))
        else:
            user_ids = [int(uid) for uid in user_ids]
        
        export_data = user_manager.export_user_data(user_ids, format_type)
        
        if format_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
            
            if export_data['data']:
                fieldnames = export_data['data'][0].keys()
                writer = csv.DictWriter(response, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in export_data['data']:
                    processed_row = {}
                    for key, value in row.items():
                        if isinstance(value, (list, dict)):
                            processed_row[key] = json.dumps(value)
                        else:
                            processed_row[key] = value
                    writer.writerow(processed_row)
            
            return response
        else:
            return Response(export_data)


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin_user), name='dispatch')
class UserAnalyticsView(View):
    """User analytics dashboard view"""
    
    def get(self, request):
        days = int(request.GET.get('days', 30))
        stats = user_manager.get_user_statistics(days)
        
        # Add role hierarchy
        stats['role_hierarchy'] = role_manager.get_role_hierarchy()
        
        return JsonResponse(stats)


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin_user), name='dispatch')
class UserSearchView(View):
    """User search and filtering"""
    
    def get(self, request):
        query = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        users = User.objects.select_related('profile')
        
        if query:
            users = users.filter(
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )
        
        # Apply filters
        is_active = request.GET.get('is_active')
        if is_active is not None:
            users = users.filter(is_active=is_active.lower() == 'true')
        
        is_verified = request.GET.get('is_verified')
        if is_verified is not None:
            users = users.filter(is_verified=is_verified.lower() == 'true')
        
        is_staff = request.GET.get('is_staff')
        if is_staff is not None:
            users = users.filter(is_staff=is_staff.lower() == 'true')
        
        # Pagination
        paginator = Paginator(users.order_by('-date_joined'), per_page)
        page_obj = paginator.get_page(page)
        
        users_data = []
        for user in page_obj:
            user_data = {
                'id': user.id,
                'email': user.email,
                'full_name': user.get_full_name(),
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'is_staff': user.is_staff,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'last_activity': user.last_activity.isoformat() if user.last_activity else None,
                'login_count': user.login_count,
                'api_usage_today': user.get_api_usage_today(),
            }
            users_data.append(user_data)
        
        return JsonResponse({
            'users': users_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })


@login_required
@user_passes_test(is_admin_user)
@require_http_methods(["GET"])
def user_activity_log(request, user_id):
    """Get user activity log"""
    try:
        user = User.objects.get(id=user_id)
        days = int(request.GET.get('days', 30))
        
        activities = UserActivity.objects.filter(
            user=user,
            timestamp__gte=timezone.now() - timedelta(days=days)
        ).order_by('-timestamp')
        
        page = int(request.GET.get('page', 1))
        paginator = Paginator(activities, 50)
        page_obj = paginator.get_page(page)
        
        activities_data = []
        for activity in page_obj:
            activities_data.append({
                'id': activity.id,
                'activity_type': activity.activity_type,
                'description': activity.description,
                'ip_address': activity.ip_address,
                'user_agent': activity.user_agent,
                'metadata': activity.metadata,
                'timestamp': activity.timestamp.isoformat(),
            })
        
        return JsonResponse({
            'activities': activities_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
            }
        })
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


@login_required
@user_passes_test(is_admin_user)
@require_http_methods(["GET"])
def user_sessions_detail(request, user_id):
    """Get user sessions"""
    try:
        user = User.objects.get(id=user_id)
        sessions = UserSession.objects.filter(user=user).order_by('-last_activity')
        
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                'id': session.id,
                'session_key': session.session_key[:8] + '...',
                'ip_address': session.ip_address,
                'user_agent': session.user_agent,
                'location': session.location,
                'is_active': session.is_active,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'is_expired': session.is_expired(),
            })
        
        return JsonResponse({'sessions': sessions_data})
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


# Role Management Views

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAdminUser])
def role_management(request):
    """Manage user roles"""
    if request.method == 'GET':
        roles = UserRole.objects.filter(is_active=True)
        roles_data = []
        for role in roles:
            roles_data.append({
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'permissions': list(role.permissions.values_list('codename', flat=True)),
                'user_count': User.objects.filter(groups__name=role.name).count(),
                'created_at': role.created_at.isoformat(),
            })
        return Response(roles_data)
    
    elif request.method == 'POST':
        name = request.data.get('name')
        description = request.data.get('description', '')
        permissions = request.data.get('permissions', [])
        
        if not name:
            return Response(
                {'error': 'Role name is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            role = role_manager.create_role(name, description, permissions)
            return Response({
                'id': role.id,
                'name': role.name,
                'description': role.description,
                'message': 'Role created successfully'
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def role_hierarchy(request):
    """Get role hierarchy"""
    hierarchy = role_manager.get_role_hierarchy()
    return Response(hierarchy)
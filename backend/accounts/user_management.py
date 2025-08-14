"""
User Management System
Provides comprehensive user management functionality including role-based access control,
user activity tracking, and bulk operations.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import logging
from typing import List, Dict, Optional, Any

from .models import UserRole, UserProfile, UserActivity, UserSession, UserAPIUsage

User = get_user_model()
logger = logging.getLogger(__name__)


class UserManager:
    """Comprehensive user management system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_user_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        now = timezone.now()
        period_start = now - timedelta(days=days)
        
        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'verified_users': User.objects.filter(is_verified=True).count(),
            'staff_users': User.objects.filter(is_staff=True).count(),
            'new_users_period': User.objects.filter(date_joined__gte=period_start).count(),
            'active_users_period': User.objects.filter(last_activity__gte=period_start).count(),
        }
        
        # Activity breakdown
        activity_stats = UserActivity.objects.filter(
            timestamp__gte=period_start
        ).values('activity_type').annotate(count=Count('id'))
        
        stats['activity_breakdown'] = {
            item['activity_type']: item['count'] 
            for item in activity_stats
        }
        
        # API usage stats
        api_stats = UserAPIUsage.objects.filter(
            date__gte=period_start.date()
        ).aggregate(
            total_requests=Count('request_count'),
            avg_success_rate=Avg('success_count') / Avg('request_count') * 100
        )
        
        stats['api_usage'] = api_stats
        
        return stats
    
    def create_user_with_profile(self, email: str, password: str, **kwargs) -> User:
        """Create user with associated profile"""
        try:
            user = User.objects.create_user(
                email=email,
                username=email,  # Use email as username
                password=password,
                **kwargs
            )
            
            # Profile is created automatically via signal
            self.log_user_activity(user, 'account_created', 'User account created')
            
            self.logger.info(f"User created successfully: {email}")
            return user
            
        except Exception as e:
            self.logger.error(f"Error creating user {email}: {str(e)}")
            raise
    
    def bulk_update_users(self, user_ids: List[int], updates: Dict[str, Any]) -> int:
        """Bulk update multiple users"""
        try:
            updated_count = User.objects.filter(id__in=user_ids).update(**updates)
            
            # Log bulk operation
            for user_id in user_ids:
                try:
                    user = User.objects.get(id=user_id)
                    self.log_user_activity(
                        user, 
                        'bulk_update', 
                        f"Bulk update applied: {updates}"
                    )
                except User.DoesNotExist:
                    continue
            
            self.logger.info(f"Bulk updated {updated_count} users with {updates}")
            return updated_count
            
        except Exception as e:
            self.logger.error(f"Error in bulk update: {str(e)}")
            raise
    
    def assign_role_to_users(self, user_ids: List[int], role_name: str) -> int:
        """Assign role to multiple users"""
        try:
            role = UserRole.objects.get(name=role_name, is_active=True)
            users = User.objects.filter(id__in=user_ids)
            
            # Create Django group if it doesn't exist
            group, created = Group.objects.get_or_create(name=role_name)
            if created:
                group.permissions.set(role.permissions.all())
            
            # Assign users to group
            for user in users:
                user.groups.add(group)
                self.log_user_activity(
                    user, 
                    'role_assigned', 
                    f"Role '{role_name}' assigned"
                )
            
            count = users.count()
            self.logger.info(f"Assigned role '{role_name}' to {count} users")
            return count
            
        except UserRole.DoesNotExist:
            self.logger.error(f"Role '{role_name}' not found")
            raise ValueError(f"Role '{role_name}' not found")
        except Exception as e:
            self.logger.error(f"Error assigning role: {str(e)}")
            raise
    
    def get_user_permissions(self, user: User) -> List[str]:
        """Get all permissions for a user including role-based permissions"""
        permissions = set()
        
        # Direct user permissions
        permissions.update(user.user_permissions.values_list('codename', flat=True))
        
        # Group permissions
        permissions.update(
            Permission.objects.filter(
                group__user=user
            ).values_list('codename', flat=True)
        )
        
        # Custom role permissions
        for group in user.groups.all():
            try:
                role = UserRole.objects.get(name=group.name, is_active=True)
                permissions.update(role.permissions.values_list('codename', flat=True))
            except UserRole.DoesNotExist:
                continue
        
        return list(permissions)
    
    def log_user_activity(self, user: User, activity_type: str, description: str = '', 
                         ip_address: str = None, user_agent: str = '', 
                         metadata: Dict = None) -> UserActivity:
        """Log user activity"""
        try:
            activity = UserActivity.objects.create(
                user=user,
                activity_type=activity_type,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {}
            )
            
            # Update user's last activity
            user.update_last_activity()
            
            return activity
            
        except Exception as e:
            self.logger.error(f"Error logging activity for {user.email}: {str(e)}")
            raise
    
    def get_user_activity_summary(self, user: User, days: int = 30) -> Dict[str, Any]:
        """Get user activity summary"""
        now = timezone.now()
        period_start = now - timedelta(days=days)
        
        activities = UserActivity.objects.filter(
            user=user,
            timestamp__gte=period_start
        )
        
        summary = {
            'total_activities': activities.count(),
            'activity_breakdown': {},
            'recent_activities': [],
            'most_active_days': [],
        }
        
        # Activity breakdown
        breakdown = activities.values('activity_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        summary['activity_breakdown'] = {
            item['activity_type']: item['count'] 
            for item in breakdown
        }
        
        # Recent activities
        recent = activities.order_by('-timestamp')[:10]
        summary['recent_activities'] = [
            {
                'type': activity.activity_type,
                'description': activity.description,
                'timestamp': activity.timestamp,
                'ip_address': activity.ip_address
            }
            for activity in recent
        ]
        
        return summary
    
    def manage_user_sessions(self, user: User, action: str = 'list') -> Any:
        """Manage user sessions"""
        sessions = UserSession.objects.filter(user=user, is_active=True)
        
        if action == 'list':
            return sessions
        elif action == 'terminate_all':
            count = sessions.update(is_active=False)
            self.log_user_activity(user, 'sessions_terminated', f'{count} sessions terminated')
            return count
        elif action == 'cleanup_expired':
            expired_sessions = sessions.filter(
                last_activity__lt=timezone.now() - timedelta(hours=24)
            )
            count = expired_sessions.update(is_active=False)
            return count
        
        return sessions
    
    def send_bulk_notification(self, user_ids: List[int], subject: str, 
                             message: str, notification_type: str = 'email') -> int:
        """Send bulk notifications to users"""
        users = User.objects.filter(id__in=user_ids, is_active=True)
        sent_count = 0
        
        for user in users:
            try:
                if notification_type == 'email' and user.profile.email_notifications:
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False
                    )
                    sent_count += 1
                    
                    self.log_user_activity(
                        user, 
                        'notification_sent', 
                        f'Email notification: {subject}'
                    )
                
                # Add other notification types (SMS, push) here
                
            except Exception as e:
                self.logger.error(f"Error sending notification to {user.email}: {str(e)}")
                continue
        
        self.logger.info(f"Sent {sent_count} notifications out of {users.count()} users")
        return sent_count
    
    def export_user_data(self, user_ids: List[int], format: str = 'csv') -> Dict[str, Any]:
        """Export user data in various formats"""
        users = User.objects.filter(id__in=user_ids).select_related('profile')
        
        data = []
        for user in users:
            user_data = {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'is_staff': user.is_staff,
                'date_joined': user.date_joined,
                'last_login': user.last_login,
                'last_activity': user.last_activity,
                'login_count': user.login_count,
                'preferred_units': user.preferred_units,
                'language': user.language,
                'api_requests_count': user.api_requests_count,
                'api_rate_limit': user.api_rate_limit,
            }
            
            # Add profile data
            if hasattr(user, 'profile'):
                profile = user.profile
                user_data.update({
                    'favorite_cities': profile.favorite_cities,
                    'default_city': profile.default_city,
                    'email_notifications': profile.email_notifications,
                    'sms_notifications': profile.sms_notifications,
                    'push_notifications': profile.push_notifications,
                })
            
            data.append(user_data)
        
        return {
            'data': data,
            'count': len(data),
            'format': format,
            'exported_at': timezone.now()
        }
    
    def cleanup_inactive_users(self, days_inactive: int = 365) -> int:
        """Clean up users who have been inactive for specified days"""
        cutoff_date = timezone.now() - timedelta(days=days_inactive)
        
        inactive_users = User.objects.filter(
            Q(last_activity__lt=cutoff_date) | Q(last_activity__isnull=True),
            is_active=True,
            is_staff=False,
            is_superuser=False
        )
        
        count = inactive_users.count()
        
        # Log before deactivation
        for user in inactive_users:
            self.log_user_activity(
                user, 
                'auto_deactivated', 
                f'Automatically deactivated after {days_inactive} days of inactivity'
            )
        
        # Deactivate users
        inactive_users.update(is_active=False)
        
        self.logger.info(f"Deactivated {count} inactive users")
        return count


class RoleManager:
    """Manage user roles and permissions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_role(self, name: str, description: str = '', 
                   permissions: List[str] = None) -> UserRole:
        """Create a new user role"""
        try:
            role = UserRole.objects.create(
                name=name,
                description=description
            )
            
            if permissions:
                perm_objects = Permission.objects.filter(codename__in=permissions)
                role.permissions.set(perm_objects)
            
            # Create corresponding Django group
            group, created = Group.objects.get_or_create(name=name)
            if permissions:
                group.permissions.set(perm_objects)
            
            self.logger.info(f"Created role: {name}")
            return role
            
        except Exception as e:
            self.logger.error(f"Error creating role {name}: {str(e)}")
            raise
    
    def assign_permissions_to_role(self, role_name: str, permissions: List[str]) -> UserRole:
        """Assign permissions to a role"""
        try:
            role = UserRole.objects.get(name=role_name)
            perm_objects = Permission.objects.filter(codename__in=permissions)
            role.permissions.add(*perm_objects)
            
            # Update corresponding Django group
            try:
                group = Group.objects.get(name=role_name)
                group.permissions.add(*perm_objects)
            except Group.DoesNotExist:
                pass
            
            self.logger.info(f"Added permissions to role {role_name}: {permissions}")
            return role
            
        except UserRole.DoesNotExist:
            self.logger.error(f"Role {role_name} not found")
            raise
        except Exception as e:
            self.logger.error(f"Error assigning permissions to role {role_name}: {str(e)}")
            raise
    
    def get_role_hierarchy(self) -> Dict[str, Any]:
        """Get role hierarchy and permissions"""
        roles = UserRole.objects.filter(is_active=True).prefetch_related('permissions')
        
        hierarchy = {}
        for role in roles:
            hierarchy[role.name] = {
                'description': role.description,
                'permissions': list(role.permissions.values_list('codename', flat=True)),
                'user_count': User.objects.filter(groups__name=role.name).count()
            }
        
        return hierarchy


# Global instances
user_manager = UserManager()
role_manager = RoleManager()
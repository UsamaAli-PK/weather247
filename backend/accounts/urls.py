from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r'management', views.UserManagementViewSet, basename='user-management')

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password, name='change-password'),
    
    # User Profile and Preferences
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('user/', views.UserDetailView.as_view(), name='user-detail'),
    path('preferences/', views.user_preferences, name='user-preferences'),
    path('dashboard/', views.user_dashboard_data, name='user-dashboard'),
    
    # User Activity and Sessions
    path('activity/', views.user_activity_history, name='user-activity'),
    path('sessions/', views.user_sessions, name='user-sessions'),
    
    # User Stats
    path('stats/', views.user_stats, name='user-stats'),
    
    # Admin User Management (Original)
    path('admin/users/', views.admin_users_list, name='admin-users-list'),
    path('admin/users/<int:user_id>/', views.admin_user_detail, name='admin-user-detail'),
    path('admin/users/bulk/', views.admin_bulk_user_operations, name='admin-bulk-operations'),
    path('admin/analytics/', views.admin_user_analytics, name='admin-user-analytics'),
    
    # Enhanced User Management System
    path('admin/analytics-dashboard/', views.UserAnalyticsView.as_view(), name='user-analytics-dashboard'),
    path('admin/search/', views.UserSearchView.as_view(), name='user-search'),
    path('admin/users/<int:user_id>/activity/', views.user_activity_log, name='user-activity-log'),
    path('admin/users/<int:user_id>/sessions/', views.user_sessions_detail, name='user-sessions-detail'),
    
    # Role Management
    path('admin/roles/', views.role_management, name='role-management'),
    path('admin/roles/hierarchy/', views.role_hierarchy, name='role-hierarchy'),
    
    # Include DRF router URLs
    path('api/', include(router.urls)),
]


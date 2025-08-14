"""
Test script for user management system functionality
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from .user_management import user_manager, role_manager
from .models import UserRole, UserActivity, UserProfile

User = get_user_model()


class UserManagementTestCase(TestCase):
    """Test cases for user management system"""
    
    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            email='test1@example.com',
            username='test1',
            password='testpass123',
            first_name='Test',
            last_name='User1'
        )
        
        self.user2 = User.objects.create_user(
            email='test2@example.com',
            username='test2',
            password='testpass123',
            first_name='Test',
            last_name='User2'
        )
    
    def test_user_statistics(self):
        """Test user statistics functionality"""
        stats = user_manager.get_user_statistics(30)
        
        self.assertIn('total_users', stats)
        self.assertIn('active_users', stats)
        self.assertIn('verified_users', stats)
        self.assertGreaterEqual(stats['total_users'], 2)
    
    def test_user_activity_logging(self):
        """Test user activity logging"""
        activity = user_manager.log_user_activity(
            user=self.user1,
            activity_type='login',
            description='Test login',
            ip_address='127.0.0.1'
        )
        
        self.assertEqual(activity.user, self.user1)
        self.assertEqual(activity.activity_type, 'login')
        self.assertEqual(activity.description, 'Test login')
        self.assertEqual(activity.ip_address, '127.0.0.1')
    
    def test_bulk_user_operations(self):
        """Test bulk user operations"""
        user_ids = [self.user1.id, self.user2.id]
        updates = {'is_verified': True}
        
        count = user_manager.bulk_update_users(user_ids, updates)
        
        self.assertEqual(count, 2)
        
        # Refresh from database
        self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        
        self.assertTrue(self.user1.is_verified)
        self.assertTrue(self.user2.is_verified)
    
    def test_role_creation(self):
        """Test role creation and management"""
        role = role_manager.create_role(
            name='Test Role',
            description='A test role',
            permissions=['add_user', 'change_user']
        )
        
        self.assertEqual(role.name, 'Test Role')
        self.assertEqual(role.description, 'A test role')
        self.assertTrue(role.is_active)
    
    def test_user_activity_summary(self):
        """Test user activity summary"""
        # Create some activities
        user_manager.log_user_activity(self.user1, 'login', 'Login test')
        user_manager.log_user_activity(self.user1, 'api_request', 'API test')
        
        summary = user_manager.get_user_activity_summary(self.user1, 30)
        
        self.assertIn('total_activities', summary)
        self.assertIn('activity_breakdown', summary)
        self.assertIn('recent_activities', summary)
        self.assertGreaterEqual(summary['total_activities'], 2)
    
    def test_user_profile_creation(self):
        """Test user profile creation via signal"""
        # Profile should be created automatically
        self.assertTrue(hasattr(self.user1, 'profile'))
        self.assertIsInstance(self.user1.profile, UserProfile)
    
    def test_export_user_data(self):
        """Test user data export"""
        user_ids = [self.user1.id, self.user2.id]
        export_data = user_manager.export_user_data(user_ids, 'json')
        
        self.assertIn('data', export_data)
        self.assertIn('count', export_data)
        self.assertEqual(export_data['count'], 2)
        self.assertEqual(len(export_data['data']), 2)


def run_manual_tests():
    """Run manual tests for user management system"""
    print("=== User Management System Tests ===")
    
    # Test 1: User Statistics
    print("\n1. Testing user statistics...")
    stats = user_manager.get_user_statistics(30)
    print(f"Total users: {stats['total_users']}")
    print(f"Active users: {stats['active_users']}")
    print(f"Verified users: {stats['verified_users']}")
    
    # Test 2: Create a test user
    print("\n2. Creating test user...")
    try:
        test_user = user_manager.create_user_with_profile(
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        print(f"Created user: {test_user.email}")
        print(f"Profile created: {hasattr(test_user, 'profile')}")
    except Exception as e:
        print(f"User might already exist: {e}")
        test_user = User.objects.get(email='testuser@example.com')
    
    # Test 3: Log user activity
    print("\n3. Testing activity logging...")
    activity = user_manager.log_user_activity(
        user=test_user,
        activity_type='login',
        description='Test login activity',
        ip_address='127.0.0.1'
    )
    print(f"Activity logged: {activity.activity_type} at {activity.timestamp}")
    
    # Test 4: Get activity summary
    print("\n4. Testing activity summary...")
    summary = user_manager.get_user_activity_summary(test_user, 30)
    print(f"Total activities: {summary['total_activities']}")
    print(f"Activity types: {list(summary['activity_breakdown'].keys())}")
    
    # Test 5: Create a role
    print("\n5. Testing role creation...")
    try:
        role = role_manager.create_role(
            name='Test Manager',
            description='Test role for managers'
        )
        print(f"Created role: {role.name}")
    except Exception as e:
        print(f"Role might already exist: {e}")
    
    # Test 6: Role hierarchy
    print("\n6. Testing role hierarchy...")
    hierarchy = role_manager.get_role_hierarchy()
    print(f"Available roles: {list(hierarchy.keys())}")
    
    print("\n=== All tests completed successfully! ===")


if __name__ == '__main__':
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather247_backend.settings')
    django.setup()
    
    run_manual_tests()
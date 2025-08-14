#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather247_backend.settings')
django.setup()

from accounts.user_management import user_manager, role_manager
from accounts.models import User

def test_user_management():
    print("=== User Management System Test ===")
    
    # Test 1: User Statistics
    print("\n1. User Statistics:")
    stats = user_manager.get_user_statistics(30)
    print(f"   Total users: {stats['total_users']}")
    print(f"   Active users: {stats['active_users']}")
    print(f"   Verified users: {stats['verified_users']}")
    print(f"   Staff users: {stats['staff_users']}")
    
    # Test 2: Test with existing user
    print("\n2. Testing with existing user:")
    user = User.objects.first()
    if user:
        print(f"   User: {user.email}")
        
        # Test activity logging
        try:
            activity = user_manager.log_user_activity(
                user=user,
                activity_type='login',
                description='Test login activity',
                ip_address='127.0.0.1'
            )
            print(f"   Activity logged: {activity.activity_type} at {activity.timestamp}")
        except Exception as e:
            print(f"   Error logging activity: {e}")
        
        # Test activity summary
        try:
            summary = user_manager.get_user_activity_summary(user, 30)
            print(f"   Total activities: {summary['total_activities']}")
            print(f"   Activity types: {list(summary['activity_breakdown'].keys())}")
        except Exception as e:
            print(f"   Error getting activity summary: {e}")
    else:
        print("   No users found in database")
    
    # Test 3: Role Management
    print("\n3. Role Management:")
    try:
        hierarchy = role_manager.get_role_hierarchy()
        print(f"   Available roles: {list(hierarchy.keys())}")
        
        # Try to create a test role
        try:
            role = role_manager.create_role(
                name='Test Role',
                description='A test role for verification'
            )
            print(f"   Created role: {role.name}")
        except Exception as e:
            print(f"   Role creation error (might already exist): {e}")
            
    except Exception as e:
        print(f"   Error in role management: {e}")
    
    # Test 4: Bulk Operations (if we have users)
    print("\n4. Bulk Operations:")
    users = User.objects.all()[:2]  # Get first 2 users
    if users.count() >= 1:
        user_ids = [user.id for user in users]
        try:
            # Test bulk update (just update last_activity)
            from django.utils import timezone
            count = user_manager.bulk_update_users(
                user_ids, 
                {'last_activity': timezone.now()}
            )
            print(f"   Bulk updated {count} users")
        except Exception as e:
            print(f"   Bulk update error: {e}")
    else:
        print("   Not enough users for bulk operations test")
    
    print("\n=== All tests completed! ===")

if __name__ == '__main__':
    test_user_management()
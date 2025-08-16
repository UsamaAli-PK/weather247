#!/usr/bin/env python
"""
Simple script to test authentication without running the full server
"""
import os
import sys
import django
from django.conf import settings

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather247_backend.settings')
django.setup()

from accounts.models import User
from accounts.serializers import UserRegistrationSerializer, UserLoginSerializer
from rest_framework.authtoken.models import Token

def test_registration():
    """Test user registration"""
    print("Testing user registration...")
    
    # Test data
    test_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123',
        'password_confirm': 'testpass123'
    }
    
    # Test serializer
    serializer = UserRegistrationSerializer(data=test_data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        print(f"✅ Registration successful! User: {user.email}, Token: {token.key[:10]}...")
        return user
    else:
        print(f"❌ Registration failed: {serializer.errors}")
        return None

def test_login(email, password):
    """Test user login"""
    print(f"Testing login for {email}...")
    
    # Test data
    test_data = {
        'email': email,
        'password': password
    }
    
    # Test serializer
    serializer = UserLoginSerializer(data=test_data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        print(f"✅ Login successful! User: {user.email}, Token: {token.key[:10]}...")
        return user
    else:
        print(f"❌ Login failed: {serializer.errors}")
        return None

def main():
    print("🧪 Testing Weather247 Authentication System")
    print("=" * 50)
    
    # Clean up any existing test user
    try:
        User.objects.filter(email='test@example.com').delete()
        print("🧹 Cleaned up existing test user")
    except:
        pass
    
    # Test registration
    user = test_registration()
    
    if user:
        # Test login with correct credentials
        test_login('test@example.com', 'testpass123')
        
        # Test login with wrong password
        test_login('test@example.com', 'wrongpassword')
        
        # Test login with wrong email
        test_login('wrong@example.com', 'testpass123')
    
    print("=" * 50)
    print("🏁 Authentication test completed!")

if __name__ == '__main__':
    main()
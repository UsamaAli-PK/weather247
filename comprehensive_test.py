#!/usr/bin/env python
"""
Comprehensive test of Weather247 functionality
"""
import requests
import json

API_BASE_URL = 'http://localhost:8000/api'

def test_authentication():
    """Test authentication system"""
    print("🔐 Testing Authentication System...")
    
    # Test login with existing user
    login_data = {
        'email': 'testuser123@example.com',
        'password': 'testpass123'
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/login/", json=login_data)
        if response.status_code == 200:
            print("✅ Login working")
            return response.json().get('token')
        else:
            print(f"❌ Login failed, trying registration...")
            
            # Try registration if login fails
            reg_data = {
                'username': 'testuser456',
                'email': 'testuser456@example.com',
                'password': 'testpass123',
                'password_confirm': 'testpass123'
            }
            
            response = requests.post(f"{API_BASE_URL}/auth/register/", json=reg_data)
            if response.status_code == 201:
                print("✅ Registration working")
                return response.json().get('token')
            else:
                print(f"❌ Registration also failed: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_weather_apis(token):
    """Test weather API endpoints"""
    print("\n🌤️  Testing Weather APIs...")
    
    headers = {'Authorization': f'Token {token}'}
    
    # Test cities endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/weather/cities/", headers=headers)
        if response.status_code == 200:
            cities = response.json()['results']
            print(f"✅ Cities API working - {len(cities)} cities available")
        else:
            print(f"❌ Cities API failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Cities API error: {e}")
        return False
    
    # Test current weather
    try:
        response = requests.get(f"{API_BASE_URL}/weather/current/?city=New York", headers=headers)
        if response.status_code == 200:
            weather = response.json()
            print("✅ Current weather API working")
        else:
            print(f"❌ Current weather API failed: {response.text}")
    except Exception as e:
        print(f"❌ Current weather API error: {e}")
    
    # Test multiple cities
    try:
        response = requests.get(f"{API_BASE_URL}/weather/multiple/?cities=New York,London", headers=headers)
        if response.status_code == 200:
            print("✅ Multiple cities API working")
        else:
            print(f"❌ Multiple cities API failed: {response.text}")
    except Exception as e:
        print(f"❌ Multiple cities API error: {e}")
    
    return True

def test_route_planning(token):
    """Test route planning endpoints"""
    print("\n🗺️  Testing Route Planning APIs...")
    
    headers = {'Authorization': f'Token {token}'}
    
    try:
        response = requests.get(f"{API_BASE_URL}/routes/routes/", headers=headers)
        if response.status_code == 200:
            print("✅ Routes API working")
        else:
            print(f"❌ Routes API failed: {response.text}")
    except Exception as e:
        print(f"❌ Routes API error: {e}")

def test_user_profile(token):
    """Test user profile endpoints"""
    print("\n👤 Testing User Profile APIs...")
    
    headers = {'Authorization': f'Token {token}'}
    
    try:
        response = requests.get(f"{API_BASE_URL}/auth/profile/", headers=headers)
        if response.status_code == 200:
            print("✅ User profile API working")
        else:
            print(f"❌ User profile API failed: {response.text}")
    except Exception as e:
        print(f"❌ User profile API error: {e}")

def main():
    print("🧪 Weather247 Comprehensive Testing")
    print("=" * 50)
    
    # Test authentication
    token = test_authentication()
    
    if token:
        # Test weather APIs
        test_weather_apis(token)
        
        # Test route planning
        test_route_planning(token)
        
        # Test user profile
        test_user_profile(token)
    
    print("\n" + "=" * 50)
    print("🏁 Comprehensive testing completed!")

if __name__ == '__main__':
    main()
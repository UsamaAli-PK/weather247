#!/usr/bin/env python
"""
Test the Weather247 API endpoints
"""
import requests
import json

API_BASE_URL = 'http://localhost:8000/api'

def test_registration():
    """Test user registration API"""
    print("🧪 Testing Registration API...")
    
    url = f"{API_BASE_URL}/auth/register/"
    data = {
        'username': 'apitest',
        'email': 'apitest@example.com',
        'password': 'testpass123',
        'password_confirm': 'testpass123'
    }
    
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Registration successful! Token: {result.get('token', 'N/A')[:10]}...")
            return result.get('token')
        else:
            print(f"❌ Registration failed: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Django server. Make sure it's running on localhost:8000")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_login():
    """Test user login API"""
    print("\n🧪 Testing Login API...")
    
    url = f"{API_BASE_URL}/auth/login/"
    data = {
        'email': 'apitest@example.com',
        'password': 'testpass123'
    }
    
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login successful! Token: {result.get('token', 'N/A')[:10]}...")
            return result.get('token')
        else:
            print(f"❌ Login failed: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Django server. Make sure it's running on localhost:8000")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_weather_api(token=None):
    """Test weather API"""
    print("\n🧪 Testing Weather API...")
    
    url = f"{API_BASE_URL}/weather/cities/"
    headers = {'Content-Type': 'application/json'}
    
    if token:
        headers['Authorization'] = f'Token {token}'
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ Weather API working!")
        else:
            print(f"❌ Weather API failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Django server. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🌦️  Weather247 API Testing")
    print("=" * 40)
    
    # Test registration
    token = test_registration()
    
    # Test login
    if not token:
        token = test_login()
    
    # Test weather API
    test_weather_api(token)
    
    print("\n" + "=" * 40)
    print("🏁 API testing completed!")

if __name__ == '__main__':
    main()
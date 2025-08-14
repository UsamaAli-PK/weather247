#!/usr/bin/env python
"""
Test weather data validation
"""
import requests
import json

API_BASE_URL = 'http://localhost:8000/api'

def test_validation():
    """Test data validation features"""
    print("🔍 Testing Data Validation...")
    
    # Get auth token
    login_data = {
        'email': 'testuser123@example.com',
        'password': 'testpass123'
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/login/", json=login_data)
        if response.status_code == 200:
            token = response.json().get('token')
            headers = {'Authorization': f'Token {token}'}
        else:
            print("❌ Could not get auth token")
            return
    except Exception as e:
        print(f"❌ Auth error: {e}")
        return
    
    # Test 1: Valid city data
    print("\n✅ Testing Valid City Data...")
    valid_city = {
        'name': 'Madrid',
        'country': 'ES',
        'latitude': 40.4168,
        'longitude': -3.7038
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/weather/cities/add/", json=valid_city, headers=headers)
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Valid city accepted: {result['message']}")
        else:
            print(f"❌ Valid city rejected: {response.text}")
    except Exception as e:
        print(f"❌ Valid city error: {e}")
    
    # Test 2: Invalid city name
    print("\n❌ Testing Invalid City Name...")
    invalid_city_name = {
        'name': 'A',  # Too short
        'country': 'ES',
        'latitude': 40.4168,
        'longitude': -3.7038
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/weather/cities/add/", json=invalid_city_name, headers=headers)
        if response.status_code == 400:
            error = response.json().get('error', '')
            print(f"✅ Invalid city name rejected: {error}")
        else:
            print(f"❌ Invalid city name accepted: {response.text}")
    except Exception as e:
        print(f"❌ Invalid city name error: {e}")
    
    # Test 3: Invalid coordinates
    print("\n❌ Testing Invalid Coordinates...")
    invalid_coords = {
        'name': 'TestCity',
        'country': 'XX',
        'latitude': 91.0,  # Invalid latitude
        'longitude': -3.7038
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/weather/cities/add/", json=invalid_coords, headers=headers)
        if response.status_code == 400:
            error = response.json().get('error', '')
            print(f"✅ Invalid coordinates rejected: {error}")
        else:
            print(f"❌ Invalid coordinates accepted: {response.text}")
    except Exception as e:
        print(f"❌ Invalid coordinates error: {e}")
    
    # Test 4: Missing required fields
    print("\n❌ Testing Missing Required Fields...")
    missing_fields = {
        'name': 'TestCity'
        # Missing country, latitude, longitude
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/weather/cities/add/", json=missing_fields, headers=headers)
        if response.status_code == 400:
            error = response.json().get('error', '')
            print(f"✅ Missing fields rejected: {error}")
        else:
            print(f"❌ Missing fields accepted: {response.text}")
    except Exception as e:
        print(f"❌ Missing fields error: {e}")
    
    # Test 5: SQL injection attempt
    print("\n🛡️  Testing SQL Injection Protection...")
    sql_injection = {
        'name': "'; DROP TABLE cities; --",
        'country': 'XX',
        'latitude': 40.0,
        'longitude': -3.0
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/weather/cities/add/", json=sql_injection, headers=headers)
        if response.status_code == 400:
            error = response.json().get('error', '')
            print(f"✅ SQL injection attempt blocked: {error}")
        else:
            print(f"⚠️  SQL injection attempt processed (check if sanitized)")
    except Exception as e:
        print(f"❌ SQL injection test error: {e}")
    
    # Test 6: XSS attempt
    print("\n🛡️  Testing XSS Protection...")
    xss_attempt = {
        'name': '<script>alert("xss")</script>',
        'country': 'XX',
        'latitude': 40.0,
        'longitude': -3.0
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/weather/cities/add/", json=xss_attempt, headers=headers)
        if response.status_code == 400:
            error = response.json().get('error', '')
            print(f"✅ XSS attempt blocked: {error}")
        else:
            print(f"⚠️  XSS attempt processed (check if sanitized)")
    except Exception as e:
        print(f"❌ XSS test error: {e}")

if __name__ == '__main__':
    print("🧪 Weather247 Data Validation Test")
    print("=" * 50)
    test_validation()
    print("=" * 50)
    print("🏁 Validation test completed!")
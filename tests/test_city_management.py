#!/usr/bin/env python
"""
Test city management features
"""
import requests
import json

API_BASE_URL = 'http://localhost:8000/api'

def test_city_management():
    """Test city management features"""
    print("🏙️  Testing City Management Features...")
    
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
    
    # Test 1: Search cities
    print("\n🔍 Testing City Search...")
    try:
        response = requests.get(f"{API_BASE_URL}/weather/cities/search/?q=lon", headers=headers)
        if response.status_code == 200:
            results = response.json().get('results', [])
            print(f"✅ City search working - found {len(results)} results")
            for result in results[:3]:
                print(f"   - {result['name']}, {result['country']} (exists: {result['exists']})")
        else:
            print(f"❌ City search failed: {response.text}")
    except Exception as e:
        print(f"❌ City search error: {e}")
    
    # Test 2: Add a new city
    print("\n➕ Testing Add City...")
    new_city_data = {
        'name': 'Barcelona',
        'country': 'ES',
        'latitude': 41.3851,
        'longitude': 2.1734
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/weather/cities/add/", json=new_city_data, headers=headers)
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Add city working: {result['message']}")
            if 'city' in result:
                city = result['city']
                print(f"   Added: {city['name']}, {city['country']} (ID: {city['id']})")
        else:
            print(f"❌ Add city failed: {response.text}")
    except Exception as e:
        print(f"❌ Add city error: {e}")
    
    # Test 3: List all cities (should include new one)
    print("\n📋 Testing Updated City List...")
    try:
        response = requests.get(f"{API_BASE_URL}/weather/cities/", headers=headers)
        if response.status_code == 200:
            cities = response.json()['results']
            print(f"✅ City list updated - now {len(cities)} cities")
            barcelona = next((c for c in cities if c['name'] == 'Barcelona'), None)
            if barcelona:
                print(f"   ✅ Barcelona found in city list")
            else:
                print(f"   ⚠️  Barcelona not found in city list")
        else:
            print(f"❌ City list failed: {response.text}")
    except Exception as e:
        print(f"❌ City list error: {e}")
    
    # Test 4: Get weather for new city
    print("\n🌤️  Testing Weather for New City...")
    try:
        response = requests.get(f"{API_BASE_URL}/weather/current/?city=Barcelona", headers=headers)
        if response.status_code == 200:
            weather = response.json()
            if 'current' in weather:
                temp = weather['current'].get('temperature', 'N/A')
                condition = weather['current'].get('weather_condition', 'N/A')
                print(f"✅ Weather for Barcelona: {temp}°C, {condition}")
            else:
                print(f"⚠️  Weather data structure unexpected")
        else:
            print(f"❌ Weather for Barcelona failed: {response.text}")
    except Exception as e:
        print(f"❌ Weather for Barcelona error: {e}")

if __name__ == '__main__':
    print("🧪 Weather247 City Management Test")
    print("=" * 50)
    test_city_management()
    print("=" * 50)
    print("🏁 City management test completed!")
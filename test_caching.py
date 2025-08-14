#!/usr/bin/env python
"""
Test Redis caching system
"""
import requests
import json
import time

API_BASE_URL = 'http://localhost:8000/api'

def test_caching_system():
    """Test caching functionality"""
    print("🗄️  Testing Redis Caching System...")
    
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
    
    # Test 1: Cache statistics
    print("\n📊 Testing Cache Statistics...")
    try:
        response = requests.get(f"{API_BASE_URL}/weather/cache/stats/", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Cache stats retrieved:")
            print(f"   Status: {stats.get('status', 'Unknown')}")
            print(f"   Backend: {stats.get('cache_backend', 'Unknown')}")
            print(f"   Weather TTL: {stats.get('cache_keys_info', {}).get('weather_ttl', 'N/A')}s")
        else:
            print(f"❌ Cache stats failed: {response.text}")
    except Exception as e:
        print(f"❌ Cache stats error: {e}")
    
    # Test 2: Performance test - First request (cache miss)
    print("\n⏱️  Testing Cache Performance...")
    city_name = "London"
    
    # First request - should be cache miss
    start_time = time.time()
    try:
        response = requests.get(f"{API_BASE_URL}/weather/current/?city={city_name}", headers=headers)
        first_request_time = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ First request (cache miss): {first_request_time:.3f}s")
        else:
            print(f"❌ First request failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ First request error: {e}")
        return
    
    # Second request - should be cache hit (if caching is working)
    start_time = time.time()
    try:
        response = requests.get(f"{API_BASE_URL}/weather/current/?city={city_name}", headers=headers)
        second_request_time = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ Second request (potential cache hit): {second_request_time:.3f}s")
            
            # Compare performance
            if second_request_time < first_request_time * 0.8:
                print(f"🚀 Cache appears to be working! {((first_request_time - second_request_time) / first_request_time * 100):.1f}% faster")
            else:
                print(f"⚠️  Cache may not be working or data was regenerated")
        else:
            print(f"❌ Second request failed: {response.text}")
    except Exception as e:
        print(f"❌ Second request error: {e}")
    
    # Test 3: Cache invalidation
    print("\n🗑️  Testing Cache Invalidation...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/weather/cache/clear/", 
            json={'city': city_name}, 
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Cache cleared: {result['message']}")
        else:
            print(f"❌ Cache clear failed: {response.text}")
    except Exception as e:
        print(f"❌ Cache clear error: {e}")
    
    # Test 4: Multiple cities caching
    print("\n🌍 Testing Multiple Cities Caching...")
    cities = ["New York", "Tokyo", "Paris"]
    
    for city in cities:
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE_URL}/weather/current/?city={city}", headers=headers)
            request_time = time.time() - start_time
            
            if response.status_code == 200:
                weather = response.json()
                temp = weather.get('current', {}).get('temperature', 'N/A')
                print(f"✅ {city}: {temp}°C ({request_time:.3f}s)")
            else:
                print(f"❌ {city}: Failed - {response.text}")
        except Exception as e:
            print(f"❌ {city}: Error - {e}")
    
    # Test 5: Cache hit rate test
    print("\n🎯 Testing Cache Hit Rate...")
    test_cities = ["London", "New York", "London", "Tokyo", "London"]  # London repeated for cache hits
    
    total_time = 0
    for i, city in enumerate(test_cities):
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE_URL}/weather/current/?city={city}", headers=headers)
            request_time = time.time() - start_time
            total_time += request_time
            
            if response.status_code == 200:
                print(f"   Request {i+1} ({city}): {request_time:.3f}s")
            else:
                print(f"   Request {i+1} ({city}): Failed")
        except Exception as e:
            print(f"   Request {i+1} ({city}): Error - {e}")
    
    print(f"📈 Total time for {len(test_cities)} requests: {total_time:.3f}s")
    print(f"📈 Average time per request: {total_time/len(test_cities):.3f}s")

if __name__ == '__main__':
    print("🧪 Weather247 Caching System Test")
    print("=" * 50)
    test_caching_system()
    print("=" * 50)
    print("🏁 Caching test completed!")
#!/usr/bin/env python
"""
Test error handling and fallback systems
"""
import requests
import json
import time

API_BASE_URL = 'http://localhost:8000/api'

def test_error_handling():
    """Test error handling and fallback functionality"""
    print("🛡️  Testing Error Handling & Fallback Systems...")
    
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
    
    # Test 1: System Health Check
    print("\n🏥 Testing System Health Check...")
    try:
        response = requests.get(f"{API_BASE_URL}/weather/health/")
        if response.status_code in [200, 206, 503]:
            health = response.json()
            print(f"✅ Health check response received:")
            print(f"   Overall Status: {health.get('overall_status', 'Unknown')}")
            print(f"   Primary Service: {health.get('primary_service', {}).get('status', 'Unknown')}")
            print(f"   Cache Status: {'Healthy' if health.get('cache_status') else 'Unhealthy'}")
            print(f"   Database: {health.get('database', {}).get('status', 'Unknown')}")
            
            if response.status_code == 200:
                print("✅ All systems healthy")
            elif response.status_code == 206:
                print("⚠️  Some systems degraded")
            else:
                print("❌ System unhealthy")
        else:
            print(f"❌ Health check failed: {response.text}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Invalid City Handling
    print("\n🏙️  Testing Invalid City Handling...")
    invalid_cities = [
        "NonExistentCity12345",
        "",
        "   ",
        "City@#$%",
        "A" * 200  # Very long name
    ]
    
    for city in invalid_cities:
        try:
            response = requests.get(f"{API_BASE_URL}/weather/current/?city={city}", headers=headers)
            if response.status_code == 400:
                print(f"✅ Invalid city '{city[:20]}...' properly rejected")
            elif response.status_code == 404:
                print(f"✅ City '{city[:20]}...' not found (expected)")
            elif response.status_code == 200:
                print(f"⚠️  City '{city[:20]}...' unexpectedly accepted")
            else:
                print(f"❓ City '{city[:20]}...' returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing city '{city[:20]}...': {e}")
    
    # Test 3: Network Timeout Simulation
    print("\n⏱️  Testing Network Resilience...")
    # Test with a valid city to see how the system handles potential delays
    test_cities = ["London", "New York", "Tokyo"]
    
    for city in test_cities:
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE_URL}/weather/current/?city={city}", headers=headers, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ {city}: Response in {response_time:.2f}s")
            else:
                print(f"❌ {city}: Failed with status {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"⏱️  {city}: Request timed out (expected for network issues)")
        except Exception as e:
            print(f"❌ {city}: Network error - {e}")
    
    # Test 4: Malformed Request Handling
    print("\n🔧 Testing Malformed Request Handling...")
    malformed_requests = [
        # Missing city parameter
        f"{API_BASE_URL}/weather/current/",
        # Invalid city ID
        f"{API_BASE_URL}/weather/current/99999/",
        # Invalid endpoint
        f"{API_BASE_URL}/weather/invalid-endpoint/",
    ]
    
    for url in malformed_requests:
        try:
            response = requests.get(url, headers=headers)
            if response.status_code in [400, 404, 405]:
                print(f"✅ Malformed request properly handled: {response.status_code}")
            else:
                print(f"⚠️  Unexpected response for malformed request: {response.status_code}")
        except Exception as e:
            print(f"❌ Error with malformed request: {e}")
    
    # Test 5: Rate Limiting Simulation
    print("\n🚦 Testing Rate Limiting Behavior...")
    rapid_requests = []
    
    for i in range(5):
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE_URL}/weather/current/?city=London", headers=headers)
            response_time = time.time() - start_time
            rapid_requests.append({
                'request': i + 1,
                'status': response.status_code,
                'time': response_time
            })
        except Exception as e:
            rapid_requests.append({
                'request': i + 1,
                'status': 'error',
                'error': str(e)
            })
    
    for req in rapid_requests:
        if req['status'] == 200:
            print(f"✅ Request {req['request']}: Success in {req.get('time', 0):.3f}s")
        elif req['status'] == 429:
            print(f"🚦 Request {req['request']}: Rate limited (expected)")
        else:
            print(f"❓ Request {req['request']}: Status {req['status']}")
    
    # Test 6: Data Consistency Check
    print("\n🔍 Testing Data Consistency...")
    try:
        # Make multiple requests for the same city
        city = "Paris"
        responses = []
        
        for i in range(3):
            response = requests.get(f"{API_BASE_URL}/weather/current/?city={city}", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if 'current' in data:
                    responses.append({
                        'temperature': data['current'].get('temperature'),
                        'condition': data['current'].get('weather_condition'),
                        'timestamp': data['current'].get('timestamp')
                    })
        
        if len(responses) >= 2:
            # Check if data is reasonably consistent (allowing for cache updates)
            temp_diff = abs(responses[0]['temperature'] - responses[1]['temperature'])
            if temp_diff <= 5:  # Allow 5 degree difference
                print(f"✅ Data consistency check passed (temp diff: {temp_diff}°C)")
            else:
                print(f"⚠️  Large temperature difference detected: {temp_diff}°C")
        else:
            print("❌ Insufficient responses for consistency check")
            
    except Exception as e:
        print(f"❌ Data consistency check error: {e}")
    
    # Test 7: Error Response Format
    print("\n📋 Testing Error Response Format...")
    try:
        # Trigger a known error
        response = requests.get(f"{API_BASE_URL}/weather/current/", headers=headers)  # Missing city
        
        if response.status_code == 400:
            error_data = response.json()
            if 'error' in error_data:
                print("✅ Error response properly formatted")
                print(f"   Error message: {error_data['error']}")
            else:
                print("⚠️  Error response missing 'error' field")
        else:
            print(f"❓ Unexpected status code for error test: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error response format test failed: {e}")

if __name__ == '__main__':
    print("🧪 Weather247 Error Handling & Fallback Test")
    print("=" * 60)
    test_error_handling()
    print("=" * 60)
    print("🏁 Error handling test completed!")
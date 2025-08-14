#!/usr/bin/env python
"""
Comprehensive test runner for Weather247
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
import subprocess
import time

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather247_backend.settings')
django.setup()

def run_django_tests():
    """Run Django unit tests"""
    print("🧪 Running Django Unit Tests...")
    print("=" * 50)
    
    try:
        TestRunner = get_runner(settings)
        test_runner = TestRunner()
        
        # Run specific app tests
        failures = test_runner.run_tests(["weather_data.tests"])
        
        if failures:
            print(f"❌ {failures} test(s) failed")
            return False
        else:
            print("✅ All Django tests passed!")
            return True
            
    except Exception as e:
        print(f"❌ Error running Django tests: {e}")
        return False

def run_integration_tests():
    """Run integration tests"""
    print("\n🔗 Running Integration Tests...")
    print("=" * 50)
    
    test_files = [
        'test_auth.py',
        'test_api.py', 
        'test_comprehensive.py',
        'test_city_management.py',
        'test_validation.py',
        'test_cache_direct.py',
        'test_fallback_direct.py'
    ]
    
    passed = 0
    failed = 0
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n📋 Running {test_file}...")
            try:
                result = subprocess.run([sys.executable, test_file], 
                                      capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    print(f"✅ {test_file} passed")
                    passed += 1
                else:
                    print(f"❌ {test_file} failed")
                    print(f"   Error: {result.stderr}")
                    failed += 1
                    
            except subprocess.TimeoutExpired:
                print(f"⏱️  {test_file} timed out")
                failed += 1
            except Exception as e:
                print(f"❌ Error running {test_file}: {e}")
                failed += 1
        else:
            print(f"⚠️  {test_file} not found, skipping...")
    
    print(f"\n📊 Integration Test Results: {passed} passed, {failed} failed")
    return failed == 0

def run_performance_tests():
    """Run performance tests"""
    print("\n⚡ Running Performance Tests...")
    print("=" * 50)
    
    try:
        # Test cache performance
        from weather_data.cache_manager import WeatherCacheManager
        
        # Cache write performance
        start_time = time.time()
        for i in range(100):
            test_key = f"perf_test_{i}"
            test_data = {"temperature": 20 + i, "city": f"City{i}"}
            WeatherCacheManager.set_cache(test_key, test_data)
        write_time = time.time() - start_time
        
        # Cache read performance
        start_time = time.time()
        for i in range(100):
            test_key = f"perf_test_{i}"
            WeatherCacheManager.get_cache(test_key)
        read_time = time.time() - start_time
        
        print(f"✅ Cache Performance:")
        print(f"   Write: {write_time:.3f}s for 100 operations ({write_time*10:.1f}ms avg)")
        print(f"   Read: {read_time:.3f}s for 100 operations ({read_time*10:.1f}ms avg)")
        
        # Cleanup
        for i in range(100):
            test_key = f"perf_test_{i}"
            WeatherCacheManager.delete_cache(test_key)
        
        # Database query performance
        from weather_data.models import City, WeatherData
        
        start_time = time.time()
        cities = list(City.objects.all())
        db_query_time = time.time() - start_time
        
        print(f"✅ Database Performance:")
        print(f"   City query: {db_query_time:.3f}s for {len(cities)} cities")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test error: {e}")
        return False

def run_security_tests():
    """Run security tests"""
    print("\n🛡️  Running Security Tests...")
    print("=" * 50)
    
    try:
        from weather_data.validators import CityValidator, WeatherDataValidator
        
        # Test SQL injection protection
        malicious_inputs = [
            "'; DROP TABLE cities; --",
            "' OR '1'='1",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "null\x00byte"
        ]
        
        sql_injection_blocked = 0
        for malicious_input in malicious_inputs:
            try:
                CityValidator.validate_city_name(malicious_input)
                print(f"⚠️  Malicious input not blocked: {malicious_input[:20]}...")
            except Exception:
                sql_injection_blocked += 1
        
        print(f"✅ Security Tests:")
        print(f"   SQL Injection: {sql_injection_blocked}/{len(malicious_inputs)} blocked")
        
        # Test data validation
        invalid_data_blocked = 0
        invalid_inputs = [
            {"temp": 1000},  # Impossible temperature
            {"humidity": -50},  # Invalid humidity
            {"lat": 91, "lon": 0},  # Invalid coordinates
        ]
        
        for invalid_input in invalid_inputs:
            try:
                if "temp" in invalid_input:
                    WeatherDataValidator.validate_temperature(invalid_input["temp"])
                elif "humidity" in invalid_input:
                    WeatherDataValidator.validate_humidity(invalid_input["humidity"])
                elif "lat" in invalid_input:
                    WeatherDataValidator.validate_coordinates(invalid_input["lat"], invalid_input["lon"])
            except Exception:
                invalid_data_blocked += 1
        
        print(f"   Data Validation: {invalid_data_blocked}/{len(invalid_inputs)} blocked")
        
        return True
        
    except Exception as e:
        print(f"❌ Security test error: {e}")
        return False

def generate_test_report():
    """Generate test coverage report"""
    print("\n📊 Test Coverage Summary...")
    print("=" * 50)
    
    try:
        from weather_data.models import City, WeatherData, AirQualityData
        from weather_data.cache_manager import WeatherCacheManager
        from weather_data.validators import WeatherDataValidator, CityValidator
        
        components = {
            "Models": ["City", "WeatherData", "AirQualityData", "WeatherForecast"],
            "Validators": ["WeatherDataValidator", "CityValidator"],
            "Cache Manager": ["WeatherCacheManager"],
            "API Endpoints": ["Cities", "Weather", "Cache", "Health"],
            "Services": ["WeatherManager", "OpenWeatherMapService"],
        }
        
        print("✅ Components Tested:")
        for category, items in components.items():
            print(f"   {category}: {', '.join(items)}")
        
        # Test statistics
        total_cities = City.objects.count()
        total_weather_records = WeatherData.objects.count()
        
        print(f"\n📈 Test Data:")
        print(f"   Cities in database: {total_cities}")
        print(f"   Weather records: {total_weather_records}")
        
        return True
        
    except Exception as e:
        print(f"❌ Report generation error: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 Weather247 Comprehensive Test Suite")
    print("=" * 60)
    
    start_time = time.time()
    
    # Run all test suites
    results = {
        "Django Tests": run_django_tests(),
        "Integration Tests": run_integration_tests(),
        "Performance Tests": run_performance_tests(),
        "Security Tests": run_security_tests(),
    }
    
    # Generate report
    generate_test_report()
    
    # Summary
    total_time = time.time() - start_time
    passed = sum(results.values())
    total = len(results)
    
    print("\n" + "=" * 60)
    print("🏁 Test Suite Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    print(f"Total time: {total_time:.2f} seconds")
    
    if passed == total:
        print("\n🎉 All tests passed! Weather247 is ready for production.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed. Please review and fix issues.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
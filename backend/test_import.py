#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather247_backend.settings')
django.setup()

try:
    print("Testing imports...")
    
    # Test basic imports
    import psutil
    print("✓ psutil imported successfully")
    
    from django.utils import timezone
    print("✓ Django timezone imported successfully")
    
    from weather_data.models import SystemMetrics, SystemAlert, SystemHealthCheck
    print("✓ Models imported successfully")
    
    from accounts.models import User
    print("✓ User model imported successfully")
    
    # Test the system monitoring module
    import weather_data.system_monitoring as sm
    print(f"✓ System monitoring module imported, contents: {[x for x in dir(sm) if not x.startswith('_')]}")
    
    # Try to import the classes directly
    from weather_data.system_monitoring import SystemMonitor, SystemDiagnostics
    print("✓ SystemMonitor and SystemDiagnostics imported successfully")
    
    # Try to import the global instances
    from weather_data.system_monitoring import system_monitor, system_diagnostics
    print("✓ Global instances imported successfully")
    
    print("All imports successful!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
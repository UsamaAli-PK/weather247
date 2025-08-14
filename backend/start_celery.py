#!/usr/bin/env python
"""
Script to start Celery worker and beat scheduler for weather data processing
"""
import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather247_backend.settings')

def start_celery_worker():
    """Start Celery worker"""
    print("Starting Celery worker...")
    worker_cmd = [
        sys.executable, '-m', 'celery', '-A', 'weather247_backend', 'worker',
        '--loglevel=info',
        '--concurrency=4',
        '--queues=weather_refresh,maintenance,cache_warming,monitoring,analytics,celery'
    ]
    
    return subprocess.Popen(worker_cmd, cwd=project_dir)

def start_celery_beat():
    """Start Celery beat scheduler"""
    print("Starting Celery beat scheduler...")
    beat_cmd = [
        sys.executable, '-m', 'celery', '-A', 'weather247_backend', 'beat',
        '--loglevel=info',
        '--scheduler=django_celery_beat.schedulers:DatabaseScheduler'
    ]
    
    return subprocess.Popen(beat_cmd, cwd=project_dir)

def start_flower_monitor():
    """Start Flower monitoring (optional)"""
    print("Starting Flower monitoring...")
    flower_cmd = [
        sys.executable, '-m', 'celery', '-A', 'weather247_backend', 'flower',
        '--port=5555'
    ]
    
    return subprocess.Popen(flower_cmd, cwd=project_dir)

def main():
    """Main function to start all Celery services"""
    processes = []
    
    try:
        # Start worker
        worker_process = start_celery_worker()
        processes.append(('worker', worker_process))
        time.sleep(2)  # Give worker time to start
        
        # Start beat scheduler
        beat_process = start_celery_beat()
        processes.append(('beat', beat_process))
        time.sleep(2)  # Give beat time to start
        
        # Optionally start Flower monitoring
        try:
            flower_process = start_flower_monitor()
            processes.append(('flower', flower_process))
            print("Flower monitoring available at http://localhost:5555")
        except Exception as e:
            print(f"Could not start Flower monitoring: {e}")
        
        print("\nCelery services started successfully!")
        print("Worker: Processing background tasks")
        print("Beat: Scheduling periodic tasks")
        print("Press Ctrl+C to stop all services")
        
        # Wait for processes
        while True:
            time.sleep(1)
            # Check if any process has died
            for name, process in processes:
                if process.poll() is not None:
                    print(f"{name} process has stopped unexpectedly")
                    return 1
                    
    except KeyboardInterrupt:
        print("\nShutting down Celery services...")
        
        # Terminate all processes
        for name, process in processes:
            print(f"Stopping {name}...")
            process.terminate()
            
        # Wait for graceful shutdown
        time.sleep(5)
        
        # Force kill if still running
        for name, process in processes:
            if process.poll() is None:
                print(f"Force killing {name}...")
                process.kill()
        
        print("All services stopped.")
        return 0
        
    except Exception as e:
        print(f"Error starting Celery services: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
"""
Simple system monitoring test
"""
import logging

logger = logging.getLogger('weather247')

class SystemMonitor:
    """Main system monitoring service"""
    
    def __init__(self):
        self.alert_thresholds = {
            'cpu_usage': {'warning': 80.0, 'critical': 95.0},
        }
    
    def collect_system_metrics(self):
        """Collect basic system metrics"""
        return {'test': 'data'}

# Global instance
system_monitor = SystemMonitor()

print("System monitoring module loaded successfully")
#!/usr/bin/env python3
"""
Network Monitoring Service
Runs continuous network scanning and compliance checking
"""

import os
import sys
import time
import logging
from datetime import datetime
import requests

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app.services.monitoring_service import MonitoringService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/monitor.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def main():
    """Main monitoring loop."""
    # Get configuration from environment
    network_range = os.getenv('NETWORK_RANGE', '192.168.1.0/24')
    poll_interval = int(os.getenv('POLL_INTERVAL', '30'))
    
    log.info("Starting Network Monitoring Service")
    log.info(f"Network Range: {network_range}")
    log.info(f"Poll Interval: {poll_interval}s")
    
    # Create monitoring service
    monitoring = MonitoringService(network_range=network_range, poll_interval=poll_interval)
    
    # Start monitoring via API
    try:
        response = requests.post('http://localhost:5000/api/monitoring/start')
        if response.status_code == 200:
            log.info("Monitoring started successfully via API")
        else:
            log.warning(f"Failed to start monitoring via API: {response.status_code}")
            # Start directly
            monitoring.start()
    except requests.exceptions.ConnectionError:
        log.warning("Backend not available, starting monitoring directly")
        monitoring.start()
    except Exception as e:
        log.error(f"Error starting monitoring: {e}")
        # Start directly as fallback
        monitoring.start()


if __name__ == '__main__':
    main()

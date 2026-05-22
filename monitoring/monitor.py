#!/usr/bin/env python3
"""
Network Monitoring Service
Runs continuous network scanning and compliance checking
"""

import os
import sys
import logging
import requests
from dotenv import load_dotenv

# Resolve paths: backend code uses `from app...` (same as backend/main.py)
MONITOR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(MONITOR_DIR, '..'))
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')

load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# SQLite DB path is relative to the backend working directory
os.chdir(BACKEND_DIR)

from app.services.monitoring_service import MonitoringService

# Ensure log directory exists
LOG_DIR = os.path.join(MONITOR_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'monitor.log')),
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
    
    # Start monitoring directly (not via API)
    try:
        monitoring.start()
    except KeyboardInterrupt:
        log.info("Monitoring stopped by user")
    except Exception as e:
        log.error(f"Error in monitoring: {e}")


if __name__ == '__main__':
    main()

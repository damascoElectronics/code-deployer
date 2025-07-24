#!/usr/bin/env python3
"""
Container 2 - Log Collector (VM2)
This will eventually monitor directories and ship log files
"""

import time
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('container2')

def main():
    """Main function for Container 2 - Log Collector"""
    logger.info("Container 2 (Log Collector) starting up...")
    logger.info("Running on VM2")
    
    # Show environment info (useful for debugging deployment)
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Hostname: {os.uname().nodename if hasattr(os, 'uname') else 'unknown'}")
    
    # Continuous loop to keep container running
    while True:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] Hello from Container 2 on VM2! Ready to collect logs.")
        logger.info("Monitoring for new log files...")
        
        # Sleep for 30 seconds
        time.sleep(30)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Container 2 shutting down gracefully...")
    except Exception as e:
        logger.error(f"Error in Container 2: {e}")
        raise
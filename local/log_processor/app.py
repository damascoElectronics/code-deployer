#!/usr/bin/env python3
"""
Container 1 - Log Processor (VM1)
This will eventually process logs and store them in a database
"""

import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('container1')

def main():
    """Main function for Container 1  - Log Processor"""
    logger.info("Container 1 (Log Processor) starting up...")
    logger.info("Running on VM1")
    
    # Continuous loop to keep container running
    while True:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] Hello from Container 1 on VM1! Ready to process logs.")
        logger.info("Waiting for logs to process...")
        
        # Sleep for 30 seconds
        time.sleep(30)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Container 1 shutting down gracefully...")
    except Exception as e:
        logger.error(f"Error in Container 1: {e}")
        raise
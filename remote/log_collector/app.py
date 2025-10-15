#!/usr/bin/env python3
"""
Container 2 - Log Collector (VM2)
Main application - orchestrates log generation and HTTP serving
"""

import time
import logging
import random
from datetime import datetime
import os

# Import custom modules
import config
from log_generator import KeyPoolLogSimulator, write_logs_to_file, generate_log_batch
from http_server import LogHTTPServer

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('log_collector')


def print_startup_info():
    """Print startup information"""
    logger.info("=" * 60)
    logger.info("Container 2 (Log Collector) starting up...")
    logger.info(f"Running on VM2 - Site ID: {config.SITE_ID}")
    logger.info(f"Log output directory: {config.LOG_OUTPUT_DIR}")
    logger.info(f"HTTP API: {config.HTTP_HOST}:{config.HTTP_PORT}")
    logger.info(f"Batch size: {config.MIN_BATCH_SIZE}-{config.MAX_BATCH_SIZE} logs")
    logger.info(f"Sleep interval: {config.MIN_SLEEP_SECONDS}-{config.MAX_SLEEP_SECONDS} seconds")
    logger.info("=" * 60)


def main():
    """Main function for Container 2 - Log Collector"""
    
    # Print startup information
    print_startup_info()
    
    # Show environment info
    logger.info(f"Working directory: {os.getcwd()}")
    if hasattr(os, 'uname'):
        logger.info(f"Hostname: {os.uname().nodename}")
    
    # Initialize components
    logger.info("\nInitializing components...")
    
    # 1. Start HTTP server
    logger.info("Starting HTTP API server...")
    http_server = LogHTTPServer()
    http_server.start()
    
    if not http_server.is_running():
        logger.error("Failed to start HTTP server. Exiting...")
        return
    
    logger.info("✓ HTTP server started successfully")
    
    # 2. Initialize log simulator
    logger.info("Initializing KeyPool log simulator...")
    simulator = KeyPoolLogSimulator(site_id=config.SITE_ID)
    logger.info(f"✓ Simulator initialized (starting sequence: {simulator.sequence_number})")
    
    logger.info("✓ All components initialized\n")
    
    iteration = 0
    
    # Main generation loop
    try:
        while True:
            iteration += 1
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            logger.info(f"[Iteration {iteration}] Generating log batch...")
            
            # Generate batch of logs
            log_lines, log_filename, stats = generate_log_batch(simulator)
            
            # Write to file
            filepath = write_logs_to_file(log_lines, log_filename)
            
            # Log statistics
            logger.info(f"✓ Generated {stats['total_lines']} log entries in {log_filename}")
            logger.info(f"  Sequence: {stats['sequence_number']}")
            logger.info(f"  Available via: http://<server>:{config.HTTP_PORT}/logs/{log_filename}")
            
            # Wait before generating next batch
            sleep_time = random.randint(config.MIN_SLEEP_SECONDS, config.MAX_SLEEP_SECONDS)
            logger.info(f"Sleeping {sleep_time}s until next batch...\n")
            time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        logger.info("\nShutdown signal received. Cleaning up...")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
    finally:
        # Cleanup
        logger.info("Stopping HTTP server...")
        http_server.stop()
        logger.info("Log collector stopped gracefully")


if __name__ == "__main__":
    main()
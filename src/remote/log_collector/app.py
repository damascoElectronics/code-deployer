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
from log_generator import (
    KeyPoolLogSimulator,
    write_logs_to_file,
    generate_log_batch
)
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
    logger.info("Running on VM2 - Site ID: %s", config.SITE_ID)
    logger.info("Log output directory: %s", config.LOG_OUTPUT_DIR)
    logger.info("HTTP API: %s:%s", config.HTTP_HOST, config.HTTP_PORT)
    logger.info(
        "Batch size: %s-%s logs",
        config.MIN_BATCH_SIZE,
        config.MAX_BATCH_SIZE
    )
    logger.info(
        "Sleep interval: %s-%s seconds",
        config.MIN_SLEEP_SECONDS,
        config.MAX_SLEEP_SECONDS
    )
    logger.info("=" * 60)


def main():
    """Main function for Container 2 - Log Collector"""

    # Print startup information
    print_startup_info()

    # Show environment info
    logger.info("Working directory: %s", os.getcwd())
    if hasattr(os, 'uname'):
        logger.info("Hostname: %s", os.uname().nodename)

    # Initialize components
    logger.info("Initializing components...")

    # 1. Start HTTP server
    logger.info("Starting HTTP API server...")
    http_server = LogHTTPServer()
    http_server.start()

    if not http_server.is_running():
        logger.error("Failed to start HTTP server. Exiting...")
        return

    logger.info("HTTP server started successfully")

    # 2. Initialize log simulator
    logger.info("Initializing KeyPool log simulator...")
    simulator = KeyPoolLogSimulator(site_id=config.SITE_ID)
    logger.info(
        "Simulator initialized (starting sequence: %s)",
        simulator.sequence_number
    )

    logger.info("All components initialized\n")

    iteration = 0

    # Main generation loop
    try:
        while True:
            iteration += 1

            logger.info("[Iteration %s] Generating log batch...", iteration)

            # Generate batch of logs
            log_lines, log_filename, stats = generate_log_batch(simulator)

            # Write to file
            write_logs_to_file(log_lines, log_filename)

            # Log statistics
            logger.info(
                "Generated %s log entries in %s",
                stats['total_lines'],
                log_filename
            )
            logger.info("  Sequence: %s", stats['sequence_number'])
            logger.info(
                "  Available via: http://<server>:%s/logs/%s",
                config.HTTP_PORT,
                log_filename
            )

            # Wait before generating next batch
            sleep_time = random.randint(
                config.MIN_SLEEP_SECONDS,
                config.MAX_SLEEP_SECONDS
            )
            logger.info("Sleeping %ss until next batch...", sleep_time)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Cleaning up...")
    except Exception as ex:
        logger.error("Unexpected error in main loop: %s", ex, exc_info=True)
    finally:
        # Cleanup
        logger.info("Stopping HTTP server...")
        http_server.stop()
        logger.info("Log collector stopped gracefully")

if __name__ == "__main__":
    main()
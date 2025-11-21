#!/usr/bin/env python3
"""
Container 1 - Log Processor (VM1)
Main application - orchestrates downloading, parsing, and storing logs
"""

import sys
import time
import logging
from datetime import datetime

# Import custom modules
import config
from database import DatabaseManager
from downloader import LogDownloader
from parser import LogParser

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('log_processor')


def print_startup_info():
    """Print startup information"""
    logger.info("=" * 60)
    logger.info("Container 1 (Log Processor) starting up...")
    logger.info("Running on VM1")
    logger.info("VM2 API URL: %s", config.VM2_API_URL)
    logger.info("Poll interval: %s seconds", config.POLL_INTERVAL)
    logger.info("Download directory: %s", config.DOWNLOAD_DIR)
    logger.info(
        "MySQL: %s@%s:%s/%s",
        config.MYSQL_USER,
        config.MYSQL_HOST,
        config.MYSQL_PORT,
        config.MYSQL_DATABASE
    )
    logger.info("=" * 60)


def main():
    """Main function for Container 1 - Log Processor"""

    # Print startup information
    print_startup_info()

    # Initialize components
    logger.info("\nInitializing components...")

    # 1. Connect to database
    logger.info("Connecting to MySQL database...")
    db_manager = DatabaseManager()

    if not db_manager.is_connected():
        logger.error("Failed to connect to database. Exiting...")
        sys.exit(1)

    # 2. Initialize downloader
    logger.info("Initializing log downloader...")
    downloader = LogDownloader()

    # 3. Initialize parser
    logger.info("Initializing log parser...")
    log_parser = LogParser(db_manager)

    logger.info("✓ All components initialized successfully\n")

    # Initial health check
    logger.info("Performing initial health check...")
    if not downloader.check_api_health():
        logger.warning("VM2 API not reachable yet. Will retry...")

    # Load already processed files
    processed_count = len(downloader.processed_files)
    logger.info("Already processed %s files", processed_count)

    iteration = 0

    # Main processing loop
    try:
        while True:
            iteration += 1
            logger.info("\n%s", "=" * 60)
            logger.info("[Iteration %s] Polling for new logs...", iteration)
            logger.info(
                "Time: %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )

            # Get new log files from VM2
            new_logs = downloader.get_new_logs()

            if not new_logs:
                logger.info("No new logs to process")
            else:
                # Process each new log file
                for log_info in new_logs:
                    filename = log_info['filename']

                    # Step 1: Download the file
                    filepath, _ = downloader.download_log_file(filename)

                    if not filepath:
                        logger.warning(
                            "Failed to download %s, skipping...\n", filename
                        )
                        continue

                    # Step 2: Parse and store in database
                    stats = log_parser.process_log_file(filepath)

                    if stats:
                        # Step 3: Mark as processed
                        downloader.mark_as_processed(filename)
                        logger.info(
                            "✓ %s completed successfully\n", filename
                        )
                    else:
                        logger.warning("Failed to process %s\n", filename)

            # Wait before next poll
            logger.info(
                "Waiting %s seconds until next poll...",
                config.POLL_INTERVAL
            )
            time.sleep(config.POLL_INTERVAL)

    except KeyboardInterrupt:
        logger.info("\nShutdown signal received. Cleaning up...")
    except Exception as error:
        logger.error(
            "Unexpected error in main loop: %s", error, exc_info=True
        )
    finally:
        # Cleanup
        logger.info("Closing database connection...")
        db_manager.close()
        logger.info("Log processor stopped gracefully")


if __name__ == "__main__":
    main()
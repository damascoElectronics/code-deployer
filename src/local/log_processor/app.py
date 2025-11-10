#!/usr/bin/env python3
"""
Container 1 - Log Processor (VM1)
Main application - orchestrates downloading, parsing, and storing logs
"""

import time
import logging
from datetime import datetime
import sys

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
    logger.info(f"Running on VM1")
    logger.info(f"VM2 API URL: {config.VM2_API_URL}")
    logger.info(f"Poll interval: {config.POLL_INTERVAL} seconds")
    logger.info(f"Download directory: {config.DOWNLOAD_DIR}")
    logger.info(f"MySQL: {config.MYSQL_USER}@{config.MYSQL_HOST}:{config.MYSQL_PORT}/{config.MYSQL_DATABASE}")
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
    parser = LogParser(db_manager)
    
    logger.info("✓ All components initialized successfully\n")
    
    # Initial health check
    logger.info("Performing initial health check...")
    if not downloader.check_api_health():
        logger.warning("VM2 API not reachable yet. Will retry...")
    
    # Load already processed files
    processed_count = len(downloader.processed_files)
    logger.info(f"Already processed {processed_count} files")
    
    iteration = 0
    
    # Main processing loop
    try:
        while True:
            iteration += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"[Iteration {iteration}] Polling for new logs...")
            logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Get new log files from VM2
            new_logs = downloader.get_new_logs()
            
            if not new_logs:
                logger.info("No new logs to process")
            else:
                # Process each new log file
                for log_info in new_logs:
                    filename = log_info['filename']
                    
                    # Step 1: Download the file
                    filepath, file_size = downloader.download_log_file(filename)
                    
                    if not filepath:
                        logger.warning(f"Failed to download {filename}, skipping...\n")
                        continue
                    
                    # Step 2: Parse and store in database
                    stats = parser.process_log_file(filepath)
                    
                    if stats:
                        # Step 3: Mark as processed
                        downloader.mark_as_processed(filename)
                        logger.info(f"✓ {filename} completed successfully\n")
                    else:
                        logger.warning(f"Failed to process {filename}\n")
            
            # Wait before next poll
            logger.info(f"Waiting {config.POLL_INTERVAL} seconds until next poll...")
            time.sleep(config.POLL_INTERVAL)
    
    except KeyboardInterrupt:
        logger.info("\nShutdown signal received. Cleaning up...")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
    finally:
        # Cleanup
        logger.info("Closing database connection...")
        db_manager.close()
        logger.info("Log processor stopped gracefully")


if __name__ == "__main__":
    main()
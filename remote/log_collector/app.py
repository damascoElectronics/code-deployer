#!/usr/bin/env python3
"""
Container 2 - Log Collector (VM2)
Simulates log generation similar to KeyPoolService logs
"""

import time
import logging
from datetime import datetime
import os
import random
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('log_collector')

# Directory where logs will be written
# Use ./logs for local testing, /app/logs in Docker
DEFAULT_LOG_DIR = '/app/logs' if os.path.exists('/app') else './logs'
LOG_OUTPUT_DIR = os.getenv('LOG_OUTPUT_DIR', DEFAULT_LOG_DIR)

class KeyPoolLogSimulator:
    """Simulates KeyPool service log generation"""
    
    def __init__(self, site_id=100):
        self.site_id = site_id
        self.sequence_number = random.randint(477000, 478000)
        self.source_sites = [101, 102, 103]
        self.key_pool_types = ['PUBLIC', 'PRIVATE', 'SHARED']
        
    def generate_log_entry(self):
        """Generate a single log entry similar to KeyPoolService"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '+0000'
        key_identity = str(uuid.uuid4())
        source_site = random.choice(self.source_sites)
        key_pool_type = random.choice(self.key_pool_types)
        
        self.sequence_number += 1
        
        log_line = (
            f"{timestamp} SiteId: {self.site_id}  INFO 26 "
            f"[quartzScheduler_Worker-{random.randint(1,10)}] "
            f"c.e.q.k.k.KeyPoolServiceImpl             : "
            f"createKey: KeyPoolService successfully created key with identity = "
            f"'{key_identity}', sequence number {self.sequence_number}, and KeyPool "
            f"{{Source site identity = '{source_site}', Destination site identity = '{self.site_id}', "
            f"and KeyPoolType name = '{key_pool_type}'}}"
        )
        
        return log_line
    
    def generate_metric_entry(self, key_count):
        """Generate metric log entries"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '+0000'
        
        # Metric for sync latency
        latency_ms = random.randint(50, 150)
        sync_log = (
            f"{timestamp} SiteId: {self.site_id}  INFO 26 "
            f"[quartzScheduler_Worker-{random.randint(1,10)}] "
            f"c.e.q.k.k.KeySyncServiceImpl             : "
            f"METRIC_KEY_SYNC_LATENCY MS={latency_ms}"
        )
        
        # Metric for received keys
        bits = key_count * 256
        key_log = (
            f"{timestamp} SiteId: {self.site_id}  INFO 26 "
            f"[quartzScheduler_Worker-{random.randint(1,10)}] "
            f"c.e.q.k.k.KeySyncServiceImpl             : "
            f"METRIC_RECEIVED_PUBLIC_KEY_COUNT BITS={bits} KEYS={key_count}"
        )
        
        return sync_log, key_log
    
    def generate_controller_entry(self):
        """Generate controller sync entry"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '+0000'
        remote_site = random.choice(self.source_sites)
        
        controller_log = (
            f"{timestamp} SiteId: {self.site_id}  INFO 26 "
            f"[https-jsse-nio-9500-exec-{random.randint(1,10)}] "
            f"c.e.q.k.k.w.KeyPoolController            : "
            f"Handling qnl db sync with remote site {remote_site}"
        )
        
        return controller_log


def write_logs_to_file(log_lines, filename):
    """Write log lines to a file"""
    os.makedirs(LOG_OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(LOG_OUTPUT_DIR, filename)
    
    with open(filepath, 'a') as f:
        for line in log_lines:
            f.write(line + '\n')
    
    logger.info(f"Written {len(log_lines)} lines to {filepath}")
    return filepath


def main():
    """Main function for Container 2 - Log Collector"""
    logger.info("Container 2 (Log Collector) starting up...")
    logger.info(f"Running on VM2 - Site ID: 100")
    logger.info(f"Log output directory: {LOG_OUTPUT_DIR}")
    
    # Show environment info
    logger.info(f"Working directory: {os.getcwd()}")
    if hasattr(os, 'uname'):
        logger.info(f"Hostname: {os.uname().nodename}")
    
    # Create log simulator
    simulator = KeyPoolLogSimulator(site_id=100)
    
    iteration = 0
    
    # Continuous loop to generate logs
    while True:
        iteration += 1
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        logger.info(f"[Iteration {iteration}] Generating log batch...")
        
        # Generate a batch of key creation logs (similar to your sample)
        batch_size = random.randint(20, 30)
        log_lines = []
        
        for _ in range(batch_size):
            log_lines.append(simulator.generate_log_entry())
        
        # Add metric entries
        sync_log, key_log = simulator.generate_metric_entry(batch_size)
        log_lines.append(sync_log)
        log_lines.append(key_log)
        
        # Occasionally add controller sync entry
        if random.random() < 0.3:  # 30% chance
            log_lines.append(simulator.generate_controller_entry())
        
        # Generate filename with timestamp
        log_filename = f"keypool_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Write to file
        filepath = write_logs_to_file(log_lines, log_filename)
        
        logger.info(f"Generated {len(log_lines)} log entries in {log_filename}")
        logger.info(f"Current sequence number: {simulator.sequence_number}")
        
        # Wait before generating next batch
        sleep_time = random.randint(30, 60)
        logger.info(f"Waiting {sleep_time} seconds before next batch...")
        time.sleep(sleep_time)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Container 2 shutting down gracefully...")
    except Exception as e:
        logger.error(f"Error in Container 2: {e}", exc_info=True)
        raise
#!/usr/bin/env python3
"""
Log Generator module for log_collector
Generates KeyPool-style log entries
"""

import os
import random
import uuid
import logging
from datetime import datetime
import config

logger = logging.getLogger('log_collector.generator')


class KeyPoolLogSimulator:
    """Simulates KeyPool service log generation"""
    
    def __init__(self, site_id=None):
        self.site_id = site_id or config.SITE_ID
        self.sequence_number = random.randint(477000, 478000)
        self.source_sites = config.SOURCE_SITES
        self.key_pool_types = config.KEY_POOL_TYPES
    
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
    os.makedirs(config.LOG_OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(config.LOG_OUTPUT_DIR, filename)
    
    with open(filepath, 'a') as f:
        for line in log_lines:
            f.write(line + '\n')
    
    logger.info(f"Written {len(log_lines)} lines to {filepath}")
    return filepath


def generate_log_batch(simulator):
    """
    Generate a complete batch of logs
    
    Returns:
        tuple: (log_lines, filename, stats)
    """
    batch_size = random.randint(config.MIN_BATCH_SIZE, config.MAX_BATCH_SIZE)
    log_lines = []
    
    # Generate key creation logs
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
    
    stats = {
        'batch_size': batch_size,
        'total_lines': len(log_lines),
        'sequence_number': simulator.sequence_number
    }
    
    return log_lines, log_filename, stats
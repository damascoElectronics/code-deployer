#!/usr/bin/env python3
"""
Fake Log Generator for VM2 Testing
Generates realistic log files matching the format:
TIMESTAMP SiteId: ID LEVEL PID [THREAD] CLASS : MESSAGE
"""

import random
import datetime
import argparse
import time
from typing import List, Dict, Tuple
import uuid

class LogGenerator:
    def __init__(self):
        # Configuration
        self.site_ids = [100, 101, 102]
        self.pid = 26
        self.log_levels = {
            'INFO': 0.7,   # 70% info when no errors forced
            'WARN': 0.2,   # 20% warnings
            'ERROR': 0.1   # 10% errors baseline
        }
        
        # Thread patterns from real logs
        self.threads = [
            'main',
            'quartzScheduler_Worker-1', 'quartzScheduler_Worker-2', 'quartzScheduler_Worker-3',
            'quartzScheduler_Worker-4', 'quartzScheduler_Worker-5', 'quartzScheduler_Worker-6',
            'quartzScheduler_Worker-7', 'quartzScheduler_Worker-8', 'quartzScheduler_Worker-9',
            'quartzScheduler_Worker-10',
            'https-jsse-nio-9500-exec-1', 'https-jsse-nio-9500-exec-2', 'https-jsse-nio-9500-exec-3',
            'https-jsse-nio-9502-exec-1', 'https-jsse-nio-9502-exec-2', 'https-jsse-nio-9502-exec-3',
            'https-jsse-nio-9502-exec-4', 'https-jsse-nio-9502-exec-8', 'https-jsse-nio-9502-exec-9'
        ]
        
        # Class patterns from real logs
        self.classes = {
            'qnl-main': [
                'c.e.q.q.Application',
                'c.e.q.q.d.DbSyncServiceImpl',
                'c.e.q.q.k.KeyRouterServiceImpl',
                'c.e.q.q.k.KeySwapServiceImpl',
                'c.e.q.q.k.KeyReserveService',
                'c.e.q.q.l.LinkStatusServiceImpl',
                'c.e.q.q.s.Startup',
                'l.lockservice',
                'l.changelog',
                'l.database',
                'o.s.b.w.e.t.TomcatWebServer'
            ],
            'qnl-metric': [
                'c.e.q.q.d.DbSyncServiceImpl',
                'c.e.q.q.k.KeySwapServiceImpl',
                'c.e.q.q.k.ProcessOutboxSubPayloadService',
                'cessNetworkHealthOutboxSubPayloadService'
            ],
            'kms-main': [
                'c.e.q.k.Application',
                'c.e.q.k.k.KeySyncServiceImpl',
                'c.e.q.k.k.KeyPoolServiceImpl',
                'c.e.q.k.s.Startup',
                'c.z.h.HikariDataSource',
                'l.lockservice',
                'l.changelog',
                'o.h.j.i.u.LogHelper',
                'o.s.b.w.e.t.TomcatWebServer'
            ],
            'kms-metric': [
                'c.e.q.k.k.KeySyncServiceImpl'
            ]
        }
        
        # Message templates
        self.message_templates = {
            'INFO': [
                "Starting Application v0.0.1-SNAPSHOT using Java 17.0.12",
                "Root WebApplicationContext: initialization completed in {time} ms",
                "HikariPool-1 - Starting...",
                "HikariPool-1 - Start completed.",
                "Successfully acquired change log lock",
                "UPDATE SUMMARY",
                "Total change sets: {count}",
                "Command execution complete",
                "METRIC_BITS KEY_POOL_ID={pool_id} BITS={bits} CATEGORY=ADMIN SUBCATEGORY=KEY_BIT_COUNT",
                "METRIC_KEY_SYNC_LATENCY MS={latency}",
                "METRIC_RECEIVED_PUBLIC_KEY_COUNT BITS={bits} KEYS={keys}",
                "METRIC_OVERHEAD_BIT_COUNT BITS={bits} CATEGORY=ADMIN SUBCATEGORY={subcategory}",
                "createKey: KeyPoolService successfully created key with identity = '{key_id}'",
                "DB sync request successfully authenticated with QNL",
                "Successfully performed DB sync against QNL",
                "ProcessKeySync is started for KMS {site_id}",
                "Key sync job started successfully",
                "All database clean up jobs started successfully"
            ],
            'WARN': [
                "Failed to perform a method call for SnakeYaml because the version is too old",
                "Missing cache[{cache_name}] was created on-the-fly",
                "Connection timeout detected for site {site_id}",
                "Retrying operation after {delay}ms delay",
                "Performance degradation detected: latency {latency}ms exceeds threshold"
            ],
            'ERROR': [
                "Exception communicating with URI 'https://qnl:9502/keysync'. Error message: {error}",
                "Failed to perform iteration for KeySync job",
                "Database connection failed: {error_msg}",
                "Key pool exhausted for site {site_id}",
                "processKeyRoutingFlows detected an null cached result from the Solver Service",
                "Authentication failed for site {site_id}: {reason}",
                "Network connectivity lost to site {site_id}",
                "Key validation failed: {validation_error}",
                "Transaction rollback due to constraint violation",
                "Service unavailable: {service_name} is not responding"
            ]
        }

    def generate_timestamp(self, base_time: datetime.datetime) -> str:
        """Generate timestamp in the format: 2025-07-22T08:13:01.200804930+0000"""
        # Add microseconds for realistic precision
        microseconds = random.randint(100000, 999999)
        timestamp = base_time.replace(microsecond=microseconds)
        return timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f+0000')

    def choose_log_level(self, error_percentage: float) -> str:
        """Choose log level based on error percentage"""
        rand = random.random()
        
        if rand < error_percentage / 100:
            return 'ERROR'
        elif rand < (error_percentage / 100) + 0.15:  # 15% warnings
            return 'WARN'
        else:
            return 'INFO'

    def generate_message_data(self, level: str) -> Dict:
        """Generate realistic data for message templates"""
        return {
            'time': random.randint(1000, 10000),
            'count': random.randint(51, 102),
            'pool_id': random.choice([1000, 1001, 2000, 2002, 2003, 2004, 2005, 2006]),
            'bits': random.choice([0, 6400, 17152, 25600, 25856, 28416, 29440]),
            'latency': random.randint(30, 100),
            'keys': random.randint(20, 30),
            'subcategory': random.choice(['KEY_BIT_COUNT', 'KEY_SWAP_BATCH', 'NETWORK_HEALTH']),
            'key_id': str(uuid.uuid4()),
            'site_id': random.choice(self.site_ids),
            'cache_name': f"com.evolutionq.{random.choice(['kms', 'qnl'])}.{random.choice(['UserProfile', 'KeyPool', 'SiteConfig'])}",
            'delay': random.randint(100, 5000),
            'error': random.choice(['Connection refused', 'Timeout', 'SSL handshake failed', 'null']),
            'error_msg': random.choice(['Connection timeout', 'Invalid credentials', 'Resource not found']),
            'reason': random.choice(['Invalid token', 'Certificate expired', 'Access denied']),
            'validation_error': random.choice(['Invalid key format', 'Key expired', 'Checksum mismatch']),
            'service_name': random.choice(['KeySync', 'DbSync', 'NetworkHealth'])
        }

    def generate_log_entry(self, timestamp: str, log_type: str, level: str) -> str:
        """Generate a single log entry"""
        site_id = random.choice(self.site_ids)
        thread = random.choice(self.threads)
        class_name = random.choice(self.classes[log_type])
        
        # Choose and format message
        template = random.choice(self.message_templates[level])
        message_data = self.generate_message_data(level)
        
        try:
            message = template.format(**message_data)
        except KeyError:
            message = template  # Use template as-is if formatting fails
        
        return f"{timestamp} SiteId: {site_id}  {level} {self.pid} [{thread}] {class_name} : {message}"

    def calculate_intervals(self, duration_hours: float, total_entries: int) -> List[float]:
        """Calculate realistic intervals between log entries"""
        total_seconds = duration_hours * 3600
        
        # Generate intervals that sum to total_seconds
        intervals = []
        remaining_time = total_seconds
        remaining_entries = total_entries
        
        for i in range(total_entries - 1):
            # Average interval with some randomness
            avg_interval = remaining_time / remaining_entries
            # Add randomness but keep it reasonable (0.5x to 2x average)
            interval = random.uniform(avg_interval * 0.5, avg_interval * 2)
            interval = min(interval, remaining_time)  # Don't exceed remaining time
            
            intervals.append(interval)
            remaining_time -= interval
            remaining_entries -= 1
        
        return intervals

    def generate_log_file(self, log_type: str, error_percentage: float, 
                         duration_hours: float, entries_per_hour: int = 100) -> List[str]:
        """Generate complete log file content"""
        total_entries = int(duration_hours * entries_per_hour)
        
        # Calculate realistic time intervals
        intervals = self.calculate_intervals(duration_hours, total_entries)
        
        # Start time (current time minus duration for realistic timestamps)
        start_time = datetime.datetime.now() - datetime.timedelta(hours=duration_hours)
        current_time = start_time
        
        log_entries = []
        
        for i in range(total_entries):
            # Generate timestamp
            timestamp = self.generate_timestamp(current_time)
            
            # Choose log level based on error percentage
            level = self.choose_log_level(error_percentage)
            
            # Generate log entry
            entry = self.generate_log_entry(timestamp, log_type, level)
            log_entries.append(entry)
            
            # Advance time for next entry
            if i < len(intervals):
                current_time += datetime.timedelta(seconds=intervals[i])
        
        return log_entries

    def save_log_file(self, filename: str, log_entries: List[str]):
        """Save log entries to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            for entry in log_entries:
                f.write(entry + '\n')
        
        print(f"Generated {filename} with {len(log_entries)} entries")

def main():
    parser = argparse.ArgumentParser(description='Generate fake log files for testing')
    parser.add_argument('--error-percentage', '-e', type=float, default=10.0,
                       help='Percentage of error messages (default: 10)')
    parser.add_argument('--duration', '-d', type=float, default=1.0,
                       help='Duration in hours (default: 1.0)')
    parser.add_argument('--entries-per-hour', '-r', type=int, default=100,
                       help='Entries per hour (default: 100)')
    parser.add_argument('--log-type', '-t', 
                       choices=['qnl-main', 'qnl-metric', 'kms-main', 'kms-metric', 'all'],
                       default='all', help='Type of log to generate (default: all)')
    parser.add_argument('--output-dir', '-o', default='.', 
                       help='Output directory (default: current directory)')
    
    args = parser.parse_args()
    
    generator = LogGenerator()
    
    log_types = [args.log_type] if args.log_type != 'all' else ['qnl-main', 'qnl-metric', 'kms-main', 'kms-metric']
    
    print(f"Generating logs with {args.error_percentage}% errors for {args.duration} hours...")
    print(f"Rate: {args.entries_per_hour} entries per hour")
    print(f"Log types: {', '.join(log_types)}")
    print("-" * 50)
    
    for log_type in log_types:
        filename = f"{args.output_dir}/{log_type}.log"
        
        # Generate log entries
        log_entries = generator.generate_log_file(
            log_type=log_type,
            error_percentage=args.error_percentage,
            duration_hours=args.duration,
            entries_per_hour=args.entries_per_hour
        )
        
        # Save to file
        generator.save_log_file(filename, log_entries)
    
    print("-" * 50)
    print("Log generation completed!")

if __name__ == "__main__":
    main()
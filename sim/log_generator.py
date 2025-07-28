#!/usr/bin/env python3
"""
Realistic Log Generator for VM2 Testing
Generates logs that closely match the real patterns from project knowledge
"""

import random
import datetime
import argparse
import time
from typing import List, Dict, Tuple
import uuid

class RealisticLogGenerator:
    def __init__(self):
        # Configuration matching real logs
        self.site_ids = [100, 101, 102]
        self.pid = 26
        
        # Thread patterns exactly from real logs
        self.threads = {
            'startup': ['main'],
            'operational': [
                'quartzScheduler_Worker-1', 'quartzScheduler_Worker-2', 'quartzScheduler_Worker-4',
                'quartzScheduler_Worker-5', 'quartzScheduler_Worker-6', 'quartzScheduler_Worker-7',
                'quartzScheduler_Worker-8', 'quartzScheduler_Worker-10',
                'https-jsse-nio-9500-exec-1', 'https-jsse-nio-9500-exec-2',
                'https-jsse-nio-9502-exec-1', 'https-jsse-nio-9502-exec-2', 'https-jsse-nio-9502-exec-3',
                'https-jsse-nio-9502-exec-4', 'https-jsse-nio-9502-exec-8', 'https-jsse-nio-9502-exec-9'
            ]
        }
        
        # Real frequency patterns (entries per hour)
        self.frequencies = {
            'qnl-main': 20,      # Startup + some operational
            'qnl-metric': 30,    # Regular metric intervals
            'kms-main': 15,      # Less frequent than QNL
            'kms-metric': 12     # Key sync every ~5-8 minutes
        }

    def generate_timestamp(self, base_time: datetime.datetime) -> str:
        """Generate realistic timestamp with microsecond precision"""
        microseconds = random.randint(100000, 999999)
        timestamp = base_time.replace(microsecond=microseconds)
        return timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f+0000')

    def generate_qnl_main_logs(self, error_percentage: float, duration_hours: float) -> List[str]:
        """Generate QNL main logs matching real patterns"""
        entries = []
        start_time = datetime.datetime.now() - datetime.timedelta(hours=duration_hours)
        current_time = start_time
        
        # Phase 1: Startup sequence (first few minutes)
        startup_messages = [
            ("INFO", "main", "c.e.q.q.Application", "Starting Application v0.0.1-SNAPSHOT using Java 17.0.12 on {container_id} with PID 26"),
            ("INFO", "main", "c.e.q.q.Application", "The following 2 profiles are active: \"postgres\", \"production\""),
            ("INFO", "main", "l.database", "Set default schema name to public"),
            ("INFO", "main", "l.lockservice", "Successfully acquired change log lock"),
            ("WARN", "main", "l.util", "Failed to perform a method call for SnakeYaml because the version of SnakeYaml being used is too old"),
            ("INFO", "main", "l.changelog", "Reading from public.databasechangelog"),
            ("INFO", "main", "l.util", "UPDATE SUMMARY"),
            ("INFO", "main", "l.util", "Total change sets: 102"),
            ("INFO", "main", "l.lockservice", "Successfully released change log lock"),
            ("INFO", "main", "c.e.q.q.s.Startup", "Auto start of database clean up job is set to true"),
            ("INFO", "main", "c.e.q.q.s.Startup", "All database clean up jobs started successfully")
        ]
        
        for i, (level, thread, class_name, message_template) in enumerate(startup_messages):
            timestamp = self.generate_timestamp(current_time)
            site_id = random.choice(self.site_ids)
            message = message_template.format(container_id=f"{random.randint(100000000, 999999999):08x}")
            entries.append(f"{timestamp} SiteId: {site_id}  {level} {self.pid} [{thread}] {class_name} : {message}")
            current_time += datetime.timedelta(seconds=random.uniform(1, 5))
        
        # Phase 2: Operational logs
        total_operational = int(duration_hours * self.frequencies['qnl-main']) - len(startup_messages)
        operational_interval = (duration_hours * 3600 - 60) / max(total_operational, 1)  # Leave 60s for startup
        
        operational_templates = [
            ("INFO", "c.e.q.q.d.DbSyncServiceImpl", "Performing DB sync DbSyncRequestDto{{uuid='{uuid}', timestamp={timestamp}}} against QNL"),
            ("INFO", "c.e.q.q.d.DbSyncServiceImpl", "DB sync request successfully authenticated with QNL Qnl{{id={site_id}}}"),
            ("INFO", "c.e.q.q.d.DbSyncServiceImpl", "Successfully performed DB sync against QNL Qnl{{id={site_id}}}"),
            ("INFO", "c.e.q.q.k.KeyRouterServiceImpl", "processKeyRoutingFlows completed successfully for site {site_id}"),
            ("INFO", "c.e.q.q.k.KeyReserveService", "Scheduling quartz job to reserve {key_count} keys from {site_id}"),
            ("INFO", "c.e.q.q.l.LinkStatusServiceImpl", "Transition to NORMAL with site {site_id}. Transition cause: KEY_TRIAGE_COMPLETE")
        ]
        
        error_templates = [
            ("ERROR", "c.e.q.q.k.KeyRouterServiceImpl", "processKeyRoutingFlows detected an null cached result from the Solver Service"),
            ("ERROR", "c.e.q.q.d.DbSyncServiceImpl", "Database connection failed: Connection timeout after {timeout}ms"),
            ("ERROR", "c.e.q.q.k.KeyServiceImpl", "Key pool exhausted for site {site_id}: no available keys"),
            ("ERROR", "c.e.q.q.k.KeySwapServiceImpl", "Key swap batch failed: Authentication error for site {site_id}")
        ]
        
        for i in range(total_operational):
            # Determine if this should be an error based on percentage
            use_error = random.random() < (error_percentage / 100)
            templates = error_templates if use_error else operational_templates
            
            level, class_name, message_template = random.choice(templates)
            thread = random.choice(self.threads['operational'])
            site_id = random.choice(self.site_ids)
            
            message_data = {
                'uuid': str(uuid.uuid4()),
                'timestamp': current_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                'site_id': site_id,
                'key_count': random.randint(200, 500),
                'timeout': random.randint(5000, 30000)
            }
            
            try:
                message = message_template.format(**message_data)
            except KeyError:
                message = message_template
                
            timestamp = self.generate_timestamp(current_time)
            entries.append(f"{timestamp} SiteId: {site_id}  {level} {self.pid} [{thread}] {class_name} : {message}")
            current_time += datetime.timedelta(seconds=random.uniform(operational_interval * 0.5, operational_interval * 1.5))
        
        return entries

    def generate_qnl_metric_logs(self, error_percentage: float, duration_hours: float) -> List[str]:
        """Generate QNL metric logs with realistic patterns"""
        entries = []
        start_time = datetime.datetime.now() - datetime.timedelta(hours=duration_hours)
        current_time = start_time
        
        total_entries = int(duration_hours * self.frequencies['qnl-metric'])
        interval = (duration_hours * 3600) / max(total_entries, 1)
        
        key_pools = [1000, 1001, 2000, 2002, 2003, 2004, 2005, 2006]
        bit_values = [0, 17152, 25600, 25856, 28416, 29440]
        
        for i in range(total_entries):
            thread = random.choice(self.threads['operational'])
            site_id = random.choice(self.site_ids)
            
            # Generate metric bursts (like real logs)
            if random.random() < 0.6:  # 60% are bit count metrics
                pool_id = random.choice(key_pools)
                bits = random.choice(bit_values)
                message = f"METRIC_BITS KEY_POOL_ID={pool_id} BITS={bits} CATEGORY=ADMIN SUBCATEGORY=KEY_BIT_COUNT"
                level = "INFO"
            elif random.random() < 0.3:  # 30% are overhead metrics
                bits = 256
                subcategory = random.choice(['KEY_SWAP_BATCH', 'NETWORK_HEALTH', 'KEY_SWAP_BATCH_ACK_RESPONSE'])
                message = f"METRIC_OVERHEAD_BIT_COUNT BITS={bits} CATEGORY=ADMIN SUBCATEGORY={subcategory}"
                level = "INFO"
            else:  # 10% are performance metrics or errors
                if random.random() < (error_percentage / 100):
                    message = f"METRIC_ERROR: Key swap batch timeout for site {random.choice(self.site_ids)}"
                    level = "ERROR"
                else:
                    latency = random.randint(2000, 5000)
                    keys = random.randint(50, 55)
                    throughput = round(keys / (latency / 1000), 2)
                    batch_id = str(uuid.uuid4())
                    message = f"METRIC_KEY_SWAP_BATCH_SUCCESS KEY_SWAP_BATCH_IDENTITY={batch_id} LATENCY={latency}ms KEY_COUNT={keys} KEY_SWAP_THROUGHPUT={throughput}keys/second CATEGORY=PERFORMANCE SUBCATEGORY=KEY_SWAP_BATCH"
                    level = "INFO"
            
            timestamp = self.generate_timestamp(current_time)
            entries.append(f"{timestamp} SiteId: {site_id}  {level} {self.pid} [{thread}] c.e.q.q.d.DbSyncServiceImpl : {message}")
            current_time += datetime.timedelta(seconds=random.uniform(interval * 0.7, interval * 1.3))
        
        return entries

    def generate_kms_main_logs(self, error_percentage: float, duration_hours: float) -> List[str]:
        """Generate KMS main logs matching real patterns"""
        entries = []
        start_time = datetime.datetime.now() - datetime.timedelta(hours=duration_hours)
        current_time = start_time
        
        # Startup sequence (similar to QNL but KMS specific)
        startup_messages = [
            ("INFO", "main", "c.e.q.k.Application", "Starting Application v0.0.1-SNAPSHOT using Java 17.0.12 on {container_id} with PID 26"),
            ("INFO", "main", "c.e.q.k.Application", "The following 2 profiles are active: \"postgres\", \"production\""),
            ("INFO", "main", "c.z.h.HikariDataSource", "HikariPool-1 - Starting..."),
            ("INFO", "main", "c.z.h.HikariDataSource", "HikariPool-1 - Start completed."),
            ("INFO", "main", "l.database", "Set default schema name to public"),
            ("INFO", "main", "l.lockservice", "Successfully acquired change log lock"),
            ("INFO", "main", "l.changelog", "Reading from public.databasechangelog"),
            ("INFO", "main", "l.util", "Total change sets: 51"),
            ("INFO", "main", "c.e.q.k.Application", "Started Application in {startup_time} seconds (JVM running for {jvm_time})"),
            ("INFO", "main", "c.e.q.k.s.Startup", "ProcessKeySync is started for KMS {site_id}"),
            ("INFO", "main", "c.e.q.k.s.Startup", "Key sync job started successfully")
        ]
        
        for level, thread, class_name, message_template in startup_messages:
            timestamp = self.generate_timestamp(current_time)
            site_id = random.choice(self.site_ids)
            message_data = {
                'container_id': f"{random.randint(100000000, 999999999):08x}",
                'startup_time': round(random.uniform(20.0, 30.0), 3),
                'jvm_time': round(random.uniform(25.0, 35.0), 3),
                'site_id': site_id
            }
            
            try:
                message = message_template.format(**message_data)
            except KeyError:
                message = message_template
                
            entries.append(f"{timestamp} SiteId: {site_id}  {level} {self.pid} [{thread}] {class_name} : {message}")
            current_time += datetime.timedelta(seconds=random.uniform(0.5, 3))
        
        # Operational phase - key creation sequences
        total_operational = int(duration_hours * self.frequencies['kms-main']) - len(startup_messages)
        operational_interval = (duration_hours * 3600 - 30) / max(total_operational, 1)
        
        for i in range(total_operational):
            thread = random.choice(self.threads['operational'])
            site_id = random.choice(self.site_ids)
            
            if random.random() < (error_percentage / 100):
                # Error messages
                error_messages = [
                    "Exception communicating with URI 'https://qnl:9502/keysync'. Error message: Connection refused",
                    "Failed to perform iteration for KeySync job",
                    f"Database constraint violation: duplicate key for site {site_id}"
                ]
                message = random.choice(error_messages)
                level = "ERROR"
                class_name = "c.e.q.k.k.KeySyncServiceImpl"
            else:
                # Key creation messages (like real logs)
                key_id = str(uuid.uuid4())
                seq_number = random.randint(15300000, 15400000)
                dest_site = random.choice([s for s in self.site_ids if s != site_id])
                message = f"createKey: KeyPoolService successfully created key with identity = '{key_id}', sequence number {seq_number}, and KeyPool {{Source site identity = '{site_id}', Destination site identity = '{dest_site}', and KeyPoolType name = 'PUBLIC'}}"
                level = "INFO"
                class_name = "c.e.q.k.k.KeyPoolServiceImpl"
            
            timestamp = self.generate_timestamp(current_time)
            entries.append(f"{timestamp} SiteId: {site_id}  {level} {self.pid} [{thread}] {class_name} : {message}")
            current_time += datetime.timedelta(seconds=random.uniform(operational_interval * 0.5, operational_interval * 1.5))
        
        return entries

    def generate_kms_metric_logs(self, error_percentage: float, duration_hours: float) -> List[str]:
        """Generate KMS metric logs with the correct 25-key batches pattern"""
        entries = []
        start_time = datetime.datetime.now() - datetime.timedelta(hours=duration_hours)
        current_time = start_time
        
        # KMS metrics are less frequent - every 8-10 minutes typically
        total_cycles = int(duration_hours * self.frequencies['kms-metric'])
        cycle_interval = (duration_hours * 3600) / max(total_cycles, 1)
        
        for cycle in range(total_cycles):
            thread = random.choice(self.threads['operational'])
            site_id = random.choice(self.site_ids)
            
            if random.random() < (error_percentage / 100):
                # Error in key sync
                message = f"Key sync failed for site {random.choice(self.site_ids)}: timeout after {random.randint(5000, 10000)}ms"
                level = "ERROR"
                timestamp = self.generate_timestamp(current_time)
                entries.append(f"{timestamp} SiteId: {site_id}  {level} {self.pid} [{thread}] c.e.q.k.k.KeySyncServiceImpl : {message}")
            else:
                # Normal key sync cycle - ALWAYS 25 keys, 6400 bits (like real logs)
                latency = random.randint(38, 65)  # Range from real logs
                
                # First: latency metric
                timestamp1 = self.generate_timestamp(current_time)
                entries.append(f"{timestamp1} SiteId: {site_id}  INFO {self.pid} [{thread}] c.e.q.k.k.KeySyncServiceImpl : METRIC_KEY_SYNC_LATENCY MS={latency}")
                
                # Second: key count metric (immediately after)
                current_time += datetime.timedelta(milliseconds=random.randint(100, 500))
                timestamp2 = self.generate_timestamp(current_time)
                entries.append(f"{timestamp2} SiteId: {site_id}  INFO {self.pid} [{thread}] c.e.q.k.k.KeySyncServiceImpl : METRIC_RECEIVED_PUBLIC_KEY_COUNT BITS=6400 KEYS=25")
            
            # Move to next cycle
            current_time += datetime.timedelta(seconds=random.uniform(cycle_interval * 0.8, cycle_interval * 1.2))
        
        return entries

    def generate_log_file(self, log_type: str, error_percentage: float, duration_hours: float) -> List[str]:
        """Generate complete log file based on type"""
        generators = {
            'qnl-main': self.generate_qnl_main_logs,
            'qnl-metric': self.generate_qnl_metric_logs,
            'kms-main': self.generate_kms_main_logs,
            'kms-metric': self.generate_kms_metric_logs
        }
        
        return generators[log_type](error_percentage, duration_hours)

    def save_log_file(self, filename: str, log_entries: List[str]):
        """Save log entries to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            for entry in log_entries:
                f.write(entry + '\n')
        
        print(f"Generated {filename} with {len(log_entries)} entries")

def main():
    parser = argparse.ArgumentParser(description='Generate realistic fake log files matching real patterns')
    parser.add_argument('--error-percentage', '-e', type=float, default=10.0,
                       help='Percentage of error messages (default: 10)')
    parser.add_argument('--duration', '-d', type=float, default=1.0,
                       help='Duration in hours (default: 1.0)')
    parser.add_argument('--log-type', '-t', 
                       choices=['qnl-main', 'qnl-metric', 'kms-main', 'kms-metric', 'all'],
                       default='all', help='Type of log to generate (default: all)')
    parser.add_argument('--output-dir', '-o', default='.', 
                       help='Output directory (default: current directory)')
    
    args = parser.parse_args()
    
    generator = RealisticLogGenerator()
    
    log_types = [args.log_type] if args.log_type != 'all' else ['qnl-main', 'qnl-metric', 'kms-main', 'kms-metric']
    
    print(f"Generating realistic logs with {args.error_percentage}% errors for {args.duration} hours...")
    print(f"Expected frequencies: QNL-main: {generator.frequencies['qnl-main']}/hr, QNL-metric: {generator.frequencies['qnl-metric']}/hr")
    print(f"                     KMS-main: {generator.frequencies['kms-main']}/hr, KMS-metric: {generator.frequencies['kms-metric']}/hr")
    print(f"Log types: {', '.join(log_types)}")
    print("-" * 70)
    
    for log_type in log_types:
        filename = f"{args.output_dir}/{log_type}.log"
        
        # Generate log entries
        log_entries = generator.generate_log_file(
            log_type=log_type,
            error_percentage=args.error_percentage,
            duration_hours=args.duration
        )
        
        # Save to file
        generator.save_log_file(filename, log_entries)
    
    print("-" * 70)
    print("Realistic log generation completed!")
    print("\nKey patterns implemented:")
    print("• KMS-metric: Always 25 keys, 6400 bits per sync cycle")
    print("• QNL-main: Startup sequence + operational DB sync patterns")
    print("• QNL-metric: Key pool bit counts + swap batch metrics")
    print("• Realistic frequencies matching actual log patterns")

if __name__ == "__main__":
    main()
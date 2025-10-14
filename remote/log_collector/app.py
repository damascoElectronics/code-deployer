#!/usr/bin/env python3
"""
Container 2 - Log Collector (VM2)
Generates KeyPool logs and exposes them via HTTP API
"""

import time
import logging
from datetime import datetime
import os
import random
import uuid
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('log_collector')

# Directory where logs will be written
DEFAULT_LOG_DIR = '/app/logs' if os.path.exists('/app') else './logs'
LOG_OUTPUT_DIR = os.getenv('LOG_OUTPUT_DIR', DEFAULT_LOG_DIR)
HTTP_PORT = int(os.getenv('HTTP_PORT', 8080))


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


class LogAPIHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for Log API"""
    
    def log_message(self, format, *args):
        """Override to use our logger instead of stderr"""
        logger.info(f"HTTP: {format % args}")
    
    def do_GET(self):
        """Handle GET requests"""
        
        if self.path == '/':
            # API info endpoint
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'service': 'Log Collector API',
                'version': '1.0',
                'endpoints': {
                    '/': 'API information',
                    '/logs': 'List all log files',
                    '/logs/<filename>': 'Download specific log file'
                }
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
        
        elif self.path == '/logs':
            # List all log files
            try:
                log_path = Path(LOG_OUTPUT_DIR)
                log_files = []
                
                if log_path.exists():
                    for log_file in sorted(log_path.glob('*.log')):
                        stats = log_file.stat()
                        log_files.append({
                            'filename': log_file.name,
                            'size': stats.st_size,
                            'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                            'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                            'download_url': f'/logs/{log_file.name}'
                        })
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    'count': len(log_files),
                    'files': log_files
                }
                self.wfile.write(json.dumps(response, indent=2).encode())
                
            except Exception as e:
                logger.error(f"Error listing logs: {e}")
                self.send_error(500, f"Error listing logs: {str(e)}")
        
        elif self.path.startswith('/logs/'):
            # Download specific log file
            filename = self.path[6:]  # Remove '/logs/'
            filepath = Path(LOG_OUTPUT_DIR) / filename
            
            # Security: prevent directory traversal
            try:
                filepath = filepath.resolve()
                if not str(filepath).startswith(str(Path(LOG_OUTPUT_DIR).resolve())):
                    self.send_error(403, "Access denied")
                    return
            except Exception:
                self.send_error(400, "Invalid filename")
                return
            
            if filepath.exists() and filepath.is_file():
                try:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                    self.end_headers()
                    
                    with open(filepath, 'rb') as f:
                        self.wfile.write(f.read())
                    
                    logger.info(f"Served log file: {filename}")
                    
                except Exception as e:
                    logger.error(f"Error serving file {filename}: {e}")
                    self.send_error(500, f"Error reading file: {str(e)}")
            else:
                self.send_error(404, "Log file not found")
        
        else:
            self.send_error(404, "Endpoint not found")


def start_http_server():
    """Start HTTP server in a separate thread"""
    server = HTTPServer(('0.0.0.0', HTTP_PORT), LogAPIHandler)
    logger.info(f"HTTP Server started on port {HTTP_PORT}")
    server.serve_forever()


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
    logger.info("=" * 60)
    logger.info("Container 2 (Log Collector) starting up...")
    logger.info(f"Running on VM2 - Site ID: 100")
    logger.info(f"Log output directory: {LOG_OUTPUT_DIR}")
    logger.info(f"HTTP API port: {HTTP_PORT}")
    logger.info("=" * 60)
    
    # Show environment info
    logger.info(f"Working directory: {os.getcwd()}")
    if hasattr(os, 'uname'):
        logger.info(f"Hostname: {os.uname().nodename}")
    
    # Start HTTP server in background thread
    http_thread = Thread(target=start_http_server, daemon=True)
    http_thread.start()
    logger.info("HTTP API server started successfully")
    
    # Create log simulator
    simulator = KeyPoolLogSimulator(site_id=100)
    
    iteration = 0
    
    # Continuous loop to generate logs
    while True:
        iteration += 1
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        logger.info(f"[Iteration {iteration}] Generating log batch...")
        
        # Generate a batch of key creation logs
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
        
        logger.info(f"✓ Generated {len(log_lines)} log entries in {log_filename}")
        logger.info(f"  Sequence: {simulator.sequence_number}")
        logger.info(f"  Available via: http://<server>:{HTTP_PORT}/logs/{log_filename}")
        
        # Wait before generating next batch
        sleep_time = random.randint(30, 60)
        logger.info(f"Sleeping {sleep_time}s until next batch...\n")
        time.sleep(sleep_time)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nContainer 2 shutting down gracefully...")
    except Exception as e:
        logger.error(f"Error in Container 2: {e}", exc_info=True)
        raise
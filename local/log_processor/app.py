#!/usr/bin/env python3
"""
Container 1 - Log Processor (VM1)
Pulls logs from VM2 and processes them
"""

import time
import logging
from datetime import datetime
import os
import requests
from pathlib import Path
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('log_processor')

# Configuration
VM2_HOST = os.getenv('VM2_HOST', '192.168.0.11')
VM2_PORT = int(os.getenv('VM2_PORT', 8080))
VM2_API_URL = f"http://{VM2_HOST}:{VM2_PORT}"
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', 30))  # seconds
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', './downloaded_logs')

# Track downloaded files to avoid re-processing
PROCESSED_FILES_LOG = os.path.join(DOWNLOAD_DIR, '.processed_files.txt')


def load_processed_files():
    """Load list of already processed files"""
    if os.path.exists(PROCESSED_FILES_LOG):
        with open(PROCESSED_FILES_LOG, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def mark_file_as_processed(filename):
    """Mark a file as processed"""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    with open(PROCESSED_FILES_LOG, 'a') as f:
        f.write(f"{filename}\n")


def check_api_health():
    """Check if VM2 API is reachable"""
    try:
        response = requests.get(f"{VM2_API_URL}/", timeout=5)
        if response.status_code == 200:
            logger.info(f"✓ Connected to VM2 API at {VM2_API_URL}")
            return True
        else:
            logger.warning(f"VM2 API returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Cannot connect to VM2 API: {e}")
        return False


def get_available_logs():
    """Get list of available log files from VM2"""
    try:
        response = requests.get(f"{VM2_API_URL}/logs", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Found {data['count']} log files on VM2")
        return data['files']
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching log list: {e}")
        return []


def download_log_file(filename):
    """Download a specific log file from VM2"""
    try:
        url = f"{VM2_API_URL}/logs/{filename}"
        logger.info(f"Downloading {filename}...")
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Save to local directory
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        file_size = len(response.content)
        logger.info(f"✓ Downloaded {filename} ({file_size} bytes)")
        return filepath
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading {filename}: {e}")
        return None


def parse_log_entry(line):
    """Parse a single log line and extract key information"""
    try:
        # Example line format:
        # 2025-07-22T08:13:45.391124448+0000 SiteId: 100 INFO 26 [...] createKey: KeyPoolService ...
        
        parts = line.split()
        if len(parts) < 5:
            return None
        
        timestamp_str = parts[0]
        site_id = parts[2] if len(parts) > 2 else None
        
        # Extract key information from the message
        entry = {
            'timestamp': timestamp_str,
            'site_id': site_id,
            'raw_line': line,
            'line_length': len(line)
        }
        
        # Check for specific log types
        if 'createKey' in line:
            entry['log_type'] = 'KEY_CREATION'
            # Extract sequence number
            if 'sequence number' in line:
                seq_part = line.split('sequence number')[1].split(',')[0].strip()
                try:
                    entry['sequence_number'] = int(seq_part)
                except ValueError:
                    pass
        
        elif 'METRIC_KEY_SYNC_LATENCY' in line:
            entry['log_type'] = 'SYNC_LATENCY'
            # Extract latency
            if 'MS=' in line:
                ms_part = line.split('MS=')[1].split()[0]
                try:
                    entry['latency_ms'] = int(ms_part)
                except ValueError:
                    pass
        
        elif 'METRIC_RECEIVED_PUBLIC_KEY_COUNT' in line:
            entry['log_type'] = 'KEY_COUNT'
            # Extract key count
            if 'KEYS=' in line:
                keys_part = line.split('KEYS=')[1].split()[0]
                try:
                    entry['key_count'] = int(keys_part)
                except ValueError:
                    pass
        
        elif 'KeyPoolController' in line:
            entry['log_type'] = 'CONTROLLER_SYNC'
        
        else:
            entry['log_type'] = 'UNKNOWN'
        
        return entry
    
    except Exception as e:
        logger.error(f"Error parsing line: {e}")
        return None


def process_log_file(filepath):
    """Process a downloaded log file"""
    try:
        logger.info(f"Processing {os.path.basename(filepath)}...")
        
        stats = {
            'total_lines': 0,
            'key_creations': 0,
            'sync_latency': 0,
            'key_counts': 0,
            'controller_syncs': 0,
            'unknown': 0
        }
        
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                stats['total_lines'] += 1
                entry = parse_log_entry(line)
                
                if entry:
                    log_type = entry.get('log_type', 'UNKNOWN')
                    
                    if log_type == 'KEY_CREATION':
                        stats['key_creations'] += 1
                    elif log_type == 'SYNC_LATENCY':
                        stats['sync_latency'] += 1
                    elif log_type == 'KEY_COUNT':
                        stats['key_counts'] += 1
                    elif log_type == 'CONTROLLER_SYNC':
                        stats['controller_syncs'] += 1
                    else:
                        stats['unknown'] += 1
        
        logger.info(f"✓ Processed {os.path.basename(filepath)}:")
        logger.info(f"  Total lines: {stats['total_lines']}")
        logger.info(f"  Key creations: {stats['key_creations']}")
        logger.info(f"  Sync latency entries: {stats['sync_latency']}")
        logger.info(f"  Key count metrics: {stats['key_counts']}")
        logger.info(f"  Controller syncs: {stats['controller_syncs']}")
        
        return stats
    
    except Exception as e:
        logger.error(f"Error processing file {filepath}: {e}")
        return None


def main():
    """Main function for Container 1 - Log Processor"""
    logger.info("=" * 60)
    logger.info("Container 1 (Log Processor) starting up...")
    logger.info(f"Running on VM1")
    logger.info(f"VM2 API URL: {VM2_API_URL}")
    logger.info(f"Poll interval: {POLL_INTERVAL} seconds")
    logger.info(f"Download directory: {DOWNLOAD_DIR}")
    logger.info("=" * 60)
    
    # Show environment info
    logger.info(f"Working directory: {os.getcwd()}")
    if hasattr(os, 'uname'):
        logger.info(f"Hostname: {os.uname().nodename}")
    
    # Initial health check
    logger.info("\nPerforming initial health check...")
    if not check_api_health():
        logger.warning("VM2 API not reachable yet. Will retry...")
    
    # Load processed files
    processed_files = load_processed_files()
    logger.info(f"Already processed {len(processed_files)} files")
    
    iteration = 0
    
    # Main processing loop
    while True:
        iteration += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"[Iteration {iteration}] Polling for new logs...")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get available logs
        available_logs = get_available_logs()
        
        if not available_logs:
            logger.info("No logs available on VM2")
        else:
            # Filter out already processed files
            new_logs = [log for log in available_logs 
                       if log['filename'] not in processed_files]
            
            if not new_logs:
                logger.info(f"All {len(available_logs)} logs already processed")
            else:
                logger.info(f"Found {len(new_logs)} new log files to process")
                
                for log_info in new_logs:
                    filename = log_info['filename']
                    
                    # Download the file
                    filepath = download_log_file(filename)
                    
                    if filepath:
                        # Process the file
                        stats = process_log_file(filepath)
                        
                        if stats:
                            # Mark as processed
                            mark_file_as_processed(filename)
                            processed_files.add(filename)
                            logger.info(f"✓ {filename} marked as processed\n")
                        else:
                            logger.warning(f"Failed to process {filename}\n")
                    else:
                        logger.warning(f"Failed to download {filename}\n")
        
        # Wait before next poll
        logger.info(f"Waiting {POLL_INTERVAL} seconds until next poll...")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nContainer 1 shutting down gracefully...")
    except Exception as e:
        logger.error(f"Error in Container 1: {e}", exc_info=True)
        raise
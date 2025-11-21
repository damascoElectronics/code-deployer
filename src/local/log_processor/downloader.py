#!/usr/bin/env python3
"""
Downloader module for log_processor
Handles downloading log files from VM2 API
"""

import os
import logging
import requests
import config

logger = logging.getLogger('log_processor.downloader')


class LogDownloader:
    """Handles downloading log files from VM2"""
    
    def __init__(self):
        self.api_url = config.VM2_API_URL
        self.download_dir = config.DOWNLOAD_DIR
        self.processed_files_log = config.PROCESSED_FILES_LOG
        self.processed_files = self._load_processed_files()
    
    def _load_processed_files(self):
        """Load list of already processed files"""
        if os.path.exists(self.processed_files_log):
            with open(self.processed_files_log, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        return set()
    
    def mark_as_processed(self, filename):
        """Mark a file as processed in tracking file"""
        os.makedirs(self.download_dir, exist_ok=True)
        with open(self.processed_files_log, 'a') as f:
            f.write(f"{filename}\n")
        self.processed_files.add(filename)
    
    def check_api_health(self):
        """Check if VM2 API is reachable"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=5)
            if response.status_code == 200:
                logger.info(f"✓ Connected to VM2 API at {self.api_url}")
                return True
            else:
                logger.warning(f"VM2 API returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Cannot connect to VM2 API: {e}")
            return False
    
    def get_available_logs(self):
        """Get list of available log files from VM2"""
        try:
            response = requests.get(f"{self.api_url}/logs", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Found {data['count']} log files on VM2")
            return data['files']
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching log list: {e}")
            return []
    
    def get_new_logs(self):
        """Get list of new log files that haven't been processed"""
        available_logs = self.get_available_logs()
        
        if not available_logs:
            return []
        
        new_logs = [log for log in available_logs 
                   if log['filename'] not in self.processed_files]
        
        if new_logs:
            logger.info(f"Found {len(new_logs)} new log files to process")
        else:
            logger.info(f"All {len(available_logs)} logs already processed")
        
        return new_logs
    
    def download_log_file(self, filename):
        """
        Download a specific log file from VM2
        
        Returns:
            tuple: (filepath, file_size) if successful, (None, 0) if failed
        """
        try:
            url = f"{self.api_url}/logs/{filename}"
            logger.info(f"Downloading {filename}...")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to local directory
            os.makedirs(self.download_dir, exist_ok=True)
            filepath = os.path.join(self.download_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content)
            logger.info(f"✓ Downloaded {filename} ({file_size} bytes)")
            return filepath, file_size
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading {filename}: {e}")
            return None, 0
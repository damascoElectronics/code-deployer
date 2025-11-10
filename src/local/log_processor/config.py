#!/usr/bin/env python3
"""
Configuration module for log_processor
Centralizes all environment variables and settings
"""

import os

# VM2 API Configuration
VM2_HOST = os.getenv('VM2_HOST', '192.168.0.11')
VM2_PORT = int(os.getenv('VM2_PORT', 8080))
VM2_API_URL = f"http://{VM2_HOST}:{VM2_PORT}"

# Polling Configuration
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', 30))  # seconds

# Storage Configuration
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', './downloaded_logs')
PROCESSED_FILES_LOG = os.path.join(DOWNLOAD_DIR, '.processed_files.txt')

# MySQL Configuration
MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
MYSQL_USER = os.getenv('MYSQL_USER', 'keypool_user')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'keypool_password')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'keypool_logs')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
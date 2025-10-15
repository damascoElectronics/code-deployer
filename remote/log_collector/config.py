#!/usr/bin/env python3
"""
Configuration module for log_collector
Centralizes all environment variables and settings
"""

import os

# Log Generation Configuration
SITE_ID = int(os.getenv('SITE_ID', 100))
SOURCE_SITES = [101, 102, 103]  # Source sites for key generation
KEY_POOL_TYPES = ['PUBLIC', 'PRIVATE', 'SHARED']

# Batch Configuration
MIN_BATCH_SIZE = int(os.getenv('MIN_BATCH_SIZE', 20))
MAX_BATCH_SIZE = int(os.getenv('MAX_BATCH_SIZE', 30))
MIN_SLEEP_SECONDS = int(os.getenv('MIN_SLEEP_SECONDS', 30))
MAX_SLEEP_SECONDS = int(os.getenv('MAX_SLEEP_SECONDS', 60))

# Storage Configuration
LOG_OUTPUT_DIR = os.getenv('LOG_OUTPUT_DIR', '/app/logs' if os.path.exists('/app') else './logs')

# HTTP Server Configuration
HTTP_HOST = os.getenv('HTTP_HOST', '0.0.0.0')
HTTP_PORT = int(os.getenv('HTTP_PORT', 8080))

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
#!/usr/bin/env python3
"""Downloader module for log_processor.

This module handles downloading log files from VM2 API
and tracking which files have been processed.
"""

import os
import logging
import requests
from . import config

logger = logging.getLogger('log_processor.downloader')


class LogDownloader:
    """Handles downloading log files from VM2."""

    def __init__(self):
        """Initialize log downloader with configuration."""
        self.api_url = config.VM2_API_URL
        self.download_dir = config.DOWNLOAD_DIR
        self.processed_files_log = config.PROCESSED_FILES_LOG
        self.processed_files = self._load_processed_files()

    def _load_processed_files(self):
        """Load list of already processed files.

        Returns:
            set: Set of processed filenames.
        """
        if os.path.exists(self.processed_files_log):
            with open(self.processed_files_log, 'r',
                      encoding='utf-8') as file:
                return set(
                    line.strip() for line in file if line.strip()
                )
        return set()

    def mark_as_processed(self, filename):
        """Mark a file as processed in tracking file.

        Args:
            filename (str): Name of the file to mark as processed.
        """
        os.makedirs(self.download_dir, exist_ok=True)
        with open(self.processed_files_log, 'a',
                  encoding='utf-8') as file:
            file.write(f"{filename}\n")
        self.processed_files.add(filename)

    def check_api_health(self):
        """Check if VM2 API is reachable.

        Returns:
            bool: True if API is reachable, False otherwise.
        """
        try:
            response = requests.get(
                f"{self.api_url}/", timeout=5
            )
            if response.status_code == 200:
                logger.info("✓ Connected to VM2 API at %s", self.api_url)
                return True

            logger.warning("VM2 API returned status %s",
                           response.status_code)
            return False
        except requests.exceptions.RequestException as error:
            logger.error("✗ Cannot connect to VM2 API: %s", error)
            return False

    def get_available_logs(self):
        """Get list of available log files from VM2.

        Returns:
            list: List of available log file dictionaries.
        """
        try:
            response = requests.get(
                f"{self.api_url}/logs", timeout=10
            )
            response.raise_for_status()

            data = response.json()
            logger.info("Found %s log files on VM2", data['count'])
            return data['files']

        except requests.exceptions.RequestException as error:
            logger.error("Error fetching log list: %s", error)
            return []

    def get_new_logs(self):
        """Get list of new log files that haven't been processed.

        Returns:
            list: List of new log file dictionaries.
        """
        available_logs = self.get_available_logs()

        if not available_logs:
            return []

        new_logs = [
            log for log in available_logs
            if log['filename'] not in self.processed_files
        ]

        if new_logs:
            logger.info("Found %s new log files to process", len(new_logs))
        else:
            logger.info("All %s logs already processed",
                        len(available_logs))

        return new_logs

    def download_log_file(self, filename):
        """Download a specific log file from VM2.

        Args:
            filename (str): Name of the file to download.

        Returns:
            tuple: (filepath, file_size) if successful,
                   (None, 0) if failed.
        """
        try:
            url = f"{self.api_url}/logs/{filename}"
            logger.info("Downloading %s...", filename)

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            os.makedirs(self.download_dir, exist_ok=True)
            filepath = os.path.join(self.download_dir, filename)

            with open(filepath, 'wb') as file:
                file.write(response.content)

            file_size = len(response.content)
            logger.info("✓ Downloaded %s (%s bytes)", filename, file_size)
            return filepath, file_size

        except requests.exceptions.RequestException as error:
            logger.error("Error downloading %s: %s", filename, error)
            return None, 0

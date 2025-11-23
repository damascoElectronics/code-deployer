#!/usr/bin/env python3
"""Database module for log_processor.

This module handles all MySQL database connections and operations
for storing and retrieving log data.
"""

import logging
from . import config
import mysql.connector
from datetime import datetime
from mysql.connector import Error

logger = logging.getLogger('log_processor.database')


class DatabaseManager:
    """Manages MySQL database connections and operations."""

    def __init__(self):
        """Initialize database manager and connect to MySQL."""
        self.connection = None
        self.connect()

    def connect(self):
        """Connect to MySQL database.

        Returns:
            bool: True if connection successful, False otherwise.
        """
        try:
            self.connection = mysql.connector.connect(
                host=config.MYSQL_HOST,
                port=config.MYSQL_PORT,
                user=config.MYSQL_USER,
                password=config.MYSQL_PASSWORD,
                database=config.MYSQL_DATABASE,
                autocommit=False
            )

            if self.connection.is_connected():
                db_info = self.connection.get_server_info()
                logger.info("✓ Connected to MySQL Server version %s",
                            db_info)
                cursor = self.connection.cursor()
                cursor.execute("SELECT DATABASE();")
                record = cursor.fetchone()
                logger.info("✓ Connected to database: %s", record[0])
                cursor.close()
                return True
        except Error as error:
            logger.error("✗ Error connecting to MySQL: %s", error)
            self.connection = None
            return False

        return False

    def is_connected(self):
        """Check if database connection is active.

        Returns:
            bool: True if connected, False otherwise.
        """
        if self.connection is None:
            return False
        try:
            return self.connection.is_connected()
        except (Error, AttributeError):
            return False

    def reconnect(self):
        """Reconnect to database if connection is lost.

        Returns:
            bool: True if reconnection successful, False otherwise.
        """
        if not self.is_connected():
            logger.info("Attempting to reconnect to database...")
            return self.connect()
        return True

    def insert_key_creation(self, key_identity, sequence_number,
                            source_site, dest_site, key_type,
                            timestamp_str, log_file):
        """Insert key creation record.

        Args:
            key_identity (str): UUID of the key.
            sequence_number (int): Sequence number of the key.
            source_site (int): Source site ID.
            dest_site (int): Destination site ID.
            key_type (str): Type of key pool.
            timestamp_str (str): ISO timestamp string.
            log_file (str): Source log filename.

        Returns:
            bool: True if insert successful, False otherwise.
        """
        try:
            if not self.reconnect():
                return False

            cursor = self.connection.cursor()

            timestamp = datetime.strptime(
                timestamp_str.split('+')[0], '%Y-%m-%dT%H:%M:%S.%f'
            )

            query = """
                INSERT INTO key_creations
                (key_identity, sequence_number, source_site_id,
                 destination_site_id, key_pool_type, timestamp, log_file)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                sequence_number = VALUES(sequence_number)
            """

            values = (
                key_identity, sequence_number, source_site, dest_site,
                key_type, timestamp, log_file
            )

            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()
            return True

        except Error as error:
            logger.error("Error inserting key creation: %s", error)
            if self.connection:
                self.connection.rollback()
            return False

    def insert_sync_latency(self, latency_ms, timestamp_str, log_file):
        """Insert sync latency metric.

        Args:
            latency_ms (int): Latency in milliseconds.
            timestamp_str (str): ISO timestamp string.
            log_file (str): Source log filename.

        Returns:
            bool: True if insert successful, False otherwise.
        """
        try:
            if not self.reconnect():
                return False

            cursor = self.connection.cursor()
            timestamp = datetime.strptime(
                timestamp_str.split('+')[0], '%Y-%m-%dT%H:%M:%S.%f'
            )

            query = """
                INSERT INTO sync_latency_metrics
                (latency_ms, timestamp, log_file)
                VALUES (%s, %s, %s)
            """

            cursor.execute(query, (latency_ms, timestamp, log_file))
            self.connection.commit()
            cursor.close()
            return True

        except Error as error:
            logger.error("Error inserting sync latency: %s", error)
            if self.connection:
                self.connection.rollback()
            return False

    def insert_key_count(self, bits, keys_count, timestamp_str, log_file):
        """Insert key count metric.

        Args:
            bits (int): Number of bits.
            keys_count (int): Number of keys.
            timestamp_str (str): ISO timestamp string.
            log_file (str): Source log filename.

        Returns:
            bool: True if insert successful, False otherwise.
        """
        try:
            if not self.reconnect():
                return False

            cursor = self.connection.cursor()
            timestamp = datetime.strptime(
                timestamp_str.split('+')[0], '%Y-%m-%dT%H:%M:%S.%f'
            )

            query = """
                INSERT INTO key_count_metrics
                (bits, keys_count, timestamp, log_file)
                VALUES (%s, %s, %s, %s)
            """

            cursor.execute(query, (bits, keys_count, timestamp, log_file))
            self.connection.commit()
            cursor.close()
            return True

        except Error as error:
            logger.error("Error inserting key count: %s", error)
            if self.connection:
                self.connection.rollback()
            return False

    def insert_controller_sync(self, local_site, remote_site,
                                timestamp_str, log_file):
        """Insert controller sync event.

        Args:
            local_site (int): Local site ID.
            remote_site (int): Remote site ID.
            timestamp_str (str): ISO timestamp string.
            log_file (str): Source log filename.

        Returns:
            bool: True if insert successful, False otherwise.
        """
        try:
            if not self.reconnect():
                return False

            cursor = self.connection.cursor()
            timestamp = datetime.strptime(
                timestamp_str.split('+')[0], '%Y-%m-%dT%H:%M:%S.%f'
            )

            query = """
                INSERT INTO controller_syncs
                (local_site_id, remote_site_id, timestamp, log_file)
                VALUES (%s, %s, %s, %s)
            """

            cursor.execute(query, (local_site, remote_site,
                                   timestamp, log_file))
            self.connection.commit()
            cursor.close()
            return True

        except Error as error:
            logger.error("Error inserting controller sync: %s", error)
            if self.connection:
                self.connection.rollback()
            return False

    def mark_file_processed(self, filename, file_size, stats):
        """Mark file as processed in database.

        Args:
            filename (str): Name of the processed file.
            file_size (int): Size of the file in bytes.
            stats (dict): Processing statistics.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if not self.reconnect():
                return False

            cursor = self.connection.cursor()

            query = """
                INSERT INTO processed_files
                (filename, file_size, total_lines, key_creations_count,
                 sync_latency_count, key_count_count,
                 controller_sync_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                file_size = VALUES(file_size),
                total_lines = VALUES(total_lines)
            """

            values = (
                filename, file_size, stats['total_lines'],
                stats['key_creations'], stats['sync_latency'],
                stats['key_counts'], stats['controller_syncs']
            )

            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()
            return True

        except Error as error:
            logger.error("Error marking file as processed: %s", error)
            if self.connection:
                self.connection.rollback()
            return False

    def close(self):
        """Close database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")

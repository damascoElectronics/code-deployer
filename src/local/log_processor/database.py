#!/usr/bin/env python3
"""
Database module for log_processor
Handles all MySQL database operations
"""

import logging
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import config

logger = logging.getLogger('log_processor.database')


class DatabaseManager:
    """Manages MySQL database connections and operations"""
    
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Connect to MySQL database"""
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
                logger.info(f"✓ Connected to MySQL Server version {db_info}")
                cursor = self.connection.cursor()
                cursor.execute("SELECT DATABASE();")
                record = cursor.fetchone()
                logger.info(f"✓ Connected to database: {record[0]}")
                cursor.close()
                return True
        except Error as e:
            logger.error(f"✗ Error connecting to MySQL: {e}")
            self.connection = None
            return False
    
    def is_connected(self):
        """Check if database connection is active"""
        if self.connection is None:
            return False
        try:
            return self.connection.is_connected()
        except:
            return False
    
    def reconnect(self):
        """Reconnect to database if connection is lost"""
        if not self.is_connected():
            logger.info("Attempting to reconnect to database...")
            return self.connect()
        return True
    
    def insert_key_creation(self, key_identity, sequence_number, source_site, 
                           dest_site, key_type, timestamp_str, log_file):
        """Insert key creation record"""
        try:
            if not self.reconnect():
                return False
            
            cursor = self.connection.cursor()
            
            # Parse timestamp
            timestamp = datetime.strptime(timestamp_str.split('+')[0], '%Y-%m-%dT%H:%M:%S.%f')
            
            query = """
                INSERT INTO key_creations 
                (key_identity, sequence_number, source_site_id, destination_site_id, 
                 key_pool_type, timestamp, log_file)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                sequence_number = VALUES(sequence_number)
            """
            
            values = (key_identity, sequence_number, source_site, dest_site, 
                     key_type, timestamp, log_file)
            
            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()
            return True
            
        except Error as e:
            logger.error(f"Error inserting key creation: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def insert_sync_latency(self, latency_ms, timestamp_str, log_file):
        """Insert sync latency metric"""
        try:
            if not self.reconnect():
                return False
            
            cursor = self.connection.cursor()
            timestamp = datetime.strptime(timestamp_str.split('+')[0], '%Y-%m-%dT%H:%M:%S.%f')
            
            query = """
                INSERT INTO sync_latency_metrics 
                (latency_ms, timestamp, log_file)
                VALUES (%s, %s, %s)
            """
            
            cursor.execute(query, (latency_ms, timestamp, log_file))
            self.connection.commit()
            cursor.close()
            return True
            
        except Error as e:
            logger.error(f"Error inserting sync latency: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def insert_key_count(self, bits, keys_count, timestamp_str, log_file):
        """Insert key count metric"""
        try:
            if not self.reconnect():
                return False
            
            cursor = self.connection.cursor()
            timestamp = datetime.strptime(timestamp_str.split('+')[0], '%Y-%m-%dT%H:%M:%S.%f')
            
            query = """
                INSERT INTO key_count_metrics 
                (bits, keys_count, timestamp, log_file)
                VALUES (%s, %s, %s, %s)
            """
            
            cursor.execute(query, (bits, keys_count, timestamp, log_file))
            self.connection.commit()
            cursor.close()
            return True
            
        except Error as e:
            logger.error(f"Error inserting key count: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def insert_controller_sync(self, local_site, remote_site, timestamp_str, log_file):
        """Insert controller sync event"""
        try:
            if not self.reconnect():
                return False
            
            cursor = self.connection.cursor()
            timestamp = datetime.strptime(timestamp_str.split('+')[0], '%Y-%m-%dT%H:%M:%S.%f')
            
            query = """
                INSERT INTO controller_syncs 
                (local_site_id, remote_site_id, timestamp, log_file)
                VALUES (%s, %s, %s, %s)
            """
            
            cursor.execute(query, (local_site, remote_site, timestamp, log_file))
            self.connection.commit()
            cursor.close()
            return True
            
        except Error as e:
            logger.error(f"Error inserting controller sync: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def mark_file_processed(self, filename, file_size, stats):
        """Mark file as processed in database"""
        try:
            if not self.reconnect():
                return False
            
            cursor = self.connection.cursor()
            
            query = """
                INSERT INTO processed_files 
                (filename, file_size, total_lines, key_creations_count, 
                 sync_latency_count, key_count_count, controller_sync_count)
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
            
        except Error as e:
            logger.error(f"Error marking file as processed: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")
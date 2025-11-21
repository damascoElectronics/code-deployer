"""
Base Processor Class

Provides common functionality for all processors.
"""

import logging
import mysql.connector
from abc import ABC, abstractmethod


class BaseProcessor(ABC):
    """
    Abstract base class for all data processors.

    Provides:
    - Database connection management with auto-reconnect
    - Common logging setup
    - Standard start/stop interface
    """

    def __init__(self, config, name):
        """
        Initialize base processor.

        Args:
            config: Configuration object
            name: Processor name for logging
        """
        self.config = config
        self.name = name
        self.running = False
        self.db_conn = None
        self.logger = logging.getLogger(f"processor.{name}")

        self.stats = {
            "total_processed": 0,
            "failed": 0,
            "last_process": None
        }

    def connect_db(self):
        """
        Connect to MySQL database with retry logic.

        Returns:
            True if connected, False otherwise
        """
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                if self.db_conn:
                    try:
                        self.db_conn.close()
                    except:
                        pass

                self.db_conn = mysql.connector.connect(
                    host=self.config.DB_HOST,
                    port=self.config.DB_PORT,
                    database=self.config.DB_NAME,
                    user=self.config.DB_USER,
                    password=self.config.DB_PASSWORD,
                    autocommit=True,  # AVIOD LONG TRANSACTIONS
                    connection_timeout=10,
                    pool_reset_session=False
                )

                if self.db_conn.is_connected():
                    self.logger.info("Connected to database")
                    return True

            except mysql.connector.Error as e:
                self.logger.warning(
                    f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}"
                )
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)

        self.logger.error("Failed to connect to database after all retries")
        return False

    def ensure_connection(self):
        """
        Ensure database connection is alive, reconnect if needed.

        Returns:
            True if connected, False otherwise
        """
        try:
            if self.db_conn is None or not self.db_conn.is_connected():
                self.logger.warning("Database connection lost, reconnecting...")
                return self.connect_db()

            # Ping to check connection
            self.db_conn.ping(reconnect=True, attempts=2, delay=1)
            return True

        except Exception as e:
            self.logger.warning("Connection check failed: {e}, reconnecting...")
            return self.connect_db()

    def disconnect_db(self):
        """Close database connection."""
        if self.db_conn:
            try:
                self.db_conn.close()
                self.logger.info("Database connection closed")
            except Exception as e:
                self.logger.error("Error closing database: {e}")

    @abstractmethod
    def process_data(self):
        """
        Process data - must be implemented by subclasses.

        Returns:
            True if processing successful, False otherwise
        """
        pass

    @abstractmethod
    def run(self):
        """
        Main processing loop - must be implemented by subclasses.
        """
        pass

    def stop(self):
        """Stop the processor."""
        self.logger.info("Stopping {self.name} processor...")
        self.running = False
        self.disconnect_db()

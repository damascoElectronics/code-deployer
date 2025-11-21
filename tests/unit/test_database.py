"""Unit tests for database.py module from log_processor.

Tests database operations with mocked MySQL connections.
Fixed to properly mock config module.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import sys


@pytest.fixture
def mock_mysql_connection():
    """Mock MySQL connection for testing."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.is_connected.return_value = True
    return mock_conn, mock_cursor


@pytest.fixture
def mock_config():
    """Mock config module."""
    config_mock = MagicMock()
    config_mock.MYSQL_HOST = '127.0.0.1'
    config_mock.MYSQL_PORT = 3306
    config_mock.MYSQL_USER = 'test_user'
    config_mock.MYSQL_PASSWORD = 'test_pass'
    config_mock.MYSQL_DATABASE = 'test_db'
    return config_mock


class TestDatabaseManager:
    """Unit tests for DatabaseManager class."""

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_connect_success(self, mock_connect, mock_config):
        """Test successful database connection."""
        # Mock config in sys.modules before import
        sys.modules['config'] = mock_config
        
        try:
            from src.local.log_processor.database import DatabaseManager
            
            mock_conn = MagicMock()
            mock_conn.is_connected.return_value = True
            mock_connect.return_value = mock_conn
            
            db = DatabaseManager()
            
            assert db.connection is not None
            assert db.is_connected()
            mock_connect.assert_called_once()
        finally:
            # Cleanup
            if 'config' in sys.modules:
                del sys.modules['config']
            if 'src.local.log_processor.database' in sys.modules:
                del sys.modules['src.local.log_processor.database']

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_connect_failure(self, mock_connect, mock_config):
        """Test database connection failure."""
        sys.modules['config'] = mock_config
        
        try:
            from src.local.log_processor.database import DatabaseManager
            
            mock_connect.side_effect = Exception("Connection failed")
            
            db = DatabaseManager()
            
            assert db.connection is None
            assert not db.is_connected()
        finally:
            if 'config' in sys.modules:
                del sys.modules['config']
            if 'src.local.log_processor.database' in sys.modules:
                del sys.modules['src.local.log_processor.database']

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_insert_key_creation_success(self, mock_connect, mock_mysql_connection, mock_config):
        """Test successful key creation insertion."""
        sys.modules['config'] = mock_config
        
        try:
            from src.local.log_processor.database import DatabaseManager
            
            mock_conn, mock_cursor = mock_mysql_connection
            mock_connect.return_value = mock_conn
            
            db = DatabaseManager()
            
            result = db.insert_key_creation(
                key_identity='550e8400-e29b-41d4-a716-446655440000',
                sequence_number=12345,
                source_site=101,
                dest_site=102,
                key_type='PUBLIC',
                timestamp_str='2024-01-01T10:00:00.000000+0000',
                log_file='test.log'
            )
            
            assert result is True
            mock_cursor.execute.assert_called_once()
            mock_conn.commit.assert_called_once()
        finally:
            if 'config' in sys.modules:
                del sys.modules['config']
            if 'src.local.log_processor.database' in sys.modules:
                del sys.modules['src.local.log_processor.database']

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_insert_key_creation_failure(self, mock_connect, mock_mysql_connection, mock_config):
        """Test key creation insertion with database error."""
        sys.modules['config'] = mock_config
        
        try:
            from src.local.log_processor.database import DatabaseManager
            
            mock_conn, mock_cursor = mock_mysql_connection
            mock_cursor.execute.side_effect = Exception("DB Error")
            mock_connect.return_value = mock_conn
            
            db = DatabaseManager()
            
            result = db.insert_key_creation(
                key_identity='550e8400-e29b-41d4-a716-446655440000',
                sequence_number=12345,
                source_site=101,
                dest_site=102,
                key_type='PUBLIC',
                timestamp_str='2024-01-01T10:00:00.000000+0000',
                log_file='test.log'
            )
            
            assert result is False
            mock_conn.rollback.assert_called_once()
        finally:
            if 'config' in sys.modules:
                del sys.modules['config']
            if 'src.local.log_processor.database' in sys.modules:
                del sys.modules['src.local.log_processor.database']

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_insert_sync_latency(self, mock_connect, mock_mysql_connection, mock_config):
        """Test sync latency insertion."""
        sys.modules['config'] = mock_config
        
        try:
            from src.local.log_processor.database import DatabaseManager
            
            mock_conn, mock_cursor = mock_mysql_connection
            mock_connect.return_value = mock_conn
            
            db = DatabaseManager()
            
            result = db.insert_sync_latency(
                latency_ms=150,
                timestamp_str='2024-01-01T10:00:00.000000+0000',
                log_file='test.log'
            )
            
            assert result is True
            mock_cursor.execute.assert_called_once()
        finally:
            if 'config' in sys.modules:
                del sys.modules['config']
            if 'src.local.log_processor.database' in sys.modules:
                del sys.modules['src.local.log_processor.database']

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_reconnect_when_disconnected(self, mock_connect, mock_config):
        """Test automatic reconnection when connection is lost."""
        sys.modules['config'] = mock_config
        
        try:
            from src.local.log_processor.database import DatabaseManager
            
            mock_conn = MagicMock()
            mock_conn.is_connected.side_effect = [True, False, True]
            mock_connect.return_value = mock_conn
            
            db = DatabaseManager()
            
            # First call - connected
            assert db.is_connected()
            
            # Second call - disconnected, should reconnect
            assert db.reconnect()
        finally:
            if 'config' in sys.modules:
                del sys.modules['config']
            if 'src.local.log_processor.database' in sys.modules:
                del sys.modules['src.local.log_processor.database']

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_mark_file_processed(self, mock_connect, mock_mysql_connection, mock_config):
        """Test marking file as processed."""
        sys.modules['config'] = mock_config
        
        try:
            from src.local.log_processor.database import DatabaseManager
            
            mock_conn, mock_cursor = mock_mysql_connection
            mock_connect.return_value = mock_conn
            
            db = DatabaseManager()
            
            stats = {
                'total_lines': 100,
                'key_creations': 50,
                'sync_latency': 10,
                'key_counts': 5,
                'controller_syncs': 2
            }
            
            result = db.mark_file_processed('test.log', 1024, stats)
            
            assert result is True
            mock_cursor.execute.assert_called_once()
        finally:
            if 'config' in sys.modules:
                del sys.modules['config']
            if 'src.local.log_processor.database' in sys.modules:
                del sys.modules['src.local.log_processor.database']

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_close_connection(self, mock_connect, mock_config):
        """Test closing database connection."""
        sys.modules['config'] = mock_config
        
        try:
            from src.local.log_processor.database import DatabaseManager
            
            mock_conn = MagicMock()
            mock_conn.is_connected.return_value = True
            mock_connect.return_value = mock_conn
            
            db = DatabaseManager()
            db.close()
            
            mock_conn.close.assert_called_once()
        finally:
            if 'config' in sys.modules:
                del sys.modules['config']
            if 'src.local.log_processor.database' in sys.modules:
                del sys.modules['src.local.log_processor.database']
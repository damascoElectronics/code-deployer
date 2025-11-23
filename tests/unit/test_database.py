"""Unit tests for database.py module from log_processor."""

import pytest
from unittest.mock import MagicMock, patch
import importlib


class TestDatabaseManager:
    """Unit tests for DatabaseManager class."""

    @pytest.mark.unit
    @patch('src.local.log_processor.database.config')
    @patch('src.local.log_processor.database.mysql.connector.connect')
    def test_connect_success(self, mock_connect, mock_config):
        """Test successful database connection."""
        mock_config.MYSQL_HOST = '127.0.0.1'
        mock_config.MYSQL_PORT = 3306
        mock_config.MYSQL_USER = 'test_user'
        mock_config.MYSQL_PASSWORD = 'test_pass'
        mock_config.MYSQL_DATABASE = 'test_db'

        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_conn.get_server_info.return_value = '8.0'
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ('test_db',)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        from src.local.log_processor.database import DatabaseManager
        db = DatabaseManager()

        assert db.is_connected()
        mock_connect.assert_called_once()

    @pytest.mark.unit
    @patch('src.local.log_processor.database.config')
    @patch('src.local.log_processor.database.mysql.connector.connect')
    def test_connect_failure(self, mock_connect, mock_config):
        """Test database connection failure."""
        from mysql.connector import Error
        
        mock_config.MYSQL_HOST = '127.0.0.1'
        mock_config.MYSQL_PORT = 3306
        mock_config.MYSQL_USER = 'test_user'
        mock_config.MYSQL_PASSWORD = 'test_pass'
        mock_config.MYSQL_DATABASE = 'test_db'

        mock_connect.side_effect = Error("Connection failed")

        from src.local.log_processor import database
        importlib.reload(database)
        
        db = database.DatabaseManager()

        assert not db.is_connected()

    @pytest.mark.unit
    @patch('src.local.log_processor.database.config')
    @patch('src.local.log_processor.database.mysql.connector.connect')
    def test_insert_key_creation_success(self, mock_connect, mock_config):
        """Test successful key creation insertion."""
        mock_config.MYSQL_HOST = '127.0.0.1'
        mock_config.MYSQL_PORT = 3306
        mock_config.MYSQL_USER = 'test_user'
        mock_config.MYSQL_PASSWORD = 'test_pass'
        mock_config.MYSQL_DATABASE = 'test_db'

        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_conn.get_server_info.return_value = '8.0'
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ('test_db',)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        from src.local.log_processor.database import DatabaseManager
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

    @pytest.mark.unit
    @patch('src.local.log_processor.database.config')
    @patch('src.local.log_processor.database.mysql.connector.connect')
    def test_insert_key_creation_failure(self, mock_connect, mock_config):
        """Test key creation insertion with database error."""
        from mysql.connector import Error
        
        mock_config.MYSQL_HOST = '127.0.0.1'
        mock_config.MYSQL_PORT = 3306
        mock_config.MYSQL_USER = 'test_user'
        mock_config.MYSQL_PASSWORD = 'test_pass'
        mock_config.MYSQL_DATABASE = 'test_db'

        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_conn.get_server_info.return_value = '8.0'
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ('test_db',)
        # First call for init, second call fails
        mock_cursor.execute.side_effect = [None, Error("DB Error")]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        from src.local.log_processor import database
        importlib.reload(database)
        
        db = database.DatabaseManager()

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

    @pytest.mark.unit
    @patch('src.local.log_processor.database.config')
    @patch('src.local.log_processor.database.mysql.connector.connect')
    def test_close_connection(self, mock_connect, mock_config):
        """Test closing database connection."""
        mock_config.MYSQL_HOST = '127.0.0.1'
        mock_config.MYSQL_PORT = 3306
        mock_config.MYSQL_USER = 'test_user'
        mock_config.MYSQL_PASSWORD = 'test_pass'
        mock_config.MYSQL_DATABASE = 'test_db'

        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_conn.get_server_info.return_value = '8.0'
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ('test_db',)
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        from src.local.log_processor.database import DatabaseManager
        db = DatabaseManager()
        db.close()

        mock_conn.close.assert_called_once()

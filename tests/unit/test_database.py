"""Additional unit tests for database.py to increase coverage.

Tests for insert_sync_latency, insert_key_count, insert_controller_sync,
mark_file_processed, and reconnect methods.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime
from mysql.connector import Error


class TestDatabaseManagerAdditional:
    """Additional tests for DatabaseManager to increase coverage."""

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_insert_sync_latency_success(self, mock_connect):
        """Test successful sync latency insertion."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn

        from src.local.log_processor.database import DatabaseManager
        db = DatabaseManager()

        result = db.insert_sync_latency(
            latency_ms=85,
            timestamp_str='2024-01-15T10:30:46.456+0000',
            log_file='test.log'
        )

        assert result is True
        # Use call_count >= 2 because __init__ also calls execute
        assert mock_cursor.execute.call_count >= 2
        mock_conn.commit.assert_called()

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_insert_sync_latency_failure(self, mock_connect):
        """Test sync latency insertion failure."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # First call succeeds (SELECT DATABASE), second fails (INSERT)
        mock_cursor.execute.side_effect = [MagicMock(), Error("Insert failed")]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn

        from src.local.log_processor.database import DatabaseManager
        db = DatabaseManager()

        result = db.insert_sync_latency(
            latency_ms=85,
            timestamp_str='2024-01-15T10:30:46.456+0000',
            log_file='test.log'
        )

        assert result is False
        mock_conn.rollback.assert_called()

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_insert_key_count_success(self, mock_connect):
        """Test successful key count insertion."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn

        from src.local.log_processor.database import DatabaseManager
        db = DatabaseManager()

        result = db.insert_key_count(
            bits=2560,
            keys_count=10,
            timestamp_str='2024-01-15T10:30:47.789+0000',
            log_file='test.log'
        )

        assert result is True
        assert mock_cursor.execute.call_count >= 2
        mock_conn.commit.assert_called()

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_insert_key_count_failure(self, mock_connect):
        """Test key count insertion failure."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # First call succeeds (SELECT DATABASE), second fails (INSERT)
        mock_cursor.execute.side_effect = [MagicMock(), Error("Insert failed")]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn

        from src.local.log_processor.database import DatabaseManager
        db = DatabaseManager()

        result = db.insert_key_count(
            bits=2560,
            keys_count=10,
            timestamp_str='2024-01-15T10:30:47.789+0000',
            log_file='test.log'
        )

        assert result is False
        mock_conn.rollback.assert_called()

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_insert_controller_sync_success(self, mock_connect):
        """Test successful controller sync insertion."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn

        from src.local.log_processor.database import DatabaseManager
        db = DatabaseManager()

        result = db.insert_controller_sync(
            local_site=101,
            remote_site=102,
            timestamp_str='2024-01-15T10:30:45.123+0000',
            log_file='test.log'
        )

        assert result is True
        assert mock_cursor.execute.call_count >= 2
        mock_conn.commit.assert_called()

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_insert_controller_sync_failure(self, mock_connect):
        """Test controller sync insertion failure."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # First call succeeds (SELECT DATABASE), second fails (INSERT)
        mock_cursor.execute.side_effect = [MagicMock(), Error("Insert failed")]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn

        from src.local.log_processor.database import DatabaseManager
        db = DatabaseManager()

        result = db.insert_controller_sync(
            local_site=101,
            remote_site=102,
            timestamp_str='2024-01-15T10:30:45.123+0000',
            log_file='test.log'
        )

        assert result is False
        mock_conn.rollback.assert_called()

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_mark_file_processed_success(self, mock_connect):
        """Test successful file processed marking."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn

        from src.local.log_processor.database import DatabaseManager
        db = DatabaseManager()

        stats = {
            'total_lines': 100,
            'key_creations': 50,
            'sync_latency': 20,
            'key_counts': 10,
            'controller_syncs': 5
        }

        result = db.mark_file_processed('test.log', 1024, stats)

        assert result is True
        assert mock_cursor.execute.call_count >= 2
        mock_conn.commit.assert_called()

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_mark_file_processed_failure(self, mock_connect):
        """Test file processed marking failure."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # First call succeeds (SELECT DATABASE), second fails (INSERT)
        mock_cursor.execute.side_effect = [MagicMock(), Error("Insert failed")]
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn

        from src.local.log_processor.database import DatabaseManager
        db = DatabaseManager()

        stats = {
            'total_lines': 100,
            'key_creations': 50,
            'sync_latency': 20,
            'key_counts': 10,
            'controller_syncs': 5
        }

        result = db.mark_file_processed('test.log', 1024, stats)

        assert result is False
        mock_conn.rollback.assert_called()

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_reconnect_when_disconnected(self, mock_connect):
        """Test reconnection when disconnected."""
        mock_conn = MagicMock()
        mock_conn.is_connected.side_effect = [True, False, True]
        mock_connect.return_value = mock_conn

        from src.local.log_processor.database import DatabaseManager
        db = DatabaseManager()

        # Force disconnection state
        db.connection.is_connected.return_value = False

        result = db.reconnect()

        assert result is True

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_reconnect_when_connected(self, mock_connect):
        """Test reconnect when already connected."""
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn

        from src.local.log_processor.database import DatabaseManager
        db = DatabaseManager()

        result = db.reconnect()

        assert result is True

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_is_connected_when_none(self, mock_connect):
        """Test is_connected returns False when connection is None."""
        mock_connect.side_effect = Error("Connection failed")

        from src.local.log_processor.database import DatabaseManager
        db = DatabaseManager()

        assert db.is_connected() is False

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_insert_key_creation_reconnect_failure(self, mock_connect):
        """Test insert_key_creation when reconnect fails."""
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = False
        mock_connect.return_value = mock_conn

        from src.local.log_processor.database import DatabaseManager
        db = DatabaseManager()

        # Force reconnect to fail
        db.connection = None

        result = db.insert_key_creation(
            key_identity='12345678-1234-5678-90ab-cdef12345678',
            sequence_number=1001,
            source_site=102,
            dest_site=101,
            key_type='PUBLIC',
            timestamp_str='2024-01-15T10:30:45.123+0000',
            log_file='test.log'
        )

        assert result is False

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_insert_sync_latency_reconnect_failure(self, mock_connect):
        """Test insert_sync_latency when reconnect fails."""
        from src.local.log_processor.database import DatabaseManager

        mock_connect.side_effect = Error("Connection failed")
        db = DatabaseManager()
        db.connection = None

        result = db.insert_sync_latency(
            latency_ms=85,
            timestamp_str='2024-01-15T10:30:46.456+0000',
            log_file='test.log'
        )

        assert result is False

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_insert_key_count_reconnect_failure(self, mock_connect):
        """Test insert_key_count when reconnect fails."""
        from src.local.log_processor.database import DatabaseManager

        mock_connect.side_effect = Error("Connection failed")
        db = DatabaseManager()
        db.connection = None

        result = db.insert_key_count(
            bits=2560,
            keys_count=10,
            timestamp_str='2024-01-15T10:30:47.789+0000',
            log_file='test.log'
        )

        assert result is False

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_insert_controller_sync_reconnect_failure(self, mock_connect):
        """Test insert_controller_sync when reconnect fails."""
        from src.local.log_processor.database import DatabaseManager

        mock_connect.side_effect = Error("Connection failed")
        db = DatabaseManager()
        db.connection = None

        result = db.insert_controller_sync(
            local_site=101,
            remote_site=102,
            timestamp_str='2024-01-15T10:30:45.123+0000',
            log_file='test.log'
        )

        assert result is False

    @pytest.mark.unit
    @patch('mysql.connector.connect')
    def test_mark_file_processed_reconnect_failure(self, mock_connect):
        """Test mark_file_processed when reconnect fails."""
        from src.local.log_processor.database import DatabaseManager

        mock_connect.side_effect = Error("Connection failed")
        db = DatabaseManager()
        db.connection = None

        stats = {
            'total_lines': 100,
            'key_creations': 50,
            'sync_latency': 20,
            'key_counts': 10,
            'controller_syncs': 5
        }

        result = db.mark_file_processed('test.log', 1024, stats)

        assert result is False
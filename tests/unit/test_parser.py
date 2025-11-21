"""Unit tests for parser.py module from log_processor.

Tests log parsing logic with various log formats.
"""

import pytest
from unittest.mock import Mock, MagicMock
import os


class TestLogParser:
    """Unit tests for LogParser class."""

    @pytest.mark.unit
    def test_parse_key_creation_entry(self):
        """Test parsing key creation log entry."""
        from src.local.log_processor.parser import LogParser
        
        mock_db = Mock()
        parser = LogParser(mock_db)
        
        log_line = (
            "2024-01-01T10:00:00.000000+0000 SiteId: 101  INFO 26 "
            "[quartzScheduler_Worker-1] c.e.q.k.k.KeyPoolServiceImpl : "
            "createKey: KeyPoolService successfully created key with identity = "
            "'550e8400-e29b-41d4-a716-446655440000', sequence number 12345, and KeyPool "
            "{Source site identity = '101', Destination site identity = '102', "
            "and KeyPoolType name = 'PUBLIC'}"
        )
        
        entry = parser.parse_log_entry(log_line)
        
        assert entry is not None
        assert entry['log_type'] == 'KEY_CREATION'
        assert entry['key_identity'] == '550e8400-e29b-41d4-a716-446655440000'
        assert entry['sequence_number'] == 12345
        assert entry['source_site'] == 101
        assert entry['dest_site'] == 102
        assert entry['key_type'] == 'PUBLIC'

    @pytest.mark.unit
    def test_parse_sync_latency_entry(self):
        """Test parsing sync latency metric."""
        from src.local.log_processor.parser import LogParser
        
        mock_db = Mock()
        parser = LogParser(mock_db)
        
        log_line = (
            "2024-01-01T10:00:00.000000+0000 SiteId: 101  INFO 26 "
            "[quartzScheduler_Worker-1] c.e.q.k.k.KeySyncServiceImpl : "
            "METRIC_KEY_SYNC_LATENCY MS=150"
        )
        
        entry = parser.parse_log_entry(log_line)
        
        assert entry is not None
        assert entry['log_type'] == 'SYNC_LATENCY'
        assert entry['latency_ms'] == 150

    @pytest.mark.unit
    def test_parse_key_count_entry(self):
        """Test parsing key count metric."""
        from src.local.log_processor.parser import LogParser
        
        mock_db = Mock()
        parser = LogParser(mock_db)
        
        log_line = (
            "2024-01-01T10:00:00.000000+0000 SiteId: 101  INFO 26 "
            "[quartzScheduler_Worker-1] c.e.q.k.k.KeySyncServiceImpl : "
            "METRIC_RECEIVED_PUBLIC_KEY_COUNT BITS=12800 KEYS=50"
        )
        
        entry = parser.parse_log_entry(log_line)
        
        assert entry is not None
        assert entry['log_type'] == 'KEY_COUNT'
        assert entry['bits'] == 12800
        assert entry['keys_count'] == 50

    @pytest.mark.unit
    def test_parse_controller_sync_entry(self):
        """Test parsing controller sync event."""
        from src.local.log_processor.parser import LogParser
        
        mock_db = Mock()
        parser = LogParser(mock_db)
        
        log_line = (
            "2024-01-01T10:00:00.000000+0000 SiteId: 101  INFO 26 "
            "[https-jsse-nio-9500-exec-1] c.e.q.k.k.w.KeyPoolController : "
            "Handling qnl db sync with remote site 102"
        )
        
        entry = parser.parse_log_entry(log_line)
        
        assert entry is not None
        assert entry['log_type'] == 'CONTROLLER_SYNC'
        assert entry['local_site'] == 101
        assert entry['remote_site'] == 102

    @pytest.mark.unit
    def test_parse_invalid_entry(self):
        """Test parsing invalid log entry."""
        from src.local.log_processor.parser import LogParser
        
        mock_db = Mock()
        parser = LogParser(mock_db)
        
        log_line = "Invalid log line"
        
        entry = parser.parse_log_entry(log_line)
        
        assert entry is None

    @pytest.mark.unit
    def test_parse_unknown_entry(self):
        """Test parsing unknown log entry type."""
        from src.local.log_processor.parser import LogParser
        
        mock_db = Mock()
        parser = LogParser(mock_db)
        
        log_line = "2024-01-01T10:00:00.000000+0000 SiteId: 101  INFO Unknown event"
        
        entry = parser.parse_log_entry(log_line)
        
        assert entry is not None
        assert entry['log_type'] == 'UNKNOWN'

    @pytest.mark.unit
    def test_store_entry_key_creation(self):
        """Test storing key creation entry."""
        from src.local.log_processor.parser import LogParser
        
        mock_db = Mock()
        mock_db.insert_key_creation.return_value = True
        parser = LogParser(mock_db)
        
        entry = {
            'log_type': 'KEY_CREATION',
            'key_identity': '550e8400-e29b-41d4-a716-446655440000',
            'sequence_number': 12345,
            'source_site': 101,
            'dest_site': 102,
            'key_type': 'PUBLIC',
            'timestamp': '2024-01-01T10:00:00.000000+0000'
        }
        
        result = parser._store_entry(entry, 'test.log')
        
        assert result is True
        mock_db.insert_key_creation.assert_called_once()

    @pytest.mark.unit
    def test_process_log_file_success(self, tmp_path):
        """Test processing complete log file."""
        from src.local.log_processor.parser import LogParser
        
        # Create temporary log file
        log_file = tmp_path / "test.log"
        log_content = """2024-01-01T10:00:00.000000+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-1] c.e.q.k.k.KeyPoolServiceImpl : createKey: KeyPoolService successfully created key with identity = '550e8400-e29b-41d4-a716-446655440000', sequence number 12345, and KeyPool {Source site identity = '101', Destination site identity = '102', and KeyPoolType name = 'PUBLIC'}
2024-01-01T10:00:01.000000+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-1] c.e.q.k.k.KeySyncServiceImpl : METRIC_KEY_SYNC_LATENCY MS=150
"""
        log_file.write_text(log_content)
        
        mock_db = Mock()
        mock_db.insert_key_creation.return_value = True
        mock_db.insert_sync_latency.return_value = True
        mock_db.mark_file_processed.return_value = True
        
        parser = LogParser(mock_db)
        stats = parser.process_log_file(str(log_file))
        
        assert stats is not None
        assert stats['total_lines'] == 2
        assert stats['key_creations'] == 1
        assert stats['sync_latency'] == 1

    @pytest.mark.unit
    def test_process_log_file_nonexistent(self):
        """Test processing nonexistent log file."""
        from src.local.log_processor.parser import LogParser
        
        mock_db = Mock()
        parser = LogParser(mock_db)
        
        stats = parser.process_log_file('/nonexistent/file.log')
        
        assert stats is None

    @pytest.mark.unit
    def test_parse_malformed_timestamp(self):
        """Test parsing entry with malformed timestamp."""
        from src.local.log_processor.parser import LogParser
        
        mock_db = Mock()
        parser = LogParser(mock_db)
        
        log_line = "InvalidTimestamp SiteId: 101"
        
        entry = parser.parse_log_entry(log_line)
        
        assert entry is None
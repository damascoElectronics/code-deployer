"""Integration tests for log_processor workflow.

Tests the complete workflow: download -> parse -> store in database.
"""

import os
import tempfile
import pytest
import requests
from unittest.mock import Mock, MagicMock, patch, mock_open


class TestLogProcessorWorkflow:
    """Integration tests for complete log processing workflow."""

    @pytest.mark.integration
    def test_full_workflow_download_parse_store(self):
        """Test complete workflow: download log, parse it, store in DB."""
        # Sample log content with valid 36-char UUIDs
        log_content = """2024-01-15T10:30:45.123+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-3] c.e.q.k.k.KeyPoolServiceImpl             : createKey: KeyPoolService successfully created key with identity = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', sequence number 477001, and KeyPool {Source site identity = '102', Destination site identity = '101', and KeyPoolType name = 'PUBLIC'}
2024-01-15T10:30:46.456+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-5] c.e.q.k.k.KeySyncServiceImpl             : METRIC_KEY_SYNC_LATENCY MS=85
2024-01-15T10:30:47.789+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-7] c.e.q.k.k.KeySyncServiceImpl             : METRIC_RECEIVED_PUBLIC_KEY_COUNT BITS=2560 KEYS=10
"""
        
        with patch('src.local.log_processor.downloader.config') as mock_dl_config:
            mock_dl_config.DOWNLOAD_DIR = '/tmp/test_logs'
            mock_dl_config.PROCESSED_FILES_LOG = '/tmp/test_logs/processed.txt'
            mock_dl_config.VM2_API_URL = 'http://test:8080'
            
            with patch('os.path.exists', return_value=False):
                with patch('os.makedirs'):
                    with patch('src.local.log_processor.downloader.requests.get') as mock_get:
                        # Mock API responses
                        mock_list_response = MagicMock()
                        mock_list_response.status_code = 200
                        mock_list_response.json.return_value = {
                            'count': 1,
                            'files': [{'filename': 'test.log'}]
                        }
                        
                        mock_download_response = MagicMock()
                        mock_download_response.content = log_content.encode()
                        
                        mock_get.side_effect = [mock_list_response, mock_download_response]
                        
                        from src.local.log_processor.downloader import LogDownloader
                        downloader = LogDownloader()
                        
                        new_logs = downloader.get_new_logs()
                        assert len(new_logs) == 1
                        
                        with patch('builtins.open', mock_open()):
                            filepath, size = downloader.download_log_file('test.log')
                            assert filepath == '/tmp/test_logs/test.log'
                            assert size > 0

        # Now test parsing
        mock_db = MagicMock()
        mock_db.insert_key_creation.return_value = True
        mock_db.insert_sync_latency.return_value = True
        mock_db.insert_key_count.return_value = True
        mock_db.mark_file_processed.return_value = True
        
        from src.local.log_processor.parser import LogParser
        parser = LogParser(mock_db)
        
        lines = log_content.strip().split('\n')
        
        entry1 = parser.parse_log_entry(lines[0])
        assert entry1['log_type'] == 'KEY_CREATION'
        assert entry1['key_identity'] == 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        assert entry1['sequence_number'] == 477001
        
        entry2 = parser.parse_log_entry(lines[1])
        assert entry2['log_type'] == 'SYNC_LATENCY'
        assert entry2['latency_ms'] == 85
        
        entry3 = parser.parse_log_entry(lines[2])
        assert entry3['log_type'] == 'KEY_COUNT'
        assert entry3['keys_count'] == 10

    @pytest.mark.integration
    def test_workflow_with_temp_file(self):
        """Test workflow using actual temp file."""
        # Valid 36-char UUID format
        log_content = """2024-01-15T10:30:45.123+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-3] c.e.q.k.k.KeyPoolServiceImpl             : createKey: KeyPoolService successfully created key with identity = '12345678-1234-5678-90ab-cdef12345678', sequence number 500001, and KeyPool {Source site identity = '103', Destination site identity = '101', and KeyPoolType name = 'PRIVATE'}
2024-01-15T10:30:46.456+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-5] c.e.q.k.k.KeySyncServiceImpl             : METRIC_KEY_SYNC_LATENCY MS=120
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(log_content)
            temp_filepath = f.name
        
        try:
            mock_db = MagicMock()
            mock_db.insert_key_creation.return_value = True
            mock_db.insert_sync_latency.return_value = True
            mock_db.insert_key_count.return_value = True
            mock_db.insert_controller_sync.return_value = True
            mock_db.mark_file_processed.return_value = True
            
            from src.local.log_processor.parser import LogParser
            parser = LogParser(mock_db)
            
            stats = parser.process_log_file(temp_filepath)
            
            assert stats is not None
            assert stats['total_lines'] == 2
            assert stats['key_creations'] == 1
            assert stats['sync_latency'] == 1
            
            assert mock_db.insert_key_creation.called
            assert mock_db.insert_sync_latency.called
            assert mock_db.mark_file_processed.called
            
        finally:
            os.unlink(temp_filepath)

    @pytest.mark.integration
    def test_workflow_multiple_key_types(self):
        """Test workflow with multiple key pool types."""
        # All UUIDs must be valid 36-char format
        log_content = """2024-01-15T10:30:45.123+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-1] c.e.q.k.k.KeyPoolServiceImpl             : createKey: KeyPoolService successfully created key with identity = '11111111-1111-1111-1111-111111111111', sequence number 1001, and KeyPool {Source site identity = '102', Destination site identity = '101', and KeyPoolType name = 'PUBLIC'}
2024-01-15T10:30:46.123+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-2] c.e.q.k.k.KeyPoolServiceImpl             : createKey: KeyPoolService successfully created key with identity = '22222222-2222-2222-2222-222222222222', sequence number 1002, and KeyPool {Source site identity = '103', Destination site identity = '101', and KeyPoolType name = 'PRIVATE'}
2024-01-15T10:30:47.123+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-3] c.e.q.k.k.KeyPoolServiceImpl             : createKey: KeyPoolService successfully created key with identity = '33333333-3333-3333-3333-333333333333', sequence number 1003, and KeyPool {Source site identity = '102', Destination site identity = '103', and KeyPoolType name = 'SHARED'}
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(log_content)
            temp_filepath = f.name
        
        try:
            mock_db = MagicMock()
            mock_db.insert_key_creation.return_value = True
            mock_db.mark_file_processed.return_value = True
            
            from src.local.log_processor.parser import LogParser
            parser = LogParser(mock_db)
            
            stats = parser.process_log_file(temp_filepath)
            
            assert stats['key_creations'] == 3
            assert mock_db.insert_key_creation.call_count == 3
            
            calls = mock_db.insert_key_creation.call_args_list
            key_types = [call[0][4] for call in calls]
            
            assert 'PUBLIC' in key_types
            assert 'PRIVATE' in key_types
            assert 'SHARED' in key_types
            
        finally:
            os.unlink(temp_filepath)

    @pytest.mark.integration
    def test_workflow_with_controller_sync(self):
        """Test workflow including controller sync entries."""
        log_content = """2024-01-15T10:30:45.123+0000 SiteId: 101  INFO 26 [https-jsse-nio-9500-exec-5] c.e.q.k.k.w.KeyPoolController            : Handling qnl db sync with remote site 102
2024-01-15T10:30:46.123+0000 SiteId: 101  INFO 26 [https-jsse-nio-9500-exec-7] c.e.q.k.k.w.KeyPoolController            : Handling qnl db sync with remote site 103
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(log_content)
            temp_filepath = f.name
        
        try:
            mock_db = MagicMock()
            mock_db.insert_controller_sync.return_value = True
            mock_db.mark_file_processed.return_value = True
            
            from src.local.log_processor.parser import LogParser
            parser = LogParser(mock_db)
            
            stats = parser.process_log_file(temp_filepath)
            
            assert stats['controller_syncs'] == 2
            assert mock_db.insert_controller_sync.call_count == 2
            
        finally:
            os.unlink(temp_filepath)

    @pytest.mark.integration
    def test_api_error_recovery(self):
        """Test workflow handles API errors gracefully."""
        with patch('src.local.log_processor.downloader.config') as mock_config:
            mock_config.DOWNLOAD_DIR = '/tmp/test_logs'
            mock_config.PROCESSED_FILES_LOG = '/tmp/test_logs/processed.txt'
            mock_config.VM2_API_URL = 'http://test:8080'
            
            with patch('os.path.exists', return_value=False):
                with patch('src.local.log_processor.downloader.requests.get') as mock_get:
                    mock_get.side_effect = [
                        requests.exceptions.RequestException("Network error"),
                        MagicMock(status_code=200, json=lambda: {'count': 0, 'files': []})
                    ]
                    
                    from src.local.log_processor.downloader import LogDownloader
                    downloader = LogDownloader()
                    
                    result1 = downloader.get_available_logs()
                    assert result1 == []
                    
                    result2 = downloader.get_available_logs()
                    assert result2 == []

    @pytest.mark.integration
    def test_database_error_handling(self):
        """Test workflow handles database errors gracefully."""
        log_content = """2024-01-15T10:30:45.123+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-3] c.e.q.k.k.KeyPoolServiceImpl             : createKey: KeyPoolService successfully created key with identity = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', sequence number 999, and KeyPool {Source site identity = '102', Destination site identity = '101', and KeyPoolType name = 'PUBLIC'}
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(log_content)
            temp_filepath = f.name
        
        try:
            mock_db = MagicMock()
            mock_db.insert_key_creation.return_value = False
            mock_db.mark_file_processed.return_value = True
            
            from src.local.log_processor.parser import LogParser
            parser = LogParser(mock_db)
            
            stats = parser.process_log_file(temp_filepath)
            
            assert stats is not None
            assert stats['db_errors'] == 1
            
        finally:
            os.unlink(temp_filepath)

    @pytest.mark.integration
    def test_empty_log_file(self):
        """Test workflow with empty log file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("")
            temp_filepath = f.name
        
        try:
            mock_db = MagicMock()
            mock_db.mark_file_processed.return_value = True
            
            from src.local.log_processor.parser import LogParser
            parser = LogParser(mock_db)
            
            stats = parser.process_log_file(temp_filepath)
            
            assert stats is not None
            assert stats['total_lines'] == 0
            assert stats['key_creations'] == 0
            
        finally:
            os.unlink(temp_filepath)

    @pytest.mark.integration
    def test_mixed_valid_invalid_entries(self):
        """Test workflow with mix of valid and invalid log entries."""
        log_content = """2024-01-15T10:30:45.123+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-3] c.e.q.k.k.KeyPoolServiceImpl             : createKey: KeyPoolService successfully created key with identity = 'abcdef01-2345-6789-abcd-ef0123456789', sequence number 1001, and KeyPool {Source site identity = '102', Destination site identity = '101', and KeyPoolType name = 'PUBLIC'}
This is an invalid log line that should be skipped
Another invalid line
2024-01-15T10:30:46.456+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-5] c.e.q.k.k.KeySyncServiceImpl             : METRIC_KEY_SYNC_LATENCY MS=100
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(log_content)
            temp_filepath = f.name
        
        try:
            mock_db = MagicMock()
            mock_db.insert_key_creation.return_value = True
            mock_db.insert_sync_latency.return_value = True
            mock_db.mark_file_processed.return_value = True
            
            from src.local.log_processor.parser import LogParser
            parser = LogParser(mock_db)
            
            stats = parser.process_log_file(temp_filepath)
            
            assert stats['total_lines'] == 4
            assert stats['key_creations'] == 1
            assert stats['sync_latency'] == 1
            
        finally:
            os.unlink(temp_filepath)
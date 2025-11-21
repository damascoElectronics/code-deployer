"""Integration tests for log_processor workflow.

Tests complete workflow from downloading to database storage.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os


@pytest.mark.integration
class TestLogProcessorIntegration:
    """Integration tests for complete log processing workflow."""

    @patch('mysql.connector.connect')
    @patch('requests.get')
    def test_complete_workflow_mock(self, mock_get, mock_connect, tmp_path):
        """Test complete workflow with mocked dependencies."""
        from src.local.log_processor.database import DatabaseManager
        from src.local.log_processor.downloader import LogDownloader
        from src.local.log_processor.parser import LogParser
        
        # Setup mock MySQL
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn
        
        # Setup mock HTTP responses
        def mock_api_response(url, **kwargs):
            response = Mock()
            if '/logs' in url and url.endswith('/logs'):
                response.json.return_value = {
                    'count': 1,
                    'files': [{'filename': 'test.log'}]
                }
            elif 'test.log' in url:
                log_content = (
                    "2024-01-01T10:00:00.000000+0000 SiteId: 101  INFO 26 "
                    "[quartzScheduler_Worker-1] c.e.q.k.k.KeyPoolServiceImpl : "
                    "createKey: KeyPoolService successfully created key with identity = "
                    "'550e8400-e29b-41d4-a716-446655440000', sequence number 12345, and KeyPool "
                    "{Source site identity = '101', Destination site identity = '102', "
                    "and KeyPoolType name = 'PUBLIC'}\n"
                )
                response.content = log_content.encode('utf-8')
            else:
                response.status_code = 200
            return response
        
        mock_get.side_effect = mock_api_response
        
        # Patch config paths
        with patch('src.local.log_processor.config.DOWNLOAD_DIR', str(tmp_path)):
            with patch('src.local.log_processor.config.PROCESSED_FILES_LOG', str(tmp_path / 'processed.txt')):
                # Initialize components
                db_manager = DatabaseManager()
                downloader = LogDownloader()
                parser = LogParser(db_manager)
                
                # Step 1: Get new logs
                new_logs = downloader.get_new_logs()
                assert len(new_logs) == 1
                
                # Step 2: Download log
                filepath, size = downloader.download_log_file('test.log')
                assert filepath is not None
                assert os.path.exists(filepath)
                
                # Step 3: Parse and store
                stats = parser.process_log_file(filepath)
                assert stats is not None
                assert stats['key_creations'] == 1
                
                # Step 4: Mark as processed
                downloader.mark_as_processed('test.log')
                assert 'test.log' in downloader.processed_files

    @patch('mysql.connector.connect')
    @patch('requests.get')
    def test_workflow_with_multiple_log_types(self, mock_get, mock_connect, tmp_path):
        """Test workflow with multiple log entry types."""
        from src.local.log_processor.database import DatabaseManager
        from src.local.log_processor.downloader import LogDownloader
        from src.local.log_processor.parser import LogParser
        
        # Setup mock MySQL
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn
        
        # Multi-line log content
        log_content = """2024-01-01T10:00:00.000000+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-1] c.e.q.k.k.KeyPoolServiceImpl : createKey: KeyPoolService successfully created key with identity = '550e8400-e29b-41d4-a716-446655440000', sequence number 12345, and KeyPool {Source site identity = '101', Destination site identity = '102', and KeyPoolType name = 'PUBLIC'}
2024-01-01T10:00:01.000000+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-1] c.e.q.k.k.KeySyncServiceImpl : METRIC_KEY_SYNC_LATENCY MS=150
2024-01-01T10:00:02.000000+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-1] c.e.q.k.k.KeySyncServiceImpl : METRIC_RECEIVED_PUBLIC_KEY_COUNT BITS=12800 KEYS=50
2024-01-01T10:00:03.000000+0000 SiteId: 101  INFO 26 [https-jsse-nio-9500-exec-1] c.e.q.k.k.w.KeyPoolController : Handling qnl db sync with remote site 102
"""
        
        def mock_api_response(url, **kwargs):
            response = Mock()
            if '/logs' in url and url.endswith('/logs'):
                response.json.return_value = {
                    'count': 1,
                    'files': [{'filename': 'multi.log'}]
                }
            elif 'multi.log' in url:
                response.content = log_content.encode('utf-8')
            else:
                response.status_code = 200
            return response
        
        mock_get.side_effect = mock_api_response
        
        with patch('src.local.log_processor.config.DOWNLOAD_DIR', str(tmp_path)):
            with patch('src.local.log_processor.config.PROCESSED_FILES_LOG', str(tmp_path / 'processed.txt')):
                db_manager = DatabaseManager()
                downloader = LogDownloader()
                parser = LogParser(db_manager)
                
                # Download and process
                filepath, _ = downloader.download_log_file('multi.log')
                stats = parser.process_log_file(filepath)
                
                # Verify all log types processed
                assert stats['key_creations'] == 1
                assert stats['sync_latency'] == 1
                assert stats['key_counts'] == 1
                assert stats['controller_syncs'] == 1

    @patch('mysql.connector.connect')
    def test_database_error_handling(self, mock_connect, tmp_path):
        """Test handling of database errors during processing."""
        from src.local.log_processor.database import DatabaseManager
        from src.local.log_processor.parser import LogParser
        
        # Setup mock MySQL with errors
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("DB Error")
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn
        
        # Create test log file
        log_file = tmp_path / "error_test.log"
        log_content = (
            "2024-01-01T10:00:00.000000+0000 SiteId: 101  INFO 26 "
            "[quartzScheduler_Worker-1] c.e.q.k.k.KeyPoolServiceImpl : "
            "createKey: KeyPoolService successfully created key with identity = "
            "'550e8400-e29b-41d4-a716-446655440000', sequence number 12345, and KeyPool "
            "{Source site identity = '101', Destination site identity = '102', "
            "and KeyPoolType name = 'PUBLIC'}\n"
        )
        log_file.write_text(log_content)
        
        db_manager = DatabaseManager()
        parser = LogParser(db_manager)
        
        # Process file - should handle DB errors gracefully
        stats = parser.process_log_file(str(log_file))
        
        assert stats is not None
        assert stats['db_errors'] > 0

    @patch('mysql.connector.connect')
    @patch('requests.get')
    def test_no_new_logs_scenario(self, mock_get, mock_connect):
        """Test scenario when no new logs are available."""
        from src.local.log_processor.database import DatabaseManager
        from src.local.log_processor.downloader import LogDownloader
        
        # Setup mocks
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'count': 0,
            'files': []
        }
        mock_get.return_value = mock_response
        
        db_manager = DatabaseManager()
        downloader = LogDownloader()
        
        # Get new logs - should be empty
        new_logs = downloader.get_new_logs()
        
        assert new_logs == []

    @patch('mysql.connector.connect')
    @patch('requests.get')
    def test_skip_already_processed_logs(self, mock_get, mock_connect, tmp_path):
        """Test that already processed logs are skipped."""
        from src.local.log_processor.downloader import LogDownloader
        
        # Setup mocks
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'count': 2,
            'files': [
                {'filename': 'old.log'},
                {'filename': 'new.log'}
            ]
        }
        mock_get.return_value = mock_response
        
        # Create processed files log
        processed_log = tmp_path / "processed.txt"
        processed_log.write_text("old.log\n")
        
        with patch('src.local.log_processor.config.PROCESSED_FILES_LOG', str(processed_log)):
            downloader = LogDownloader()
            new_logs = downloader.get_new_logs()
            
            # Should only return unprocessed log
            assert len(new_logs) == 1
            assert new_logs[0]['filename'] == 'new.log'
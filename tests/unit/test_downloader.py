"""Unit tests for downloader.py module from log_processor.

Tests log file downloading from remote API.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import os


class TestLogDownloader:
    """Unit tests for LogDownloader class."""

    @pytest.mark.unit
    def test_init_creates_directory(self, tmp_path):
        """Test that initialization creates download directory."""
        from src.local.log_processor.downloader import LogDownloader
        
        with patch('src.local.log_processor.config.DOWNLOAD_DIR', str(tmp_path / 'downloads')):
            with patch('src.local.log_processor.config.PROCESSED_FILES_LOG', str(tmp_path / 'processed.txt')):
                downloader = LogDownloader()
                
                assert downloader.processed_files == set()

    @pytest.mark.unit
    def test_load_processed_files_existing(self, tmp_path):
        """Test loading existing processed files list."""
        from src.local.log_processor.downloader import LogDownloader
        
        processed_log = tmp_path / "processed.txt"
        processed_log.write_text("file1.log\nfile2.log\n")
        
        with patch('src.local.log_processor.config.PROCESSED_FILES_LOG', str(processed_log)):
            downloader = LogDownloader()
            
            assert 'file1.log' in downloader.processed_files
            assert 'file2.log' in downloader.processed_files
            assert len(downloader.processed_files) == 2

    @pytest.mark.unit
    def test_mark_as_processed(self, tmp_path):
        """Test marking file as processed."""
        from src.local.log_processor.downloader import LogDownloader
        
        processed_log = tmp_path / "processed.txt"
        
        with patch('src.local.log_processor.config.DOWNLOAD_DIR', str(tmp_path)):
            with patch('src.local.log_processor.config.PROCESSED_FILES_LOG', str(processed_log)):
                downloader = LogDownloader()
                downloader.mark_as_processed('test.log')
                
                assert 'test.log' in downloader.processed_files
                assert processed_log.exists()
                content = processed_log.read_text()
                assert 'test.log' in content

    @pytest.mark.unit
    @patch('requests.get')
    def test_check_api_health_success(self, mock_get):
        """Test successful API health check."""
        from src.local.log_processor.downloader import LogDownloader
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        downloader = LogDownloader()
        result = downloader.check_api_health()
        
        assert result is True

    @pytest.mark.unit
    @patch('requests.get')
    def test_check_api_health_failure(self, mock_get):
        """Test API health check failure."""
        from src.local.log_processor.downloader import LogDownloader
        
        mock_get.side_effect = Exception("Connection error")
        
        downloader = LogDownloader()
        result = downloader.check_api_health()
        
        assert result is False

    @pytest.mark.unit
    @patch('requests.get')
    def test_get_available_logs_success(self, mock_get):
        """Test getting available logs from API."""
        from src.local.log_processor.downloader import LogDownloader
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'count': 2,
            'files': [
                {'filename': 'log1.log'},
                {'filename': 'log2.log'}
            ]
        }
        mock_get.return_value = mock_response
        
        downloader = LogDownloader()
        logs = downloader.get_available_logs()
        
        assert len(logs) == 2
        assert logs[0]['filename'] == 'log1.log'

    @pytest.mark.unit
    @patch('requests.get')
    def test_get_available_logs_error(self, mock_get):
        """Test getting available logs with API error."""
        from src.local.log_processor.downloader import LogDownloader
        
        mock_get.side_effect = Exception("API error")
        
        downloader = LogDownloader()
        logs = downloader.get_available_logs()
        
        assert logs == []

    @pytest.mark.unit
    @patch('requests.get')
    def test_get_new_logs_filters_processed(self, mock_get):
        """Test that new logs excludes already processed files."""
        from src.local.log_processor.downloader import LogDownloader
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'count': 3,
            'files': [
                {'filename': 'log1.log'},
                {'filename': 'log2.log'},
                {'filename': 'log3.log'}
            ]
        }
        mock_get.return_value = mock_response
        
        downloader = LogDownloader()
        downloader.processed_files = {'log2.log'}
        
        new_logs = downloader.get_new_logs()
        
        assert len(new_logs) == 2
        assert any(log['filename'] == 'log1.log' for log in new_logs)
        assert any(log['filename'] == 'log3.log' for log in new_logs)
        assert not any(log['filename'] == 'log2.log' for log in new_logs)

    @pytest.mark.unit
    @patch('requests.get')
    def test_download_log_file_success(self, mock_get, tmp_path):
        """Test successful log file download."""
        from src.local.log_processor.downloader import LogDownloader
        
        mock_response = Mock()
        mock_response.content = b"log content"
        mock_get.return_value = mock_response
        
        with patch('src.local.log_processor.config.DOWNLOAD_DIR', str(tmp_path)):
            downloader = LogDownloader()
            filepath, size = downloader.download_log_file('test.log')
            
            assert filepath == str(tmp_path / 'test.log')
            assert size == len(b"log content")
            assert os.path.exists(filepath)

    @pytest.mark.unit
    @patch('requests.get')
    def test_download_log_file_error(self, mock_get):
        """Test log file download with error."""
        from src.local.log_processor.downloader import LogDownloader
        
        mock_get.side_effect = Exception("Download error")
        
        downloader = LogDownloader()
        filepath, size = downloader.download_log_file('test.log')
        
        assert filepath is None
        assert size == 0

    @pytest.mark.unit
    @patch('requests.get')
    def test_get_new_logs_empty_response(self, mock_get):
        """Test getting new logs when no logs available."""
        from src.local.log_processor.downloader import LogDownloader
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'count': 0,
            'files': []
        }
        mock_get.return_value = mock_response
        
        downloader = LogDownloader()
        new_logs = downloader.get_new_logs()
        
        assert new_logs == []
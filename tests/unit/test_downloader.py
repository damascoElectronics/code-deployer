"""Unit tests for downloader.py module from log_processor.

Tests file download operations with mocked HTTP requests.
"""

import os
import pytest
import requests
from unittest.mock import Mock, MagicMock, patch, mock_open


class TestLogDownloader:
    """Unit tests for LogDownloader class."""

    @pytest.mark.unit
    def test_init_creates_directory(self):
        """Test that initialization sets up downloader correctly."""
        with patch('src.local.log_processor.downloader.config') as mock_config:
            mock_config.DOWNLOAD_DIR = '/tmp/test_logs'
            mock_config.PROCESSED_FILES_LOG = '/tmp/test_logs/processed.txt'
            mock_config.VM2_API_URL = 'http://test:8080'

            with patch('os.path.exists', return_value=False):
                from src.local.log_processor.downloader import LogDownloader
                downloader = LogDownloader()

                assert downloader.api_url == 'http://test:8080'
                assert downloader.download_dir == '/tmp/test_logs'

    @pytest.mark.unit
    def test_load_processed_files_existing(self):
        """Test loading existing processed files list."""
        with patch('src.local.log_processor.downloader.config') as mock_config:
            mock_config.DOWNLOAD_DIR = '/tmp'
            mock_config.PROCESSED_FILES_LOG = '/tmp/processed.txt'
            mock_config.VM2_API_URL = 'http://test:8080'

            mock_file_content = "file1.log\nfile2.log\nfile3.log\n"
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=mock_file_content)):
                    from src.local.log_processor.downloader import LogDownloader
                    downloader = LogDownloader()

                    assert 'file1.log' in downloader.processed_files
                    assert 'file2.log' in downloader.processed_files
                    assert len(downloader.processed_files) == 3

    @pytest.mark.unit
    def test_mark_as_processed(self):
        """Test marking a file as processed."""
        with patch('src.local.log_processor.downloader.config') as mock_config:
            mock_config.DOWNLOAD_DIR = '/tmp'
            mock_config.PROCESSED_FILES_LOG = '/tmp/processed.txt'
            mock_config.VM2_API_URL = 'http://test:8080'

            with patch('os.path.exists', return_value=False):
                with patch('os.makedirs'):
                    m = mock_open()
                    with patch('builtins.open', m):
                        from src.local.log_processor.downloader import LogDownloader
                        downloader = LogDownloader()
                        downloader.mark_as_processed('new_file.log')

                        assert 'new_file.log' in downloader.processed_files

    @pytest.mark.unit
    def test_check_api_health_success(self):
        """Test successful API health check."""
        with patch('src.local.log_processor.downloader.config') as mock_config:
            mock_config.DOWNLOAD_DIR = '/tmp'
            mock_config.PROCESSED_FILES_LOG = '/tmp/processed.txt'
            mock_config.VM2_API_URL = 'http://test:8080'

            with patch('os.path.exists', return_value=False):
                with patch('src.local.log_processor.downloader.requests.get') as mock_get:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_get.return_value = mock_response

                    from src.local.log_processor.downloader import LogDownloader
                    downloader = LogDownloader()
                    result = downloader.check_api_health()

                    assert result is True

    @pytest.mark.unit
    def test_check_api_health_failure(self):
        """Test API health check failure."""
        with patch('src.local.log_processor.downloader.config') as mock_config:
            mock_config.DOWNLOAD_DIR = '/tmp'
            mock_config.PROCESSED_FILES_LOG = '/tmp/processed.txt'
            mock_config.VM2_API_URL = 'http://test:8080'

            with patch('os.path.exists', return_value=False):
                with patch('src.local.log_processor.downloader.requests.get') as mock_get:
                    # Use RequestException instead of generic Exception
                    mock_get.side_effect = requests.exceptions.RequestException("Connection error")

                    from src.local.log_processor.downloader import LogDownloader
                    downloader = LogDownloader()
                    result = downloader.check_api_health()

                    assert result is False

    @pytest.mark.unit
    def test_get_available_logs_success(self):
        """Test getting available logs successfully."""
        with patch('src.local.log_processor.downloader.config') as mock_config:
            mock_config.DOWNLOAD_DIR = '/tmp'
            mock_config.PROCESSED_FILES_LOG = '/tmp/processed.txt'
            mock_config.VM2_API_URL = 'http://test:8080'

            with patch('os.path.exists', return_value=False):
                with patch('src.local.log_processor.downloader.requests.get') as mock_get:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        'count': 2,
                        'files': [
                            {'filename': 'log1.log'},
                            {'filename': 'log2.log'}
                        ]
                    }
                    mock_get.return_value = mock_response

                    from src.local.log_processor.downloader import LogDownloader
                    downloader = LogDownloader()
                    logs = downloader.get_available_logs()

                    assert len(logs) == 2
                    assert logs[0]['filename'] == 'log1.log'

    @pytest.mark.unit
    def test_get_available_logs_error(self):
        """Test getting available logs with API error."""
        with patch('src.local.log_processor.downloader.config') as mock_config:
            mock_config.DOWNLOAD_DIR = '/tmp'
            mock_config.PROCESSED_FILES_LOG = '/tmp/processed.txt'
            mock_config.VM2_API_URL = 'http://test:8080'

            with patch('os.path.exists', return_value=False):
                with patch('src.local.log_processor.downloader.requests.get') as mock_get:
                    # Use RequestException instead of generic Exception
                    mock_get.side_effect = requests.exceptions.RequestException("API error")

                    from src.local.log_processor.downloader import LogDownloader
                    downloader = LogDownloader()
                    logs = downloader.get_available_logs()

                    assert logs == []

    @pytest.mark.unit
    def test_get_new_logs_filters_processed(self):
        """Test that get_new_logs filters out processed files."""
        with patch('src.local.log_processor.downloader.config') as mock_config:
            mock_config.DOWNLOAD_DIR = '/tmp'
            mock_config.PROCESSED_FILES_LOG = '/tmp/processed.txt'
            mock_config.VM2_API_URL = 'http://test:8080'

            mock_file_content = "log1.log\n"
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=mock_file_content)):
                    with patch('src.local.log_processor.downloader.requests.get') as mock_get:
                        mock_response = MagicMock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {
                            'count': 2,
                            'files': [
                                {'filename': 'log1.log'},
                                {'filename': 'log2.log'}
                            ]
                        }
                        mock_get.return_value = mock_response

                        from src.local.log_processor.downloader import LogDownloader
                        downloader = LogDownloader()
                        new_logs = downloader.get_new_logs()

                        # log1.log should be filtered out
                        assert len(new_logs) == 1
                        assert new_logs[0]['filename'] == 'log2.log'

    @pytest.mark.unit
    def test_download_log_file_success(self):
        """Test successful log file download."""
        with patch('src.local.log_processor.downloader.config') as mock_config:
            mock_config.DOWNLOAD_DIR = '/tmp/logs'
            mock_config.PROCESSED_FILES_LOG = '/tmp/logs/processed.txt'
            mock_config.VM2_API_URL = 'http://test:8080'

            with patch('os.path.exists', return_value=False):
                with patch('os.makedirs'):
                    with patch('src.local.log_processor.downloader.requests.get') as mock_get:
                        mock_response = MagicMock()
                        mock_response.content = b'log content here'
                        mock_get.return_value = mock_response

                        m = mock_open()
                        with patch('builtins.open', m):
                            from src.local.log_processor.downloader import LogDownloader
                            downloader = LogDownloader()
                            filepath, size = downloader.download_log_file('test.log')

                            assert filepath == '/tmp/logs/test.log'
                            assert size == len(b'log content here')

    @pytest.mark.unit
    def test_download_log_file_error(self):
        """Test log file download error."""
        with patch('src.local.log_processor.downloader.config') as mock_config:
            mock_config.DOWNLOAD_DIR = '/tmp/logs'
            mock_config.PROCESSED_FILES_LOG = '/tmp/logs/processed.txt'
            mock_config.VM2_API_URL = 'http://test:8080'

            with patch('os.path.exists', return_value=False):
                with patch('src.local.log_processor.downloader.requests.get') as mock_get:
                    # Use RequestException instead of generic Exception
                    mock_get.side_effect = requests.exceptions.RequestException("Download error")

                    from src.local.log_processor.downloader import LogDownloader
                    downloader = LogDownloader()
                    filepath, size = downloader.download_log_file('test.log')

                    assert filepath is None
                    assert size == 0

    @pytest.mark.unit
    def test_get_new_logs_empty_response(self):
        """Test get_new_logs with empty API response."""
        with patch('src.local.log_processor.downloader.config') as mock_config:
            mock_config.DOWNLOAD_DIR = '/tmp'
            mock_config.PROCESSED_FILES_LOG = '/tmp/processed.txt'
            mock_config.VM2_API_URL = 'http://test:8080'

            with patch('os.path.exists', return_value=False):
                with patch('src.local.log_processor.downloader.requests.get') as mock_get:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        'count': 0,
                        'files': []
                    }
                    mock_get.return_value = mock_response

                    from src.local.log_processor.downloader import LogDownloader
                    downloader = LogDownloader()
                    new_logs = downloader.get_new_logs()

                    assert new_logs == []
"""Global pytest configuration - Mock config module."""

import sys
import pytest
from unittest.mock import MagicMock


@pytest.fixture(scope="session", autouse=True)
def mock_config_module():
    """Mock config module for all tests."""
    config_mock = MagicMock()
    
    # MySQL config
    config_mock.MYSQL_HOST = '127.0.0.1'
    config_mock.MYSQL_PORT = 3306
    config_mock.MYSQL_USER = 'test_user'
    config_mock.MYSQL_PASSWORD = 'test_pass'
    config_mock.MYSQL_DATABASE = 'test_db'
    
    # Log processor config
    config_mock.VM2_HOST = '192.168.0.11'
    config_mock.VM2_PORT = 8080
    config_mock.VM2_API_URL = 'http://192.168.0.11:8080'
    config_mock.POLL_INTERVAL = 30
    config_mock.DOWNLOAD_DIR = '/tmp/test_downloads'
    config_mock.PROCESSED_FILES_LOG = '/tmp/.processed_files.txt'
    config_mock.LOG_LEVEL = 'INFO'
    
    # OGS config
    config_mock.OGS_PROVIDER_URL = 'http://ogs-data-generator:5000'
    config_mock.FETCH_INTERVAL = 10
    config_mock.FETCH_TIMEOUT = 5
    config_mock.DATA_DIR = '/tmp/test_data'
    config_mock.HTTP_SERVER_PORT = 8080
    
    # Inject into sys.modules
    sys.modules['config'] = config_mock
    
    yield config_mock
    
    # Cleanup
    if 'config' in sys.modules:
        del sys.modules['config']
"""Global pytest configuration and fixtures.

This module contains shared fixtures and configuration for all tests
in the project.
"""

import os
import sys
import tempfile
import pytest
from typing import Generator


# Register custom markers to avoid warnings
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "skip_coverage: Skip coverage for this test")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add unit marker to tests in unit directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to tests in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to tests that take longer
        if "performance" in item.name or "large_file" in item.name:
            item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session")
def test_data_dir() -> str:
    """Fixture that provides the path to test data directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "data")


@pytest.fixture
def temp_directory() -> Generator[str, None, None]:
    """Fixture that provides a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_text_file(temp_directory: str) -> str:
    """Fixture that creates a sample text file for testing."""
    file_path = os.path.join(temp_directory, "sample.txt")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("Sample line 1\n")
        f.write("Sample line 2\n")
        f.write("\n")  # Empty line
        f.write("Sample line 4\n")
        f.write("Sample line 5\n")
    
    return file_path


@pytest.fixture
def sample_log_content() -> str:
    """Fixture that provides sample KeyPool log content."""
    return """2024-01-15T10:30:45.123+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-3] c.e.q.k.k.KeyPoolServiceImpl             : createKey: KeyPoolService successfully created key with identity = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', sequence number 477001, and KeyPool {Source site identity = '102', Destination site identity = '101', and KeyPoolType name = 'PUBLIC'}
2024-01-15T10:30:46.456+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-5] c.e.q.k.k.KeySyncServiceImpl             : METRIC_KEY_SYNC_LATENCY MS=85
2024-01-15T10:30:47.789+0000 SiteId: 101  INFO 26 [quartzScheduler_Worker-7] c.e.q.k.k.KeySyncServiceImpl             : METRIC_RECEIVED_PUBLIC_KEY_COUNT BITS=2560 KEYS=10
"""


@pytest.fixture
def mock_db_manager():
    """Fixture that provides a mock database manager."""
    from unittest.mock import MagicMock
    
    mock_db = MagicMock()
    mock_db.is_connected.return_value = True
    mock_db.insert_key_creation.return_value = True
    mock_db.insert_sync_latency.return_value = True
    mock_db.insert_key_count.return_value = True
    mock_db.insert_controller_sync.return_value = True
    mock_db.mark_file_processed.return_value = True
    
    return mock_db
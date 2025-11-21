"""Global pytest configuration and fixtures.

This module contains shared fixtures and configuration for all tests
in the project.
"""

import os
import tempfile
import pytest
from typing import Generator


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
def large_text_file(temp_directory: str) -> str:
    """Fixture that creates a large text file for performance testing."""
    file_path = os.path.join(temp_directory, "large_sample.txt")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for i in range(1000):
            f.write(f"Large file line {i}\n")
    
    return file_path


@pytest.fixture
def empty_text_file(temp_directory: str) -> str:
    """Fixture that creates an empty text file for testing."""
    file_path = os.path.join(temp_directory, "empty.txt")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        pass  # Create empty file
    
    return file_path


@pytest.fixture
def csv_test_file(temp_directory: str) -> str:
    """Fixture that creates a CSV file for testing."""
    file_path = os.path.join(temp_directory, "test.csv")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("name,age,city\n")
        f.write("John,25,New York\n")
        f.write("Jane,30,Los Angeles\n")
        f.write("Bob,35,Chicago\n")
    
    return file_path


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (deselect with '-m \"not unit\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "skip_coverage: skip coverage for this test"
    )


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
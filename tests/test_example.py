"""Main tests for the example module.

This module contains general tests for the DataProcessor class,
mixing both unit and integration style tests.
"""

import os
import tempfile
import pytest
from unittest.mock import patch, mock_open
from src.example import DataProcessor


class TestDataProcessor:
    """Test suite for DataProcessor class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_data.txt")
        
        # Create a test file
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write("line1\n")
            f.write("line2\n")
            f.write("\n")  # Empty line
            f.write("line4\n")

    def teardown_method(self):
        """Clean up after each test method."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        os.rmdir(self.temp_dir)

    def test_init_valid_parameters(self):
        """Test DataProcessor initialization with valid parameters."""
        processor = DataProcessor("test.txt", max_items=50)
        
        assert processor.data_source == "test.txt"
        assert processor.max_items == 50
        assert processor._processed_count == 0

    def test_init_default_max_items(self):
        """Test DataProcessor initialization with default max_items."""
        processor = DataProcessor("test.txt")
        
        assert processor.data_source == "test.txt"
        assert processor.max_items == 100

    def test_init_empty_data_source(self):
        """Test DataProcessor initialization with empty data_source raises ValueError."""
        with pytest.raises(ValueError, match="data_source cannot be empty"):
            DataProcessor("")

    def test_get_processed_count_initial(self):
        """Test get_processed_count returns 0 initially."""
        processor = DataProcessor("test.txt")
        assert processor.get_processed_count() == 0

    def test_process_data_file_exists(self):
        """Test process_data with an existing file."""
        processor = DataProcessor(self.test_file, max_items=10)
        
        result = processor.process_data(filter_empty=True)
        
        assert len(result) == 3  # line1, line2, line4 (empty line filtered)
        assert result == ["line1", "line2", "line4"]
        assert processor.get_processed_count() == 3

    def test_process_data_without_filter_empty(self):
        """Test process_data without filtering empty lines."""
        processor = DataProcessor(self.test_file, max_items=10)
        
        result = processor.process_data(filter_empty=False)
        
        assert len(result) == 4  # All lines including empty
        assert result == ["line1", "line2", "", "line4"]
        assert processor.get_processed_count() == 4

    def test_process_data_max_items_limit(self):
        """Test process_data respects max_items limit."""
        processor = DataProcessor(self.test_file, max_items=2)
        
        result = processor.process_data(filter_empty=True)
        
        assert len(result) == 2  # Limited by max_items
        assert result == ["line1", "line2"]
        assert processor.get_processed_count() == 2

    def test_process_data_file_not_found(self):
        """Test process_data raises FileNotFoundError for non-existent file."""
        processor = DataProcessor("non_existent_file.txt")
        
        with pytest.raises(FileNotFoundError, match="File not found: non_existent_file.txt"):
            processor.process_data()

    @patch("builtins.open", mock_open())
    @patch("os.path.exists", return_value=True)
    def test_process_data_io_error(self, mock_exists):
        """Test process_data handles IOError properly."""
        # Configure mock to raise IOError
        with patch("builtins.open", side_effect=IOError("Mocked IO error")):
            processor = DataProcessor("test.txt")
            
            with pytest.raises(IOError, match="Error reading file: Mocked IO error"):
                processor.process_data()

    @pytest.mark.parametrize("filename,extensions,expected", [
        ("test.txt", None, True),
        ("test.csv", None, True),
        ("test.pdf", None, False),
        ("test.TXT", None, True),  # Case insensitive
        ("test.json", [".json", ".xml"], True),
        ("test.txt", [".json", ".xml"], False),
        ("file_without_extension", None, False),
    ])
    def test_validate_file_extension(self, filename, extensions, expected):
        """Test validate_file_extension with various inputs."""
        result = DataProcessor.validate_file_extension(filename, extensions)
        assert result == expected

    def test_validate_file_extension_default_extensions(self):
        """Test validate_file_extension uses default extensions when None provided."""
        assert DataProcessor.validate_file_extension("test.txt") is True
        assert DataProcessor.validate_file_extension("test.csv") is True
        assert DataProcessor.validate_file_extension("test.pdf") is False

    def test_multiple_process_data_calls(self):
        """Test multiple calls to process_data accumulate processed_count."""
        processor = DataProcessor(self.test_file, max_items=2)
        
        # First call
        result1 = processor.process_data(filter_empty=True)
        assert len(result1) == 2
        assert processor.get_processed_count() == 2
        
        # Second call should continue counting
        result2 = processor.process_data(filter_empty=True)
        assert len(result2) == 2
        assert processor.get_processed_count() == 4  # Accumulated

    def test_empty_file_processing(self):
        """Test processing an empty file."""
        empty_file = os.path.join(self.temp_dir, "empty.txt")
        with open(empty_file, 'w', encoding='utf-8') as f:
            pass  # Create empty file
        
        processor = DataProcessor(empty_file)
        result = processor.process_data()
        
        assert result == []
        assert processor.get_processed_count() == 0
        
        os.remove(empty_file)

    def test_large_file_processing(self):
        """Test processing a file with many lines."""
        large_file = os.path.join(self.temp_dir, "large.txt")
        with open(large_file, 'w', encoding='utf-8') as f:
            for i in range(200):
                f.write(f"line{i}\n")
        
        processor = DataProcessor(large_file, max_items=150)
        result = processor.process_data()
        
        assert len(result) == 150  # Limited by max_items
        assert processor.get_processed_count() == 150
        
        os.remove(large_file)

    def test_file_with_special_characters(self):
        """Test processing file with special characters and Unicode."""
        special_file = os.path.join(self.temp_dir, "special.txt")
        with open(special_file, 'w', encoding='utf-8') as f:
            f.write("línea con acentos\n")
            f.write("special chars: @#$%^&*()\n")
        
        processor = DataProcessor(special_file)
        result = processor.process_data()
        
        assert len(result) == 3
        assert "línea con acentos" in result
        assert "line with émojis 🚀" in result
        assert "special chars: @#$%^&*()" in result
        
        os.remove(special_file)


# Fixture examples
@pytest.fixture
def sample_processor():
    """Fixture that provides a DataProcessor instance for testing."""
    return DataProcessor("sample.txt", max_items=10)


@pytest.fixture
def temp_file_with_data():
    """Fixture that provides a temporary file with test data."""
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, "fixture_test.txt")
    
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write("fixture line 1\n")
        f.write("fixture line 2\n")
        f.write("fixture line 3\n")
    
    yield temp_file
    
    # Cleanup
    os.remove(temp_file)
    os.rmdir(temp_dir)


def test_with_sample_processor_fixture(sample_processor):
    """Test using the sample_processor fixture."""
    assert sample_processor.data_source == "sample.txt"
    assert sample_processor.max_items == 10
    assert sample_processor.get_processed_count() == 0


def test_with_temp_file_fixture(temp_file_with_data):
    """Test using the temp_file_with_data fixture."""
    processor = DataProcessor(temp_file_with_data)
    result = processor.process_data()
    
    assert len(result) == 3
    assert all("fixture line" in line for line in result)
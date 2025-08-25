
"""Unit tests for the DataProcessor class.

This module contains isolated unit tests that test individual methods
of the DataProcessor class without external dependencies.
"""

import pytest
from unittest.mock import patch, mock_open, MagicMock
from src.example import DataProcessor


class TestDataProcessorUnit:
    """Unit tests for DataProcessor class focusing on isolated functionality."""

    @pytest.mark.unit
    def test_init_with_valid_parameters(self):
        """Test initialization with valid parameters."""
        processor = DataProcessor("test.txt", max_items=50)
        
        assert processor.data_source == "test.txt"
        assert processor.max_items == 50
        assert processor._processed_count == 0

    @pytest.mark.unit
    def test_init_with_default_max_items(self):
        """Test initialization with default max_items parameter."""
        processor = DataProcessor("test.txt")
        
        assert processor.data_source == "test.txt"
        assert processor.max_items == 100
        assert processor._processed_count == 0

    @pytest.mark.unit
    def test_init_empty_data_source_raises_value_error(self):
        """Test that empty data_source raises ValueError."""
        with pytest.raises(ValueError, match="data_source cannot be empty"):
            DataProcessor("")

    @pytest.mark.unit
    def test_init_none_data_source_raises_value_error(self):
        """Test that None data_source raises ValueError."""
        with pytest.raises(ValueError, match="data_source cannot be empty"):
            DataProcessor(None)

    @pytest.mark.unit
    def test_get_processed_count_initial_state(self):
        """Test get_processed_count returns 0 in initial state."""
        processor = DataProcessor("test.txt")
        assert processor.get_processed_count() == 0

    @pytest.mark.unit
    def test_get_processed_count_after_manual_increment(self):
        """Test get_processed_count after manually incrementing counter."""
        processor = DataProcessor("test.txt")
        processor._processed_count = 5
        assert processor.get_processed_count() == 5

    @pytest.mark.unit
    @patch("os.path.exists", return_value=False)
    def test_process_data_file_not_found(self, mock_exists):
        """Test process_data raises FileNotFoundError when file doesn't exist."""
        processor = DataProcessor("nonexistent.txt")
        
        with pytest.raises(FileNotFoundError, match="File not found: nonexistent.txt"):
            processor.process_data()
        
        mock_exists.assert_called_once_with("nonexistent.txt")

    @pytest.mark.unit
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", side_effect=IOError("Permission denied"))
    def test_process_data_io_error(self, mock_open_func, mock_exists):
        """Test process_data handles IOError properly."""
        processor = DataProcessor("test.txt")
        
        with pytest.raises(IOError, match="Error reading file: Permission denied"):
            processor.process_data()

    @pytest.mark.unit
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", mock_open(read_data="line1\nline2\nline3\n"))
    def test_process_data_basic_functionality(self, mock_exists):
        """Test basic process_data functionality with mocked file."""
        processor = DataProcessor("test.txt", max_items=10)
        
        result = processor.process_data(filter_empty=True)
        
        assert result == ["line1", "line2", "line3"]
        assert processor.get_processed_count() == 3

    @pytest.mark.unit
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", mock_open(read_data="line1\n\nline3\n"))
    def test_process_data_filter_empty_true(self, mock_exists):
        """Test process_data with filter_empty=True removes empty lines."""
        processor = DataProcessor("test.txt")
        
        result = processor.process_data(filter_empty=True)
        
        assert result == ["line1", "line3"]
        assert processor.get_processed_count() == 2

    @pytest.mark.unit
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", mock_open(read_data="line1\n\nline3\n"))
    def test_process_data_filter_empty_false(self, mock_exists):
        """Test process_data with filter_empty=False keeps empty lines."""
        processor = DataProcessor("test.txt")
        
        result = processor.process_data(filter_empty=False)
        
        assert result == ["line1", "", "line3"]
        assert processor.get_processed_count() == 3

    @pytest.mark.unit
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", mock_open(read_data="line1\nline2\nline3\nline4\nline5\n"))
    def test_process_data_respects_max_items(self, mock_exists):
        """Test process_data respects max_items limit."""
        processor = DataProcessor("test.txt", max_items=3)
        
        result = processor.process_data()
        
        assert len(result) == 3
        assert result == ["line1", "line2", "line3"]
        assert processor.get_processed_count() == 3

    @pytest.mark.unit
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", mock_open(read_data=""))
    def test_process_data_empty_file(self, mock_exists):
        """Test process_data with empty file."""
        processor = DataProcessor("empty.txt")
        
        result = processor.process_data()
        
        assert result == []
        assert processor.get_processed_count() == 0

    @pytest.mark.unit
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", mock_open(read_data="line1\nline2\n"))
    def test_process_data_accumulates_count(self, mock_exists):
        """Test that multiple calls to process_data accumulate the count."""
        processor = DataProcessor("test.txt")
        
        # First call
        result1 = processor.process_data()
        assert processor.get_processed_count() == 2
        
        # Second call should add to the count
        result2 = processor.process_data()
        assert processor.get_processed_count() == 4

    @pytest.mark.unit
    @pytest.mark.parametrize("filename,extensions,expected", [
        ("test.txt", None, True),
        ("test.csv", None, True),
        ("test.TXT", None, True),  # Case insensitive
        ("test.PDF", None, False),
        ("test.json", [".json", ".xml"], True),
        ("test.txt", [".json", ".xml"], False),
        ("no_extension", None, False),
        ("file.with.multiple.dots.txt", None, True),
        ("", None, False),
    ])
    def test_validate_file_extension_parametrized(self, filename, extensions, expected):
        """Test validate_file_extension with various parameter combinations."""
        result = DataProcessor.validate_file_extension(filename, extensions)
        assert result == expected

    @pytest.mark.unit
    def test_validate_file_extension_with_none_extensions(self):
        """Test validate_file_extension when extensions parameter is None."""
        # Should use default extensions ['.txt', '.csv']
        assert DataProcessor.validate_file_extension("test.txt", None) is True
        assert DataProcessor.validate_file_extension("test.csv", None) is True
        assert DataProcessor.validate_file_extension("test.pdf", None) is False

    @pytest.mark.unit
    def test_validate_file_extension_with_empty_list(self):
        """Test validate_file_extension with empty extensions list."""
        result = DataProcessor.validate_file_extension("test.txt", [])
        assert result is False

    @pytest.mark.unit
    def test_validate_file_extension_case_sensitivity(self):
        """Test that file extension validation is case insensitive."""
        extensions = [".TXT", ".CSV"]
        
        assert DataProcessor.validate_file_extension("test.txt", extensions) is True
        assert DataProcessor.validate_file_extension("test.TXT", extensions) is True
        assert DataProcessor.validate_file_extension("test.csv", extensions) is True
        assert DataProcessor.validate_file_extension("test.CSV", extensions) is True

    @pytest.mark.unit
    def test_data_processor_properties_immutable(self):
        """Test that DataProcessor properties are set correctly and don't change unexpectedly."""
        original_source = "original.txt"
        original_max = 42
        
        processor = DataProcessor(original_source, original_max)
        
        # Properties should remain unchanged
        assert processor.data_source == original_source
        assert processor.max_items == original_max
        
        # Even after accessing them multiple times
        _ = processor.data_source
        _ = processor.max_items
        
        assert processor.data_source == original_source
        assert processor.max_items == original_max

    @pytest.mark.unit
    def test_private_processed_count_encapsulation(self):
        """Test that _processed_count is properly encapsulated."""
        processor = DataProcessor("test.txt")
        
        # Should only be accessible through getter method
        assert hasattr(processor, '_processed_count')
        assert processor.get_processed_count() == 0
        
        # Direct manipulation for testing purposes
        processor._processed_count = 10
        assert processor.get_processed_count() == 10

    @pytest.mark.unit
    def test_static_method_independence(self):
        """Test that static method validate_file_extension works independently."""
        # Should work without creating an instance
        result = DataProcessor.validate_file_extension("test.txt")
        assert result is True
        
        # Should work the same way through an instance
        processor = DataProcessor("dummy.txt")
        instance_result = processor.validate_file_extension("test.txt")
        assert instance_result is True
        assert result == instance_result

    @pytest.mark.unit
    @patch("os.path.exists", return_value=True)
    def test_process_data_file_encoding_handling(self, mock_exists):
        """Test that process_data handles file encoding properly."""
        # Mock file with simple ASCII content
        ascii_content = "line1\nline2\nline3\n"
        
        with patch("builtins.open", mock_open(read_data=ascii_content)):
            processor = DataProcessor("ascii_test.txt")
            result = processor.process_data()
            
            assert "line1" in result
            assert "line2" in result
            assert "line3" in result

    @pytest.mark.unit
    def test_edge_case_zero_max_items(self):
        """Test behavior when max_items is set to 0."""
        processor = DataProcessor("test.txt", max_items=0)
        
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="line1\nline2\n")):
                result = processor.process_data()
                
                assert result == []
                assert processor.get_processed_count() == 0

    @pytest.mark.unit
    def test_edge_case_negative_max_items(self):
        """Test behavior when max_items is negative."""
        processor = DataProcessor("test.txt", max_items=-5)
        
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="line1\nline2\n")):
                result = processor.process_data()
                
                # Should process no items when max_items is negative
                assert result == []
                assert processor.get_processed_count() == 0
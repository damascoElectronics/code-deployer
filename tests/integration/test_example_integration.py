"""Integration tests for the DataProcessor class.

This module contains integration tests that test the DataProcessor class
with real file operations and end-to-end workflows.
"""

import os
import tempfile
import pytest
import shutil
from src.example import DataProcessor


class TestDataProcessorIntegration:
    """Integration tests for DataProcessor with real file operations."""

    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []

    def teardown_method(self):
        """Clean up temporary files and directories."""
        for file_path in self.test_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_file(self, filename: str, content: str) -> str:
        """Helper method to create test files."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self.test_files.append(file_path)
        return file_path

    @pytest.mark.integration
    def test_end_to_end_basic_workflow(self):
        """Test complete workflow from file creation to processing."""
        # Create test file
        content = "First line\nSecond line\n\nFourth line\nFifth line\n"
        test_file = self.create_test_file("basic_test.txt", content)
        
        # Process file
        processor = DataProcessor(test_file, max_items=10)
        result = processor.process_data(filter_empty=True)
        
        # Verify results
        expected = ["First line", "Second line", "Fourth line", "Fifth line"]
        assert result == expected
        assert processor.get_processed_count() == 4
        
        # Test file extension validation
        assert DataProcessor.validate_file_extension(test_file) is True

    @pytest.mark.integration
    def test_multiple_file_processing(self):
        """Test processing multiple files with the same processor."""
        # Create multiple test files
        file1 = self.create_test_file("file1.txt", "Line 1A\nLine 1B\n")
        file2 = self.create_test_file("file2.txt", "Line 2A\nLine 2B\nLine 2C\n")
        
        # Process first file
        processor1 = DataProcessor(file1)
        result1 = processor1.process_data()
        assert len(result1) == 2
        assert processor1.get_processed_count() == 2
        
        # Process second file with different processor
        processor2 = DataProcessor(file2)
        result2 = processor2.process_data()
        assert len(result2) == 3
        assert processor2.get_processed_count() == 3
        
        # Verify results are independent
        assert result1 != result2
        assert processor1.get_processed_count() != processor2.get_processed_count()

    @pytest.mark.integration
    def test_large_file_processing(self):
        """Test processing a large file with many lines."""
        # Create large file
        lines = [f"Large file line {i}" for i in range(1000)]
        content = "\n".join(lines) + "\n"
        large_file = self.create_test_file("large_file.txt", content)
        
        # Process with limit
        processor = DataProcessor(large_file, max_items=500)
        result = processor.process_data()
        
        # Verify results
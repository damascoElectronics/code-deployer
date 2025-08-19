"""Example of a Python module following the Google Style Guide.

This module demonstrates the Google Style Guide conventions 
and is used to test the pylint configuration.
"""

import os
import sys
from typing import List, Optional


class DataProcessor:
    """Procesador de datos que sigue Google Style Guide.
    Data processor that follows the Google Style Guide.

    This class demonstrates the naming conventions and documentation
    required by the Google Style Guide.

    Attributes:
        data_source: Data source to process.
        max_items: Maximum number of items to process.
    """

    def __init__(self, data_source: str, max_items: int = 100):
        """Initializes the data processor.

        Args:
            data_source: Path to the data file.
            max_items: Limit of items to process.

        Raises:
            ValueError: If data_source is empty.
        """
        if not data_source:
            raise ValueError("data_source cannot be empty")
            
        self.data_source = data_source
        self.max_items = max_items
        self._processed_count = 0

    def process_data(self, filter_empty: bool = True) -> List[str]:
        """Processes the data from the source file.

        Args:
            filter_empty: Whether to filter empty elements.

        Returns:
            List of processed elements.

        Raises:
            FileNotFoundError: If the file does not exist.
            IOError: If there are problems reading the file.
            OSError: If there are problems with permissions or system.
        """
        if not os.path.exists(self.data_source):
            raise FileNotFoundError(
                f"File not found: {self.data_source}")
            
        processed_items = []
        
        try:
            with open(self.data_source, 'r', encoding='utf-8') as file:
                for line_number, line in enumerate(file, 1):
                    if line_number > self.max_items:
                        break
                        
                    processed_line = line.strip()
                    
                    if filter_empty and not processed_line:
                        continue
                        
                    processed_items.append(processed_line)
                    self._processed_count += 1
                    
        except IOError as error:
            raise IOError(f"Error reading file: {error}") from error
            
        return processed_items

    def get_processed_count(self) -> int:
        """Returns the number of elements processed.

        Returns:
            Number of elements processed.
        """
        return self._processed_count

    @staticmethod
    
    def validate_file_extension(filename: str,
                                allowed_extensions: Optional[List[str]] = None
                                ) -> bool:
        """Validates whether the file has an allowed extension.

        Args:
            filename: Name of the file to validate.
            allowed_extensions: List of allowed extensions.
            By default, .txt and .csv are allowed.

        Returns:
            True if the extension is valid, False otherwise.
            Valida si el archivo tiene una extensión permitida.
        """
        if allowed_extensions is None:
            allowed_extensions = ['.txt', '.csv']
            
        file_extension = os.path.splitext(filename)[1].lower()
        return file_extension in allowed_extensions


def main():
    """Main function to demonstrate processor usage."""
    # use case
    processor = DataProcessor("data.txt", max_items=50)
    
    try:
        results = processor.process_data(filter_empty=True)
        print(f"Processed {len(results)} elements")
        print(f"Total processed elements: {processor.get_processed_count()}")
        
    except (FileNotFoundError, IOError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()



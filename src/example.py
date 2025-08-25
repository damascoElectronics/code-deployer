"""Network and parsing utilities following Google Style Guide.

This module provides utilities for making HTTP requests and parsing responses,
commonly needed in data processing and API integration tasks.
"""

import json
import re
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, List, Optional, Union, Any


class NetworkParser:
    """Network client and response parser following Google Style Guide.

    This class handles HTTP requests and provides methods to parse common
    response formats like JSON, plain text, and extract specific data patterns.

    Attributes:
        base_url: Base URL for API requests.
        timeout: Request timeout in seconds.
        headers: Default headers for requests.
    """

    def __init__(self, base_url: str = "", timeout: int = 30):
        """Initializes the NetworkParser.

        Args:
            base_url: Base URL for API requests. Defaults to empty string.
            timeout: Request timeout in seconds. Defaults to 30.

        Raises:
            ValueError: If timeout is negative.
        """
        if timeout < 0:
            raise ValueError("Timeout must be non-negative")

        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'NetworkParser/1.0',
            'Accept': 'application/json, text/plain',
            'Content-Type': 'application/json'
        }

    def make_request(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> str:
        """Makes an HTTP GET request to the specified endpoint.

        Args:
            endpoint: API endpoint to request.
            params: Query parameters to include in the request.

        Returns:
            Response body as string.

        Raises:
            ValueError: If endpoint is empty.
            urllib.error.URLError: If request fails.
            urllib.error.HTTPError: If HTTP error occurs.
        """
        if not endpoint:
            raise ValueError("Endpoint cannot be empty")

        # Build URL
        if self.base_url:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
        else:
            url = endpoint

        # Add query parameters
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"

        # Create request
        request = urllib.request.Request(url, headers=self.headers)

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.read().decode('utf-8')
        except (urllib.error.URLError, urllib.error.HTTPError) as error:
            raise error

    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parses JSON response string into dictionary.

        Args:
            response: JSON response string.

        Returns:
            Parsed JSON as dictionary.

        Raises:
            json.JSONDecodeError: If response is not valid JSON.
            ValueError: If response is empty.
        """
        if not response.strip():
            raise ValueError("Response cannot be empty")

        try:
            return json.loads(response)
        except json.JSONDecodeError as error:
            raise json.JSONDecodeError(
                f"Invalid JSON response: {error.msg}", error.doc, error.pos
            ) from error

    def extract_emails(self, text: str) -> List[str]:
        """Extracts email addresses from text using regex.

        Args:
            text: Text to search for email addresses.

        Returns:
            List of unique email addresses found.
        """
        if not text:
            return []

        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return list(set(emails))  # Remove duplicates

    def extract_urls(self, text: str) -> List[str]:
        """Extracts URLs from text using regex.

        Args:
            text: Text to search for URLs.

        Returns:
            List of unique URLs found.
        """
        if not text:
            return []

        url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+\.[A-Za-z]{2,}'
        urls = re.findall(url_pattern, text)
        return list(set(urls))  # Remove duplicates

    def parse_key_value_pairs(self, text: str, delimiter: str = "=") -> Dict[str, str]:
        """Parses key-value pairs from text.

        Args:
            text: Text containing key-value pairs, one per line.
            delimiter: Character that separates keys from values.

        Returns:
            Dictionary of key-value pairs.

        Raises:
            ValueError: If delimiter is empty.
        """
        if not delimiter:
            raise ValueError("Delimiter cannot be empty")

        result = {}
        if not text:
            return result

        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or delimiter not in line:
                continue

            key, value = line.split(delimiter, 1)
            result[key.strip()] = value.strip()

        return result

    def filter_lines_by_pattern(self, text: str, pattern: str) -> List[str]:
        """Filters lines that match a regex pattern.

        Args:
            text: Text to filter.
            pattern: Regex pattern to match.

        Returns:
            List of lines that match the pattern.

        Raises:
            re.error: If pattern is invalid regex.
        """
        if not text:
            return []

        try:
            compiled_pattern = re.compile(pattern)
        except re.error as error:
            raise re.error(f"Invalid regex pattern: {pattern}") from error

        lines = text.split('\n')
        return [line for line in lines if compiled_pattern.search(line)]

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validates if a string is a properly formatted URL.

        Args:
            url: URL string to validate.

        Returns:
            True if URL is valid, False otherwise.
        """
        if not url:
            return False

        url_pattern = r'^https?://[^\s<>"\']+\.[A-Za-z]{2,}'
        return bool(re.match(url_pattern, url))

    @staticmethod
    def clean_text(text: str) -> str:
        """Cleans text by removing extra whitespace and special characters.

        Args:
            text: Text to clean.

        Returns:
            Cleaned text string.
        """
        if not text:
            return ""

        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove non-printable characters except newlines and tabs
        cleaned = re.sub(r'[^\x20-\x7E\n\t]', '', cleaned)
        
        return cleaned

    def get_response_stats(self, response: str) -> Dict[str, int]:
        """Gets basic statistics about a response string.

        Args:
            response: Response string to analyze.

        Returns:
            Dictionary with statistics (character count, word count, line count).
        """
        if not response:
            return {"chars": 0, "words": 0, "lines": 0}

        stats = {
            "chars": len(response),
            "words": len(response.split()),
            "lines": len(response.split('\n'))
        }

        return stats


def main():
    """Main function demonstrating NetworkParser usage."""
    # Example usage
    parser = NetworkParser("https://api.example.com", timeout=10)
    
    try:
        # This would work with a real API
        # response = parser.make_request("status")
        # data = parser.parse_json_response(response)
        
        # Example with text parsing
        sample_text = """
        Contact us at support@example.com or admin@test.org
        Visit https://www.example.com or http://test.com
        key1=value1
        key2=value2
        """
        
        emails = parser.extract_emails(sample_text)
        urls = parser.extract_urls(sample_text)
        key_values = parser.parse_key_value_pairs("key1=value1\nkey2=value2")
        
        print(f"Found emails: {emails}")
        print(f"Found URLs: {urls}")
        print(f"Key-value pairs: {key_values}")
        
    except (ValueError, urllib.error.URLError) as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
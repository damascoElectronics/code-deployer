"""Main tests for the NetworkParser class.

This module contains general tests for NetworkParser functionality.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from src.example import NetworkParser


class TestNetworkParser:
    """General test suite for NetworkParser class."""

    def test_initialization_basic(self):
        """Test basic NetworkParser initialization."""
        parser = NetworkParser()
        assert parser is not None
        assert parser.timeout == 30
        assert parser.base_url == ""

    def test_initialization_with_parameters(self):
        """Test NetworkParser initialization with parameters."""
        parser = NetworkParser("https://api.test.com", timeout=15)
        assert parser.base_url == "https://api.test.com"
        assert parser.timeout == 15

    def test_json_parsing_success(self):
        """Test successful JSON parsing."""
        parser = NetworkParser()
        json_data = '{"name": "test", "value": 123}'
        
        result = parser.parse_json_response(json_data)
        
        assert result["name"] == "test"
        assert result["value"] == 123

    def test_email_extraction_basic(self):
        """Test basic email extraction."""
        parser = NetworkParser()
        text = "Send email to contact@example.com for support"
        
        emails = parser.extract_emails(text)
        
        assert len(emails) == 1
        assert "contact@example.com" in emails

    def test_url_extraction_basic(self):
        """Test basic URL extraction."""
        parser = NetworkParser()
        text = "Visit our website at https://www.example.com"
        
        urls = parser.extract_urls(text)
        
        assert len(urls) == 1
        assert "https://www.example.com" in urls

    def test_key_value_parsing_basic(self):
        """Test basic key-value parsing."""
        parser = NetworkParser()
        text = "name=John\nage=30"
        
        result = parser.parse_key_value_pairs(text)
        
        assert result["name"] == "John"
        assert result["age"] == "30"

    def test_text_filtering_basic(self):
        """Test basic text filtering."""
        parser = NetworkParser()
        text = "INFO: Starting\nERROR: Failed\nINFO: Running"
        
        errors = parser.filter_lines_by_pattern(text, "ERROR")
        
        assert len(errors) == 1
        assert "ERROR: Failed" in errors

    def test_url_validation_static_method(self):
        """Test URL validation static method."""
        assert NetworkParser.validate_url("https://example.com") is True
        assert NetworkParser.validate_url("http://test.org") is True
        assert NetworkParser.validate_url("invalid-url") is False
        assert NetworkParser.validate_url("") is False

    def test_text_cleaning_static_method(self):
        """Test text cleaning static method."""
        dirty_text = "  hello   world  "
        clean_text = NetworkParser.clean_text(dirty_text)
        
        assert clean_text == "hello world"

    def test_response_stats_basic(self):
        """Test response statistics."""
        parser = NetworkParser()
        text = "hello world\nsecond line"
        
        stats = parser.get_response_stats(text)
        
        assert stats["words"] == 4
        assert stats["lines"] == 2
        assert stats["chars"] > 10

    @patch('urllib.request.urlopen')
    def test_make_request_mocked(self, mock_urlopen):
        """Test make_request with mocked HTTP call."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"status": "ok"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=None)
        mock_urlopen.return_value = mock_response
        
        parser = NetworkParser("https://api.example.com")
        result = parser.make_request("test")
        
        assert result == '{"status": "ok"}'
        mock_urlopen.assert_called_once()

    def test_error_handling_json(self):
        """Test error handling for invalid JSON."""
        parser = NetworkParser()
        
        with pytest.raises(json.JSONDecodeError):
            parser.parse_json_response("invalid json")

    def test_error_handling_empty_endpoint(self):
        """Test error handling for empty endpoint."""
        parser = NetworkParser()
        
        with pytest.raises(ValueError, match="Endpoint cannot be empty"):
            parser.make_request("")

    def test_error_handling_negative_timeout(self):
        """Test error handling for negative timeout."""
        with pytest.raises(ValueError, match="Timeout must be non-negative"):
            NetworkParser(timeout=-1)

    def test_error_handling_empty_delimiter(self):
        """Test error handling for empty delimiter."""
        parser = NetworkParser()
        
        with pytest.raises(ValueError, match="Delimiter cannot be empty"):
            parser.parse_key_value_pairs("test", delimiter="")

    def test_complex_email_extraction(self):
        """Test email extraction with complex patterns."""
        parser = NetworkParser()
        text = """
        Contact information:
        - Primary: admin@company.com
        - Secondary: support+help@example.org
        - Sales: sales@new-domain.co.uk
        """
        
        emails = parser.extract_emails(text)
        
        assert len(emails) >= 3
        assert "admin@company.com" in emails
        assert "support+help@example.org" in emails
        assert "sales@new-domain.co.uk" in emails

    def test_complex_url_extraction(self):
        """Test URL extraction with various formats."""
        parser = NetworkParser()
        text = """
        Resources:
        - Documentation: https://docs.example.com/api
        - Website: http://www.example.com
        - Help: www.help.example.org
        """
        
        urls = parser.extract_urls(text)
        
        assert len(urls) >= 3
        valid_urls = [url for url in urls if "example" in url]
        assert len(valid_urls) >= 3

    def test_end_to_end_workflow(self):
        """Test end-to-end workflow with realistic data."""
        parser = NetworkParser()
        
        # Simulate processing a configuration response
        config_response = """{
            "api_settings": {
                "endpoints": "https://api.service.com, https://backup.service.com",
                "contact": "admin@service.com",
                "timeout": "30"
            },
            "raw_config": "debug=true\\nverbose=false"
        }"""
        
        # Parse JSON
        data = parser.parse_json_response(config_response)
        
        # Extract information
        endpoints_text = data["api_settings"]["endpoints"]
        contact_text = data["api_settings"]["contact"]
        raw_config = data["raw_config"].replace("\\n", "\n")
        
        # Process extracted data
        urls = parser.extract_urls(endpoints_text)
        emails = parser.extract_emails(contact_text)
        config = parser.parse_key_value_pairs(raw_config)
        
        # Verify end-to-end processing
        assert len(urls) >= 2
        assert len(emails) >= 1
        assert "admin@service.com" in emails
        assert config["debug"] == "true"
        assert config["verbose"] == "false"
        assert any("api.service.com" in url for url in urls)


# Fixtures for reuse across tests
@pytest.fixture
def sample_parser():
    """Fixture providing a NetworkParser instance."""
    return NetworkParser("https://api.example.com", timeout=10)


@pytest.fixture
def sample_json_response():
    """Fixture providing sample JSON response."""
    return '{"users": [{"name": "John", "email": "john@example.com"}], "total": 1}'


@pytest.fixture 
def sample_mixed_content():
    """Fixture providing mixed content for parsing."""
    return """
    Welcome! Contact us at support@company.com
    Visit https://www.company.com for more info
    Configuration:
    api_key=abc123
    timeout=60
    """


def test_with_sample_parser(sample_parser):
    """Test using sample parser fixture."""
    assert sample_parser.base_url == "https://api.example.com"
    assert sample_parser.timeout == 10


def test_with_sample_json(sample_parser, sample_json_response):
    """Test using JSON fixture."""
    result = sample_parser.parse_json_response(sample_json_response)
    
    assert result["total"] == 1
    assert len(result["users"]) == 1
    assert result["users"][0]["name"] == "John"


def test_with_mixed_content(sample_parser, sample_mixed_content):
    """Test using mixed content fixture."""
    emails = sample_parser.extract_emails(sample_mixed_content)
    urls = sample_parser.extract_urls(sample_mixed_content)
    
    assert "support@company.com" in emails
    assert any("company.com" in url for url in urls)
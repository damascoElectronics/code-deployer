"""Unit tests for the NetworkParser class.

This module contains isolated unit tests that test individual methods
of the NetworkParser class without external dependencies.
"""

import json
import re
import urllib.error
import pytest
from unittest.mock import patch, mock_open, MagicMock
from src.example import NetworkParser


class TestNetworkParserUnit:
    """Unit tests for NetworkParser class focusing on isolated functionality."""

    @pytest.mark.unit
    def test_init_with_valid_parameters(self):
        """Test initialization with valid parameters."""
        parser = NetworkParser("https://api.example.com", timeout=10)
        
        assert parser.base_url == "https://api.example.com"
        assert parser.timeout == 10
        assert "User-Agent" in parser.headers

    @pytest.mark.unit
    def test_init_with_default_parameters(self):
        """Test initialization with default parameters."""
        parser = NetworkParser()
        
        assert parser.base_url == ""
        assert parser.timeout == 30
        assert isinstance(parser.headers, dict)

    @pytest.mark.unit
    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is removed from base_url."""
        parser = NetworkParser("https://api.example.com/")
        assert parser.base_url == "https://api.example.com"

    @pytest.mark.unit
    def test_init_negative_timeout_raises_error(self):
        """Test that negative timeout raises ValueError."""
        with pytest.raises(ValueError, match="Timeout must be non-negative"):
            NetworkParser(timeout=-1)

    @pytest.mark.unit
    def test_parse_json_response_valid_json(self):
        """Test parsing valid JSON response."""
        parser = NetworkParser()
        json_string = '{"key": "value", "number": 42}'
        
        result = parser.parse_json_response(json_string)
        
        assert result == {"key": "value", "number": 42}

    @pytest.mark.unit
    def test_parse_json_response_empty_string(self):
        """Test that empty string raises ValueError."""
        parser = NetworkParser()
        
        with pytest.raises(ValueError, match="Response cannot be empty"):
            parser.parse_json_response("")

    @pytest.mark.unit
    def test_parse_json_response_invalid_json(self):
        """Test that invalid JSON raises JSONDecodeError."""
        parser = NetworkParser()
        
        with pytest.raises(json.JSONDecodeError):
            parser.parse_json_response("invalid json")

    @pytest.mark.unit
    def test_extract_emails_valid_emails(self):
        """Test extracting valid email addresses."""
        parser = NetworkParser()
        text = "Contact us at support@example.com or admin@test.org"
        
        emails = parser.extract_emails(text)
        
        assert len(emails) == 2
        assert "support@example.com" in emails
        assert "admin@test.org" in emails

    @pytest.mark.unit
    def test_extract_emails_no_emails(self):
        """Test extracting from text with no emails."""
        parser = NetworkParser()
        text = "No emails in this text"
        
        emails = parser.extract_emails(text)
        
        assert emails == []

    @pytest.mark.unit
    def test_extract_emails_empty_string(self):
        """Test extracting from empty string."""
        parser = NetworkParser()
        
        emails = parser.extract_emails("")
        
        assert emails == []

    @pytest.mark.unit
    def test_extract_emails_duplicates_removed(self):
        """Test that duplicate emails are removed."""
        parser = NetworkParser()
        text = "Email test@example.com and test@example.com again"
        
        emails = parser.extract_emails(text)
        
        assert len(emails) == 1
        assert "test@example.com" in emails

    @pytest.mark.unit
    def test_extract_urls_valid_urls(self):
        """Test extracting valid URLs."""
        parser = NetworkParser()
        text = "Visit https://www.example.com or http://test.com"
        
        urls = parser.extract_urls(text)
        
        assert len(urls) == 2
        assert "https://www.example.com" in urls
        assert "http://test.com" in urls

    @pytest.mark.unit
    def test_extract_urls_with_www(self):
        """Test extracting URLs with www prefix."""
        parser = NetworkParser()
        text = "Check www.example.com for more info"
        
        urls = parser.extract_urls(text)
        
        assert len(urls) == 1
        assert "www.example.com" in urls

    @pytest.mark.unit
    def test_extract_urls_empty_string(self):
        """Test extracting URLs from empty string."""
        parser = NetworkParser()
        
        urls = parser.extract_urls("")
        
        assert urls == []

    @pytest.mark.unit
    def test_parse_key_value_pairs_basic(self):
        """Test parsing basic key-value pairs."""
        parser = NetworkParser()
        text = "key1=value1\nkey2=value2"
        
        result = parser.parse_key_value_pairs(text)
        
        assert result == {"key1": "value1", "key2": "value2"}

    @pytest.mark.unit
    def test_parse_key_value_pairs_custom_delimiter(self):
        """Test parsing with custom delimiter."""
        parser = NetworkParser()
        text = "key1:value1\nkey2:value2"
        
        result = parser.parse_key_value_pairs(text, delimiter=":")
        
        assert result == {"key1": "value1", "key2": "value2"}

    @pytest.mark.unit
    def test_parse_key_value_pairs_empty_delimiter(self):
        """Test that empty delimiter raises ValueError."""
        parser = NetworkParser()
        
        with pytest.raises(ValueError, match="Delimiter cannot be empty"):
            parser.parse_key_value_pairs("key=value", delimiter="")

    @pytest.mark.unit
    def test_parse_key_value_pairs_empty_text(self):
        """Test parsing empty text returns empty dict."""
        parser = NetworkParser()
        
        result = parser.parse_key_value_pairs("")
        
        assert result == {}

    @pytest.mark.unit
    def test_parse_key_value_pairs_whitespace_handling(self):
        """Test that whitespace is properly handled."""
        parser = NetworkParser()
        text = " key1 = value1 \n key2 = value2 "
        
        result = parser.parse_key_value_pairs(text)
        
        assert result == {"key1": "value1", "key2": "value2"}

    @pytest.mark.unit
    def test_filter_lines_by_pattern_basic(self):
        """Test filtering lines by regex pattern."""
        parser = NetworkParser()
        text = "line1\nerror: something\nline3\nerror: other"
        
        result = parser.filter_lines_by_pattern(text, r"error:")
        
        assert len(result) == 2
        assert "error: something" in result
        assert "error: other" in result

    @pytest.mark.unit
    def test_filter_lines_by_pattern_invalid_regex(self):
        """Test that invalid regex raises re.error."""
        parser = NetworkParser()
        
        with pytest.raises(re.error):
            parser.filter_lines_by_pattern("text", "[invalid")

    @pytest.mark.unit
    def test_filter_lines_by_pattern_empty_text(self):
        """Test filtering empty text returns empty list."""
        parser = NetworkParser()
        
        result = parser.filter_lines_by_pattern("", r"pattern")
        
        assert result == []

    @pytest.mark.unit
    def test_validate_url_valid_urls(self):
        """Test URL validation with valid URLs."""
        assert NetworkParser.validate_url("https://www.example.com") is True
        assert NetworkParser.validate_url("http://test.org") is True

    @pytest.mark.unit
    def test_validate_url_invalid_urls(self):
        """Test URL validation with invalid URLs."""
        assert NetworkParser.validate_url("not-a-url") is False
        assert NetworkParser.validate_url("") is False
        assert NetworkParser.validate_url("ftp://example.com") is False

    @pytest.mark.unit
    def test_clean_text_basic(self):
        """Test basic text cleaning."""
        result = NetworkParser.clean_text("  hello   world  ")
        
        assert result == "hello world"

    @pytest.mark.unit
    def test_clean_text_empty_string(self):
        """Test cleaning empty string."""
        result = NetworkParser.clean_text("")
        
        assert result == ""

    @pytest.mark.unit
    def test_clean_text_special_characters(self):
        """Test cleaning text with special characters."""
        text = "hello\t\tworld\n\ntest"
        result = NetworkParser.clean_text(text)
        
        # Should preserve newlines and tabs but normalize other whitespace
        assert "hello" in result
        assert "world" in result
        assert "test" in result

    @pytest.mark.unit
    def test_get_response_stats_basic(self):
        """Test getting response statistics."""
        parser = NetworkParser()
        response = "hello world\nline two"
        
        stats = parser.get_response_stats(response)
        
        assert stats["chars"] > 0
        assert stats["words"] == 4
        assert stats["lines"] == 2

    @pytest.mark.unit
    def test_get_response_stats_empty_response(self):
        """Test getting stats for empty response."""
        parser = NetworkParser()
        
        stats = parser.get_response_stats("")
        
        assert stats == {"chars": 0, "words": 0, "lines": 0}

    @pytest.mark.unit
    def test_make_request_empty_endpoint(self):
        """Test that empty endpoint raises ValueError."""
        parser = NetworkParser()
        
        with pytest.raises(ValueError, match="Endpoint cannot be empty"):
            parser.make_request("")

    @pytest.mark.unit
    @patch('urllib.request.urlopen')
    def test_make_request_basic(self, mock_urlopen):
        """Test basic request functionality with mocking."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"status": "ok"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=None)
        mock_urlopen.return_value = mock_response
        
        parser = NetworkParser("https://api.example.com")
        result = parser.make_request("status")
        
        assert result == '{"status": "ok"}'
        mock_urlopen.assert_called_once()

    @pytest.mark.unit 
    @patch('urllib.request.urlopen')
    def test_make_request_with_params(self, mock_urlopen):
        """Test request with query parameters."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'response'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=None)
        mock_urlopen.return_value = mock_response
        
        parser = NetworkParser("https://api.example.com")
        parser.make_request("search", {"q": "test", "limit": "10"})
        
        # Verify urlopen was called with the right URL structure
        mock_urlopen.assert_called_once()
        call_args = mock_urlopen.call_args[0][0]
        assert "search" in call_args.full_url
        assert "q=test" in call_args.full_url
        assert "limit=10" in call_args.full_url
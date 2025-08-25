"""Integration tests for the NetworkParser class.

This module contains integration tests that test NetworkParser
with realistic data and end-to-end workflows.
"""

import pytest
from src.example import NetworkParser


class TestNetworkParserIntegration:
    """Integration tests for NetworkParser with realistic scenarios."""

    @pytest.mark.integration
    def test_full_text_processing_workflow(self):
        """Test complete text processing workflow."""
        parser = NetworkParser()
        
        # Realistic sample text with emails, URLs, and key-value pairs
        sample_text = """
        Welcome to our service!
        
        Contact information:
        support@company.com
        admin@example.org
        
        Useful links:
        https://www.documentation.com
        http://api.example.com
        www.help-center.org
        
        Configuration:
        api_key=abc123def456
        timeout=30
        debug=true
        """
        
        # Extract all information
        emails = parser.extract_emails(sample_text)
        urls = parser.extract_urls(sample_text)
        
        # Test that we found the expected items
        assert len(emails) >= 2
        assert "support@company.com" in emails
        assert "admin@example.org" in emails
        
        assert len(urls) >= 3
        assert any("documentation.com" in url for url in urls)
        assert any("api.example.com" in url for url in urls)
        assert any("help-center.org" in url for url in urls)

    @pytest.mark.integration
    def test_config_file_parsing(self):
        """Test parsing configuration file format."""
        parser = NetworkParser()
        
        config_content = """
        # Database settings
        db_host=localhost
        db_port=5432
        db_name=myapp
        
        # API settings
        api_timeout=60
        api_retries=3
        
        # Feature flags
        enable_logging=true
        debug_mode=false
        """
        
        # Parse configuration
        config = parser.parse_key_value_pairs(config_content)
        
        # Verify parsed configuration
        assert "db_host" in config
        assert config["db_host"] == "localhost"
        assert config["db_port"] == "5432"
        assert config["api_timeout"] == "60"
        assert config["enable_logging"] == "true"
        
        # Test we got all non-comment lines
        assert len(config) >= 6  # Should be at least 6 items

    @pytest.mark.integration
    def test_log_file_analysis(self):
        """Test analyzing log file content."""
        parser = NetworkParser()
        
        log_content = """
        2024-01-01 10:00:00 INFO Application started
        2024-01-01 10:00:01 DEBUG Loading configuration
        2024-01-01 10:00:02 INFO User login: user@example.com
        2024-01-01 10:05:00 WARNING Low memory detected
        2024-01-01 10:10:00 ERROR Database connection failed
        2024-01-01 10:10:01 INFO Retrying connection
        2024-01-01 10:10:05 ERROR Connection timeout
        """
        
        # Filter different log levels
        errors = parser.filter_lines_by_pattern(log_content, r"ERROR")
        warnings = parser.filter_lines_by_pattern(log_content, r"WARNING")
        info_logs = parser.filter_lines_by_pattern(log_content, r"INFO")
        
        # Verify filtering worked
        assert len(errors) == 2
        assert len(warnings) == 1
        assert len(info_logs) == 3
        
        # Extract emails from logs
        emails = parser.extract_emails(log_content)
        assert "user@example.com" in emails

    @pytest.mark.integration
    def test_response_processing_chain(self):
        """Test chaining multiple processing methods."""
        parser = NetworkParser()
        
        # Simulate an API response with mixed content
        api_response = """
        {
            "status": "success",
            "message": "Contact support@api.com for help",
            "documentation": "Visit https://docs.api.com",
            "config": "timeout=120\\nretries=5"
        }
        """
        
        # Parse as JSON
        data = parser.parse_json_response(api_response)
        
        # Extract information from the parsed data
        message = data.get("message", "")
        doc_url = data.get("documentation", "")
        config_str = data.get("config", "")
        
        # Process the extracted content
        emails = parser.extract_emails(message)
        urls = parser.extract_urls(doc_url)
        
        # Parse configuration string (simulating escaped newlines)
        config_normalized = config_str.replace("\\n", "\n")
        config = parser.parse_key_value_pairs(config_normalized)
        
        # Verify the chain worked
        assert data["status"] == "success"
        assert "support@api.com" in emails
        assert any("docs.api.com" in url for url in urls)
        assert config["timeout"] == "120"
        assert config["retries"] == "5"

    @pytest.mark.integration
    def test_text_cleaning_and_stats(self):
        """Test text cleaning and statistics generation."""
        parser = NetworkParser()
        
        messy_text = """
        
        Hello    world!   This  is   a  test.
        
        
        Line   with   extra    spaces.
        Final line.
        
        """
        
        # Clean the text
        cleaned = parser.clean_text(messy_text)
        
        # Get statistics
        original_stats = parser.get_response_stats(messy_text)
        cleaned_stats = parser.get_response_stats(cleaned)
        
        # Verify cleaning worked
        assert "Hello world!" in cleaned
        assert len(cleaned) < len(messy_text)  # Should be shorter after cleaning
        
        # Verify stats make sense
        assert original_stats["chars"] > cleaned_stats["chars"]  # Cleaning removed characters
        assert original_stats["words"] == cleaned_stats["words"]  # Same word count
        
        # Both should have reasonable line counts
        assert cleaned_stats["lines"] > 0

    @pytest.mark.integration
    def test_email_extraction_from_multiple_formats(self):
        """Test email extraction from various formats."""
        parser = NetworkParser()
        
        text_samples = [
            "Email me at john.doe@example.com for details",
            "Contact: <admin@test.org>",
            "Support team (support+help@company.co.uk)",
            "Sales: sales@new-company.com, Marketing: marketing@new-company.com"
        ]
        
        all_emails = []
        for text in text_samples:
            emails = parser.extract_emails(text)
            all_emails.extend(emails)
        
        # Remove duplicates
        unique_emails = list(set(all_emails))
        
        # Verify we found emails from all samples
        assert len(unique_emails) >= 4
        assert any("john.doe@example.com" in email for email in unique_emails)
        assert any("admin@test.org" in email for email in unique_emails)
        assert any("support+help@company.co.uk" in email for email in unique_emails)

    @pytest.mark.integration
    def test_url_validation_and_extraction_combined(self):
        """Test combining URL extraction and validation."""
        parser = NetworkParser()
        
        text_with_urls = """
        Valid URLs:
        https://www.example.com
        http://test.org
        
        Invalid or incomplete URLs:
        www.incomplete
        not-a-url
        ftp://file.server.com
        """
        
        # Extract all URLs
        extracted_urls = parser.extract_urls(text_with_urls)
        
        # Validate each extracted URL
        valid_urls = [url for url in extracted_urls if parser.validate_url(url)]
        
        # Should find the valid HTTP/HTTPS URLs
        assert len(extracted_urls) >= 2
        assert len(valid_urls) >= 2
        
        # Verify specific URLs
        https_found = any("https://www.example.com" in url for url in valid_urls)
        http_found = any("http://test.org" in url for url in valid_urls)
        
        assert https_found or http_found  # At least one should be found

    @pytest.mark.integration  
    def test_error_handling_in_workflow(self):
        """Test error handling in realistic scenarios."""
        parser = NetworkParser()
        
        # Test with invalid JSON
        try:
            parser.parse_json_response("invalid json {")
            assert False, "Should have raised JSONDecodeError"
        except Exception as e:
            assert "JSONDecodeError" in str(type(e))
        
        # Test with empty values
        assert parser.extract_emails("") == []
        assert parser.extract_urls("") == []
        assert parser.parse_key_value_pairs("") == {}
        
        # Test with invalid regex (should raise error)
        try:
            parser.filter_lines_by_pattern("text", "[invalid regex")
            assert False, "Should have raised re.error"
        except Exception as e:
            assert "error" in str(type(e)).lower()

    @pytest.mark.integration
    def test_performance_with_large_text(self):
        """Test performance with larger text samples."""
        parser = NetworkParser()
        
        # Create a larger text sample
        large_text = ""
        for i in range(100):
            large_text += f"Line {i}: Contact user{i}@example.com or visit https://site{i}.com\n"
            large_text += f"Config line: setting{i}=value{i}\n"
        
        # Process the large text
        emails = parser.extract_emails(large_text)
        urls = parser.extract_urls(large_text)
        stats = parser.get_response_stats(large_text)
        
        # Verify we processed everything
        assert len(emails) == 100  # Should find 100 unique emails
        assert len(urls) == 100   # Should find 100 unique URLs
        assert stats["chars"] > 5000  # Should be a substantial amount of text
        assert stats["lines"] >= 200   # Should be around 200 lines (100 * 2)
        
        # Test cleaning large text
        cleaned = parser.clean_text(large_text)
        assert len(cleaned) > 0
        assert len(cleaned) <= len(large_text)  # Should be same or smaller

    @pytest.mark.integration
    def test_realistic_api_response_processing(self):
        """Test processing realistic API response structure."""
        parser = NetworkParser()
        
        # Simulate realistic API response
        api_response = """{
            "users": [
                {
                    "id": 1,
                    "email": "john@company.com",
                    "profile_url": "https://profiles.company.com/john"
                },
                {
                    "id": 2,
                    "email": "jane@company.com", 
                    "profile_url": "https://profiles.company.com/jane"
                }
            ],
            "meta": {
                "total": 2,
                "api_docs": "Visit https://api.company.com/docs",
                "support": "Contact support@company.com"
            },
            "config": "cache_timeout=3600\\nmax_results=100"
        }"""
        
        # Parse JSON
        data = parser.parse_json_response(api_response)
        
        # Extract emails from the entire response
        response_emails = parser.extract_emails(api_response)
        
        # Extract URLs
        response_urls = parser.extract_urls(api_response) 
        
        # Parse configuration
        config_str = data["config"].replace("\\n", "\n")
        config = parser.parse_key_value_pairs(config_str)
        
        # Verify comprehensive extraction
        assert len(response_emails) >= 3  # john, jane, support
        assert len(response_urls) >= 3    # 2 profiles + docs
        assert len(data["users"]) == 2
        assert config["cache_timeout"] == "3600"
        assert config["max_results"] == "100"
        
        # Verify specific data
        assert "john@company.com" in response_emails
        assert "support@company.com" in response_emails
        assert any("api.company.com" in url for url in response_urls)
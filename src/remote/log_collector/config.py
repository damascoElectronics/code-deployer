#!/usr/bin/env python3
"""Configuration for Log Collector.

This module defines configuration settings for the log collector
service that packages data from OGS providers.
"""
import os


class Config:
    """Configuration for log collector."""

    # OGS Data Provider URL
    OGS_PROVIDER_URL = os.getenv(
        "OGS_PROVIDER_URL",
        "http://ogs-data-generator:5000"
    )

    # Fetch configuration
    FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "10"))
    FETCH_TIMEOUT = int(os.getenv("FETCH_TIMEOUT", "5"))

    # Storage configuration
    DATA_DIR = os.getenv("DATA_DIR", "/app/collected_data")

    # HTTP Server configuration
    HTTP_SERVER_PORT = int(os.getenv("HTTP_SERVER_PORT", "8080"))

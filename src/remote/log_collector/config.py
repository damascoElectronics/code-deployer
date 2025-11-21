"""
Configuration for Log Collector
"""
import os


class Config:
    """Configuration for log collector."""
    
    # OGS Data Provider URL (será reemplazado por proveedor real en futuro)
    OGS_PROVIDER_URL = os.getenv(
        "OGS_PROVIDER_URL",
        "http://ogs-data-generator:5000"
    )
    
    # Fetch configuration
    FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "10"))  # seconds
    FETCH_TIMEOUT = int(os.getenv("FETCH_TIMEOUT", "5"))  # seconds
    
    # Storage configuration
    DATA_DIR = os.getenv("DATA_DIR", "/app/collected_data")
    
    # HTTP Server configuration
    HTTP_SERVER_PORT = int(os.getenv("HTTP_SERVER_PORT", "8080"))

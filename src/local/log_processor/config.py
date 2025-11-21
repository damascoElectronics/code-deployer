    """
    Centralized configuration for all data processors.

    Each processor can access common settings (DB, logging)
    and processor-specific settings.
    """

import os

class Config:

    # Database Configuration (Shared by all processors)
    DB_HOST = os.getenv("DB_HOST", "keypool_mysql")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_NAME = os.getenv("DB_NAME", "keypool_logs")
    DB_USER = os.getenv("DB_USER", "ogs_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "ogs_password")

    # Processor Enable/Disable Flags
    ENABLE_KEYPOOL = os.getenv("ENABLE_KEYPOOL", "true").lower() == "true"
    ENABLE_OGS = os.getenv("ENABLE_OGS", "true").lower() == "true"

    # KeyPool Processor Configuration
    KEYPOOL_LOG_DIR = os.getenv("KEYPOOL_LOG_DIR", "/data/keypool_logs")
    KEYPOOL_PROCESS_INTERVAL = int(os.getenv("KEYPOOL_PROCESS_INTERVAL", "30"))

    # OGS Processor Configuration
    OGS_COLLECTOR_URL = os.getenv(
        "OGS_COLLECTOR_URL",
        "http://192.168.0.11:8080"
    )
    OGS_PROCESS_INTERVAL = int(os.getenv("OGS_PROCESS_INTERVAL", "15"))
    OGS_DOWNLOAD_DIR = os.getenv("OGS_DOWNLOAD_DIR", "/app/downloads/ogs")
    OGS_SAVE_DOWNLOADS = os.getenv("OGS_SAVE_DOWNLOADS", "true").lower() == "true"

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    def __repr__(self):
        """String representation for debugging."""
        return (
            f"Config(\n"
            f"  DB: {self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}\n"
            f"  KeyPool: {'Enabled' if self.ENABLE_KEYPOOL else 'Disabled'}\n"
            f"  OGS: {'Enabled' if self.ENABLE_OGS else 'Disabled'}\n"
            f")"
        )

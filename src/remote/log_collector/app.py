#!/usr/bin/env python3
"""
Parser module for log_processor.

Handles parsing log files and storing data in database.
"""

import sys
import signal
import time
import logging
import json
from datetime import datetime
from pathlib import Path
from threading import Thread

import requests
from flask import Flask, jsonify, send_file

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


class LogCollector:
    """
    Collector for OGS Data Generator and packages data.
    
    The collector fetches data from multiple endpoints and creates
    JSON packages for Log Processor consumption.
    """
    
    def __init__(self):
        """Initialize the LogCollector with configuration."""
        self.config = Config()
        self.running = False
        self._setup_directories()
        
        self.stats = {
            "total_fetches": 0,
            "failed_fetches": 0,
            "last_fetch": None,
            "ogs_provider": self.config.OGS_PROVIDER_URL
        }
    
    def _setup_directories(self):
        """Create data directory."""
        Path(self.config.DATA_DIR).mkdir(parents=True, exist_ok=True)
        logger.info("Data directory: %s", self.config.DATA_DIR)
    
    def fetch_from_ogs(self, endpoint):
        """
        Query OGS Data Generator endpoint.
        
        Args:
            endpoint: API endpoint to query
            
        Returns:
            JSON response or None on error
        """
        try:
            url = f"{self.config.OGS_PROVIDER_URL}/{endpoint}"
            response = requests.get(
                url, 
                timeout=self.config.FETCH_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            logger.error("Failed to fetch from OGS %s: %s", endpoint, error)
            return None
    
    def package_data(self):
        """
        Package OGS data and own logs.
        
        Creates a JSON package with all information from OGS endpoints.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Query all OGS endpoints
            package = {
                "package_timestamp": (
                    datetime.utcnow().isoformat() + "Z"
                ),
                "collector_id": "log_collector_001",
                "ogs_provider": self.config.OGS_PROVIDER_URL,
                "data": {
                    "environment": self.fetch_from_ogs("api/environment"),
                    "link": self.fetch_from_ogs("api/link"),
                    "summary": self.fetch_from_ogs("api/summary"),
                    "alerts": self.fetch_from_ogs("api/alerts"),
                    "schedule": self.fetch_from_ogs("api/schedule")
                },
                "logs": {
                    "collector_status": "operational",
                    "last_fetch": self.stats["last_fetch"],
                    "total_fetches": self.stats["total_fetches"]
                }
            }
            
            # Save package
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.config.DATA_DIR}/package_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(package, file, indent=2)
            
            logger.info("Package created: %s", filename)
            return True
            
        except (IOError, OSError) as error:
            logger.error("Error creating package: %s", error)
            return False
    
    def run(self):
        """Main collection loop."""
        self.running = True
        logger.info("=" * 60)
        logger.info("Log Collector Started")
        logger.info("=" * 60)
        logger.info("OGS Provider: %s", self.config.OGS_PROVIDER_URL)
        logger.info("Fetch Interval: %ss", self.config.FETCH_INTERVAL)
        logger.info("HTTP Server: Port %s", self.config.HTTP_SERVER_PORT)
        logger.info("=" * 60)
        
        # Test connection to OGS
        try:
            response = requests.get(
                f"{self.config.OGS_PROVIDER_URL}/health",
                timeout=5
            )
            logger.info(
                "OGS Provider status: %s",
                response.json().get('status')
            )
        except requests.RequestException as error:
            logger.warning("Cannot reach OGS Provider: %s", error)
        
        # Main loop
        while self.running:
            try:
                if self.package_data():
                    self.stats["total_fetches"] += 1
                else:
                    self.stats["failed_fetches"] += 1
                
                self.stats["last_fetch"] = (
                    datetime.utcnow().isoformat() + "Z"
                )
                
                logger.info(
                    "Fetch #%d, Failed: %d",
                    self.stats['total_fetches'],
                    self.stats['failed_fetches']
                )
                
                time.sleep(self.config.FETCH_INTERVAL)
            except Exception as error:
                logger.error("Error in main loop: %s", error)
                time.sleep(self.config.FETCH_INTERVAL)
        
        logger.info("Log Collector stopped")
    
    def stop(self):
        """Stop the collector."""
        logger.info("Stopping collector...")
        self.running = False


# Global collector instance
collector = LogCollector()


# HTTP API for Log Processor
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "log_collector",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "stats": collector.stats
    })


@app.route('/api/packages', methods=['GET'])
def list_packages():
    """List all available packages."""
    data_dir = Path(collector.config.DATA_DIR)
    packages = sorted([
        f.name for f in data_dir.glob("package_*.json")
    ])
    return jsonify({
        "count": len(packages),
        "packages": packages
    })


@app.route('/api/packages/latest', methods=['GET'])
def get_latest_package():
    """Get the latest package."""
    data_dir = Path(collector.config.DATA_DIR)
    packages = sorted(data_dir.glob("package_*.json"))
    
    if packages:
        latest = packages[-1]
        with open(latest, 'r', encoding='utf-8') as file:
            return jsonify(json.load(file))
    
    return jsonify({"error": "No packages available"}), 404


@app.route('/api/packages/<filename>', methods=['GET'])
def get_package(filename):
    """
    Download a specific package.
    
    Args:
        filename: Name of the package file
        
    Returns:
        File download or error
    """
    if not filename.startswith('package_'):
        return jsonify({"error": "Invalid package name"}), 400
    if not filename.endswith('.json'):
        return jsonify({"error": "Invalid package name"}), 400
    
    filepath = Path(collector.config.DATA_DIR) / filename
    if filepath.exists():
        return send_file(filepath, mimetype='application/json')
    
    return jsonify({"error": "Package not found"}), 404


def run_collector():
    """Run collector in background thread."""
    collector.run()


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info("Shutdown signal received")
    collector.stop()
    sys.exit(0)


def main():
    """Main entry point."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start collector in background
    collector_thread = Thread(target=run_collector, daemon=True)
    collector_thread.start()
    
    # Start HTTP server
    port = collector.config.HTTP_SERVER_PORT
    logger.info("Starting HTTP server on 0.0.0.0:%s", port)
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == "__main__":
    main()
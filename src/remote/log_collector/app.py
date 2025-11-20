#!/usr/bin/env python3
"""
Log Collector

1. Consulta a OGS Data Generator (http://ogs-data-generator:5000)
2. Empaqueta datos del OGS + logs propios
3. Expone HTTP API para que Log Processor lo consuma
"""

import sys
import signal
import time
import logging
import requests
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, send_file
from threading import Thread
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
    Collector que:
    1. Consulta a OGS Data Generator
    2. Empaqueta datos + logs
    3. Los guarda para que Log Processor los consuma
    """
    
    def __init__(self):
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
        logger.info(f"Data directory: {self.config.DATA_DIR}")
    
    def fetch_from_ogs(self, endpoint):
        """Consulta al OGS Data Generator."""
        try:
            url = f"{self.config.OGS_PROVIDER_URL}/{endpoint}"
            response = requests.get(url, timeout=self.config.FETCH_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch from OGS {endpoint}: {e}")
            return None
    
    def package_data(self):
        """
        Empaqueta los datos del OGS + logs propios.
        Crea un paquete JSON con toda la información.
        """
        try:
            # Consultar todos los endpoints del OGS
            package = {
                "package_timestamp": datetime.utcnow().isoformat() + "Z",
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
            
            # Guardar paquete
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.config.DATA_DIR}/package_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(package, f, indent=2)
            
            logger.info(f"Package created: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating package: {e}")
            return False
    
    def run(self):
        """Main collection loop."""
        self.running = True
        logger.info("="*60)
        logger.info("Log Collector Started")
        logger.info("="*60)
        logger.info(f"OGS Provider: {self.config.OGS_PROVIDER_URL}")
        logger.info(f"Fetch Interval: {self.config.FETCH_INTERVAL}s")
        logger.info(f"HTTP Server: Port {self.config.HTTP_SERVER_PORT}")
        logger.info("="*60)
        
        # Test connection to OGS
        try:
            response = requests.get(
                f"{self.config.OGS_PROVIDER_URL}/health",
                timeout=5
            )
            logger.info(f"OGS Provider status: {response.json().get('status')}")
        except Exception as e:
            logger.warning(f"Cannot reach OGS Provider: {e}")
        
        # Main loop
        while self.running:
            try:
                if self.package_data():
                    self.stats["total_fetches"] += 1
                else:
                    self.stats["failed_fetches"] += 1
                
                self.stats["last_fetch"] = datetime.utcnow().isoformat() + "Z"
                
                logger.info(
                    f"Fetch #{self.stats['total_fetches']}, "
                    f"Failed: {self.stats['failed_fetches']}"
                )
                
                time.sleep(self.config.FETCH_INTERVAL)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(self.config.FETCH_INTERVAL)
        
        logger.info("Log Collector stopped")
    
    def stop(self):
        """Stop the collector."""
        logger.info("Stopping collector...")
        self.running = False


# Global collector instance
collector = LogCollector()


# ============================================================
# HTTP API para Log Processor
# ============================================================

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
    packages = sorted([f.name for f in data_dir.glob("package_*.json")])
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
        with open(latest, 'r') as f:
            return jsonify(json.load(f))
    
    return jsonify({"error": "No packages available"}), 404


@app.route('/api/packages/<filename>', methods=['GET'])
def get_package(filename):
    """Download a specific package."""
    if not filename.startswith('package_') or not filename.endswith('.json'):
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
    logger.info(f"Starting HTTP server on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == "__main__":
    main()
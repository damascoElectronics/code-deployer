#!/usr/bin/env python3
"""
HTTP Server module for log_collector
Exposes log files via REST API
"""

import json
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread
import config

logger = logging.getLogger('log_collector.http_server')


class LogAPIHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for Log API"""

    def log_message(self, format, *args):
        """Override to use our logger instead of stderr"""
        logger.info("HTTP: {format % args}")

    def do_GET(self):
        """Handle GET requests"""

        if self.path == '/':
            # API info endpoint
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            response = {
                'service': 'Log Collector API',
                'version': '1.0',
                'site_id': config.SITE_ID,
                'endpoints': {
                    '/': 'API information',
                    '/logs': 'List all log files',
                    '/logs/<filename>': 'Download specific log file'
                }
            }
            self.wfile.write(json.dumps(response, indent=2).encode())

        elif self.path == '/logs':
            # List all log files
            try:
                log_path = Path(config.LOG_OUTPUT_DIR)
                log_files = []

                if log_path.exists():
                    for log_file in sorted(log_path.glob('*.log')):
                        stats = log_file.stat()
                        log_files.append({
                            'filename': log_file.name,
                            'size': stats.st_size,
                            'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                            'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                            'download_url': f'/logs/{log_file.name}'
                        })

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()

                response = {
                    'count': len(log_files),
                    'files': log_files
                }
                self.wfile.write(json.dumps(response, indent=2).encode())

            except Exception as e:
                logger.error("Error listing logs: {e}")
                self.send_error(500, f"Error listing logs: {str(e)}")

        elif self.path.startswith('/logs/'):
            # Download specific log file
            filename = self.path[6:]  # Remove '/logs/'
            filepath = Path(config.LOG_OUTPUT_DIR) / filename

            # Security: prevent directory traversal
            try:
                filepath = filepath.resolve()
                if not str(filepath).startswith(str(Path(config.LOG_OUTPUT_DIR).resolve())):
                    self.send_error(403, "Access denied")
                    return
            except Exception:
                self.send_error(400, "Invalid filename")
                return

            if filepath.exists() and filepath.is_file():
                try:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                    self.end_headers()

                    with open(filepath, 'rb') as f:
                        self.wfile.write(f.read())

                    logger.info("Served log file: {filename}")

                except Exception as e:
                    logger.error("Error serving file {filename}: {e}")
                    self.send_error(500, f"Error reading file: {str(e)}")
            else:
                self.send_error(404, "Log file not found")

        else:
            self.send_error(404, "Endpoint not found")


class LogHTTPServer:
    """Manages the HTTP server for serving logs"""

    def __init__(self, host=None, port=None):
        self.host = host or config.HTTP_HOST
        self.port = port or config.HTTP_PORT
        self.server = None
        self.thread = None

    def start(self):
        """Start HTTP server in a separate thread"""
        self.server = HTTPServer((self.host, self.port), LogAPIHandler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        logger.info("HTTP Server started on {self.host}:{self.port}")

    def stop(self):
        """Stop HTTP server"""
        if self.server:
            self.server.shutdown()
            logger.info("HTTP Server stopped")

    def is_running(self):
        """Check if server is running"""
        return self.thread and self.thread.is_alive()

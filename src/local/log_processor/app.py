#!/usr/bin/env python3
"""
Unified Log Processor

Orchestrates multiple data processors:
- KeyPool: Processes quantum key creation logs
- OGS: Processes Optical Ground Station monitoring data
- (Future) Camera: Processes camera feed data
- (Future) Weather: Processes weather station data
"""

import sys
import signal
import logging
from threading import Thread, Event
from config import Config
from processors.keypool_processor import KeyPoolProcessor
from processors.ogs_processor import OGSProcessor

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class UnifiedProcessor:
    """
    Main orchestrator for all data processors.

    Manages multiple independent processors that share the same database.
    Each processor runs in its own thread.
    """

    def __init__(self):
        self.config = Config()
        self.shutdown_event = Event()

        # Initialize processors
        self.processors = {}

        # KeyPool Processor
        if self.config.ENABLE_KEYPOOL:
            logger.info("Initializing KeyPool Processor...")
            self.processors['keypool'] = KeyPoolProcessor(self.config)

        # OGS Processor
        if self.config.ENABLE_OGS:
            logger.info("Initializing OGS Processor...")
            self.processors['ogs'] = OGSProcessor(self.config)

        # Future processors will be added here:
        # if self.config.ENABLE_CAMERA:
        #     self.processors['camera'] = CameraProcessor(self.config)
        # if self.config.ENABLE_WEATHER:
        #     self.processors['weather'] = WeatherProcessor(self.config)

        self.threads = []

    def setup_signal_handlers(self):
        """Setup graceful shutdown on SIGTERM and SIGINT."""
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signal."""
        logger.info("Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_event.set()
        self.stop()

    def start(self):
        """Start all enabled processors."""
        logger.info("="*70)
        logger.info("Unified Log Processor Starting")
        logger.info("="*70)
        logger.info("Database: {self.config.DB_HOST}:{self.config.DB_PORT}/{self.config.DB_NAME}")
        logger.info("Enabled Processors: {', '.join(self.processors.keys())}")
        logger.info("="*70)

        if not self.processors:
            logger.error("No processors enabled! Check configuration.")
            return

        # Start each processor in its own thread
        for name, processor in self.processors.items():
            thread = Thread(
                target=self._run_processor,
                args=(name, processor),
                daemon=True,
                name=f"{name.capitalize()}Thread"
            )
            thread.start()
            self.threads.append(thread)
            logger.info("✓ {name.capitalize()} Processor started")

        logger.info("="*70)
        logger.info("All processors running. Press Ctrl+C to stop.")
        logger.info("="*70)

        # Wait for shutdown signal
        try:
            self.shutdown_event.wait()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()

    def _run_processor(self, name, processor):
        """
        Run a processor with error handling.

        Args:
            name: Processor name for logging
            processor: Processor instance to run
        """
        try:
            processor.run()
        except Exception as e:
            logger.error("{name.capitalize()} Processor crashed: {e}", exc_info=True)
            # Don't crash the whole application if one processor fails

    def stop(self):
        """Stop all processors gracefully."""
        logger.info("Stopping all processors...")

        for name, processor in self.processors.items():
            try:
                processor.stop()
                logger.info("✓ {name.capitalize()} Processor stopped")
            except Exception as e:
                logger.error("Error stopping {name} processor: {e}")

        logger.info("All processors stopped")


def main():
    """Main entry point."""
    app = UnifiedProcessor()
    app.setup_signal_handlers()

    try:
        app.start()
    except Exception as e:
        logger.error("Application error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

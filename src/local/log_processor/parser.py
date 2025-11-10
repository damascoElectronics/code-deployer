#!/usr/bin/env python3
"""
Parser module for log_processor
Handles parsing log files and storing data in database
"""

import os
import re
import logging

logger = logging.getLogger('log_processor.parser')


class LogParser:
    """Parses KeyPool log files and extracts structured data"""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def parse_log_entry(self, line):
        """
        Parse a single log line and extract key information

        Returns:
            dict: Parsed entry with log type and extracted fields,
                  or None if parsing fails
        """
        try:
            parts = line.split()
            if len(parts) < 5:
                return None

            timestamp_str = parts[0]
            site_id = parts[2] if len(parts) > 2 else None

            entry = {
                'timestamp': timestamp_str,
                'site_id': site_id,
                'raw_line': line
            }

            # Parse KEY CREATION
            if 'createKey' in line and 'sequence number' in line:
                entry['log_type'] = 'KEY_CREATION'

                # Extract key identity (UUID)
                identity_match = re.search(
                    r"identity = '([a-f0-9-]{36})'", line
                )
                if identity_match:
                    entry['key_identity'] = identity_match.group(1)

                # Extract sequence number
                seq_match = re.search(r'sequence number (\d+)', line)
                if seq_match:
                    entry['sequence_number'] = int(seq_match.group(1))

                # Extract source site
                source_match = re.search(
                    r"Source site identity = '(\d+)'", line
                )
                if source_match:
                    entry['source_site'] = int(source_match.group(1))

                # Extract destination site
                dest_match = re.search(
                    r"Destination site identity = '(\d+)'", line
                )
                if dest_match:
                    entry['dest_site'] = int(dest_match.group(1))

                # Extract key pool type
                type_match = re.search(
                    r"KeyPoolType name = '(PUBLIC|PRIVATE|SHARED)'", line
                )
                if type_match:
                    entry['key_type'] = type_match.group(1)

            # Parse SYNC LATENCY
            elif 'METRIC_KEY_SYNC_LATENCY' in line:
                entry['log_type'] = 'SYNC_LATENCY'
                ms_match = re.search(r'MS=(\d+)', line)
                if ms_match:
                    entry['latency_ms'] = int(ms_match.group(1))

            # Parse KEY COUNT
            elif 'METRIC_RECEIVED_PUBLIC_KEY_COUNT' in line:
                entry['log_type'] = 'KEY_COUNT'

                bits_match = re.search(r'BITS=(\d+)', line)
                if bits_match:
                    entry['bits'] = int(bits_match.group(1))

                keys_match = re.search(r'KEYS=(\d+)', line)
                if keys_match:
                    entry['keys_count'] = int(keys_match.group(1))

            # Parse CONTROLLER SYNC
            elif 'KeyPoolController' in line and 'remote site' in line:
                entry['log_type'] = 'CONTROLLER_SYNC'

                local_site_match = re.search(r'SiteId: (\d+)', line)
                if local_site_match:
                    entry['local_site'] = int(local_site_match.group(1))

                remote_match = re.search(r'remote site (\d+)', line)
                if remote_match:
                    entry['remote_site'] = int(remote_match.group(1))

            else:
                entry['log_type'] = 'UNKNOWN'

            return entry

        except (ValueError, AttributeError, IndexError) as error:
            logger.error("Error parsing line: %s", error)
            return None

    def process_log_file(self, filepath):
        """
        Process a downloaded log file and store in database

        Returns:
            dict: Statistics about processed file, or None if
                  processing fails
        """
        try:
            filename = os.path.basename(filepath)
            file_size = os.path.getsize(filepath)
            logger.info("Processing %s...", filename)

            stats = {
                'total_lines': 0,
                'key_creations': 0,
                'sync_latency': 0,
                'key_counts': 0,
                'controller_syncs': 0,
                'unknown': 0,
                'db_errors': 0
            }

            with open(filepath, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue

                    stats['total_lines'] += 1
                    entry = self.parse_log_entry(line)

                    if not entry:
                        continue

                    # Store entry in database
                    success = self._store_entry(entry, filename)

                    if success:
                        log_type = entry.get('log_type', 'UNKNOWN')
                        if log_type == 'KEY_CREATION':
                            stats['key_creations'] += 1
                        elif log_type == 'SYNC_LATENCY':
                            stats['sync_latency'] += 1
                        elif log_type == 'KEY_COUNT':
                            stats['key_counts'] += 1
                        elif log_type == 'CONTROLLER_SYNC':
                            stats['controller_syncs'] += 1
                        else:
                            stats['unknown'] += 1
                    elif entry.get('log_type') != 'UNKNOWN':
                        stats['db_errors'] += 1

            # Mark file as processed in database
            self.db_manager.mark_file_processed(
                filename, file_size, stats
            )

            # Log statistics
            self._log_statistics(filename, stats)

            return stats

        except (IOError, OSError) as error:
            logger.error("Error processing file %s: %s", filepath, error)
            return None

    def _store_entry(self, entry, filename):
        """Store a parsed entry in the database"""
        log_type = entry.get('log_type', 'UNKNOWN')

        if log_type == 'KEY_CREATION':
            required_keys = [
                'key_identity', 'sequence_number',
                'source_site', 'dest_site', 'key_type'
            ]
            if all(k in entry for k in required_keys):
                return self.db_manager.insert_key_creation(
                    entry['key_identity'],
                    entry['sequence_number'],
                    entry['source_site'],
                    entry['dest_site'],
                    entry['key_type'],
                    entry['timestamp'],
                    filename
                )

        elif log_type == 'SYNC_LATENCY':
            if 'latency_ms' in entry:
                return self.db_manager.insert_sync_latency(
                    entry['latency_ms'],
                    entry['timestamp'],
                    filename
                )

        elif log_type == 'KEY_COUNT':
            if 'bits' in entry and 'keys_count' in entry:
                return self.db_manager.insert_key_count(
                    entry['bits'],
                    entry['keys_count'],
                    entry['timestamp'],
                    filename
                )

        elif log_type == 'CONTROLLER_SYNC':
            if 'local_site' in entry and 'remote_site' in entry:
                return self.db_manager.insert_controller_sync(
                    entry['local_site'],
                    entry['remote_site'],
                    entry['timestamp'],
                    filename
                )

        return False

    def _log_statistics(self, filename, stats):
        """Log processing statistics"""
        logger.info("✓ Processed %s:", filename)
        logger.info("  Total lines: %s", stats['total_lines'])
        logger.info("  Key creations: %s", stats['key_creations'])
        logger.info("  Sync latency entries: %s", stats['sync_latency'])
        logger.info("  Key count metrics: %s", stats['key_counts'])
        logger.info("  Controller syncs: %s", stats['controller_syncs'])
        if stats['db_errors'] > 0:
            logger.warning("  DB errors: %s", stats['db_errors'])
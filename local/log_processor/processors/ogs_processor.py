"""
OGS Processor

Processes Optical Ground Station monitoring data from remote collector.
"""

import time
import requests
import json
from datetime import datetime
from pathlib import Path
from .base_processor import BaseProcessor


def parse_timestamp(timestamp_str):
    """
    Conviert timestamp ISO (with Z) to format MySQL.
    '2025-11-19T10:49:48Z' -> '2025-11-19 10:49:48'
    '2025-11-19T10:49:48.123456Z' -> '2025-11-19 10:49:48'
    """
    if not timestamp_str:
        return None
    
    # Remove 'Z' and microsegundos if it exists
    timestamp_str = timestamp_str.replace('Z', '')
    # remove microseconds id exist
    if '.' in timestamp_str:
        timestamp_str = timestamp_str.split('.')[0]
    # Replace 'T' with space
    timestamp_str = timestamp_str.replace('T', ' ')
    
    return timestamp_str


class OGSProcessor(BaseProcessor):
    """
    Processes OGS monitoring data.
    
    Fetches data packages from remote log collector and inserts into database.
    """
    
    def __init__(self, config):
        super().__init__(config, "ogs")
        self.processed_packages = set()
        self._setup_directories()
    
    def _setup_directories(self):
        """Create download directory if needed."""
        if self.config.OGS_SAVE_DOWNLOADS:
            Path(self.config.OGS_DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    
    def fetch_latest_package(self):
        """Fetch latest package from remote collector."""
        try:
            url = f"{self.config.OGS_COLLECTOR_URL}/api/packages/latest"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching package: {e}")
            return None
    
    def insert_environment(self, data):
        """Insert environment data into database."""
        if not data:
            return False
        
        if not self.ensure_connection():
            self.logger.error("Cannot insert: no database connection")
            return False

        try:
            
            cursor = self.db_conn.cursor()
            
            query = """
            INSERT INTO ogs_environment_data 
            (timestamp, ogs_id, dome_open, dome_anomaly, temperature, wind_speed, 
             wind_direction, humidity, air_pressure, cloud_cover, precipitation, brightness)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            dome = data.get('dome_status', {})
            weather = data.get('weather', {})
            
            values = (
                parse_timestamp(data.get('timestamp')),
                data.get('ogs_id'),
                dome.get('is_open'),
                dome.get('anomaly_detected'),
                weather.get('temperature_c'),
                weather.get('wind_speed_mps'),
                weather.get('wind_direction_deg'),
                weather.get('humidity_percent'),
                weather.get('air_pressure_hpa'),
                weather.get('cloud_cover_percent'),
                weather.get('precipitation'),
                weather.get('brightness_lux')
            )
            
            cursor.execute(query, values)
            cursor.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error inserting environment: {e}")
            return False
    
    def insert_link(self, data):
        """Insert link status into database."""
        if not data:
            return False
        if not self.ensure_connection():
            self.logger.error("Cannot insert: no database connection")
            return False

        try:
            cursor = self.db_conn.cursor()
            
            query = """
            INSERT INTO ogs_link_data 
            (timestamp, pass_id, quantum_locked, tracking_status, qber, 
             link_power_margin, received_power, uplink_power, 
             fso_uplink_power, fso_downlink_power, fso_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            quantum = data.get('link_status', {}).get('quantum', {})
            fso = data.get('link_status', {}).get('classical_fso', {})
            
            values = (
                parse_timestamp(data.get('timestamp')),
                data.get('pass_id'),
                quantum.get('locked'),
                quantum.get('tracking_status'),
                quantum.get('qber'),
                quantum.get('link_power_margin_dB'),
                quantum.get('received_power_dBm'),
                quantum.get('uplink_power_dBm'),
                fso.get('uplink_power_dBm'),
                fso.get('downlink_power_dBm'),
                fso.get('status')
            )
            
            cursor.execute(query, values)
            cursor.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error inserting link: {e}")
            return False
    
    def insert_summary(self, data):
        """Insert pass summary into database."""
        if not data:
            return False

        if not self.ensure_connection():
            self.logger.error("Cannot insert: no database connection")
            return False
        try:
            cursor = self.db_conn.cursor()
            
            query = """
            INSERT INTO ogs_pass_summary 
            (pass_id, satellite_id, start_time, end_time, total_duration_sec,
             locked_duration_sec, lock_percentage, lost_tracking_events,
             avg_tracking_stability, keys_distilled, key_size_bits,
             key_distillation_success, avg_wind_speed, avg_temperature,
             avg_humidity, precipitation_during_pass, dome_closed_during_pass, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                end_time = VALUES(end_time),
                lock_percentage = VALUES(lock_percentage),
                keys_distilled = VALUES(keys_distilled)
            """
            
            link_lock = data.get('link_lock', {})
            tracking = data.get('tracking_summary', {})
            weather = data.get('weather_conditions', {})
            key_dist = data.get('key_distillation', {})
            
            values = (
                data.get('pass_id'),
                data.get('satellite_id'),
                parse_timestamp(data.get('start_time')),
                parse_timestamp(data.get('end_time')),
                link_lock.get('total_duration_sec'),
                link_lock.get('locked_duration_sec'),
                link_lock.get('lock_percentage'),
                tracking.get('lost_tracking_events'),
                tracking.get('avg_tracking_stability_percent'),
                key_dist.get('keys_distilled'),
                key_dist.get('key_size_bits'),
                key_dist.get('success'),
                weather.get('avg_wind_speed_mps'),
                weather.get('avg_temperature_c'),
                weather.get('avg_humidity_percent'),
                weather.get('precipitation_during_pass'),
                data.get('dome_closed_during_pass'),
                data.get('notes')
            )
            
            cursor.execute(query, values)
            cursor.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error inserting summary: {e}")
            return False
    
    def insert_alerts(self, alerts):
        """Insert alerts into database."""
        if not alerts:
            return True
        
        success = True
        for alert in alerts:
            try:
                cursor = self.db_conn.cursor()
                
                query = """
                INSERT IGNORE INTO ogs_alerts 
                (timestamp, alert_id, severity, severity_code, component,
                 component_id, description, action_taken, related_pass_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    parse_timestamp(alert.get('timestamp')),
                    alert.get('alert_id'),
                    alert.get('severity'),
                    alert.get('severity_code'),
                    alert.get('component'),
                    alert.get('component_id'),
                    alert.get('description'),
                    alert.get('action_taken'),
                    alert.get('related_pass_id')
                )
                
                cursor.execute(query, values)
                self.db_conn.commit()
                cursor.close()
                
            except Exception as e:
                self.logger.error(f"Error inserting alert: {e}")
                self.db_conn.rollback()
                success = False
        
        return success
    
    def process_data(self):
        """Process latest OGS package."""
        package = self.fetch_latest_package()
        
        if not package:
            self.stats["failed"] += 1
            return False
        
        # Check if already processed
        package_id = package.get('package_timestamp')
        if package_id in self.processed_packages:
            return False
        
        # Extract data
        data = package.get('data', {})
        
        # Insert into database
        success = True
        success &= self.insert_environment(data.get('environment'))
        success &= self.insert_link(data.get('link'))
        success &= self.insert_summary(data.get('summary'))
        success &= self.insert_alerts(data.get('alerts', {}).get('alerts', []))
        
        if success:
            self.processed_packages.add(package_id)
            self.stats["total_processed"] += 1
            self.stats["last_process"] = datetime.utcnow().isoformat() + "Z"
            self.logger.info(f"✓ Package processed: {package_id}")
        else:
            self.stats["failed"] += 1
            self.logger.error(f"✗ Failed to process package: {package_id}")
        
        return success
    
    def run(self):
        """Main processing loop."""
        self.running = True
        self.logger.info("="*60)
        self.logger.info("OGS Processor Started")
        self.logger.info(f"Remote Collector: {self.config.OGS_COLLECTOR_URL}")
        self.logger.info(f"Process Interval: {self.config.OGS_PROCESS_INTERVAL}s")
        self.logger.info("="*60)
        
        # Connect to database
        if not self.connect_db():
            self.logger.error("Cannot start without database")
            return
        
        # Main loop
        while self.running:
            try:
                self.process_data()
                
                self.logger.debug(
                    f"Stats - Processed: {self.stats['total_processed']}, "
                    f"Failed: {self.stats['failed']}"
                )
                
                time.sleep(self.config.OGS_PROCESS_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(self.config.OGS_PROCESS_INTERVAL)
        
        self.disconnect_db()
        self.logger.info("OGS Processor stopped")
     
     
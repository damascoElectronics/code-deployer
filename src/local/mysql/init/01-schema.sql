-- Database schema for KeyPool log processing system and OGS Monitoring system
-- Drop database if exists (CAUTION: use only in development)
-- DROP DATABASE IF EXISTS keypool_logs;

CREATE DATABASE IF NOT EXISTS keypool_logs CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE keypool_logs;

-- Table for individual key creation events
CREATE TABLE IF NOT EXISTS key_creations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_identity VARCHAR(36) NOT NULL UNIQUE,  -- UUID format (32 chars + 4 dashes)
    sequence_number INT NOT NULL,
    source_site_id INT NOT NULL,
    destination_site_id INT NOT NULL,
    key_pool_type ENUM('PUBLIC', 'PRIVATE', 'SHARED') NOT NULL,
    timestamp DATETIME(6) NOT NULL,
    log_file VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_key_identity (key_identity),
    INDEX idx_sequence (sequence_number),
    INDEX idx_timestamp (timestamp),
    INDEX idx_source_site (source_site_id),
    INDEX idx_dest_site (destination_site_id),
    INDEX idx_key_type (key_pool_type)
) ENGINE=InnoDB;

-- Table for sync latency metrics
CREATE TABLE IF NOT EXISTS sync_latency_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    latency_ms INT NOT NULL,
    timestamp DATETIME(6) NOT NULL,
    log_file VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_latency (latency_ms)
) ENGINE=InnoDB;

-- Table for key count metrics
CREATE TABLE IF NOT EXISTS key_count_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bits INT NOT NULL,
    keys_count INT NOT NULL,
    timestamp DATETIME(6) NOT NULL,
    log_file VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_keys_count (keys_count)
) ENGINE=InnoDB;

-- Table for controller sync events
CREATE TABLE IF NOT EXISTS controller_syncs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    local_site_id INT NOT NULL,
    remote_site_id INT NOT NULL,
    timestamp DATETIME(6) NOT NULL,
    log_file VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_remote_site (remote_site_id)
) ENGINE=InnoDB;

-- Table for processed log files tracking
CREATE TABLE IF NOT EXISTS processed_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL UNIQUE,
    file_size BIGINT,
    total_lines INT DEFAULT 0,
    key_creations_count INT DEFAULT 0,
    sync_latency_count INT DEFAULT 0,
    key_count_count INT DEFAULT 0,
    controller_sync_count INT DEFAULT 0,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_filename (filename),
    INDEX idx_processed_at (processed_at)
) ENGINE=InnoDB;

-- OGS MONITORING TABLES (New)
-- Environment Data Table
-- Stores weather and dome status information from OGS
CREATE TABLE IF NOT EXISTS ogs_environment_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    ogs_id VARCHAR(50) NOT NULL,
    dome_open BOOLEAN,
    dome_anomaly BOOLEAN,
    temperature FLOAT COMMENT 'Temperature in Celsius',
    wind_speed FLOAT COMMENT 'Wind speed in m/s',
    wind_direction INT COMMENT 'Wind direction in degrees',
    humidity FLOAT COMMENT 'Humidity percentage',
    air_pressure FLOAT COMMENT 'Air pressure in hPa',
    cloud_cover INT COMMENT 'Cloud cover percentage',
    precipitation BOOLEAN,
    brightness INT COMMENT 'Brightness in lux',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_ogs_id (ogs_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB COMMENT='OGS environmental conditions and dome status';

-- Link Status Data Table
-- Stores quantum and classical FSO link telemetry
CREATE TABLE IF NOT EXISTS ogs_link_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    pass_id VARCHAR(100),
    quantum_locked BOOLEAN COMMENT 'Quantum link locked status',
    tracking_status VARCHAR(50) COMMENT 'TRACKING, LOST, or LOCKED',
    qber FLOAT COMMENT 'Quantum Bit Error Rate',
    link_power_margin FLOAT COMMENT 'Link power margin in dB',
    received_power FLOAT COMMENT 'Received power in dBm',
    uplink_power FLOAT COMMENT 'Uplink power in dBm',
    fso_uplink_power FLOAT COMMENT 'FSO uplink power in dBm',
    fso_downlink_power FLOAT COMMENT 'FSO downlink power in dBm',
    fso_status VARCHAR(50) COMMENT 'FSO link status',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_pass_id (pass_id),
    INDEX idx_tracking_status (tracking_status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB COMMENT='OGS quantum and classical link telemetry';

-- Pass Summary Table
-- Stores satellite pass performance summaries
CREATE TABLE IF NOT EXISTS ogs_pass_summary (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    pass_id VARCHAR(100) UNIQUE NOT NULL,
    satellite_id VARCHAR(50),
    start_time DATETIME,
    end_time DATETIME,
    total_duration_sec INT,
    locked_duration_sec INT,
    lock_percentage FLOAT,
    lost_tracking_events INT,
    avg_tracking_stability FLOAT,
    keys_distilled INT COMMENT 'Number of quantum keys generated',
    key_size_bits INT COMMENT 'Size of each key in bits',
    key_distillation_success BOOLEAN,
    avg_wind_speed FLOAT,
    avg_temperature FLOAT,
    avg_humidity FLOAT,
    precipitation_during_pass BOOLEAN,
    dome_closed_during_pass BOOLEAN,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_pass_id (pass_id),
    INDEX idx_satellite_id (satellite_id),
    INDEX idx_start_time (start_time),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB COMMENT='OGS satellite pass performance summaries';

-- Alerts Table
-- Stores OGS system alerts and anomalies
CREATE TABLE IF NOT EXISTS ogs_alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    alert_id VARCHAR(100) UNIQUE,
    severity VARCHAR(20) COMMENT 'warning, critical, etc.',
    severity_code INT,
    component VARCHAR(100) COMMENT 'Component that generated alert',
    component_id VARCHAR(50),
    description TEXT,
    action_taken TEXT,
    related_pass_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_alert_id (alert_id),
    INDEX idx_severity (severity),
    INDEX idx_component (component),
    INDEX idx_related_pass_id (related_pass_id),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (related_pass_id) REFERENCES ogs_pass_summary(pass_id) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='OGS system alerts and anomalies';

-- Schedule Table
-- Stores upcoming satellite pass schedules
CREATE TABLE IF NOT EXISTS ogs_pass_schedule (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    pass_id VARCHAR(100) UNIQUE NOT NULL,
    satellite_id VARCHAR(50),
    ogs_id VARCHAR(50),
    start_time DATETIME,
    end_time DATETIME,
    max_elevation FLOAT COMMENT 'Maximum elevation in degrees',
    predicted_wind_speed FLOAT,
    predicted_precipitation BOOLEAN,
    predicted_cloud_cover INT,
    estimated_qber FLOAT,
    estimated_keys INT,
    pass_viable BOOLEAN,
    generated_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_pass_id (pass_id),
    INDEX idx_satellite_id (satellite_id),
    INDEX idx_ogs_id (ogs_id),
    INDEX idx_start_time (start_time),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB COMMENT='OGS upcoming satellite pass schedules';

-- Processed Packages Table
-- Tracks which OGS packages have been processed (avoid duplicates)
CREATE TABLE IF NOT EXISTS ogs_processed_packages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    package_timestamp VARCHAR(100) UNIQUE NOT NULL,
    collector_id VARCHAR(50),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    records_inserted INT DEFAULT 0,
    INDEX idx_package_timestamp (package_timestamp),
    INDEX idx_processed_at (processed_at)
) ENGINE=InnoDB COMMENT='Tracking of processed OGS data packages';

-- KEYPOOL VIEWS (Existing - unchanged)
-- View for summary statistics
CREATE OR REPLACE VIEW key_creation_summary AS
SELECT 
    key_pool_type,
    source_site_id,
    destination_site_id,
    COUNT(*) as total_keys,
    MIN(timestamp) as first_key,
    MAX(timestamp) as last_key,
    DATE(timestamp) as date
FROM key_creations
GROUP BY key_pool_type, source_site_id, destination_site_id, DATE(timestamp);

-- View for latency statistics
CREATE OR REPLACE VIEW latency_stats AS
SELECT 
    DATE(timestamp) as date,
    AVG(latency_ms) as avg_latency,
    MIN(latency_ms) as min_latency,
    MAX(latency_ms) as max_latency,
    COUNT(*) as measurement_count
FROM sync_latency_metrics
GROUP BY DATE(timestamp);

-- View for daily key production
CREATE OR REPLACE VIEW daily_key_production AS
SELECT 
    DATE(timestamp) as date,
    key_pool_type,
    COUNT(*) as keys_produced,
    MIN(sequence_number) as first_sequence,
    MAX(sequence_number) as last_sequence
FROM key_creations
GROUP BY DATE(timestamp), key_pool_type
ORDER BY date DESC, key_pool_type;
-- OGS VIEWS (New)
-- Latest environment conditions
CREATE OR REPLACE VIEW ogs_v_latest_environment AS
SELECT 
    timestamp,
    ogs_id,
    dome_open,
    temperature,
    wind_speed,
    humidity,
    cloud_cover,
    precipitation
FROM ogs_environment_data
ORDER BY timestamp DESC
LIMIT 100;

-- Latest link status
CREATE OR REPLACE VIEW ogs_v_latest_link AS
SELECT 
    timestamp,
    pass_id,
    quantum_locked,
    tracking_status,
    qber,
    link_power_margin,
    received_power
FROM ogs_link_data
ORDER BY timestamp DESC
LIMIT 100;

-- Recent passes with key statistics
CREATE OR REPLACE VIEW ogs_v_recent_passes AS
SELECT 
    pass_id,
    satellite_id,
    start_time,
    end_time,
    lock_percentage,
    keys_distilled,
    key_size_bits,
    notes
FROM ogs_pass_summary
ORDER BY start_time DESC
LIMIT 50;

-- Active alerts (last 24 hours)
CREATE OR REPLACE VIEW ogs_v_active_alerts AS
SELECT 
    timestamp,
    severity,
    component,
    description,
    action_taken
FROM ogs_alerts
WHERE timestamp > DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY timestamp DESC;

-- Database User Permissions
GRANT ALL PRIVILEGES ON keypool_logs.* TO 'ogs_user'@'%';
FLUSH PRIVILEGES;

-- Show all tables
SHOW TABLES;
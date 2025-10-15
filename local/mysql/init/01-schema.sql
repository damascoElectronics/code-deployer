-- Database schema for KeyPool log processing system
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
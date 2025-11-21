#!/usr/bin/env python3
"""
OGS Data Generator - External Provider Simulator

Simulates an external OGS data provider service.
Generates synthetic monitoring data and exposes it via HTTP endpoints.
"""

import json
import random
import time
import uuid
import signal
import sys
import threading
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
config = Config()

# Global data storage
current_data = {
    "environment": {},
    "link": {},
    "summary": {},
    "alerts": [],
    "schedule": {}
}
data_lock = threading.Lock()


def now():
    """Return current UTC timestamp in ISO format."""
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def randfloat(base, variance):
    """Generate random float with variance."""
    return round(base + random.uniform(-variance, variance), 2)


def randint(base, variance):
    """Generate random integer with variance."""
    return base + random.randint(-variance, variance)


def generate_environment_status():
    """Generate current environment status data."""
    return {
        "timestamp": now(),
        "ogs_id": config.OGS_ID,
        "dome_status": {
            "is_open": random.choice([True, True, True, False]),
            "last_opened": (datetime.utcnow() - timedelta(
                minutes=random.randint(0, 15)
            )).isoformat() + "Z",
            "anomaly_detected": random.choice([False, False, False, True])
        },
        "weather": {
            "wind_speed_mps": randfloat(3.5, 1.5),
            "wind_direction_deg": randint(0, 180),
            "brightness_lux": randint(25000, 15000),
            "precipitation": random.random() < 0.1,
            "temperature_c": randfloat(20, 5),
            "humidity_percent": randfloat(45, 15),
            "air_pressure_hpa": randfloat(1012, 5),
            "cloud_cover_percent": randint(10, 40),
            "source_station": "weather_station_1"
        }
    }


def generate_link_status(pass_id):
    """Generate current quantum and classical link status."""
    qber = max(0.005, random.gauss(0.015, 0.005))

    return {
        "timestamp": now(),
        "pass_id": pass_id,
        "link_status": {
            "quantum": {
                "locked": random.random() > 0.05,
                "tracking_status": random.choice(["TRACKING", "LOST", "LOCKED"]),
                "qber": round(qber, 4),
                "link_power_margin_dB": randfloat(3.0, 0.8),
                "received_power_dBm": randfloat(-43.5, 1.5),
                "uplink_power_dBm": randfloat(-42.0, 1.2)
            },
            "classical_fso": {
                "uplink_power_dBm": randfloat(-10.5, 1.0),
                "downlink_power_dBm": randfloat(-11.2, 1.0),
                "status": random.choice(["active", "active", "active", "idle"])
            }
        }
    }


def generate_pass_summary(pass_id):
    """Generate satellite pass summary."""
    lock_percentage = randfloat(95, 3)

    return {
        "pass_id": pass_id,
        "satellite_id": config.SATELLITE_ID,
        "start_time": (datetime.utcnow() - timedelta(
            minutes=15
        )).isoformat() + "Z",
        "end_time": now(),
        "link_lock": {
            "total_duration_sec": 900,
            "locked_duration_sec": int(900 * lock_percentage / 100),
            "lock_percentage": lock_percentage
        },
        "tracking_summary": {
            "lost_tracking_events": random.randint(0, 3),
            "avg_tracking_stability_percent": randfloat(97, 2)
        },
        "weather_conditions": {
            "avg_wind_speed_mps": randfloat(4.5, 1.0),
            "avg_temperature_c": randfloat(22, 3),
            "avg_humidity_percent": randfloat(50, 10),
            "precipitation_during_pass": random.random() < 0.1,
            "cloud_cover_percent": randint(10, 30)
        },
        "dome_closed_during_pass": random.random() < 0.05,
        "key_distillation": {
            "keys_distilled": random.randint(100, 130),
            "key_size_bits": random.choice([128, 256, 512]),
            "success": True
        },
        "anomalies_detected": [],
        "notes": random.choice([
            "Nominal pass. Weather stable.",
            "Minor QBER fluctuations detected.",
            "Slight dome closure delay, no impact.",
            "Excellent link quality observed."
        ])
    }


def generate_alert(pass_id):
    """Generate system alert based on conditions."""
    if random.random() > 0.85:
        return {
            "timestamp": now(),
            "alert_id": str(uuid.uuid4()),
            "severity": random.choice(["warning", "critical"]),
            "severity_code": random.choice([2, 3]),
            "component": random.choice([
                "weather_monitoring",
                "link_tracking",
                "dome_control"
            ]),
            "component_id": f"SCU-{random.randint(1, 3):02d}",
            "description": random.choice([
                "Precipitation detected during satellite pass. Dome closed automatically.",
                "Lost tracking lock, attempting recovery.",
                "High QBER detected, monitoring subsystem notified."
            ]),
            "action_taken": random.choice([
                "Dome closed automatically.",
                "System initiated re-tracking sequence.",
                "Alert logged, operator notified."
            ]),
            "related_pass_id": pass_id
        }
    return None


def generate_pass_schedule():
    """Generate upcoming satellite pass schedule."""
    start = datetime.utcnow() + timedelta(minutes=10)
    end = start + timedelta(minutes=15)

    return {
        "generated_at": now(),
        "ogs_id": config.OGS_ID,
        "scheduled_passes": [{
            "pass_id": f"pass-{start.strftime('%Y%m%d-%H%M%S')}",
            "satellite_id": config.SATELLITE_ID,
            "start_time": start.isoformat() + "Z",
            "end_time": end.isoformat() + "Z",
            "max_elevation_deg": randfloat(70, 10),
            "predicted_weather": {
                "wind_speed_mps": randfloat(4, 1),
                "precipitation": random.random() < 0.1,
                "cloud_cover_percent": randint(5, 20)
            },
            "estimated_qber": round(random.gauss(0.015, 0.004), 4),
            "estimated_keys": random.randint(110, 130),
            "pass_viable": True
        }]
    }


def update_data():
    """Background thread to update data periodically."""
    schedule = generate_pass_schedule()
    pass_id = schedule["scheduled_passes"][0]["pass_id"]

    while True:
        try:
            with data_lock:
                current_data["environment"] = generate_environment_status()
                current_data["link"] = generate_link_status(pass_id)
                current_data["summary"] = generate_pass_summary(pass_id)
                current_data["schedule"] = schedule

                alert = generate_alert(pass_id)
                if alert:
                    current_data["alerts"].insert(0, alert)
                    current_data["alerts"] = current_data["alerts"][:10]

            time.sleep(config.UPDATE_INTERVAL)
        except Exception as e:
            logger.error("Error updating data: {e}", exc_info=True)
            time.sleep(config.UPDATE_INTERVAL)


# HTTP Endpoints
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": now(),
        "ogs_id": config.OGS_ID,
        "service": "OGS Data Generator"
    })


@app.route('/api/environment', methods=['GET'])
def get_environment():
    """Get current environment status."""
    with data_lock:
        return jsonify(current_data["environment"])


@app.route('/api/link', methods=['GET'])
def get_link():
    """Get current link status."""
    with data_lock:
        return jsonify(current_data["link"])


@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Get pass summary."""
    with data_lock:
        return jsonify(current_data["summary"])


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get recent alerts."""
    with data_lock:
        return jsonify({
            "alerts": current_data["alerts"],
            "count": len(current_data["alerts"])
        })


@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    """Get satellite pass schedule."""
    with data_lock:
        return jsonify(current_data["schedule"])


@app.route('/api/all', methods=['GET'])
def get_all():
    """Get all data in one request."""
    with data_lock:
        return jsonify({
            "timestamp": now(),
            "environment": current_data["environment"],
            "link": current_data["link"],
            "summary": current_data["summary"],
            "alerts": current_data["alerts"],
            "schedule": current_data["schedule"]
        })


def signal_handler(_sig, _frame):
    """Handle shutdown signals."""
    logger.info("Shutdown signal received, stopping...")
    sys.exit(0)


def main():
    """Main entry point."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("="*60)
    logger.info("OGS Data Generator - External Provider Simulator")
    logger.info("="*60)
    logger.info("OGS ID: {config.OGS_ID}")
    logger.info("Satellite ID: {config.SATELLITE_ID}")
    logger.info("Port: {config.PORT}")
    logger.info("Update Interval: {config.UPDATE_INTERVAL}s")
    logger.info("="*60)

    # Start background data updater
    updater_thread = threading.Thread(target=update_data, daemon=True)
    updater_thread.start()
    logger.info("Data updater started")

    # Start Flask server
    logger.info("Starting HTTP server on {config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=False)


if __name__ == "__main__":
    main()

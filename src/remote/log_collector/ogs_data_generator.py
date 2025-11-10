#!/usr/bin/env python3
import json
import random
import time
import uuid
from datetime import datetime, timedelta

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
OGS_ID = "OGS-001"
SATELLITE_ID = "SAT-Alpha-01"
OUTPUT_DIR = "./synthetic_data"
PRINT_ONLY = False  # If False, will save to JSON files
UPDATE_INTERVAL = 5  # seconds between updates

# ---------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------
def now():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def randfloat(base, variance):
    return round(base + random.uniform(-variance, variance), 2)

def randint(base, variance):
    return base + random.randint(-variance, variance)

def save_json(filename, data):
    if PRINT_ONLY:
        print(f"\n--- {filename} ---")
        print(json.dumps(data, indent=2))
    else:
        with open(f"{OUTPUT_DIR}/{filename}", "w") as f:
            json.dump(data, f, indent=2)

# ---------------------------------------------------------
# Payload Generators
# ---------------------------------------------------------
def generate_environment_status():
    return {
        "timestamp": now(),
        "ogs_id": OGS_ID,
        "dome_status": {
            "is_open": random.choice([True, True, True, False]),
            "last_opened": (datetime.utcnow() - timedelta(minutes=random.randint(0, 15))).isoformat() + "Z",
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
    lock_percentage = randfloat(95, 3)
    return {
        "pass_id": pass_id,
        "satellite_id": SATELLITE_ID,
        "start_time": (datetime.utcnow() - timedelta(minutes=15)).isoformat() + "Z",
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

def generate_alerts(pass_id):
    if random.random() > 0.85:
        alert = {
            "timestamp": now(),
            "alert_id": str(uuid.uuid4()),
            "severity": random.choice(["warning", "critical"]),
            "severity_code": random.choice([2, 3]),
            "component": random.choice(["weather_monitoring", "link_tracking", "dome_control"]),
            "component_id": f"SCU-{random.randint(1,3):02d}",
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
        return alert
    return None

def generate_pass_schedule():
    start = datetime.utcnow() + timedelta(minutes=10)
    end = start + timedelta(minutes=15)
    return {
        "generated_at": now(),
        "ogs_id": OGS_ID,
        "scheduled_passes": [{
            "pass_id": f"pass-{start.strftime('%Y%m%d-%H%M%S')}",
            "satellite_id": SATELLITE_ID,
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

# ---------------------------------------------------------
# Main simulation loop
# ---------------------------------------------------------
def main():
    schedule = generate_pass_schedule()
    pass_id = schedule["scheduled_passes"][0]["pass_id"]

    while True:
        env = generate_environment_status()
        link = generate_link_status(pass_id)
        summary = generate_pass_summary(pass_id)
        alert = generate_alerts(pass_id)

        save_json("environment_status.json", env)
        save_json("link_status.json", link)
        save_json("pass_summary.json", summary)
        if alert:
            save_json("alerts.json", alert)
        save_json("satellite_pass_schedule.json", schedule)

        time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    main()

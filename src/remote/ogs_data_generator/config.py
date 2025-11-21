#!/usr/bin/env python3
"""Configuration for OGS Data Generator.

This module defines configuration settings for the OGS
data provider simulator.
"""
import os


class Config:
    """Configuration for OGS data provider simulator."""

    # OGS identification
    OGS_ID = os.getenv("OGS_ID", "OGS-001")
    SATELLITE_ID = os.getenv("SATELLITE_ID", "SAT-Alpha-01")

    # Server configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))

    # Data generation
    UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", "5"))

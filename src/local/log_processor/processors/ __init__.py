"""
Processors package

Contains all data processors:
- KeyPoolProcessor: Quantum key creation logs
- OGSProcessor: Optical Ground Station monitoring
- (Future) CameraProcessor: Camera feed processing
- (Future) WeatherProcessor: Weather data processing
"""

from .keypool_processor import KeyPoolProcessor
from .ogs_processor import OGSProcessor

__all__ = ['KeyPoolProcessor', 'OGSProcessor']

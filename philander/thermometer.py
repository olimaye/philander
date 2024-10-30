"""Abstract interface for temperature sensors accessible via serial communication.

Provide an API to abstract from temperature measurement devices.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Data", ]

from .penum import dataclass

from .primitives import PreciseTemperature


@dataclass
class Data:
    """Container type to wrap a thermometer's primary measurement result.
    
    Measurement data should always be expressed as a signed value in
    degree Celsius.
    """
    temperature:  PreciseTemperature

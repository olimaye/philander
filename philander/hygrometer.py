"""Abstract interface for humidity sensors accessible via serial communication.

Provide an API to abstract from relative humidity measurement devices.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Data",]
from dataclasses import dataclass

from .primitives import Percentage


@dataclass
class Data:
    """Container type to wrap a hygrometer's primary measurement result.
    
    Measurement data should always be expressed as percentage.
    """
    humidity:  Percentage

"""Abstract interface for pressure sensors accessible via serial communication.

Provide an API to abstract from pressure measurement devices.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Data",]

from .penum import dataclass

from .primitives import Pressure


@dataclass
class Data:
    """Container type to wrap a pressure gauge's primary measurement result.
    
    Measurement data should always be expressed in Pascal [Pa].
    Remember that 1 Pa = 1 N / m^2
    """
    pressure:  Pressure = Pressure.invalid

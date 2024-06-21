# -*- coding: utf-8 -*-
"""A module to provide a base class for potentiometer driver implementations.
"""
__author__ = "Carl Bellgardt"
__version__ = "0.1"
__all__ = []

from .primitives import Voltage, Percentage
from .systypes import ErrorCode, Info
from .module import Module

class Potentiometer( Module ):
    """Generic digital potentiometer driver class.

    A digital potentiometer is able to adjust a resistance divider's wiper by sending a resistance value to set digitalky, e.g. using I2C.\
    It can be used as a variable resistor or for more complex things. Depending on the specific ship it can feature different terminals\
    to make use of it's resistance divider functionality.
    """
    
    DEFAULT_RESISTANCE_MAX = 10000
    DEFAULT_RESOLUTION = 7
    
    @classmethod
    def Params_init(cls, paramDict):
        """Initializes configuration parameters with defaults.
        
        The following settings are supported:
        
        =============================    =====================================================================================================
        Key name                         Value type, meaning and default
        =============================    =====================================================================================================
        Potentiometer.resistance.max     ``int``; Maximum resistance in Ohm; :attr:`DEFAULT_RESISTANCE_MAX`.
        Potentiometer.resolution         ``int``; Number of bits used to set resistance value.
        ======================================================================================================================================
        """
        defaults = {
            "Potentiometer.resistance.max": Potentiometer.DEFAULT_RESISTANCE_MAX,
            "Potentiometer.resolution": Potentiometer.DEFAULT_RESOLUTION
        }
        defaults.update(paramDict)
        paramDict = defaults
        return None
    
    def open(self, paramDict):
        """Initialize an instance and prepare it for use.

        Also see: :meth:`.Module.open`.
        
        :param dict(str, object) paramDict: Configuration parameters as\
        possibly obtained from :meth:`Params_init`.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return NotImplementedError
        
    def close(self, paramDict):
        """Close this instance and release hardware resources.
        
        Also see: :meth:`.Module.close`.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return NotImplementedError
    
    def _digitalize_resistance_value(value, isAbsolute=False, max_resistance=None, isDigital=False, resolution=None):
        """Converts an either digital, absolute or relative resistance value into a digital value. It also checks for it's validity.

        Also see: :meth:`.potentiometer._eval_resistance_value`.
        
        :param int value: Resistance value, interpreted as percentage (0 to 100) by default.\
        Will be inpreted as absolute resistance in ohms, if isAbsolute is set true.
        :param bool isAbsolute: Set true if value is in ohms.
        :return: An error code indicating either success or the reason of failure.
        :rtype: int
        """
        Potentiometer._eval_resistance_value(value, isAbsolute, max_resistance, isDigital, resolution)
        pot_steps = 2 ** resolution # number of available steps, dependent on number of bits for resolution
        if isAbsolute:
            return round((value / max_resistance) * (pot_steps - 1))
        elif isDigital:
            return value
        else:
            return round((value / 100) * (pot_steps - 1))
    
    def _eval_resistance_value(value, isAbsolute=False, max_resistance=None, isDigital=False, resolution=None):
        """Evaluate values given to set method. Raises error if values are invalid (e.g. over 100% or over maximum resistance).
        
        :param int value: Resistance value, interpreted as percentage (0 to 100) by default.\
        Will be inpreted as absolute resistance in ohms, if isAbsolute is set true.
        :param bool isAbsolute: Set true if value is in ohms.
        :return: An error code indicating either success or the reason of failure.
        :rtype: None
        """
        if isAbsolute and (value < 0 or value > max_resistance):
            print(f"Given absolute resistance value was {value} ohm must be between 0 ohm and the given maximum ({max_resistance} is currently set)")
            raise ValueError
        elif isDigital and (value < 0 or value >= (2**resolution)):
            print(f"Digital value must be between 0 and the given resolution (currently {resolution} bit -> {2**resolution}).")
            raise ValueError
        elif not isAbsolute and not isDigital and (value < 0 or value > 100):
            print("Percentage value must be between 0 and 100.")
            raise ValueError
        return None
    
    def set(self, value, isAbsolute=False):
        """Set resistance of potentiometer to a relative (percentage) or absolute (ohms) value.
        
        :param int value: Resistance value, interpreted as percentage (0 to 100) by default.\
        Will be inpreted as absolute resistance in ohms, if isAbsolute is set true.
        :param bool isAbsolute: Set true if value is in ohms.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        self.__eval_resistance_value(value, isAbsolute, max_resistance)
        return NotImplementedError
        
        
            
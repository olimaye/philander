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
    DEFAULT_RESOLUTION = 128
    
    @classmethod
    def Params_init(cls, paramDict):
        """Initializes configuration parameters with defaults.
        
        The following settings are supported:
        
        =============================    =====================================================================================================
        Key name                         Value type, meaning and default
        =============================    =====================================================================================================
        Potentiometer.resistance.max     ``int``; Maximum resistance in Ohm; :attr:`DEFAULT_RESISTANCE_MAX`.
        Potentiometer.resolution         ``int``; Number of possible steps to set resistance value to (2^(bits used for resistance)). :attr:`DEFAULT_RESOLUTION`.
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
    
    def _digitalize_resistance_value(percentage=None, absolute=None, digital=None, resolution=None, max_resistance=None): 
        """Converts an either digital, absolute or relative resistance value into a digital value. It also checks for it's validity.\
        There must only be one out of the parameters percentage, absolute and digital given.
        
        Also see: :meth:`.potentiometer._eval_resistance_value`.
        
        :param percentage percentage: Resistance value, interpreted as percentage (0 to 100) by default.
        :param int absolute: Resistance value in Ohms. Must be between 0 and the set maximum value.
        :param int digital: Digital resistance value to be sent directly to the potentiometer without conversion.
        :param int resolution: Number of possible steps to set resistance value to (2^(bits used for resistance)).
        :param int max_resistance: Maximum resistance of Potentiometer in Ohm.
        :return: An error code indicating either success or the reason of failure.
        :rtype: None
        """
        err = Potentiometer._eval_resistance_value(percentage, absolute, digital, resolution, max_resistance)
        if err:
            return None, err
        elif percentage != None:
            val = resolution * percentage // 100
            return min(val, resolution-1), err
        elif absolute != None:
            val = resolution * percentage // max_resistance
            return min(val, resolution-1), err
        elif digital != None:
            return digital, err
        return None, Exception("What happened here?")
    
    def _eval_resistance_value(percentage=None, absolute=None, digital=None, resolution=None, max_resistance=None):
        """Evaluate values given to set method. Raises error if values are invalid (e.g. over 100% or over maximum resistance).\
        There must only be one out of the parameters percentage, absolute and digital given.

        :param percentage percentage: Resistance value, interpreted as percentage (0 to 100) by default.
        :param int absolute: Resistance value in Ohms. Must be between 0 and the set maximum value.
        :param int digital: Digital resistance value to be sent directly to the potentiometer without conversion.
        :param int resolution: Number of possible steps to set resistance value to (2^(bits used for resistance)).
        :param int max_resistance: Maximum resistance of Potentiometer in Ohm.
        :return: An error code indicating either success or the reason of failure.
        :rtype: None
        """
        if (percentage != None) ^ bool(absolute != None) ^ bool(digital != None): # check if exactly one parameter is given
            if percentage and (percentage < 0 or percentage > 100):
                raise ValueError("Percentage value must be between 0 and 100.")
            elif absolute and (absolute < 0 or absolute > max_resistance):
                raise ValueError(f"Given absolute resistance value was {value} ohm must be between 0 ohm and the given maximum ({max_resistance} is currently set)")
            elif digital and (digital < 0 or digital >= (resolution-1)):
                raise ValueError(f"Digital value must be between 0 and the given resolution.")
            return None
        else:
            return ValueError("There must only be one parameter given.")
    
    def set(self, percentage=None, absolute=None, digital=None):
        """Set resistance of potentiometer to a relative (percentage), absolute (ohms), or digital value.\
        There must only be one parameter given. When implementing this method,\
        consider using :meth:`.potentiometer._eval_resistance_value`. 
        
        :param percentage percentage: Resistance value, interpreted as percentage (0 to 100) by default.
        :param int absolute: Resistance value in Ohms. Must be between 0 and the set maximum value.
        :param int digital: Digital resistance value to be sent directly to the potentiometer without conversion.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        self.__eval_resistance_value(value, isAbsolute, max_resistance)
        return NotImplementedError
    
    def get(self, asPercentage=True, asAbsolute=False, asDigital=False):
        """Get current resistance setting of potentiometer as ative (percentage), absolute (ohms), or digital value.\
        There must only be one parameter set to true.
        
        :param bool asPercentage: Set true to convert value into a relative percent value. (default).
        :param bool asAblsolute: Set true to convert value into ohms. False for a percentage value (default).
        :param bool asDigital: Set true to return value as digital value.
        :return: The resistance value and an error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return NotImplementedError
        
        
            
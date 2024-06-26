# -*- coding: utf-8 -*-
"""A module to provide a base class for potentiometer driver implementations.
"""
__author__ = "Carl Bellgardt"
__version__ = "0.1"
__all__ = []

from .primitives import Percentage
from .systypes import ErrorCode
from .module import Module

class Potentiometer( Module ):
    """Generic digital potentiometer driver class.

    A digital potentiometer is able to adjust a resistance divider's wiper to a received value, e.g. using I2C.\
    It can be used as a variable resistor or for more complex things. Depending on the specific chip it can feature different terminals\
    to make use of it's resistance divider functionality. The resistance is generally defined as the relative resistance between ground and the wiper.\
    To comply with this standard, some implementations may need to invert the given value before sending it out.
    """
    
    DEFAULT_RESISTANCE_MAX = 10000
    DEFAULT_digital_max = 128
    
    @classmethod
    def Params_init(cls, paramDict):
        """Initializes configuration parameters with defaults.
        
        The following settings are supported:
        
        =============================    =====================================================================================================
        Key name                         Value type, meaning and default
        =============================    =====================================================================================================
        Potentiometer.resistance.max     ``int`` Maximum resistance in Ohm; :attr:`DEFAULT_RESISTANCE_MAX`.
        Potentiometer.digital_max        ``int`` Number of possible steps to set resistance value to (2^(bits used for resistance)). :attr:`DEFAULT_digital_max`.
        ======================================================================================================================================
        """
        defaults = {
            "Potentiometer.resistance.max": Potentiometer.DEFAULT_RESISTANCE_MAX,
            "Potentiometer.digital_max": Potentiometer.DEFAULT_digital_max
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
        return ErrorCode.errNotImplemented
        
    def close(self, paramDict):
        """Close this instance and release hardware resources.
        
        Also see: :meth:`.Module.close`.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return ErrorCode.errNotImplemented
    
    def _digitalize_resistance_value(percentage=None, absolute=None, digital=None, digital_max=None, max_resistance=None): 
        """Converts an either digital, absolute or relative resistance value into a digital value. It also checks for it's validity.\
        There must only be one out of the parameters percentage, absolute and digital given.
        
        Also see: :meth:`.potentiometer._eval_resistance_value`.
        
        :param percentage percentage: Resistance value, interpreted as percentage (0 to 100) by default.
        :param int absolute: Resistance value in Ohms. Must be between 0 and the set maximum value.
        :param int digital: Digital resistance value to be sent directly to the potentiometer without conversion.
        :param int digital_max: Number of possible steps to set resistance value to (2^(bits used for resistance)).
        :param int max_resistance: Maximum resistance of Potentiometer in Ohm.
        :return: An error code indicating either success or the reason of failure.
        :rtype: Tuple(value, ErrorCode)
        """
        val = None
        err = Potentiometer._eval_resistance_value(percentage, absolute, digital, digital_max, max_resistance)
        if err == ErrorCode.errOk:
            if percentage != None:
                val = (digital_max * percentage) // 100
            elif absolute != None:
                val = int(digital_max * absolute) // max_resistance
            elif digital != None:
                pass
            val = (digital_max-1) if val > (digital_max-1) else val
        return val, err
    
    def _eval_resistance_value(percentage=None, absolute=None, digital=None, digital_max=None, max_resistance=None):
        """Evaluate values given to set method. Raises error if values are invalid (e.g. over 100% or over maximum resistance).\
        There must only be one out of the parameters percentage, absolute and digital given.

        :param percentage percentage: Resistance value, interpreted as percentage (0 to 100) by default.
        :param int absolute: Resistance value in Ohms. Must be between 0 and the set maximum value.
        :param int digital: Digital resistance value to be sent directly to the potentiometer without conversion.
        :param int digital_max: Number of possible steps to set resistance value to (2^(bits used for resistance)).
        :param int max_resistance: Maximum resistance of Potentiometer in Ohm.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        err = ErrorCode.errOk
        if (percentage != None) ^ bool(absolute != None) ^ bool(digital != None): # check if exactly one parameter is given
            if percentage and (percentage < 0 or percentage > 100):
                err = ErrorCode.errInvalidParameter # Percentage value must be between 0 and 100.
            elif absolute and (absolute < 0 or absolute > max_resistance):
                err = ErrorCode.errInvalidParameter # Given absolute resistance value was {value} ohm must be between 0 ohm and the given maximum ({max_resistance} is currently set)
            elif digital and (digital < 0 or digital >= (digital_max-1)):
                err = ErrorCode.errInvalidParameter # Digital value must be between 0 and the given digital_max.
        else:
            err = ErrorCode.errInvalidParameter # There must only be one parameter given.
        return err
    
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
        return ErrorCode.errNotImplemented
    
    def get(self, asPercentage=True, asAbsolute=False, asDigital=False):
        """Get current resistance setting of potentiometer as ative (percentage), absolute (ohms), or digital value.\
        There must only be one parameter set to true.
        
        :param bool asPercentage: Set true to convert value into a relative percent value. (default).
        :param bool asAblsolute: Set true to convert value into ohms. False for a percentage value (default).
        :param bool asDigital: Set true to return value as digital value.
        :return: The resistance value and an error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        return ErrorCode.errNotImplemented
        
        
            
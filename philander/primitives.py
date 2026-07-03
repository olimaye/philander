# -*- coding: utf-8 -*-
"""A module to reflect fundamental physical units and scales.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Percentage", "PrecisePercentage", 
           "Voltage", "Current",
           "Temperature", "PreciseTemperature",
           "Pressure", "PrecisePressure"]

from philander.systypes import ErrorCode

class Percentage(int):
    """Percentage [0...100%] in percent [%]
    """
    invalid = 0xFF
    
    @staticmethod
    def checkRange( value ):
        """Check if the given value is a plausible percentage.

        If the given value is within the range of [0...100], this method
        returns ``ErrorCode.errOk``. Otherwise, it gives
        ``ErrorCode.errInvalidParameter``.
        
        :param int value: Something that compares to integer numbers, interpreted as a percentage.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        if value < 0 or value > 100:
            ret = ErrorCode.errInvalidParameter
        else:
            ret = ErrorCode.errOk
        return ret

class PrecisePercentage(int):
    """Percentage [0...100%] given as a Q8.8 fixed-point rational.
    """
    invalid = 0xFFFF
    
    @staticmethod
    def checkRange( value ):
        """Check if the given value is a plausible percentage.

        If the given value is within the range of [0...100], this method
        returns ``ErrorCode.errOk``. Otherwise, it gives
        ``ErrorCode.errInvalidParameter``.
        
        :param int value: Something that compares to integer numbers, interpreted as a percentage.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        if (value < 0) or (value > 25600):
            ret = ErrorCode.errInvalidParameter
        else:
            ret = ErrorCode.errOk
        return ret


class Voltage(int):
    """Voltage [0...60V] in milli Volt [mV]
    """
    invalid = 0xFFFF

class Current(int):
    """Current [-1A...+1A] in micro Amp [µA]
    """
    invalid = -1

class Temperature(int):
    """Temperature [-70...+125] in full degree Celsius [°C]
    """
    invalid = -128

class PreciseTemperature(int):
    """Temperature [-70...+125] in degree Celsius [°C], given as a\
    Q8.8 fixed-point number with 8-bit decimals.
    """
    invalid = -32768
    min     = -32767
    max     = 0x7FFF

class Pressure(int):
    """Pressure [-2 GPa ... +2 GPa] in full Pascal [Pa]
    """
    invalid = -2147483648   # 0x80000000
    min     = -2147483647   # 0x80000001
    max     = 2147483647    # 0x7FFFFFFF

class PrecisePressure(int):
    """Pressure [-8 MPa ... +8 MPa] in Pascal [Pa], given as a\
    Q24.8 fixed-point number with 8-bit decimals.
    """
    invalid = -2147483648   # 0x80000000
    min     = -2147483647   # 0x80000001
    max     = 2147483647    # 0x7FFFFFFF

    
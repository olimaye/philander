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
    DEFAULT_DIGITAL_MAX = 127
    
    def __init__(self):
        _digitalMax = 1
        _resistanceMax = 1
        
    #
    # Module API
    #
        
    @classmethod
    def Params_init(cls, paramDict):
        """Initializes configuration parameters with defaults.
        
        The following settings are supported:
        
        =============================    =====================================================================================================
        Key name                         Value type, meaning and default
        =============================    =====================================================================================================
        Potentiometer.resistance.max     ``int`` Maximum resistance in Ohm; :attr:`DEFAULT_RESISTANCE_MAX`.
        Potentiometer.digital.max        ``int`` Maximum possible digital value to set resistance to (2^n-1). :attr:`DEFAULT_DIGITAL_MAX`.
        ======================================================================================================================================
        """
        defaults = {
            "Potentiometer.resistance.max": Potentiometer.DEFAULT_RESISTANCE_MAX,
            "Potentiometer.digital.max": Potentiometer.DEFAULT_DIGITAL_MAX
        }
        for key, value in defaults.items():
            if not key in paramDict:
                paramDict[key] = value
        return None
    
    def open(self, paramDict):
        """Initialize an instance and prepare it for use.

        Also see: :meth:`.Module.open`.
        
        :param dict(str, object) paramDict: Configuration parameters as\
        possibly obtained from :meth:`Params_init`.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        # Get default parameters
        Potentiometer.Params_init( paramDict )
        # Store potentiometer properties
        self._resistanceMax = paramDict["Potentiometer.resistance.max"]
        self._digitalMax = paramDict["Potentiometer.digital.max"]
        return ret


    #
    # Potentiometer API
    #

    @staticmethod
    def _rangeMap( source, sourceMax, destMax ): 
        """Converts a source value into some destination range.
        
        After a value validity check, maps the source value from
        [0, ``sourceMax``] into the corresponding position in
        [0, ``destMax``].
        Rounding scheme is as follows ::
            [0 ... 0.5) -> 0
            [0.5 ... 1.5) -> 1
            [1.5 ... 2.5) -> 2
        and so on.
        
        Also see: :meth:`.Potentiometer._checkRange`.
        
        :param int source: Source value. Must be between 0 and ``sourceMax``, inclusive.
        :param int sourceMax: Maximum source value.
        :param int destMax: Maximum destination value.
        :return: The resulting value in destination range and an error code indicating success or the reason of failure.
        :rtype: Tuple(value, ErrorCode)
        """
        val = None
        err = Potentiometer._checkRange( source, sourceMax)
        if err.isOk():
            val = int(destMax * source + sourceMax//2) // sourceMax
        return val, err
    
    @staticmethod
    def _checkRange( value, maximum):
        """Check if the given value is within the allowed range [0, maximum].

        Returns ``ErrorCode.errOk``, if the given value is within the
        allowed range of [0...``maximum``], or
        ``ErrorCode.errInvalidParameter``, otherwise.

        :param int value: Value to check. Must be between 0 and the ``maximum`` parameter.
        :param int maximum: Upper bound for the value. Maximum of the allowed range.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        err = ErrorCode.errOk
        if value < 0 or value > maximum:
            err = ErrorCode.errInvalidParameter
        else:
            err = ErrorCode.errOk
        return err
    
    
    def setDigital(self, digital):
        """Set resistance of potentiometer to a digital value.
        
        This method must be implemented by a subclass.
        It is a complementary alternative to :meth:`.setResistance` and
        :meth:`.setPercentage`.
        
        :param int digital: Digital resistance value to be sent directly to the potentiometer without conversion.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del digital
        return ErrorCode.errNotImplemented
    
    def setResistance(self, resistance):
        """Set resistance of potentiometer to an absolute value (Ohms).
        
        This is a complementary alternative to :meth:`.setDigital` and
        :meth:`.setPercentage`.
        
        :param int resistance: Resistance value in Ohms. Must be between 0 and the set maximum value.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        digital, err = Potentiometer._rangeMap(resistance, self._resistanceMax, self._digitalMax)
        if err.isOk():
            err = self.setDigital(digital)
        return err
    
    def setPercentage(self, percentage):
        """Set resistance of potentiometer to a relative value (percentage).
        
        This is a complementary alternative to :meth:`.setDigital` and
        :meth:`.setResistance`.
        
        :param percentage percentage: Resistance value, interpreted as percentage (0 to 100).
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        digital, err = Potentiometer._rangeMap(percentage, 100, self._digitalMax)
        if err.isOk():
            err = self.setDigital(digital)
        return err
    
    def getDigital(self):
        """Get resistance of potentiometer as a digital value in [0...digital.max]
        
        This method must be implemented by a subclass.
        It is a complementary alternative to :meth:`.getResistance` and
        :meth:`.getPercentage`.
        
        :return: The resistance value and an error code indicating either success or the reason of failure.
        :rtype: int, ErrorCode
        """
        return 0, ErrorCode.errNotImplemented
        
    def getResistance(self):
        """Get resistance of potentiometer as an absolute value in [0...resistance.max](Ohms)
        
        This method is a complementary alternative to :meth:`.getDigital`
        and :meth:`.getPercentage`.
        
        :return: The resistance value and an error code indicating either success or the reason of failure.
        :rtype: int, ErrorCode
        """
        ret = None
        digital, err = self.getDigital()
        if err.isOk():
            ret, err = Potentiometer._rangeMap(digital, self._digitalMax, self._resistanceMax)
        return ret, err
        
    def getPercentage(self):
        """Get resistance of potentiometer as a percentage value in [0...100]
        
        This method is a complementary alternative to :meth:`.getDigital`
        and :meth:`.getResistance`.
        
        :return: The resistance value and an error code indicating either success or the reason of failure.
        :rtype: .Percentage, ErrorCode
        """
        ret = None
        digital, err = self.getDigital()
        if err.isOk():
            ret, err = Potentiometer._rangeMap(digital, self._digitalMax, 100)
        return ret, err
        

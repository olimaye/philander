# -*- coding: utf-8 -*-
"""Driver implementation for the MCP40 17/18/19 digital potentiometers.

More information on the functionality of the chip can be found at
the microchip's site for the 18 series chip with download for data sheet of all three chips:
https://www.microchip.com/en-us/product/MCP4018
"""
__author__ = "Carl Bellgardt"
__version__ = "0.1"
__all__ = ["MCP40"]

from .potentiometer import Potentiometer
from .serialbus import SerialBusDevice
from .systypes import ErrorCode
from .primitives import Percentage

class MCP40( SerialBusDevice, Potentiometer ):
    """MCP40 family and MCP40D family driver implementation.\
    This implementation was tested using a MCP40D18T-104E/LT. It should also work for any other specified chip.

    The MCP40 and MCP40D family's chips are digital potentiometers that are controlled via an I2C interface. Their difference lies in their terminal configurations.
    The all come in different resistances of 5kOhm, 10kOhm, 50kOhm and 100kOhm. Read more under https://www.microship.com/en-us/product/MCP4017
    """
    
    ADDRESSES_ALLOWED = [0x2E, 0x3E, 0x2F]

    def __init__(self):
        # Create instance attributes and initialize parent classes and interfaces
        SerialBusDevice.__init__(self)
        _digitalMax = 127       # should apply for all MCP40xx boards
        _resistanceMax = None

    #
    # Module API
    #

    @classmethod
    def Params_init(cls, paramDict):
        """Initializes configuration parameters with defaults.
        
        The following settings are supported:
        
        =============================    ==========================================================================================================
        Key name                         Value type, meaning and default
        =============================    ==========================================================================================================
        SerialBusDevice.address          ``int`` I2C serial device address; default is :attr:`ADDRESSES_ALLOWED` [0].
        Potentiometer.resistance.max     ``int`` Maximum resistance in Ohm; :attr:`DEFAULT_RESISTANCE_MAX`.
        ===========================================================================================================================================
        
        Also see: :meth:`.SerialBusDevice.Params_init`, :meth:`.Potentiometer.Params_init`. 
        """
        defaults = dict()
        SerialBusDevice.Params_init( paramDict )
        Potentiometer.Params_init( paramDict )
        defaults.update( paramDict )
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
        # Get default parameters
        MCP40.Params_init( paramDict )
        # Open the bus device
        ret = SerialBusDevice.open(self, paramDict)
        # Store potentiometer properties
        self._resistanceMax = paramDict["Potentiometer.resistance.max"]
        return ret


    def close(self):
        """Close this instance and release hardware resources.
        
        Also see: :meth:`.Module.close`.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = SerialBusDevice.close(self)
        return ret
    
    def setDigital(self, digital):
        """Set resistance of potentiometer to a digital value.
        
        Also see: :meth:`.Potentiometer.setDigital`.
        
        :param int digital: Digital resistance value to be sent directly to the potentiometer without conversion.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        err = Potentiometer._checkRange( digital, self._digitalMax )
        if err.isOk():
            err = SerialBusDevice.writeByteRegister(self, 0x00, digital)
        return err
    
    def getDigital(self):
        """Get resistance of potentiometer as a digital value in [0...digital.max]
        
        Also see: :meth:`.Potentiometer.get`.
        
        :return: The resistance value and an error code indicating either success or the reason of failure.
        :rtype: Tuple(ErrorCode, data)
        """
        data, err = SerialBusDevice.readByteRegister(self, 0x00)
        return data, err
    

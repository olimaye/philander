# -*- coding: utf-8 -*-
"""Driver implementation for the MCP40D 17/18/19 digital potentiometers.

More information on the functionality of the chip can be found at
the microchip's site for the 18 series chip with download for data sheet of all three chips:
https://www.microchip.com/en-us/product/MCP40D18
"""
__author__ = "Carl Bellgardt"
__version__ = "0.1"
__all__ = ["MCP40D"]

import time
from enum import unique, auto, Enum

from .potentiometer import Potentiometer
from .serialbus import SerialBusDevice
from .systypes import ErrorCode, RunLevel

'''
@unique
class PackageTypes(Enum):
    """Data class to decide which PackageType of sensor is being
    """
    MCP40D17 = auto()
    MCP40D18 = auto()
    MCP40D19 = auto()
    
@unique
class ResistanceCode(Enum):
    """Data class to decide which resistance code the device has\
    and which resistance thus must be it's maximum value.
    """
    _502 = 5000
    _103 = 10000
    _503 = 50000
    _104 = 100000
'''

class MCP40D( SerialBusDevice, Potentiometer ):
    """MCP40D17/18/19 driver implementation.

    The CMP40D17/18/19 chips are digital potentiometers that are controlled via an I2C interface. Their difference lies in their terminal configurations.
    The all come in different resistances of 5kOhm, 10kOhm, 50kOhm and 100kOhm. Read more under https://www.microship.com/en-us/product/MCP40D17
    """
    
    ADDRESSES_ALLOWED = [0x2E, 0x3E]
    _potentiometer_resolution = None
    _potentiometer_resistance_max = None

    def __init__(self):
        # Create instance attributes and initialize parent classes and interfaces
        SerialBusDevice.__init__(self)
        Potentiometer.__init__(self)

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
        Potentiometer.resistance.max     ``int``; Maximum resistance in Ohm; :attr:`DEFAULT_RESISTANCE_MAX`.
        Potentiometer.resolution         ``int``; Number of bits used to set resistance value.
        ===========================================================================================================================================
        
        For the ``SerialBusDevice.address`` value, also 0 or 1
        can be specified alternatively to the absolute addresses to reflect
        the level of the ``SDO`` pin. In this case, 0 will be mapped to
        0x18, while 1 maps to 0x19.
        
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
        MCP40D.Params_init( paramDict )
        # Open the bus device
        ret = SerialBusDevice.open(self, paramDict)
        # Store potentiometer properties
        self._potentiometer_resolution = paramDict["Potentiometer.resolution"]
        self._potentiometer_resistance_max = paramDict["Potentiometer.resistance.max"]
        return ret


    def close(self):
        """Close this instance and release hardware resources.
        
        Also see: :meth:`.Module.close`.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = super().close()
        return ret
    
    def set(self, value, isAbsolute=False, isDigital=False):
        """Set resistance of potentiometer to a relative (percentage) or absolute (Ohms) value via I2C.
        
        Also see: :meth:`.Potentiometer.set`.
        
        :param int value: Resistance value, interpreted as percentage (0 to 100) by default.\
        Will be inpreted as absolute resistance in ohms, if isAbsolute is set true,\
        or as digital value if isDigital is true.
        :param bool isAbsolute: Set true if value is in ohms.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        value = Potentiometer._digitalize_resistance_value(value, isAbsolute, self._potentiometer_resistance_max, isDigital, self._potentiometer_resolution)
        print(value)
        err = SerialBusDevice.writeByteRegister(self, 0x00, value)
        return err
    
    def get(self, asAbsolute=False, asDigital=False):
        """Get current resistance setting of potentiometer as relative (percentage) or absolute (Ohms) or digital value via I2C.
        
        Also see: :meth:`.Potentiometer.get`.
        
        :param bool asAblsolute: Set true to convert value into ohms. False for a percentage value (default).
        :param bool asDigital: Set true to return value as digital value.
        :return: The resistance value and an error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        data, err = SerialBusDevice.readByteRegister(self, 0x00)
        if asDigital:
            return data, err
        # convert data into percentage or ohms
        pot_steps = 2 ** self._potentiometer_resolution # number of available steps, dependent on number of bits for resolution
        if asAbsolute:
            data *= (self._potentiometer_resistance_max / pot_steps)
        else:
            data *= (100/pot_steps)
        return data, err
    
    def _get_digital(self):
         data, err = SerialBusDevice.readByteRegister(self, 0x00)
         return data, err
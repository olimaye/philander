"""Support module for the Mikro-e Vibra sense 2 click board.

This board carries a TE LDT0-028K Piezo Film sensor as its core element. 
"""
from systypes import ErrorCode
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["VibraSense2"]

from interruptable import Interruptable
from pymitter import EventEmitter
from sensor import Sensor
from serialbus import SerialBusDevice

class VibraSense2( EventEmitter, Sensor, Interruptable, SerialBusDevice):
    """Vibra sense 2 driver implementation.
    
    More information on the Mikroelektronika Vibra sense 2 click
    (MIKROE-4355) board are available at:
    https://www.mikroe.com/vibra-sense-2-click

    The functional core element is a TE LDT0-028K Piezo Film sensor.
    More information on that device can be found at:
    https://www.te.com/deu-de/product-CAT-PFS0006.html
    """

    # The only address. No alternative.
    ADDRESSES_ALLOWED = [0x4D]
    
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
        SerialBusDevice.deviceAddress    ``int`` I2C serial device address, must be :attr:`ADDRESS`; default is :attr:`ADDRESS`.
        Sensor.dataRate                  ``int`` Data rate in Hz; default is set by :meth:`.Sensor.Params_init`.
        =============================    ==========================================================================================================
        
        Also see: :meth:`.Sensor.Params_init`, :meth:`.SerialBusDevice.Params_init`. 
        """

        paramDict["SerialBusDevice.deviceAddress"] = VibraSense2.ADDRESSES_ALLOWED[0]
        super().Params_init(paramDict)
        return None


    def open(self, paramDict):
        ret = super().open(paramDict)
        return ret
    
    def close(self):
        ret = super().close()
        return ret
        
    #
    # Sensor API
    #
    
    def getLatestData(self):
        return self.getNextData()

    def getNextData(self):
        # Read 2 bytes without prior writing of a register number
        data, err = self.readBuffer(2)
        if (err == ErrorCode.errOk):
            data = data[1]
        else:
            data = 0
    
        return data, err
    
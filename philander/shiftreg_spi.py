"""Module to control a shift register by means of an SPI bus.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["ShiftRegSPI"]

import logging

from .serialbus import SerialBusDevice, SerialBusType
from .shiftreg import ShiftReg
from .systypes import ErrorCode


class ShiftRegSPI( ShiftReg ):
    """Driver class for a shift register device using SPI.
    """
        
    def __init__(self):
        """Initialize the instance with defaults.
        
        Also see: :meth:`.Params_init`, :meth:`.ShiftReg.Params_init`
        """
        ShiftReg.__init__(self)
        self.serbusdev = None

    #
    # Module API
    #

    @classmethod
    def Params_init(cls, paramDict):
        """Initializes configuration parameters with defaults.
        
        General or global GPIO adjustments or defaults can be set using
        the `shiftreg.gpio.*` keys. They can be pin-wise overridden by
        specific e.g. `shiftreg.ena.gpio.*` settings.
        
        The following settings are supported:
        
        ==================================   =====================================================================
        Key name                             Value type, meaning and default
        ==================================   =====================================================================
        shiftreg.*                           Shift register configuration; See :meth:`.ShiftReg.Params_init`.
        shiftreg.SerialBusDevice.*           Serial bus configuration; See :meth:`.SerialBusDevice.Params_init`.
        ==========================================================================================================
        
        Also see: :meth:`.Module.Params_init`, :meth:`.ShiftReg.Params_init`, :meth:`.SerialBusDevice.Params_init`.
        """
        # Remove GPIO definitions for DIN and DCLK, if present
        paramDict.pop( "shiftreg.din.gpio.pinDesignator", None)
        paramDict.pop( "shiftreg.dclk.gpio.pinDesignator", None)
        # Base class settings
        ShiftReg.Params_init( paramDict )
        # Driver defaults
        serialDefaults = {}
        serialDefaults["SerialBus.type"] = SerialBusType.SPI
        SerialBusDevice.Params_init( serialDefaults )
        # Mandatory settings
        itemKey = ShiftReg.MODULE_PARAM_PREFIX + "." + "SerialBus.type"
        paramDict[itemKey] = SerialBusType.SPI
        # Add missing values by setting defaults
        for key, value in serialDefaults.items():
            itemKey = ShiftReg.MODULE_PARAM_PREFIX + "." + key
            if not( itemKey in paramDict):
                paramDict[itemKey] = value
        return None


    def open(self, paramDict):
        ret = ErrorCode.errOk
        if self.serbusdev:
            ret = ErrorCode.errResourceConflict
        if ret.isOk():
            self.Params_init( paramDict )
            prefixMod = ShiftReg.MODULE_PARAM_PREFIX + "."
            prefixSub1 = prefixMod + "SerialBus."
            prefixSub2 = prefixMod + "SerialBusDevice."
            # Extract serial bus parameters
            serialParams = dict( [(k.replace(prefixMod, ""),v) \
                                  for k,v in paramDict.items() \
                                  if k.startswith(prefixSub1) or k.startswith(prefixSub2)] )
            self.serbusdev = SerialBusDevice()
            ret = self.serbusdev.open(serialParams)
            if not ret.isOk():
                logging.debug("ShiftRegSPI couldn't open serial bus device, error: %s.", ret)
                self.serbusdev = None
        if ret.isOk():
            ret = super().open( paramDict )
        logging.debug('ShiftRegSPI.open() returns: %s.', ret)
        return ret
    
    def close(self):
        ret = ErrorCode.errOk
        if self.serbusdev:
            ret = self.serbusdev.close()
            self.serbusdev = None
        err = super().close()
        if ret.isOk():
            ret = err
        logging.debug('ShiftReg closed, return: %s.', ret)
        return ret
    
    #
    # Module specific API
    #
    
    def write(self, data, numBits=8, autoLatch=True):
        """Feed data into the shift register.
        
        As the underlying mechanism is SPI, only full bytes can be
        written to the register. So, 'numBits' must be a multiple of 8.
        At maximum, four bytes can be written at once, so numBits must
        be one of `numBits={8 | 16 | 24 | 32}`.
        The highest-significant byte selected is written first.
        If, for example, `data = 0xa4b3c2d1` and `numBits=24`, the
        sequence shifted into the register is `b3-c2-d1`. 
        
        If `autoLatch` is `True` and depending on the underlying
        hardware, the resulting content of the shift register is
        latched into the buffer.
        
        :param int data: The data to send to the shift register.
        :param int numBits: Non-negative number of least-significant \
        bits in 'data' to shift-in. One of `{8 | 16 | 24 | 32}`. 
        :param bool autoLatch: Whether to automatically latch the result into the buffer.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if not self.serbusdev:
            ret = ErrorCode.errNotInited
        elif not isinstance( data, int ) or \
             not isinstance( numBits, int ) or (numBits not in [0,8,16,24,32]):
            ret = ErrorCode.errInvalidParameter
        elif numBits == 0:
            # Do nothing
            ret = ErrorCode.errOk
        else:
            buf = []
            while numBits > 0:
                numBits -= 8
                buf.append( (data >> numBits) & 0xFF )
            ret = self.serbusdev.writeBuffer(buf)
            if( ret.isOk() and autoLatch ):
                self.latch()
                
        logging.debug('ShiftReg write(data=%02x, numBits=%d), return: %s.',
                      data, numBits, ret)
        return ret

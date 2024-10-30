"""Provide the serial bus API for the Micropython environment.

An application should never use this module directly. Instead, the
system factory will provide suitable instances.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["_SerialBus_Micropython" ]

from machine import I2C

from philander.serialbus import SerialBus
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode

    
class _SerialBus_Micropython( SerialBus ):
    """Periphery serial bus implementation.
    """
    
    def __init__(self):
        super().__init__()
        self.provider = SysProvider.MICROPYTHON
        
    def open( self, paramDict ):
        # Scan the parameters
        ret = super().open(paramDict)
        if (ret.isOk()):
            try:
                self.bus = I2C( self.designator )
            except TypeError:
                ret = ErrorCode.errInvalidParameter
        return ret
    
    def close(self):
        ret = super().close()
        if (not self.bus is None) and hasattr(self.bus, "deinit"):
            self.bus.deinit()
        return ret
    
    def _readBytes( self, device, reg, num ):
        err = ErrorCode.errOk
        data = self.bus.readfrom_mem( device.address, reg, num )
        data = int.from_bytes( data, "little" )
        return data, err

    def _writeBytes( self, device, reg, data, num ):
        err = ErrorCode.errOk
        buf = data.to_bytes( num, "little" )
        self.bus.writeto_mem( device.address, reg, buf )
        return err

    def readByteRegister( self, device, reg ):
        return self._readBytes( device, reg, 1 )

    def writeByteRegister( self, device, reg, data ):
        return self._writeBytes(device, reg, data, 1)

    def readWordRegister( self, device, reg ):
        return self._readBytes( device, reg, 2 )

    def writeWordRegister( self, device, reg, data16 ):
        return self._writeBytes(device, reg, data16, 2)

    def readDWordRegister( self, device, reg ):
        return self._readBytes( device, reg, 4 )

    def writeDWordRegister( self, device, reg, data32 ):
        return self._writeBytes(device, reg, data32, 4)
    
    def readBufferRegister( self, device, reg, length ):
        err = ErrorCode.errOk
        data = self.bus.readfrom_mem( device.address, reg, length )
        data = list(data)
        return data, err

    def writeBufferRegister( self, device, reg, data ):
        err = ErrorCode.errOk
        self.bus.writeto_mem( device.address, reg, bytes(data) )
        return err

    def readBuffer( self, device, length ):
        err = ErrorCode.errOk
        data = self.bus.readfrom( device.address, length )
        data = list(data)
        return data, err

    def writeBuffer( self, device, buffer ):
        err = ErrorCode.errOk
        self.bus.writeto( device.address, bytes(buffer) )
        return err
    

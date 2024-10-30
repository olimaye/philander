"""Provide the serial bus API while relying on the periphery package.

An application should never use this module directly. Instead, the
system factory will provide suitable instances.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["_SerialBus_Periphery" ]

from periphery import I2C

from philander.serialbus import SerialBus
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode

    
class _SerialBus_Periphery( SerialBus ):
    """Periphery serial bus implementation.
    """
    
    def __init__(self):
        super().__init__()
        self.provider = SysProvider.PERIPHERY
        
    def open( self, paramDict ):
        # Scan the parameters
        ret = super().open(paramDict)
        if (ret.isOk()):
            self.bus = I2C( self.designator )
        return ret
    
    def close(self):
        ret = super().close()
        if not self.bus is None:
            self.bus.close()
        return ret
    
    def readByteRegister( self, device, reg ):
        err = ErrorCode.errOk
        msgs = [self.bus.Message([reg]), self.bus.Message([0x00], read=True)]
        self.bus._transfer( device.address, msgs)
        data = msgs[1].data[0]
        return data, err

    def writeByteRegister( self, device, reg, data ):
        err = ErrorCode.errOk
        msgs = [self.bus.Message([reg, data])]
        self.bus._transfer( device.address, msgs)
        return err

    def readWordRegister( self, device, reg ):
        err = ErrorCode.errOk
        msgs = [self.bus.Message([reg]), self.bus.Message([0, 0], read=True)]
        self.bus._transfer( device.address, msgs)
        data = (msgs[1].data[1] << 8) | msgs[1].data[0]
        return data, err

    def writeWordRegister( self, device, reg, data16 ):
        err = ErrorCode.errOk
        msgs = [self.bus.Message([reg, (data16 & 0xFF), (data16 >> 8)])]
        self.bus._transfer( device.address, msgs)
        return err

    def readDWordRegister( self, device, reg ):
        err = ErrorCode.errOk
        msgs = [self.bus.Message([reg]), self.bus.Message([0, 0, 0, 0], read=True)]
        self.bus._transfer( device.address, msgs)
        data = (msgs[1].data[3] << 24) | (msgs[1].data[2] << 16) | (msgs[1].data[1] << 8) | msgs[1].data[0]
        return data, err

    def writeDWordRegister( self, device, reg, data32 ):
        err = ErrorCode.errOk
        msgs = [self.bus.Message([reg, (data32 & 0xFF), (data32 >> 8), (data32 >> 16), (data32 >> 24)])]
        self.bus._transfer( device.address, msgs)
        return err
    
    def readBufferRegister( self, device, reg, length ):
        err = ErrorCode.errOk
        ba = bytearray(length)
        msgs = [self.bus.Message([reg]), self.bus.Message(ba, read=True)]
        self.bus._transfer( device.address, msgs)
        data = msgs[1].data
        return data, err

    def writeBufferRegister( self, device, reg, data ):
        err = ErrorCode.errOk
        bdata = data
        bdata.insert( 0, reg )
        msgs = [self.bus.Message( bdata )]
        self.bus._transfer( device.address, msgs)
        return err

    def readBuffer( self, device, length ):
        err = ErrorCode.errOk
        ba = bytearray(length)
        msgs = [self.bus.Message(ba, read=True)]
        self.bus._transfer( device.address, msgs)
        data = msgs[0].data
        return data, err

    def writeBuffer( self, device, buffer ):
        err = ErrorCode.errOk
        msgs = [self.bus.Message( buffer )]
        self.bus._transfer( device.address, msgs)
        return err
    
    def readWriteBuffer( self, device, inLength, outBuffer ):
        err = ErrorCode.errOk
        ba = bytearray(inLength)
        msgs = [self.bus.Message(outBuffer), self.bus.Message(ba, read=True)]
        self.bus._transfer( device.address, msgs)
        data = msgs[1].data
        return data, err


"""Provide the serial bus API while relying on the SMBus2 package.

An application should never use this module directly. Instead, the
system factory will provide suitable instances.
"""
from serialbus import SerialBusType
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["_SerialBus_SMBus2" ]

from smbus2 import SMBus, i2c_msg

from philander.serialbus import SerialBus
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode


class _SerialBus_SMBus2( SerialBus ):
    """SMBUS2 serial bus implementation.
    
    Supports I2C, only.
    """

    def __init__(self):
        super().__init__()
        self.provider = SysProvider.SMBUS2
        self.msg = i2c_msg
        
    def open( self, paramDict ):
        # Scan the parameters
        if paramDict.get( "SerialBus.type", None) != SerialBusType.I2C:
            ret = ErrorCode.errNotSupported
        else:
            ret = super().open(paramDict)
        if (ret.isOk()):
            try:
                self.bus = SMBus( self.designator )
                ret = ErrorCode.errOk
            except Exception:
                ret = ErrorCode.errLowLevelFail
                #raise OSError("Couldn't initialize serial bus ["+str(self.designator)+"]. Designator right? Access to interface granted?") from exc
                # better log something
        return ret

    def close( self ):
        ret = super().close()
        if not self.bus is None:
            self.bus.close()
        return ret
    
    def readByteRegister( self, device, reg ):
        err = ErrorCode.errOk
        data = 0
        try:
            data = self.bus.read_byte_data( device.address, reg )
        except OSError:
            err = ErrorCode.errFailure
        return data, err

    def writeByteRegister( self, device, reg, data ):
        err = ErrorCode.errOk
        try:
            self.bus.write_byte_data( device.address, reg, data )
        except OSError:
            err = ErrorCode.errFailure
        return err

    def readWordRegister( self, device, reg ):
        err = ErrorCode.errOk
        data = 0
        try:
            data = self.bus.read_word_data( device.address, reg )
        except OSError:
            err = ErrorCode.errFailure
        return data, err

    def writeWordRegister( self, device, reg, data16 ):
        err = ErrorCode.errOk
        try:
            self.bus.write_word_data( device.address, reg, data16 )
        except OSError:
            err = ErrorCode.errFailure
        return err

    def readBufferRegister( self, device, reg, length ):
        err = ErrorCode.errOk
        try:
            if (length <= 32 ):
                data = self.bus.read_i2c_block_data( device.address, reg, length )
            else:
                msg1 = self.msg.write( device.address, [reg] )
                msg2 = self.msg.read( device.address, length )
                self.bus.i2c_rdwr( msg1, msg2 )
                data = list(msg2)
        except OSError:
            err = ErrorCode.errFailure
            data = list()
        return data, err

    def writeBufferRegister( self, device, reg, data ):
        err = ErrorCode.errOk
        try:
            if (len(data) <= 32 ):
                self.bus.write_i2c_block_data( device.address, reg, data )
            else:
                bdata = data
                bdata.insert( 0, reg )
                msg = self.msg.write( device.address, bdata )
                self.bus.i2c_rdwr( msg )
        except OSError:
            err = ErrorCode.errFailure
        return err

    def readBuffer( self, device, length ):
        err = ErrorCode.errOk
        try:
            msg = self.msg.read( device.address, length )
            self.bus.i2c_rdwr( msg )
            data = list(msg)
        except OSError:
            err = ErrorCode.errFailure
            data = list()
        return data, err

    def writeBuffer( self, device, buffer ):
        err = ErrorCode.errOk
        try:
            msg = self.msg.write( device.address, buffer )
            self.bus.i2c_rdwr( msg )
        except OSError:
            err = ErrorCode.errFailure
        return err
    
    def readWriteBuffer( self, device, inLength, outBuffer ):
        err = ErrorCode.errOk
        try:
            msgW = self.msg.write( device.address, outBuffer )
            msgR = self.msg.read( device.address, inLength )
            self.bus.i2c_rdwr( msgW, msgR )
            data = list(msgR)
        except OSError:
            err = ErrorCode.errFailure
            data = list()
        return data, err

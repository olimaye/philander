"""Provide the serial bus API for the Micropython environment.

An application should never use this module directly. Instead, the
system factory will provide suitable instances.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["_SerialBus_Micropython" ]

from machine import I2C, SPI

from philander.gpio import GPIO
from philander.serialbus import SerialBus,SerialBusType, SPIMode
from philander.sysfactory import SysFactory, SysProvider
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
                speed= paramDict["SerialBus.speed"]
                if self.type == SerialBusType.I2C:
                    self.bus = I2C( self.designator, freq=speed )
                elif self.type == SerialBusType.SPI:
                    mode = paramDict["SerialBus.SPI.mode"]
                    pol = 0 if mode in [SPIMode.CPOL0_CPHA0, SPIMode.CPOL0_CPHA1] else 1
                    ph  = 0 if mode in [SPIMode.CPOL0_CPHA0, SPIMode.CPOL1_CPHA0] else 1
                    if paramDict["SerialBus.SPI.bitorder"].lower() == "MSB".lower():
                        bit1 = SPI.MSB
                    else:
                        bit1 = SPI.LSB
                    bpw  = paramDict["SerialBus.SPI.bpw"]
                    self.bus = SPI( self.designator, baudrate=speed, polarity=pol, phase=ph, bits=bpw, firstbit=bit1 )
            except TypeError:
                ret = ErrorCode.errInvalidParameter
        return ret
    
    def close(self):
        ret = super().close()
        if (not self.bus is None) and hasattr(self.bus, "deinit"):
            self.bus.deinit()
        return ret

    def attach( self, device ):
        result = ErrorCode.errOk
        if (self.type == SerialBusType.SPI) and (device.pinCS is None):
            result = ErrorCode.errFewData  # Need explicit CS pin designator!
        if result.isOk():
            result = super().attach( device )
        return result

    def _readBytes( self, device, reg, num ):
        err = ErrorCode.errOk
        data = 0
        if self.type == SerialBusType.I2C:
            try:
                resp = self.bus.readfrom_mem( device.address, reg, num )
                data = int.from_bytes( resp, "little" )
            except OSError:
                err = ErrorCode.errLowLevelFail
        elif self.type == SerialBusType.SPI:
            # Note that CS activation/de-activation is NOT done by hardware
            device.pinCS.set( GPIO.LEVEL_LOW )
            try:
                self.bus.write( reg.to_bytes() )
                resp = self.bus.read(num)
                data = int.from_bytes( resp, "little" )
            except OSError:
                err = ErrorCode.errLowLevelFail
            finally:
                device.pinCS.set( GPIO.LEVEL_HIGH )
        else:
            err = ErrorCode.errNotSupported
        return data, err

    def _writeBytes( self, device, reg, data, num ):
        err = ErrorCode.errOk
        if self.type == SerialBusType.I2C:
            try:
                buf = data.to_bytes( num, "little" )
                self.bus.writeto_mem( device.address, reg, buf )
            except OSError:
                err = ErrorCode.errLowLevelFail
        elif self.type == SerialBusType.SPI:
            device.pinCS.set( GPIO.LEVEL_LOW )
            try:
                buf = reg.to_bytes( 1 ) + data.to_bytes( num, "little" )
                self.bus.write( buf )
            except OSError:
                err = ErrorCode.errLowLevelFail
            finally:
                device.pinCS.set( GPIO.LEVEL_HIGH )
        else:
            err = ErrorCode.errNotSupported
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
        data = []
        if self.type == SerialBusType.I2C:
            try:
                resp = self.bus.readfrom_mem( device.address, reg, length )
                data = list(resp)
            except OSError:
                err = ErrorCode.errLowLevelFail
        elif self.type == SerialBusType.SPI:
            # Note that CS activation/de-activation is NOT done by hardware
            device.pinCS.set( GPIO.LEVEL_LOW )
            try:
                self.bus.write([reg])
                resp = self.bus.read(length)
                data = list(resp)
            except OSError:
                err = ErrorCode.errLowLevelFail
            finally:
                device.pinCS.set( GPIO.LEVEL_HIGH )
        else:
            err = ErrorCode.errNotSupported
        return data, err

    def writeBufferRegister( self, device, reg, data ):
        err = ErrorCode.errOk
        if self.type == SerialBusType.I2C:
            try:
                self.bus.writeto_mem( device.address, reg, bytes(data) )
            except OSError:
                err = ErrorCode.errLowLevelFail
        elif self.type == SerialBusType.SPI:
            device.pinCS.set( GPIO.LEVEL_LOW )
            try:
                buf = reg.to_bytes( 1 ) + bytes( data )
                self.bus.write( buf )
            except OSError:
                err = ErrorCode.errLowLevelFail
            finally:
                device.pinCS.set( GPIO.LEVEL_HIGH )
        else:
            err = ErrorCode.errNotSupported
        return err

    def readBuffer( self, device, length ):
        data, err = self.writeReadBuffer( device, None, length )
        return data, err

    def writeBuffer( self, device, buffer ):
        _, err = self.writeReadBuffer( device, buffer, 0 )
        return err
    
    def writeReadBuffer( self, device, outBuffer, inLength, ):
        err = ErrorCode.errOk
        data = []
        if self.type == SerialBusType.I2C:
            try:
                if (outBuffer is not None) and (len(outBuffer) > 0):
                    self.bus.writeto( device.address, bytes(outBuffer) )
                if inLength > 0:
                    resp = self.bus.readfrom( device.address, inLength )
                    data = list(resp)
            except OSError:
                err = ErrorCode.errLowLevelFail
        elif self.type == SerialBusType.SPI:
            device.pinCS.set( GPIO.LEVEL_LOW )
            try:
                tempData = bytearray() if outBuffer is None else bytearray(outBuffer)
                diff = inLength - len(tempData)
                if diff > 0:
                    tempData += bytearray( diff )
                self.bus.write_readinto( tempData, tempData)
                if inLength > 0:
                    data = list( tempData[-inLength:] )
            except OSError:
                err = ErrorCode.errLowLevelFail
            finally:
                device.pinCS.set( GPIO.LEVEL_HIGH )
        else:
            err = ErrorCode.errNotSupported
        
        return data, err

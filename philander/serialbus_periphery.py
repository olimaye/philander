"""Provide the serial bus API while relying on the periphery package.

An application should never use this module directly. Instead, the
system factory will provide suitable instances.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["_SerialBus_Periphery" ]

from periphery import I2C, I2CError, SPI, SPIError

from philander.serialbus import SerialBus, SerialBusType
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode

    
class _SerialBus_Periphery( SerialBus ):
    """Periphery serial bus implementation.
    """
    
    def __init__(self):
        super().__init__()
        self.provider = SysProvider.PERIPHERY
        
    @classmethod
    def Params_init( cls, paramDict ):
        """Initialize parameters with default values.
        
        Supported key names and their meanings are:

        ======================    =================================================    ==============================================
        Key                       Range                                                Default
        ======================    =================================================    ==============================================
        SerialBus.SPI.mode        :class:`SPIMode` mode; only for SPI.                 :attr:`SerialBus.DEFAULT_SPI_MODE`.
        SerialBus.SPI.speed       [int|float] maximum SPI clock frequency in Hz.       :attr:`SerialBus.DEFAULT_SPI_SPEED`.
        SerialBus.SPI.bitorder    ["msb"|"lsb"] bit transmission order.                :attr:`SerialBus.DEFAULT_SPI_BIT_ORDER`.
        SerialBus.SPI.bpw         int; bits per word                                   :attr:`SerialBus.DEFAULT_SPI_BITS_PER_WORD`.
        ======================    =================================================    ==============================================
        
        :param dict(str, object) paramDict: Configuration parameters as obtained from :meth:`Params_init`, possibly.
        :return: none
        :rtype: None
        """
        SPIdefaults = {
            "SerialBus.SPI.mode":       SerialBus.DEFAULT_SPI_MODE,
            "SerialBus.SPI.speed":      SerialBus.DEFAULT_SPI_SPEED,
            "SerialBus.SPI.bitorder":   SerialBus.DEFAULT_SPI_BIT_ORDER,
            "SerialBus.SPI.bpw":        SerialBus.DEFAULT_SPI_BITS_PER_WORD,
        }
        SerialBus.Params_init( paramDict )
        if paramDict.get( "SerialBus.type", None ) == SerialBusType.SPI:
            for key, value in SPIdefaults.items():
                if not key in paramDict:
                    paramDict[key] = value
        return None

    def open( self, paramDict ):
        # Scan the parameters
        self.Params_init(paramDict)
        ret = super().open(paramDict)
        if (ret.isOk()):
            if self.type == SerialBusType.I2C:
                self.bus = I2C( self.designator )
            elif self.type == SerialBusType.SPI:
                mode = paramDict["SerialBus.SPI.mode"]
                speed= paramDict["SerialBus.SPI.speed"]
                bitorder = paramDict["SerialBus.SPI.bitorder"]
                bpw  = paramDict["SerialBus.SPI.bpw"]
                self.bus = SPI( self.designator, mode.value, speed, bitorder, bpw )
            else:
                ret = ErrorCode.errNotSupported
                self._status = SerialBus._STATUS_FREE
        return ret
    
    def close(self):
        ret = super().close()
        if not self.bus is None:
            self.bus.close()
        return ret
    
    def transfer(self, device, *, reg=None, outBuf=None, inNum=0):
        """Helper to do the I2C low-level communication and error/exception handling.

        :param [I2C.Message] msgs: The I2C messages to transfer.
        :return: The same messages, possibly filled during read phases.
        :rtype: [I2C.Message], ErrorCode
        """        
        err = ErrorCode.errOk
        resultData = None
        
        outData = []
        if (reg is not None):
            outData = [reg]
        if (outBuf is not None):
            outData += outBuf
        inData = [0] * inNum
        if (len(outData) < 1) and (inNum < 1):
            err = ErrorCode.errInvalidParameter
        else:
            try:
                if self.type == SerialBusType.I2C:
                    msgs = []
                    if len(outData) > 0:
                        msgs = [self.bus.Message( outData ) ]
                    if len( inData )> 0:
                        inMsg = self.bus.Message( inData, read=True)
                        msgs.append( inMsg )
                    self.bus.transfer( device.address, msgs)
                    if inNum > 0:
                        resultData = inMsg.data
                elif self.type == SerialBusType.SPI:
                    # Note that CS activation/de-activation is done by hardware
                    inData = self.bus.transfer(outData+inData)
                    if inNum > 0:
                        resultData = inData[-inNum:]
                else:
                    err = ErrorCode.errNotSupported
            except (I2CError, SPIError):
                err = ErrorCode.errLowLevelFail
            except TypeError:
                err = ErrorCode.errInvalidParameter
            except ValueError:
                err = ErrorCode.errCorruptData
        return resultData, err
        
        
    def readByteRegister( self, device, reg ):
        inData, err = self.transfer( device, reg=reg, inNum=1)
        result = inData[0] if err.isOk() else 0
        return result, err

    def writeByteRegister( self, device, reg, data ):
        _, err = self.transfer( device, reg=reg, outBuf=[data] )
        return err
    
    def readWordRegister( self, device, reg ):
        inData, err = self.transfer( device, reg=reg, inNum=2)
        result = (inData[1] << 8) | inData[0] if err.isOk() else 0
        return result, err

    def writeWordRegister( self, device, reg, data16 ):
        outData = [(data16 & 0xFF), (data16 >> 8)]
        _, err = self.transfer( device, reg=reg, outBuf=outData )
        return err

    def readDWordRegister( self, device, reg ):
        inData, err = self.transfer( device, reg=reg, inNum=4)
        result = (inData[3] << 24) | (inData[2] << 16) | (inData[1] << 8) | inData[0] if err.isOk() else 0
        return result, err

    def writeDWordRegister( self, device, reg, data32 ):
        outData = [(data32 & 0xFF), (data32 >> 8) & 0xFF, (data32 >> 16) & 0xFF, (data32 >> 24)]
        _, err = self.transfer( device, reg=reg, outBuf=outData )
        return err
    
    def readBufferRegister( self, device, reg, length ):
        inData, err = self.transfer( device, reg=reg, inNum=length)
        return inData, err

    def writeBufferRegister( self, device, reg, data ):
        _, err = self.transfer( device, reg=reg, outBuf=data )
        return err

    def readBuffer( self, device, length ):
        inData, err = self.transfer( device, inNum=length)
        return inData, err

    def writeBuffer( self, device, buffer ):
        _, err = self.transfer( device, outBuf=buffer )
        return err
    
    def readWriteBuffer( self, device, inLength, outBuffer ):
        inData, err = self.transfer( device, outBuf=outBuffer, inNum=inLength)
        return inData, err


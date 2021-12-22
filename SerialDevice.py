from Device import Device
from Configurable import Configurable

class SerialDevice( Device, Configurable ):
    
    BUSTYPE_I2C = 10
    BUSTYPE_SPI = 20
    BUSTYPE_UART= 30
    
    _MOD_NONE      = 0
    _MOD_SMBUS     = 1
    _MOD_SMBUS2    = 2
    _MOD_PERIPHERY = 3
    
    def _detectDriverModule( self, busType ):
        ret = SerialDevice._MOD_NONE
        if busType == SerialDevice.BUSTYPE_I2C:
            try:
                from smbus import SMBus
                ret = SerialDevice._MOD_SMBUS
            except ModuleNotFoundError:
                try:
                    from smbus2 import SMBus
                    ret = SerialDevice._MOD_SMBUS2
                except ModuleNotFoundError:
                    try:
                        from periphery import I2C
                        ret = SerialDevice._MOD_PERIPHERY
                    except ModuleNotFoundError:
                        raise
            
        else:
            raise NotImplementedError('Currently, only I2C is supported!')
        return ret

#
# Implementation variants depending on different underlying driver modules
#

# *** SMBus implementation ***

    def _smbus_init( self ):
        if (self.drvMod == SerialDevice._MOD_SMBUS):
            from smbus import SMBus
        else:
            from smbus2 import SMBus
        self.i2c = SMBus( self.busDesignator )
    
    def _smbus_close(self):
        self.i2c.close()
        
    def _smbus_readByte( self, aReg ):
        data = self.i2c.read_byte_data( self.deviceAddress, aReg )
        return data

    def _smbus_readWord( self, aReg ):
        data = self.i2c.read_word_data( self.deviceAddress, aReg )
        return data

    def _smbus_readDWord( self, aReg ):
        L = self._smbus_readWord( aReg )
        H = self._smbus_readWord( aReg+2 )
        ret = (H << 16) + L
        return ret

    def _smbus_readBlock( self, aReg, num ):
        data = self.i2c.read_i2c_block_data( self.deviceAddress, aReg, num )
        return data

    def _smbus_writeByte( self, aReg, data ):
        self.i2c.write_byte_data( self.deviceAddress, aReg, data )

    def _smbus_writeWord( self, aReg, data ):
        self.i2c.write_word_data( self.deviceAddress, aReg, data )

    def _smbus_writeDWord( self, aReg, data ):
        L = data & 0xFFFF
        H = (data & 0xFFFF0000) >> 16
        self._smbus_writeWord( aReg, L )
        self._smbus_writeWord( aReg+2, H )
    
    def _smbus_writeBlock( self, aReg, data ):
        self.i2c.write_i2c_block_data( self.deviceAddress, aReg, data )
    
# *** periphery module implementation ***

    def _periphery_init( self ):
        from periphery import I2C
        self.i2c = I2C( self.busDesignator )
    
    def _periphery_close(self):
        self.i2c.close()
        
    def _periphery_readByte( self, aReg ):
        msgs = [self.i2c.Message([aReg]), self.i2c.Message([0x00], read=True)]
        self.i2c.transfer( self.deviceAddress, msgs)
        return msgs[1].data[0]

    def _periphery_readWord( self, aReg ):
        msgs = [self.i2c.Message([aReg]), self.i2c.Message([0, 0], read=True)]
        self.i2c.transfer( self.deviceAddress, msgs)
        ret = (msgs[1].data[1] << 8) | msgs[1].data[0]
        return ret

    def _periphery_readDWord( self, aReg ):
        msgs = [self.i2c.Message([aReg]), self.i2c.Message([0, 0, 0, 0], read=True)]
        self.i2c.transfer( self.deviceAddress, msgs)
        ret = (msgs[1].data[3] << 24) | (msgs[1].data[2] << 16) | (msgs[1].data[1] << 8) | msgs[1].data[0]
        return ret

    def _periphery_readBlock( self, aReg, num ):
        ba = bytearray(num)
        msgs = [self.i2c.Message([aReg]), self.i2c.Message(ba, read=True)]
        self.i2c.transfer( self.deviceAddress, msgs)
        return msgs[1].data

    def _periphery_writeByte( self, aReg, data ):
        msgs = [self.i2c.Message([aReg, data])]
        self.i2c.transfer( self.deviceAddress, msgs)

    def _periphery_writeWord( self, aReg, data ):
        msgs = [self.i2c.Message([aReg, (data & 0xFF), (data >> 8)])]
        self.i2c.transfer( self.deviceAddress, msgs)

    def _periphery_writeDWord( self, aReg, data ):
        msgs = [self.i2c.Message([aReg, (data & 0xFF), (data >> 8), (data >> 16), (data >> 24)])]
        self.i2c.transfer( self.deviceAddress, msgs)
    
    def _periphery_writeBlock( self, aReg, data ):
        bdata = data
        bdata.insert( 0, aReg )
        msgs = [self.i2c.Message( bdata )]
        self.i2c.transfer( self.deviceAddress, msgs)
    
    #
    # Configurable API
    #
    
    def _scanParameters( self, paramDict ):
        # Scan parameters
        if "SerialDevice.busType" in paramDict:
            self.drvMod = self._detectDriverModule( paramDict["SerialDevice.busType"] )

        if "SerialDevice.busDesignator" in paramDict:
            self.busDesignator = paramDict["SerialDevice.busDesignator"]
        
        if "SerialDevice.deviceAddress" in paramDict:
            self.deviceAddress = paramDict["SerialDevice.deviceAddress"]
                                
    # Nothing to do do:
    # def _applyConfiguration( self ):
    
    #
    # Constructor
    # The only input parameter is a dictionary containing key-value pairs that
    # configure the instance. Regarded key names and their meanings are:
    # SerialDevice.busType      : One of the SerialDevice.BUSTYPE_xxx values.
    # SerialDevice.busDesignator: The bus designator. May be a name or number, such as "/dev/i2c-3" or 1.
    # SerialDevice.deviceAddress: either the I2C address (0x18/0x19) or the state of the SDO line (0/1).
    def __init__( self, paramDict ):
        # Set defaults, where necessary
        self.drvMod = self._detectDriverModule( SerialDevice.BUSTYPE_I2C )
        self.busDesignator = "/dev/i2c-1"
        self.deviceAddress = 0x42
        Configurable.__init__( self, paramDict )
                        
        # Multiplex the different implementations depending on the driver module
        if (self.drvMod==SerialDevice._MOD_SMBUS) or (self.drvMod==SerialDevice._MOD_SMBUS2):
            self._serDevPtr_init = self._smbus_init
            self._serDevPtr_close = self._smbus_close
            self._serDevPtr_readByte = self._smbus_readByte
            self._serDevPtr_readWord = self._smbus_readWord
            self._serDevPtr_readDWord = self._smbus_readDWord
            self._serDevPtr_readBlock = self._smbus_readBlock
            self._serDevPtr_writeByte = self._smbus_writeByte
            self._serDevPtr_writeWord = self._smbus_writeWord
            self._serDevPtr_writeDWord = self._smbus_writeDWord
            self._serDevPtr_writeBlock = self._smbus_writeBlock
        elif (self.drvMod==SerialDevice._MOD_PERIPHERY):
            self._serDevPtr_init = self._periphery_init
            self._serDevPtr_close = self._periphery_close
            self._serDevPtr_readByte = self._periphery_readByte
            self._serDevPtr_readWord = self._periphery_readWord
            self._serDevPtr_readDWord = self._periphery_readDWord
            self._serDevPtr_readBlock = self._periphery_readBlock
            self._serDevPtr_writeByte = self._periphery_writeByte
            self._serDevPtr_writeWord = self._periphery_writeWord
            self._serDevPtr_writeDWord = self._periphery_writeDWord
            self._serDevPtr_writeBlock = self._periphery_writeBlock
        else:
            raise NotImplementedError('Driver module ' + str(self.drvMod) + ' is not supported.')

    def init( self ):
        self._serDevPtr_init()
        Configurable.init(self)
    
    def close(self):
        self._serDevPtr_close()
        
    def readByte( self, aReg ):
        return self._serDevPtr_readByte(aReg )

    def readWord( self, aReg ):
        return self._serDevPtr_readWord( aReg )

    def readDWord( self, aReg ):
        return self._serDevPtr_readDWord( aReg )

    def readBlock( self, aReg, num ):
        return self._serDevPtr_readBlock( aReg, num )

    def writeByte( self, aReg, data ):
        self._serDevPtr_writeByte( aReg, data )

    def writeWord( self, aReg, data ):
        self._serDevPtr_word( aReg, data )

    def writeDWord( self, aReg, data ):
        self._serDevPtr_writeDWord( aReg, data )
    
    def writeBlock( self, aReg, data ):
        self._serDevPtr_writeBlock( aReg, data )

    #
    # Device API
    #
    
    def getReg( self, register ):
        return self.readByte( register )
    
    def setReg( self, register, data ):
        self.writeByte( register, data )

    def getWReg( self, register ):
        return self.readWord( register )
    
    def setWReg( self, register, data ):
        self.writeWord( register, data )


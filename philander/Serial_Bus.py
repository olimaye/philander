from module import Module
from systypes import ErrorCode
from simbus import SimBusNull

class Serial_Bus_Device( Module ):
    DEFAULT_ADDRESS     = 0x21
    
    def __init__(self):
        self.serial_bus   = None
        self.deviceAddress = Serial_Bus_Device.DEFAULT_ADDRESS

    @classmethod
    def Params_init( cls, paramDict ):
        # Fill paramDict with defaults
        paramDict["Serial_Bus_Device.deviceAddress"] = paramDict.get("Serial_Bus_Device.deviceAddress", Serial_Bus_Device.DEFAULT_ADDRESS)
        Serial_Bus.Params_init(paramDict)
        return None
    
    def open(self, paramDict):
        result = ErrorCode.errOk
        if (self.serial_bus is None ):
            paramDict["Serial_Bus_Device.deviceAddress"] = paramDict.get("Serial_Bus_Device.deviceAddress", Serial_Bus_Device.DEFAULT_ADDRESS)
            self.deviceAddress = paramDict["Serial_Bus_Device.deviceAddress"]
            if ("Serial_Bus_Device.bus" in paramDict):
                sb = paramDict["Serial_Bus_Device.bus"]
                if not( isinstance(sb, Serial_Bus)):
                    result = ErrorCode.errInvalidParameter
            else:
                sb = Serial_Bus()
                if (sb is None):
                    result = ErrorCode.errExhausted
                else:
                    result = sb.open(paramDict)
                if (result == ErrorCode.errOk):
                    paramDict["Serial_Bus_Device.bus"] = sb
            if (result == ErrorCode.errOk):
                result = sb.attach( self )
        else:
            result = ErrorCode.errResourceConflict
        return result

    def close(self):
        result = ErrorCode.errOk
        if not (self.serial_bus is None ):
            result = self.serial_bus.detach(self)
        return result
    
    def setRunLevel(self, level):
        del level
        return ErrorCode.errNotImplemented
    
    def isAttached(self):
        return not(self.serial_bus is None)

    # This method provides 8 bit register read access to a device. First, a
    # byte is sent to the device. This may address the register to read out.
    # Then, one byte - the register content - is read back from the device.
    # @param[in] reg The data to write to this device. This may be a register
    # identification or some sort of command.
    # @param[out] data8 A one-byte buffer to hold the response of the device.
    # Depending on the device protocol semantics, this may be the register content
    # or the command response. Must not be NULL.
    # @return An error code indicating success or the reason of failure.
    def read_Reg_Byte( self, reg ):
        return self.serial_bus.read_Reg_Byte( self, reg )

    # Assuming a register-type access, this function writes a byte register.
    # The register value is written first, followed by the given data parameter.
    # @param[in] reg The register number. This addresses the place where to put the
    # content. Depending on the device, this could also be some kind of command.
    # @param[in] data8 The data to write to the addressed register.
    # @return An error code indicating success or the reason of failure.
    def write_Reg_Byte( self, reg, data8 ):
        return self.serial_bus.write_Reg_Byte( self, reg, data8)

    # This provides register read access for 16 bit data words. After a byte is sent,
    # two bytes are read from the device. The word is always read in little endian order
    # i.e. the least significant low-byte first, the highes-significant high-byte second.
    # @param[in] reg The register identification or command to write to this device.
    # @param[out] data16 The response of the device. Depending on the
    # device, this may be the register content or the command response. Must not be
    # NULL.
    # Note that the data is sent in little endian order, i.e. the first byte received
    # is interpreted as the least significant byte (lower 8 bits).
    # @return An error code indicating success or the reason of failure.
    def read_Reg_Word( self, reg ):
        return self.serial_bus.read_Reg_Word( self, reg )

    # <p>Sends a register number followed by a 16 bit word down to the device
    # addressed. Use this function, when writing word-size data to a serial
    # device.</p>
    # <p>The data is sent in little endian, i.e. the least-significant byte is
    # sent first.</p>
    # @param[in] reg The register number. This addresses the place where to put the
    # content. Depending on the device, this could also be some kind of command.
    # @param[in] data16 The word to store to the given register.
    # @return An error code indicating success or the reason of failure.
    def write_Reg_Word( self, reg, data16 ):
        return self.serial_bus.write_Reg_Word( self, reg, data16 )

    # This provides register read access for 32 bit data words. After a byte is sent,
    # four bytes are read from the device. The dword is always read in little endian order
    # i.e. the least significant low-byte first, the highes-significant high-byte last.
    # @param[in] reg The register identification or command to write to this device.
    # @param[out] data32 The response of the device. Depending on the
    # device, this may be the register content or the command response. Must not be
    # NULL.
    # Note that the data is sent in little endian order, i.e. the first byte received
    # is interpreted as the least significant byte (lower 8 bits).
    # @return An error code indicating success or the reason of failure.
    def read_Reg_DWord( self, reg ):
        return self.serial_bus.read_Reg_DWord( self, reg )

    # <p>Sends a register number followed by a 32 bit dword down to the device
    # addressed. Use this function, when writing double word-size data to a serial
    # device.</p>
    # <p>The data is sent in little endian, i.e. the least-significant byte is
    # sent first.</p>
    # @param[in] reg The register number. This addresses the place where to put the
    # content. Depending on the device, this could also be some kind of command.
    # @param[in] data32 The dword to store to the given register.
    # @return An error code indicating success or the reason of failure.
    def write_Reg_DWord( self, reg, data32 ):
        return self.serial_bus.write_Reg_DWord( self, reg, data32 )
    
    # <p>Multi-byte read access to a register-type serial bus device.
    # After sending one byte of command or register address, a
    # number of bytes is read back into the buffer provided.</p>
    # <p>For SPI, the byte received during transmission of the <code>reg</code>
    # byte is discarded. It does not appear in the underlying input queue, nor in
    # the response buffer. Then, enough dummy traffic is generated to receive
    # <code>len</code> number of bytes.</p>
    # @param[in] reg The byte to send. May be a command or register address,
    # according to the protocol of the addressed device.
    # @param[out] buffer A buffer to place the data read from the device. The
    # first byte coming from the device, is put at index zero, the second one at
    # index one and so on. This argument must not be NULL.
    # @param[in] len   The number of bytes to read from the device. At the same
    # time, this is the minimum size that the buffer is assumed to have. This value
    # should be greater than zero.
    # @return An error code indicating success or the reason of failure.
    def read_Reg_Buffer( self, reg, length ):
        return self.serial_bus.read_Reg_Buffer( self, reg, length )

    #
    #
    #
    def write_Reg_Buffer( self, reg, buffer ):
        return self.serial_bus.write_Reg_Buffer( self, reg, buffer )

    # Directly reads multiple bytes from the given device.
    # @param[out] buffer A buffer to place the data read from the device. The
    # first byte coming from the device, is put at index zero, the second one at
    # index one and so on. This argument must not be NULL.
    # @param[in] len   The number of bytes to read from the device. At the same
    # time, this is the minimum size that the buffer is assumed to have. This value
    # should be greater than zero.
    # @return An error code indicating success or the reason of failure.
    def read_Buffer( self, buffer, length ):
        return self.serial_bus.read_Buffer( self, buffer, length)

    # Writes the given data to the device specified.
    # Note that, in SPI mode, the data received during transmission, is discarded.
    # @param[in] buffer A buffer holding the data to send to the device. Must not
    # be NULL. Must be at least as large as indicated by the <em>len</em> parameter.
    # @param[in] len The number of bytes to send. Should be positive.
    # @return An error code indicating success or the reason of failure.
    def write_Buffer( self, buffer, length ):
        return self.serial_bus.write_Buffer( self, buffer, length)
    
    # Writes and reads a number of bytes.
    # Due to the duplex nature of SPI, transmission and reception of data
    # occurs simultaneously. For this reason, each buffer must either be NULL or
    # be at least as large as the maximum of both length parameters!
    # @param[in] device Address of the device to communicate with.
    # Must not be NULL.
    # @param[out] inBuffer A buffer to hold the incoming data received from the
    # device.
    # Must not be NULL. Must be at least as large as given by the length indicator.
    # @param[in] inLen The number of bytes to read. This is the minimum size that
    # the input buffers MUST have. Indeed, the buffer could be larger, but never be
    # smaller than the number given with this parameter.
    # This value should be greater than zero.
    # @param[in] outBuffer A buffer holding the data to send to the device. Must not
    # be NULL.
    # @param[in] outLen The number of bytes send. The output buffer should be at
    # least as large as given by this parameter.
    # This value should be greater than zero.
    # If the underlying protocol is SPI, the size of the input and output buffers
    # must either be the same or less than dword size. In other words: Different
    # buffer sizes can be handled as long as the larger one does not exceed
    # dword size.
    # @return An error code indicating success or the reason of failure.
    # @see #Serial_Bus_write_Buffer
    # @see #Serial_Bus_read_Buffer
    def read_write_Buffer( self, device, inBuffer, inLen, outBuffer, outLen ):
        return self.serial_bus.read_write_Buffer( self, inBuffer, inLen, outBuffer, outLen)

    
class Serial_Bus( Module ):
    
    TYPE_I2C = 10
    TYPE_SPI = 20
    TYPE_UART= 30
    
    _IMPLMOD_NONE      = 0
    _IMPLMOD_SMBUS     = 1
    _IMPLMOD_SMBUS2    = 2
    _IMPLMOD_PERIPHERY = 3
    _IMPLMOD_SIM	   = 4

    _STATUS_FREE		= 1
    _STATUS_OPEN		= 2
    
    #
    # Internal helpers
    #
    def __init__(self):
        self._attachedDevices = list()
        self._status = Serial_Bus._STATUS_FREE
        
    def _detectDriverModule( self, busType ):
        ret = Serial_Bus._IMPLMOD_NONE
        if busType == Serial_Bus.TYPE_I2C:
            try:
                from smbus2 import SMBus, i2c_msg
                ret = Serial_Bus._IMPLMOD_SMBUS2
            except ModuleNotFoundError:
                try:
                    from periphery import I2C
                    ret = Serial_Bus._IMPLMOD_PERIPHERY
                except ModuleNotFoundError:
                    ret = Serial_Bus._IMPLMOD_SIM
        else:
            raise NotImplementedError('Currently, only I2C is supported!')
        return ret

    #
    # Implementation variants depending on different underlying driver modules
    #

    # *** SMBus implementation ***

    def _smbus_open( self, paramDict ):
        try:
            if (self.drvMod == Serial_Bus._IMPLMOD_SMBUS):
                from smbus import SMBus
                self.msg = None
            elif (self.drvMod == Serial_Bus._IMPLMOD_SMBUS2):
                from smbus2 import SMBus, i2c_msg
                self.msg = i2c_msg
            self.bus = SMBus( self.busDesignator )
        except Exception as exc:
            raise SystemError("Couldn't initialize serial bus ["+str(self.busDesignator)+"]. Designator right? Access to interface granted?") from exc
        return None

    def _smbus_close( self ):
        return self.bus.close()
    
    def _smbus_readRegByte( self, devAdr, aReg ):
        return self.bus.read_byte_data( devAdr, aReg )
    
    def _smbus_writeRegByte( self, devAdr, aReg, data ):
        return self.bus.write_byte_data( devAdr, aReg, data )
            
    def _smbus_readRegWord( self, devAdr, aReg ):
        return self.bus.read_word_data( devAdr, aReg )
    
    def _smbus_writeRegWord( self, devAdr, aReg, data ):
        return self.bus.write_word_data( devAdr, aReg, data )
            
    def _smbus_readRegDWord( self, devAdr, aReg ):
        L = self.bus.read_word_data( devAdr, aReg )
        H = self.bus.read_word_data( devAdr, aReg+2 )
        ret = (H << 16) + L
        return ret

    def _smbus_writeRegDWord( self, devAdr, aReg, data ):
        L = data & 0xFFFF
        H = (data & 0xFFFF0000) >> 16
        self.bus.write_word_data( devAdr, aReg, L )
        self.bus.write_word_data( devAdr, aReg+2, H )
        return None
    
    def _smbus_readRegBlock( self, devAdr, aReg, num ):
        if (num <= 32 ):
            ret = self.bus.read_i2c_block_data( devAdr, aReg, num )
        else:
            msg1 = self.msg.write( devAdr, [aReg] )
            msg2 = self.msg.read( devAdr, num )
            self.bus.i2c_rdwr( msg1, msg2 )
            ret = list(msg2)
        return ret
    
    def _smbus_writeRegBlock( self, devAdr, aReg, data ):
        if (len(data) <= 32 ):
            self.bus.write_i2c_block_data( devAdr, aReg, data )
        else:
            bdata = data
            bdata.insert( 0, aReg )
            msg = self.msg.write( devAdr, bdata )
            self.bus.i2c_rdwr( msg )
        return None
            
   
    # *** periphery module implementation ***

    def _periphery_open( self, paramDict ):
        from periphery import I2C
        self.bus = I2C( self.busDesignator )
    
    def _periphery_close(self):
        self.bus.close()
        
    def _periphery_readRegByte( self, devAdr, aReg ):
        msgs = [self.bus.Message([aReg]), self.bus.Message([0x00], read=True)]
        self.bus._transfer( devAdr, msgs)
        return msgs[1].data[0]

    def _periphery_writeRegByte( self, devAdr, aReg, data ):
        msgs = [self.bus.Message([aReg, data])]
        self.bus._transfer( devAdr, msgs)
        return None

    def _periphery_readRegWord( self, devAdr, aReg ):
        msgs = [self.bus.Message([aReg]), self.bus.Message([0, 0], read=True)]
        self.bus._transfer( devAdr, msgs)
        ret = (msgs[1].data[1] << 8) | msgs[1].data[0]
        return ret

    def _periphery_writeRegWord( self, devAdr, aReg, data ):
        msgs = [self.bus.Message([aReg, (data & 0xFF), (data >> 8)])]
        self.bus._transfer( devAdr, msgs)
        return None

    def _periphery_readRegDWord( self, devAdr, aReg ):
        msgs = [self.bus.Message([aReg]), self.bus.Message([0, 0, 0, 0], read=True)]
        self.bus._transfer( devAdr, msgs)
        ret = (msgs[1].data[3] << 24) | (msgs[1].data[2] << 16) | (msgs[1].data[1] << 8) | msgs[1].data[0]
        return ret

    def _periphery_writeRegDWord( self, devAdr, aReg, data ):
        msgs = [self.bus.Message([aReg, (data & 0xFF), (data >> 8), (data >> 16), (data >> 24)])]
        self.bus._transfer( devAdr, msgs)
        return None
    
    def _periphery_readRegBlock( self, devAdr, aReg, num ):
        ba = bytearray(num)
        msgs = [self.bus.Message([aReg]), self.bus.Message(ba, read=True)]
        self.bus._transfer( devAdr, msgs)
        return msgs[1].data

    def _periphery_writeRegBlock( self, devAdr, aReg, data ):
        bdata = data
        bdata.insert( 0, aReg )
        msgs = [self.bus.Message( bdata )]
        self.bus._transfer( devAdr, msgs)
        return None

    # *** Serial Bus simulator implementation ***

    def _sbsim_findSim( self, devAdr ):
        sim = self._defaultSim
        for dev in self._attachedDevices:
            if (dev.deviceAddress == devAdr):
                if (hasattr(dev, 'sim')):
                    sim = dev.sim
                break
        return sim
    
    def _sbsim_open( self, paramDict ):
        self._defaultSim = SimBusNull()
        self._defaultSim.open(paramDict)
    
    def _sbsim_close(self):
        self._defaultSim.close()
        
    def _sbsim_readRegByte( self, devAdr, aReg ):
        sim = self._sbsim_findSim(devAdr)
        return sim.readRegByte( aReg )

    def _sbsim_writeRegByte( self, devAdr, aReg, data ):
        sim = self._sbsim_findSim(devAdr)
        return sim.writeRegByte( aReg, data )
    
    def _sbsim_readRegWord( self, devAdr, aReg ):
        sim = self._sbsim_findSim(devAdr)
        return sim.readRegWord( aReg )

    def _sbsim_writeRegWord( self, devAdr, aReg, data ):
        sim = self._sbsim_findSim(devAdr)
        return sim.writeRegWord( aReg, data )

    def _sbsim_readRegDWord( self, devAdr, aReg ):
        sim = self._sbsim_findSim(devAdr)
        return sim.readRegDWord( aReg )

    def _sbsim_writeRegDWord( self, devAdr, aReg, data ):
        sim = self._sbsim_findSim(devAdr)
        return sim.writeRegDWord( aReg, data )
    
    def _sbsim_readRegBlock( self, devAdr, aReg, num ):
        sim = self._sbsim_findSim(devAdr)
        return sim.readRegBlock( aReg, num )

    def _sbsim_writeRegBlock( self, devAdr, aReg, data ):
        sim = self._sbsim_findSim(devAdr)
        return sim.writeRegBlock( aReg, data )

    
    #
    # Module API
    #
    

    # The only input parameter is a dictionary containing key-value pairs that
    # configure the instance. Regarded key names and their meanings are:
    # Serial_Bus.busType      : One of the Serial_Bus.TYPE_xxx values.
    # Serial_Bus.busDesignator: The bus designator. May be a name or number, such as "/dev/i2c-3" or 1.
    # Serial_Bus.deviceAddress: either the I2C address (0x18/0x19) or the state of the SDO line (0/1).
    @classmethod
    def Params_init( cls, paramDict ):
        # Fill paramDict with defaults
        if not ("Serial_Bus.busType" in paramDict):
            paramDict["Serial_Bus.busType"] = Serial_Bus.TYPE_I2C
        if not ("Serial_Bus.busDesignator" in paramDict):
            paramDict["Serial_Bus.busDesignator"] = "/dev/i2c-1"
        return None

    #
    #
    #
    def open(self, paramDict):
        ret = ErrorCode.errOk
        # Retrieve defaults
        defaults = {}
        self.Params_init( defaults )
        # Scan parameters
        if "Serial_Bus.busType" in paramDict:
            self.drvMod = self._detectDriverModule( paramDict["Serial_Bus.busType"] )
        else:
            self.drvMod = self._detectDriverModule( defaults["Serial_Bus.busType"] )

        if "Serial_Bus.busDesignator" in paramDict:
            self.busDesignator = paramDict["Serial_Bus.busDesignator"]
        else:
            self.busDesignator = defaults["Serial_Bus.busDesignator"]

        # Multiplex the different implementations depending on the driver module
        if (self.drvMod==Serial_Bus._IMPLMOD_SMBUS) or (self.drvMod==Serial_Bus._IMPLMOD_SMBUS2):
            self._serDevPtr_open = self._smbus_open
            self._serDevPtr_close = self._smbus_close
            self._serDevPtr_readRegByte = self._smbus_readRegByte
            self._serDevPtr_writeRegByte = self._smbus_writeRegByte
            self._serDevPtr_readRegWord = self._smbus_readRegWord
            self._serDevPtr_writeRegWord = self._smbus_writeRegWord
            self._serDevPtr_readRegDWord = self._smbus_readRegDWord
            self._serDevPtr_writeRegDWord = self._smbus_writeRegDWord
            self._serDevPtr_readRegBlock = self._smbus_readRegBlock
            self._serDevPtr_writeRegBlock = self._smbus_writeRegBlock
        elif (self.drvMod==Serial_Bus._IMPLMOD_PERIPHERY):
            self._serDevPtr_open = self._periphery_open
            self._serDevPtr_close = self._periphery_close
            self._serDevPtr_readRegByte = self._periphery_readRegByte
            self._serDevPtr_writeRegByte = self._periphery_writeRegByte
            self._serDevPtr_readRegWord = self._periphery_readRegWord
            self._serDevPtr_writeRegWord = self._periphery_writeRegWord
            self._serDevPtr_readRegDWord = self._periphery_readRegDWord
            self._serDevPtr_writeRegDWord = self._periphery_writeRegDWord
            self._serDevPtr_readRegBlock = self._periphery_readRegBlock
            self._serDevPtr_writeRegBlock = self._periphery_writeRegBlock
        elif (self.drvMod==Serial_Bus._IMPLMOD_SIM):
            self._serDevPtr_open = self._sbsim_open
            self._serDevPtr_close = self._sbsim_close
            self._serDevPtr_readRegByte = self._sbsim_readRegByte
            self._serDevPtr_writeRegByte = self._sbsim_writeRegByte
            self._serDevPtr_readRegWord = self._sbsim_readRegWord
            self._serDevPtr_writeRegWord = self._sbsim_writeRegWord
            self._serDevPtr_readRegDWord = self._sbsim_readRegDWord
            self._serDevPtr_writeRegDWord = self._sbsim_writeRegDWord
            self._serDevPtr_readRegBlock = self._sbsim_readRegBlock
            self._serDevPtr_writeRegBlock = self._sbsim_writeRegBlock
        else:
            raise NotImplementedError('Driver module ' + str(self.drvMod) + ' is not supported.')
        # Allocate resources
        self._serDevPtr_open( paramDict )
        self._status = Serial_Bus._STATUS_OPEN
        return ret

    #
    #
    #
    def close(self):
        self._serDevPtr_close()
        self._status = Serial_Bus._STATUS_FREE
        
    #
    #
    #
    def setRunLevel(self, level):
        del level
        return ErrorCode.errNotImplemented

    # Determines, if the given bus is already open.
    # @param[in] self The bus in question.
    # @return An <code>ErrorCode</code>: <code>errOk</code>, if the bus is already open; <code>errUnavailable</code>, if it has
    # not been opened before; Any other value to indicate the failure or reason, why this information
    # could not be retrieved.
    def isOpen( self ):
        result = ErrorCode.errOk
        if (self._status == Serial_Bus._STATUS_OPEN):
            result = ErrorCode.errOk
        else:
            result = ErrorCode.errUnavailable
        return result

    # Attaches a device to a serial bus. If this bus is not open, yet, then it will get opened, now.
    # @param[in] self The bus to attach the device to.
    # @param[in] device The device to be attached.
    # @return An error code indicating success or the reason of failure.
    def attach( self, device ):
        result = ErrorCode.errOk
        if (device.serial_bus == self):
            result = ErrorCode.errOk
        elif (device.serial_bus != None):
            result = ErrorCode.errResourceConflict
        else:
            # Check if bus is open, already
            result = self.isOpen()
            if (result == ErrorCode.errUnavailable):
                params = {}
                self.Params_init(params)
                result = self.open(params)
            if (result == ErrorCode.errOk):
                # Mark the device as being attached
                device.serial_bus = self
                if not (device in self._attachedDevices):
                    self._attachedDevices.append( device )
        return result
            
            

    # Detaches a device from a serial bus. If this is the last device on the bus, that bus is
    # closed, automatically.
    # @param[in] self The bus to detach the device from.
    # @param[in] device The device to be detached.
    # @return An error code indicating success or the reason of failure.
    def detach( self, device ):
        result = ErrorCode.errOk
        if (device.serial_bus == self):
            device.serial_bus = None
            self._attachedDevices.remove( device )
            if ( len(self._attachedDevices) < 1 ):
                self.close()
        else:
            result = ErrorCode.errResourceConflict
        return result

    # Determines, if the given device is already attached to some bus.
    # @param[in] device The device in question.
    # @return An error code. <code>errOk</code>, if the bus is already attached to some bus;
    # <code>errUnavailable</code>, if it has not been attached before;
    # Any other value to indicate the failure or reason, why this information
    # could not be retrieved.
    def isAttached( self, device ):
        result = ErrorCode.errOk
        if (device in self.attachedDevices):
            result = ErrorCode.errOk
        else:
            result = ErrorCode.errUnavailable
        return result
            
    # This method provides 8 bit register read access to a device. First, a
    # byte is sent to the device. This may address the register to read out.
    # Then, one byte - the register content - is read back from the device.
    # @param[in] device The device to communicate with. Must not be NULL.
    # @param[in] reg The data to write to this device. This may be a register
    # identification or some sort of command.
    # @param[out] data8 A one-byte buffer to hold the response of the device.
    # Depending on the device protocol semantics, this may be the register content
    # or the command response. Must not be NULL.
    # @return An error code indicating success or the reason of failure.
    def read_Reg_Byte( self, device, reg ):
        data = self._serDevPtr_readRegByte(device.deviceAddress, reg )
        return data, ErrorCode.errOk

    # Assuming a register-type access, this function writes a byte register.
    # The register value is written first, followed by the given data parameter.
    # @param[in] device The device to communicate with. Must not be NULL.
    # @param[in] reg The register number. This addresses the place where to put the
    # content. Depending on the device, this could also be some kind of command.
    # @param[in] data8 The data to write to the addressed register.
    # @return An error code indicating success or the reason of failure.
    def write_Reg_Byte( self, device, reg, data8 ):
        self._serDevPtr_writeRegByte(device.deviceAddress, reg, data8)
        return ErrorCode.errOk

    # This provides register read access for 16 bit data words. After a byte is sent,
    # two bytes are read from the device. The word is always read in little endian order
    # i.e. the least significant low-byte first, the highes-significant high-byte second.
    # @param[in] device The device to communicate with. Must not be NULL.
    # @param[in] reg The register identification or command to write to this device.
    # @param[out] data16 The response of the device. Depending on the
    # device, this may be the register content or the command response. Must not be
    # NULL.
    # Note that the data is sent in little endian order, i.e. the first byte received
    # is interpreted as the least significant byte (lower 8 bits).
    # @return An error code indicating success or the reason of failure.
    def read_Reg_Word( self, device, reg ):
        data = self._serDevPtr_readRegWord( device.deviceAddress, reg )
        return data, ErrorCode.errOk

    # <p>Sends a register number followed by a 16 bit word down to the device
    # addressed. Use this function, when writing word-size data to a serial
    # device.</p>
    # <p>The data is sent in little endian, i.e. the least-significant byte is
    # sent first.</p>
    # @param[in] device The device to communicate with. Must not be NULL.
    # @param[in] reg The register number. This addresses the place where to put the
    # content. Depending on the device, this could also be some kind of command.
    # @param[in] data16 The word to store to the given register.
    # @return An error code indicating success or the reason of failure.
    def write_Reg_Word( self, device, reg, data16 ):
        self._serDevPtr_writeRegWord( device.deviceAddress, reg, data16 )
        return ErrorCode.errOk

    # This provides register read access for 32 bit data words. After a byte is sent,
    # four bytes are read from the device. The dword is always read in little endian order
    # i.e. the least significant low-byte first, the highes-significant high-byte last.
    # @param[in] device The device to communicate with. Must not be NULL.
    # @param[in] reg The register identification or command to write to this device.
    # @param[out] data32 The response of the device. Depending on the
    # device, this may be the register content or the command response. Must not be
    # NULL.
    # Note that the data is sent in little endian order, i.e. the first byte received
    # is interpreted as the least significant byte (lower 8 bits).
    # @return An error code indicating success or the reason of failure.
    def read_Reg_DWord( self, device, reg ):
        data = self._serDevPtr_readRegDWord( device.deviceAddress, reg )
        return data, ErrorCode.errOk

    # <p>Sends a register number followed by a 32 bit dword down to the device
    # addressed. Use this function, when writing double word-size data to a serial
    # device.</p>
    # <p>The data is sent in little endian, i.e. the least-significant byte is
    # sent first.</p>
    # @param[in] device The device to communicate with. Must not be NULL.
    # @param[in] reg The register number. This addresses the place where to put the
    # content. Depending on the device, this could also be some kind of command.
    # @param[in] data32 The dword to store to the given register.
    # @return An error code indicating success or the reason of failure.
    def write_Reg_DWord( self, device, reg, data32 ):
        self._serDevPtr_writeRegDWord( device.deviceAddress, reg, data32 )
        return ErrorCode.errOk
    
    # <p>Multi-byte read access to a register-type serial bus device.
    # After sending one byte of command or register address, a
    # number of bytes is read back into the buffer provided.</p>
    # <p>For SPI, the byte received during transmission of the <code>reg</code>
    # byte is discarded. It does not appear in the underlying input queue, nor in
    # the response buffer. Then, enough dummy traffic is generated to receive
    # <code>len</code> number of bytes.</p>
    # @param[in] device The device to communicate with. Must not be NULL.
    # @param[in] reg The byte to send. May be a command or register address,
    # according to the protocol of the addressed device.
    # @param[out] buffer A buffer to place the data read from the device. The
    # first byte coming from the device, is put at index zero, the second one at
    # index one and so on. This argument must not be NULL.
    # @param[in] len   The number of bytes to read from the device. At the same
    # time, this is the minimum size that the buffer is assumed to have. This value
    # should be greater than zero.
    # @return An error code indicating success or the reason of failure.
    def read_Reg_Buffer( self, device, reg, length ):
        data = self._serDevPtr_readRegBlock( device.deviceAddress, reg, length )
        return data, ErrorCode.errOk

    #
    #
    #
    def write_Reg_Buffer( self, device, reg, buffer ):
        self._serDevPtr_writeRegBlock( device.deviceAddress, reg, buffer )
        return ErrorCode.errOk

    # Directly reads multiple bytes from the given device.
    # @param[in] device The device to communicate with. Must not be NULL.
    # @param[out] buffer A buffer to place the data read from the device. The
    # first byte coming from the device, is put at index zero, the second one at
    # index one and so on. This argument must not be NULL.
    # @param[in] len   The number of bytes to read from the device. At the same
    # time, this is the minimum size that the buffer is assumed to have. This value
    # should be greater than zero.
    # @return An error code indicating success or the reason of failure.
    def read_Buffer( self, device, buffer, length ):
        raise NotImplementedError()

    # Writes the given data to the device specified.
    # Note that, in SPI mode, the data received during transmission, is discarded.
    # @param[in] device The device to communicate with. Must not be NULL.
    # @param[in] buffer A buffer holding the data to send to the device. Must not
    # be NULL. Must be at least as large as indicated by the <em>len</em> parameter.
    # @param[in] len The number of bytes to send. Should be positive.
    # @return An error code indicating success or the reason of failure.
    def write_Buffer( self, device, buffer, length ):
        raise NotImplementedError()
    
    # Writes and reads a number of bytes.
    # Due to the duplex nature of SPI, transmission and reception of data
    # occurs simultaneously. For this reason, each buffer must either be NULL or
    # be at least as large as the maximum of both length parameters!
    # @param[in] device Address of the device to communicate with.
    # Must not be NULL.
    # @param[out] inBuffer A buffer to hold the incoming data received from the
    # device.
    # Must not be NULL. Must be at least as large as given by the length indicator.
    # @param[in] inLen The number of bytes to read. This is the minimum size that
    # the input buffers MUST have. Indeed, the buffer could be larger, but never be
    # smaller than the number given with this parameter.
    # This value should be greater than zero.
    # @param[in] outBuffer A buffer holding the data to send to the device. Must not
    # be NULL.
    # @param[in] outLen The number of bytes send. The output buffer should be at
    # least as large as given by this parameter.
    # This value should be greater than zero.
    # If the underlying protocol is SPI, the size of the input and output buffers
    # must either be the same or less than dword size. In other words: Different
    # buffer sizes can be handled as long as the larger one does not exceed
    # dword size.
    # @return An error code indicating success or the reason of failure.
    # @see #Serial_Bus_write_Buffer
    # @see #Serial_Bus_read_Buffer
    def read_write_Buffer( self, device, inBuffer, inLen, outBuffer, outLen ):
        raise NotImplementedError()

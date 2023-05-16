"""Serial bus convergence layer for smbus, smbus2, periphery or simulative implementation.

Provide a common API for serial bus communication (I2C / SPI).
This interface is to to abstract from details of the implementation.

Basically, there are two main classes: ``SerialBus`` and ``SerialBusDevice``.
The ``SerialBus`` class unifies the implementations like smbus or periphery
by providing similar communication functions, such as read/write byte,
word and buffer data.

The ``SerialBusDevice`` carries specific information for a specific bus
participant, such as its address.
For that reason, every read or write function of the ``SerialBus`` class needs
an ``SerialBusDevice`` instance as a parameter. For convenience, read and
write functions are also available at the ``SerialBusDevice`` class,
delegating their calls to the matching functions in ``SerialBus`` along
with their self-reference.

For the sake of consistency, each ``SerialBusDevice`` must be mated with
a certain ``SerialBus`` in order to work, properly. This process is called
*attaching a device to a bus*. Several devices may be attached to the
same bus. However, a single device may only attached to at most one bus.
After attaching, the bus and device are double-linked to each other:
The bus has a list of attached devices, while a device has a reference
to the bus it is attached to.  
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["SerialBus", "SerialBusDevice", "SerialBusProvider", "SerialBusType"]
from enum import unique, auto, Enum
from module import Module
from systypes import ErrorCode
from simdev import SimDevNull

class SerialBusDevice( Module ):
    """Reflect a specific device communicating over a serial bus.
    
    As its main information, an instance of ``SerialBusDevice`` is to
    hold specific information of that single device, such as its unique
    bus address. This class is meant to be sub-classed by implementations
    for real devices.
    
    Before using a device for communication, it must be attached to a
    bus by calling :meth:`SerialBus.attach`. However, a device's
    :meth:`isAttached` function may be used to check, whether it has
    been attached to a bus, already.
    """
    DEFAULT_ADDRESS     = 0x21
    
    def __init__(self):
        self.serialBus   = None
        self.deviceAddress = SerialBusDevice.DEFAULT_ADDRESS

    @classmethod
    def Params_init( cls, paramDict ):
        """Initialize the set of configuration parameters with supported options.
        Supported configuration key names and their meanings are:
        
        * ``SerialBusDevice.deviceAddress``: The address of the device.\
        The value should be given as an integer number.\
        Must be unique in that, a serial bus does not allow two devices\
        with the same address being attached.\
        Defaults to :attr:`DEFAULT_ADDRESS`.
        
        Also see :meth:`.module.Module.Params_init`.
        
        :param dict(str, object) paramDict: Dictionary mapping option\
        names to their respective values.
        :returns: none
        :rtype: None
        """
        paramDict["SerialBusDevice.deviceAddress"] = paramDict.get("SerialBusDevice.deviceAddress", SerialBusDevice.DEFAULT_ADDRESS)
        SerialBus.Params_init(paramDict)
        return None
    
    def open(self, paramDict):
        """Opens this serial device and puts it into a usable state.
        
        If this device has been attached to some bus, already, this method
        returns an error code.
        Otherwise, it tries to do this attachment as follows:
        
        * If the ``paramDict`` configuration parameters contain the\
        ``SerialBusDevice.bus`` key, the associated value object is checked\
        to be an instance of ``SerialBus``. If successful, this device\
        is attached to that bus. Otherwise, an error code is returned.
        * If no bus instance is passed in, one is created and opened\
        using the same ``paramDict`` dictionary of options. If successful,\
        this device gets attached to that new bus. Upon return, the caller\
        might retrieve a reference to the new bus from the parameter\
        dictionary entry with key ``SerialBusDevice.bus``, or by\
        reading the :attr:`SerialBusDevice.serialBus` attribute.
                
        Also see: :meth:`.module.Module.open`.
        
        :param dict(str, object) paramDict: Configuration parameters as\
        obtained from :meth:`Params_init`, possibly.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
        if (self.serialBus is None ):
            paramDict["SerialBusDevice.deviceAddress"] = paramDict.get("SerialBusDevice.deviceAddress", SerialBusDevice.DEFAULT_ADDRESS)
            self.deviceAddress = paramDict["SerialBusDevice.deviceAddress"]
            if ("SerialBusDevice.bus" in paramDict):
                sb = paramDict["SerialBusDevice.bus"]
                if not( isinstance(sb, SerialBus)):
                    result = ErrorCode.errInvalidParameter
            else:
                sb = SerialBus()
                if (sb is None):
                    result = ErrorCode.errExhausted
                else:
                    result = sb.open(paramDict)
                if (result == ErrorCode.errOk):
                    paramDict["SerialBusDevice.bus"] = sb
            if (result == ErrorCode.errOk):
                result = sb.attach( self )
        else:
            result = ErrorCode.errResourceConflict
        return result

    def close(self):
        """Shut down this instance and release associated hardware resources.
        
        If this instance is attached to some bus, it gets detached, before
        the method returns.
        
        Also see: :meth:`.module.Module.close`.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
        if not (self.serialBus is None ):
            result = self.serialBus.detach(self)
        return result
    
    
    def isAttached(self):
        """Determines, if this instance is attached to some bus.

        Also see: :meth:`SerialBus.isAttached`.

        :return: An error code. :attr:`ErrorCode.errOk`, if the device\
        is already attached to some bus; :attr:`ErrorCode.errUnavailable`,\
        if it has not been attached before; Any other value to indicate\
        the failure or reason, why this information could not be retrieved.
        :rtype: ErrorCode
        """
        err = ErrorCode.errOk
        if (self.serialBus is None):
            err = ErrorCode.errUnavailable
        else:
            err = ErrorCode.errOk
        return err

    def readByteRegister( self, reg ):
        """This method provides 8 bit register read access to a device.
        
        The call is delegated to the corresponding method at the bus that
        this device is attached to.
        
        Also see: :meth:`SerialBus.readByteRegister`.
        
        :param int reg: The data to write to this device. This may be a\
        register identification or some sort of command.
        :return: A one-byte integer representing the response of the device\
        and an error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        return self.serialBus.readByteRegister( self, reg )

    def writeByteRegister( self, reg, data8 ):
        """Assuming a register-type access, this function writes a byte register.
        
        The call is delegated to the corresponding method at the bus that
        this device is attached to.
        The register value is written first, followed by the given data parameter.
        
        Also see: :meth:`SerialBus.writeByteRegister`.
        
        :param int reg: The register number. This addresses the place\
        where to put the content. Depending on the device, this could\
        also be some kind of command.
        :param int data8: The data to write to the addressed register.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        return self.serialBus.writeByteRegister( self, reg, data8)

    def readWordRegister( self, reg ):
        """Provide register read access for 16 bit data words.
        
        The call is delegated to the corresponding method at the bus that
        this device is attached to.
        After a byte is sent, two bytes are read from the device in
        little endian order.
        
        Also see: :meth:`SerialBus.readWordRegister`.
        
        :param int reg: The register identification or command to write to this device.
        :return: A 16-bit integer representing the response of the device\
        and an error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        return self.serialBus.readWordRegister( self, reg )

    def writeWordRegister( self, reg, data16 ):
        """Assuming a register-type access, this function writes a word register.
        
        The call is delegated to the corresponding method at the bus that
        this device is attached to.
        The register ``reg`` value is written first, followed by the given
        ``data16`` parameter in little-endian order.

        Also see: :meth:`SerialBus.writeWordRegister`.
        
        :param int reg: The register number. This addresses the place\
        where to put the content. Depending on the device, this could\
        also be some kind of command.
        :param int data16: The word to store to the given register.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        return self.serialBus.writeWordRegister( self, reg, data16 )

    def readDWordRegister( self, reg ):
        """Provide register read access for 32 bit data words.
        
        The call is delegated to the corresponding method at the bus that
        this device is attached to.
        After a byte is sent, four bytes are read from the device in
        little endian order.
        
        Also see: :meth:`SerialBus.readDWordRegister`.
        
        :param int reg: The register identification or command to write to this device.
        :return: A 32-bit integer representing the response of the device\
        and an error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        return self.serialBus.readDWordRegister( self, reg )

    def writeDWordRegister( self, reg, data32 ):
        """Assuming a register-type access, this function writes a dword register.
        
        The call is delegated to the corresponding method at the bus that
        this device is attached to.
        The register ``reg`` value is written first, followed by the given
        ``data32`` parameter in little-endian order.

        Also see: :meth:`SerialBus.writeDWordRegister`.
        
        :param int reg: The register number. This addresses the place\
        where to put the content. Depending on the device, this could\
        also be some kind of command.
        :param int data32: The double-word to store to the given register.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        return self.serialBus.writeDWordRegister( self, reg, data32 )
    
    def readBufferRegister( self, reg, length ):
        """Multi-byte read access to a register-type serial bus device.
        
        The call is delegated to the corresponding method at the bus that
        this device is attached to.
        
        After sending one byte of command or register address, a number
        of bytes is read back and returned.
        
        For SPI, the byte received during transmission of the ``reg``
        byte is discarded. It does not appear in the response buffer.
        Then, enough dummy traffic is generated to receive ``length``
        number of bytes.
        
        Also see: :meth:`SerialBus.readBufferRegister`.
        
        :param int reg: The byte to send. May be a command or register\
        address, depending on the protocol of the addressed device.
        :param int length: The number of bytes to read from the device.\
        Should be greater than zero.
        :return: A buffer of the indicated length holding the response\
        and an error code indicating success or the reason of failure.
        :rtype: int[], ErrorCode
        """
        return self.serialBus.readBufferRegister( self, reg, length )

    def writeBufferRegister( self, reg, buffer ):
        """Assuming a register-type access, this function writes a buffer to a register.
        
        The call is delegated to the corresponding method at the bus that
        this device is attached to.
        The register ``reg`` value is written first, followed by the given
        ``buffer`` content.

        Also see: :meth:`SerialBus.writeBufferRegister`.
        
        :param int reg: The register number. This addresses the place\
        where to put the content. Depending on the device, this could\
        also be some kind of command.
        :param int[] buffer: The data to store to the given register.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        return self.serialBus.writeBufferRegister( self, reg, buffer )

    def readBuffer( self, length ):
        """Directly reads multiple bytes from the given device.
        
        The call is delegated to the corresponding method at the bus that
        this device is attached to.
        
        Differently from :meth:`readBufferRegister`, this method does not
        write any register information beforehand, but just starts reading.
         
        Also see: :meth:`SerialBus.readBuffer`, :meth:`readBufferRegister`.
        
        :param int length: The number of bytes to read from the device.\
        Should be greater than zero.
        :return: A buffer of the indicated length holding the response\
        and an error code indicating success or the reason of failure.
        :rtype: int[], ErrorCode
        """
        return self.serialBus.readBuffer( self, length)

    def writeBuffer( self, buffer ):
        """Writes the given data to the device specified.
        
        The call is delegated to the corresponding method at the bus that
        this device is attached to.
        The buffer is not interpreted any further but is written as such,
        no matter of a register information being present, or not.
        In SPI mode, the data received during transmission, is discarded.

        Also see: :meth:`SerialBus.writeBuffer`, :meth:`writeBufferRegister`.
        
        :param int[] buffer: The data to store.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        return self.serialBus.writeBuffer( self, buffer )
    
    def readWriteBuffer( self, inLength, outBuffer ):
        """Writes and reads a number of bytes.
        
        The call is delegated to the corresponding method at the bus that
        this device is attached to.
         
        Also see: :meth:`SerialBus.readWriteBuffer`.
        
        :param int inLength: The number of bytes to read from the device.\
        Should be greater than zero.
        :param int[] outBuffer: The data to write to the device.
        :return: A buffer of the indicated length holding the response\
        and an error code indicating success or the reason of failure.
        :rtype: int[], ErrorCode
        """
        return self.serialBus.readWriteBuffer( self, inLength, outBuffer )

@unique
class SerialBusProvider(Enum):
    NONE      = auto()
    AUTO      = auto()
    SMBUS     = auto()
    SMBUS2    = auto()
    PERIPHERY = auto()
    SIM       = auto()

@unique
class SerialBusType(Enum):
    I2C = 10
    SPI = 20
    UART= 30
    
class _SerialBusIface( Module ):
    """Abstract interface to define a serial bus implementation.

    A sub class must overwrite at least the methods for reading and writing
    a single byte and buffer.
    """

    def __init__(self):
        self.busDesignator = ""
        self.provider = SerialBusProvider.NONE
        self.type = SerialBusType.I2C
        self._attachedDevices = list()
    
    @classmethod
    def Params_init( cls, paramDict ):
        # Fill paramDict with defaults
        if not ("SerialBus.busType" in paramDict):
            paramDict["SerialBus.busType"] = SerialBusType.I2C
        if not ("SerialBus.busDesignator" in paramDict):
            paramDict["SerialBus.busDesignator"] = "/dev/i2c-1"
        if not ("SerialBus.provider" in paramDict):
            paramDict["SerialBus.provider"] = SerialBusProvider.AUTO
        return None

    def open( self, paramDict ):
        ret = ErrorCode.errOk
        # Retrieve defaults
        defaults = {}
        self.Params_init( defaults )
        # Scan parameters
        if "SerialBus.provider" in paramDict:
            self.provider = paramDict["SerialBus.provider"]
        else:
            self.provider = SerialBusProvider.NONE
            ret = ErrorCode.errInvalidParameter

        if "SerialBus.busType" in paramDict:
            self.type = paramDict["SerialBus.busType"]
        else:
            self.type = defaults["SerialBus.busType"]
            paramDict["SerialBus.busType"] = self.type

        if "SerialBus.busDesignator" in paramDict:
            self.busDesignator = paramDict["SerialBus.busDesignator"]
        else:
            self.busDesignator = defaults["SerialBus.busDesignator"]
            paramDict["SerialBus.busDesignator"] = self.busDesignator
        return ret

    def close(self):
        """Shut down this implementation and release associated hardware resources.
        
        If this bus has some devices attached, they get detached, before
        the method returns.
        
        Also see: :meth:`.module.Module.close`.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        # Detach all devices.
        for device in self._attachedDevices:
            device.serialBus = None
        self._attachedDevices.clear()
        return ret
        
    def attach( self, device ):
        """Attaches a device to this implementation.
                
        :param: SerialBusDevice device: The device to be attached.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
        if not (device in self._attachedDevices):
            self._attachedDevices.append( device )
        return result
            
    def detach( self, device ):
        """Detach a device from this serial bus implementation.
        
        :param: SerialBusDevice device: The device to be detached.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
        self._attachedDevices.remove( device )
        return result

    def isAttached( self, device ):
        """ Determines, if the given device is already attached to this bus.
        
        Also see: :meth:`SerialBusDevice.isAttached`.
        
        :return: An error code. :attr:`ErrorCode.errOk`, if the device\
        is already attached to some bus; :attr:`ErrorCode.errUnavailable`,\
        if it has not been attached before; Any other value to indicate\
        the failure or reason, why this information could not be retrieved.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
        if (device in self._attachedDevices):
            result = ErrorCode.errOk
        else:
            result = ErrorCode.errUnavailable
        return result

    def isAnyAttached( self ):
        """ Determines, if there is any device attached to this bus implementation.
        
        :return: An error code. :attr:`ErrorCode.errOk`, if there is at\
        least one device attached to this bus;\
        :attr:`ErrorCode.errUnavailable`,\
        if no device has been attached before;\
        Any other value to indicate the failure or reason, why this\
        information could not be retrieved.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
        if ( self._attachedDevices ):
            result = ErrorCode.errOk
        else:
            result = ErrorCode.errUnavailable
        return result

    def readByteRegister( self, devAdr, reg ):
        """Read a single byte from a certain register.\
        A sub-class must overwrite this method.
        
        The method is expected to deliver a register's content to the
        caller.
        
        :param int devAdr: The device address uniquely identifying the\
        affected bus participant.
        :param int reg: The data to write to this device. This may be a\
        register identification or some sort of command.
        :return: A one-byte integer representing the response of the device\
        and an error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        pass

    def writeByteRegister( self, devAdr, reg, data ):
        """Write a single byte value into a certain register.\
        A sub-class must overwrite this method.
        
        The method is expected to store the given value to a register.
        
        :param int devAdr: The device address uniquely identifying the\
        affected bus participant.
        :param int reg: The address of the register to receive the new value.
        :param int data: The new value to store to that register.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        pass

    def readWordRegister( self, devAdr, reg ):
        """Read a word from a certain register.\
        A sub-class may overwrite this method.
        
        With this implementation, the word is formed from the content of
        the given register (low) and the content of the immediate
        successor ``reg+1`` of that register (high).
        
        :param int devAdr: The device address uniquely identifying the\
        affected bus participant.
        :param int reg: The address of the register to be read.
        :return: A 16-bit integer representing the response of the device\
        and an error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        lo, _ = self.readByteRegister(devAdr, reg)
        hi, err = self.readByteRegister(devAdr, reg+1)
        return ((hi << 8) | lo), err

    def writeWordRegister( self, devAdr, reg, data16 ):
        """Write a double-byte (word) value into a certain register.\
        A sub-class may overwrite this method.
        
        This implementation stores the given value to a pair of
        registers. The low-part of the ``data16`` item is stored at the
        given register, while the high-part is put at ``reg+1``.
        
        :param int devAdr: The device address uniquely identifying the\
        affected bus participant.
        :param int reg: The address of the register to receive\
        the (low-part of) the new value.
        :param int data16: The word to store to that register.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        bVal = data16 & 0xFF
        self.writeByteRegister(devAdr, reg, bVal)
        bVal = (data16 >> 8) & 0xFF
        err = self.writeByteRegister(devAdr, reg+1, bVal)
        return err

    def readDWordRegister( self, devAdr, reg ):
        """Read a 32 bit double word from a certain register.\
        A sub-class may overwrite this method.
        
        This implementation forms the dword from the content of the four
        consecutive registers starting with the given address ``reg``
        (low-byte of the low-word) and its successors
        ``reg+1`` (high-byte of the low-word),
        ``reg+2`` (low-byte of the high-word) and
        ``reg+3`` (high-byte of the high-word).
        
        :param int devAdr: The device address uniquely identifying the\
        affected bus participant.
        :param int reg: The address of the register to be read.
        :return: A 32-bit integer representing the response of the device\
        and an error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        L, _ = self.readWordRegister( devAdr, reg )
        H, err = self.readWordRegister( devAdr, reg+2 )
        ret = (H << 16) + L
        return ret, err

    def writeDWordRegister( self, devAdr, reg, data32 ):
        """Write a 32 bit double-word value into a certain register.\
        A sub-class may overwrite this method.
        
        This implementation stores the given value to a quadruple of
        registers. The low-byte of the low word is stored at the given
        register ``reg``. The high-byte of the low-word goes to ``reg+1``.
        The low-part of the high-word is stored to ``reg+2`` and the
        high-part of the high-word is put at ``reg+3``.
        
        :param int devAdr: The device address uniquely identifying the\
        affected bus participant.
        :param int reg: The register number. This addresses the place\
        where to put the content. Depending on the device, this could\
        also be some kind of command.
        :param int data32: The double-word to store to the given register.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        L = data32 & 0xFFFF
        H = (data32 & 0xFFFF0000) >> 16
        self.writeWordRegister( devAdr, reg, L )
        err = self.writeWordRegister( devAdr, reg+2, H )
        return err
    
    def readBufferRegister( self, devAdr, reg, length ):
        """Read a block of data starting from the given register.\
        A sub-class may overwrite this method.
        
        Starting with the given Register address, ``length`` bytes are
        read byte-wise.
        
        :param int devAdr: The device address uniquely identifying the\
        affected bus participant.
        :param int reg: The address of the first register to be read.
        :param int length: The number of bytes to read. Should be greater than zero.
        :return: A buffer of the indicated length holding the response\
        and an error code indicating success or the reason of failure.
        :rtype: int[], ErrorCode
        """
        data = [0] * length
        err = ErrorCode.errOk
        for idx in range(length):
            data[idx], err = self.readByteRegister(devAdr, reg+idx)
        return data, err

    def writeBufferRegister( self, devAdr, reg, data ):
        """Write a block of byte data to a register.\
        A sub-class may overwrite this method.
        
        This implementation stores the first byte - at index zero - at
        the given register ``reg``, the next byte - at index 1 - at
        ``reg+1`` and so on. More formally::
            
            data[0] -> reg
            data[1] -> reg + 1
            ...

        The number of bytes written is determined implicitly by the length
        of the ``data`` list. 
        
        :param int devAdr: The device address uniquely identifying the\
        affected bus participant.
        :param int reg: The address of the register to receive the block\
        of data.
        :param int[] data: List of bytes to be written. The length of the\
        list determines the number of bytes to write. So, all values in\
        the list will be transferred to the device.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        err = ErrorCode.errOk
        for idx in range( len(data) ):
            err = self.writeByteRegister(devAdr, reg+idx, data[idx])
        return err

    def readBuffer( self, devAdr, length ):
        """Directly reads multiple bytes from the given device.\
        A sub-class must overwrite this method.
        
        :param int devAdr: The device address uniquely identifying the\
        affected bus participant.
        :param int length: The number of bytes to read from the device.\
        Should be greater than zero.
        :return: A buffer of the indicated length holding the response\
        and an error code indicating success or the reason of failure.
        :rtype: int[], ErrorCode
        """
        pass

    def writeBuffer( self, devAdr, buffer ):
        """Writes the given data to the device specified.\
        A sub-class must overwrite this method.
        
        The buffer is not interpreted any further but is written as such,
        no matter of a register information being present, or not.
        
        :param int devAdr: The device address uniquely identifying the\
        affected bus participant.
        :param int[] buffer: The data to store.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        pass
    
    def readWriteBuffer( self, devAdr, inLength, outBuffer ):
        """Writes and reads a number of bytes.\
        A sub-class must overwrite this method.
        
        :param int devAdr: The device address uniquely identifying the\
        affected bus participant.
        :param int inLength: The number of bytes to read from the device.\
        Should be greater than zero.
        :param int[] outBuffer: The data to write to the device.
        :return: A buffer of the indicated length holding the response\
        and an error code indicating success or the reason of failure.
        :rtype: int[], ErrorCode
        """
        pass

    
# *** SMBus implementation ***
class _SerialBus_SMBus( _SerialBusIface ):
    """SMBUS serial bus implementation.
    """
        
    def open( self, paramDict ):
        # Scan the parameters
        ret = super().open(paramDict)
        if (ret == ErrorCode.errOk):
            try:
                if (self.provider == SerialBusProvider.SMBUS):
                    from smbus import SMBus
                    self.msg = None
                elif (self.provider == SerialBusProvider.SMBUS2):
                    from smbus2 import SMBus, i2c_msg
                    self.msg = i2c_msg
                self.bus = SMBus( self.busDesignator )
                ret = ErrorCode.errOk
            except Exception as exc:
                ret = ErrorCode.errInternal
                raise SystemError("Couldn't initialize serial bus ["+str(self.busDesignator)+"]. Designator right? Access to interface granted?") from exc
        return ret

    def close( self ):
        ret = ErrorCode.errOk
        if not self.bus is None:
            self.bus.close()
        return ret
    
    def readByteRegister( self, devAdr, reg ):
        err = ErrorCode.errOk
        data = self.bus.read_byte_data( devAdr, reg )
        return data, err

    def writeByteRegister( self, devAdr, reg, data ):
        err = ErrorCode.errOk
        self.bus.write_byte_data( devAdr, reg, data )
        return err

    def readWordRegister( self, devAdr, reg ):
        err = ErrorCode.errOk
        data = self.bus.read_word_data( devAdr, reg )
        return data, err

    def writeWordRegister( self, devAdr, reg, data16 ):
        err = ErrorCode.errOk
        self.bus.write_word_data( devAdr, reg, data16 )
        return err

    def readBufferRegister( self, devAdr, reg, length ):
        err = ErrorCode.errOk
        if (length <= 32 ):
            data = self.bus.read_i2c_block_data( devAdr, reg, length )
        else:
            msg1 = self.msg.write( devAdr, [reg] )
            msg2 = self.msg.read( devAdr, length )
            self.bus.i2c_rdwr( msg1, msg2 )
            data = list(msg2)
        return data, err

    def writeBufferRegister( self, devAdr, reg, data ):
        err = ErrorCode.errOk
        if (len(data) <= 32 ):
            self.bus.write_i2c_block_data( devAdr, reg, data )
        else:
            bdata = data
            bdata.insert( 0, reg )
            msg = self.msg.write( devAdr, bdata )
            self.bus.i2c_rdwr( msg )
        return err

    def readBuffer( self, devAdr, length ):
        pass

    def writeBuffer( self, devAdr, buffer ):
        pass
    
    def readWriteBuffer( self, devAdr, inLength, outBuffer ):
        pass

class _SerialBus_Periphery( _SerialBusIface ):
    """Periphery serial bus implementation.
    """
    
    def open( self, paramDict ):
        # Scan the parameters
        ret = super().open(paramDict)
        if (ret == ErrorCode.errOk):
            from periphery import I2C
            self.bus = I2C( self.busDesignator )
        return ret
    
    def close(self):
        ret = ErrorCode.errOk
        if not self.bus is None:
            self.bus.close()
        return ret
    
    def readByteRegister( self, devAdr, reg ):
        err = ErrorCode.errOk
        msgs = [self.bus.Message([reg]), self.bus.Message([0x00], read=True)]
        self.bus._transfer( devAdr, msgs)
        data = msgs[1].data[0]
        return data, err

    def writeByteRegister( self, devAdr, reg, data ):
        err = ErrorCode.errOk
        msgs = [self.bus.Message([reg, data])]
        self.bus._transfer( devAdr, msgs)
        return err

    def readWordRegister( self, devAdr, reg ):
        err = ErrorCode.errOk
        msgs = [self.bus.Message([reg]), self.bus.Message([0, 0], read=True)]
        self.bus._transfer( devAdr, msgs)
        data = (msgs[1].data[1] << 8) | msgs[1].data[0]
        return data, err

    def writeWordRegister( self, devAdr, reg, data16 ):
        err = ErrorCode.errOk
        msgs = [self.bus.Message([reg, (data16 & 0xFF), (data16 >> 8)])]
        self.bus._transfer( devAdr, msgs)
        return err

    def readDWordRegister( self, devAdr, reg ):
        err = ErrorCode.errOk
        msgs = [self.bus.Message([reg]), self.bus.Message([0, 0, 0, 0], read=True)]
        self.bus._transfer( devAdr, msgs)
        data = (msgs[1].data[3] << 24) | (msgs[1].data[2] << 16) | (msgs[1].data[1] << 8) | msgs[1].data[0]
        return data, err

    def writeDWordRegister( self, devAdr, reg, data32 ):
        err = ErrorCode.errOk
        msgs = [self.bus.Message([reg, (data32 & 0xFF), (data32 >> 8), (data32 >> 16), (data32 >> 24)])]
        self.bus._transfer( devAdr, msgs)
        return err
    
    def readBufferRegister( self, devAdr, reg, length ):
        err = ErrorCode.errOk
        ba = bytearray(length)
        msgs = [self.bus.Message([reg]), self.bus.Message(ba, read=True)]
        self.bus._transfer( devAdr, msgs)
        data = msgs[1].data
        return data, err

    def writeBufferRegister( self, devAdr, reg, data ):
        err = ErrorCode.errOk
        bdata = data
        bdata.insert( 0, reg )
        msgs = [self.bus.Message( bdata )]
        self.bus._transfer( devAdr, msgs)
        return err

    def readBuffer( self, devAdr, length ):
        err = ErrorCode.errOk
        ba = bytearray(length)
        msgs = [self.bus.Message(ba, read=True)]
        self.bus._transfer( devAdr, msgs)
        data = msgs[0].data
        return data, err

    def writeBuffer( self, devAdr, buffer ):
        err = ErrorCode.errOk
        msgs = [self.bus.Message( buffer )]
        self.bus._transfer( devAdr, msgs)
        return err
    
    def readWriteBuffer( self, devAdr, inLength, outBuffer ):
        err = ErrorCode.errOk
        ba = bytearray(inLength)
        msgs = [self.bus.Message(outBuffer), self.bus.Message(ba, read=True)]
        self.bus._transfer( devAdr, msgs)
        data = msgs[1].data
        return data, err

class _SerialBus_Sim( _SerialBusIface ):
    """Simulative serial bus implementation.
    """
    
    def _findSim( self, devAdr ):
        sim = None
        for dev in self._attachedDevices:
            if (dev.deviceAddress == devAdr):
                if (hasattr(dev, 'sim')):
                    sim = dev.sim
                else:
                    sim = self._defaultSim
                break
        return sim
    
    def open( self, paramDict ):
        # Scan the parameters
        ret = super().open(paramDict)
        self._defaultSim = SimDevNull()
        self._defaultSim.open(paramDict)
        return ret
    
    def close(self):
        err = ErrorCode.errOk
        self._defaultSim.close()
        return err
        
    def readByteRegister( self, devAdr, reg ):
        sim = self._findSim(devAdr)
        if (sim):
            data, err = sim.readByteRegister( reg )
        else:
            data = 0
            err = ErrorCode.errFailure
        return data, err

    def writeByteRegister( self, devAdr, reg, data ):
        sim = self._findSim(devAdr)
        if (sim):
            err = sim.writeByteRegister( reg, data )
        else:
            err = ErrorCode.errFailure
        return err

    def readWordRegister( self, devAdr, reg ):
        sim = self._findSim(devAdr)
        if (sim):
            data, err = sim.readWordRegister( reg )
        else:
            data = 0
            err = ErrorCode.errFailure
        return data, err

    def writeWordRegister( self, devAdr, reg, data16 ):
        sim = self._findSim(devAdr)
        if (sim):
            err = sim.writeWordRegister( reg, data16 )
        else:
            err = ErrorCode.errFailure
        return err

    def readDWordRegister( self, devAdr, reg ):
        sim = self._findSim(devAdr)
        if (sim):
            data, err = sim.readDWordRegister( reg )
        else:
            data = 0
            err = ErrorCode.errFailure
        return data, err

    def writeDWordRegister( self, devAdr, reg, data32 ):
        sim = self._findSim(devAdr)
        if (sim):
            err = sim.writeDWordRegister( reg, data32 )
        else:
            err = ErrorCode.errFailure
        return err
    
    def readBufferRegister( self, devAdr, reg, length ):
        sim = self._findSim(devAdr)
        if (sim):
            data, err = sim.readBufferRegister( reg, length )
        else:
            data = 0
            err = ErrorCode.errFailure
        return data, err

    def writeBufferRegister( self, devAdr, reg, data ):
        sim = self._findSim(devAdr)
        if (sim):
            err = sim.writeBufferRegister( reg, data )
        else:
            err = ErrorCode.errFailure
        return err

    def readBuffer( self, devAdr, length ):
        pass

    def writeBuffer( self, devAdr, buffer ):
        pass
    
    def readWriteBuffer( self, devAdr, inLength, outBuffer ):
        pass

class SerialBus( _SerialBusIface ):
    """Convergence layer to abstract from multiple implementations of\
    serial communication (I2C, SPI), such as smbus or periphery.
    
    This class represents the serial bus as such, without any participating
    device. For communicating with a specific device, a corresponding
    instance of ``SerialBusDevice`` must be provided to the read/write
    method of interest.
    
    The implementation currently supports the following serial communication
    packages in the given order of priority:
    
    * smbus2
    * smbus
    * periphery
    * simulated devices
    
    """
    
    _STATUS_FREE		= 1
    _STATUS_OPEN		= 2
    
    #
    # Internal helpers
    #
    
    def __init__(self):
        self._status = SerialBus._STATUS_FREE
        self._impl = None
        
    def _detectProvider( self, busType ):
        ret = SerialBusProvider.NONE
        if busType == SerialBusType.I2C:
            try:
                from smbus2 import SMBus, i2c_msg
                ret = SerialBusProvider.SMBUS2
            except ModuleNotFoundError:
                try:
                    from smbus import SMBus, i2c_msg
                    ret = SerialBusProvider.SMBUS
                except ModuleNotFoundError:
                    try:
                        from periphery import I2C
                        ret = SerialBusProvider.PERIPHERY
                    except ModuleNotFoundError:
                        ret = SerialBusProvider.SIM
        else:
            raise NotImplementedError('Currently, only I2C is supported!')
        return ret

    #
    # Module API
    #
    

    @classmethod
    def Params_init( cls, paramDict ):
        """Initialize parameters with default values.
        Supported key names and their meanings are:
        
        * ``SerialBus.busType``: A :class:`SerialBusType` to indicate the\
        serial protocol. The default is :attr:`SerialBusType.I2C`.
        * ``SerialBus.busDesignator``: A string or number to identify\
        the bus port, such as "/dev/i2c-3" or 1. Defaults to "/dev/i2c-1".
        * ``SerialBus.provider``: A :class:`SerialBusProvider` indicating the\
        implementation to use. Defaults to :attr:`SerialBusProvider.AUTO`.

        :param dict(str, object) paramDict: Configuration parameters as obtained from :meth:`Params_init`, possibly.
        :return: none
        :rtype: None
        """
        _SerialBusIface.Params_init(paramDict)
        return None

    def open(self, paramDict):
        """Open a new serial bus and apply the given configuration.
        
        If this instance was opened before, already, this method returns
        an error code. The same is true, when the same physical bus was
        opened before, possible using another instance.
        
        Also see: :meth:`Params_init`, :meth:`.module.Module.open`.
        
        :param dict(str, object) paramDict: Configuration parameters as\
        obtained from :meth:`Params_init`, possibly.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if (self._status == SerialBus._STATUS_OPEN):
            ret = ErrorCode.errResourceConflict
        else:
            # Retrieve defaults
            defaults = {}
            self.Params_init( defaults )
            # Scan parameters
            if "SerialBus.provider" in paramDict:
                provider = paramDict["SerialBus.provider"]
            else:
                provider = defaults["SerialBus.provider"]
            if (provider == SerialBusProvider.AUTO):
                if "SerialBus.busType" in paramDict:
                    busType = paramDict["SerialBus.busType"]
                else:
                    busType = defaults["SerialBus.busType"]
                provider = self._detectProvider( busType )
                paramDict["SerialBus.provider"] = provider
            
    
            # Multiplex the different implementations depending on the provider module
            if (provider==SerialBusProvider.SMBUS) or (provider==SerialBusProvider.SMBUS2):
                self._impl = _SerialBus_SMBus()
            elif (provider==SerialBusProvider.PERIPHERY):
                self._impl = _SerialBus_Periphery()
            elif (provider==SerialBusProvider.SIM):
                self._impl = _SerialBus_Sim()
            else:
                raise NotImplementedError('Driver module ' + str(provider) + ' is not supported.')
            
            # Allocate resources
            ret = self._impl.open( paramDict )
            if (ret == ErrorCode.errOk):
                self._status = SerialBus._STATUS_OPEN
        return ret

    def close(self):
        """Shut down this bus and release associated hardware resources.
        
        If this bus has some devices attached, they get detached, before
        the method returns.
        
        Also see: :meth:`.module.Module.close`.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        # Actually close the bus
        if (self._status != SerialBus._STATUS_FREE):
            if not self._impl is None:
                # Detach all devices.
                ret = self._impl.close()
                self._impl = None
            self._status = SerialBus._STATUS_FREE
        return ret

    def setRunLevel(self, level):
        """Switch the bus into some operating or power-saving mode.
        
        Also see: :meth:`.module.Module.setRunLevel`.
        
        :param RunLevel level: The level to switch to.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        err = self._impl.setRunLevel(level)
        return err

    def isOpen( self ):
        """Determine, if the given bus is already open.
        
        :return: :attr:`ErrorCode.errOk`, if the bus is already open;\
        :attr:`ErrorCode.errUnavailable, if it has not been opened before;\
        Any other value to indicate the failure or reason, why this\
        information could not be retrieved.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
        if (self._status == SerialBus._STATUS_OPEN):
            result = ErrorCode.errOk
        else:
            result = ErrorCode.errUnavailable
        return result

    def attach( self, device ):
        """Attaches a device to this serial bus.
        
        If this bus is not open, yet, then it will get opened, now. If
        the same device has been attached before, the method will just
        return successfully.
        
        :param: SerialBusDevice device: The device to be attached.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
        if (device.serialBus == self):
            result = ErrorCode.errOk
        elif (device.serialBus != None):
            result = ErrorCode.errResourceConflict
        else:
            # Check if bus is open, already
            result = self.isOpen()
            if (result == ErrorCode.errUnavailable):
                params = {}
                self.Params_init(params)
                result = self.open(params)
            # Attach it to the implementation
            if (result == ErrorCode.errOk):
                result = self._impl.attach( device )
            if (result == ErrorCode.errOk):
                # Mark the device as being attached
                device.serialBus = self
        return result
            
    def detach( self, device ):
        """Detach a device from this serial bus.
        
        If this is the last device on the bus, the bus is closed,
        automatically.
        
        :param: SerialBusDevice device: The device to be detached.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
        if (device.serialBus == self):
            device.serialBus = None
            result = self._impl.detach( device )
            if ( self._impl.isAnyAttached() == ErrorCode.errUnavailable ):
                result = self.close()
        else:
            result = ErrorCode.errResourceConflict
        return result

    def isAttached( self, device ):
        """ Determines, if the given device is already attached to this bus.
        
        Also see: :meth:`SerialBusDevice.isAttached`.
        
        :return: An error code. :attr:`ErrorCode.errOk`, if the device\
        is already attached to some bus; :attr:`ErrorCode.errUnavailable`,\
        if it has not been attached before; Any other value to indicate\
        the failure or reason, why this information could not be retrieved.
        :rtype: ErrorCode
        """
        return self._impl.isAttached(device)
            
    def readByteRegister( self, device, reg ):
        """This method provides 8 bit register read access to a device.
        
        First, the ``reg`` byte is sent to the device. This may address
        the register to be read out or be some sort of command.
        Then, one byte is read back from the device. Depending on the
        device protocol semantics, this may be the register content or
        the command response.
        
        Also see: :meth:`SerialBusDevice.readByteRegister`.
        
        :param SerialBusDevice device: The device to communicate with.
        :param int reg: The data to write to this device. This may be a\
        register identification or some sort of command.
        :return: A one-byte integer representing the response of the device\
        and an error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        return self._impl.readByteRegister( device.deviceAddress, reg )

    def writeByteRegister( self, device, reg, data8 ):
        """Assuming a register-type access, this function writes a byte register.
        
        The register value is written first, followed by the given data
        parameter.
        
        Also see: :meth:`SerialBusDevice.writeByteRegister`.
        
        :param SerialBusDevice device: The device to communicate with.
        :param int reg: The register number. This addresses the place\
        where to put the content. Depending on the device, this could\
        also be some kind of command.
        :param int data8: The data to write to the addressed register.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        return self._impl.writeByteRegister(device.deviceAddress, reg, data8)

    def readWordRegister( self, device, reg ):
        """Provide register read access for 16 bit data words.
        
        After a byte is sent, two bytes are read from the device.
        The word is always read in little endian order, i.e. the least
        significant low-byte first, the highes-significant high-byte second.
        
        Also see: :meth:`SerialBusDevice.readByteRegister`.
        
        :param SerialBusDevice device: The device to communicate with.
        :param int reg: The register identification or command to write\
        to this device.
        :return: A 16-bit integer representing the response of the device\
        and an error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        return self._impl.readWordRegister( device.deviceAddress, reg )

    def writeWordRegister( self, device, reg, data16 ):
        """Assuming a register-type access, this function writes a word register.
        
        The register ``reg`` value is written first, followed by the given
        ``data16`` parameter in little-endian order.

        Also see: :meth:`SerialBusDevice.writeWordRegister`.
        
        :param SerialBusDevice device: The device to communicate with.
        :param int reg: The register number. This addresses the place\
        where to put the content. Depending on the device, this could\
        also be some kind of command.
        :param int data16: The word to store to the given register.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        return self._impl.writeWordRegister( device.deviceAddress, reg, data16 )

    def readDWordRegister( self, device, reg ):
        """Read a 32-bit word from the given register.
        
        After the ``reg`` byte is sent, four bytes are read from the device.
        The 32 bit double-word is always read in little endian order,
        i.e. the least significant low-byte first, the highes-significant
        high-byte last.
        
        Also see: :meth:`SerialBusDevice.readDWordRegister`.
        
        :param SerialBusDevice device: The device to communicate with.
        :param int reg: The register identification or command to write\
        to this device.
        :return: A 32-bit integer representing the response of the device\
        and an error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        return self._impl.readDWordRegister( device.deviceAddress, reg )

    def writeDWordRegister( self, device, reg, data32 ):
        """Write a 32 bit double-word to the given register.
        
        The register ``reg`` value is written first, followed by the given
        ``data32`` parameter in little-endian order.

        Also see: :meth:`SerialBusDevice.writeDWordRegister`.
        
        :param SerialBusDevice device: The device to communicate with.
        :param int reg: The register number. This addresses the place\
        where to put the content. Depending on the device, this could\
        also be some kind of command.
        :param int data32: The dword to store to the given register.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        return self._impl.writeDWordRegister( device.deviceAddress, reg, data32 )
    
    def readBufferRegister( self, device, reg, length ):
        """Multi-byte read access to a register-type serial bus device.
        
        After sending one byte of command or register address, a number
        of bytes is read back and returned.
        
        For SPI, the byte received during transmission of the ``reg``
        byte is discarded. It does not appear in the response buffer.
        Then, enough dummy traffic is generated to receive ``length``
        number of bytes.
        
        Also see: :meth:`SerialBusDevice.readBufferRegister`.
        
        :param SerialBusDevice device: The device to communicate with.
        :param int reg: The byte to send. May be a command or register\
        address, depending on the protocol of the addressed device.
        :param int length: The number of bytes to read from the device.\
        Should be greater than zero.
        :return: A buffer of the indicated length holding the response\
        and an error code indicating success or the reason of failure.
        :rtype: int[], ErrorCode
        """
        return self._impl.readBufferRegister( device.deviceAddress, reg, length )

    def writeBufferRegister( self, device, reg, buffer ):
        """Assuming a register-type access, this function writes a buffer\
        to a register.
        
        The register ``reg`` value is written first, followed by the given
        ``buffer`` content.

        Also see: :meth:`SerialBusDevice.writeBufferRegister`.
        
        :param SerialBusDevice device: The device to communicate with.
        :param int reg: The register number. This addresses the place\
        where to put the content. Depending on the device, this could\
        also be some kind of command.
        :param int buffer: The data to store to the given register.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        return self._impl.writeBufferRegister( device.deviceAddress, reg, buffer )

    def readBuffer( self, device, length ):
        """Directly reads multiple bytes from the given device.

        Also see: :meth:`SerialBusDevice.readBuffer`.
        
        :param SerialBusDevice device: The device to communicate with.
        :param int length: The number of bytes to read from the device.\
        Should be greater than zero.
        :return: A buffer of the indicated length holding the response\
        and an error code indicating success or the reason of failure.
        :rtype: int[], ErrorCode
        """
        return self._impl.readBuffer( device.deviceAddress, length )

    def writeBuffer( self, device, buffer ):
        """Writes the given data to the device specified.
        
        The buffer is not interpreted any further but is written as such,
        no matter of a register information being present, or not.

        Also see: :meth:`SerialBusDevice.writeBuffer`.
        
        :param SerialBusDevice device: The device to communicate with.
        :param int[] buffer: The data to store.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        return self._impl.writeBuffer( device.deviceAddress, buffer )
    
    def readWriteBuffer( self, device, inLength, outBuffer ):
        """Writes and reads a number of bytes.
        
        Also see: :meth:`SerialBusDevice.readWriteBuffer`.
        
        :param SerialBusDevice device: The device to communicate with.
        :param int inLength: The number of bytes to read from the device.\
        Should be greater than zero.
        :param int[] outBuffer: The data to write to the device.
        :return: A buffer of the indicated length holding the response\
        and an error code indicating success or the reason of failure.
        :rtype: int[], ErrorCode
        """
        return self._impl.readWriteBuffer( device.deviceAddress, inLength, outBuffer )

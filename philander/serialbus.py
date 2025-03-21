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
__all__ = ["SerialBus", "SerialBusDevice", "SerialBusType"]

from philander.penum import Enum, unique, auto, idiotypic

from philander.module import Module
from philander.sysfactory import SysProvider, SysFactory
from philander.systypes import ErrorCode


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
        self.provider = SysProvider.NONE
        self.serialBus   = None
        self.address = SerialBusDevice.DEFAULT_ADDRESS

    @classmethod
    def Params_init( cls, paramDict ):
        """Initialize the set of configuration parameters with supported options.
        Supported configuration key names and their meanings are:
        
        * ``SerialBusDevice.address``: The address of the device if on I2C-type bus.\
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
        # Add bus-related defaults
        bus = paramDict.get("SerialBusDevice.bus", None)
        if bus:
            bus.Params_init(paramDict)
        else:
            SerialBus.Params_init(paramDict)
        # Add device-related defaults; may depend on bus type.
        btype = paramDict.get("SerialBus.type", None)
        defaults = {}
        if btype == SerialBusType.I2C:
            defaults = {
                "SerialBusDevice.address": SerialBusDevice.DEFAULT_ADDRESS,
            }
        for key, value in defaults.items():
            if not key in paramDict:
                paramDict[key] = value
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
            adr = paramDict.get("SerialBusDevice.address", SerialBusDevice.DEFAULT_ADDRESS)
            if not isinstance(adr, int):
                try:
                    adr = int( adr, 0 )
                except ValueError:
                    adr = SerialBusDevice.DEFAULT_ADDRESS
                    
            paramDict["SerialBusDevice.address"] = adr
            self.address = adr
            if ("SerialBusDevice.bus" in paramDict):
                sb = paramDict["SerialBusDevice.bus"]
                if not( isinstance(sb, SerialBus)):
                    result = ErrorCode.errInvalidParameter
                elif not( sb.isOpen().isOk() ):
                    result = sb.open(paramDict)
            else:
                sb = SysFactory.getSerialBus()
                if (sb is None):
                    result = ErrorCode.errExhausted
                else:
                    result = sb.open(paramDict)
                if (result.isOk()):
                    paramDict["SerialBusDevice.bus"] = sb
            if (result.isOk()):
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
@idiotypic
class SerialBusType(Enum):
    I2C = 10
    SPI = 20
    UART= 30

@unique
@idiotypic
class SPIMode(Enum):
    """SPI mode specification.
    
    The basic SPI specification leaves some degree of freedom with respect
    to the clock idle state, often referred to as clock polarity (CPOL).
    It may be chosen either low or high.
    Also the phase (edge), at which to read data can either be first or
    second. This is referred to as the clock phase (CPHA).
    Varying CPOL and CPHA offers in total 4 modes that SPI can be operated
    in. For more information on SPI modes refer to:
    https://en.wikipedia.org/wiki/Serial_Peripheral_Interface#Clock_polarity_and_phase 
    """
    CPOL0_CPHA0 = 0         # idle low, read on first edge (rising)
    CPOL0_CPHA1 = 1         # idle low, read on second edge (falling)
    CPOL1_CPHA0 = 2         # idle high, read on first edge (falling)
    CPOL1_CPHA1 = 3         # idle high, read on second edge (rising)

class SerialBus( Module ):
    """Convergence layer to abstract from multiple implementations of\
    serial communication (I2C, SPI), such as smbus or periphery.
    
    This class represents the serial bus as such, without any participating
    device. For communicating with a specific device, a corresponding
    instance of ``SerialBusDevice`` must be provided to the read/write
    method of interest.

    A sub class must overwrite at least the methods for reading and writing
    a single byte and buffer.
    """
    
    _STATUS_FREE		= 1
    _STATUS_OPEN		= 2
    
    DEFAULT_TYPE        = SerialBusType.I2C
    DEFAULT_DESGINATOR  = "/dev/i2c-1"
    DEFAULT_SPI_MODE    = SPIMode.CPOL1_CPHA1
    DEFAULT_SPI_SPEED   = 1000000
    DEFAULT_SPI_BIT_ORDER= "MSB"
    DEFAULT_SPI_BITS_PER_WORD = 8
    
    #
    # Internal helpers
    #
    
    def __init__(self):
        self.designator = ""
        self.provider = SysProvider.NONE
        self.type = SerialBusType.I2C
        self._attachedDevices = list()
        self._status = SerialBus._STATUS_FREE
        

    #
    # Module API
    #
    

    @classmethod
    def Params_init( cls, paramDict ):
        """Initialize parameters with default values.
        
        Supported key names and their meanings are:

        ==================    =================================================    ================================
        Key                   Range                                                Default
        ==================    =================================================    ================================
        SerialBus.type        :class:`SerialBusType` to indicate the protocol.     :attr:`SerialBus.DEFAULT_TYPE`.
        SerialBus.designator  [string | number]: bus port, "/dev/i2c-3" or 1.      "/dev/i2c-1".
        ==================    =================================================    ================================
        
        :param dict(str, object) paramDict: Configuration parameters as obtained from :meth:`Params_init`, possibly.
        :return: none
        :rtype: None
        """
        defaults = {
            "SerialBus.type":       SerialBus.DEFAULT_TYPE,
            "SerialBus.designator": SerialBus.DEFAULT_DESGINATOR,
        }
        for key, value in defaults.items():
            if not key in paramDict:
                paramDict[key] = value
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
            if "SerialBus.type" in paramDict:
                self.type = paramDict["SerialBus.type"]
            else:
                self.type = defaults["SerialBus.type"]
                paramDict["SerialBus.type"] = self.type
    
            if "SerialBus.designator" in paramDict:
                self.designator = paramDict["SerialBus.designator"]
            else:
                self.designator = defaults["SerialBus.designator"]
                paramDict["SerialBus.designator"] = self.designator
            
        if( ret.isOk() ):
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
        ret = ErrorCode.errOk
        # Actually close the bus
        if (self._status != SerialBus._STATUS_FREE):
            # Detach all devices.
            self.detachAll()
            self._status = SerialBus._STATUS_FREE
        return ret

    def setRunLevel(self, level):
        """Switch the bus into some operating or power-saving mode.
        
        Also see: :meth:`.module.Module.setRunLevel`.
        
        :param RunLevel level: The level to switch to.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del level
        err = ErrorCode.errOk
        if (self._status != SerialBus._STATUS_OPEN):
            err = ErrorCode.errResourceConflict
        return err

    #
    # SerialBus API
    #

    def isOpen( self ):
        """Determine, if the given bus is already open.
        
        :return: :attr:`ErrorCode.errOk`, if the bus is already open;\
        :attr:`ErrorCode.errUnavailable`, if it has not been opened before;\
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
            if (result.isOk()):
                if not (device in self._attachedDevices):
                    self._attachedDevices.append( device )
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
            if (device in self._attachedDevices):
                self._attachedDevices.remove( device )
            if (self._status == SerialBus._STATUS_OPEN) and \
               (self.isAnyAttached() == ErrorCode.errUnavailable ):
                result = self.close()
        else:
            result = ErrorCode.errResourceConflict
        return result

    def detachAll(self):
        """Detaches all devices from this serial bus.
        
        Note that this will *not* close the bus automatically.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
        for device in self._attachedDevices:
            device.serialBus = None
        self._attachedDevices.clear()
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
        ret = ErrorCode.errOk
        if (self._status == SerialBus._STATUS_OPEN):
            if (device in self._attachedDevices):
                ret = ErrorCode.errOk
            else:
                ret = ErrorCode.errUnavailable
        else:
            ret = ErrorCode.errResourceConflict
        return ret

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
        if (self._status == SerialBus._STATUS_OPEN):
            if ( self._attachedDevices ):
                result = ErrorCode.errOk
            else:
                result = ErrorCode.errUnavailable
        else:
            result = ErrorCode.errResourceConflict
        return result

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
        # A sub-class implementation must overwrite this method.
        del device, reg
        return 0, ErrorCode.errNotImplemented

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
        # A sub-class implementation must overwrite this method.
        del device, reg, data8
        return ErrorCode.errNotImplemented

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
        lo, _ = self.readByteRegister(device, reg)
        hi, err = self.readByteRegister(device, reg+1)
        return ((hi << 8) | lo), err

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
        bVal = data16 & 0xFF
        self.writeByteRegister(device, reg, bVal)
        bVal = (data16 >> 8) & 0xFF
        err = self.writeByteRegister(device, reg+1, bVal)
        return err

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
        L, _ = self.readWordRegister( device, reg )
        H, err = self.readWordRegister( device, reg+2 )
        ret = (H << 16) + L
        return ret, err

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
        L = data32 & 0xFFFF
        H = (data32 & 0xFFFF0000) >> 16
        self.writeWordRegister( device, reg, L )
        err = self.writeWordRegister( device, reg+2, H )
        return err
    
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
        data = [0] * length
        err = ErrorCode.errOk
        for idx in range(length):
            data[idx], err = self.readByteRegister(device, reg+idx)
        return data, err

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
        err = ErrorCode.errOk
        for idx in range( len(buffer) ):
            err = self.writeByteRegister(device, reg+idx, buffer[idx])
        return err

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
        # A sub-class implementation must overwrite this method.
        del device, length
        return [], ErrorCode.errNotImplemented

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
        # A sub-class implementation must overwrite this method.
        del device, buffer
        return ErrorCode.errNotImplemented
    
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
        # A sub-class implementation must overwrite this method.
        del device, inLength, outBuffer
        return [], ErrorCode.errNotImplemented

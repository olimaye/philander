"""Serial bus simulation module to support debugging and cross-platform development.

This module provides a fake serial bus implementation to virtualize serial
communication. 
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["SimBus", "SimBusNull", "SimBusMemory", "MemoryType", "Register"]

import module
import enum
import dataclasses
import systypes

class SimBus( module.Module ):
    """Abstract base class to define the functionality of a simulated serial bus.
    
    A sub class must overwrite at least the methods for reading and writing
    a single byte. Implementation should use as least as possible dependencies
    to other modules. Use of hardware-dependent drivers must be completely
    avoided!
    """
    
    def readByteRegister( self, aReg ):
        """Read a single byte from a certain register.\
        A sub-class must overwrite this method.
        
        The method is expected to deliver a register's content to the
        caller.
        
        :param int aReg: The address of the register to be read.
        :returns: The value stored by the given register.
        :rtype: int
        """
        pass

    def writeByteRegister( self, aReg, data ):
        """Write a single byte value into a certain register.\
        A sub-class must overwrite this method.
        
        The method is expected to store the given value to a register.
        
        :param int aReg: The address of the register to receive the new value.
        :param int data: The new value to store to that register.
        :returns: None
        :rtype: none
        """
        pass

    def readWordRegister( self, aReg ):
        """Read a word from a certain register.
        
        The word is formed from the content of the given register (low)
        and the content of the immediate successor ``aReg+1`` of that
        register (high).
        
        :param int aReg: The address of the low-byte register to be read.
        :returns: The value stored by the given register.
        :rtype: int
        """
        lo = self.readByteRegister(aReg)
        hi = self.readByteRegister(aReg+1)
        return ((hi << 8) | lo)

    def writeWordRegister( self, aReg, data16 ):
        """Write a double-byte (word) value into a certain register.
        
        The method is expected to store the given value to a pair of
        registers. The low-part of the data16 item is stored at the given
        register, while the high-part is put at ``aReg+1``.
        
        :param int aReg: The address of the (low-) register to receive\
        the low-part of the new value.
        :param int data16: The new value to store to that pair of registers.
        :returns: None
        :rtype: none
        """
        bVal = data16 & 0xFF
        self.writeByteRegister(aReg, bVal)
        bVal = (data16 >> 8) & 0xFF
        self.writeByteRegister(aReg+1, bVal)
        return None

    def readDWordRegister( self, aReg ):
        """Read a double word from a certain register.
        
        The dword is formed from the content of the four registers,
        starting with the given address ``aReg`` (low-byte of the low-word)
        and its successors ``aReg+1`` (high-byte of the low-word),
        ``aReg+2`` (low-byte of the high-word) and
        ``aReg+3`` (high-byte of the high-word).
        
        :param int aReg: The address of the first (lowest-byte) register to be read.
        :returns: The value stored by the given register.
        :rtype: int
        """
        L = self.readWordRegister( aReg )
        H = self.readWordRegister( aReg+2 )
        ret = (H << 16) + L
        return ret

    def writeDWordRegister( self, aReg, data32 ):
        """Write a double-word (four bytes) value into a certain register.
        
        The method is expected to store the given value to a quadruple of
        registers. The low-byte of the low word is stored at the given
        register ``aReg``. The high-byte of the low-word goes to ``aReg+1``.
        The low-part of the high-word is stored to ``aReg+2`` and the
        high-part of the high-word is put at ``aReg+3``.
        
        :param int aReg: The address of the first (lowest byte) register\
        to receive part of the new value.
        :param int data32: The new value to store to that quadruple of registers.
        :returns: None
        :rtype: none
        """
        L = data32 & 0xFFFF
        H = (data32 & 0xFFFF0000) >> 16
        self.writeWordRegister( aReg, L )
        self.writeWordRegister( aReg+2, H )
        return None
    
    def readBufferRegister( self, aReg, length ):
        """Read a block of data starting from the given register.
        
        Starting with the given Register address, ``length`` bytes are
        read and returned.
        
        :param int aReg: The address of the first register to be read.
        :param int length: The number of bytes to read.
        :returns: A list of ``length`` byte values as read from the registers.
        :rtype: list of integers
        """
        data = [0] * length
        for idx in range(length):
            data[idx] = self.readByteRegister(aReg+idx)
        return data

    def writeBufferRegister( self, aReg, data ):
        """Write a block of byte data into registers.
        
        The first byte - at index zero - is stored at the given register
        ``aReg``, the next byte - at index 1 - is stored at ``aReg+1``
        and so on. More formally::
            
            data[0] -> aReg
            data[1] -> aReg + 1
            ...

        The number of bytes written is determined implicitly by the length
        of the ``data`` list. 
        
        :param int aReg: The address of the first register to receive\
        the block of data.
        :param list data: List of bytes to be written. The length of the\
        list determines the number of bytes to werite. So, all values in\
        the list will be transferred to the device.
        :returns: None
        :rtype: none
        """
        for idx in range( len(data) ):
            self.writeByteRegister(aReg+idx, data[idx])
        return None


class SimBusNull( SimBus ):
    """Slim line serial bus simulation. Reading retrieves always the same\
    constant value, while writing is simply ignored. 
    """
    
    DEFAULT_READING = 0x3A
    
    @classmethod
    def Params_init(cls, paramDict):
        """Initialize configuration parameters.
        
        Any supported option missed in the dictionary handed in, will be
        added upon return. Also see :meth:`.module.Module.Params_init`.
        The following options are supported.
        
        ==================    =======    ==========================
        Key                   Range      Default
        ==================    =======    ==========================
        SimBusNull.reading    integer    SimBusNull.DEFAULT_READING
        ==================    =======    ==========================
        
        :param dict(str, object) paramDict: Dictionary mapping option names to their respective values.
        :returns: none
        :rtype: None
        """
        paramDict["SimBusNull.reading"] = paramDict.get("SimBusNull.reading", SimBusNull.DEFAULT_READING)
        return None
    
    def open( self, paramDict ):
        """Open the instance and prepare it for use.
        
        Also see :meth:`.module.Module.open`.
        
        :param dict(str, object) paramDict: Configuration parameters as\
        obtained from :meth:`Params_init`, possibly.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        paramDict["SimBusNull.reading"] = paramDict.get("SimBusNull.reading", SimBusNull.DEFAULT_READING)
        self._reading = paramDict["SimBusNull.reading"]
        return systypes.ErrorCode.errOk
            
    def readByteRegister( self, aReg ):
        """Read a single byte.
        
        Independent of the given register, the delivered value will
        always be the same. That delivered reading can be configured
        using the SimBusNull.reading option when calling :meth:`open`.

        :param int aReg: The address of the register to be read.\
        Actually ignored.
        :returns: The value stored by the given register.
        :rtype: int
        """
        del aReg
        return self._reading

    def writeByteRegister( self, aReg, data ):
        """ Write a single byte.

        Actually, does nothing. Also see :meth:`SimBus.writeByteRegister`.
        
        :param int aReg: The address of the register. Ignored.
        :param int data: The new value to store to that register. Ignored.
        :returns: None
        :rtype: none
        """
        pass
    


@enum.unique
class MemoryType(enum.Enum):
    """Enumeration to reflect the different types of memory.
    """
    ROM   = enum.auto()
    RAM   = enum.auto()
    NVM   = enum.auto()
    VOLATILE  = enum.auto()
    
@dataclasses.dataclass
class Register:
    """Simulate a memory-based register. Depending on the type of memory,\
    the register content can or cannot be changed by simply writing to it.\
    Volatile registers may change their content spontaneously or by\
    mechanisms that cannot be controlled by the user. 
    """
    address:    int
    """The address to identify this register during read/write operations."""
    content:    int
    """The register content. Can be initialized, independently of the\
    memory type of that register."""
    type:       MemoryType
    """The type of memory for that register."""

    def __init__(self, adr, cont=0, typ=MemoryType.RAM):
        self.address = adr
        self.content = cont
        self.type = typ


    
class SimBusMemory( SimBus ):
    """Serial bus implementation to simulate a device that can be accessed\
    through a set of memory-based registers. The list of registers\
    must be provided during instantiation.
    """
    
    def __init__(self, regs):
        self._regs = regs
        
    def _findReg(self, regAdr):
        reg = next( (r for r in self._regs if r.address==regAdr), None)
        return reg
    
    def open( self, paramDict ):
        del paramDict
        return systypes.ErrorCode.errOk
            
    def readByteRegister( self, aReg ):
        """Retrieves a register's content. To also simulate side effects\
        of reading, the following steps are executed in sequence, no
        matter what the memory type of the given register is:
        
        #. calling :meth:`._onPreRead`
        #. reading the register content
        #. calling :meth:`._onPostRead`
        
        Note that the return value is solely determined by what is read
        from the register in step #2. It cannot be altered by :meth:`._onPostRead`,
        anymore.

        Also see :meth:`.simbus.SimBus.readByteRegister`.
        
        :param int aReg: The address of the register to be read.
        :returns: The value stored by the given register.
        :rtype: int
        """
        reg = self._findReg( aReg )
        if (reg is None):
            result = 0
        else:
            self._onPreRead( reg )
            result = reg.content
            self._onPostRead( reg )
        return result

    def writeByteRegister( self, aReg, data ):
        """Write a single byte value into a certain register.\
        Write attempts to registers with non-writable memory are ignored.\
        For registers with writable memory, the following sequence is\
        executed in order to give sub-classes the opportunity to simulate\
        side effects:
        
        #. calling :meth:`._onPreWrite`, may alter the intended data and\
        returns the actual new content.
        #. writing the new register content
        #. calling :meth:`._onPostWrite`
        
        :param int aReg: The address of the register to receive the new value.
        :param int data: The new value to store to that register.
        :returns: None
        :rtype: none
        """
        reg = self._findReg( aReg )
        if not (reg is None):
            if (reg.type == MemoryType.RAM):
                newContent = self._onPreWrite(reg, data)
                reg.content = newContent
                self._onPostWrite(reg)
        return None

    def _onPreRead(self, reg):
        """Interface function that will be called right before a register\
        is read. Can be used by sub-classes to simulate the exact\
        hardware behavior while reading a register. Modifying the
        register content here, would highly affect the return value
        of the surrounding :meth:`.readByteRegister` function.
        
        The current implementation is simply empty.

        :param Register reg: The register instance to be read.
        :returns: None
        :rtype: none
        """
        pass
    
    def _onPostRead(self, reg):
        """Interface function that will be called right after a register\
        was read. Can be used by sub-classes to simulate the exact\
        hardware behavior while reading a register.
        Any action in this routine will not influence the return value
        of the (current call of the) surrounding :meth:`.readByteRegister`
        function.
        
        The current implementation increments the register content if
        the register's memory type is :attr:`MemoryType.VOLATILE`.

        :param Register reg: The register instance to be read.
        :returns: None
        :rtype: none
        """
        if (reg.type == MemoryType.VOLATILE):
            reg.content = reg.content + 1
        return None
    
    def _onPreWrite(self, reg, newData):
        """Interface function that will be called right before a register\
        is written. Can be used by sub-classes to simulate the exact\
        hardware behavior while writing a register. The return value\
        immediately defines the actual content to be written. 
        
        The current implementation just returns the `newData` argument.

        :param Register reg: The register instance to write to.
        :param int newData: The new value that is intended to be stored\
        to that register.
        :returns: The value that will actually be stored to the register.\
        Possibly a modified variant of the `newData` parameter.
        :rtype: int
        """
        del reg
        return newData
    
    def _onPostWrite(self, reg):
        """Interface function that will be called right after a register\
        was written. Can be used by sub-classes to simulate the exact\
        hardware behavior while writing a register.
        
        The current implementation is simply empty.

        :param Register reg: The register instance that was written.
        :returns: None
        :rtype: none
        """
        pass
    

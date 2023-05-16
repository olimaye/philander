"""Serial bus simulation module to support debugging and cross-platform development.

This module provides a fake serial bus implementation to virtualize serial
communication. 
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["SimDev", "SimDevNull", "SimDevMemory", "MemoryType", "Register"]

import enum
import dataclasses
from module import Module
from systypes import ErrorCode

class SimDev():
    """Abstract base class to define the functionality of a simulated serial device.
    
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
        :return: A one-byte integer representing the response of the device\
        and an error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        pass

    def writeByteRegister( self, aReg, data ):
        """Write a single byte value into a certain register.\
        A sub-class must overwrite this method.
        
        The method is expected to store the given value to a register.
        
        :param int aReg: The address of the register to receive the new value.
        :param int data: The new value to store to that register.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        pass

    def readWordRegister( self, aReg ):
        """Read a word from a certain register.
        
        The word is formed from the content of the given register (low)
        and the content of the immediate successor ``aReg+1`` of that
        register (high).
        
        :param int aReg: The address of the low-byte register to be read.
        :return: A 16-bit integer representing the response of the device\
        and an error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        lo, _ = self.readByteRegister(aReg)
        hi, err = self.readByteRegister(aReg+1)
        data = ((hi << 8) | lo)
        return data, err

    def writeWordRegister( self, aReg, data16 ):
        """Write a double-byte (word) value into a certain register.
        
        The method is expected to store the given value to a pair of
        registers. The low-part of the data16 item is stored at the given
        register, while the high-part is put at ``aReg+1``.
        
        :param int aReg: The address of the (low-) register to receive\
        the low-part of the new value.
        :param int data16: The new value to store to that pair of registers.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        bVal = data16 & 0xFF
        self.writeByteRegister(aReg, bVal)
        bVal = (data16 >> 8) & 0xFF
        err = self.writeByteRegister(aReg+1, bVal)
        return err

    def readDWordRegister( self, aReg ):
        """Read a double word from a certain register.
        
        The dword is formed from the content of the four registers,
        starting with the given address ``aReg`` (low-byte of the low-word)
        and its successors ``aReg+1`` (high-byte of the low-word),
        ``aReg+2`` (low-byte of the high-word) and
        ``aReg+3`` (high-byte of the high-word).
        
        :param int aReg: The address of the first (lowest-byte) register to be read.
        :return: A 32-bit integer representing the response of the device\
        and an error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        L, _ = self.readWordRegister( aReg )
        H, err = self.readWordRegister( aReg+2 )
        data = (H << 16) + L
        return data, err

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
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        L = data32 & 0xFFFF
        H = (data32 & 0xFFFF0000) >> 16
        self.writeWordRegister( aReg, L )
        err = self.writeWordRegister( aReg+2, H )
        return err
    
    def readBufferRegister( self, aReg, length ):
        """Read a block of data starting from the given register.
        
        Starting with the given Register address, ``length`` bytes are
        read and returned.
        
        :param int aReg: The address of the first register to be read.
        :param int length: The number of bytes to read.
        :return: A buffer of the indicated length holding the response\
        and an error code indicating success or the reason of failure.
        :rtype: list(int), ErrorCode
        """
        data = [0] * length
        err = ErrorCode.errOk
        for idx in range(length):
            data[idx], err = self.readByteRegister(aReg+idx)
        return data, err

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
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        err = ErrorCode.errOk
        for idx in range( len(data) ):
            err = self.writeByteRegister(aReg+idx, data[idx])
        return err

class SimDevNull( SimDev, Module ):
    """Slim line serial device simulation. Reading retrieves always the same\
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
        SimDevNull.reading    integer    SimDevNull.DEFAULT_READING
        ==================    =======    ==========================
        
        :param dict(str, object) paramDict: Dictionary mapping option names to their respective values.
        :returns: none
        :rtype: None
        """
        paramDict["SimDevNull.reading"] = paramDict.get("SimDevNull.reading", SimDevNull.DEFAULT_READING)
        return None
    
    def open( self, paramDict ):
        """Open the instance and prepare it for use.
        
        Also see :meth:`.module.Module.open`.
        
        :param dict(str, object) paramDict: Configuration parameters as\
        obtained from :meth:`Params_init`, possibly.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        paramDict["SimDevNull.reading"] = paramDict.get("SimDevNull.reading", SimDevNull.DEFAULT_READING)
        self._reading = paramDict["SimDevNull.reading"]
        return ErrorCode.errOk
            
    def readByteRegister( self, aReg ):
        """Read a single byte.
        
        Independent of the given register, the delivered value will
        always be the same. That delivered reading can be configured
        using the SimDevNull.reading option when calling :meth:`open`.

        :param int aReg: The address of the register to be read.\
        Actually ignored.
        :return: A one-byte integer representing the response of the device\
        and an error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        del aReg
        return self._reading, ErrorCode.errOk

    def writeByteRegister( self, aReg, data ):
        """ Write a single byte.

        Actually, does nothing. Also see :meth:`SimDev.writeByteRegister`.
        
        :param int aReg: The address of the register. Ignored.
        :param int data: The new value to store to that register. Ignored.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        del aReg, data
        return ErrorCode.errOk

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
   
class SimDevMemory( SimDev ):
    """Serial bus implementation to simulate a device that can be accessed\
    through a set of memory-based registers. The list of registers\
    must be provided during instantiation.
    """
    
    def __init__(self, regs):
        self._regs = regs
        
    def _findReg(self, regAdr):
        reg = next( (r for r in self._regs if r.address==regAdr), None)
        return reg
                
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

        Also see :meth:`.simbus.SimDev.readByteRegister`.
        
        :param int aReg: The address of the register to be read.
        :return: A one-byte integer representing the response of the device\
        and an error code indicating success or the reason of failure.
        :rtype: int, ErrorCode
        """
        reg = self._findReg( aReg )
        if (reg is None):
            data = 0
            err = ErrorCode.errInvalidParameter
        else:
            err = self._onPreRead( reg )
            data = reg.content
            self._onPostRead( reg )
        return data, err

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
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        reg = self._findReg( aReg )
        err = ErrorCode.errOk
        if not reg:
            err = ErrorCode.errInvalidParameter
        else:
            if (reg.type == MemoryType.RAM):
                newContent = self._onPreWrite(reg, data)
                reg.content = newContent
                err = self._onPostWrite(reg)
            else:
                err = ErrorCode.errFailure
        return err

    def _onPreRead(self, reg):
        """Interface function that will be called right before a register\
        is read. Can be used by sub-classes to simulate the exact\
        hardware behavior while reading a register. Modifying the
        register content here, would highly affect the return value
        of the surrounding :meth:`.readByteRegister` function.
        
        The return value is to indicate if the read operation will succeed.
        
        The current implementation is simply empty.

        :param Register reg: The register instance to be read.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        del reg
        return ErrorCode.errOk
    
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
        
        The return value is to indicate if the write operation succeeded.        
        
        The current implementation is simply empty.

        :param Register reg: The register instance that was written.
        :return: An error code indicating success or the reason of failure.
        :rtype: ErrorCode
        """
        del reg
        return ErrorCode.errOk
    

"""Provide the serial bus API while simulating a virtual serial bus.

An application should never use this module directly. Instead, the
system factory will provide suitable instances.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["_SerialBus_Sim" ]

from philander.serialbus import SerialBus
from philander.simdev import SimDevNull
from philander.sysfactory import SysProvider
from philander.systypes import ErrorCode


class _SerialBus_Sim( SerialBus ):
    """Simulative serial bus implementation.
    """
    
    def __init__(self):
        super().__init__()
        self.provider = SysProvider.SIM
        
    def attach( self, device ):
        ret = super().attach( device  )
        if ret.isOk():
            moduleName = getattr(device, "simModuleName", None)
            className = getattr(device, "simClassName", None)
            if isinstance(moduleName, str) and isinstance(className, str)\
               and moduleName and className:
                if not hasattr(device, "sim"):
                    try:
                        module = __import__(moduleName, None, None, [className])
                        cls = getattr( module, className )
                        device.sim = cls()
                    except ImportError:
                        ret = ErrorCode.errUnavailable
            elif not hasattr(device, "sim"):
                device.sim = SimDevNull()
                ret = ErrorCode.errOk
        return ret
    
    def readByteRegister( self, device, reg ):
        try:
            data, err = device.sim.readByteRegister( reg )
        except (AttributeError, TypeError):
            data, err = 0, ErrorCode.errFailure
        return data, err

    def writeByteRegister( self, device, reg, data ):
        try:
            err = device.sim.writeByteRegister( reg, data )
        except (AttributeError, TypeError):
            err = ErrorCode.errFailure
        return err

    def readWordRegister( self, device, reg ):
        try:
            data, err = device.sim.readWordRegister( reg )
        except (AttributeError, TypeError):
            data, err = 0, ErrorCode.errFailure
        return data, err

    def writeWordRegister( self, device, reg, data16 ):
        try:
            err = device.sim.writeWordRegister( reg, data16 )
        except (AttributeError, TypeError):
            err = ErrorCode.errFailure
        return err

    def readDWordRegister( self, device, reg ):
        try:
            data, err = device.sim.readDWordRegister( reg )
        except (AttributeError, TypeError):
            data, err = 0, ErrorCode.errFailure
        return data, err

    def writeDWordRegister( self, device, reg, data32 ):
        try:
            err = device.sim.writeDWordRegister( reg, data32 )
        except (AttributeError, TypeError):
            err = ErrorCode.errFailure
        return err
    
    def readBufferRegister( self, device, reg, length ):
        try:
            data, err = device.sim.readBufferRegister( reg, length )
        except (AttributeError, TypeError):
            data, err = 0, ErrorCode.errFailure
        return data, err

    def writeBufferRegister( self, device, reg, data ):
        try:
            err = device.sim.writeBufferRegister( reg, data )
        except (AttributeError, TypeError):
            err = ErrorCode.errFailure
        return err


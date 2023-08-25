"""A module for the FastGait ActorUnit driver implementations.

In case of FOG, the ActorUnit is alerted via BlueTooth and starts
vibrating in pulses, giving the patient a tactile cueing impulse.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Event", "ActorUnit",]

from enum import auto, unique, Enum
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakDBusError
from threading import Thread, Lock
import asyncio
import logging

from .actuator import Actuator
from .ble import BLE
from .systypes import ErrorCode

@unique
class Event( Enum ):
    """Data class to represent events emitted by the ActorUnit.
    """
    cueStandard    = auto()
    cueStop        = auto()
    
    
class ActorUnit( BLE, Actuator ):
    """Implementation of the vibration belt driver, also called ActorUnit.
    """

    #
    # Public attributes
    #
    
    MOTORS_1 = 1
    """First actuator"""
    MOTORS_2 = 2
    """Second actuator"""
    MOTORS_NONE = 0
    """Mnemonics for no actuator"""
    MOTORS_ALL  = MOTORS_1 | MOTORS_2
    """Mnemonics for all actuators"""
    
    
    #
    # Pulses are emitted periodically in rectangle form and the low-level
    # API allows to configure:
    #   - the length of one period,
    #   - the length of the on-part,
    #   - an initial delay and
    #   - the number of periods to run.
    #
    #            |< PULSE ON >|
    #            _____________       _____________       ______     ON
    # ...........|            |______|            |______|     ...  OFF
    #
    #|<  DELAY  >|<   PULSE PERIOD  >|
    #
    
    DELAY_DEFAULT           = 0     # immediately
    """Delay of the first pulse, given in milliseconds 0...65535 (0xFFFF). Zero (0) to start cueing immediately."""
    PULSE_PERIOD_DEFAULT    = 200  # ms
    """Pulse period in milliseconds 0...65535 (0xFFFF)."""
    PULSE_ON_DEFAULT        = 120   # ms; 60% duty cycle
    """Pulse ON duration in milliseconds 0...65535 (0xFFFF). Must be less than the period."""
    PULSE_COUNT_DEFAULT     = 3
    """Total number of pulses 0...255. Zero (0) means infinitely."""
    PULSE_INTENSITY_DEFAULT = 80    # 80% strength
    """Intensity of the ON phase vibration [0...100]."""
    ACTUATORS_DEFAULT       = MOTORS_ALL # All motors
    """Motor selection used for vibration [0...3]: Motors #1, or #2 or both."""

    CMD_START         = 0x01
    """Command to start a vibration as specified by further parameters.""" 
    CMD_STOP          = 0x02
    """Command to immediately stop vibration.""" 
    CMD_SET_DEFAULT   = 0x03
    """Configure default vibration parameters."""
    CMD_GET_DEFAULT   = 0x04
    """Retrieve current default configuration:"""
    CMD_START_DEFAULT = 0x05
    """Start vibration as specified by the default parameters."""
    
    TIMER_KEEP  = 0x00
    """Vibration parameter indicating to keep the current timer setting:"""
    TIMER_RESET = 0x01
    """Vibration parameter to reset the timer."""
    
    CMDBUF_STOP          = bytearray( [CMD_STOP] )
    """Command buffer to stop vibration."""
    CMDBUF_GET_DEFAULT   = bytearray( [CMD_GET_DEFAULT] )
    """Command buffer to retrieve default vibration parameters."""
    CMDBUF_START_DEFAULT = bytearray( [CMD_START_DEFAULT] )
    """Complete command buffer to start vibration using the default parameter set."""

    # BLE UUIDs
    DEVICE_UUID         = '0000fa01-0000-1000-8000-00805f9b34fb'
    CHARACTERISTIC_UUID = '0000fa61-0000-1000-8000-00805f9b34fb'
    

    #
    # Private attributes
    #
    
    #
    # Module API
    #

    def __init__( self ):
        # Initialize base class attributes
        super().__init__()
        # Create instance attributes
        defDict = {}
        ActorUnit.Params_init(defDict)
        self.delay = defDict["ActorUnit.delay"]
        self.pulsePeriod = defDict["ActorUnit.pulsePeriod"]
        self.pulseOn = defDict["ActorUnit.pulseOn"]
        self.pulseCount = defDict["ActorUnit.pulseCount"]
        self.pulseIntensity = defDict["ActorUnit.pulseIntensity"]
        self.actuators = defDict["ActorUnit.actuators"]
        self.dataBuf = bytearray( 11 )

    @classmethod
    def Params_init( cls, paramDict ):
        """Initialize parameters with their defaults.
        
        The following settings are supported:
        
        ===============================    ==========================================================================================================
        Key name                           Value type, meaning and default
        ===============================    ==========================================================================================================
        ActorUnit.delay                    ``int`` [0...65535] Initial delay in ms; :attr:`DELAY_DEFAULT`
        ActorUnit.pulsePeriod              ``int`` [0...65535] Length of one period in ms; :attr:`PULSE_PERIOD_DEFAULT`
        ActorUnit.pulseOn                  ``int`` [0...pulsePeriod] Length of the active part in that period in ms; :attr:`PULSE_ON_DEFAULT`
        ActorUnit.pulseCount               ``int`` [0...255] Number of pulses. Zero (0) means infinite pulses. :attr:`PULSE_COUNT_DEFAULT`
        ActorUnit.pulseIntensity           ``int`` [0...100] Intensity of the pulses given as a percentage %. :attr:`PULSE_INTENSITY_DEFAULT`
        ActorUnit.actuators                Motors to be used for the pulses [0...3] meaning none, left, right, both motors; :attr:`ACTUATORS_DEFAULT`
        ===============================    ==========================================================================================================

        Also see: :meth:`.Module.Params_init`.
        
        :param dict(str, object) paramDict: The configuration dictionary.
        :returns: none
        :rtype: None
        """
        if not "ActorUnit.delay" in paramDict:
            paramDict["ActorUnit.delay"] = ActorUnit.DELAY_DEFAULT
        if not "ActorUnit.pulsePeriod" in paramDict:
            paramDict["ActorUnit.pulsePeriod"] = ActorUnit.PULSE_PERIOD_DEFAULT
        if not "ActorUnit.pulseOn" in paramDict:
            paramDict["ActorUnit.pulseOn"] = ActorUnit.PULSE_ON_DEFAULT
        if not "ActorUnit.pulseCount" in paramDict:
            paramDict["ActorUnit.pulseCount"] = ActorUnit.PULSE_COUNT_DEFAULT
        if not "ActorUnit.pulseIntensity" in paramDict:
            paramDict["ActorUnit.pulseIntensity"] = ActorUnit.PULSE_INTENSITY_DEFAULT
        if not "ActorUnit.actuators" in paramDict:
            paramDict["ActorUnit.actuators"] = ActorUnit.ACTUATORS_DEFAULT
        super(ActorUnit, cls).Params_init( paramDict )
        return None
    
    def open( self, paramDict ):
        """Initialize an instance and prepare it for use.

        Also see: :meth:`.Module.open`.
        
        :param dict(str, object) paramDict: Configuration parameters as\
        possibly obtained from :meth:`Params_init`.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
        defParam = {}
        ActorUnit.Params_init( defParam )
        
        sKey = "ActorUnit.delay"
        paramDict[sKey] = paramDict.get( sKey, defParam[sKey] )
        val = paramDict[sKey]
        if (val < 0) or (val > 0xFFFF):
            val = defParam[sKey]
            paramDict[sKey] = val
            result = ErrorCode.errInvalidParameter
        self.delay = val
            
        sKey = "ActorUnit.pulsePeriod"
        paramDict[sKey] = paramDict.get( sKey, defParam[sKey] )
        val = paramDict[sKey]
        if (val < 0) or (val > 0xFFFF):
            val = defParam[sKey]
            paramDict[sKey] = val
            result = ErrorCode.errInvalidParameter
        self.pulsePeriod = val
            
        sKey = "ActorUnit.pulseOn"
        paramDict[sKey] = paramDict.get( sKey, defParam[sKey] )
        val = paramDict[sKey]
        if (val < 0) or (val > self.pulsePeriod):
            val = self.pulsePeriod / 2
            paramDict[sKey] = val
            result = ErrorCode.errInvalidParameter
        self.pulseOn = val

        sKey = "ActorUnit.pulseCount"
        paramDict[sKey] = paramDict.get( sKey, defParam[sKey] )
        val = paramDict[sKey]
        if (val < 0) or (val > 0xFF):
            val = defParam[sKey]
            paramDict[sKey] = val
            result = ErrorCode.errInvalidParameter
        self.pulseCount = val
            
        sKey = "ActorUnit.pulseIntensity"
        paramDict[sKey] = paramDict.get( sKey, defParam[sKey] )
        val = paramDict[sKey]
        if (val < 0) or (val > 100):
            val = defParam[sKey]
            paramDict[sKey] = val
            result = ErrorCode.errInvalidParameter
        self.pulseIntensity = val
            
        sKey = "ActorUnit.actuators"
        paramDict[sKey] = paramDict.get( sKey, defParam[sKey] )
        val = paramDict[sKey]
        if (val < ActorUnit.MOTORS_NONE) or (val > ActorUnit.MOTORS_ALL):
            val = defParam[sKey]
            paramDict[sKey] = val
            result = ErrorCode.errInvalidParameter
        self.actuators = val
            
        if (result == ErrorCode.errOk):
            result = super().open( paramDict )
        
        #self.couple()
        return result

    
    #
    # Actuator API
    #
    def action(self, pattern=None):
        """Executes a predefined action or movement pattern with this actuator.
        
        :param int pattern: The action pattern to execute.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del pattern
        result = self.writeCharacteristic( ActorUnit.CMDBUF_START_DEFAULT )
        return result

    def startOperation(self, direction=Actuator.Direction.positive,
                       strengthIntensity = self.pulseIntensity,
                       onSpeedDuty = self.pulseOn,
                       ctrlInterval = self.pulsePeriod,
                       durationLengthCycles = self.pulseCount ):
        """Issue a start command to the actuator unit.

        Make the actor unit start cueing.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del direction
        #Create parametric start-vibration-command buffer
        self.dataBuf[0] = ActorUnit.CMD_START
        self.dataBuf[1] = onSpeedDuty & 0xFF
        self.dataBuf[2] = onSpeedDuty >> 8
        self.dataBuf[3] = ctrlInterval & 0xFF
        self.dataBuf[4] = ctrlInterval >> 8
        self.dataBuf[5] = self.delay & 0xFF
        self.dataBuf[6] = self.delay >> 8
        self.dataBuf[7] = durationLengthCycles
        self.dataBuf[8] = strengthIntensity
        self.dataBuf[9] = self.actuators
        self.dataBuf[10] = ActorUnit.TIMER_RESET
        
        result = self.writeCharacteristic( self.dataBuf )
        return result
    
    def stopOperation(self):
        """Issue a stop command to the actuator unit.

        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        result = self.writeCharacteristic( ActorUnit.CMDBUF_STOP )
        return result

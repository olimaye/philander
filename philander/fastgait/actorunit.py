"""A module for the FastGait ActorUnit driver implementations.

In case of FOG, the ActorUnit is alerted via BlueTooth and starts
vibrating in pulses, giving the patient a tactile cueing impulse.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Event", \
           "Default", "Intensity", "Motor", "TimerControl", \
           "Configuration", \
           "ActorUnit",]

from dataclasses import dataclass
from enum import auto, unique, Enum, IntEnum, IntFlag

from philander.actuator import Actuator, Direction
from philander.ble import BLE
from philander.configurable import ConfigItem, Configuration as BaseConfiguration, Configurable
from philander.primitives import Percentage
from philander.systypes import ErrorCode


@unique
class Event( Enum ):
    """Data class to represent events emitted by the ActorUnit.
    """
    cueStandard    = auto()
    cueStop        = auto()

@dataclass
class Default:
    """Container for default values that are not part of any other data structure.
    """
    FIRST_DELAY         = 0     # immediately
    """Delay of the first pulse, given in milliseconds 0...65535 (0xFFFF). Zero (0) to start immediately."""
    PULSE_PERIOD        = 200  # ms
    """Pulse period in milliseconds 0...65535 (0xFFFF)."""
    PULSE_ON_DURATION   = 120   # ms; 60% duty cycle
    """Pulse ON duration in milliseconds 0...65535 (0xFFFF). Must be less than the period."""
    PULSE_COUNT         = 3
    """Total number of pulses 0...255. Zero (0) means infinitely."""


class Intensity( Percentage ):
    """Structure to reflect the intensity that the vibration motors run on.
    """
    MIN = 0
    """Minimal intensity."""
    OFF = MIN
    """Least possible intensity, actually no vibration."""
    WEAK = 20
    """Weak intensity."""
    MEDIUM = 50
    """Medium vibration intensity."""
    STRONG = 80
    """Strong intensity."""
    MAX = 100
    """Maximum possible intensity."""
    DEFAULT = STRONG
    """The default intensity."""
    
class Motor(IntFlag):
    """Motor selection used for vibration: Motor #1, or #2 or both."""
    NONE = 0
    """Mnemonics for no actuator"""
    ONE = 1
    """First actuator"""
    TWO = 2
    """Second actuator"""
    ALL  = ONE | TWO
    """Mnemonics for all motors"""
    DEFAULT = ALL
    """Default motor selection."""

class TimerControl(IntEnum):
    """Structure to reflect the timer control setting as part of a vibration command
    """
    KEEP  = 0x00
    """Keep the current timer setting."""
    RESET = 0x01
    """Reset the timer."""
    DEFAULT = RESET
    """Default timer control value."""
    
@dataclass
class Configuration( BaseConfiguration ):
    """Data class to represent a (default) configuration of the ActorUnit.

    Pulses are emitted periodically in rectangle form and the low-level
    API allows to configure:
    - the length of one period,
    - the length of the on-part,
    - an initial delay and
    - the number of periods to run.
    
    ::
    
                    |< PULSE ON >|
                    _____________       _____________       ______     ON
         ...........|            |______|            |______|     ...  OFF
        |<  DELAY  >|<      PERIOD     >|
    
    """
    onDuration  : int = Default.PULSE_ON_DURATION
    """Length of the duty cycle, given in milliseconds."""
    period      : int = Default.PULSE_PERIOD
    """Total length of each interval in milliseconds. Must be larger than the onDuration.""" 
    delay       : int = Default.FIRST_DELAY
    """Wait time before the first interval, specified in milliseconds."""
    numPulses   : int = Default.PULSE_COUNT
    """Number of repetitions. Zero means infinitely."""
    intensity   : int = Intensity.DEFAULT
    """Intensity of the vibration [0...100]."""
    motors      : int = Motor.DEFAULT
    """Motor(s) to use for vibration. 0=none, 1=left, 2=right, 3=both.""" 
    resetTimer  : int = TimerControl.DEFAULT
    """Whether or not to reset the pulse timer. 0=keep, 1=reset."""


class ActorUnit( BLE, Actuator, Configurable ):
    """Implementation of the vibration belt driver, also called ActorUnit.
    
    """

    #
    # Public attributes
    #

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
    
    CMDBUF_STOP          = bytearray( [CMD_STOP] )
    """Command buffer to stop vibration."""
    CMDBUF_GET_DEFAULT   = bytearray( [CMD_GET_DEFAULT] )
    """Command buffer to retrieve default vibration parameters."""
    CMDBUF_START_DEFAULT = bytearray( [CMD_START_DEFAULT] )
    """Complete command buffer to start vibration using the default parameter set."""

    # BLE UUIDs
    #DEVICE_UUID         = '0000fa01-0000-1000-8000-00805f9b34fb'
    CLIENT_NAME         = "FastGait AU"
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
        self.vibConfig = Configuration( ConfigItem.implicit )
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
        ActorUnit.motors                   Motors to be used for the pulses [0...3] meaning none, left, right, both motors; :attr:`MOTORS_DEFAULT`
        All other BLE.* settings as documented at :meth:`.BLE.Params_init`.
        =============================================================================================================================================

        Also see: :meth:`.Module.Params_init`.
        
        :param dict(str, object) paramDict: The configuration dictionary.
        :returns: none
        :rtype: None
        """
        # ActorUnit pulse configuration
        if not "ActorUnit.delay" in paramDict:
            paramDict["ActorUnit.delay"] = Default.FIRST_DELAY
        if not "ActorUnit.pulsePeriod" in paramDict:
            paramDict["ActorUnit.pulsePeriod"] = Default.PULSE_PERIOD
        if not "ActorUnit.pulseOn" in paramDict:
            paramDict["ActorUnit.pulseOn"] = Default.PULSE_ON_DURATION
        if not "ActorUnit.pulseCount" in paramDict:
            paramDict["ActorUnit.pulseCount"] = Default.PULSE_COUNT
        if not "ActorUnit.pulseIntensity" in paramDict:
            paramDict["ActorUnit.pulseIntensity"] = Intensity.DEFAULT
        if not "ActorUnit.motors" in paramDict:
            paramDict["ActorUnit.motors"] = Motor.DEFAULT
        # BLE UUIDs
        if not "BLE.client.name" in paramDict:
            paramDict["BLE.client.name"] = ActorUnit.CLIENT_NAME
        if not "BLE.characteristic.uuid" in paramDict:
            paramDict["BLE.characteristic.uuid"] = ActorUnit.CHARACTERISTIC_UUID
        # General BLE configuration
        super(ActorUnit, cls).Params_init( paramDict )
        return None
    
    @classmethod
    def _extractParameterInt( cls, val, default, lowLimit=0, highLimit=0xFFFF ):
        err = ErrorCode.errOk
        if not isinstance(val, int):
            try:
                intValue = int( val, 0 )
            except ValueError as e:
                intValue = default
                err = ErrorCode.errInvalidParameter
        if (intValue < lowLimit) or (intValue > highLimit):
            intValue = default
            result = ErrorCode.errInvalidParameter
        return intValue, err
    
    
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
        val = paramDict.get( sKey, defParam[sKey] )
        val, result = ActorUnit._extractParameterInt( val, defParam[sKey], 0, 0xFFFF )
        paramDict[sKey] = val
        self.vibConfig.delay = val
            
        sKey = "ActorUnit.pulsePeriod"
        val = paramDict.get( sKey, defParam[sKey] )
        val, result = ActorUnit._extractParameterInt( val, defParam[sKey], 0, 0xFFFF )
        paramDict[sKey] = val
        self.vibConfig.period = val
            
        sKey = "ActorUnit.pulseOn"
        val = paramDict.get( sKey, defParam[sKey] )
        val, result = ActorUnit._extractParameterInt( val, self.vibConfig.period/2, 0, self.vibConfig.period )
        paramDict[sKey] = val
        self.vibConfig.onDuration = val

        sKey = "ActorUnit.pulseCount"
        val = paramDict.get( sKey, defParam[sKey] )
        val, result = ActorUnit._extractParameterInt( val, defParam[sKey], 0, 0xFF )
        paramDict[sKey] = val
        self.vibConfig.numPulses = val
            
        sKey = "ActorUnit.pulseIntensity"
        val = paramDict.get( sKey, defParam[sKey] )
        val, result = ActorUnit._extractParameterInt( val, defParam[sKey], Intensity.MIN, Intensity.MAX )
        paramDict[sKey] = val
        self.vibConfig.intensity = val
            
        sKey = "ActorUnit.motors"
        val = paramDict.get( sKey, defParam[sKey] )
        if isinstance(val, Motor):
            pass
        elif isinstance(val, int):
            val = Motor(val)
        else:
            try:
                val = int( val, 0 )
            except ValueError as e:
                val = defParam[sKey]
                err = ErrorCode.errInvalidParameter
        if (val < Motor.NONE) or (val > Motor.ALL):
            val = defParam[sKey]
            result = ErrorCode.errInvalidParameter
        paramDict[sKey] = val
        self.vibConfig.motors = val
        
        if (result == ErrorCode.errOk):
            sKey = "BLE.client.name"
            paramDict[sKey] = paramDict.get( sKey, defParam[sKey] )
            sKey = "BLE.characteristic.uuid"
            paramDict[sKey] = paramDict.get( sKey, defParam[sKey] )
            result = super().open( paramDict )
        
        #self.couple()
        return result

    #
    # Configurable API
    #
    
    def configure(self, configData):
        """Re-configures the driver's default vibration parameters.

        :param .actorunit.Configuration configData: The configuration to apply.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        result = ErrorCode.errOk
        if (configData is None):
            result = ErrorCode.errFewData
        elif not isinstance(configData, Configuration):
            result = ErrorCode.errInvalidParameter
        else:
            result = ErrorCode.errOk
            # Do range-checking, instead of blunt copy
            if (0 <= configData.period) and (configData.period <= 0xFFFF):
                self.vibConfig.period = configData.period
            else:
                result = ErrorCode.errInvalidParameter
            if (0 <= configData.onDuration) and (configData.onDuration < self.vibConfig.period):
                self.vibConfig.onDuration = configData.onDuration
            else:
                result = ErrorCode.errInvalidParameter
            if (0 <= configData.delay) and (configData.delay <= 0xFFFF):
                self.vibConfig.delay = configData.delay
            else:
                result = ErrorCode.errInvalidParameter
            if (0 <= configData.numPulses) and (configData.numPulses <= 0xFF):
                self.vibConfig.numPulses = configData.numPulses
            else:
                result = ErrorCode.errInvalidParameter
            if (Intensity.MIN <= configData.intensity) and (configData.intensity <= Intensity.MAX):
                self.vibConfig.intensity = configData.intensity
            else:
                result = ErrorCode.errInvalidParameter
            if (Motor.NONE <= configData.motors) and (configData.motors <= Motor.ALL):
                self.vibConfig.motors = configData.motors
            else:
                result = ErrorCode.errInvalidParameter
            if (TimerControl.KEEP <= configData.resetTimer) and (configData.resetTimer <= TimerControl.RESET):
                self.vibConfig.resetTimer = configData.resetTimer
            else:
                result = ErrorCode.errInvalidParameter
                
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
        result, _ = self.writeCharacteristic( ActorUnit.CMDBUF_START_DEFAULT )
        return result

    def startOperation(self, direction=Direction.positive,
                       strengthIntensity = None,
                       onSpeedDuty = None,
                       ctrlInterval = None,
                       durationLengthCycles = None ):
        """Issue a start command to the actuator unit.

        Make the actor unit start cueing.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        del direction
        if (strengthIntensity is None):
            strengthIntensity = self.vibConfig.intensity
        if (onSpeedDuty is None):
            onSpeedDuty = self.vibConfig.onDuration
        if (ctrlInterval is None):
            ctrlInterval = self.vibConfig.period
        if (durationLengthCycles is None):
            durationLengthCycles = self.vibConfig.numPulses
        #Create parametric start-vibration-command buffer
        self.dataBuf[0] = ActorUnit.CMD_START
        self.dataBuf[1] = onSpeedDuty & 0xFF
        self.dataBuf[2] = onSpeedDuty >> 8
        self.dataBuf[3] = ctrlInterval & 0xFF
        self.dataBuf[4] = ctrlInterval >> 8
        self.dataBuf[5] = self.vibConfig.delay & 0xFF
        self.dataBuf[6] = self.vibConfig.delay >> 8
        self.dataBuf[7] = durationLengthCycles
        self.dataBuf[8] = strengthIntensity
        self.dataBuf[9] = self.vibConfig.motors
        self.dataBuf[10] = self.vibConfig.resetTimer
        
        result, _ = self.writeCharacteristic( self.dataBuf )
        return result
    
    def stopOperation(self):
        """Issue a stop command to the actuator unit.

        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        result, _ = self.writeCharacteristic( ActorUnit.CMDBUF_STOP )
        return result

    #
    # Individual specific API
    #

    def getDefault(self):
        """Retrieve default configuration from the remote client unit.

        :return: The configuration and an error code indicating either success or the reason of failure.
        :rtype: Configuration, ErrorCode
        """
        cfg = Configuration()
        err, dataBuf = self.writeCharacteristic( ActorUnit.CMDBUF_GET_DEFAULT,
                                                 readResponse = True )
        if (err == ErrorCode.errOk):
            if ( (dataBuf is None) or (len(dataBuf) < 11) ):
                err = ErrorCode.errFewData
            else:
                # neglect CMD byte at index 0
                cfg.onDuration  = (dataBuf[2] << 8) + dataBuf[1]
                cfg.period      = (dataBuf[4] << 8) + dataBuf[3]
                cfg.delay       = (dataBuf[6] << 8) + dataBuf[5]
                cfg.numPulses   = dataBuf[7]
                cfg.intensity   = dataBuf[8]
                cfg.motors      = Motor( dataBuf[9] )
                cfg.resetTimer  = TimerControl( dataBuf[10] )
        return cfg, err
    
    def setDefault(self, newDefault: Configuration):
        """Store default configuration onto the remote client unit.

        :param newDefault: The configuration to store as the new default.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        self.dataBuf[0] = ActorUnit.CMD_SET_DEFAULT
        self.dataBuf[1] = newDefault.onDuration & 0xFF
        self.dataBuf[2] = newDefault.onDuration >> 8
        self.dataBuf[3] = newDefault.period & 0xFF
        self.dataBuf[4] = newDefault.period >> 8
        self.dataBuf[5] = newDefault.delay & 0xFF
        self.dataBuf[6] = newDefault.delay >> 8
        self.dataBuf[7] = newDefault.numPulses
        self.dataBuf[8] = newDefault.intensity
        self.dataBuf[9] = newDefault.motors
        self.dataBuf[10] = newDefault.resetTimer
        
        result, _ = self.writeCharacteristic( self.dataBuf )
        return result
    

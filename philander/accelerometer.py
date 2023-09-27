"""Abstract interface for accelerometer sensors accessible via serial communication.

Provide an API to abstract from acceleration measurement devices.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Activity", "AxesSign", "Orientation", "Tap",\
           "SamplingMode", \
           "EventSource", "EventContext", "Configuration", "StatusID", "Data",\
           "Accelerometer"]
from dataclasses import dataclass
from enum import Enum, Flag, unique, auto

from .configurable import Configuration
from .interruptable import EventContext as IntEventContext
from .sensor import Sensor


@unique
class Activity(Enum):
    """Identifies general types of human walking activities, that an\
    accelerometer is possibly able to detect or distinguish.
    """
    unknown      = auto()
    still        = auto()
    walking      = auto()
    running      = auto()

class AxesSign(Flag):
    """Data class to name coordinate axes along with their positive or\
    negative sign.
    """
    x            = auto()
    y            = auto()
    z            = auto()
    sign         = auto()
    signPos      = 0
    signNeg      = sign
    none         = 0
    all          = (x | y | z)

class Orientation(Enum):
    """Data class to enumerate orientations that the device carrying the\
    accelerometer may be in.
    """
    standMask     = 0x03
    portraitUp    = 0x00
    portraitDown  = 0x01
    landscapeLeft = 0x02
    landscapeRight= 0x03
    faceMask      = 0x04
    faceUp        = 0
    faceDown      = faceMask
    tiltMask      = 0x08
    tiltStand     = 0
    tiltFlat      = tiltMask
    invalidMask   = 0xF0
    invalidStand  = 0x10
    invalidFace   = 0x20
    invalidTilt   = 0x40
    unknown       = 0xFF

@unique    
class Tap(Flag):
    """Data class to identify different types of tap.
    
    A tap should be understood as a quick finger tip onto some touch
    screen to simulate the click of a mouse. 
    """
    none         = 0
    single       = auto()
    double       = auto()
    triple       = auto()
    
@unique
class SamplingMode(Enum):
    """Mnemonic type to identify different types of sampling techniques,\
    such as averaging, normal or over-sampling.
    """
    average     = auto()
    normal      = auto()
    OSR2        = auto()
    OSR4        = auto()

@unique    
class EventSource(Flag):
    """Data class to hold known event (interrupt) sources.
    """
    none                = 0
    dataReady           = auto()
    fifoWatermark       = auto()
    fifoFull            = auto()
    lowG                = auto()
    lowGTime            = auto()
    highG               = auto()
    highGTime           = auto()
    lowSlope            = auto()
    lowSlopeTime        = auto()
    highSlope           = auto()
    highSlopeTime       = auto()
    significantMotion   = auto()
    tap                 = auto()
    step                = auto()
    gesture             = auto()
    activity            = auto()
    lyingFlat           = auto()
    orientation         = auto()
    error               = auto()
    all                 = 0xFFFFFFFF

@dataclass
class Configuration( Configuration ):
    """Data class to describe common configuration settings.
    
    Use the parental class :attr:`sensor.Configuration.type` attribute
    to de-multiplex the inner data types.
    """
        
    @dataclass
    class CfgRateMode():
        mValue: int = 2
        control: SamplingMode = SamplingMode.normal

    @dataclass
    class CfgInterrupt():
        delay:      int = 10
        thrshld:    int = 1500
        hysteresis: int = 200
        axes:       AxesSign = AxesSign.z
        event:      EventSource = EventSource.dataReady
        
    rateMode:   CfgRateMode = None
    eventCondition: CfgInterrupt = None
        
@unique
class StatusID(Enum):
    """Data class to comprise different types of status information.
    """
    dieTemp     = auto()
    dataReady   = auto()
    interrupt   = auto()
    fifo        = auto()
    error       = auto()
    activity    = auto()
    stepCount   = auto()
    highG       = auto()
    highSlope   = auto()
    orientation = auto()
    tap         = auto()
    NVM         = auto()
    sensorTime  = auto()

@dataclass
class Data:
    """Container type to wrap an accelerometer's primary measurement result.
    
    Measurement data should always be expressed as a signed value in
    per-mille of the standard gravity milli-g [mg] along the three axes.
    Of course::
    
        1000 mg = 1 g = 9,80665 m/s^2
        
    """
    x:  int
    y:  int
    z:  int

@dataclass
class EventContext( IntEventContext ):
    """Data class holding the context information of an event (interrupt).
    
    Use the :attr:`source` attribute to de-multiplex the inner data items.
    """
    source:     EventSource = EventSource.none
    data:       Data = (0,0,0)
    status:     int = 0

        
class Accelerometer(Sensor):
    """Abstract base class for digital accelerometers.
    """
    pass    

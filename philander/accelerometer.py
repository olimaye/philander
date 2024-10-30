"""Abstract interface for accelerometer sensors accessible via serial communication.

Provide an API to abstract from acceleration measurement devices.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["Activity", "AxesSign", "Orientation", "Tap",\
           "SamplingMode", \
           "EventSource", "EventContext", "Configuration", "StatusID", "Data",\
           "Accelerometer"]

from .penum import Enum, Flag, unique, auto, idiotypic, dataclass

from .configurable import Configuration as ConfConfiguration
from .interruptable import EventContext as IntEventContext
from .sensor import Sensor


@unique
@idiotypic
class Activity(Enum):
    """Identifies general types of human walking activities, that an\
    accelerometer is possibly able to detect or distinguish.
    """
    unknown      = auto()
    still        = auto()
    walking      = auto()
    running      = auto()

@idiotypic
class AxesSign(Flag):
    """Data class to name coordinate axes along with their positive or\
    negative sign.
    """
    x            = 0x01
    y            = 0x02
    z            = 0x04
    sign         = 0x08
    signPos      = 0
    signNeg      = sign
    none         = 0
    all          = (x | y | z)

@idiotypic
class Orientation(Flag):
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
@idiotypic
class Tap(Enum):
    """Data class to identify different types of tap.
    
    A tap should be understood as a quick finger tip onto some touch
    screen to simulate the click of a mouse. 
    """
    none         = auto()
    single       = auto()
    double       = auto()
    triple       = auto()
    
@unique
@idiotypic
class SamplingMode(Enum):
    """Mnemonic type to identify different types of sampling techniques,\
    such as averaging, normal or over-sampling.
    """
    average     = auto()
    normal      = auto()
    OSR2        = auto()
    OSR4        = auto()

@unique    
@idiotypic
class EventSource(Flag):
    """Data class to hold known event (interrupt) sources.
    """
    none                = 0
    dataReady           = 0x00000001
    fifoWatermark       = 0x00000002
    fifoFull            = 0x00000004
    lowG                = 0x00000008
    lowGTime            = 0x00000010
    highG               = 0x00000020
    highGTime           = 0x00000040
    lowSlope            = 0x00000080
    lowSlopeTime        = 0x00000100
    highSlope           = 0x00000200
    highSlopeTime       = 0x00000400
    significantMotion   = 0x00000800
    tap                 = 0x00001000
    step                = 0x00002000
    gesture             = 0x00004000
    activity            = 0x00008000
    lyingFlat           = 0x00010000
    orientation         = 0x00020000
    error               = 0x00040000
    all                 = 0xFFFFFFFF

@dataclass
class Configuration( ConfConfiguration ):
    """Data class to describe common configuration settings.
    
    Use the parental class :attr:`sensor.Configuration.item` attribute
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
@idiotypic
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
    x:  int = 0
    y:  int = 0
    z:  int = 0

@dataclass
class EventContext( IntEventContext ):
    """Data class holding the context information of an event (interrupt).
    
    Use the :attr:`source` attribute to de-multiplex the inner data items.
    """
    source:     EventSource = EventSource.none
    data:       Data = Data(x=0,y=0,z=0)
    status:     int = 0

        
class Accelerometer(Sensor):
    """Abstract base class for digital accelerometers.
    """
    pass    

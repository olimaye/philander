from dataclasses import dataclass
from enum import Enum, Flag, unique, auto
from Interruptable import Interruptable, Event, EventContext as InterruptableEventContext
import Sensor

@unique
class Activity(Enum):
    actUnknown      = auto()
    actStill        = auto()
    actWalking      = auto()
    actRunning      = auto()

class AxesSign(Flag):
    axsX            = auto()
    axsY            = auto()
    axsZ            = auto()
    axsSign         = auto()
    axsSignPos      = 0
    axsSignNeg      = axsSign
    axsNone         = 0
    axsAll          = (axsX | axsY | axsZ)

class Orientation(Enum):
    orientStandMask = 0x03
    orientPortUp    = 0x00
    orientPortDown  = 0x01
    orientLandLeft  = 0x02
    orientLandRight = 0x03
    orientFaceMask  = 0x04
    orientFaceUp    = 0
    orientFaceDown  = orientFaceMask
    orientTiltMask  = 0x08
    orientTiltStand = 0
    orientTiltFlat  = orientTiltMask
    orientInvalidMask   = 0xF0
    orientInvalidStand  = 0x10
    orientInvalidFace   = 0x20
    orientInvalidTilt   = 0x40
    orientUnknown       = 0xFF

@unique    
class Tap(Flag):
    tapNone         = 0
    tapSingle       = auto()
    tapDouble       = auto()
    tapTriple       = auto()
    
@unique
class SamplingMode(Enum):
    smplAverage     = auto()
    smplNormal      = auto()
    smplOSR2        = auto()
    smplOSR4        = auto()

@unique    
class EventSource(Flag):
    evtSrcNone      = 0
    evtSrcDataRdy   = auto()
    evtSrcFifoWM    = auto()
    evtSrcFifoFull  = auto()
    evtSrcLowG      = auto()
    evtSrcLowGTime  = auto()
    evtSrcHighG     = auto()
    evtSrcHighGTime = auto()
    evtSrcLowSlope  = auto()
    evtSrcLowSlopeTime = auto()
    evtSrcHighSlope = auto()
    evtSrcHighSlopeTime = auto()
    evtSrcSigMotion = auto()
    evtSrcTap       = auto()
    evtSrcStep      = auto()
    evtSrcGesture   = auto()
    evtSrcActivity  = auto()
    evtSrcLyingFlat = auto()
    evtSrcOrientation = auto()
    evtSrcError     = auto()
    evtSrcAll       = 0xFFFFFFFF


@dataclass
class Configuration( Sensor.Configuration ):
        
    @dataclass
    class CfgRateMode():
        mValue: int = 2
        control: SamplingMode = SamplingMode.smplNormal

    @dataclass
    class CfgFifo():
        watermark:  int = 4
        control:    int = 0
        
    @dataclass
    class CfgInterrupt():
        delay:      int = 10
        thrshld:    int = 1500
        hysteresis: int = 200
        axes:       AxesSign = AxesSign.axsZ
        event:      EventSource = EventSource.evtSrcDataRdy
        
    rateMode:   CfgRateMode = None
    fifo:       CfgFifo = None
    armedEvents:    EventSource = EventSource.evtSrcNone
    eventCondition: CfgInterrupt = None
    
    
        
@unique
class StatusID(Enum):
    StatusDieTemp   = auto()
    StatusDataReady = auto()
    StatusInterrupt = auto()
    StatusFifo      = auto()
    StatusError     = auto()
    StatusActivity  = auto()
    StatusStepCnt   = auto()
    StatusHighG     = auto()
    StatusHighSlope = auto()
    StatusOrientation = auto()
    StatusTap       = auto()
    StatusNVM       = auto()
    StatusSensorTime = auto()

@dataclass
class Data:
    x:  int
    y:  int
    z:  int

@dataclass
class EventContext( InterruptableEventContext ):
    source:     EventSource = EventSource.evtSrcNone
    data:       Data = (0,0,0)
    status:     int = 0
    
    def __init__(self):
        super().__init__()

#
#
#        
class Accelerometer(Interruptable, Sensor.Sensor):
    pass    
   
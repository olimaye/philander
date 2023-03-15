from dataclasses import dataclass
from enum import Enum, Flag, unique, auto
from Interruptable import Interruptable, EventContextControl
from Sensor import Sensor

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
class ConfigItem(Enum):
    cfgRateAvg      = auto()
    cfgRange        = auto()
    cfgFifo         = auto()
    cfgEventArm     = auto()
    cfgEventCondition = auto()
    
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
class Configuration():
    
    @dataclass
    class CfgRateMode():
        rate:   int
        mValue: int
        control:    SamplingMode

    @dataclass
    class CfgFifo():
        watermark:  int
        control:    int
        
    @dataclass
    class CfgInterrupt():
        delay:      int
        thrshld:    int
        hysteresis: int
        axes:       AxesSign
        event:      EventSource
        
    type:       ConfigItem
    rateMode:   CfgRateMode
    range:      int
    fifo:       CfgFifo
    armedEvents:    EventSource
    eventCondition: CfgInterrupt
    
        
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

@unique
class Event(Enum):
    evtNone   = auto()
    evtInt1   = auto()
    evtInt2   = auto()

@dataclass
class EventContext:
    control:    EventContextControl
    remainInt:  int
    source:     EventSource
    data:       Data
    status:     int

#
#
#        
class Accelerometer(Interruptable, Sensor):
    pass    
    
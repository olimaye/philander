from dataclasses import dataclass, field
from enum import Enum, unique, auto
from Module import Module
from systypes import ErrorCode
from typing import List

@unique
class ConfigItem(Enum):
    cfgRate  = auto()
    cfgRange = auto()
    cfgFifo         = auto()
    cfgEventArm     = auto()
    cfgEventCondition = auto()

@dataclass
class Configuration():
    type: ConfigItem
    value: int = 1
    
@unique
class CalibType(Enum):
    calibDefault            = auto()
    calibZero               = auto()
    calibOne                = auto()
    calibHundred            = auto()
    calibTrueValue          = auto()
    calibExpose1            = auto()
    calibExpose2            = auto()
    calibExpose3            = auto()
    calibOffset             = auto()
    calibShiftOffset        = auto()
    calibLinear             = auto()
    calibLinearRel          = auto()
    calibParam              = auto()
    calibParamRel           = auto()
    calibTrueMeasurement    = auto()
    calibTrueMeasurement2   = auto()
    calibKnownMeasurement   = auto()
    calibKnownMeasurement1  = auto()
    calibKnonwMeasurement2  = auto()
    calibKnonwMeasurement3  = auto()
    calibTemperature        = auto()

@dataclass
class _CalibrationData_linear:
    offset:             object = None
    sensitivity:        object = None
    
@dataclass
class _CalibrationData_iLinear:
    offset:             int = 0
    sensitivity:        int = 0
    
@dataclass
class _CalibrationData_trueMeasurement:
    measurement:        object = None
    trueValue:          object = None
    
@dataclass
class _CalibrationData_knownMeasurement:
    measure:            List[int] = field( default_factory=lambda : [0,0,0] )
    trueValue:          object = None
    
@dataclass
class CalibrationData:
    trueValue:          object = None
    offset:             object = None
    iOffset:            int = 0
    linear:             _CalibrationData_linear = _CalibrationData_linear()
    iLinear:            _CalibrationData_iLinear= _CalibrationData_iLinear()
    param:              object = None
    trueMeasurement:    _CalibrationData_trueMeasurement = _CalibrationData_trueMeasurement()
    trueMeasurement2:   _CalibrationData_trueMeasurement = _CalibrationData_trueMeasurement()
    knownMeasurement:   List[_CalibrationData_knownMeasurement] = field( default_factory=lambda :
                                                                  [_CalibrationData_knownMeasurement(),
                                                                   _CalibrationData_knownMeasurement(),
                                                                   _CalibrationData_knownMeasurement()] )
    temp:               _CalibrationData_iLinear = _CalibrationData_iLinear()

@dataclass
class Calibration:
    type:       CalibType = CalibType.calibDefault
    data:       CalibrationData = CalibrationData()
        
    
class SelfTest:
    CONNECTION      = 0x0001    # Test physical connection, possibly by reading ID
    FUNCTIONAL      = 0x0002    # Functional test, subject to the implementation
    SELFTEST_ALL    = 0xFFFF    # All possible self tests
    
class Info:
    VALID_CHIPID    = 0x01  # The chipID is valid
    VALID_REVMAJOR  = 0x02  # Major revision is valid.
    VALID_REVMINOR  = 0x04  # Minor revision is valid.
    VALID_MODELID   = 0x08  # Valid module identification.
    VALID_MANUFACID = 0x10  # Valid manufacturer ID
    VALID_SERIALNUM = 0x20  # Serial number is valid.
    VALID_NOTHING   = 0x00  # No attribute valid.
    VALID_ANYTHING  = 0xFF  # All attributes are valid.

    def __init__(self):
        self.validity = Info.VALID_NOTHING
        self.chipID = 0
        self.revMajor = 0
        self.revMinor = 0
        self.modelID = 0
        self.manufacturerID = 0
        self.serialNumber = 0


class Sensor(Module):

    #
    # Initializes the sensor.
    #
    def __init__( self ):
        defaults = dict()
        self.Params_init( defaults )
        # Create instance attributes
        self.dataRange = paramDict["Sensor.dataRange"]
        self.dataRate  = paramDict["Sensor.dataRate"]
 
    # The only input parameter is a dictionary containing key-value pairs that
    # configure the instance. Regarded key names and their meanings are:
    # Sensor.dataRange : Upper/lower limit of expected measurements
    # Sensor.dataRate  : Measurement frequency
    @classmethod
    def Params_init( cls, paramDict ):
        # Fill paramDict with defaults
        if not ("Sensor.dataRange" in paramDict):
            paramDict["Sensor.dataRange"] = 1
        if not ("Sensor.dataRate" in paramDict):
            paramDict["Sensor.dataRate"] = 1
        return None

    #
    #
    #
    def open(self, paramDict):
        defaults = dict()
        self.Params_init( defaults )
        ret = ErrorCode.errOk
        if ("Sensor.dataRange" in paramDict):
            cfg = Configuration( ConfigItem.cfgRange, value=paramDict["Sensor.dataRange"])
            ret = self.configure( cfg )
        else:
            paramDict["Sensor.dataRange"] = defaults["Sensor.dataRange"]
        if ("Sensor.dataRate" in paramDict):
            cfg = Configuration( ConfigItem.cfgRate, value=paramDict["Sensor.dataRate"])
            ret = self.configure( cfg )
        else:
            paramDict["Sensor.dataRate"] = defaults["Sensor.dataRate"]
        return ret
    
    #
    # Sensor self test
    #
    def selfTest(self, tests):
        del tests
        return ErrorCode.errNotSupported

    #
    # Soft resets the sensor. The device is in some default state, afterwards and
    # must be re-configured according to the application's needs.
    #
    def reset(self):
        return ErrorCode.errNotSupported

    #
    # Configures the sensor
    #
    def configure(self, configData):
        ret = ErrorCode.errOk
        if (configData.type == ConfigItem.cfgRange):
            self.dataRange = configData.value
        elif (configData.type == ConfigItem.cfgRate):
            self.dataRate = configData.value
        else:
            ret = ErrorCode.errNotSupported
        return ret

    #
    # Calibrates the sensor
    #
    def calibrate(self, calib):
        del calib
        return ErrorCode.errNotSupported


    #
    # Gets static info data from sensor
    #
    def getInfo(self):
        info = Info()
        ret = ErrorCode.errOk
        return info, ret

    #
    # Gets dynamic status data from sensor
    #
    def getStatus(self, statusID):
        del statusID
        return None, ErrorCode.errNotSupported

    #
    # Retrieves the most recent data available and returns immediately.
    # This function will never block, but may read data that has been
    # read before.
    #
    def getLatestData(self):
        return None, ErrorCode.errNotSupported
    
    #
    # Retrieves the next data, possibly waiting (blocking) depending on the
    # data dataRate configured.
    # Always returns with fresh, new data, never read before.
    #
    def getNextData(self):
        return None, ErrorCode.errNotSupported

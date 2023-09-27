"""Driver implementation for the HTU21D relative humidity and temperature sensor.

More information on the functionality of the chip can be found at
the TE site:
https://www.te.com/deu-de/product-CAT-HSC0004.html
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["StatusID", "Data", "HTU21D"]

from dataclasses import dataclass
from enum import unique, Enum, auto
import time    

from .configurable import Configuration, ConfigItem
from .hygrometer import Data as hygData
from .sensor import Sensor, SelfTest
from .serialbus import SerialBusDevice
from .systypes import ErrorCode
from .thermometer import Data as thmData


@unique
class StatusID(Enum):
    """Data class to comprise different types of status information.
    """
    powerOk     = auto()

@dataclass
class Data( thmData, hygData ):
    """Container type to wrap this sensor's measurement result.
    
    This data type carries both, temperature and humidity measurement
    results.
    Also see: :class:`.thermometer.Data`, :class:`.hygrometer.Data` 
    """
    
    pass

class HTU21D( Sensor, SerialBusDevice ):
    """HTU21D driver implementation.
    """
    
    # Chip address
    ADDRESS = 0x40
    
    # Configuration mnemonics
    CFG_RESOLUTION_HUM8_TEMP12    = 12
    CFG_RESOLUTION_HUM10_TEMP13   = 13
    CFG_RESOLUTION_HUM11_TEMP11   = 11
    CFG_RESOLUTION_HUM12_TEMP14   = 14
    CFG_RESOLUTION_DEFAULT        = CFG_RESOLUTION_HUM12_TEMP14
    
    # Communication commands and registers
    CMD_GET_TEMP_HOLD  = 0xE3
    CMD_GET_HUM_HOLD   = 0xE5
    CMD_GET_TEMP       = 0xF3
    CMD_GET_HUM        = 0xF5
    CMD_WRITE_USR_REG  = 0xE6
    CMD_READ_USR_REG   = 0xE7
    CMD_SOFT_RESET     = 0xFE
    
    # Register content
    CNT_USR_RESOLUTION     = 0x81
    CNT_USR_RESOLUTION_RH12_T14 = 0x00
    CNT_USR_RESOLUTION_RH8_T12  = 0x01
    CNT_USR_RESOLUTION_RH10_T13 = 0x80
    CNT_USR_RESOLUTION_RH11_T11 = 0x81
    CNT_USR_RESOLUTION_DEFAULT  = CNT_USR_RESOLUTION_RH12_T14
    CNT_USR_POWER          = 0x40
    CNT_USR_POWER_GOOD     = 0x00
    CNT_USR_POWER_LOW      = CNT_USR_POWER
    CNT_USR_RESERVED       = 0x38
    CNT_USR_CHIP_HEATER    = 0x04
    CNT_USR_CHIP_HEATER_ON = CNT_USR_CHIP_HEATER   # Consumes 5.5mW, heat by ~1.0°C
    CNT_USR_CHIP_HEATER_OFF= 0x00
    CNT_USR_OTP_RELOAD     = 0x02
    CNT_USR_OTP_RELOAD_ENABLE=0x00
    CNT_USR_OTP_RELOAD_DISABLE = CNT_USR_OTP_RELOAD
    CNT_USR_DEFAULT = CNT_USR_RESOLUTION_DEFAULT | CNT_USR_POWER_GOOD | CNT_USR_CHIP_HEATER_OFF | CNT_USR_OTP_RELOAD_DISABLE
    
    # Diagnosis bits in a data frame
    DIAG_CIRC_OPEN     = 0
    DIAG_TEMP_OK       = 1  # documented as 0, should it be 1 ?
    DIAG_HUM_OK        = 2
    DIAG_CIRC_SHORT    = 3
    
    # Time constants
    MEAS_TIME_MAX_MS_RH8    = 3
    MEAS_TIME_MAX_MS_RH10   = 5
    MEAS_TIME_MAX_MS_RH11   = 8
    MEAS_TIME_MAX_MS_RH12   = 16
    MEAS_TIME_MAX_MS_T11    = 7
    MEAS_TIME_MAX_MS_T12    = 13
    MEAS_TIME_MAX_MS_T13    = 25
    MEAS_TIME_MAX_MS_T14    = 50
    RESET_TIME_MAX_MS       = 15
    SELFTEST_TIME_WAIT_S    = 5
    
    def __init__(self):
        self.timeStampLatest = 0
        self.latestData = None
        self.measInterval    = 0  # in seconds
        self.resolution = HTU21D.CNT_USR_RESOLUTION_DEFAULT
        super().__init__()
        
    @classmethod
    def Params_init(cls, paramDict):
        """Initializes configuration parameters with defaults.
        
        The following settings are supported:
        
        =============================    ==========================================================================================================
        Key name                         Value type, meaning and default
        =============================    ==========================================================================================================
        SerialBusDevice.address          ``int`` I2C serial device address, must be :attr:`ADDRESS`; default is :attr:`ADDRESS`.
        Sensor.dataRate                  ``int`` Data rate in Hz; default is set by :meth:`.Sensor.Params_init`.
        HTU21D.resolution                ``int`` Resolution in bits; default is :attr:`.CFG_RESOLUTION_HUM12_TEMP14`.
        =============================    ==========================================================================================================
        
        Also see: :meth:`.Sensor.Params_init`, :meth:`.SerialBusDevice.Params_init`. 
        """

        paramDict["SerialBusDevice.address"] = HTU21D.ADDRESS
        if not ("HTU21D.resolution" in paramDict):
            paramDict["HTU21D.resolution"] = HTU21D.CFG_RESOLUTION_DEFAULT
        super().Params_init(paramDict)
        return None


    def open(self, paramDict):
        # Get defaults
        defaults = dict()
        HTU21D.Params_init(defaults)
        # Open the bus device
        paramDict["SerialBusDevice.address"] = defaults["SerialBusDevice.address"]
        ret = SerialBusDevice.open(self, paramDict)
        # Reset sensor
        if (ret == ErrorCode.errOk):
            self.timeStampLatest = 0
            ret = self.reset()
        # Open the sensor, configure rate and range
        if (ret == ErrorCode.errOk):
            ret = Sensor.open( self, paramDict )
        # Configure the sensor
        if ("HTU21D.resolution" in paramDict):
            cfg = Configuration( ConfigItem.resolution, value=paramDict["HTU21D.resolution"])
            ret = self.configure( cfg )
        else:
            paramDict["HTU21D.resolution"] = defaults["HTU21D.resolution"]
        return ret


    def close(self):
        return super().close()
    
    def _heaterOn(self, flag=True):
        data, ret = self.readByteRegister( HTU21D.CMD_READ_USR_REG )
        if (ret == ErrorCode.errOk):
            data = data & ~HTU21D.CNT_USR_CHIP_HEATER
            if flag:
                data = data | HTU21D.CNT_USR_CHIP_HEATER_ON
            else:
                data = data | HTU21D.CNT_USR_CHIP_HEATER_OFF
            ret  = self.writeByteRegister( HTU21D.CMD_WRITE_USR_REG, data )
        return ret
        
    def selfTest(self, tests):
        """Execute one or more sensor self tests.
        
        :attr:`.SelfTest.FUNCTIONAL`: 
        The on-chip heater is used to check if the sensor shows the
        expected temperature raise and humidity drop. The heater consumes
        ~5.5mW and the test takes about 5 seconds.
        
        Also see: :meth:`.Sensor.selfTest`.

        :param int tests: A bit mask to select the tests to be executed.
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if ((tests & SelfTest.FUNCTIONAL) and (ret == ErrorCode.errOk)):
            if (self.timeStampLatest > 0):
                oldTemp = self.latestData.temperature
                oldHum  = self.latestData.humidity
            else:
                oldTemp = self._getTemperature()
                oldHum  = self._getHumidity( oldTemp )
            ret = self._heaterOn(True)
            if (ret == ErrorCode.errOk):
                time.sleep( HTU21D.SELFTEST_TIME_WAIT_S )
                newTemp = self._getTemperature()
                newHum  = self._getHumidity( newTemp )
                ret = self._heaterOn( False )
            if (ret == ErrorCode.errOk):
                if (newTemp >= oldTemp + 0.5) and (newHum <= oldHum - 2):
                    ret = ErrorCode.errOk
                else:
                    ret = ErrorCode.errFailure
        return ret
        
    
    def reset(self):
        """Reboots the sensor.
        
        Power-cycles the chip and restarts it with the default
        configuration. So, any user configuration applied before, will
        be lost.
        
        Also see: :meth:`.Sensor.reset`.
        
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = self.writeBuffer( [HTU21D.CMD_SOFT_RESET] )
        if (ret == ErrorCode.errOk):
            time.sleep( 2*HTU21D.RESET_TIME_MAX_MS / 1000 )
            self.timeStampLatest = 0
            self.latestData = None
            self.resolution = HTU21D.CNT_USR_RESOLUTION_DEFAULT
            ret = Sensor.reset(self)
            self.measInterval = 1 / self.dataRate
        return ret

    @classmethod
    def _getMaxMeasurementTime(cls, resolution):
        if (resolution == HTU21D.CNT_USR_RESOLUTION_RH8_T12):
            maxTime = max( HTU21D.MEAS_TIME_MAX_MS_RH8, HTU21D.MEAS_TIME_MAX_MS_T12 )
        elif (resolution == HTU21D.CNT_USR_RESOLUTION_RH10_T13):
            maxTime = max( HTU21D.MEAS_TIME_MAX_MS_RH10, HTU21D.MEAS_TIME_MAX_MS_T13 )
        elif (resolution == HTU21D.CNT_USR_RESOLUTION_RH11_T11):
            maxTime = max( HTU21D.MEAS_TIME_MAX_MS_RH11, HTU21D.MEAS_TIME_MAX_MS_T11 )
        elif (resolution == HTU21D.CNT_USR_RESOLUTION_RH12_T14):
            maxTime = max( HTU21D.MEAS_TIME_MAX_MS_RH12, HTU21D.MEAS_TIME_MAX_MS_T14 )
        else:
            maxTime = -1000
        maxTime = maxTime / 1000
        return maxTime
        
    def configure(self, configData):
        data, ret = self.readByteRegister( HTU21D.CMD_READ_USR_REG )
        if (ret == ErrorCode.errOk):
            # Resolution
            if (configData.type == ConfigItem.resolution):
                data = data & ~HTU21D.CNT_USR_RESOLUTION
                if( configData.value == HTU21D.CFG_RESOLUTION_HUM8_TEMP12 ):
                    newResolution = HTU21D.CNT_USR_RESOLUTION_RH8_T12
                elif( configData.value == HTU21D.CFG_RESOLUTION_HUM10_TEMP13 ):
                    newResolution = HTU21D.CNT_USR_RESOLUTION_RH10_T13
                elif( configData.value == HTU21D.CFG_RESOLUTION_HUM11_TEMP11 ):
                    newResolution = HTU21D.CNT_USR_RESOLUTION_RH11_T11
                elif( configData.value == HTU21D.CFG_RESOLUTION_HUM12_TEMP14 ):
                    newResolution = HTU21D.CNT_USR_RESOLUTION_RH12_T14
                else:
                    ret = ErrorCode.errSpecRange
                if (ret == ErrorCode.errOk):
                    data = data | newResolution
                    ret  = self.writeByteRegister( HTU21D.CMD_WRITE_USR_REG, data )
                if (ret == ErrorCode.errOk):
                    self.resolution = newResolution
                    maxTime = HTU21D._getMaxMeasurementTimeMS( self.resolution )
                    if( self.measInterval < maxTime ):
                        self.measInterval = maxTime
                        self.dataRate = 1 / self.measInterval
            # Data rate
            elif (configData.type == ConfigItem.rate):
                maxTime = HTU21D._getMaxMeasurementTimeMS( self.resolution )
                if (maxTime <= 0):
                    ret = ErrorCode.errCorruptData
                elif (0 < configData.value) and (configData.value <= 1/maxTime):
                    self.dataRate = configData.value
                    self.measInterval = 1 / self.dataRate
                else:
                    ret = ErrorCode.errSpecRange
            # Anything else
            else:
                ret = ErrorCode.errNotSupported
        return ret


    def getStatus(self, statusID):
        """Retrieve dynamic status info from the sensor.
        
        The resulting status data object depends on the requested info
        as follows:
        
        :attr:`.htu21d.StatusID.powerOk`:
        Reads the power indicator bit (#6, End-of-Battery) and returns
        a boolean True, if the VDD power is above the minimum required,
        or False otherwise.
        
        Also see: :meth:`.Sensor.getStatus`.

        :param int statusID: Identifies the status information to be retrieved.
        :return: The status object and an error code indicating either success or the reason of failure.
        :rtype: Object, ErrorCode
        """
        result = None
        ret = ErrorCode.errOk
        if (statusID == StatusID.powerOk):
            data, ret = self.readByteRegister( HTU21D.CMD_READ_USR_REG )
            if (ret == ErrorCode.errOk):
                result = ((data & HTU21D.CNT_USR_POWER) == HTU21D.CNT_USR_POWER_GOOD)
        else:
            ret = ErrorCode.errNotSupported
        return result, ret
        
    @classmethod    
    def _extractReading( cls, data, isTemperature ):
        err = ErrorCode.errOk
        reading = (data[0] << 8) + (data[1] & 0xFC)
        status = data[1] & 0x03
        # CRC is currently not checked
        #crcValue = data[2]
        if (status==HTU21D.DIAG_CIRC_OPEN):
            if (reading==0):
                # Open circuit
                err = ErrorCode.errUnderrun
            elif not isTemperature:
                err = ErrorCode.errInadequate
        elif (status == HTU21D.DIAG_HUM_OK):
            if isTemperature:
                err = ErrorCode.errInadequate
        elif (status==HTU21D.DIAG_CIRC_SHORT):
            if (reading == 0xFFFC):
                # Short circuit
                err = ErrorCode.errOverflow
        return reading, err


    def _getTemperature( self ):
        temp = 0
        data, err = self.readBufferRegister( HTU21D.CMD_GET_TEMP_HOLD, 3 )
        if (err == ErrorCode.errOk):
            reading, err = HTU21D._extractReading( data, True )
        if (err == ErrorCode.errOk):
            # Transfer function: temp = -46,85 + 175,72*reading/2^16
            temp = reading * 175.72 / 0x10000 - 46.85
        return temp, err

    
    def _getHumidity( self, temp ):
        hum = 0
        data, err = self.readBufferRegister( HTU21D.CMD_GET_HUM_HOLD, 3 )
        if (err == ErrorCode.errOk):
            reading, err = HTU21D._extractReading( data, False )
        if (err == ErrorCode.errOk):
            # RH transfer function: rh = -6 + 125 * reading / 2^16
            hum = reading * 125 / 65536 - 6
            # Now, compensate by temperature
            hum = hum + (temp - 25) * 0.15
        return hum, err

    def _getMeasurement( self ):
        measurement = None
        temp, err = self._getTemperature()
        if (err == ErrorCode.errOk):
            hum, err = self._getHumidity(temp)
            if (err == ErrorCode.errOk):
                measurement = Data()
                measurement.temperature = temp
                measurement.humidity = hum
                # Update latest memory
                self.timeStampLatest = time.time()
                self.latestData = measurement
        return measurement, err
    
    def getLatestData( self ):
        """Retrieves the most recent data.
        
        If the data is older than the measurement interval indicated by
        the configured data rate, a new measurement sample is retrieved
        from the sensor.
        
        Also see: :meth:`.Sensor.getLatestData`.

        :return: The measurement data object and an error code indicating\
        either success or the reason of failure.
        :rtype: Object, ErrorCode
        """
        measurement = None
        err = ErrorCode.errOk
        tNow = time.time()
        if tNow - self.timeStampLatest < self.measInterval:
            measurement = self.latestData
        else:
            measurement, err = self._getMeasurement()
        return measurement, err
    
    def getNextData(self):
        """Wait for the next sample and retrieve that measurement.
        
        If a full measurement interval, as defined by the configured
        data rate, has not yet elapsed, wait until that point. Then,
        retrieve a fresh measurement sample.

        Also see: :meth:`.Sensor.getNextData`.

        :return: The measurement data object and an error code indicating\
        either success or the reason of failure.
        :rtype: Object, ErrorCode
        """
        tNow = time.time()
        tDiff = tNow - self.timeStampLatest
        if (tDiff < self.measInterval):
            time.sleep( self.measInterval - tDiff )
        return self._getMeasurement()

# -*- coding: utf-8 -*-
"""Driver implementation for the BME280 temperature, humidity and pressure sensor.

More information on the functionality of the chip can be found at
the Bosch-Sensortec site:
https://www.bosch-sensortec.com/en/products/environmental-sensors/humidity-sensors-bme280
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["BME280"]

import logging

from .configurable import ConfigItem, Configuration
from .dictionary import Dictionary
from .penum import dataclass
from .primitives import PrecisePercentage, PreciseTemperature, PrecisePressure
from .sensor import SelfTest, Sensor
from .serialbus import SerialBusDevice, SerialBus, SerialBusType
from .systypes import ErrorCode, Info, RunLevel

@dataclass
class Data():
    """Data structure to represent this sensor's measurement result.
    """
    temperature: PreciseTemperature = PreciseTemperature.invalid
    pressure: PrecisePressure       = PrecisePressure.invalid
    humidity: PrecisePercentage     = PrecisePercentage.invalid


class BME280(Sensor, SerialBusDevice):
    """BME280 driver implementation.
    """

    MODULE_PARAM_PREFIX = "weather"

    ADDRESSES_ALLOWED = [0x76, 0x77]
    """Default address is 0x76 assuming that SDO is set/tied to GND.
    
    Alternatively, the address can be 0x77 by pulling SDO high (VDDIO).
    """

#
# BME280 register definitions.
# 1. trimming parameter as given in section 4.2. of the data sheet
#

    REG_CALIB_T1 = 0x88
    REG_CALIB_T2 = 0x8A
    REG_CALIB_T3 = 0x8C
    REG_CALIB_P1 = 0x8E
    REG_CALIB_P2 = 0x90
    REG_CALIB_P3 = 0x92
    REG_CALIB_P4 = 0x94
    REG_CALIB_P5 = 0x96
    REG_CALIB_P6 = 0x98
    REG_CALIB_P7 = 0x9A
    REG_CALIB_P8 = 0x9C
    REG_CALIB_P9 = 0x9E
    REG_CALIB_H1 = 0xA1
    REG_CALIB_H2 = 0xE1
    REG_CALIB_H3 = 0xE3
    REG_CALIB_H4 = 0xE4
    REG_CALIB_H5 = 0xE5
    REG_CALIB_H6 = 0xE7

# 2. Communication registers as given by the global memory map
# in the data sheet, chapter 5.3.

    REG_ID          = 0xD0
    CNT_CHIP_ID     = 0x60

    REG_RESET       = 0xE0
    CNT_DO_SOFT_RESET=0xB6

    REG_CTRL_HUM    = 0xF2
    CNT_OSRS_H_SKIP = 0x00
    CNT_OSRS_H_x1   = 0x01
    CNT_OSRS_H_x2   = 0x02
    CNT_OSRS_H_x4   = 0x03
    CNT_OSRS_H_x8   = 0x04
    CNT_OSRS_H_x16  = 0x05

    REG_STATUS      = 0xF3
    CNT_MEASURING   = 0x08
    CNT_IM_UPDATE   = 0x01
    
    REG_CTRL_MEAS   = 0xF4
    CNT_OSRS_T_SKIP = 0x00
    CNT_OSRS_T_x1   = 0x20
    CNT_OSRS_T_x2   = 0x40
    CNT_OSRS_T_x4   = 0x60
    CNT_OSRS_T_x8   = 0x80
    CNT_OSRS_T_x16  = 0xA0
    CNT_OSRS_P_SKIP = 0x00
    CNT_OSRS_P_x1   = 0x04
    CNT_OSRS_P_x2   = 0x08
    CNT_OSRS_P_x4   = 0x0C
    CNT_OSRS_P_x8   = 0x10
    CNT_OSRS_P_x16  = 0x14
    CNT_MODE_SLEEP  = 0x00
    CNT_MODE_FORCED = 0x01
    CNT_MODE_NORMAL = 0x03

    REG_CONFIG      = 0xF5
    CNT_T_STANDBY_0_5   = 0x00
    CNT_T_STANDBY_62_5  = 0x20
    CNT_T_STANDBY_125   = 0x40
    CNT_T_STANDBY_250   = 0x60
    CNT_T_STANDBY_500   = 0x80
    CNT_T_STANDBY_1000  = 0xA0
    CNT_T_STANDBY_10    = 0xC0
    CNT_T_STANDBY_20    = 0xE0
    CNT_FILTER_OFF  = 0x00
    CNT_FILTER_2    = 0x04
    CNT_FILTER_4    = 0x08
    CNT_FILTER_8    = 0x0C
    CNT_FILTER_16   = 0x10
    CNT_SPI_3W      = 0x01

    REG_PRESS_MSB   = 0xF7
    REG_PRESS_LSB   = 0xF8
    REG_PRESS_XLSB  = 0xF9
    REG_TEMP_MSB    = 0xFA
    REG_TEMP_LSB    = 0xFB
    REG_TEMP_XLSB   = 0xFC
    REG_HUM_MSB     = 0xFD
    REG_HUM_LSB     = 0xFE

#
# Generic mnemonics for the location of data when reading in burst mode
#
    REG_DATA_BURST  = REG_PRESS_MSB
    DATA_BURST_LEN  = 8

    #
    # Internal helpers
    #
 
    def _compensateTemperature( self, adc_T ):
        """Compensate the digital temperature measurement value.
        
        Correction is done by the sensor's individual calibration
        factors/offsets.
        Refer to chapter 4.2 of the data sheet for more details.

        :param int adc_T: 24bit digital register reading
        :returns: The corresponding temperature value in deg. Celsius as a Q8.8 integer.
        :rtype: int
        """
        ret = 0
        var1 = (((adc_T>>3) - (self.dig_T1<<1)) * self.dig_T2) >> 11
        var2 = (((((adc_T>>4) - self.dig_T1) *
                ((adc_T>>4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
    
        self._fineTemperature = var1 + var2
        # For x.2 base 10 format, where 0x0B77 = 2935 stands for 29.35°C:
        # ret = (fineTemperature * 5 + 128) >> 8
        # For Q8.8 binary format, where 0x1D5A (=29#90 = 29 + 90/256)
        # stands for 29.35°C:
        if self._fineTemperature < 0:
            ret = (self._fineTemperature - 10) // 20
        else:
            ret = (self._fineTemperature + 10) // 20
        return ret
    
    def _compensatePressure( self, adc_P ):
        """Compensate the pressure measurement value.
        
        Correction is done by the sensor's individual calibration
        factors/offsets.
        Refer to chapter 4.2 of the data sheet for more details.

        :param int adc_P: 24bit digital register reading
        :returns: The corresponding pressure value in Pascal as a Q24.8 integer.
        :rtype: int
        """
        ret = 0
        # This implementation is a ported version of the algorithm given
        # in the data sheet. It relies on 64 bit wide integers.
        # If the target platform provides only 32 bit integers, look at
        # the appendix 8.2 for a 32 bit version. However, that
        # variant will produce a Q32.0 result, instead!
        var1 = self._fineTemperature - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1*self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + \
               ((var1 * self.dig_P2) << 12)
        var1 = (((1 << 47) + var1)) * self.dig_P1 >> 33
        if var1 == 0:
            ret = 0     # avoid exception caused by division by zero
        else:
            p = 1048576 - adc_P
            p = (((p << 31) - var2) * 3125) // var1
            var1 = (self.dig_P9 * (p >> 13) * (p>>13)) >> 25
            var2 = (self.dig_P8 * p) >> 19
            p = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)
            ret = p
        return ret
    
    def _compensateHumidity( self, adc_H ):
        """Compensate the humidity measurement value as read from ADC.
        
        Correction is done by the sensor's individual calibration
        factors/offsets.
        Refer to chapter 4.2 of the data sheet for more details.

        :param int adc_H: 24bit digital register reading
        :returns: The corresponding humidity value in Percent [%RH] as a Q22(7).10 integer.
        :rtype: int
        """
        ret = self._fineTemperature - 76800
        ret = (((((adc_H << 14) - (self.dig_H4 << 20) -
                (self.dig_H5 * ret)) + 16384) >> 15) *
                (((((((ret * self.dig_H6) >> 10) * (((ret *
                self.dig_H3) >> 11) + 32768)) >> 10) + 2097152) *
                self.dig_H2 + 8192) >> 14))
        ret = (ret - (((((ret >> 15) * (ret >> 15)) >> 7) *
                self.dig_H1) >> 4))
        ret = 0 if ret < 0 else ret                 # Cut-off negatives
        ret = 419430400 if ret > 419430400 else ret # Limit to 100%
        ret = ret >> 12
        # The original algorithm ends here, returning a Q22.10 integer,
        # which in fact is a Q7.10 (because it's limited to 100%).
        # However, for consistency, we decide for the Q8.8 format also
        # used for the temperature. So we need two more shifts:
        ret = ret >> 2
        return ret

    def _readCalibration( self ):
        """Read the compensation coefficients from the chip.
        
        As a side effect, update the dig_* instance attributes.
        """
        ret = ErrorCode.errOk
        
        # Put in sleep mode to safely read the NVM registers
        self.writeByteRegister( BME280.REG_CTRL_MEAS,
                                BME280.CNT_OSRS_T_SKIP |
                                BME280.CNT_OSRS_P_SKIP |
                                BME280.CNT_MODE_SLEEP )
    
        # Wait for copying NVM data after startup / measurement is done
        status = BME280.CNT_IM_UPDATE
        while (status & BME280.CNT_IM_UPDATE) and ret.isOk():
            status, ret = self.readByteRegister( BME280.REG_STATUS )
    
        # T1...T3 + P1...P9
        if ret.isOk():
            buf, ret = self.readBufferRegister( BME280.REG_CALIB_T1, 24 )
        if ret.isOk():
            self.dig_T1 = (buf[1] << 8) | buf[0]
            raw = (buf[3] << 8) | buf[2]
            self.dig_T2 = (raw & 0x7FFF) - (raw & 0x8000) # sign-extend
            raw = (buf[5] << 8) | buf[4]
            self.dig_T3 = (raw & 0x7FFF) - (raw & 0x8000) # sign-extend
            self.dig_P1 = (buf[7] << 8) | buf[7]
            raw = (buf[9] << 8) | buf[8]
            self.dig_P2 = (raw & 0x7FFF) - (raw & 0x8000) # sign-extend
            raw = (buf[11] << 8) | buf[10]
            self.dig_P3 = (raw & 0x7FFF) - (raw & 0x8000) # sign-extend
            raw = (buf[13] << 8) | buf[12]
            self.dig_P4 = (raw & 0x7FFF) - (raw & 0x8000) # sign-extend
            raw = (buf[15] << 8) | buf[14]
            self.dig_P5 = (raw & 0x7FFF) - (raw & 0x8000) # sign-extend
            raw = (buf[17] << 8) | buf[16]
            self.dig_P6 = (raw & 0x7FFF) - (raw & 0x8000) # sign-extend
            raw = (buf[19] << 8) | buf[18]
            self.dig_P7 = (raw & 0x7FFF) - (raw & 0x8000) # sign-extend
            raw = (buf[21] << 8) | buf[20]
            self.dig_P8 = (raw & 0x7FFF) - (raw & 0x8000) # sign-extend
            raw = (buf[23] << 8) | buf[22]
            self.dig_P9 = (raw & 0x7FFF) - (raw & 0x8000) # sign-extend
        
        # H1
        if ret.isOk():
            self.dig_H1, ret = self.readByteRegister( BME280.REG_CALIB_H1 )
        # H2...H7
        if ret.isOk():
            buf, ret = self.readBufferRegister( BME280.REG_CALIB_H2, 7 )
        if ret.isOk():
            raw = (buf[1] << 8) | buf[0]
            self.dig_H2 = (raw & 0x7FFF) - (raw & 0x8000) # sign-extend
            self.dig_H3 = buf[2]
            raw = (buf[3] << 4) | (buf[4] & 0x0F)
            self.dig_H4 = (raw & 0x07FF) - (raw & 0x0800) # sign-extend
            raw = (buf[5] << 4) | ((buf[4] & 0xF0) >> 4)
            self.dig_H5 = (raw & 0x07FF) - (raw & 0x0800) # sign-extend
            self.dig_H6 = (buf[6] & 0x7F) - (buf[6] & 0x80) # sign-extend
    
        # Now that the parameters were read, return to normal operation.
        if ret.isOk():
            ret = self.writeByteRegister( BME280.REG_CTRL_MEAS,
                                          self.shadowCtrlMeas )
        return ret
    
    def __init__( self ):
        # Create instance attributes
        self.shadowCtrlMeas = 0     # copy of REG_CTRL_MEAS
        self.shadowSPI3w    = False # copy of REG_CONFIG:SPI3W
        # Compensation parameters
        self.dig_T1 = 0     # 0x89:88    unsigned short
        self.dig_T2 = 0     # 0x8B:8A    signed short
        self.dig_T3 = 0     # 0x8D:8C    signed short
        self.dig_P1 = 0     # 0x8F:8E    unsigned short
        self.dig_P2 = 0     # 0x91:90    signed short
        self.dig_P3 = 0     # 0x93:92    signed short
        self.dig_P4 = 0     # 0x95:94    signed short
        self.dig_P5 = 0     # 0x97:96    signed short
        self.dig_P6 = 0     # 0x99:98    signed short
        self.dig_P7 = 0     # 0x9B:9A    signed short
        self.dig_P8 = 0     # 0x9D:9C    signed short
        self.dig_P9 = 0     # 0x9F:9E    signed short
        self.dig_H1 = 0     # 0xA1       unsigned char
        self.dig_H2 = 0     # 0xE2:E1    signed short
        self.dig_H3 = 0     # 0xE3       unsigned char
        self.dig_H4 = 0     # 0xE4:E5[3:0] 12 bit signed short
        self.dig_H5 = 0     # 0xE6:E5[7:4] 12 bit signed short
        self.dig_H6 = 0     # 0xE7       signed char
        self._fineTemperature=0x1F400   # 25 degC, Needed for compensation
        Sensor.__init__(self)
        SerialBusDevice.__init__(self)

    #
    # Module API
    #
 
    @classmethod
    def Params_init( cls, paramDict ):
        """Initializes parameters to their default values.
        The following settings are supported:
        
        =====================================    ==================================================================================================================
        Key name                                 Value type, meaning and default
        =====================================    ==================================================================================================================
        weather.SerialBusDevice.address          ``int`` I2C serial device address, one of :attr:`ADDRESSES_ALLOWED`; default is :attr:`ADDRESSES_ALLOWED` ``[0]``.
        weather.SerialBus.SPI.wires              [3 | 4] Three-wire SPI (joint SDIO pin) or standard four-wire SPI (separate MOSI and MISO pins)
        weather.SerialBus.*                      optional: serial bus configuration; See :meth:`serialbus.SerialBus.Params_init`.
        weather.SerialBusDevice.*                serial bus configuration; See :meth:`serialbus.SerialBusDevice.Params_init`.
        weather.Sensor.temp.sampling             temperature sampling: [0, 1, 2, 4, 8, 16]; 0=None, 1=single shot, 2 and above = oversampling
        weather.Sensor.press.sampling            pressure sampling: [0, 1, 2, 4, 8, 16]
        weather.Sensor.hum.sampling              humidity sampling: [0, 1, 2, 4, 8, 16]
        weather.Sensor.measurement.standby       milliseconds of inactivity in a measurement cycle: [0, 1, 10, 20, 63, 125, 250, 500, 1000]; 0=cycling off
        weather.Sensor.measurement.filter        low pass filter coefficient to apply: Sensor.FILTER_[NONE | WEAK | MILD | INTENSE | STRONG]
        ===========================================================================================================================================================
        
        For the ``SerialBusDevice.address`` value, also 0 or 1
        can be specified alternatively to the absolute addresses to reflect
        the level of the ``SDO`` pin. In this case, 0 will be mapped to
        0x76, while 1 maps to 0x77.
        
        Also see: :meth:`.SerialBusDevice.Params_init`. 
        
        :param dict(str, object) paramDict: Dictionary mapping option\
        names to their respective values.
        :returns: none
        :rtype: None
        """
        prefix = cls.MODULE_PARAM_PREFIX + "."

        # Setup defaults
        defaults = {
            "SerialBusDevice.address": cls.ADDRESSES_ALLOWED[0],
            #"SerialBus.SPI.wires": 4,
            "Sensor.temp.sampling": 2,
            "Sensor.press.sampling": 2,
            "Sensor.hum.sampling": 2,
            "Sensor.measurement.standby": 125,
            "Sensor.measurement.filter": Sensor.FILTER_NONE,
        }
        # Add defaults to paramDict
        cls._aggregateParams( paramDict, defaults, prefix )
        
        localParams = cls._extractParams( paramDict, prefix)
        SerialBus.Params_init(localParams)
        SerialBusDevice.Params_init(localParams)
        Sensor.Params_init(localParams)
        cls._aggregateParams( paramDict, localParams, prefix )

        return None


    def open(self, paramDict):
        ret = ErrorCode.errOk
        self.Params_init(paramDict)
        localParams = self._extractParams( paramDict, self.MODULE_PARAM_PREFIX + ".")
        logging.debug("BME280.open> Params: %s.", localParams)
        # Open serial connection
        if ret.isOk():
            ret = SerialBusDevice.open(self, localParams)
            logging.debug("BME280.open> SerialBusDevice.open: %s.", ret)
        # Configure correct SPI wiring, before writing anything
        if ret.isOk() and (self.serialBus.type == SerialBusType.SPI):
            self.shadowSPI3w = (localParams.get( "SerialBus.SPI.wires", 4) == 3)
            if self.shadowSPI3w:
                ret = self.writeByteRegister( BME280.REG_CONFIG,
                                              BME280.CNT_SPI_3W )
            logging.debug("BME280.open> write SPI_3W: %s.", ret)
        if ret.isOk():
            ret = self.selfTest( SelfTest.CONNECTION )
            logging.debug("BME280.open> selfTest: %s.", ret)
        # Read shadow register
        if ret.isOk():
            self.shadowCtrlMeas, ret = self.readByteRegister(BME280.REG_CTRL_MEAS)
            logging.debug("BME280.open> read CTRL_MEAS: %s.", ret)
        # Read calibration data
        if ret.isOk():
            ret = self._readCalibration()
            logging.debug("BME280.open> readCalibration: %s.", ret)
        # Configure
        if ret.isOk():
            cfg = Configuration( item=ConfigItem.multisetting,
                                 setting=paramDict )
            ret = self.configure(cfg)
            logging.debug("BME280.open> configure: %s.", ret)
      
        return ret


    def close(self):
        ret = self.setRunLevel( RunLevel.shutdown )
        err = super().close()
        if ret.isOk():
            ret = err
        return ret


    def setRunLevel(self, level):
        ret = self.isAttached()
        if ret.isOk():
            data = (self.shadowCtrlMeas & 0xFC) # Wipe-out mode bits
            if level == RunLevel.active:
                data |= BME280.CNT_MODE_NORMAL
            elif level in [RunLevel.idle, RunLevel.relax,
                           RunLevel.snooze, RunLevel.nap]:
                data |= BME280.CNT_MODE_FORCED
            else:
                data |= BME280.CNT_MODE_SLEEP
            ret = self.writeByteRegister( BME280.REG_CTRL_MEAS, data )
        if ret.isOk():
            self.shadowCtrlMeas = data
        return ret

    #
    # Sensor API
    #
    
    def selfTest(self, tests):
        ret = ErrorCode.errOk
        if tests & SelfTest.CONNECTION:
            data, ret = self.readByteRegister( BME280.REG_ID )
            if ret.isOk() and (data != BME280.CNT_CHIP_ID):
                ret = ErrorCode.errFailure
        return ret


    def reset(self):
        # Do a software reset
        ret =self.writeByteRegister( BME280.REG_RESET, BME280.CNT_DO_SOFT_RESET )
        self.shadowCtrlMeas = 0
        # Configure correct SPI wiring, before writing anything
        if self.serialBus.type == SerialBusType.SPI:
            if ret.isOk() and self.shadowSPI3w:
                ret = self.writeByteRegister( BME280.REG_CONFIG,
                                              BME280.CNT_SPI_3W )
        return ret


    def configure(self, cfg):
        """Configures the sensor device as described by the given configuration data.
        
        Note the ``cfg`` data is a multi-compound data class. Its ``item``
        attribute must be set to ``multisetting``. The configuration
        data is passed as a string-to-value dictionary in the
        ``cfg.setting`` attribute. This is pretty much like the initial
        parameters are passed to :meth:`open`.
        
        The following settings (keys) are supported:
        
        =====================================    ==========================================================================================================
        Key name                                 Value type, meaning and default
        =====================================    ==========================================================================================================
        weather.Sensor.temp.sampling             temperature sampling: [0, 1, 2, 4, 8, 16]; 0=None, 1=single shot, 2 and above = oversampling
        weather.Sensor.press.sampling            pressure sampling: [0, 1, 2, 4, 8, 16]
        weather.Sensor.hum.sampling              humidity sampling: [0, 1, 2, 4, 8, 16]
        weather.Sensor.measurement.standby       milliseconds of inactivity in a measurement cycle: [0, 1, 10, 20, 63, 125, 250, 500, 1000]; 0=cycling off
        weather.Sensor.measurement.filter        low pass filter coefficient to apply: Sensor.FILTER_[NONE | WEAK | MILD | INTENSE | STRONG]
        ===================================================================================================================================================
        
        Also see: :meth:`Params_init`, :class:`.configurable.Configuration`.        
        
        :param Configuration cfg: Configuration data. 
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        if (not cfg) or (cfg.item != ConfigItem.multisetting) or \
            (not cfg.setting) or (not isinstance(cfg.setting, dict)):
            logging.debug("BME280.configure> cfg.item=%s, cfg.setting=%s.", cfg.item, cfg.setting)
            return ErrorCode.errInvalidParameter
        
        osrDict  = Dictionary( {0:0, 1:1, 2:2, 3:4, 4:8, 5:16} )
        stbyDict = Dictionary( {-1:0, 0:1, 1:63, 2:125, 3:250, 4:500, 5:1000,
                               6:10, 7:20} )
        prefix = self.MODULE_PARAM_PREFIX + "." + "Sensor" + "."
        
        # Put in sleep mode to safely write the config register
        ret = self.writeByteRegister( BME280.REG_CTRL_MEAS,
                                      BME280.CNT_OSRS_P_SKIP |
                                      BME280.CNT_OSRS_T_SKIP |
                                      BME280.CNT_MODE_SLEEP )
        logging.debug("BME280.configure> write CTRL_MEAS to sleep: %s.", ret)
        mustWriteCtrlMeas = False
        
        # Anything for the CTRL_HUM register?
        value = cfg.setting.get(prefix+"hum.sampling", None)
        if ret.isOk() and (value is not None):
            data, _ = osrDict.findKey(value)
            ret = self.writeByteRegister( BME280.REG_CTRL_HUM, data )
            mustWriteCtrlMeas = True
            logging.debug("BME280.configure> write CTRL_HUM: %s, value=%s, data=%s", ret, value, data)
        # Anything for CONFIG ?
        dataMode = None
        valueStby = cfg.setting.get(prefix+"measurement.standby", None)
        valueFlt = cfg.setting.get(prefix+"measurement.filter", None)
        if ret.isOk() and ((valueStby is not None) or (valueFlt is not None)):
            data, ret = self.readByteRegister( BME280.REG_CONFIG )
            if ret.isOk():
                data = (data & 0xFE) | (1 if self.shadowSPI3w else 0)
                if valueFlt is not None:
                    data = (data & 0xE3) | ((valueFlt & 0x07) << 2)
                if valueStby is not None:
                    key, _ = stbyDict.findKey(valueStby)
                    if key < 0:
                        dataMode = BME280.CNT_MODE_FORCED
                    else:
                        data = (data & 0x1F) | (key << 5)
                        dataMode = BME280.CNT_MODE_NORMAL  
                ret = self.writeByteRegister( BME280.REG_CONFIG, data )
            logging.debug("BME280.configure> read/write CONFIG: %s.", ret)
        # Now, treat CTRL_MEAS right
        valueT = cfg.setting.get(prefix+"temp.sampling", None)
        valueP = cfg.setting.get(prefix+"press.sampling", None)
        if dataMode is not None:
            dataMode = dataMode if (self.shadowCtrlMeas & 0xFC) != dataMode else None
        if ret.isOk() and ((valueT is not None) or \
                           (valueP is not None) or \
                           mustWriteCtrlMeas or \
                           (dataMode is not None)):
            data = self.shadowCtrlMeas
            if valueT is not None:
                bits, _ = osrDict.findKey(valueT)
                data = (data & 0x1F) | (bits << 5)  
            if valueP is not None:
                bits, _ = osrDict.findKey(valueP)
                data = (data & 0xE3) | (bits << 2)
            if dataMode is not None:
                data = (data & 0xFC) | dataMode
            ret = self.writeByteRegister( BME280.REG_CTRL_MEAS, data )
            if ret.isOk():
                self.shadowCtrlMeas = data
            logging.debug("BME280.configure> write CTRL_MEAS: %s.", ret)
        return ret


    def getInfo(self):
        info = Info()
        chipID, ret = self.readByteRegister( BME280.REG_ID )
        if ret.isOk():
            info.validity = Info.validChipID
            info.chipID = chipID

        return info, ret


    def getStatus(self, statusID):
        del statusID
        status, ret = self.readByteRegister( BME280.REG_STATUS )
        return status, ret


    def getLatestData(self):
        data = Data()
        # Read out raw data
        buf, ret = self.readBufferRegister( BME280. REG_DATA_BURST,
                                            BME280.DATA_BURST_LEN )
    
        # Separate and compensate individual measurement data
        if ret.isOk():
            # Temperature first: buf[3...5]
            rawValue = (buf[3] << 12) | (buf[4] << 4) | (buf[5] >> 4)
            if rawValue == 0x080000:
                data.pressure = PreciseTemperature.invalid
            else:
                data.temperature = self._compensateTemperature( rawValue )
    
            # Pressure, buf[0...2]
            rawValue = (buf[0] << 12) | (buf[1] << 4) | (buf[2] >> 4)
            if rawValue == 0x080000:
                data.pressure = PrecisePressure.invalid
            else:
                data.pressure = self._compensatePressure( rawValue )
    
            # Humidity, buf[6...7]
            rawValue = (buf[6] << 8) | buf[7]
            if rawValue == 0x8000:
                data.pressure = PrecisePercentage.invalid
            else:
                data.humidity = self._compensateHumidity( rawValue )
        return data, ret
    

    def getNextData(self):
        data = None
        ret = ErrorCode.errOk
        runMode = self.shadowCtrlMeas & 0x03
        if runMode == BME280.CNT_MODE_SLEEP:
            ret = ErrorCode.errInadequate
        else:
            if runMode == BME280.CNT_MODE_FORCED:
                ret = self.writeByteRegister( BME280.REG_CTRL_MEAS,
                                              self.shadowCtrlMeas )
            # Wait for the measuring flag being cleared
            status = BME280.CNT_MEASURING
            while ret.isOk() and (status & BME280.CNT_MEASURING):
                status, ret = self.readByteRegister( BME280.REG_STATUS )
    
            if ret.isOk():
                data, ret = self.getLatestData()
        return data, ret

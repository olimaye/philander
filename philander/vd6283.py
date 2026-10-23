"""Driver implementation for the VD6283 and similar ambient light sensors by ST micro.

More information on the functionality of the chip can be found at
the ST site:
https://www.st.com/en/imaging-and-photonics-solutions/VD6283.html

This sensor is a matrix of 5x5 photo diodes providing six different
light channels as follows:
- Red. 3 diodes, 550...700nm, peak 610nm
- Green. 5 diodes, 420...650nm, peak 550nm
- Blue. 3 diodes, 380...550nm, peak 460nm
- IR. 4 diodes, 600...1000nm, peak 850 nm
- Visible. 3 diodes, 370...700nm, peak 540nm
- Clear. 5 diodes, 350...1050nm, peak 550-680nm
- Dark. 2 blind diodes, only internal channel.

Undocumented details on the mode of operation:
- Endiannes for multi-byte registers, such as ALS_CHx_DATA or ALS_EXPOSURE,
  is BIG endian! So the high-byte is at the lower address, gets read first.
- Continous and handshake mode run in parallel, more or less.
- The interrupt flag INTR_ST is low-active.
- Clearing INTR_ST is achieved by cycling CRL_INTR through a 1-0 sequence.
  So, INTERRUPT_CTRL needs to be written twice.
- Clearing INTR_ST starts a new measurement.
- Not verified: EXPOSURE+6ms after clearing INTR_ST the ALS_CHx_DATA have
  fresh data ready to be read.
- After EXPOSURE+IM_PERIOD the interrupt is raised (INTR_ST=0).
- ALS_CHx_DATA registers are never locked. They may change with fresh data.
- If interrupt is not cleared, another measurement starts automatically ("continously")
- After another EXPOSURE+IM_PERIOD, the next measurement is available
- but interrupt is still active.

So, without using  the interrupt flag, it's purely the application's
responsibility to stay in sync with the sensor's continous mode. There
is no way to know, whether the same data was picked up before, or whether
data is fresh.
When using the interrupt flag, the flag indicates that data was updated
since last clearance. However, if the application waits for too long,
data was possibly updated a multiple times.

There is no way of reading calibration factors.
Exposure time and gain factor work mainly proportional on the data value,
except when approaching saturation.
"""
__author__ = "Oliver Maye"
__version__ = "0.1"
__all__ = ["VD6283"]

import logging
from time import sleep

from .configurable import ConfigItem, Configuration
from .dictionary import Dictionary
from .gpio import GPIO
from .imath import bswap16
from .penum import dataclass
from .sensor import SelfTest, Sensor
from .serialbus import SerialBusDevice, SerialBus, SerialBusType
from .systypes import ErrorCode, Info, RunLevel

class VD6283(Sensor, SerialBusDevice):
    """VD6283 driver implementation.
    """

    MODULE_PARAM_PREFIX = "light"

    ADDRESSES_ALLOWED = [0x20]
    """The only address is 0x20.
    """
    
    #
    # Hardware register definitions.
    #
    REG_DEVICE_ID       = 0x00
    DEVICE_ID           = 0x70
    
    REG_REVISION_ID     = 0x01
    REVISION_ID_2_2     = 0xBC
    REVISION_ID_2_3     = 0xBD

    REG_INTERRUPT_CTRL  = 0x02
    INTR_ST             = 0x02
    CLR_INTR            = 0x01
    
    REG_ALS_CTRL        = 0x03
    ALS_MODE_SINGLE     = 0x00
    ALS_MODE_CONT       = 0x06
    ALS_EN              = 0x01
    
    REG_ALS_PERIOD      = 0x04  # Periods of 20.5 ms (=LSB)

    REG_ALS_CHX_DATA    = 0x06
    # REG_ALS_CH1_DATA_H  = 0x06
    # REG_ALS_CH1_DATA_M  = 0x07
    # REG_ALS_CH1_DATA_L  = 0x08
    # REG_ALS_CH2_DATA_H  = 0x0A
    # REG_ALS_CH2_DATA_M  = 0x0B
    # REG_ALS_CH2_DATA_L  = 0x0C
    # REG_ALS_CH3_DATA_H  = 0x0E
    # REG_ALS_CH3_DATA_M  = 0x0F
    # REG_ALS_CH3_DATA_L  = 0x10
    # REG_ALS_CH4_DATA_H  = 0x12
    # REG_ALS_CH4_DATA_M  = 0x13
    # REG_ALS_CH4_DATA_L  = 0x14
    # REG_ALS_CH5_DATA_H  = 0x16
    # REG_ALS_CH5_DATA_M  = 0x17
    # REG_ALS_CH5_DATA_L  = 0x18
    # REG_ALS_CH6_DATA_H  = 0x1A
    # REG_ALS_CH6_DATA_M  = 0x1B
    # REG_ALS_CH6_DATA_L  = 0x1C
    
    REG_ALS_EXPOSURE    = 0x1D
    # REG_ALS_EXPOSURE_M  = 0x1D
    # REG_ALS_EXPOSURE_L  = 0x1E
    # EXPOSURE_DEFAULT    = 0x0032    # Intervals of 1.6 ms 
    
    REG_ALS_GAIN_CHX    = 0x25
    ALS_GAIN            = 0x0F
    # REG_ALS_GAIN_CH1    = 0x25
    # REG_ALS_GAIN_CH2    = 0x26
    # REG_ALS_GAIN_CH3    = 0x27
    # REG_ALS_GAIN_CH4    = 0x28
    # REG_ALS_GAIN_CH5    = 0x29
    # REG_ALS_GAIN_CH6    = 0x2A
    # ALS_GAIN_66p6   = 0x01
    # ALS_GAIN_50     = 0x02
    # ALS_GAIN_33     = 0x03
    # ALS_GAIN_25     = 0x04
    # ALS_GAIN_16     = 0x05
    # ALS_GAIN_10     = 0x06
    # ALS_GAIN_7p1    = 0x07
    # ALS_GAIN_5      = 0x08
    # ALS_GAIN_3p33   = 0x09
    # ALS_GAIN_2p5    = 0x0A
    # ALS_GAIN_1p67   = 0x0B
    # ALS_GAIN_1p25   = 0x0C
    # ALS_GAIN_1      = 0x0D
    # ALS_GAIN_0p83   = 0x0E
    # ALS_GAIN_0p71   = 0x0F
    
    REG_CHANNEL6_ENABLE = 0x2D
    CH6_EN          = 0x01

    REG_ALS_CHANNEL_ENABLE = 0x2E
    ALS_CH_EN_NONE  = 0x00
    ALS_CH_EN_1     = 0x01
    ALS_CH_EN_2     = 0x02
    ALS_CH_EN_3     = 0x04
    ALS_CH_EN_4     = 0x08
    ALS_CH_EN_5     = 0x10
    ALS_CH_EN_ALL   = 0x1F

    REG_AC_MODE_CTRL    = 0x31
    PEDESTAL_DIS    = 0x40
    PDM_CLK_SEL     = 0x20
    AC_OUT_SEL      = 0x10
    AC_CH_SEL_NONE  = 0x00
    AC_CH_SEL_1     = 0x04
    AC_CH_SEL_2     = 0x06
    AC_CH_SEL_3     = 0x08
    AC_CH_SEL_4     = 0x0A
    AC_CH_SEL_5     = 0x0C
    AC_CH_SEL_6     = 0x02
    AC_FREQEXT_EN   = 0x01
    AC_CH_SEL       = 0x0E

    REG_PEDESTAL_VALUE  = 0x32
    PDST_VAL        = 0x07
    PEDESTAL_DEFAULT= 0x05
    
    REG_SDA_DRV_CFG     = 0x3C
    SDA_LOAD        = 0x08
    SDA_DRV         = 0x07
    SDA_DRV_LOWEST  = 0x00
    SDA_DRV_DEFAULT = 0x01
    SDA_DRV_HIGHEST = 0x04
    
    REG_GPIO1_DRV_CFG   = 0x41
    GPIO1_CFG_OD    = 0x00  # Open drain
    GPIO1_CFG_PUSH_PULL = 0x01  # Push-pull
    GPIO1_CFG_ANALOGUE  = 0x02  # Analog output via 200 Ohm series resistor
    GPIO1_CFG_DEFAULT   = 0x00

    CHANNEL_NUM         = 6
    CHANNEL_NONE        = 0
    CHANNEL_IDX_1_RED   = 1
    CHANNEL_IDX_2_VISIBLE   = 2
    CHANNEL_IDX_3_BLUE  = 3
    CHANNEL_IDX_4_GREEN = 4
    CHANNEL_IDX_5_IR    = 5
    CHANNEL_IDX_6_CLEAR = 6
    
    @dataclass
    class ChannelCharacteristic():
        """Data structure to represent fix channel data (characteristic).
        """
        name:			str
        # Scaling factor for mapping into intensity [uW/cm^2]
        # Holds for exposure=50ms and at 25 deg. C.
        # Stored in 1/10 Counts / uW/cm^2
        # so, e.g. 62.3 is stored as 623.
        # Refer to chap. 8.2. for more details on the sensitivity.
        sensitivity:    int     # in 1/10

    @dataclass
    class ChannelConfig():
        """Data structure to represent variable channel data (configuration).
        """
        index:          int
        maskAlsEnable:  int
        maskAcModeCtrl: int
        isEnabled:      bool = False
        hasFlicker:     bool = False
        gain:			int = 24    # Gain factor stored in 1/24.

    CHANNEL = {
        CHANNEL_IDX_1_RED:		ChannelCharacteristic(name="red", sensitivity=146),
        CHANNEL_IDX_2_VISIBLE:	ChannelCharacteristic(name="visible", sensitivity=497),
        CHANNEL_IDX_3_BLUE:		ChannelCharacteristic(name="blue", sensitivity=146),
        CHANNEL_IDX_4_GREEN:	ChannelCharacteristic(name="green", sensitivity=295),
        CHANNEL_IDX_5_IR:		ChannelCharacteristic(name="ir", sensitivity=860),
        CHANNEL_IDX_6_CLEAR:	ChannelCharacteristic(name="clear", sensitivity=623),
        }
    
    # Map register REG_ALS_GAIN_CHX content to gain factors as stored internally in 1/24.
    GAIN_DICT  = Dictionary( {
                    15: 17,     # 0.71
                    14: 20,     # 0.83
                    13: 24,     # 1 
                    12: 30,     # 1.25
                    11: 40,     # 1.67
                    10: 60,     # 2.5
                    9:  80,     # 3.33
                    8:  120,    # 5
                    7:  170,    # 7.1
                    6:  240,    # 10
                    5:  400,    # 16
                    4:  600,    # 25
                    3:  800,    # 33
                    2:  1200,   # 50
                    1:  1600,   # 66.6
        } )
    

    #
    # Internal helpers
    #
    
    def _syncShadows(self):
        """Synchronize shadow registers.

        Instance variables are used as local copies of frequently-used registers.
        This method synchronizes the variables with the true register content by
        reading in the registers and overwriting the instance attributes with
        their content.
        
        :returns: An error code to indicate success or the reason of failure.
        :rtype: ErrorCode
        """
        data, ret = self.readByteRegister(VD6283.REG_ALS_CTRL)
        logging.debug("VD6283._syncShadows> read REG_ALS_CTRL: data=x%02x, err=%s.", data, ret)
        if ret.isOk():
            self._shadowAlsCtrl = data
            data, ret = self.readByteRegister(VD6283.REG_ALS_PERIOD)
            logging.debug("VD6283._syncShadows> read REG_ALS_PERIOD: data=x%02x, err=%s.", data, ret)
        if ret.isOk():
            self._shadowAlsPeriod = (data * 41) // 2	# LSB = 20.5ms
            data, ret = self.readByteRegister(VD6283.REG_ALS_EXPOSURE)
            data = bswap16( data )  # swap endianess
            logging.debug("VD6283._syncShadows> read REG_ALS_EXPOSURE: data=x%02x, err=%s.", data, ret)
        if ret.isOk():
            # exposure time = (data + 1) * 16384 / (10.24 MHz)
            # 	= (data + 1) * 2^14 * 100 / (2^10 * 10^6 * 1/s)
            #	= (data + 1) * 2^4 / 10^4 * s = (data + 1) * 16 / 10 ms
            #   = (data + 1) * 8 / 5 ms. Stored in 1/5 of ms.
            self._shadowAlsExposure = (data+1) * 8
            ch6Ena, ret = self.readByteRegister(VD6283.REG_CHANNEL6_ENABLE)
            logging.debug("VD6283._syncShadows> read REG_CHANNEL6_ENABLE: data=x%02x, err=%s.", ch6Ena, ret)
        if ret.isOk():
            chEna, ret = self.readByteRegister(VD6283.REG_ALS_CHANNEL_ENABLE)
            logging.debug("VD6283._syncShadows> read REG_ALS_CHANNEL_ENABLE: data=x%02x, err=%s.", chEna, ret)
        if ret.isOk():
            acModeCtrl, ret = self.readByteRegister(VD6283.REG_AC_MODE_CTRL)
            logging.debug("VD6283._syncShadows> read REG_AC_MODE_CTRL: data=x%02x, err=%s.", acModeCtrl, ret)
        if ret.isOk():
            for ch in self._channel:
                if ch.index == VD6283.CHANNEL_IDX_6_CLEAR:
                    ch.isEnabled = ch.maskAlsEnable & ch6Ena
                else:        
                    ch.isEnabled = ch.maskAlsEnable & chEna
                ch.hasFlicker = ((acModeCtrl & VD6283.AC_CH_SEL) == ch.maskAcModeCtrl)
                data, ret = self.readByteRegister(VD6283.REG_ALS_GAIN_CHX + ch.index - 1)
                logging.debug("VD6283._syncShadows> read REG_ALS_GAIN_CH%d: data=x%02x, err=%s.", 
                              (ch.index-1), data, ret)
                if ret.isOk():
                    ch.gain = VD6283.GAIN_DICT.getValue(data & VD6283.ALS_GAIN)
        return ret
    
    def _setGain(self, channel, value):
        """Set channel gain.
        Expect value in external format, as a plain factor, possibly float!

        :returns: An error code to indicate success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        data = None
        if (value is not None) and isinstance(value, (int, float)):
            value = value * 24
            if isinstance( value, float ):
                value = round(value)
            data, ret = VD6283.GAIN_DICT.findKey( value )
            if ret.isOk():
                register = VD6283.REG_ALS_GAIN_CHX + channel.index - 1
                ret = self.writeByteRegister( register, data )
            if ret.isOk():
                channel.gain, ret = VD6283.GAIN_DICT.getValue(data)
        logging.debug("VD6283._setGain> channel #%d: value=%s, data=%s, gain=%d, ret=%s",
                      channel.index, value, data, channel.gain, ret)
        return ret
    
    def _transferToIntensity( self, adcCounts, channel ):
        """Translate digital measurement value into intensity.
        
        :param int adcCounts: 24bit digital register reading
        :param Channel channel: The channel for which to compute the intensity. 
        :returns: The corresponding intensity value in uW/cm^2 as int \
        and an error code to indicate success or the reason of failure.
        :rtype: int, ErrorCode
        """
        err = ErrorCode.errOk
        logging.debug("VD6283._transferToIntensity> adc: %s, channel #%d.", adcCounts, channel.index)
        if channel is None:
            ret = 0
            err = ErrorCode.errInvalidParameter
        else:
            # Apply channel gain, sensitivity and exposure time, where
            # sensitivity reference is given for EXTIME=50ms.
            # Gain correction:    * 24 / channel.gain
            # sensitivity:        * 10 / VD6283.CHANNEL[channel.index].sensitivity
            # exposure time:      * 248 / self._shadowAlsExposure; 248 = 49.6ms * 5 ~ 50ms*5
            # So overall:        *24*10*248 / (...gain*...sensitivity*...exposure)
            ret = adcCounts * 59520 // (channel.gain * VD6283.CHANNEL[channel.index].sensitivity * self._shadowAlsExposure)
            logging.debug("VD6283._transferToIntensity> apply gain, sensitivity, exposure: ret=%s", ret)
            err = ErrorCode.errOk
        return ret, err
    
    def _clearInt(self):
        """Clears the interrupt flag INTR_ST.

        :returns: An error code to indicate success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = self.writeByteRegister( VD6283.REG_INTERRUPT_CTRL, VD6283.CLR_INTR )
        if ret.isOk():
            ret = self.writeByteRegister( VD6283.REG_INTERRUPT_CTRL, 0x00 )
        return ret


    def __init__(self):
        # Create instance attributes
        self.pinInt = None
        # Shadow / copies of register contents
        self._shadowAlsCtrl = 0     # copy of REG_ALS_CTRL
        self._shadowAlsPeriod = 0   # inter-measurement period in ms, derived from REG_ALS_PERIOD
        self._shadowAlsExposure = 0 # exposure time in 1/5ms, derived from REG_ALS_EXPOSURE
        self._shadowAcModeCtrl = 0  # copy of REG_AC_MODE_CTRL
        self._channel = [
            VD6283.ChannelConfig( index=VD6283.CHANNEL_IDX_1_RED,
                                      maskAlsEnable=VD6283.ALS_CH_EN_1,
                                      maskAcModeCtrl=VD6283.AC_CH_SEL_1 ),
            VD6283.ChannelConfig( index=VD6283.CHANNEL_IDX_2_VISIBLE,
                                      maskAlsEnable=VD6283.ALS_CH_EN_2,
                                      maskAcModeCtrl=VD6283.AC_CH_SEL_2 ),
            VD6283.ChannelConfig( index=VD6283.CHANNEL_IDX_3_BLUE,
                                      maskAlsEnable=VD6283.ALS_CH_EN_3,
                                      maskAcModeCtrl=VD6283.AC_CH_SEL_3 ),
            VD6283.ChannelConfig( index=VD6283.CHANNEL_IDX_4_GREEN,
                                      maskAlsEnable=VD6283.ALS_CH_EN_4,
                                      maskAcModeCtrl=VD6283.AC_CH_SEL_4 ),
            VD6283.ChannelConfig( index=VD6283.CHANNEL_IDX_5_IR ,
                                      maskAlsEnable=VD6283.ALS_CH_EN_5,
                                      maskAcModeCtrl=VD6283.AC_CH_SEL_5 ),
            VD6283.ChannelConfig( index=VD6283.CHANNEL_IDX_6_CLEAR,
                                      maskAlsEnable=VD6283.CH6_EN,
                                      maskAcModeCtrl=VD6283.AC_CH_SEL_6 ),
            ]
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
        light.SerialBusDevice.address            ``int`` I2C serial device address, one of :attr:`ADDRESSES_ALLOWED`; default is :attr:`ADDRESSES_ALLOWED` ``[0]``.
        light.SerialBus.*                        optional: serial bus configuration; See :meth:`serialbus.SerialBus.Params_init`.
        light.SerialBusDevice.*                  serial bus configuration; See :meth:`serialbus.SerialBusDevice.Params_init`.
        light.int.gpio.*                         GPIO1 pin configuration; See :meth:`.GPIO.Params_init`.
        light.int.cfg                            GPIO1 Interrupt pin configuration, VD6283.GPIO1_CFG_[OD | PUSH_PULL | ANALOGUE]
        light.sda.highcap                        SDA line capacitive load > 95pF, bool [True | False]
        light.sda.drv                            SDA current drive strength, low to high, int [1, ..., 5]
        light.Sensor.exposure                    Exposure time in [2, ..., 1638] milliseconds
        light.Sensor.interval                    Inter-measurement period in [0, ..., 5237] milliseconds. Only valid for continuous mode!
        light.Sensor.mode                        VD6283.ALS_MODE_[SINGLE | CONT], single-shot or continuous measurement+handshake mode. 
        light.Sensor.red.enable                  Enable the Red channel measurements. bool [True | False]
        light.Sensor.red.gain                    Red channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.green.enable                Enable the Green channel measurements. bool [True | False]
        light.Sensor.green.gain                  Green channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.blue.enable                 Enable the Blue channel measurements. bool [True | False]
        light.Sensor.blue.gain                   Blue channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.ir.enable                   Enable the IR channel measurements. bool [True | False]
        light.Sensor.ir.gain                     IR channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.visible.enable              Enable the Visible light channel measurements. bool [True | False]
        light.Sensor.visible.gain                Visible channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.clear.enable                Enable the Clear un-filtered light channel measurements. bool [True | False]
        light.Sensor.clear.gain                  Clear channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.flicker.bias.enable         Enable/Disable pedestal value feature, bool [True | False].
        light.Sensor.flicker.bias.value          Pedestal value for flicker output, int [0...7].
        light.Sensor.flicker.channel             Flicker operation channel; VD6283.CHANNEL_[NONE | FIRST | IDX_[RED | GREEN | BLUE | IR | VISIBLE | CLEAR]]
        light.Sensor.flicker.enable              Enable the frequency extraction feature. bool [True | False]
        light.Sensor.flicker.outport             GPIO output port for the flicker PDM signal; int [1 | 2]
        ===========================================================================================================================================================
        
        Also see: :meth:`.SerialBusDevice.Params_init`. 
        
        :param dict(str, object) paramDict: Dictionary mapping option\
        names to their respective values.
        :returns: none
        :rtype: None
        """
        prefix = cls.MODULE_PARAM_PREFIX + "."

        # Setup defaults
        defaults = {
            "light.SerialBusDevice.address": cls.ADDRESSES_ALLOWED[0],
            "light.int.gpio.direction":         GPIO.DIRECTION_IN,
            "light.int.cfg":                    VD6283.GPIO1_CFG_OD,
            "light.sda.highcap":                True, 
            "light.sda.drv":                    2,
            "light.Sensor.exposure":            80,
            "light.Sensor.interval":            300,
            "light.Sensor.mode":                VD6283.ALS_MODE_CONT,
            "light.Sensor.red.enable":          True,
            "light.Sensor.red.gain":            1,
            "light.Sensor.green.enable":        True,
            "light.Sensor.green.gain":          1,
            "light.Sensor.blue.enable":         True,
            "light.Sensor.blue.gain":           1,
            "light.Sensor.ir.enable":           True,
            "light.Sensor.ir.gain":             1,
            "light.Sensor.visible.enable":      True,
            "light.Sensor.visible.gain":        1,
            "light.Sensor.clear.enable":        True,
            "light.Sensor.clear.gain":          1,
            "light.Sensor.flicker.bias.enable": True,
            "light.Sensor.flicker.bias.value":  3,
            "light.Sensor.flicker.channel":     VD6283.CHANNEL_IDX_6_CLEAR,
            "light.Sensor.flicker.enable":      True,
            "light.Sensor.flicker.outport":     2
        }
        # Add defaults to paramDict
        cls._aggregateParams( paramDict, defaults )
        
        localParams = cls._extractParams( paramDict, prefix)
        SerialBus.Params_init(localParams)
        SerialBusDevice.Params_init(localParams)
        Sensor.Params_init(localParams)
        gpioParams = cls._extractParams( localParams, prefix+"int.")
        GPIO.Params_init( gpioParams )
        cls._aggregateParams( paramDict, localParams, prefix )
        cls._aggregateParams( paramDict, gpioParams, prefix+"int." )
        return None


    def open(self, paramDict):
        ret = ErrorCode.errOk
        self.Params_init(paramDict)
        localParams = self._extractParams( paramDict, self.MODULE_PARAM_PREFIX + ".")
        logging.debug("VD6283.open> Params: %s.", localParams)
        # Open serial connection
        if ret.isOk():
            ret = SerialBusDevice.open(self, localParams)
            logging.debug("VD6283.open> SerialBusDevice.open: %s.", ret)
        # Open GPIO(1) pin
        if ret.isOk():
            gpioParams = self._extractParams( localParams, "int.")
            if "gpio.pinDesignator" in gpioParams:
                self.pinInt = GPIO.getGPIO()
                ret = self.pinInt.open( gpioParams )
                logging.debug("VD6283.open> GPIO.open: %s.", ret)
        # Execute simple self-test
        if ret.isOk():
            ret = self.selfTest( SelfTest.CONNECTION )
            logging.debug("VD6283.open> selfTest: %s.", ret)
        # Read register shadows
        if ret.isOk():
            ret = self._syncShadows()
        # Configure
        if ret.isOk():
            cfg = Configuration( item=ConfigItem.multisetting,
                                 setting=paramDict )
            ret = self.configure(cfg)
            logging.debug("VD6283.open> configure: %s.", ret)
        # Activate
        if ret.isOk():
            ret = self.setRunLevel( RunLevel.active )
            logging.debug("VD6283.open> run level active: %s.", ret)
        # Clear any interrupt pending
        if ret.isOk():
            ret = self._clearInt()
        return ret

    def close(self):
        ret = self.setRunLevel( RunLevel.shutdown )
        logging.debug("VD6283.close> run level shutdown: %s.", ret)
        err = super().close()
        logging.debug("VD6283.close> super.close: %s.", err)
        if ret.isOk():
            ret = err
        if self.pinInt:
            err = self.pinInt.close()
            self.pinInt = None
            logging.debug("VD6283.close> gpio.close: %s.", err)
        if ret.isOk():
            ret = err
        return ret


    def setRunLevel(self, level):
        ret = self.isAttached()
        if ret.isOk():
            dataALS = self._shadowAlsCtrl
            dataFLK = self._shadowAcModeCtrl
            if level == RunLevel.active:
                # Set enable bit
                dataALS |= VD6283.ALS_EN     
                dataFLK |= VD6283.AC_FREQEXT_EN
            else:
                # Wipe-out enable bit
                dataALS &= ~VD6283.ALS_EN
                dataFLK &= ~VD6283.AC_FREQEXT_EN
            ret = self.writeByteRegister( VD6283.REG_ALS_CTRL, dataALS )
            logging.debug("VD6283.setRunLevel> write REG_ALS_CTRL(x%02x): %s.",
                          dataALS, ret)
            if ret.isOk():
                self._shadowAlsCtrl = dataALS
                ret = self.writeByteRegister( VD6283.REG_AC_MODE_CTRL, dataFLK )
                logging.debug("VD6283.setRunLevel> write REG_AC_MODE_CTRL(x%02x): %s.",
                              dataFLK, ret)
                if ret.isOk():
                    self._shadowAcModeCtrl = dataFLK
        else:
            logging.debug("VD6283.setRunLevel> serial bus not attached: %s.", ret)
        return ret

    #
    # Sensor API
    #
    
    def selfTest(self, tests):
        ret = ErrorCode.errOk
        if tests & SelfTest.CONNECTION:
            data, ret = self.readByteRegister( VD6283.REG_DEVICE_ID )
            logging.debug("VD6283.selfTest> read REG_DEVICE_ID: x%02x, %s.",
                          data, ret)
            if ret.isOk() and (data != VD6283.DEVICE_ID):
                ret = ErrorCode.errFailure
        else:
            logging.debug("VD6283.selfTest> invalid tests: x%04x.", tests)
        return ret


    def reset(self):
        # Re-read register shadows
        ret = self._syncShadows()
        # Clear any interrupt pending
        if ret.isOk():
            ret = self._clearInt()
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
        light.int.cfg                            GPIO1 Interrupt pin configuration, VD6283.GPIO1_CFG_[OD | PUSH_PULL | ANALOGUE]
        light.sda.highcap                        SDA line capacitive load > 95pF, bool [True | False]
        light.sda.drv                            SDA current drive strength, low to high, int [1, ..., 5]
        light.Sensor.exposure                    Exposure time in [2, ..., 1638] milliseconds
        light.Sensor.interval                    Inter-measurement period in [0, ..., 5237] milliseconds. Only valid for continuous mode!
        light.Sensor.mode                        VD6283.ALS_MODE_[SINGLE | CONT], single-shot or continuous measurement+handshake mode. 
        light.Sensor.red.enable                  Enable the Red channel measurements. bool [True | False]
        light.Sensor.red.gain                    Red channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.green.enable                Enable the Green channel measurements. bool [True | False]
        light.Sensor.green.gain                  Green channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.blue.enable                 Enable the Blue channel measurements. bool [True | False]
        light.Sensor.blue.gain                   Blue channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.ir.enable                   Enable the IR channel measurements. bool [True | False]
        light.Sensor.ir.gain                     IR channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.visible.enable              Enable the Visible light channel measurements. bool [True | False]
        light.Sensor.visible.gain                Visible channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.clear.enable                Enable the Clear un-filtered light channel measurements. bool [True | False]
        light.Sensor.clear.gain                  Clear channel gain factor [66.6, 50, 33, 25, 16, 10, 7.1, 5, 3.33, 2.5, 1.67, 1.25, 1, 0.83, 0.71]
        light.Sensor.flicker.bias.enable         Enable/Disable pedestal value feature, bool [True | False].
        light.Sensor.flicker.bias.value          Pedestal value for flicker output, int [0...7].
        light.Sensor.flicker.channel             Flicker operation channel; VD6283.CHANNEL_[NONE | IDX_1_RED ... IDX_6_CLEAR]
        light.Sensor.flicker.enable              Enable the frequency extraction feature. bool [True | False]
        light.Sensor.flicker.outport             GPIO output port for the flicker PDM signal; int [1 | 2]
        ===================================================================================================================================================
        
        Also see: :meth:`Params_init`, :class:`.configurable.Configuration`.        
        
        :param .configurable.Configuration cfg: Configuration data. 
        :return: An error code indicating either success or the reason of failure.
        :rtype: ErrorCode
        """
        if (not cfg) or (cfg.item != ConfigItem.multisetting) or \
            (not cfg.setting) or (not isinstance(cfg.setting, dict)):
            logging.debug("VD6283.configure> cfg.item=%s, cfg.setting=%s.", cfg.item, cfg.setting)
            return ErrorCode.errInvalidParameter
        
        ret = ErrorCode.errOk
        prefix = self.MODULE_PARAM_PREFIX + "."
        cs = cfg.setting
        flagClearInt = False
        
        # light.int.cfg  -->  REG_GPIO1_DRV_CFG
        value = cs.get(prefix + "int.cfg", None)
        if ret.isOk() and (value is not None) and isinstance(value, int):
            data = value if (value >= 0) and (value <= 2) else VD6283.GPIO1_CFG_DEFAULT
            ret = self.writeByteRegister( VD6283.REG_GPIO1_DRV_CFG, data )
            logging.debug("VD6283.configure> write REG_GPIO1_DRV_CFG: %s, value=x%02x, data=x%02x", ret, value, data)
       
        # light.sda:highcap, drv  -->  REG_SDA_DRV_CFG
        data = None
        value = cs.get(prefix + "sda.highcap", None)
        if ret.isOk() and (value is not None):
            data, ret = self.readByteRegister( VD6283.REG_SDA_DRV_CFG )
            data = (data | VD6283.SDA_LOAD) if value else (data & ~VD6283.SDA_LOAD)
        value = cs.get(prefix + "sda.drv", None)
        if ret.isOk() and (value is not None) and isinstance(value, int):
            if not data:
                data, ret = self.readByteRegister( VD6283.REG_SDA_DRV_CFG )
            data = data & ~VD6283.SDA_DRV
            data |= (value-1) if (value>0) and (value<=5) else VD6283.SDA_DRV_DEFAULT
        if ret.isOk() and data:
            ret = self.writeByteRegister( VD6283.REG_SDA_DRV_CFG, data )
            logging.debug("VD6283.configure> write REG_SDA_DRV_CFG: %s, data=x%02x", ret, data)
        
        prefix += "Sensor" + "."
        # light.Sensor.exposure  -->  REG_ALS_EXPOSURE
        value = cs.get(prefix + "exposure", None)
        if ret.isOk() and (value is not None) and isinstance(value, (int, float)):
            value = value if (value >= 1) and (value <= 1638) else 80	# ms!
            data = int(value * 10 + 8) // 16 - 1    # ms -> native register format
            revdata = (data + 1) * 8                # -> internal storage format in 1/5 ms
            data = bswap16( data )          # swap endianess
            ret = self.writeWordRegister( VD6283.REG_ALS_EXPOSURE, data )
            logging.debug("VD6283.configure> write REG_ALS_EXPOSURE: %s, value=%s, data=x%04x, revdata=%d", ret, value, data, revdata)
            if ret.isOk():
                self._shadowAlsExposure = revdata
            flagClearInt = True
            
        # light.Sensor.interval  -->  REG_ALS_PERIOD
        value = cs.get(prefix + "interval", None)
        if ret.isOk() and (value is not None) and isinstance(value, (int, float)):
            value = value if (value >= 0) and (value <= 5237) else 0
            data = int(value * 2 + 20) // 41
            revdata = data * 41 // 2
            ret = self.writeByteRegister( VD6283.REG_ALS_PERIOD, data )
            logging.debug("VD6283.configure> write REG_ALS_PERIOD: %s, value=%s, data=%d, revdata=%d", ret, value, data, revdata)
            if ret.isOk():
                self._shadowAlsPeriod = revdata
            flagClearInt = True
            
        # light.Sensor.mode  -->  REG_ALS_CTRL
        value = cs.get(prefix + "mode", None)
        if ret.isOk() and (value is not None) and \
            value in [VD6283.ALS_MODE_SINGLE, VD6283.ALS_MODE_CONT]:
            data = value | (self._shadowAlsCtrl & VD6283.ALS_EN) 
            ret = self.writeByteRegister( VD6283.REG_ALS_CTRL, data )
            logging.debug("VD6283.configure> write REG_ALS_CTRL: %s, value=%s, data=x%02x", ret, value, data)
            if ret.isOk():
                self._shadowAlsCtrl = data
            flagClearInt = True
        
        # light.Sensor.x.enable  -->  REG_ALS_CHANNEL_ENABLE
        data = None
        if ret.isOk():
            for ch in self._channel:
                if ch.index != VD6283.CHANNEL_IDX_6_CLEAR:
                    value = cs.get(prefix + VD6283.CHANNEL[ch.index].name + ".enable", None)
                    if value is not None:
                        ch.isEnabled = bool(value)
                        if data is None:
                            data = ch.maskAlsEnable if value else VD6283.ALS_CH_EN_NONE
                        elif value:
                            data |= ch.maskAlsEnable
            if data:
                ret = self.writeByteRegister( VD6283.REG_ALS_CHANNEL_ENABLE, data )
                logging.debug("VD6283.configure> write REG_ALS_CHANNEL_ENABLE: %s, data=x%02x", ret, data)
        
        # light.Sensor.clear.enable  -->  REG_CHANNEL6_ENABLE
        value = cs.get(prefix + "clear.enable", None)
        if ret.isOk() and (value is not None):
            for ch in self._channel:
                if ch.index == VD6283.CHANNEL_IDX_6_CLEAR:
                    ch.isEnabled = bool(value)
                    data = ch.maskAlsEnable if value else 0
                    ret = self.writeByteRegister( VD6283.REG_CHANNEL6_ENABLE, data )
                    logging.debug("VD6283.configure> write REG_CHANNEL6_ENABLE: %s, value=%s, data=x%02x", ret, value, data)
        
        # light.Sensor.x.gain  -->  REG_ALS_GAIN_CHX
        for ch in self._channel:
            if ret.isOk():
                value = cs.get(prefix + VD6283.CHANNEL[ch.index].name + ".gain", None)
                ret = self._setGain( ch, value )
        
        # light.Sensor.flicker.bias.value  -->  REG_PEDESTAL_VALUE
        value = cs.get(prefix + "flicker.bias.value", None)
        if ret.isOk() and (value is not None) and isinstance(value, int):
            data = value & VD6283.PDST_VAL
            ret = self.writeByteRegister( VD6283.REG_PEDESTAL_VALUE, data )
            logging.debug("VD6283.configure> write REG_PEDESTAL_VALUE: %s, value=%s, data=x%02x", ret, value, data)

        # light.Sensor.flicker:bias.enable, channel, enable, outport  -->  REG_AC_MODE_CTRL
        setFeature = lambda ind, dat, pos, msk: dat if ind is None else ((dat & ~msk) | pos) if ind else (dat & ~msk)
        clrFeature = lambda ind, dat, pos, msk: dat if ind is None else (dat & ~msk) if ind else ((dat & ~msk) | pos) 
        data = self._shadowAcModeCtrl
        if ret.isOk():
            value = cs.get(prefix + "flicker.bias.enable", None)
            data = clrFeature( value, data, VD6283.PEDESTAL_DIS, VD6283.PEDESTAL_DIS )
            value = cs.get(prefix + "flicker.channel", None)
            if (value is not None) and isinstance( value, int) and (value>=0) and (value<=6):
                data &= ~VD6283.AC_CH_SEL
                for ch in self._channel:
                    if ch.index == value:
                        ch.hasFlicker = True
                        data |= ch.maskAcModeCtrl
                    else:
                        ch.hasFlicker = False
            value = cs.get(prefix + "flicker.enable", None)
            data = setFeature( value, data, VD6283.AC_FREQEXT_EN, VD6283.AC_FREQEXT_EN )
            value = cs.get(prefix + "flicker.outport", None)
            if value is not None:
                if value==1:
                    data &= ~VD6283.AC_OUT_SEL
                else: 
                    data |= VD6283.AC_OUT_SEL
            if data != self._shadowAcModeCtrl:
                ret = self.writeByteRegister( VD6283.REG_AC_MODE_CTRL, data )
                logging.debug("VD6283.configure> write REG_AC_MODE_CTRL: %s, data=x%02x", ret, data)
                if ret.isOk():
                    self._shadowAcModeCtrl = data
            else:
                logging.debug("VD6283.configure> no change for REG_AC_MODE_CTRL, data=x%02x.", data)
        
        # If necessary, clear the interrupt flag
        if ret.isOk() and flagClearInt:
            ret = self._clearInt()
        return ret


    def getInfo(self):
        info = Info()
        data, ret = self.readByteRegister( VD6283.REG_ID )
        logging.debug("VD6283.getInfo> read REG_ID: data=x%02x, err=%s.", data, ret)
        if ret.isOk():
            info.validity |= Info.validChipID
            info.chipID = data
        data, ret = self.readByteRegister( VD6283.REG_REVISION_ID )
        logging.debug("VD6283.getInfo> read REG_REVISION_ID: data=x%02x, err=%s.", data, ret)
        if ret.isOk():
            info.validity |= Info.validRevMajor
            info.revMajor = data

        return info, ret


    def getStatus(self, statusID):
        del statusID
        status, ret = self.readByteRegister( VD6283.REG_INTERRUPT_CTRL )
        logging.debug("VD6283.getStatus> read REG_INTERRUPT_CTRL: data=x%02x, err=%s.", status, ret)
        if ret.isOk():
            status = not (status & VD6283.INTR_ST)
        return status, ret


    def getRawData(self):
        data = dict()
        ret = ErrorCode.errOk
        
        flickerDisabled = not (self._shadowAcModeCtrl & VD6283.AC_FREQEXT_EN)
        # Immediate read, no wait for nothing
        for ch in self._channel:
            # Read out raw data
            if ch.isEnabled and (flickerDisabled or not ch.hasFlicker):
                reg = VD6283.REG_ALS_CHX_DATA + (ch.index - 1)*4
                value, ret = self.readWordRegister( reg )
                logging.debug("VD6283.getRawData> read REG #x%02X: data=x%04x, err=%s.", reg, value, ret)
                if ret.isOk():
                    value = bswap16( value )  # swap endianess
                    logging.debug("VD6283.getRawData> swapped value=x%04x.", value)
                    name = VD6283.CHANNEL[ch.index].name
                    data[name] = value
                    logging.debug("VD6283.getRawData> data[%s]: %d.", name, value)
            else:
                logging.debug("VD6283.getRawData> Channel #%d skipped. ch.enabled=%r flkDisabled=%r ch.hasFlk=%r.",
                              ch.index, ch.isEnabled, flickerDisabled, ch.hasFlicker)
        if not data:
            ret = ErrorCode.errFewData
        return data, ret
 
    def raw2Abs(self, raw):
        data = dict()
        ret = ErrorCode.errOk

        for ch in self._channel:
            chName = VD6283.CHANNEL[ch.index].name
            rawValue = raw.get( chName, None )
            if rawValue is not None:
                absValue, ret = self._transferToIntensity( rawValue, ch )
                if ret.isOk():
                    data[chName] = absValue
                    logging.debug("VD6283.raw2Abs> transferred %d -> %d, err=%s.",
                                  rawValue, absValue, ret)
                    
        if not data:
            ret = ErrorCode.errFewData
        return data, ret

           
    def getLatestData(self):
        data, ret = self.getRawData()
        if ret.isOk():
            data, ret = self.raw2Abs( data )            
        return data, ret
    

    def getNextData(self):
        data = None
        ret = ErrorCode.errOk
        loopCount = 0
        maxLoops = 3
        
        # Wait for an interrupt, indicated by '0'
        wait_time = (self._shadowAlsExposure + 2) // 5  # Exposure time in ms 
        wait_time += self._shadowAlsPeriod              # inter-measurement period
        wait_time = (wait_time + 1) // 2                # take half of a period
        wait_time /= 1000       # express in seconds (->float!)
        
        intr, ret = self.getStatus( None )
        while (not intr) and ret.isOk() and (loopCount < maxLoops):
            sleep( wait_time )   
            intr, ret = self.getStatus( None )
            loopCount += 1
            
        # Retrieve data
        if ret.isOk():
            if intr:
                data, ret = self.getLatestData()
            elif ret.isOk():
                ret = ErrorCode.errUnavailable
        # Clear interrupt
        self.writeByteRegister( VD6283.REG_INTERRUPT_CTRL, VD6283.CLR_INTR )
        self.writeByteRegister( VD6283.REG_INTERRUPT_CTRL, 0x00 )

        return data, ret

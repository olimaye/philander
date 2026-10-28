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
- Continous (streaming) mode is still mystique. It's unclear, how it works.
- The interrupt flag INTR_ST is low-active.
- Clearing INTR_ST is achieved by cycling CRL_INTR through a 1-0 sequence.
  So, INTERRUPT_CTRL needs to be written twice.
- Clearing INTR_ST starts a new measurement.
- Not verified: EXPOSURE+6ms after clearing INTR_ST the ALS_CHx_DATA have
  fresh data ready to be read.
- After EXPOSURE+IM_PERIOD the interrupt is raised (INTR_ST=0).
- ALS_CHx_DATA registers are not locked with INTR_ST. They still may change afterwards.
- If interrupt is not cleared, another measurement starts automatically
- After another EXPOSURE+IM_PERIOD, the next measurement is available
- but interrupt is still active.
- This cycle works only once. Data is locked then until INTR_ST is cleared.

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
    DELAY_MIN			= 0
    DELAY_DEFAULT 		= 0
    DELAY_MAX			= 5228

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
    
    REG_ALS_EXPOSURE    = 0x1D		# Intervals of 1.6 ms 
    # REG_ALS_EXPOSURE_M  = 0x1D
    # REG_ALS_EXPOSURE_L  = 0x1E
    EXPOSURE_MIN		= 1
    EXPOSURE_DEFAULT    = 80
    EXPOSURE_MAX		= 1638
    
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
    GAIN_MIN		= 0.71
    GAIN_DEFAULT	= 1
    GAIN_MAX		= 67
    
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
    
    HOUSEKEEPING_DELAY  = 6     # Delay in ms for measurement housekeeping
    
    @dataclass
    class ChannelCharacteristic():
        """Data structure to represent fix channel data (characteristic).
        """
        name:			str
        maskAlsEnable:  int     # For REG_ALS_CHANNEL_ENABLE / REG_CHANNEL6_ENABLE
        maskFlkEnable:  int     # For REG_AC_MODE_CTRL
        # Scaling factor for mapping into intensity [mW/m^2]
        # Holds for exposure=50ms and at 25 deg. C.
        # Datasheet gives it in counts per uW/cm^2, so we store it
        # as 1/100 counts per mw/m^2
        # so, e.g. 62.3 cnt/(uW/cm^2) = 623 * 1/100 * cnt/(mW/m^2).
        # Refer to chap. 8.2. for more details on the sensitivity.
        sensitivity:    int     # in 1/100 mW/m^2

    CHANNEL = {
        CHANNEL_IDX_1_RED:		ChannelCharacteristic(
                                    name="red",
                                    maskAlsEnable=ALS_CH_EN_1,
                                    maskFlkEnable=AC_CH_SEL_1,
                                    sensitivity=146 ),
        CHANNEL_IDX_2_VISIBLE:	ChannelCharacteristic(
                                    name="visible",
                                    maskAlsEnable=ALS_CH_EN_2,
                                    maskFlkEnable=AC_CH_SEL_2,
                                    sensitivity=497 ),
        CHANNEL_IDX_3_BLUE:		ChannelCharacteristic(
                                    name="blue",
                                    maskAlsEnable=ALS_CH_EN_3,
                                    maskFlkEnable=AC_CH_SEL_3,
                                    sensitivity=146 ),
        CHANNEL_IDX_4_GREEN:	ChannelCharacteristic(
                                    name="green",
                                    maskAlsEnable=ALS_CH_EN_4,
                                    maskFlkEnable=AC_CH_SEL_4,
                                    sensitivity=295 ),
        CHANNEL_IDX_5_IR:		ChannelCharacteristic(
                                    name="ir",
                                    maskAlsEnable=ALS_CH_EN_5,
                                    maskFlkEnable=AC_CH_SEL_5,
                                    sensitivity=860 ),
        CHANNEL_IDX_6_CLEAR:	ChannelCharacteristic(
                                    name="clear",
                                    maskAlsEnable=CH6_EN,
                                    maskFlkEnable=AC_CH_SEL_6,
                                    sensitivity=623 ),
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
    

    @dataclass
    class ChannelConfig():
        """Data structure to represent variable channel data (configuration).
        """
        isEnabled:      bool = False
        hasFlicker:     bool = False
        gain:           int = 24    # Gain factor stored in 1/24.


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
            for chIdx in range( VD6283.CHANNEL_NUM ):
                ch = self._channel[chIdx]
                if (chIdx+1) == VD6283.CHANNEL_IDX_6_CLEAR:
                    ch.isEnabled = ch6Ena & VD6283.CH6_EN
                else:        
                    ch.isEnabled = chEna & VD6283.CHANNEL[chIdx+1].maskAlsEnable
                ch.hasFlicker = ((acModeCtrl & VD6283.AC_CH_SEL) == VD6283.CHANNEL[chIdx+1].maskFlkEnable)
                data, ret = self.readByteRegister(VD6283.REG_ALS_GAIN_CHX + chIdx)
                logging.debug("VD6283._syncShadows> read REG_ALS_GAIN_CH%d: data=x%02x, err=%s.", 
                              (chIdx+1), data, ret)
                if ret.isOk():
                    ch.gain = VD6283.GAIN_DICT.getValue(data & VD6283.ALS_GAIN)
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
            VD6283.ChannelConfig(),
            VD6283.ChannelConfig(),
            VD6283.ChannelConfig(),
            VD6283.ChannelConfig(),
            VD6283.ChannelConfig(),
            VD6283.ChannelConfig(),
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
        light.Sensor.flicker.bias.value          Pedestal value for flicker output, int [0...7] or None to disable feature.
        light.Sensor.flicker.channel             Flicker operation channel; VD6283.CHANNEL_[NONE | IDX_1_RED ... IDX_6_CLEAR]. CHANNEL_NONE to disable.
        light.Sensor.flicker.outport             GPIO output port for the flicker PDM signal; int [1 | 2]. Avoid conflict with externclk=True!
        light.Sensor.flicker.externclk           bool. True if PDM uses external clock on GPIO2, False for internal clock (default).
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
            "light.Sensor.flicker.bias.value":  3,
            "light.Sensor.flicker.channel":     VD6283.CHANNEL_IDX_6_CLEAR,
            "light.Sensor.flicker.outport":     2,
            "light.Sensor.flicker.externclk":   False
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
            logging.debug("VD6283.open> _syncShadows: %s.", ret)
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
            ret = self.clearInt()
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
            if level == RunLevel.active:
                # Set enable bit
                dataALS |= VD6283.ALS_EN     
            else:
                # Wipe-out enable bit
                dataALS &= ~VD6283.ALS_EN
            ret = self.writeByteRegister( VD6283.REG_ALS_CTRL, dataALS )
            logging.debug("VD6283.setRunLevel> write REG_ALS_CTRL(x%02x): %s.",
                          dataALS, ret)
            if ret.isOk():
                self._shadowAlsCtrl = dataALS
                if level == RunLevel.active:
                    self.settle()
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
            ret = self.clearInt()
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
        light.Sensor.flicker.bias.value          Pedestal value for flicker output, int [0...7] or None to disable feature.
        light.Sensor.flicker.channel             Flicker operation channel; VD6283.CHANNEL_[NONE | IDX_1_RED ... IDX_6_CLEAR]. CHANNEL_NONE to disable.
        light.Sensor.flicker.outport             GPIO output port for the flicker PDM signal; int [1 | 2]. Avoid conflict with externclk=True!
        light.Sensor.flicker.externclk           bool. True if PDM uses external clock on GPIO2, False for internal clock (default).
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
            ret = self.setGpioDrv( value )
       
        # light.sda:highcap, drv  -->  REG_SDA_DRV_CFG
        flgHighCap = cs.get(prefix + "sda.highcap", None)
        value = cs.get(prefix + "sda.drv", None)
        if ret.isOk():
            ret = self.setSdaDrv( flgHighCap, value )
        
        prefix += "Sensor" + "."
        # light.Sensor.exposure  -->  REG_ALS_EXPOSURE
        value = cs.get(prefix + "exposure", None)
        if ret.isOk() and (value is not None) and isinstance(value, (int, float)):
            self.setExposure( value )
            flagClearInt = True
            
        # light.Sensor.interval  -->  REG_ALS_PERIOD
        value = cs.get(prefix + "interval", None)
        if ret.isOk() and (value is not None) and isinstance(value, (int, float)):
            ret = self.setDelay( value )
            flagClearInt = True
            
        # light.Sensor.mode  -->  REG_ALS_CTRL
        value = cs.get(prefix + "mode", None)
        if ret.isOk() and (value is not None):
            ret = self.setMode( value )
            flagClearInt = True
        
        # light.Sensor.x.enable  -->  REG_ALS_CHANNEL_ENABLE, REG_CHANNEL6_ENABLE
        if ret.isOk():
            value = [None] * VD6283.CHANNEL_NUM
            for chIdx in range( VD6283.CHANNEL_NUM ):
                token = cs.get(prefix + VD6283.CHANNEL[chIdx+1].name + ".enable", None)
                if token is not None:
                    value[chIdx] = bool(token)
            ret = self.enableChannels( value )
        
        # light.Sensor.x.gain  -->  REG_ALS_GAIN_CHX
        for chIdx in range(1, 7):
            if ret.isOk():
                value = cs.get(prefix + VD6283.CHANNEL[chIdx].name + ".gain", None)
                ret = self.setGain( chIdx, value )
        
        # light.Sensor.flicker.bias.value  -->  REG_PEDESTAL_VALUE
        # light.Sensor.flicker:bias.enable, channel, enable, outport  -->  REG_AC_MODE_CTRL
        if ret.isOk():
            bias = cs.get(prefix + "flicker.bias.value", None)
            chNum = cs.get(prefix + "flicker.channel", None)
            pdmOut = cs.get(prefix + "flicker.outport", None)
            extClk = cs.get(prefix + "flicker.externclk", None)
            ret = self.setFlicker(chNum, pdmOut, extClk, bias)
        
        # If necessary, clear the interrupt flag
        if ret.isOk() and flagClearInt:
            ret = self.clearInt()
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


    def getLatestData(self):
        data, ret = self.getRawData()
        if ret.isOk():
            data, ret = self.rawToIntensity( data )            
        return data, ret
    

    def getNextData(self):
        data = None
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
        self.clearInt()

        return data, ret


    #
    # Individual, proprietary API
    #

    def settle(self):
        """Waits an amount of time to get the sensor settled.
        
        This method does nothing else than just spending time. The exact
        amount of time depends on the currently adjusted exposure time
        EXTIME and inter-measuremen period IM_PERIOD. The sum of both is
        extend by the ```VD6283.HOUSEKEEPING_DELAY``` to render a complete
        measurement cycle.
        The application should call this method once after modifying the
        exposure or gain setting before starting measurements.

        :returns: An error code to indicate success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        wait_time = self._shadowAlsExposure / 5 + self._shadowAlsPeriod
        wait_time += VD6283.HOUSEKEEPING_DELAY
        wait_time /= 1000
        sleep( wait_time )
        return ret
         
    def clearInt(self):
        """Clears the interrupt flag INTR_ST.

        :returns: An error code to indicate success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = self.writeByteRegister( VD6283.REG_INTERRUPT_CTRL, VD6283.CLR_INTR )
        if ret.isOk():
            ret = self.writeByteRegister( VD6283.REG_INTERRUPT_CTRL, 0x00 )
        logging.debug("VD6283.clearInt> write REG_INTERRUPT_CTRL: %s", ret)
        return ret
    
    def setGpioDrv(self, value):
        """Set GPIO drive capability.

        The given value is written to the REG_GPIO1_DRV_CFG register.
        
        :param int value: New GPIO drive configuration, one of the VD6283.GPIO1_CFG_ constants.
        :returns: An error code to indicate success or the reason of failure.
        :rtype: ErrorCode
        """
        data = value if (value >= 0) and (value <= 2) else VD6283.GPIO1_CFG_DEFAULT
        ret = self.writeByteRegister( VD6283.REG_GPIO1_DRV_CFG, data )
        logging.debug("VD6283.setGpioDrv> write REG_GPIO1_DRV_CFG: %s, value=x%02x, data=x%02x", ret, value, data)
        return ret
    
    def setSdaDrv(self, valHighcap, valDrv):
        """Set SDA drive capability.

        The given values are written to the REG_SDA_DRV_CFG register.
        
        :param int valHighcap: VD6283.SDA_LOAD for high capacitive load on SDA, zero otherwise.
        :param int valDrv: [0...4] New SDA drive configuration, one of the VD6283.SDA_DRV_ constants.
        :returns: An error code to indicate success or the reason of failure.
        :rtype: ErrorCode
        """
        data = None
        ret = ErrorCode.errOk
        if valHighcap is not None:
            data, ret = self.readByteRegister( VD6283.REG_SDA_DRV_CFG )
            data = (data | VD6283.SDA_LOAD) if valHighcap else (data & ~VD6283.SDA_LOAD)
        if ret.isOk() and (valDrv is not None) and isinstance(valDrv, int):
            if not data:
                data, ret = self.readByteRegister( VD6283.REG_SDA_DRV_CFG )
            data = data & ~VD6283.SDA_DRV
            data |= (valDrv-1) if (valDrv>0) and (valDrv<=5) else VD6283.SDA_DRV_DEFAULT
        if ret.isOk() and data:
            ret = self.writeByteRegister( VD6283.REG_SDA_DRV_CFG, data )
            logging.debug("VD6283.setSdaDrv> write REG_SDA_DRV_CFG: %s, data=x%02x", ret, data)
        return ret
    
    def setExposure(self, value, autoSettle=False):
        """Set exposure time.

        The given value is written to the REG_ALS_EXPOSURE register.
        Note the exposure time defines the duration that the sensor is
        exposed light. This is the ADC integration time.
        The exposure time plus the inter-measurement delay plus some
        time for housekeeping (~6ms) together define the duration of one
        measurement cycle, which as its reciprocal, gives the data rate.
        
        :param int value: New exposure time in milliseconds (ms), increments of 1.6ms.
        :param bool autoSettle: True for automatically calling  ```settle``` afterwards.
        :returns: An error code to indicate success or the reason of failure.
        :rtype: ErrorCode
        """
        value = value if (value >= VD6283.EXPOSURE_MIN) and (value <= VD6283.EXPOSURE_MAX) else VD6283.EXPOSURE_DEFAULT
        data = int(value * 10 + 8) // 16 - 1    # ms -> native register format
        revdata = (data + 1) * 8                # -> internal storage format in 1/5 ms
        data = bswap16( data )          # swap endianess
        ret = self.writeWordRegister( VD6283.REG_ALS_EXPOSURE, data )
        logging.debug("VD6283.setExposure> write REG_ALS_EXPOSURE: %s, value=%s, data=x%04x, revdata=%d", ret, value, data, revdata)
        if ret.isOk():
            self._shadowAlsExposure = revdata
            if autoSettle:
                ret = self.settle()
        return ret

    def setDelay(self, value):
        """Set the inter-measurement delay interval.

        The given value is written to the REG_ALS_PERIOD register.
        Note the delay time defines the time between the end of one
        measurement and the beginning of the next one.
        The exposure time plus the inter-measurement interval plus some
        time for housekeeping (~6ms) together define the duration of one
        measurement cycle, which as its reciprocal, gives the data rate.  
        
        :param int value: New delay time in milliseconds (ms), increments of 20.5ms
        :returns: An error code to indicate success or the reason of failure.
        :rtype: ErrorCode
        """
        value = value if (value >= VD6283.DELAY_MIN) and (value <= VD6283.DELAY_MAX) else VD6283.DELAY_DEFAULT
        data = int(value * 2 + 20) // 41
        revdata = data * 41 // 2
        ret = self.writeByteRegister( VD6283.REG_ALS_PERIOD, data )
        logging.debug("VD6283.setDelay> write REG_ALS_PERIOD: %s, value=%s, data=%d, revdata=%d", ret, value, data, revdata)
        if ret.isOk():
            self._shadowAlsPeriod = revdata
        return ret
    
    def setMode(self, value):
        """Set the measurement mode to either single or continous measurement.

        The given value is written to the REG_ALS_CTRL register.
        
        :param int value: New mode to operate in.
        :returns: An error code to indicate success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if value in [VD6283.ALS_MODE_SINGLE, VD6283.ALS_MODE_CONT]:
            data = value | (self._shadowAlsCtrl & VD6283.ALS_EN) 
            ret = self.writeByteRegister( VD6283.REG_ALS_CTRL, data )
            logging.debug("VD6283.setMode> write REG_ALS_CTRL: %s, value=%s, data=x%02x", ret, value, data)
            if ret.isOk():
                self._shadowAlsCtrl = data
        else:
            ret = ErrorCode.errInvalidParameter
        return ret
    
    def enableChannels(self, lstValue):
        """Enables or disables one or more channels.

        The given parameter must be a list with at least VD6283.CHANNEL_NUM
        positions. It is interpreted as a list of values, where each value
        corresponds to a channel.
        Note the different indexing scheme: The value at list index zero
        [0] corresponds to the first channel, which is channel #1.
        If a value is True, the corresponding channel is enabled.
        If it is False, the channel is disabled.
        If the value is None, the status of the channel is left unchanged.
        The result affects the REG_ALS_CHANNEL_ENABLE and
        REG_CHANNEL6_ENABLE registers.
        
        :param int value: New mode to operate in.
        :returns: An error code to indicate success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        if isinstance( lstValue, list ) and (len(lstValue) >= VD6283.CHANNEL_NUM):
            if not all( val is None for val in lstValue ):
                oldData, ret = self.readByteRegister( VD6283.REG_ALS_CHANNEL_ENABLE )
                if ret.isOk():
                    oldData &= VD6283.ALS_CH_EN_ALL
                    newData = oldData
                    for chIdx in range(VD6283.CHANNEL_NUM-1):
                        if lstValue[chIdx]:
                            newData |= VD6283.CHANNEL[chIdx+1].maskAlsEnable
                            self._channel[chIdx].isEnabled = True
                        elif lstValue[chIdx] is not None:
                            newData &= ~VD6283.CHANNEL[chIdx+1].maskAlsEnable
                            self._channel[chIdx].isEnabled = False
                        else:
                            self._channel[chIdx].isEnabled = bool(newData & VD6283.CHANNEL[chIdx+1].maskAlsEnable)
                    if newData != oldData:
                        ret = self.writeByteRegister( VD6283.REG_ALS_CHANNEL_ENABLE, newData )
                        logging.debug("VD6283.enableChannels> Write REG_ALS_CHANNEL_ENABLE: %s, newData=x%02x", ret, newData)
                    else:
                        logging.debug("VD6283.enableChannels> Skipping rewriting REG_ALS_CHANNEL_ENABLE: oldData=x%02x, newData=x%02x",
                                      oldData, newData)
                else:
                    logging.debug("VD6283.enableChannels> Couldn't read REG_ALS_CHANNEL_ENABLE: %s", ret)
                if ret.isOk() and (lstValue[5] is not None):
                    oldData, ret = self.readByteRegister( VD6283.REG_CHANNEL6_ENABLE )
                    if ret.isOk():
                        if bool(oldData & VD6283.CH6_EN) != bool(lstValue[5]):
                            newData = oldData ^ VD6283.CH6_EN
                            ret = self.writeByteRegister( VD6283.REG_CHANNEL6_ENABLE, newData )
                            self._channel[5].isEnabled = bool(newData & VD6283.CH6_EN)
                            logging.debug("VD6283.enableChannels> Write REG_CHANNEL6_ENABLE: %s, newData=x%02x", ret, newData)
                        else:
                            logging.debug("VD6283.enableChannels> No change for REG_CHANNEL6_ENABLE: oldData=x%02x, newData=%s",
                                          oldData, lstValue[5])
                    else:
                        logging.debug("VD6283.enableChannels> Couldn't read REG_CHANNEL6_ENABLE: %s", ret)
                else:
                    logging.debug("VD6283.enableChannels> Something went wrong before working on REG_CHANNEL6_ENABLE: %s", ret)
                logging.debug("VD6283.enableChannels> %s. Leaving. list=%s", ret, lstValue)
            else:
                logging.debug("VD6283.enableChannels> %s. Nothing to do: list=%s", ret, lstValue)
        else:
            ret = ErrorCode.errInvalidParameter
            logging.debug("VD6283.enableChannels> %s. list=%s", ret, lstValue)
        return ret
    
    def setGain(self, channelNum, value, autoSettle=False):
        """Set channel gain.

        Expect value in external format, as a plain factor, possibly float!
        The given value is written to the REG_ALS_GAIN_CHX register.

        :param int channelNum: [1...6] Number of the channel to adjust the gain for.
        :param int value: [0.71 ... 67] The new gain factor for the given channel.
        :param bool autoSettle: True for automatically calling  ```settle``` afterwards.
        :returns: An error code to indicate success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        data = None
        if (channelNum is None) or not isinstance(channelNum, int) or \
            (value is None) or not isinstance(value, (int, float)):
            ret = ErrorCode.errInvalidParameter
            logging.debug("VD6283.setGain> channel #%s, value=%s failed ret=%s",
                          channelNum, value, ret)
        else:
            value = value * 24
            if isinstance( value, float ):
                value = round(value)
            data, ret = VD6283.GAIN_DICT.findKey( value )
            if ret.isOk():
                register = VD6283.REG_ALS_GAIN_CHX + channelNum - 1
                ret = self.writeByteRegister( register, data )
            if ret.isOk():
                gain, ret = VD6283.GAIN_DICT.getValue(data)
                self._channel[channelNum-1].gain = gain
                if autoSettle:
                    ret = self.settle()
            logging.debug("VD6283.setGain> channel #%d: value=%s, data=%s, gain=%d, ret=%s",
                          channelNum, value, data, gain, ret)
        return ret

    def setFlicker(self, channelNum=CHANNEL_NONE,
                    pdmOut=1, extClk=False,
                    pedestal=PEDESTAL_DEFAULT ):
        """Setup the flicker engine.

        Configures the flicker engine as specified by the given parameters.
        Note that there is implicit meaning and side effects as described
        in the parameters section.
        The given values affect the REG_AC_MODE_CTRL and REG_PEDESTAL_VALUE
        registers.

        :param int channelNum: [0...6] The ALS channel to use for flicker recognition.\
        Intensity measurements cannot be made on that channel, simultaneously!\
        VD6283.CHANNEL_NONE to disable the flicker engine.
        :param int pdmOut: [1 | 2] Sensor's GPIO for PDM output. 1 for GPIO1 (default), 2 for GPIO2.
        :param bool extClk: True if external clk on GPIO2 shall be used for PDM, False for internal clock.
        :param int pedestal: [0...7] Pedestal value to apply. None to disable the pedestal feature.
        :returns: An error code to indicate success or the reason of failure.
        :rtype: ErrorCode
        """
        ret = ErrorCode.errOk
        newAcModeCtrl = self._shadowAcModeCtrl
        # REG_PEDESTAL_VALUE and REG_AC_MODE_CTRL:PEDESTAL_DIS
        if pedestal is None:
            newAcModeCtrl |= VD6283.PEDESTAL_DIS
        elif not isinstance(pedestal, int):
            ret = ErrorCode.errInvalidParameter
        else:
            newAcModeCtrl &= ~VD6283.PEDESTAL_DIS
            data = pedestal & VD6283.PDST_VAL
            ret = self.writeByteRegister( VD6283.REG_PEDESTAL_VALUE, data )
            logging.debug("VD6283.setFlicker> write REG_PEDESTAL_VALUE: %s, pedestal=%s, data=x%02x", ret, pedestal, data)
        if ret.isOk():  # AC_CH_SEL and AC_FREQEXT_EN
            if (channelNum is None) or not isinstance( channelNum, int) or \
                (channelNum < VD6283.CHANNEL_NONE) or (channelNum > VD6283.CHANNEL_NUM):
                ret = ErrorCode.errInvalidParameter
            else:
                newAcModeCtrl &= ~VD6283.AC_CH_SEL
                newAcModeCtrl &= ~VD6283.AC_FREQEXT_EN
                for chIdx in range( VD6283.CHANNEL_NUM ): 
                    ch = self._channel[chIdx]
                    if (chIdx+1) == channelNum:
                        ch.hasFlicker = True
                        newAcModeCtrl |= VD6283.CHANNEL[chIdx+1].maskFlkEnable | VD6283.AC_FREQEXT_EN
                    else:
                        ch.hasFlicker = False
        if ret.isOk():  # AC_OUT_SEL and PDM_CLK_SEL
            if (pdmOut is None) or not isinstance( pdmOut, int) or  \
                (pdmOut < 1) or (pdmOut > 2):
                ret = ErrorCode.errInvalidParameter
            elif (extClk is None) or not isinstance( extClk, bool):
                ret = ErrorCode.errInvalidParameter
            elif (pdmOut != 1) and extClk:	# GPIO2 shall be PDM output and input for external clock
                ret = ErrorCode.errResourceConflict
            else:
                if pdmOut==1:
                    newAcModeCtrl &= ~VD6283.AC_OUT_SEL
                else: 
                    newAcModeCtrl |= VD6283.AC_OUT_SEL
                if extClk:
                    newAcModeCtrl |= VD6283.PDM_CLK_SEL
                else: 
                    newAcModeCtrl &= ~VD6283.PDM_CLK_SEL
        # Update REG_AC_MODE_CTRL, if new content is different    
        if ret.isOk():
            if newAcModeCtrl != self._shadowAcModeCtrl:
                ret = self.writeByteRegister( VD6283.REG_AC_MODE_CTRL, newAcModeCtrl )
                logging.debug("VD6283.setFlicker> write REG_AC_MODE_CTRL: %s, newAcModeCtrl=x%02x, old shadow=x%02x",
                              ret, newAcModeCtrl, self._shadowAcModeCtrl)
                if ret.isOk():
                    self._shadowAcModeCtrl = newAcModeCtrl
            else:
                logging.debug("VD6283.setFlicker> no change for REG_AC_MODE_CTRL, newAcModeCtrl=x%02x.", newAcModeCtrl)
        return ret

    def getRawData(self):
        """Retrieve a measurement as raw digital counts.

        The measurement result is a list of integer values.
        This list has always CHANNEL_NUM entries.
        The first element in this list (at index 0) is the measurement
        result for CHANNEL_IDX_1_RED, the second element at index 1
        corresponds to CHANNEL_IDX_2_VISIBLE and so on.
        So, list[0...5] corresponds to CHANNEL_1...CHANNEL_6.
        Note that the flicker frequency is not part of a sensor
        measurement. Instead, flicker must be determined by the surrounding
        circuitry and the application.
        If a sensor channel is disabled or has the flicker engine operating
        on it, the corresponding list entry is negative.
        Otherwise, the raw ADC measurement value is a 16 bit value
        ranging in [0 ... 65535].
        
        :returns: A list of raw measurement int values \
        and an error code to indicate success or the reason of failure.
        :rtype: list, ErrorCode
        """
        data = [-1] * VD6283.CHANNEL_NUM
        ret = ErrorCode.errOk
        
        flickerDisabled = not (self._shadowAcModeCtrl & VD6283.AC_FREQEXT_EN)
        # Immediate read, no wait for nothing
        for chIdx in range( VD6283.CHANNEL_NUM ): 
            ch = self._channel[chIdx]
            # Read out raw data
            if ch.isEnabled and (flickerDisabled or not ch.hasFlicker):
                reg = VD6283.REG_ALS_CHX_DATA + chIdx*4
                value, ret = self.readWordRegister( reg )
                logging.debug("VD6283.getRawData> read REG #x%02X: data=x%04x, err=%s.", reg, value, ret)
                if ret.isOk():
                    value = bswap16( value )  # swap endianess
                    logging.debug("VD6283.getRawData> swapped value=x%04x.", value)
                    data[chIdx] = value
                    logging.debug("VD6283.getRawData> data[%d]: %d.", chIdx, value)
            else:
                logging.debug("VD6283.getRawData> Channel #%d skipped. ch.enabled=%r flkDisabled=%r ch.hasFlk=%r.",
                              (chIdx+1), ch.isEnabled, flickerDisabled, ch.hasFlicker)

        # Alternative implementation
        # Immediate read, no wait for nothing
#         buf, ret = self.readBufferRegister( VD6283.REG_ALS_CHX_DATA, VD6283.CHANNEL_NUM * 4 )
#         logging.debug("VD6283.getRawData> read base REG #x%02X: err=%s.",
#                       VD6283.REG_ALS_CHX_DATA, ret)
#         if ret.isOk():
#             for chIdx in range( VD6283.CHANNEL_NUM ): 
#                 ch = self._channel[chIdx]
#                 # Peek raw data
#                 if ch.isEnabled and (flickerDisabled or not ch.hasFlicker):
#                     # Just _H and _M, ignore _L.
#                     data[chIdx] = (buf[4*chIdx] << 8) | buf[4*chIdx+1]
#                     logging.debug("VD6283.getRawData> data[%d]: %d.", chIdx, data[chIdx])
#                 else:
#                     logging.debug("VD6283.getRawData> Channel #%d skipped. ch.enabled=%r flkDisabled=%r ch.hasFlk=%r.",
#                                   (chIdx+1), ch.isEnabled, flickerDisabled, ch.hasFlicker)
        
        return data, ret
 
    def rawToIntensity( self, rawData ):
        """Translate digital measurement value into intensity.
        
        :param list(int) adcCounts: List of 16bit raw digital reading
        :returns: List of corresponding intensity values in mW/m^2 as int \
        and an error code to indicate success or the reason of failure.
        :rtype: list(int), ErrorCode
        """
        err = ErrorCode.errOk
        result = [-1] * len(rawData)
        for chIdx in range( VD6283.CHANNEL_NUM ):
            ch = self._channel[chIdx]
            rawValue = rawData[chIdx]
            if rawValue >= 0:
                # Apply channel gain, sensitivity and exposure time, where
                # sensitivity reference is given for EXTIME=50ms and 5x / 10x gain
                # sensitivity is already in mW/m^2.
                # Gain correction:    * 10[5] * 24 / channel.gain
                # sensitivity:        * 100 / VD6283.CHANNEL[channel.index].sensitivity
                # exposure time:      * 248 / self._shadowAlsExposure; 248 = 49.6ms * 5 ~ 50ms*5
                # So overall:        *24*10[5]*100*248 / (...gain*...sensitivity*...exposure)
                # Finally, reduce the fraction by 256 for numerical reasons.
                divisor = (ch.gain * VD6283.CHANNEL[chIdx+1].sensitivity * self._shadowAlsExposure + 128) >> 8
                if (chIdx+1)==VD6283.CHANNEL_IDX_6_CLEAR:
                    intens = rawValue * 11625 
                else:
                    intens = rawValue * 23250
                result[chIdx] = (intens + (divisor>>1)) // divisor
                logging.debug("VD6283._transferToIntensity> channel #%d: raw=%d -> result=%d",
                              (chIdx+1), rawValue, result[chIdx])
                err = ErrorCode.errOk
            else:
                logging.debug("VD6283._transferToIntensity> channel #%d skipped.",
                              (chIdx+1))
        return result, err
